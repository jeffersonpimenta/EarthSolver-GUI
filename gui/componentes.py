"""Componentes de UI reutilizados entre paginas (cartoes de resultado).

O visual segue a direcao "engenharia moderna" (ver `gui/layout.py`): cartoes de
metrica com rotulo em maiusculas, valor grande monoespacado e cor de estado;
selo de veredito (APROVADO/REPROVADO) em destaque. As classes `es-*` sao
definidas na folha de estilo do tema em `layout.py`.
"""

from __future__ import annotations

from nicegui import ui


def selo(aprovado: bool) -> None:
    """Selo de veredito em destaque: APROVADO (verde) ou REPROVADO (vermelho)."""
    cls = "es-selo es-selo-ok" if aprovado else "es-selo es-selo-no"
    with ui.row().classes(cls):
        ui.icon("check_circle" if aprovado else "cancel").classes("text-lg")
        ui.label("APROVADO" if aprovado else "REPROVADO")


def cartao(titulo: str, valor: str, sub: str = "", ok: bool | None = None) -> None:
    """Cartao de metrica: rotulo maiusculo, valor grande em mono e subtexto opcional.

    `ok=True/False` tinge o valor de verde/vermelho (limite atingido ou nao).
    """
    with ui.card().classes("es-metric"):
        ui.label(titulo).classes("es-metric-label")
        cor = "" if ok is None else (" es-pos" if ok else " es-neg")
        ui.label(valor).classes("es-metric-value" + cor)
        if sub:
            ui.label(sub).classes("es-metric-sub")


def cartoes_resultado(res: dict) -> None:
    """Bloco padrao de resultado de aterramento: veredito + Rg/GPR/Em/Es/segmentos.

    Aceita o dicionario de resultado tanto do estudo analitico quanto do numerico
    (campos ausentes sao simplesmente omitidos).
    """
    aprovado = res.get("aprovado")
    if aprovado is not None:
        selo(bool(aprovado))
    with ui.row().classes("gap-4 w-full"):
        cartao("Rg", f"{res['Rg']:.3f}", "Ohm")
        cartao("GPR", f"{res['GPR']:.1f}", "V")
        if "Em" in res:
            cartao("Em (toque)", f"{res['Em']:.1f}", f"limite {res['E_toque']:.1f} V",
                   ok=res.get("toque_ok"))
        if "Es" in res:
            cartao("Es (passo)", f"{res['Es']:.1f}", f"limite {res['E_passo']:.1f} V",
                   ok=res.get("passo_ok"))
        if "n_segmentos" in res:
            cartao("Segmentos", str(res["n_segmentos"]), "")


def num_json(o):
    """default= para json.dumps: converte escalares numpy em tipos nativos."""
    return o.item() if hasattr(o, "item") else str(o)


def _fmt_eta(seg) -> str:
    """Formata segundos restantes: '12s' / '1m03s' / '--' (None/NaN/negativo).

    Espelha `earthsolver.progresso._fmt_eta` (o evento traz `eta` em segundos).
    """
    if seg is None or seg != seg or seg < 0:        # None ou NaN ou negativo
        return "--"
    seg = int(round(seg))
    if seg < 60:
        return f"{seg}s"
    return f"{seg // 60}m{seg % 60:02d}s"


class BarraProgresso:
    """Barra de progresso + ETA reutilizavel (calculo numerico e convergencia).

    Cria os widgets no container atual (escondidos). `iniciar()` mostra e zera;
    `aplicar(ev)` consome um evento de progresso do nucleo
    (`{fracao, fase, eta, ...}`); `encerrar()` esconde de novo.
    """

    def __init__(self) -> None:
        self._cont = ui.column().classes("w-full gap-1")
        with self._cont:
            self._barra = ui.linear_progress(value=0.0, show_value=False) \
                .props("instant-feedback rounded color=primary")
            self._rotulo = ui.label("").classes("text-sm text-grey font-mono")
        self._cont.set_visibility(False)

    def iniciar(self) -> None:
        self._barra.value = 0.0
        self._rotulo.text = "iniciando..."
        self._cont.set_visibility(True)

    def aplicar(self, ev: dict) -> None:
        frac = float(ev.get("fracao", 0.0))
        self._barra.value = frac
        fase = ev.get("fase") or ""
        self._rotulo.text = f"{fase} · {frac * 100:.0f}% · ETA {_fmt_eta(ev.get('eta'))}"

    def encerrar(self) -> None:
        self._cont.set_visibility(False)


def barra_progresso() -> BarraProgresso:
    """Cria uma BarraProgresso no container atual (ver a classe)."""
    return BarraProgresso()
