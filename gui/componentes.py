"""Componentes de UI reutilizados entre paginas (cartoes de resultado)."""

from __future__ import annotations

from nicegui import ui


def cartao(titulo: str, valor: str, sub: str = "", ok: bool | None = None) -> None:
    """Cartao compacto: titulo, valor em destaque e subtexto opcional."""
    with ui.card().classes("min-w-[130px]"):
        ui.label(titulo).classes("text-sm text-grey")
        cor = "" if ok is None else (" text-positive" if ok else " text-negative")
        ui.label(valor).classes("text-xl font-bold" + cor)
        if sub:
            ui.label(sub).classes("text-xs text-grey")


def cartoes_resultado(res: dict) -> None:
    """Bloco padrao de resultado de aterramento: veredito + Rg/GPR/Em/Es/segmentos.

    Aceita o dicionario de resultado tanto do estudo analitico quanto do numerico
    (campos ausentes sao simplesmente omitidos).
    """
    aprovado = res.get("aprovado")
    if aprovado is not None:
        ui.label("APROVADO" if aprovado else "REPROVADO") \
            .classes(f"text-2xl font-bold text-{'positive' if aprovado else 'negative'}")
    with ui.row().classes("gap-4"):
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
                .props("instant-feedback")
            self._rotulo = ui.label("").classes("text-sm text-grey")
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
