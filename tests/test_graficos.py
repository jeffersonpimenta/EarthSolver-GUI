"""Testes dos graficos Plotly (gui/graficos.py) - funcoes puras dados -> Figure."""

import numpy as np
import plotly.graph_objects as go

from gui import graficos

# raster 2x2 (mesmo formato 2D do nucleo: X, Y, Phi como meshgrid)
X = np.array([[0.0, 1.0], [0.0, 1.0]])
Y = np.array([[0.0, 0.0], [1.0, 1.0]])
PHI = np.array([[1.0, 2.0], [3.0, 4.0]])
CONDS = [
    {"p1": [0.0, 0.0, 0.5], "p2": [1.0, 0.0, 0.5]},
    {"p1": [1.0, 0.0, 0.5], "p2": [1.0, 1.0, 0.5]},
]
# campos de seguranca 2x2 (mesmo grid do raster)
TOQUE = np.array([[4.0, 3.0], [2.0, 1.0]])
PASSO = np.array([[1.0, 1.5], [2.0, 2.5]])


def test_curva_wenner_tem_medido_e_ajuste_em_eixos_log():
    fig = graficos.curva_wenner([1.0, 2.0, 4.0], [100.0, 80.0, 60.0],
                                [1.0, 2.0, 4.0], [98.0, 82.0, 61.0])
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2  # pontos medidos + curva do ajuste
    assert fig.layout.xaxis.type == "log"
    assert fig.layout.yaxis.type == "log"


def test_mapa_potencial_tem_heatmap_e_contorno():
    fig = graficos.mapa_potencial(X, Y, PHI, gpr=10.0)
    tipos = [d.type for d in fig.data]
    assert "heatmap" in tipos
    assert "contour" in tipos


def test_mapa_potencial_com_condutores_adiciona_overlay_em_planta():
    fig = graficos.mapa_potencial(X, Y, PHI, condutores=CONDS)
    assert "scatter" in [d.type for d in fig.data]


def test_superficie_3d_e_um_surface():
    fig = graficos.superficie_3d(X, Y, PHI)
    assert [d.type for d in fig.data] == ["surface"]


def test_vista_malha_e_scatter3d_com_separador_entre_condutores():
    fig = graficos.vista_malha(CONDS)
    assert fig.data[0].type == "scatter3d"
    # dois condutores -> um separador None na lista x
    assert list(fig.data[0].x).count(None) == 1


def test_mapa_toque_tem_heatmap_e_iso_linha_do_limite():
    fig = graficos.mapa_toque(X, Y, TOQUE, limite=2.5)
    tipos = [d.type for d in fig.data]
    assert "heatmap" in tipos
    assert "contour" in tipos          # iso-linha do limite toleravel


def test_mapa_toque_sem_limite_nao_tem_contorno_mas_aceita_condutores():
    fig = graficos.mapa_toque(X, Y, TOQUE, condutores=CONDS)
    tipos = [d.type for d in fig.data]
    assert "heatmap" in tipos
    assert "contour" not in tipos
    assert "scatter" in tipos          # overlay dos condutores em planta


def test_mapa_passo_tem_heatmap():
    fig = graficos.mapa_passo(X, Y, PASSO, limite=2.0)
    assert "heatmap" in [d.type for d in fig.data]


def test_mapa_margem_tem_heatmap_e_contorno_de_100pc():
    fig = graficos.mapa_margem(X, Y, TOQUE, PASSO, e_toque=2.0, e_passo=2.0,
                               condutores=CONDS)
    tipos = [d.type for d in fig.data]
    assert isinstance(fig, go.Figure)
    assert "heatmap" in tipos
    assert "contour" in tipos          # iso-linha de 100% (reprovacao)


def test_mapa_corrente_colore_pontos_medios_por_magnitude():
    A = [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]
    B = [[1.0, 0.0, 0.0], [1.0, 1.0, 0.0]]
    fig = graficos.mapa_corrente(A, B, [2.0, 5.0])
    # ha um trace de marcadores nos pontos medios colorido por |I|
    marcadores = [d for d in fig.data if d.mode == "markers"]
    assert len(marcadores) == 1
    assert list(marcadores[0].marker.color) == [2.0, 5.0]


def test_perfis_tem_dois_cortes_com_tres_series_cada():
    fig = graficos.perfis(X, Y, PHI, TOQUE, PASSO, e_toque=3.0, e_passo=2.0, gpr=5.0)
    assert isinstance(fig, go.Figure)
    # 3 series (potencial/toque/passo) x 2 cortes = 6 traces (as linhas-limite
    # sao shapes via add_hline, nao traces)
    assert len(fig.data) == 6


def test_curva_convergencia_tem_dois_eixos_y():
    fig = graficos.curva_convergencia(
        {"n_segmentos": [4, 8, 16], "Rg": [2.0, 1.9, 1.85], "GPR": [100.0, 95.0, 93.0]})
    assert len(fig.data) == 2          # Rg e GPR
    assert fig.layout.yaxis2.overlaying == "y"


def test_campo_3d_e_um_surface():
    fig = graficos.campo_3d(X, Y, TOQUE, titulo="Toque (3D)", rotulo="V")
    assert [d.type for d in fig.data] == ["surface"]
