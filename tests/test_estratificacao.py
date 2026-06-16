"""Testes do parser de sondagem (gui/sondagem.py)."""

import pytest

from gui.sondagem import parse_sondagem


def test_parse_com_cabecalho_de_resistencia():
    a, v, eh_rho = parse_sondagem("spacing,resistance\n1,10\n2,5\n")
    assert a == [1.0, 2.0]
    assert v == [10.0, 5.0]
    assert eh_rho is False


def test_parse_sem_cabecalho():
    a, v, eh_rho = parse_sondagem("1,10\n2,5")
    assert a == [1.0, 2.0]
    assert eh_rho is False


def test_parse_detecta_resistividade_aparente_no_cabecalho():
    _, _, eh_rho = parse_sondagem("a,rho_a\n1,100\n2,80")
    assert eh_rho is True


def test_parse_aceita_ponto_e_virgula():
    a, v, _ = parse_sondagem("1;10\n2;5")
    assert a == [1.0, 2.0] and v == [10.0, 5.0]


def test_parse_vazio_levanta_erro():
    with pytest.raises(ValueError):
        parse_sondagem("   \n  ")
