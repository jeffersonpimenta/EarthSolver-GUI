"""Moldura comum das paginas: cabecalho + gaveta de navegacao.

Uso:

    @ui.page("/rota")
    async def pagina():
        await ui.context.client.connected()   # libera app.storage.tab
        with moldura("Titulo da pagina"):
            ...  # conteudo

O `await connected()` e necessario porque as paginas leem o estado por aba
(`app.storage.tab`), que so existe apos a conexao do cliente.
"""

from __future__ import annotations

from contextlib import contextmanager

from nicegui import ui

from gui.estado import obter_projeto

# (rota, rotulo, icone) de cada secao do pipeline (na ordem do caminho normal)
_LINKS = [
    ("/", "Inicio", "home"),
    ("/estratificacao", "1. Estratificacao", "layers"),
    ("/malha", "2. Malha", "grid_on"),
    ("/calculo", "3. Calculo", "calculate"),
    ("/visualizador", "Visualizador", "insights"),
]

# (numero, rota, rotulo, chave de conclusao no Projeto) dos passos do pipeline
_PASSOS = [
    (1, "/estratificacao", "Estratificacao", "solo"),
    (2, "/malha", "Malha", "eletrodo"),
    (3, "/calculo", "Calculo", "resultado"),
]


def _passo_concluido(proj, chave: str) -> bool:
    """Diz se um passo ja produziu saida no projeto."""
    if chave == "resultado":
        return proj.resultado_analitico is not None or proj.resultado_numerico is not None
    return getattr(proj, chave) is not None


def barra_passos(atual: int) -> None:
    """Barra de progresso do caminho normal: passo atual destacado, ✓ nos prontos.

    Cada passo e um link para a sua pagina (a navegacao continua livre).
    """
    proj = obter_projeto()
    with ui.row().classes("items-center gap-1 w-full flex-wrap"):
        for i, (num, rota, rotulo, chave) in enumerate(_PASSOS):
            if i:
                ui.icon("chevron_right").classes("text-slate-400")
            feito = _passo_concluido(proj, chave)
            if num == atual:
                cor = "bg-blue-600 text-white"
            elif feito:
                cor = "bg-green-600 text-white"
            else:
                cor = "bg-slate-200 text-slate-600"
            with ui.link(target=rota).classes("no-underline"):
                with ui.row().classes(f"items-center gap-1 px-3 py-1 rounded-full {cor}"):
                    if feito:
                        ui.icon("check")
                    else:
                        ui.label(str(num)).classes("font-bold")
                    ui.label(rotulo)


def botao_proximo(rota: str, rotulo: str) -> None:
    """Botao 'Proximo passo ->' que navega para a proxima etapa do pipeline."""
    with ui.row().classes("w-full justify-end"):
        ui.button(rotulo, icon="arrow_forward",
                  on_click=lambda: ui.navigate.to(rota)).props("outline")


@contextmanager
def moldura(titulo: str):
    """Renderiza cabecalho + gaveta e devolve o container de conteudo da pagina."""
    drawer = ui.left_drawer(value=True).classes("bg-slate-100")
    with drawer:
        ui.label("EarthSolver").classes("text-xl font-bold q-pa-md")
        for rota, rotulo, icone in _LINKS:
            with ui.link(target=rota).classes("w-full no-underline text-black"):
                with ui.row().classes("items-center gap-2 q-pa-sm"):
                    ui.icon(icone)
                    ui.label(rotulo)

    with ui.header().classes("items-center"):
        ui.button(on_click=drawer.toggle, icon="menu").props("flat color=white")
        ui.label(titulo).classes("text-lg")

    container = ui.column().classes("w-full max-w-screen-lg mx-auto p-4 gap-4")
    with container:
        yield container
