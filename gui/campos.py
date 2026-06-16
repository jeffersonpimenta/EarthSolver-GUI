"""Helpers de parsing de campos de formulario (sem dependencia de UI)."""

from __future__ import annotations

import re


def lista_floats(texto: str) -> list[float]:
    """Converte 'a, b; c' em [a, b, c]; string vazia -> []."""
    return [float(c) for c in re.split(r"[,;\s]+", (texto or "").strip()) if c]
