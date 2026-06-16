"""Pagina inicial: apresentacao + carregar/salvar projeto (entrada do pipeline)."""

from __future__ import annotations

import json

from nicegui import ui

from gui import recursos
from gui.estado import Projeto, obter_projeto
from gui.layout import cabecalho, moldura

# (campo do Projeto, rotulo, rota do passo) na ordem do caminho normal
_SECOES = [
    ("sondagem", "Sondagem (Wenner)", "/estratificacao"),
    ("solo", "Modelo de solo", "/estratificacao"),
    ("eletrodo", "Geometria da malha", "/malha"),
    ("malha", "Parametros IEEE-80 / brita", "/malha"),
    ("falta", "Corrente de falta", "/malha"),
]

_LEAD = ("Estratificacao do solo (Wenner / NBR 7117), estudo analitico pelo IEEE Std 80 "
         "e solver numerico de segmentacao de condutores. Comece por qualquer etapa ou "
         "carregue o projeto de exemplo — o estado e compartilhado entre as paginas "
         "durante a sessao.")

# (numero, rota, titulo, descricao) dos cartoes do pipeline
_PIPELINE = [
    ("1", "/estratificacao", "Estratificacao",
     "Ajusta o modelo de solo em camadas a partir da sondagem de Wenner."),
    ("2", "/malha", "Malha e falta",
     "Define a geometria do eletrodo (parametros ou DXF) e a corrente de falta."),
    ("3", "/calculo", "Calculo",
     "IEEE-80, numerico ou ambos, com veredito de toque e passo."),
]


@ui.page("/")
async def pagina_inicio() -> None:
    await ui.context.client.connected()
    proj = obter_projeto()

    with moldura("Inicio", "/"):
        cabecalho("Suite de aterramento eletrico", "Bem-vindo ao EarthSolver", _LEAD)

        with ui.row().classes("w-full gap-5 items-start no-wrap"):
            # ----------------------------------------------- estado do projeto
            with ui.card().classes("flex-1 p-0 overflow-hidden"):
                with ui.row().classes("items-center justify-between w-full px-5 py-4") \
                        .style("border-bottom:1px solid #eef0f3"):
                    ui.label("Estado do projeto").classes("es-section-title")
                    ui.label("clique para ir ao passo").classes("text-xs text-grey")

                @ui.refreshable
                def status() -> None:
                    with ui.column().classes("w-full gap-0 px-5"):
                        for campo, rotulo, rota in _SECOES:
                            carregado = getattr(proj, campo) is not None
                            with ui.link(target=rota).classes("no-underline w-full"):
                                with ui.row().classes("es-statrow w-full no-wrap"):
                                    ui.icon("check_circle" if carregado else "radio_button_unchecked") \
                                        .classes("text-positive" if carregado else "text-grey-4")
                                    ui.label(rotulo).classes("flex-1 text-sm").style("color:#1f2937")
                                    ui.label("carregado" if carregado else "vazio") \
                                        .classes("es-badge " + ("es-badge-ok" if carregado else "es-badge-no"))

                status()

            # --------------------------------------------------------- projeto
            with ui.card().classes("w-80 p-5 gap-3"):
                ui.label("Projeto").classes("es-section-title")

                def carregar_exemplo() -> None:
                    d = json.loads(recursos.caminho_exemplo("projeto.json").read_text(encoding="utf-8"))
                    for campo in ("sondagem", "malha", "falta"):
                        setattr(proj, campo, d.get(campo))
                    status.refresh()
                    ui.notify("Projeto exemplo carregado.", type="positive")

                def baixar() -> None:
                    ui.download.content(json.dumps(proj.to_dict(), indent=2, ensure_ascii=False),
                                        "projeto.json")

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

                ui.button("Carregar projeto exemplo", icon="science",
                          on_click=carregar_exemplo).classes("w-full")
                ui.button("Baixar projeto atual", icon="download",
                          on_click=baixar).props("outline").classes("w-full")
                ui.upload(label="Importar projeto.json", on_upload=importar, auto_upload=True) \
                    .props("accept=.json flat bordered").classes("w-full")

        # ------------------------------------------------------------ pipeline
        ui.label("O pipeline").classes("es-eyebrow").style("color:#7c8696;margin-top:8px")
        with ui.row().classes("w-full gap-4 no-wrap"):
            for num, rota, titulo, desc in _PIPELINE:
                with ui.card().classes("flex-1 p-5 gap-2 cursor-pointer") \
                        .on("click", lambda r=rota: ui.navigate.to(r)):
                    ui.html(f'<div style="width:34px;height:34px;border-radius:8px;'
                            f'background:#eef4ff;color:var(--es-accent);display:flex;'
                            f'align-items:center;justify-content:center;font-family:\'IBM Plex Mono\';'
                            f'font-weight:600;font-size:15px">{num}</div>')
                    ui.label(titulo).classes("text-base font-semibold").style("color:#0f172a")
                    ui.label(desc).classes("text-xs").style("color:#7c8696;line-height:1.5")
