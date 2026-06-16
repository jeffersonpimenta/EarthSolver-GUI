"""Camada de execucao do solver: funcoes modulo-level (picaveis) que envolvem o
nucleo `earthsolver`.

Sao picaveis (entrada/saida = tipos simples; objetos do nucleo construidos
dentro da funcao) para rodarem em subprocesso via `nicegui.run.cpu_bound`, sem
travar a UI nem esbarrar no pickling do multiprocessing no Windows.

Cap opcional de seguranca para o demo publico: env `EARTHGUI_MAX_SEG` limita o
numero de segmentos (0 ou ausente = ilimitado). Util porque solo estratificado
(N>1) com malha grande e custoso no nucleo.
"""

from __future__ import annotations

import os

import numpy as np
from earthsolver.estratificacao import Estratificador
from earthsolver.malha import EstudoAterramento, Malha
from earthsolver.numerico import (
    Condutor,
    Eletrodo,
    EstudoNumerico,
    estudo_convergencia,
)
from earthsolver.solo import ModeloSolo


# --------------------------------------------------------------- eletrodo
def _construir_eletrodo(spec: dict) -> Eletrodo:
    """Constroi um `Eletrodo` a partir do spec da GUI.

    spec aceita uma das chaves:
      - "condutores": [{"p1":[x,y,z], "p2":[x,y,z], "raio":r}, ...]
      - "malha_retangular": {comprimento_x, comprimento_y, espac_x, espac_y,
                             prof_h, d, n_hastes, comp_haste}
      - "dxf": caminho + "mapa": {padrao, layers, escala}
    """
    if "malha_retangular" in spec:
        mr = dict(spec["malha_retangular"])
        mr["n_hastes"] = int(mr.get("n_hastes", 0))  # ui.number entrega float
        return Eletrodo.malha_retangular(**mr)
    if "condutores" in spec:
        return Eletrodo([Condutor(c["p1"], c["p2"], c["raio"])
                         for c in spec["condutores"]])
    if "dxf" in spec:
        from earthsolver import dxf
        return dxf.from_dxf(spec["dxf"], mapa=spec.get("mapa"))
    raise ValueError("spec de eletrodo deve ter 'condutores', 'malha_retangular' ou 'dxf'")


def _interfaces(solo_dict: dict) -> np.ndarray:
    esp = solo_dict.get("espessura") or []
    return np.cumsum(esp) if len(esp) else np.asarray(())


def estimar_segmentos(eletrodo_spec: dict, comp_alvo: float, solo_dict=None) -> int:
    """Numero de segmentos que a geometria gera (so geometria, sem resolver)."""
    el = _construir_eletrodo(eletrodo_spec)
    interfaces = _interfaces(solo_dict or {})
    return int(el.segmentar(comp_alvo, interfaces).n)


def _limite_segmentos() -> int:
    try:
        return int(os.environ.get("EARTHGUI_MAX_SEG", "0"))
    except ValueError:
        return 0


def condutores_do_spec(eletrodo_spec: dict) -> list[dict]:
    """Lista de condutores {p1, p2, raio} do spec (p/ pre-visualizacao, sem resolver)."""
    el = _construir_eletrodo(eletrodo_spec)
    return [{"p1": list(c.p1), "p2": list(c.p2), "raio": c.raio} for c in el.condutores]


def escanear_dxf(caminho: str) -> dict:
    """Varre as layers de um DXF: {layer: {'tipos': [...], 'n': contagem}}.

    Base para o mapeador visual de layers (substitui o wizard interativo da CLI).
    """
    import ezdxf
    from earthsolver import dxf

    doc = ezdxf.readfile(caminho)
    scan = dxf.escanear_layers(doc)
    return {nome: {"tipos": sorted(d["tipos"]), "n": d["n"]} for nome, d in scan.items()}


def params_malha_analitica(ret: dict, rho_s=None, h_s: float = 0.1) -> dict:
    """Deriva os parametros da `Malha` (IEEE-80) a partir da malha retangular.

    A geometria retangular do solver numerico (`malha_retangular`) descreve a
    mesma grade que o estudo analitico precisa em forma agregada (area + Lc). O
    `Lc` segue a contagem de condutores de `Eletrodo.malha_retangular`:
    `nx = round(cx/espac_x)`, `ny = round(cy/espac_y)`; ha `ny+1` linhas de
    comprimento `cx` e `nx+1` linhas de comprimento `cy`.

    Ancora de regressao: `exemplos/eletrodo_malha.json` -> area=4900, Lc=1540
    (igual a `exemplos/projeto.json`). `espac_D` usa o menor espacamento.
    """
    cx = float(ret["comprimento_x"])
    cy = float(ret["comprimento_y"])
    ex = float(ret["espac_x"])
    ey = float(ret["espac_y"])
    nx = int(round(cx / ex))
    ny = int(round(cy / ey))
    return {
        "area": cx * cy,
        "Lc": (ny + 1) * cx + (nx + 1) * cy,
        "comprimento_x": cx,
        "comprimento_y": cy,
        "espac_D": min(ex, ey),
        "prof_h": float(ret["prof_h"]),
        "d": float(ret["d"]),
        "n_hastes": int(ret.get("n_hastes", 0)),
        "comp_haste": float(ret.get("comp_haste", 0.0)),
        "rho_s": rho_s,
        "h_s": float(h_s),
    }


# --------------------------------------------------------------- pipeline
def rodar_estratificacao(espacamentos, valores, eh_rho: bool,
                         camadas, max_camadas: int = 4) -> dict:
    """Estratifica o solo a partir de uma sondagem de Wenner.

    `valores` sao resistencias (eh_rho=False) ou resistividades aparentes
    (eh_rho=True). `camadas` = "auto" ou um inteiro. Devolve solo, metricas do
    ajuste e os dados da curva de resistividade aparente (medida + ajustada).
    """
    if eh_rho:
        est = Estratificador(espacamentos, resistividades=valores)
    else:
        est = Estratificador(espacamentos, resistencias=valores)
    if str(camadas) == "auto":
        est.auto_estratificar(max_camadas=int(max_camadas))
    else:
        est.estratificar(int(camadas))

    a_fit = np.geomspace(float(est.a.min()), float(est.a.max()), 100)
    rho_fit = est.modelo_direto(est.modelo, a_fit)  # forward model do nucleo
    return {
        "solo": est.modelo.to_dict(),
        "ajuste": {
            "rms": None if est.rms is None else float(est.rms),
            "n_camadas": len(est.modelo.rho),
            "convergiu": bool(est.convergiu),
            "n_iter": est.n_iter,
        },
        "curva": {
            "a": est.a.tolist(),
            "rho_medido": est.rho_a.tolist(),
            "a_fit": a_fit.tolist(),
            "rho_fit": np.asarray(rho_fit, dtype=float).tolist(),
        },
    }


def rodar_analitico(solo_dict: dict, malha_dict: dict, falta_dict: dict) -> dict:
    """Estudo analitico IEEE Std 80 (classe Malha agregada)."""
    solo = ModeloSolo.from_dict(solo_dict)
    malha = Malha(**malha_dict)
    estudo = EstudoAterramento(
        solo, malha,
        Ig=falta_dict["Ig"], t=falta_dict["t"], peso=falta_dict.get("peso", 70))
    estudo.resolver()
    return estudo.resultado


def rodar_numerico(solo_dict: dict, eletrodo_spec: dict, params: dict, fila=None) -> dict:
    """Solver numerico de segmentacao. Devolve resultado, rasters, corrente e condutores.

    Aplica o cap `EARTHGUI_MAX_SEG` antes de resolver (etapa cara). `fila` (opcional)
    e uma fila entre processos: quando dada, recebe um evento de progresso por passo
    (ver `earthsolver.progresso`), consumido pela barra de progresso da GUI. O
    callable e montado aqui dentro porque a funcao roda em subprocesso (`cpu_bound`).
    """
    solo = ModeloSolo.from_dict(solo_dict)
    eletrodo = _construir_eletrodo(eletrodo_spec)
    comp_alvo = float(params.get("comp_alvo", 2.0))

    n_seg = int(eletrodo.segmentar(comp_alvo, _interfaces(solo_dict)).n)
    limite = _limite_segmentos()
    if limite and n_seg > limite:
        raise ValueError(
            f"geometria gera {n_seg} segmentos, acima do limite de {limite} "
            f"(aumente comp_alvo ou reduza a malha).")

    estudo = EstudoNumerico(
        solo, eletrodo,
        Ig=params["Ig"], t=params["t"], peso=params.get("peso", 70),
        comp_alvo=comp_alvo, rho_s=params.get("rho_s"), h_s=params.get("h_s", 0.1))
    estudo.resolver(progresso=(fila.put if fila is not None else None))
    X, Y, Phi = estudo.raster
    Xt, Yt, Tq = estudo.raster_toque
    Xp, Yp, Pa = estudo.raster_passo
    A, B, Iseg = estudo.dados_corrente()
    return {
        "resultado": estudo.resultado,
        "raster": {"x": X.tolist(), "y": Y.tolist(), "phi": Phi.tolist(),
                   "GPR": float(estudo.V)},
        "raster_toque": {"x": Xt.tolist(), "y": Yt.tolist(), "v": Tq.tolist()},
        "raster_passo": {"x": Xp.tolist(), "y": Yp.tolist(), "v": Pa.tolist()},
        "corrente": {"A": np.asarray(A).tolist(), "B": np.asarray(B).tolist(),
                     "I": np.asarray(Iseg).tolist()},
        "condutores": [{"p1": list(c.p1), "p2": list(c.p2), "raio": c.raio}
                       for c in eletrodo.condutores],
    }


def rodar_convergencia(solo_dict: dict, eletrodo_spec: dict, params: dict,
                       comp_alvos, fila=None) -> dict:
    """Curva de convergencia: Rg e GPR por numero de segmentos.

    Re-resolve a malha (caminho rapido, so Rg/GPR) para cada comprimento-alvo em
    `comp_alvos` -- etapa cara, roda em subprocesso. `fila` alimenta a barra de
    progresso da GUI (ver `rodar_numerico`). Devolve {n_segmentos, Rg, GPR} (listas).
    """
    solo = ModeloSolo.from_dict(solo_dict)
    eletrodo = _construir_eletrodo(eletrodo_spec)

    # cap de seguranca: o comp_alvo mais fino e o que gera mais segmentos.
    limite = _limite_segmentos()
    if limite:
        n_seg = int(eletrodo.segmentar(min(comp_alvos), _interfaces(solo_dict)).n)
        if n_seg > limite:
            raise ValueError(
                f"convergencia geraria ate {n_seg} segmentos, acima do limite de "
                f"{limite} (aumente o comp_alvo minimo ou reduza a malha).")

    dados = estudo_convergencia(
        solo, eletrodo, Ig=params["Ig"], t=params["t"], comp_alvos=list(comp_alvos),
        peso=params.get("peso", 70), rho_s=params.get("rho_s"),
        h_s=params.get("h_s", 0.1), progresso=(fila.put if fila is not None else None))
    return {k: np.asarray(dados[k]).tolist() for k in ("n_segmentos", "Rg", "GPR")}
