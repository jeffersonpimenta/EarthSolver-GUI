"""Graficos Plotly do EarthSolver-GUI.

Funcoes puras: recebem dados crus (numpy/listas) e devolvem `go.Figure`. Sem
dependencia do NiceGUI nem do matplotlib do nucleo - assim sao testaveis sem
navegador e renderizadas interativamente no browser via `ui.plotly`.

O raster segue o formato do nucleo (`exportar_raster`): X, Y, Phi como malhas
2D (meshgrid). As funcoes aceitam X/Y em 2D ou 1D e normalizam para os eixos.
"""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go


def _eixos_1d(x, y):
    """Reduz X, Y (meshgrid 2D) para os vetores de eixo 1D; aceita ja-1D."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    xs = x[0, :] if x.ndim == 2 else x
    ys = y[:, 0] if y.ndim == 2 else y
    return xs, ys


def _segmentos_xyz(condutores):
    """Concatena os condutores em listas x/y/z com `None` entre cada segmento.

    Um unico trace de linhas renderiza toda a geometria; o `None` quebra a linha
    entre condutores nao conectados.
    """
    xs, ys, zs = [], [], []
    for c in condutores:
        p1, p2 = c["p1"], c["p2"]
        xs += [p1[0], p2[0], None]
        ys += [p1[1], p2[1], None]
        zs += [p1[2], p2[2], None]
    for seq in (xs, ys, zs):  # remove o separador final
        if seq:
            seq.pop()
    return xs, ys, zs


def curva_wenner(a, rho_medido, a_fit, rho_fit) -> go.Figure:
    """Curva de resistividade aparente: pontos medidos + ajuste, eixos log-log."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(a), y=list(rho_medido), mode="markers",
                             name="Medido"))
    fig.add_trace(go.Scatter(x=list(a_fit), y=list(rho_fit), mode="lines",
                             name="Ajuste"))
    fig.update_layout(
        title="Resistividade aparente (Wenner)",
        xaxis=dict(title="Espacamento a (m)", type="log"),
        yaxis=dict(title="rho_a (Ohm.m)", type="log"),
        margin=dict(l=60, r=20, t=40, b=50),
    )
    return fig


def mapa_potencial(x, y, phi, gpr=None, condutores=None) -> go.Figure:
    """Mapa de potencial de superficie: heatmap + contornos, com condutores em planta."""
    xs, ys = _eixos_1d(x, y)
    phi = np.asarray(phi, dtype=float)
    fig = go.Figure()
    fig.add_trace(go.Heatmap(x=xs, y=ys, z=phi, colorscale="Viridis",
                             colorbar=dict(title="Phi (V)")))
    fig.add_trace(go.Contour(x=xs, y=ys, z=phi, showscale=False,
                             contours=dict(coloring="lines"),
                             line=dict(color="rgba(255,255,255,0.5)")))
    if condutores:
        sx, sy, _ = _segmentos_xyz(condutores)
        fig.add_trace(go.Scatter(x=sx, y=sy, mode="lines",
                                 line=dict(color="black", width=1),
                                 name="Condutores"))
    titulo = "Potencial de superficie"
    if gpr is not None:
        titulo += f" (GPR = {gpr:.1f} V)"
    fig.update_layout(title=titulo, xaxis=dict(title="x (m)"),
                      yaxis=dict(title="y (m)", scaleanchor="x", scaleratio=1),
                      margin=dict(l=60, r=20, t=40, b=50))
    return fig


def superficie_3d(x, y, phi) -> go.Figure:
    """Superficie 3D interativa do potencial (substitui o plot 3D matplotlib)."""
    xs, ys = _eixos_1d(x, y)
    phi = np.asarray(phi, dtype=float)
    fig = go.Figure(go.Surface(x=xs, y=ys, z=phi, colorscale="Viridis",
                               colorbar=dict(title="Phi (V)")))
    fig.update_layout(
        title="Potencial de superficie (3D)",
        scene=dict(xaxis_title="x (m)", yaxis_title="y (m)", zaxis_title="Phi (V)"),
        margin=dict(l=0, r=0, t=40, b=0),
    )
    return fig


def vista_malha(condutores) -> go.Figure:
    """Vista 3D da geometria do eletrodo (um trace de linhas, segmentos separados)."""
    sx, sy, sz = _segmentos_xyz(condutores)
    fig = go.Figure(go.Scatter3d(x=sx, y=sy, z=sz, mode="lines",
                                 line=dict(color="#1565C0", width=4),
                                 name="Condutores"))
    fig.update_layout(
        title="Geometria do eletrodo",
        scene=dict(xaxis_title="x (m)", yaxis_title="y (m)",
                   zaxis_title="profundidade z (m)", zaxis=dict(autorange="reversed")),
        margin=dict(l=0, r=0, t=40, b=0),
    )
    return fig


# ----------------------------------------------------- mapas de seguranca

def _overlay_condutores(fig: go.Figure, condutores) -> None:
    """Sobrepoe o contorno dos condutores em planta (um trace de linhas pretas)."""
    if condutores:
        sx, sy, _ = _segmentos_xyz(condutores)
        fig.add_trace(go.Scatter(x=sx, y=sy, mode="lines",
                                 line=dict(color="black", width=1),
                                 name="Condutores"))


def _mapa_campo(x, y, campo, rotulo, titulo, colorscale, limite, condutores) -> go.Figure:
    """Heatmap de um campo escalar (toque/passo) + iso-linha do limite + malha.

    A iso-linha vermelha no valor toleravel realca a fronteira da regiao que
    excede o limite (substitui a hachura do matplotlib do nucleo).
    """
    xs, ys = _eixos_1d(x, y)
    campo = np.asarray(campo, dtype=float)
    fig = go.Figure()
    fig.add_trace(go.Heatmap(x=xs, y=ys, z=campo, colorscale=colorscale,
                             colorbar=dict(title=rotulo)))
    if limite is not None:
        fig.add_trace(go.Contour(
            x=xs, y=ys, z=campo, showscale=False,
            contours=dict(start=limite, end=limite, size=1, coloring="lines"),
            line=dict(color="red", width=2), name=f"limite {limite:.0f} V"))
    _overlay_condutores(fig, condutores)
    fig.update_layout(title=titulo, xaxis=dict(title="x (m)"),
                      yaxis=dict(title="y (m)", scaleanchor="x", scaleratio=1),
                      margin=dict(l=60, r=20, t=40, b=50))
    return fig


def mapa_toque(x, y, toque, limite=None, condutores=None) -> go.Figure:
    """Mapa de tensao de toque (GPR - potencial de superficie).

    `limite` = tensao de toque toleravel (E_toque): traca a iso-linha do limite.
    Espelha `plot.plot_tensao_toque`.
    """
    return _mapa_campo(x, y, toque, "Tensao de toque (V)", "Tensao de toque",
                       "YlOrRd", limite, condutores)


def mapa_passo(x, y, passo, limite=None, condutores=None) -> go.Figure:
    """Mapa de tensao de passo (diferenca de potencial a 1 m, pior direcao).

    `limite` = tensao de passo toleravel (E_passo). Espelha `plot.plot_tensao_passo`.
    """
    return _mapa_campo(x, y, passo, "Tensao de passo (V)", "Tensao de passo",
                       "PuBu", limite, condutores)


def mapa_margem(x, y, toque, passo, e_toque, e_passo, condutores=None) -> go.Figure:
    """Mapa de utilizacao max(toque/E_toque, passo/E_passo) em %: >100% reprova.

    A contribuicao de toque e restrita a projecao (bbox) dos condutores quando
    dados (so ha o que tocar sobre o metal aterrado); a de passo vale toda a area.
    Espelha `plot.plot_margem`.
    """
    xs, ys = _eixos_1d(x, y)
    toque = np.asarray(toque, dtype=float)
    passo = np.asarray(passo, dtype=float)
    ut = toque / e_toque
    if condutores:
        sx, sy, _ = _segmentos_xyz(condutores)
        sx = [v for v in sx if v is not None]
        sy = [v for v in sy if v is not None]
        X, Y = np.meshgrid(xs, ys)
        dentro = (X >= min(sx)) & (X <= max(sx)) & (Y >= min(sy)) & (Y <= max(sy))
        ut = np.where(dentro, ut, 0.0)
    util = np.maximum(ut, passo / e_passo) * 100.0
    fig = go.Figure()
    fig.add_trace(go.Heatmap(x=xs, y=ys, z=util, colorscale="RdYlGn",
                             reversescale=True, colorbar=dict(title="Utilizacao (%)")))
    fig.add_trace(go.Contour(
        x=xs, y=ys, z=util, showscale=False,
        contours=dict(start=100.0, end=100.0, size=1, coloring="lines"),
        line=dict(color="black", width=2), name="100%"))
    _overlay_condutores(fig, condutores)
    fig.update_layout(title="Margem de seguranca (utilizacao)",
                      xaxis=dict(title="x (m)"),
                      yaxis=dict(title="y (m)", scaleanchor="x", scaleratio=1),
                      margin=dict(l=60, r=20, t=40, b=50))
    return fig


def mapa_corrente(A, B, corrente) -> go.Figure:
    """Distribuicao da corrente drenada por segmento (planta).

    A, B (M,3): extremos de cada segmento; corrente (M,): corrente para o solo.
    Os segmentos aparecem como linhas cinza e os pontos medios sao marcados e
    coloridos por |I| (picos tipicamente nos cantos da malha). Espelha
    `plot.plot_corrente`.
    """
    A = np.asarray(A, dtype=float)
    B = np.asarray(B, dtype=float)
    mag = np.abs(np.asarray(corrente, dtype=float))
    xs, ys = [], []
    for a, b in zip(A, B, strict=False):
        xs += [a[0], b[0], None]
        ys += [a[1], b[1], None]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", showlegend=False,
                             line=dict(color="rgba(120,120,120,0.5)", width=1),
                             name="Segmentos"))
    mid = 0.5 * (A + B)
    fig.add_trace(go.Scatter(
        x=mid[:, 0], y=mid[:, 1], mode="markers", name="Corrente drenada",
        marker=dict(color=mag, colorscale="Plasma", size=8,
                    colorbar=dict(title="|I| (A)"))))
    fig.update_layout(title="Distribuicao de corrente por segmento",
                      xaxis=dict(title="x (m)"),
                      yaxis=dict(title="y (m)", scaleanchor="x", scaleratio=1),
                      margin=dict(l=60, r=20, t=40, b=50))
    return fig


def perfis(x, y, phi, toque, passo, e_toque, e_passo, gpr) -> go.Figure:
    """Perfis em corte pelas linhas centrais da malha (apresentacao IEEE-80).

    Dois cortes (em x e em y) pelo centro do raster, cada um com potencial de
    superficie, tensao de toque e tensao de passo, mais as linhas de GPR e dos
    limites toleraveis. Espelha `plot.plot_perfis`.
    """
    from plotly.subplots import make_subplots
    xs, ys = _eixos_1d(x, y)
    phi = np.asarray(phi, dtype=float)
    toque = np.asarray(toque, dtype=float)
    passo = np.asarray(passo, dtype=float)
    ny, nx = phi.shape
    i, j = ny // 2, nx // 2
    fig = make_subplots(rows=2, cols=1, subplot_titles=(
        "Corte em x (y central)", "Corte em y (x central)"))
    cortes = [
        (1, xs, phi[i, :], toque[i, :], passo[i, :]),
        (2, ys, phi[:, j], toque[:, j], passo[:, j]),
    ]
    for r, eixo, ph, tq, pa in cortes:
        ver = (r == 1)                                   # legenda so no 1o corte
        fig.add_trace(go.Scatter(x=eixo, y=ph, name="Potencial (V)", legendgroup="phi",
                                 line=dict(color="#1565C0"), showlegend=ver), row=r, col=1)
        fig.add_trace(go.Scatter(x=eixo, y=tq, name="Toque (V)", legendgroup="tq",
                                 line=dict(color="#EF6C00"), showlegend=ver), row=r, col=1)
        fig.add_trace(go.Scatter(x=eixo, y=pa, name="Passo (V)", legendgroup="pa",
                                 line=dict(color="#2E7D32"), showlegend=ver), row=r, col=1)
        fig.add_hline(y=gpr, line=dict(color="gray", dash="dot", width=1), row=r, col=1)
        fig.add_hline(y=e_toque, line=dict(color="#EF6C00", dash="dash", width=1), row=r, col=1)
        fig.add_hline(y=e_passo, line=dict(color="#2E7D32", dash="dash", width=1), row=r, col=1)
    fig.update_xaxes(title_text="distancia (m)", row=2, col=1)
    fig.update_yaxes(title_text="tensao (V)")
    fig.update_layout(title="Perfis de potencial e tensoes (cortes centrais)",
                      margin=dict(l=60, r=20, t=60, b=50))
    return fig


def curva_convergencia(dados) -> go.Figure:
    """Curva de convergencia Rg e GPR vs numero de segmentos.

    `dados` = {n_segmentos, Rg, GPR} (saida de `solver.rodar_convergencia`). Rg no
    eixo y esquerdo, GPR no direito. Espelha `plot.plot_convergencia`.
    """
    n = list(dados["n_segmentos"])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=n, y=list(dados["Rg"]), mode="lines+markers",
                             name="Rg (Ohm)", line=dict(color="#1565C0")))
    fig.add_trace(go.Scatter(x=n, y=list(dados["GPR"]), mode="lines+markers",
                             name="GPR (V)", line=dict(color="#C62828"), yaxis="y2"))
    fig.update_layout(
        title="Convergencia da discretizacao",
        xaxis=dict(title="numero de segmentos"),
        yaxis=dict(title="Rg (Ohm)", color="#1565C0"),
        yaxis2=dict(title="GPR (V)", color="#C62828", overlaying="y", side="right"),
        margin=dict(l=60, r=60, t=40, b=50),
    )
    return fig


def campo_3d(x, y, campo, titulo="Campo (3D)", rotulo="V") -> go.Figure:
    """Superficie 3D interativa de um campo escalar de seguranca (toque ou passo).

    Eleva o campo no eixo z sobre o plano (x, y). Espelha `plot.plot_campo_3d`.
    """
    xs, ys = _eixos_1d(x, y)
    campo = np.asarray(campo, dtype=float)
    fig = go.Figure(go.Surface(x=xs, y=ys, z=campo, colorscale="Inferno",
                               colorbar=dict(title=rotulo)))
    fig.update_layout(
        title=titulo,
        scene=dict(xaxis_title="x (m)", yaxis_title="y (m)", zaxis_title=rotulo),
        margin=dict(l=0, r=0, t=40, b=0),
    )
    return fig
