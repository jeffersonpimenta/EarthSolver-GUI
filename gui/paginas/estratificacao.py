"""Pagina de estratificacao: sondagem de Wenner -> modelo de solo + curva."""

from __future__ import annotations

import json

from nicegui import run, ui

from gui import graficos
from gui.estado import obter_projeto
from gui.layout import barra_passos, botao_proximo, cabecalho, moldura
from gui.solver import rodar_estratificacao
from gui.sondagem import parse_sondagem


@ui.page("/estratificacao")
async def pagina_estratificacao() -> None:
    await ui.context.client.connected()
    proj = obter_projeto()
    estado: dict = {"res": None, "entrada": None}

    # pre-preenche a partir da sondagem do projeto, se houver
    texto_inicial = ""
    if proj.sondagem:
        s = proj.sondagem
        vals = s.get("resistencias") or s.get("resistividades") or []
        cab = "a,rho_a" if s.get("resistividades") else "a,R"
        linhas = [cab] + [f"{a},{v}"
                          for a, v in zip(s.get("espacamentos", []), vals, strict=False)]
        texto_inicial = "\n".join(linhas)

    with moldura("Estratificacao", "/estratificacao"):
        cabecalho("Passo 1", "Estratificacao do solo")
        barra_passos(1)

        with ui.card().classes("w-full p-5 gap-3"):
            ui.label("Sondagem de Wenner").classes("es-section-title")
            ui.markdown("Cole ou envie a sondagem (`espacamento, valor` por linha; "
                        "valor = resistencia em Ohm, ou rho aparente se o cabecalho disser).") \
                .classes("text-sm text-grey")

            entrada = ui.textarea("Sondagem", value=texto_inicial) \
                .props("outlined rows=8").classes("w-full font-mono")

            async def importar_csv(e) -> None:
                entrada.value = (await e.file.text()).strip()
                ui.notify(f"{e.file.name} carregado.", type="positive")

            ui.upload(label="Importar CSV", on_upload=importar_csv, auto_upload=True) \
                .props("accept=.csv,.txt flat bordered").classes("max-w-md")

            with ui.row().classes("items-center gap-4"):
                modo = ui.radio({"auto": "Automatico", "fixo": "Numero fixo"},
                                value="auto").props("inline")
                n_fixo = ui.number("Camadas", value=2, min=1, max=6, format="%d").classes("w-28")
                max_cam = ui.number("Max (auto)", value=3, min=1, max=6, format="%d").classes("w-28")

            with ui.row().classes("items-center gap-3"):
                botao = ui.button("Estratificar", icon="play_arrow")
                spin = ui.spinner(size="lg").classes("hidden")

        @ui.refreshable
        def resultado() -> None:
            res = estado["res"]
            if not res:
                return
            aj = res["ajuste"]
            solo = res["solo"]
            with ui.card().classes("w-full p-5 gap-4"):
                with ui.row().classes("items-center justify-between w-full"):
                    ui.label("Modelo de solo ajustado").classes("es-section-title")
                    cor = "es-badge-ok" if aj["convergiu"] else "es-badge-no"
                    with ui.row().classes("items-center gap-3"):
                        ui.label(f"{aj['n_camadas']} camada(s) · "
                                 f"{'convergiu' if aj['convergiu'] else 'NAO convergiu'}") \
                            .classes("es-badge " + cor)
                        ui.label(f"RMS {aj['rms']:.2f}%").classes("text-sm text-grey font-mono")

                esp = solo.get("espessura", [])
                linhas = []
                for i, rho in enumerate(solo["rho"]):
                    espessura = f"{esp[i]:.2f}" if i < len(esp) else "infinita"
                    linhas.append({"camada": i + 1, "rho": round(rho, 2), "espessura": espessura})
                ui.table(columns=[
                    {"name": "camada", "label": "Camada", "field": "camada", "align": "left"},
                    {"name": "rho", "label": "rho (Ohm.m)", "field": "rho", "align": "left"},
                    {"name": "espessura", "label": "Espessura (m)", "field": "espessura", "align": "left"},
                ], rows=linhas).props("flat").classes("w-full")

                c = res["curva"]
                ui.plotly(graficos.curva_wenner(c["a"], c["rho_medido"],
                                                c["a_fit"], c["rho_fit"])).classes("w-full")

                def usar() -> None:
                    proj.solo = solo
                    proj.sondagem = estado["entrada"]
                    ui.notify("Solo salvo no projeto.", type="positive")

                def baixar() -> None:
                    ui.download.content(json.dumps(solo, indent=2, ensure_ascii=False), "solo.json")

                with ui.row().classes("gap-3"):
                    ui.button("Usar no projeto", icon="check", on_click=usar)
                    ui.button("Baixar solo.json", icon="download", on_click=baixar).props("flat")

        async def estratificar() -> None:
            try:
                espac, valores, eh_rho = parse_sondagem(entrada.value or "")
            except Exception as exc:  # noqa: BLE001
                ui.notify(f"Sondagem invalida: {exc}", type="negative")
                return
            camadas = "auto" if modo.value == "auto" else int(n_fixo.value)
            botao.disable()
            spin.classes(remove="hidden")
            try:
                res = await run.cpu_bound(rodar_estratificacao, espac, valores,
                                          eh_rho, camadas, int(max_cam.value))
            except Exception as exc:  # noqa: BLE001
                ui.notify(f"Falha na estratificacao: {exc}", type="negative")
            else:
                chave = "resistividades" if eh_rho else "resistencias"
                estado["entrada"] = {"espacamentos": espac, chave: valores,
                                     "camadas": camadas, "max_camadas": int(max_cam.value)}
                estado["res"] = res
                resultado.refresh()
                ui.notify("Estratificacao concluida.", type="positive")
            finally:
                spin.classes(add="hidden")
                botao.enable()

        botao.on_click(estratificar)
        resultado()
        botao_proximo("/malha", "Ir para a malha")
