"""Passo 2 do pipeline: definicao da malha + corrente de falta.

A geometria do eletrodo e definida de um de dois modos:
  - Parametros (malha retangular): alimenta tanto o IEEE-80 quanto o numerico.
  - Importar DXF: geometria arbitraria; so o solver numerico.

Aqui tambem ficam os parametros do estudo compartilhados pelos dois metodos:
brita (rho_s, h_s) e corrente de falta (Ig, t, peso). A pre-visualizacao (so
geometria, sem resolver) usa um comp_alvo de referencia.
"""

from __future__ import annotations

import json
import tempfile
import uuid
from pathlib import Path

from nicegui import ui

from gui import graficos, recursos
from gui.componentes import campo_num, dropzone
from gui.estado import obter_projeto
from gui.layout import barra_passos, cabecalho, moldura
from gui.solver import (
    condutores_do_spec,
    escanear_dxf,
    estimar_segmentos,
    params_malha_analitica,
)

_RET = ["comprimento_x", "comprimento_y", "espac_x", "espac_y",
        "prof_h", "d", "n_hastes", "comp_haste"]

# comp_alvo usado so na previa (o valor do calculo fica na pagina de calculo)
_COMP_ALVO_PREVIA = 5.0


def _defaults() -> tuple[dict, dict, dict]:
    """(malha_retangular, malha analitica, falta) do projeto de exemplo."""
    ret = json.loads(recursos.caminho_exemplo("eletrodo_malha.json")
                     .read_text(encoding="utf-8"))["malha_retangular"]
    proj = json.loads(recursos.caminho_exemplo("projeto.json").read_text(encoding="utf-8"))
    return ret, proj["malha"], proj["falta"]


@ui.page("/malha")
async def pagina_malha() -> None:
    await ui.context.client.connected()
    proj = obter_projeto()
    estado: dict = {"dxf_path": None}
    campos_layer: dict = {}

    ret_def, malha_def, falta_def = _defaults()
    # pre-preenche a geometria retangular a partir do projeto, se houver
    ret_base = (proj.eletrodo or {}).get("malha_retangular") or ret_def
    malha_base = proj.malha or malha_def
    falta_base = proj.falta or falta_def

    with moldura("Malha e falta", "/malha"):
        cabecalho("Passo 2", "Malha e corrente de falta")
        barra_passos(2)

        # previa (refreshables definidos antes para ficarem na coluna direita)
        @ui.refreshable
        def preview() -> None:
            dados = estado.get("preview")
            if not dados:
                ui.label("Pre-visualize para ver a geometria.").classes("text-sm text-grey")
                return
            ui.plotly(graficos.vista_malha(dados["condutores"])).classes("w-full")

        @ui.refreshable
        def preview_meta() -> None:
            dados = estado.get("preview")
            txt = (f"≈ {dados['n']} segmentos estimados (comp_alvo {_COMP_ALVO_PREVIA} m)"
                   if dados else "—")
            ui.label(txt).classes("es-card-meta")

        # previa ja pintada por padrao a partir da geometria retangular (mesmo sem DXF)
        try:
            _spec0 = {"malha_retangular": {k: float(ret_base[k]) for k in _RET}}
            estado["preview"] = {"n": estimar_segmentos(_spec0, _COMP_ALVO_PREVIA),
                                 "condutores": condutores_do_spec(_spec0)}
        except Exception:  # noqa: BLE001
            pass

        # ---------------------------------------------- geometria + previa (grade)
        with ui.grid().classes("w-full gap-5 items-stretch") \
                .style("grid-template-columns:minmax(0,1.3fr) minmax(0,1fr)"):
            with ui.card().classes("w-full h-full p-0 overflow-hidden"):
                ui.label("Geometria do eletrodo").classes("es-section-title px-5 pt-5")
                with ui.tabs().props("inline-label no-caps").classes("self-start px-3") as abas:
                    ui.tab("ret", "Parametros (malha retangular)")
                    ui.tab("dxf", "Importar DXF")
                abas.value = "ret"
                with ui.tab_panels(abas, value="ret").classes("w-full"):
                    with ui.tab_panel("ret"):
                        campos_ret: dict = {}
                        with ui.grid(columns=3).classes("gap-3 w-full"):
                            for k in _RET:
                                unidade = "" if k == "n_hastes" else "m"
                                campos_ret[k] = campo_num(k, float(ret_base[k]), unit=unidade)
                    with ui.tab_panel("dxf"):
                        ui.markdown("DXF -> **somente metodo numerico** (o IEEE-80 exige "
                                    "malha retangular). Mapeie cada layer como fio ou haste.")
                        with ui.row().classes("gap-4 items-center"):
                            escala = ui.number("Escala (desenho->m)", value=1.0).classes("w-40")
                            padrao_prof = ui.number("Prof. padrao (m)", value=0.5).classes("w-40")
                            padrao_raio = ui.number("Raio padrao (m)", value=0.005).classes("w-40")

                        @ui.refreshable
                        def tabela_layers() -> None:
                            campos_layer.clear()
                            if not estado["dxf_path"]:
                                ui.label("Envie um DXF para mapear as layers.").classes("text-grey")
                                return
                            scan = escanear_dxf(estado["dxf_path"])
                            for nome, info in scan.items():
                                with ui.row().classes("items-center gap-3"):
                                    ui.label(f"{nome} ({info['n']})").classes("w-40")
                                    prof = ui.number("prof", value=0.5).classes("w-24")
                                    raio = ui.number("raio", value=0.005).classes("w-24")
                                    rod = ui.checkbox("haste")
                                    comp = ui.number("comp", value=3.0).classes("w-24")
                                    campos_layer[nome] = {"prof": prof, "raio": raio,
                                                          "rod": rod, "comp": comp}

                        async def importar_dxf(e) -> None:
                            destino = Path(tempfile.gettempdir()) / f"earthgui_{uuid.uuid4().hex}.dxf"
                            await e.file.save(destino)
                            estado["dxf_path"] = str(destino)
                            tabela_layers.refresh()
                            ui.notify(f"{e.file.name} carregado.", type="positive")

                        dropzone('Importar <span class="es-mono" style="color:#334155">'
                                 'arquivo .dxf</span>', "Arraste ou clique para enviar",
                                 importar_dxf, accept=".dxf")
                        tabela_layers()

            with ui.card().classes("w-full h-full p-0 overflow-hidden"):
                with ui.row().classes("es-card-head"):
                    ui.label("Previa da geometria").classes("es-card-head-title")
                    preview_meta()
                with ui.column().classes("w-full p-4"):
                    preview()

        # ----------------------------------------------- parametros do estudo
        with ui.card().classes("w-full p-5 gap-3"):
            ui.label("Parametros do estudo").classes("es-section-title")
            with ui.grid(columns=5).classes("gap-3 w-full"):
                rho_s = campo_num("rho_s — brita", malha_base.get("rho_s"), unit="Ω·m")
                h_s = campo_num("h_s", float(malha_base.get("h_s", 0.1)), unit="m", min=0.01)
                ig = campo_num("Ig", float(falta_base["Ig"]), unit="A")
                tf = campo_num("t", float(falta_base["t"]), unit="s")
                with ui.column().classes("gap-1.5"):
                    ui.label("Peso").classes("es-field-label")
                    peso = ui.select({50: "50 kg", 70: "70 kg"},
                                     value=int(falta_base.get("peso", 70))) \
                        .props("outlined dense").classes("es-num w-full")

        def _spec() -> dict:
            if abas.value == "ret":
                return {"malha_retangular": {k: campos_ret[k].value for k in _RET}}
            if not estado["dxf_path"]:
                raise ValueError("envie um arquivo DXF")
            layers = {}
            for nome, w in campos_layer.items():
                ent = {"prof": w["prof"].value, "raio": w["raio"].value}
                if w["rod"].value:
                    ent.update(rod=True, comp=w["comp"].value)
                layers[nome] = ent
            mapa = {"escala": escala.value,
                    "padrao": {"prof": padrao_prof.value, "raio": padrao_raio.value},
                    "layers": layers}
            return {"dxf": estado["dxf_path"], "mapa": mapa}

        def pre_visualizar() -> None:
            try:
                spec = _spec()
                n = estimar_segmentos(spec, _COMP_ALVO_PREVIA)
                conds = condutores_do_spec(spec)
            except Exception as exc:  # noqa: BLE001
                ui.notify(f"Geometria invalida: {exc}", type="negative")
                return
            estado["preview"] = {"n": n, "condutores": conds}
            preview.refresh()
            preview_meta.refresh()

        def usar() -> None:
            try:
                spec = _spec()
            except Exception as exc:  # noqa: BLE001
                ui.notify(f"Geometria invalida: {exc}", type="negative")
                return
            brita = {"rho_s": rho_s.value, "h_s": h_s.value}
            proj.eletrodo = spec
            proj.falta = {"Ig": ig.value, "t": tf.value, "peso": int(peso.value)}
            if "malha_retangular" in spec:
                proj.malha = params_malha_analitica(
                    spec["malha_retangular"], rho_s=brita["rho_s"], h_s=brita["h_s"])
            else:
                # DXF: sem malha retangular -> IEEE-80 indisponivel, guarda so a brita
                proj.malha = brita
            ui.notify("Malha e falta salvas no projeto.", type="positive")

        with ui.row().classes("items-center justify-between w-full flex-wrap gap-3"):
            with ui.row().classes("items-center gap-3"):
                ui.button("Pre-visualizar", icon="visibility",
                          on_click=pre_visualizar).props("outline")
                ui.button("Usar no projeto", icon="check", on_click=usar)
            ui.button("Ir para o calculo", icon="arrow_forward",
                      on_click=lambda: ui.navigate.to("/calculo")).props("outline")
