"""Passo 3 do pipeline: calculo do aterramento.

Le tudo do projeto (solo, geometria, malha analitica derivada, falta) e roda o
metodo escolhido: IEEE Std 80 (fechado), numerico (segmentacao, em subprocesso)
ou ambos com comparacao lado a lado. O IEEE-80 so fica disponivel quando a
geometria e uma malha retangular parametrica.
"""

from __future__ import annotations

import asyncio
import json
from multiprocessing import Manager

from nicegui import run, ui

from gui import graficos
from gui.componentes import barra_progresso, campo_num, cartoes_resultado, num_json, segmented, selo
from gui.estado import obter_projeto
from gui.layout import barra_passos, cabecalho, moldura
from gui.solver import rodar_analitico, rodar_convergencia, rodar_numerico

# fatores do estudo analitico IEEE-80
_FATORES = [("rho", "rho eq (Ohm.m)"), ("rho_s", "rho_s (Ohm.m)"), ("n", "n"),
            ("Ki", "Ki"), ("Km", "Km"), ("Ks", "Ks"), ("Kh", "Kh"), ("Kii", "Kii"),
            ("Cs", "Cs"), ("L_M", "L_M (m)"), ("L_S", "L_S (m)")]

# (chave, rotulo, casas) das grandezas comparadas IEEE-80 x numerico
_COMPARA = [("Rg", "Rg (Ohm)", 3), ("GPR", "GPR (V)", 1), ("Em", "Em toque (V)", 1),
            ("Es", "Es passo (V)", 1), ("E_toque", "Limite toque (V)", 1),
            ("E_passo", "Limite passo (V)", 1)]


def _tabela_comparacao(a: dict, n: dict) -> None:
    """Compara IEEE-80 x numerico nas grandezas principais."""
    linhas = []
    for k, rot, dec in _COMPARA:
        linhas.append({
            "g": rot,
            "ieee": round(float(a[k]), dec) if k in a else "-",
            "num": round(float(n[k]), dec) if k in n else "-",
        })
    linhas.append({
        "g": "Veredito",
        "ieee": "APROVADO" if a.get("aprovado") else "REPROVADO",
        "num": "APROVADO" if n.get("aprovado") else "REPROVADO",
    })
    ui.table(columns=[
        {"name": "g", "label": "Grandeza", "field": "g", "align": "left"},
        {"name": "ieee", "label": "IEEE-80", "field": "ieee"},
        {"name": "num", "label": "Numerico", "field": "num"},
    ], rows=linhas).props("flat").classes("w-full")


def _tabela_fatores(res: dict) -> None:
    """Fatores intermediarios do estudo IEEE-80."""
    linhas = [{"fator": rot, "valor": round(float(res[k]), 4)}
              for k, rot in _FATORES if k in res]
    ui.table(columns=[{"name": "fator", "label": "Fator", "field": "fator", "align": "left"},
                      {"name": "valor", "label": "Valor", "field": "valor"}],
             rows=linhas).props("flat").classes("w-full")


@ui.page("/calculo")
async def pagina_calculo() -> None:
    await ui.context.client.connected()
    proj = obter_projeto()
    estado: dict = {"ieee80": None, "numerico": None}

    with moldura("Calculo", "/calculo"):
        cabecalho("Passo 3", "Calculo do aterramento")
        barra_passos(3)

        # ---------------------------------------------------- pre-requisitos
        faltas = []
        if not proj.solo:
            faltas.append(("Solo nao definido.", "/estratificacao", "Estratificacao"))
        if not proj.eletrodo:
            faltas.append(("Malha nao definida.", "/malha", "Malha"))
        if not proj.falta:
            faltas.append(("Corrente de falta nao definida.", "/malha", "Malha"))
        if faltas:
            for msg, rota, rotulo in faltas:
                with ui.row().classes("items-center gap-2"):
                    ui.icon("warning", color="warning")
                    ui.label(msg)
                    ui.button(f"Ir para {rotulo}",
                              on_click=lambda r=rota: ui.navigate.to(r)).props("flat dense")
            return

        analitico_ok = "malha_retangular" in proj.eletrodo and "area" in (proj.malha or {})

        # ---------------------------------------------------------- metodo
        with ui.card().classes("w-full p-5 gap-3"):
            with ui.row().classes("items-center justify-between w-full flex-wrap gap-4"):
                with ui.column().classes("gap-2"):
                    ui.label("Metodo de calculo").classes("es-section-title")
                    if analitico_ok:
                        metodo = segmented({"ieee80": "IEEE-80", "numerico": "Numerico",
                                            "ambos": "Ambos (comparar)"}, "ambos")
                    else:
                        metodo = segmented({"numerico": "Numerico"}, "numerico")
                comp_alvo = campo_num("comp_alvo (m)", 5.0, unit="m", min=0.1)
                comp_alvo.style("width:150px")
                botao = ui.button("Calcular", icon="play_arrow")
            if not analitico_ok:
                ui.label("Geometria nao retangular (DXF) -> IEEE-80 indisponivel; "
                         "apenas o metodo numerico.").classes("text-warning text-sm")
        barra_calc = barra_progresso()

        # ---------------------------------------------------------- resultado
        @ui.refreshable
        def resultado() -> None:
            ieee = estado["ieee80"]
            num = estado["numerico"]
            if not ieee and not num:
                return

            ambos = bool(ieee and num)
            if ambos:
                ok = bool(ieee.get("aprovado") and num["resultado"].get("aprovado"))
                with ui.row().classes("items-center gap-4 flex-wrap"):
                    selo(ok)
                    ui.label("Toque e passo dentro dos limites do IEEE Std 80 para a corrente "
                             "de falta informada." if ok else
                             "Toque e/ou passo excedem os limites do IEEE Std 80 — revise a "
                             "malha ou a brita.").classes("text-sm text-grey")
            else:
                cartoes_resultado(ieee or num["resultado"])

            def _card_comparacao() -> None:
                with ui.card().classes("w-full h-full p-0 overflow-hidden"):
                    with ui.row().classes("es-card-head"):
                        ui.label("IEEE-80 × Numerico").classes("es-card-head-title")
                    _tabela_comparacao(ieee, num["resultado"])

            def _card_graficos() -> None:
                ras = num["raster"]
                rt, rp = num["raster_toque"], num["raster_passo"]
                cor, conds = num["corrente"], num["condutores"]
                et, ep = num["resultado"]["E_toque"], num["resultado"]["E_passo"]
                with ui.card().classes("w-full h-full p-3"):
                    with ui.tabs().props("no-caps active-color=primary").classes("w-full") as plots:
                        ui.tab("mapa", "Mapa de potencial")
                        ui.tab("toque", "Tensao de toque")
                        ui.tab("passo", "Tensao de passo")
                        ui.tab("margem", "Margem")
                        ui.tab("corrente", "Corrente")
                        ui.tab("perfis", "Perfis")
                        ui.tab("s3d", "Superficie 3D")
                        ui.tab("c3d", "Campo 3D (toque)")
                        ui.tab("geo", "Geometria")
                    with ui.tab_panels(plots, value="mapa").classes("w-full"):
                        with ui.tab_panel("mapa"):
                            ui.plotly(graficos.mapa_potencial(
                                ras["x"], ras["y"], ras["phi"], gpr=ras["GPR"],
                                condutores=conds)).classes("w-full")
                        with ui.tab_panel("toque"):
                            ui.plotly(graficos.mapa_toque(
                                rt["x"], rt["y"], rt["v"], limite=et,
                                condutores=conds)).classes("w-full")
                        with ui.tab_panel("passo"):
                            ui.plotly(graficos.mapa_passo(
                                rp["x"], rp["y"], rp["v"], limite=ep,
                                condutores=conds)).classes("w-full")
                        with ui.tab_panel("margem"):
                            ui.plotly(graficos.mapa_margem(
                                rt["x"], rt["y"], rt["v"], rp["v"], et, ep,
                                condutores=conds)).classes("w-full")
                        with ui.tab_panel("corrente"):
                            ui.plotly(graficos.mapa_corrente(
                                cor["A"], cor["B"], cor["I"])).classes("w-full")
                        with ui.tab_panel("perfis"):
                            ui.plotly(graficos.perfis(
                                ras["x"], ras["y"], ras["phi"], rt["v"], rp["v"],
                                et, ep, ras["GPR"])).classes("w-full")
                        with ui.tab_panel("s3d"):
                            ui.plotly(graficos.superficie_3d(
                                ras["x"], ras["y"], ras["phi"])).classes("w-full")
                        with ui.tab_panel("c3d"):
                            ui.plotly(graficos.campo_3d(
                                rt["x"], rt["y"], rt["v"],
                                "Tensao de toque (3D)", "V")).classes("w-full")
                        with ui.tab_panel("geo"):
                            ui.plotly(graficos.vista_malha(conds)).classes("w-full")

            if ambos:
                with ui.grid().classes("w-full gap-5 items-stretch") \
                        .style("grid-template-columns:minmax(0,1fr) minmax(0,1.25fr)"):
                    _card_comparacao()
                    _card_graficos()
            elif num:
                _card_graficos()

            if ieee:
                ui.label("Fatores IEEE-80").classes("es-section-title")
                with ui.card().classes("w-full p-0 overflow-hidden"):
                    _tabela_fatores(ieee)

            def usar() -> None:
                if ieee:
                    proj.resultado_analitico = ieee
                if num:
                    proj.resultado_numerico = num["resultado"]
                    proj.raster = num["raster"]
                ui.notify("Resultado salvo no projeto.", type="positive")

            with ui.row().classes("gap-3"):
                ui.button("Usar no projeto", icon="check", on_click=usar)
                if ieee:
                    ui.button("Baixar IEEE-80", icon="download",
                              on_click=lambda: ui.download.content(
                                  json.dumps(ieee, indent=2, default=num_json),
                                  "analitico.json")).props("outline")
                if num:
                    ui.button("Baixar resultado", icon="download",
                              on_click=lambda: ui.download.content(
                                  json.dumps(num["resultado"], indent=2, default=num_json),
                                  "aterramento_numerico.json")).props("outline")
                    ui.button("Baixar potencial", icon="download",
                              on_click=lambda: ui.download.content(
                                  json.dumps(num["raster"], indent=2, default=num_json),
                                  "potencial.json")).props("outline")

        async def calcular() -> None:
            escolha = metodo.value
            estado["ieee80"] = None
            estado["numerico"] = None

            if escolha in ("ieee80", "ambos"):
                try:
                    estado["ieee80"] = rodar_analitico(proj.solo, proj.malha, proj.falta)
                except Exception as exc:  # noqa: BLE001
                    ui.notify(f"Falha no IEEE-80: {exc}", type="negative")
                    return

            if escolha in ("numerico", "ambos"):
                brita = proj.malha or {}
                params = {"Ig": proj.falta["Ig"], "t": proj.falta["t"],
                          "peso": int(proj.falta.get("peso", 70)),
                          "comp_alvo": comp_alvo.value,
                          "rho_s": brita.get("rho_s"), "h_s": brita.get("h_s", 0.1)}
                botao.disable()
                barra_calc.iniciar()
                gerente = Manager()
                fila = gerente.Queue()
                tarefa = asyncio.create_task(run.cpu_bound(
                    rodar_numerico, proj.solo, proj.eletrodo, params, fila))
                try:
                    while not tarefa.done():           # drena a fila enquanto resolve
                        while not fila.empty():
                            barra_calc.aplicar(fila.get())
                        await asyncio.sleep(0.05)
                    estado["numerico"] = await tarefa   # propaga excecao do subprocesso
                except Exception as exc:  # noqa: BLE001
                    ui.notify(f"Falha no numerico: {exc}", type="negative")
                    return
                finally:
                    barra_calc.encerrar()
                    botao.enable()

            resultado.refresh()
            ui.notify("Calculo concluido.", type="positive")

        botao.on_click(calcular)

        resultado()

        # ---------------------------------------------- convergencia (sob demanda)
        @ui.refreshable
        def painel_convergencia() -> None:
            dados = estado.get("convergencia")
            if dados:
                ui.plotly(graficos.curva_convergencia(dados)).classes("w-full")

        async def estudar_convergencia() -> None:
            ca = float(comp_alvo.value or 5.0)
            comp_alvos = [f * ca for f in (2.0, 1.5, 1.0, 0.75, 0.5)]
            brita = proj.malha or {}
            params = {"Ig": proj.falta["Ig"], "t": proj.falta["t"],
                      "peso": int(proj.falta.get("peso", 70)),
                      "rho_s": brita.get("rho_s"), "h_s": brita.get("h_s", 0.1)}
            botao_conv.disable()
            barra_conv.iniciar()
            gerente = Manager()
            fila = gerente.Queue()
            tarefa = asyncio.create_task(run.cpu_bound(
                rodar_convergencia, proj.solo, proj.eletrodo, params, comp_alvos, fila))
            try:
                while not tarefa.done():
                    while not fila.empty():
                        barra_conv.aplicar(fila.get())
                    await asyncio.sleep(0.05)
                estado["convergencia"] = await tarefa
            except Exception as exc:  # noqa: BLE001
                ui.notify(f"Falha na convergencia: {exc}", type="negative")
                return
            finally:
                barra_conv.encerrar()
                botao_conv.enable()
            painel_convergencia.refresh()
            ui.notify("Convergencia concluida.", type="positive")

        with ui.card().classes("w-full p-5 gap-2"):
            ui.label("Estudo de convergencia").classes("es-section-title")
            ui.label("Re-resolve a malha em varias resolucoes (comp_alvo) e traca "
                     "Rg/GPR vs numero de segmentos. Etapa cara.").classes("text-sm text-grey")
            with ui.row().classes("items-center gap-3"):
                botao_conv = ui.button("Estudar convergencia", icon="timeline",
                                       on_click=estudar_convergencia).props("outline")
            barra_conv = barra_progresso()
            painel_convergencia()
