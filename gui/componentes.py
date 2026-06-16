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


def cartao(titulo: str, valor: str, unit: str = "", sub: str = "", ok: bool | None = None) -> None:
    """Cartao de metrica: rotulo maiusculo, valor grande em mono e subtexto opcional.

    `unit` aparece na mesma baseline do valor (ex.: Ohm/V); `sub` e a linha mono
    abaixo (ex.: 'limite 838.1 V'). `ok=True/False` tinge o valor de verde/vermelho
    e adiciona a borda de estado ao cartao (limite atingido ou nao).
    """
    extra = "" if ok is None else (" es-metric-ok" if ok else " es-metric-no")
    with ui.card().classes("es-metric" + extra):
        ui.label(titulo).classes("es-metric-label")
        cor = "" if ok is None else (" es-pos" if ok else " es-neg")
        with ui.row().classes("items-baseline gap-1"):
            ui.label(valor).classes("es-metric-value" + cor)
            if unit:
                ui.label(unit).classes("es-metric-unit")
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
    with ui.row().classes("gap-4 w-full items-stretch"):
        cartao("Rg", f"{res['Rg']:.3f}", unit="Ohm")
        cartao("GPR", f"{res['GPR']:.1f}", unit="V")
        if "Em" in res:
            cartao("Em (toque)", f"{res['Em']:.1f}", unit="V",
                   sub=f"limite {res['E_toque']:.1f} V", ok=res.get("toque_ok"))
        if "Es" in res:
            cartao("Es (passo)", f"{res['Es']:.1f}", unit="V",
                   sub=f"limite {res['E_passo']:.1f} V", ok=res.get("passo_ok"))
        if "n_segmentos" in res:
            cartao("Segmentos", str(res["n_segmentos"]))


def campo_num(label: str, value, *, unit: str = "", **kwargs):
    """Campo numerico no estilo do modelo: rotulo mono acima + input mono + unidade.

    Devolve o `ui.number` para o chamador ler `.value`. `unit` vira o sufixo do
    campo (ex.: 'm', 'A'); `kwargs` extra repassam para `ui.number` (min, max...).
    """
    with ui.column().classes("gap-1.5"):
        ui.label(label).classes("es-field-label")
        campo = ui.number(value=value, **kwargs).props("outlined dense").classes("es-num w-full")
        if unit:
            campo.props(f'suffix={unit}')
    return campo


def segmented(opcoes: dict, value):
    """Controle segmentado (pilulas) no estilo do modelo, sobre `ui.toggle`.

    Devolve o `ui.toggle` (`.value`). Reuso: Modo (estratificacao) e Metodo (calculo).
    """
    return ui.toggle(opcoes, value=value).props("no-caps unelevated").classes("es-segmented")


# SVGs equivalentes aos do prototipo (upload / arquivo) usados nas dropzones.
_SVG_UPLOAD = ('<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" '
               'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
               '<path d="M12 16V4"></path><path d="M8 8l4-4 4 4"></path>'
               '<path d="M4 16v3a1 1 0 001 1h14a1 1 0 001-1v-3"></path></svg>')
_SVG_FILE = ('<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#1f6feb" '
             'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">'
             '<path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"></path>'
             '<path d="M14 2v6h6"></path></svg>')


def _upload_oculto(on_upload, accept: str) -> str:
    """Cria um `ui.upload` escondido e devolve o JS que abre o seletor de arquivo.

    O input fica no DOM (so `display:none`), entao `.click()` programatico abre o
    dialogo normalmente — permite estilizar o gatilho como botao/dropzone.
    """
    up = ui.upload(on_upload=on_upload, auto_upload=True).props(f"accept={accept}")
    up.classes(f"hidden es-up-{up.id}")
    return f"document.querySelector('.es-up-{up.id} input[type=file]').click()"


def botao_importar(label: str, on_upload, *, accept: str = ".csv,.txt",
                   icon: str = "upload", props: str = "outline") -> None:
    """Botao que dispara um upload escondido (look de botao, sem o chrome do Quasar)."""
    js = _upload_oculto(on_upload, accept)
    ui.button(label, icon=icon, on_click=lambda: ui.run_javascript(js)).props(props)


def dropzone(titulo_html: str, sub_html: str, on_upload, *, accept: str = ".json",
             vertical: bool = True, icon: str = "upload") -> None:
    """Tile tracejado de importacao (clique abre o seletor).

    `vertical` empilha icone/texto (Inicio) ou alinha em linha (Visualizador);
    `icon` = 'upload' (seta) ou 'file' (folha de arquivo).
    """
    js = _upload_oculto(on_upload, accept)
    cls = "es-dropzone " + ("es-dz-col" if vertical else "es-dz-row")
    with ui.element("div").classes(cls).on("click", lambda: ui.run_javascript(js)):
        ui.html(_SVG_FILE if icon == "file" else _SVG_UPLOAD)
        with ui.element("div").classes("es-dz-text"):
            ui.html(f'<span class="es-dz-title">{titulo_html}</span>')
            ui.html(f'<span class="es-dz-sub">{sub_html}</span>')


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
