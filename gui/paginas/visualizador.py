"""Pagina visualizador: recarrega exports (resultado / potencial) e replota.

Nao roda solver - so le os JSON exportados (`aterramento_numerico.json` e
`potencial.json`, do nucleo ou da pagina numerica) e desenha.
"""

from __future__ import annotations

import numpy as np
from nicegui import ui

from gui import graficos
from gui.componentes import cartoes_resultado, dropzone
from gui.layout import cabecalho, moldura


@ui.page("/visualizador")
async def pagina_visualizador() -> None:
    await ui.context.client.connected()
    estado: dict = {"res": None, "raster": None}

    with moldura("Visualizador", "/visualizador"):
        cabecalho("Sem solver", "Visualizador de resultados",
                  "Carregue um aterramento_numerico.json (resultado) e/ou um "
                  "potencial.json (mapa de potencial) para revisualizar sem recalcular.")

        async def importar_resultado(e) -> None:
            try:
                d = await e.file.json()
                assert "Rg" in d
            except Exception:  # noqa: BLE001
                ui.notify("Arquivo de resultado invalido.", type="negative")
                return
            estado["res"] = d
            vista.refresh()
            ui.notify("Resultado carregado.", type="positive")

        async def importar_potencial(e) -> None:
            try:
                d = await e.file.json()
                assert {"x", "y", "phi"} <= set(d)
            except Exception:  # noqa: BLE001
                ui.notify("Arquivo de potencial invalido.", type="negative")
                return
            estado["raster"] = d
            vista.refresh()
            ui.notify("Mapa de potencial carregado.", type="positive")

        with ui.grid().classes("w-full gap-4") \
                .style("grid-template-columns:minmax(0,1fr) minmax(0,1fr)"):
            dropzone("Resultado (.json)",
                     '<span class="es-mono" style="color:#475569">aterramento_numerico.json</span>',
                     importar_resultado, accept=".json", vertical=False, icon="file")
            dropzone("Potencial (.json)",
                     '<span class="es-mono" style="color:#475569">potencial.json</span>',
                     importar_potencial, accept=".json", vertical=False, icon="file")

        @ui.refreshable
        def vista() -> None:
            if not estado["res"] and not estado["raster"]:
                ui.label("Nenhum arquivo carregado.").classes("text-grey")
                return
            if estado["res"]:
                cartoes_resultado(estado["res"])
            if estado["raster"]:
                ras = estado["raster"]
                gpr = ras.get("GPR")
                tem_toque = gpr is not None       # toque = GPR - phi (derivavel do potencial)
                with ui.card().classes("w-full p-3"):
                    with ui.tabs().props("no-caps").classes("self-start") as plots:
                        ui.tab("mapa", "Mapa de potencial")
                        if tem_toque:
                            ui.tab("toque", "Tensao de toque")
                        ui.tab("s3d", "Superficie 3D")
                    with ui.tab_panels(plots, value="mapa").classes("w-full"):
                        with ui.tab_panel("mapa"):
                            ui.plotly(graficos.mapa_potencial(ras["x"], ras["y"], ras["phi"],
                                      gpr=gpr)).classes("w-full")
                        if tem_toque:
                            with ui.tab_panel("toque"):
                                toque = (np.asarray(gpr, dtype=float)
                                         - np.asarray(ras["phi"], dtype=float))
                                ui.plotly(graficos.mapa_toque(ras["x"], ras["y"],
                                          toque)).classes("w-full")
                        with ui.tab_panel("s3d"):
                            ui.plotly(graficos.superficie_3d(ras["x"], ras["y"],
                                      ras["phi"])).classes("w-full")

        ui.separator()
        vista()
