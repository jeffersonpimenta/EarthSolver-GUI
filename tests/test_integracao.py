"""Integracao solver -> graficos.

Alimenta os plots Plotly com a saida real de `solver.rodar_numerico` /
`rodar_convergencia` exatamente como a pagina de calculo faz, pegando erros de
chave ou de forma no contrato entre as duas camadas (ex.: `raster_toque["v"]`,
`corrente["A"]`, `resultado["E_toque"]`).
"""

import plotly.graph_objects as go

from gui import graficos, solver

SOLO = {"rho": [400.0], "espessura": []}
# malha 20x20 com algumas malhas internas -> varios segmentos (corrente nao trivial)
MALHA = {"comprimento_x": 20.0, "comprimento_y": 20.0, "espac_x": 10.0,
         "espac_y": 10.0, "prof_h": 0.5, "d": 0.01, "n_hastes": 0, "comp_haste": 0.0}
PARAMS = {"Ig": 1000.0, "t": 0.5, "peso": 70, "comp_alvo": 10.0,
          "rho_s": None, "h_s": 0.1}


def test_saida_numerica_alimenta_todos_os_plots_da_pagina():
    num = solver.rodar_numerico(SOLO, {"malha_retangular": MALHA}, PARAMS)
    ras, rt, rp = num["raster"], num["raster_toque"], num["raster_passo"]
    cor, conds = num["corrente"], num["condutores"]
    et, ep = num["resultado"]["E_toque"], num["resultado"]["E_passo"]
    figs = [
        graficos.mapa_potencial(ras["x"], ras["y"], ras["phi"], gpr=ras["GPR"], condutores=conds),
        graficos.mapa_toque(rt["x"], rt["y"], rt["v"], limite=et, condutores=conds),
        graficos.mapa_passo(rp["x"], rp["y"], rp["v"], limite=ep, condutores=conds),
        graficos.mapa_margem(rt["x"], rt["y"], rt["v"], rp["v"], et, ep, condutores=conds),
        graficos.mapa_corrente(cor["A"], cor["B"], cor["I"]),
        graficos.perfis(ras["x"], ras["y"], ras["phi"], rt["v"], rp["v"], et, ep, ras["GPR"]),
        graficos.superficie_3d(ras["x"], ras["y"], ras["phi"]),
        graficos.campo_3d(rt["x"], rt["y"], rt["v"], "Tensao de toque (3D)", "V"),
        graficos.vista_malha(conds),
    ]
    assert all(isinstance(f, go.Figure) and f.data for f in figs)


def test_saida_convergencia_alimenta_a_curva():
    dados = solver.rodar_convergencia(SOLO, {"malha_retangular": MALHA}, PARAMS, [10.0, 7.0])
    fig = graficos.curva_convergencia(dados)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2
