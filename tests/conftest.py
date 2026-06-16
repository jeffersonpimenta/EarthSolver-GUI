"""Configuracao de testes: habilita as fixtures de teste do NiceGUI.

A fixture `user` executa o arquivo apontado por `main_file` (pyproject:
`gui/main.py`) para registrar as paginas antes de cada teste.
"""

pytest_plugins = ["nicegui.testing.plugin"]
