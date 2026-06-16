"""Testes do estado de projeto (gui/estado.py)."""

import json
from pathlib import Path

from gui.estado import Projeto, obter_projeto

EXEMPLOS = Path(__file__).resolve().parent.parent / "exemplos"


def _projeto_exemplo() -> dict:
    return json.loads((EXEMPLOS / "projeto.json").read_text(encoding="utf-8"))


def test_from_dict_popula_campos_do_projeto_json():
    proj = Projeto.from_dict(_projeto_exemplo())
    assert proj.sondagem["espacamentos"][0] == 0.5
    assert proj.malha["area"] == 4900.0
    assert proj.falta["Ig"] == 1908.0


def test_to_dict_roundtrip_preserva_secoes_do_projeto():
    d = _projeto_exemplo()
    saida = Projeto.from_dict(d).to_dict()
    assert saida["sondagem"] == d["sondagem"]
    assert saida["malha"] == d["malha"]
    assert saida["falta"] == d["falta"]


def test_to_dict_omite_campos_ausentes():
    proj = Projeto(solo={"rho": [400.0], "espessura": []})
    assert proj.to_dict() == {"solo": {"rho": [400.0], "espessura": []}}


def test_obter_projeto_cria_uma_vez_e_reusa_o_mesmo_objeto():
    armazem = {}
    p1 = obter_projeto(armazem)
    p2 = obter_projeto(armazem)
    assert p1 is p2
    assert isinstance(p1, Projeto)
