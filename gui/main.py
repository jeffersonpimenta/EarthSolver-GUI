"""Ponto de entrada do app NiceGUI do EarthSolver.

Importar os modulos de pagina registra suas rotas (`@ui.page`), o que acontece
tanto ao rodar o servidor quanto ao importar este arquivo nos testes
(`nicegui.testing` executa via `runpy`). Apenas `ui.run()` fica sob o guard
`__main__`/`__mp_main__`.
"""

import os

from nicegui import ui

# registra as rotas das paginas (efeito de importacao)
from gui.paginas import (  # noqa: F401,E402
    calculo,
    estratificacao,
    inicio,
    malha,
    visualizador,
)


def main() -> None:
    """Inicia o servidor NiceGUI (porta e segredo configuraveis por ambiente)."""
    ui.run(
        title="EarthSolver",
        port=int(os.environ.get("PORT", "8080")),
        storage_secret=os.environ.get("STORAGE_SECRET", "earthsolver-dev-secret"),
        show=os.environ.get("EARTHGUI_HEADLESS") != "1",
        reload=False,
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
