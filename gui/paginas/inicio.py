"""Pagina inicial: apresentacao + carregar/salvar projeto (entrada do pipeline)."""

from __future__ import annotations

import json

from nicegui import ui

from gui import recursos
from gui.estado import Projeto, obter_projeto
from gui.layout import moldura

# (campo do Projeto, rotulo, rota do passo) na ordem do caminho normal
_SECOES = [
    ("sondagem", "Sondagem (Wenner)", "/estratificacao"),
    ("solo", "Modelo de solo", "/estratificacao"),
    ("eletrodo", "Geometria da malha", "/malha"),
    ("malha", "Parametros IEEE-80 / brita", "/malha"),
    ("falta", "Corrente de falta", "/malha"),
]

_INTRO = """
## EarthSolver

Suite de analise de aterramento eletrico: **estratificacao** do solo (Wenner /
NBR 7117), **estudo analitico** pelo IEEE Std 80 e **solver numerico** de
segmentacao de condutores (geometria arbitraria, inclusive importada de DXF).

Esta interface conduz o pipeline completo: comece em uma secao qualquer ou
carregue o projeto de exemplo abaixo. O estado e compartilhado entre as paginas
durante a sessao.
"""


@ui.page("/")
async def pagina_inicio() -> None:
    await ui.context.client.connected()
    proj = obter_projeto()

    with moldura("EarthSolver"):
        ui.markdown(_INTRO)

        @ui.refreshable
        def status() -> None:
            ui.label("Estado do projeto (clique para ir ao passo)").classes("text-lg font-bold")
            for campo, rotulo, rota in _SECOES:
                carregado = getattr(proj, campo) is not None
                with ui.link(target=rota).classes("no-underline text-black"):
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("check_circle" if carregado else "radio_button_unchecked",
                                color="positive" if carregado else "grey")
                        ui.label(f"{rotulo}: {'carregado' if carregado else 'vazio'}")

        def carregar_exemplo() -> None:
            d = json.loads(recursos.caminho_exemplo("projeto.json").read_text(encoding="utf-8"))
            for campo in ("sondagem", "malha", "falta"):
                setattr(proj, campo, d.get(campo))
            status.refresh()
            ui.notify("Projeto exemplo carregado.", type="positive")

        async def importar(e) -> None:
            try:
                d = await e.file.json()
            except Exception as exc:  # noqa: BLE001
                ui.notify(f"JSON invalido: {exc}", type="negative")
                return
            novo = Projeto.from_dict(d)
            for campo, _, _ in _SECOES:
                setattr(proj, campo, getattr(novo, campo))
            status.refresh()
            ui.notify("Projeto importado.", type="positive")

        def baixar() -> None:
            ui.download.content(json.dumps(proj.to_dict(), indent=2, ensure_ascii=False),
                                "projeto.json")

        with ui.row().classes("items-center gap-3"):
            ui.button("Carregar projeto exemplo", icon="science", on_click=carregar_exemplo)
            ui.button("Baixar projeto atual", icon="download", on_click=baixar)
        ui.upload(label="Importar projeto.json", on_upload=importar, auto_upload=True) \
            .props("accept=.json flat bordered").classes("max-w-md")

        ui.separator()
        status()
