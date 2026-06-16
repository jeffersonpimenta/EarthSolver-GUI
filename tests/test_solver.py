"""Testes da camada de execucao do solver (gui/solver.py).

Casos pequenos e rapidos (solo uniforme, malhas pequenas, comp_alvo grosso) para
nao depender do caminho lento de solo estratificado.
"""

import json
import queue
from pathlib import Path

import pytest

from gui import solver

EXEMPLOS = Path(__file__).resolve().parent.parent / "exemplos"

SOLO_UNIFORME = {"rho": [400.0], "espessura": []}
# quadrado simples 10x10 (so o anel externo), poucos segmentos
MALHA_PEQUENA = {
    "comprimento_x": 10.0, "comprimento_y": 10.0, "espac_x": 10.0, "espac_y": 10.0,
    "prof_h": 0.5, "d": 0.01, "n_hastes": 0, "comp_haste": 0.0,
}
PARAMS = {"Ig": 1000.0, "t": 0.5, "peso": 70, "comp_alvo": 5.0, "rho_s": None, "h_s": 0.1}


def test_rodar_estratificacao_n_fixo_devolve_solo_e_curva():
    sond = json.loads((EXEMPLOS / "projeto.json").read_text(encoding="utf-8"))["sondagem"]
    saida = solver.rodar_estratificacao(
        sond["espacamentos"], sond["resistencias"], eh_rho=False,
        camadas=2, max_camadas=4)
    assert len(saida["solo"]["rho"]) == 2
    assert saida["ajuste"]["rms"] is not None
    assert len(saida["curva"]["a_fit"]) == len(saida["curva"]["rho_fit"]) > 2
    assert len(saida["curva"]["a"]) == len(saida["curva"]["rho_medido"])


def test_rodar_estratificacao_auto_escolhe_n_camadas():
    sond = json.loads((EXEMPLOS / "projeto.json").read_text(encoding="utf-8"))["sondagem"]
    # max_camadas=1 mantem o caminho "auto" barato (so testa N=1)
    saida = solver.rodar_estratificacao(
        sond["espacamentos"], sond["resistencias"], eh_rho=False,
        camadas="auto", max_camadas=1)
    assert saida["ajuste"]["n_camadas"] == 1


def test_params_malha_analitica_deriva_area_e_lc():
    ret = json.loads((EXEMPLOS / "eletrodo_malha.json")
                     .read_text(encoding="utf-8"))["malha_retangular"]
    p = solver.params_malha_analitica(ret, rho_s=2500.0, h_s=0.102)
    # ancora de regressao: bate com exemplos/projeto.json
    assert p["area"] == 4900.0
    assert p["Lc"] == 1540.0
    assert p["espac_D"] == 7.0
    assert p["n_hastes"] == 20
    # o dict derivado deve servir de entrada para o estudo analitico
    res = solver.rodar_analitico(SOLO_UNIFORME, p, {"Ig": 1908.0, "t": 0.5, "peso": 70})
    assert res["Rg"] > 0


def test_rodar_analitico_devolve_rg_positivo():
    malha = json.loads((EXEMPLOS / "projeto.json").read_text(encoding="utf-8"))["malha"]
    falta = {"Ig": 1908.0, "t": 0.5, "peso": 70}
    res = solver.rodar_analitico(SOLO_UNIFORME, malha, falta)
    assert res["Rg"] > 0
    assert "GPR" in res


def test_rodar_numerico_malha_retangular_uniforme():
    saida = solver.rodar_numerico(SOLO_UNIFORME, {"malha_retangular": MALHA_PEQUENA}, PARAMS)
    assert saida["resultado"]["Rg"] > 0
    assert {"x", "y", "phi"} <= set(saida["raster"])
    assert len(saida["condutores"]) >= 1
    assert "p1" in saida["condutores"][0]


def test_rodar_numerico_devolve_rasters_de_seguranca_e_corrente():
    saida = solver.rodar_numerico(SOLO_UNIFORME, {"malha_retangular": MALHA_PEQUENA}, PARAMS)
    assert {"raster_toque", "raster_passo", "corrente"} <= set(saida)
    assert {"x", "y", "v"} <= set(saida["raster_toque"])
    assert {"x", "y", "v"} <= set(saida["raster_passo"])
    cor = saida["corrente"]
    n = len(saida["condutores"])  # malha pequena: 1 segmento por condutor (comp_alvo grosso)
    assert len(cor["A"]) == len(cor["B"]) == len(cor["I"]) >= n >= 1


def test_rodar_numerico_emite_progresso_quando_recebe_fila():
    fila = queue.Queue()
    solver.rodar_numerico(SOLO_UNIFORME, {"malha_retangular": MALHA_PEQUENA}, PARAMS, fila=fila)
    eventos = []
    while not fila.empty():
        eventos.append(fila.get())
    assert eventos                              # houve progresso
    assert eventos[-1]["concluido"] is True
    assert eventos[-1]["fracao"] == 1.0


def test_rodar_convergencia_devolve_curvas_alinhadas():
    comp_alvos = [10.0, 7.0, 5.0]
    saida = solver.rodar_convergencia(
        SOLO_UNIFORME, {"malha_retangular": MALHA_PEQUENA}, PARAMS, comp_alvos)
    assert len(saida["n_segmentos"]) == len(saida["Rg"]) == len(saida["GPR"]) == 3
    assert all(rg > 0 for rg in saida["Rg"])
    # estudo_convergencia ordena por numero crescente de segmentos
    assert saida["n_segmentos"] == sorted(saida["n_segmentos"])


def test_rodar_numerico_aceita_lista_de_condutores():
    spec = json.loads((EXEMPLOS / "cond.json").read_text(encoding="utf-8"))
    params = {**PARAMS, "comp_alvo": 20.0}  # bem grosso -> rapido
    saida = solver.rodar_numerico(SOLO_UNIFORME, spec, params)
    assert saida["resultado"]["Rg"] > 0


def test_estimar_segmentos_positivo():
    n = solver.estimar_segmentos({"malha_retangular": MALHA_PEQUENA}, comp_alvo=5.0)
    assert isinstance(n, int) and n > 0


def test_estimar_segmentos_via_dxf():
    mapa = json.loads((EXEMPLOS / "layers.json").read_text(encoding="utf-8"))
    n = solver.estimar_segmentos(
        {"dxf": str(EXEMPLOS / "malha.dxf"), "mapa": mapa}, comp_alvo=10.0)
    assert n > 0


def test_condutores_do_spec_para_preview():
    conds = solver.condutores_do_spec({"malha_retangular": MALHA_PEQUENA})
    assert conds and {"p1", "p2", "raio"} <= set(conds[0])


def test_escanear_dxf_lista_layers():
    scan = solver.escanear_dxf(str(EXEMPLOS / "malha.dxf"))
    assert scan  # ao menos uma layer
    alguma = next(iter(scan.values()))
    assert "tipos" in alguma and "n" in alguma


def test_cap_de_segmentos_recusa_malha_grande(monkeypatch):
    monkeypatch.setenv("EARTHGUI_MAX_SEG", "10")
    spec = json.loads((EXEMPLOS / "cond.json").read_text(encoding="utf-8"))
    params = {**PARAMS, "comp_alvo": 0.5}  # muitos segmentos
    with pytest.raises(ValueError, match="segmento"):
        solver.rodar_numerico(SOLO_UNIFORME, spec, params)
