"""Testes do parser de listas de floats (gui/campos.py)."""

from gui.campos import lista_floats


def test_lista_floats_virgula_e_espaco():
    assert lista_floats("400, 100  200") == [400.0, 100.0, 200.0]


def test_lista_floats_vazia():
    assert lista_floats("") == []
    assert lista_floats("   ") == []
