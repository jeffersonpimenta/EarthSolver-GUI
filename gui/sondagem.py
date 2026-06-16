"""Parsing de sondagem de Wenner (sem dependencia de UI).

Modulo separado da pagina para ser testavel sem importar uma rota `@ui.page`
(o que atrapalharia o ciclo de reset de modulos do `nicegui.testing`).
"""

from __future__ import annotations

import re

_SEP = re.compile(r"[,;\s]+")


def parse_sondagem(texto: str) -> tuple[list[float], list[float], bool]:
    """Le 'espacamento valor' por linha. Detecta cabecalho e coluna de rho_a.

    Separadores aceitos: virgula, ponto-e-virgula ou espaco. Retorna
    (espacamentos, valores, eh_resistividade). eh_resistividade=True quando o
    cabecalho menciona 'rho'/'resistivid' (valores ja sao rho aparente); senao
    os valores sao resistencias medidas (Ohm).
    """
    linhas = [ln for ln in texto.splitlines() if ln.strip()]
    if not linhas:
        raise ValueError("sondagem vazia")
    eh_rho = False
    inicio = 0
    primeiro = [c for c in _SEP.split(linhas[0].strip()) if c]
    try:
        float(primeiro[0])
    except (ValueError, IndexError):
        inicio = 1  # primeira linha e cabecalho
        eh_rho = any("rho" in c.lower() or "resistivid" in c.lower() for c in primeiro)
    espac, valores = [], []
    for n, ln in enumerate(linhas[inicio:], start=inicio + 1):
        celulas = [c for c in _SEP.split(ln.strip()) if c]
        if len(celulas) < 2:
            raise ValueError(f"linha {n}: esperado 'espacamento valor', recebido {ln!r}")
        espac.append(float(celulas[0]))
        valores.append(float(celulas[1]))
    return espac, valores, eh_rho
