"""Moldura comum das paginas: app-shell (gaveta escura + cabecalho) e tema.

Uso:

    @ui.page("/rota")
    async def pagina():
        await ui.context.client.connected()   # libera app.storage.tab
        with moldura("Titulo da pagina", "/rota"):
            ...  # conteudo

O `await connected()` e necessario porque as paginas leem o estado por aba
(`app.storage.tab`), que so existe apos a conexao do cliente.

Este modulo concentra o SISTEMA VISUAL do app (direcao "engenharia moderna"):
shell de aplicacao com navegacao lateral escura, tipografia IBM Plex Sans/Mono,
cartoes claros, tabelas e botoes restilizados. O tema e injetado uma vez por
pagina em `_aplicar_tema()` (chamado dentro de `moldura`). As cores de marca do
Quasar sao alinhadas com `ui.colors(...)`, de modo que os widgets existentes
(botoes, selos `text-positive/negative`, etc.) herdam o novo visual sem mudar a
logica das paginas.
"""

from __future__ import annotations

from contextlib import contextmanager

from nicegui import ui

from gui.estado import obter_projeto

# Paleta da direcao visual (ver tambem o README do handoff de design)
ACENTO = "#1f6feb"

# (rota, rotulo, icone, numero) de cada secao do pipeline (ordem do caminho normal).
# `numero` != None desenha um badge numerado (passos 1/2/3); None usa o icone.
_LINKS = [
    ("/", "Inicio", "home", None),
    ("/estratificacao", "Estratificacao", "layers", "1"),
    ("/malha", "Malha e falta", "grid_on", "2"),
    ("/calculo", "Calculo", "calculate", "3"),
    ("/visualizador", "Visualizador", "insights", None),
]

# (numero, rota, rotulo, chave de conclusao no Projeto) dos passos do pipeline
_PASSOS = [
    (1, "/estratificacao", "Estratificacao", "solo"),
    (2, "/malha", "Malha", "eletrodo"),
    (3, "/calculo", "Calculo", "resultado"),
]

# Folha de estilo do tema (injetada uma vez por pagina). Restiliza primitivos do
# Quasar/NiceGUI (cartoes, tabelas, botoes, gaveta, cabecalho) + utilitarios `es-*`.
_CSS = """
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root { --es-accent: #1f6feb; }

body, .q-page, .nicegui-content {
  font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif;
  color: #0f172a;
  background: #f4f5f7;
}
.q-page-container, .q-layout { background: #f4f5f7; }
.font-mono, .es-mono { font-family: 'IBM Plex Mono', ui-monospace, monospace; }

/* ---- conteudo ---- */
.es-content { max-width: 1080px; margin: 0 auto; padding: 30px 40px; }
.es-eyebrow { font-size: 11.5px; font-weight: 600; letter-spacing: 0.09em;
  text-transform: uppercase; color: var(--es-accent); }
.es-h1 { font-size: 26px; font-weight: 700; letter-spacing: -0.02em; color: #0f172a; line-height: 1.15; }
.es-lead { font-size: 15px; color: #5b6675; line-height: 1.6; max-width: 720px; }
.es-section-title { font-size: 14px; font-weight: 600; color: #0f172a; }

/* ---- cabecalho (barra fina clara com breadcrumb) ---- */
.es-header { background: rgba(244,245,247,0.85) !important; color: #334155 !important;
  box-shadow: none !important; border-bottom: 1px solid #e6e9ee;
  -webkit-backdrop-filter: blur(8px); backdrop-filter: blur(8px); min-height: 56px; }
.es-crumb { font-size: 13px; color: #94a3b8; font-weight: 500; }
.es-crumb b { color: #334155; font-weight: 600; }
.es-pill-sess { display: flex; align-items: center; gap: 8px; padding: 5px 11px;
  border-radius: 20px; background: #fff; border: 1px solid #e6e9ee; font-size: 12px;
  color: #64748b; font-weight: 500; }
.es-dot { width: 7px; height: 7px; border-radius: 50%; background: #16a34a; }

/* ---- gaveta (navegacao escura) ---- */
.es-drawer, .es-drawer .q-drawer__content {
  background: #0e1420 !important; color: #cbd5e1; }
.es-drawer .q-drawer__content { display: flex; flex-direction: column; height: 100%; padding: 0; }
.es-brand { padding: 22px 20px 18px; gap: 12px; border-bottom: 1px solid #1a2230; }
.es-logo { width: 38px; height: 38px; border-radius: 9px; background: var(--es-accent);
  display: flex; flex-direction: column; justify-content: center; gap: 3px; padding: 0 8px; flex: none; }
.es-logo span { height: 3px; border-radius: 2px; background: rgba(255,255,255,0.95); display: block; }
.es-logo span:nth-child(2) { background: rgba(255,255,255,0.6); }
.es-logo span:nth-child(3) { background: rgba(255,255,255,0.35); }
.es-brand-name { font-size: 16px; font-weight: 700; color: #fff; line-height: 1.15; }
.es-brand-sub { font-size: 11px; color: #6b7a90; font-weight: 500; }
.es-navhead { font-size: 10.5px; letter-spacing: 0.09em; text-transform: uppercase;
  color: #5b6b82; font-weight: 600; padding: 16px 18px 6px; }
.es-navlink { text-decoration: none; display: block; }
.es-navitem { align-items: center; gap: 11px; padding: 9px 11px; border-radius: 8px;
  margin: 1px 8px; color: #94a3b8; font-size: 13.5px; font-weight: 500;
  transition: background .12s, color .12s; flex-wrap: nowrap; }
.es-navitem:hover { background: rgba(255,255,255,0.05); color: #e2e8f0; }
.es-navitem-active { background: rgba(255,255,255,0.09); color: #fff;
  box-shadow: inset 3px 0 0 var(--es-accent); }
.es-navnum { width: 22px; height: 22px; border-radius: 6px; background: rgba(255,255,255,0.07);
  display: flex; align-items: center; justify-content: center;
  font-family: 'IBM Plex Mono'; font-size: 11.5px; font-weight: 600; flex: none; }
.es-navitem .q-icon { font-size: 18px; width: 22px; }
.es-navsep { height: 1px; background: #1a2230; margin: 12px 18px; }
.es-foot { margin-top: auto; padding: 16px 18px 18px; border-top: 1px solid #1a2230; gap: 8px; }
.es-foot-label { font-size: 11px; color: #7a8aa0; font-weight: 500; }
.es-foot-count { font-size: 11px; color: #cbd5e1; font-family: 'IBM Plex Mono'; }
.es-foot-track { height: 5px; border-radius: 3px; background: rgba(255,255,255,0.08); overflow: hidden; }
.es-foot-fill { height: 100%; border-radius: 3px; background: var(--es-accent); }

/* ---- cartoes ---- */
.q-card { border-radius: 12px !important; border: 1px solid #e6e9ee;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04) !important; }
.es-metric { padding: 15px 17px !important; gap: 6px; min-width: 140px; }
.es-metric-label { font-size: 11px; font-weight: 600; letter-spacing: 0.05em;
  text-transform: uppercase; color: #7c8696; }
.es-metric-value { font-family: 'IBM Plex Mono'; font-size: 25px; font-weight: 600;
  color: #0f172a; letter-spacing: -0.02em; line-height: 1.1; }
.es-metric-value.es-pos { color: #117a56; }
.es-metric-value.es-neg { color: #c4332b; }
.es-metric-unit { font-size: 13px; color: #94a3b8; font-family: 'IBM Plex Mono'; }
.es-metric-sub { font-size: 11.5px; color: #94a3b8; font-family: 'IBM Plex Mono'; }

/* ---- selo de veredito ---- */
.es-selo { align-items: center; gap: 8px; padding: 9px 18px; border-radius: 11px;
  font-weight: 700; font-size: 16px; letter-spacing: 0.02em; width: fit-content; }
.es-selo-ok { background: #e7f6ef; color: #117a56; border: 1px solid #bfe3d1; }
.es-selo-no { background: #fdecea; color: #c4332b; border: 1px solid #f3c7c2; }

/* ---- barra de passos ---- */
.es-steps { background: #fff; border: 1px solid #e6e9ee; border-radius: 10px;
  padding: 6px; width: fit-content; }
.es-step { align-items: center; gap: 7px; padding: 7px 13px; border-radius: 7px;
  font-size: 13px; font-weight: 600; }
.es-step-active { background: var(--es-accent); color: #fff; }
.es-step-done { background: #e7f6ef; color: #117a56; }
.es-step-todo { background: transparent; color: #94a3b8; }
.es-step-num { font-family: 'IBM Plex Mono'; }
.es-step-sep { color: #cbd5e1; }

/* ---- linhas de estado (pagina inicial) ---- */
.es-statrow { align-items: center; gap: 13px; padding: 13px 4px; border-bottom: 1px solid #f2f4f6; }
.es-statrow:last-child { border-bottom: none; }
.es-badge { font-size: 11px; font-weight: 600; padding: 3px 9px; border-radius: 5px; }
.es-badge-ok { color: #16a34a; background: #e7f6ef; }
.es-badge-no { color: #94a3b8; background: #f1f3f5; }

/* ---- botoes ---- */
.q-btn { border-radius: 9px; text-transform: none; font-weight: 600; letter-spacing: 0; }

/* ---- tabelas ---- */
.q-table { border-radius: 10px; }
.q-table thead th { text-transform: uppercase; font-size: 11px; letter-spacing: 0.05em;
  color: #7c8696; font-weight: 600; background: #fafbfc; }
.q-table tbody td { font-size: 13px; color: #334155; font-family: 'IBM Plex Mono'; }
.q-table tbody td:first-child, .q-table thead th:first-child { font-family: 'IBM Plex Sans'; }

/* ---- inputs / abas ---- */
.q-field--outlined .q-field__control { border-radius: 8px; }
.q-tab { text-transform: none; font-weight: 600; }

/* ---- divisoria fina ---- */
.es-div { height: 1px; background: #eef0f3; width: 100%; }

/* ---- cabecalho de cartao emoldurado (plot/previa) ---- */
.es-card-head { align-items: center; justify-content: space-between; width: 100%;
  padding: 13px 16px; border-bottom: 1px solid #eef0f3; }
.es-card-head-title { font-size: 13px; font-weight: 600; color: #334155; }
.es-card-meta { font-size: 11.5px; color: #64748b; font-family: 'IBM Plex Mono'; }

/* ---- legenda da curva ---- */
.es-legend { gap: 14px; font-size: 11px; color: #94a3b8; font-family: 'IBM Plex Mono'; }
.es-legend-item { align-items: center; gap: 5px; }
.es-legend-dot { width: 9px; height: 9px; border-radius: 50%; background: #94a3b8; }
.es-legend-line { width: 12px; height: 3px; border-radius: 2px; background: var(--es-accent); }

/* ---- campo numerico (rotulo mono acima + valor mono + sufixo) ---- */
.es-field-label { font-size: 11.5px; font-weight: 600; color: #64748b;
  font-family: 'IBM Plex Mono'; }
.es-num .q-field__control { border-radius: 8px; min-height: 40px; }
.es-num .q-field__control:before { border-color: #d6dbe2; }
.es-num input { font-family: 'IBM Plex Mono'; font-size: 14px; color: #0f172a; }
.es-num .q-field__suffix, .es-num .q-field__append {
  color: #aab2bf; font-family: 'IBM Plex Mono'; font-size: 12px; }

/* ---- controle segmentado (ui.toggle restilizado) ---- */
.es-segmented.q-btn-group { box-shadow: none; border: none; background: #f1f3f5;
  border-radius: 8px; padding: 3px; gap: 2px; }
.es-segmented .q-btn { border: none !important; border-radius: 6px !important;
  min-height: 0 !important; padding: 6px 13px !important; font-size: 13px;
  font-weight: 500; color: #64748b; box-shadow: none !important; }
.es-segmented .q-btn .q-btn__content { padding: 0; }
.es-segmented .q-btn:not(.q-btn--flat), .es-segmented .q-btn--active {
  background: #fff; color: #0f172a; font-weight: 600;
  box-shadow: 0 1px 2px rgba(0,0,0,0.06) !important; }

/* ---- dropzone (importar arquivo) ---- */
.es-dropzone { border: 1.5px dashed #d0d6de; border-radius: 11px; background: #fafbfc;
  cursor: pointer; display: flex; transition: background .12s, border-color .12s; }
.es-dropzone:hover { background: #f4f7fb; border-color: #bcc6d3; }
.es-dz-col { flex-direction: column; align-items: center; text-align: center;
  padding: 18px 16px; gap: 6px; }
.es-dz-row { flex-direction: row; align-items: center; padding: 22px; gap: 14px; }
.es-dz-text { display: flex; flex-direction: column; gap: 3px; }
.es-dz-col .es-dz-text { align-items: center; }
.es-dz-title { font-size: 13.5px; font-weight: 600; color: #334155; }
.es-dz-sub { font-size: 11.5px; color: #94a3b8; }

/* ---- variantes de borda dos cartoes de metrica ---- */
.es-metric-ok { border-color: #bfe3d1 !important; }
.es-metric-no { border-color: #f3c7c2 !important; }
"""


def _aplicar_tema() -> None:
    """Injeta cores de marca, fontes e a folha de estilo do tema (uma vez por pagina)."""
    ui.colors(primary=ACENTO, positive="#16a34a", negative="#c4332b", warning="#9a6700")
    ui.add_css(_CSS)


def _passo_concluido(proj, chave: str) -> bool:
    """Diz se um passo ja produziu saida no projeto."""
    if chave == "resultado":
        return proj.resultado_analitico is not None or proj.resultado_numerico is not None
    return getattr(proj, chave) is not None


def cabecalho(eyebrow: str, titulo: str, lead: str | None = None) -> None:
    """Cabecalho padrao de pagina: eyebrow (cor de acento) + titulo + lead opcional."""
    with ui.column().classes("gap-1 w-full"):
        ui.label(eyebrow).classes("es-eyebrow")
        ui.label(titulo).classes("es-h1")
        if lead:
            ui.label(lead).classes("es-lead")


def barra_passos(atual: int) -> None:
    """Barra de progresso do caminho normal: passo atual destacado, check nos prontos.

    Cada passo e um link para a sua pagina (a navegacao continua livre).
    """
    proj = obter_projeto()
    with ui.row().classes("es-steps items-center gap-1"):
        for i, (num, rota, rotulo, chave) in enumerate(_PASSOS):
            if i:
                ui.icon("chevron_right").classes("es-step-sep")
            feito = _passo_concluido(proj, chave)
            if num == atual:
                cls = "es-step es-step-active"
            elif feito:
                cls = "es-step es-step-done"
            else:
                cls = "es-step es-step-todo"
            with ui.link(target=rota).classes("no-underline"):
                with ui.row().classes(cls):
                    if feito and num != atual:
                        ui.icon("check").classes("text-sm")
                    else:
                        ui.label(str(num)).classes("es-step-num")
                    ui.label(rotulo)


def botao_proximo(rota: str, rotulo: str) -> None:
    """Botao 'Proximo passo ->' que navega para a proxima etapa do pipeline."""
    with ui.row().classes("w-full justify-end"):
        ui.button(rotulo, icon="arrow_forward",
                  on_click=lambda: ui.navigate.to(rota)).props("outline")


def _gaveta(rota_ativa: str | None) -> None:
    """Desenha o conteudo da gaveta escura: marca + nav numerada + progresso."""
    proj = obter_projeto()
    feitos = sum(1 for _, _, _, ch in _PASSOS if _passo_concluido(proj, ch))
    pct = round(feitos / len(_PASSOS) * 100)

    with ui.row().classes("es-brand items-center"):
        ui.html('<div class="es-logo"><span></span><span></span><span></span></div>')
        with ui.column().classes("gap-0"):
            ui.label("EarthSolver").classes("es-brand-name")
            ui.label("Analise de aterramento").classes("es-brand-sub")

    ui.label("Pipeline").classes("es-navhead")
    for rota, rotulo, icone, num in _LINKS:
        if rota == "/visualizador":
            ui.html('<div class="es-navsep"></div>')
        ativo = rota == rota_ativa
        cls = "es-navitem" + (" es-navitem-active" if ativo else "")
        with ui.link(target=rota).classes("es-navlink"):
            with ui.row().classes(cls):
                if num is not None:
                    ui.label(num).classes("es-navnum")
                else:
                    ui.icon(icone)
                ui.label(rotulo)

    with ui.column().classes("es-foot w-full"):
        with ui.row().classes("items-center justify-between w-full"):
            ui.label("Projeto · sessao").classes("es-foot-label")
            ui.label(f"{feitos}/{len(_PASSOS)}").classes("es-foot-count")
        with ui.element("div").classes("es-foot-track w-full"):
            ui.element("div").classes("es-foot-fill").style(f"width:{pct}%")


@contextmanager
def moldura(titulo: str, rota: str | None = None):
    """Renderiza shell (gaveta escura + cabecalho) e devolve o container de conteudo.

    `rota` destaca o item ativo na navegacao (ex.: "/calculo"); opcional para
    compatibilidade.
    """
    _aplicar_tema()

    with ui.left_drawer(value=True, bordered=True).props("width=248").classes("es-drawer"):
        _gaveta(rota)

    with ui.header(elevated=False).classes("es-header items-center justify-between px-10"):
        ui.html(f'<span class="es-crumb">EarthSolver&nbsp;&nbsp;/&nbsp;&nbsp;<b>{titulo}</b></span>')
        with ui.element("div").classes("es-pill-sess"):
            ui.html('<span class="es-dot"></span>')
            ui.label("Estado salvo na sessao")

    container = ui.column().classes("es-content w-full gap-6")
    with container:
        yield container
