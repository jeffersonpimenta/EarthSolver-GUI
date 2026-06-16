"""Smoke tests das paginas (fixture `user` do NiceGUI).

Verificam que cada pagina renderiza e que os fluxos sem calculo pesado
(navegacao, carregar exemplo) funcionam. O calculo via `run.cpu_bound` e
coberto por tests/test_solver.py e pela verificacao manual do app.
"""

from nicegui.testing import User


async def test_pagina_inicial_mostra_titulo_e_navegacao(user: User) -> None:
    await user.open("/")
    await user.should_see("EarthSolver")
    await user.should_see("Estratificacao")  # link no drawer
    await user.should_see("Visualizador")


async def test_carregar_projeto_exemplo_atualiza_estado(user: User) -> None:
    await user.open("/")
    await user.should_see("vazio")  # nada carregado ainda
    user.find("Carregar projeto exemplo").click()
    await user.should_see("carregado")


async def test_pagina_estratificacao_renderiza(user: User) -> None:
    await user.open("/estratificacao")
    await user.should_see("Estratificacao do solo")
    await user.should_see("Estratificar")


async def test_pagina_malha_renderiza_e_pre_visualiza(user: User) -> None:
    await user.open("/malha")
    await user.should_see("Malha e corrente de falta")
    await user.should_see("Pre-visualizar")
    # pre-visualizacao e sincrona (so geometria) -> estima segmentos
    user.find("Pre-visualizar").click()
    await user.should_see("segmentos estimados")


async def test_calculo_sem_dados_mostra_avisos(user: User) -> None:
    # sem solo/malha/falta no projeto, a pagina pede os passos anteriores
    await user.open("/calculo")
    await user.should_see("Solo nao definido")
    await user.should_see("Ir para Estratificacao")


async def test_visualizador_renderiza(user: User) -> None:
    await user.open("/visualizador")
    await user.should_see("Visualizador de resultados")
    await user.should_see("Nenhum arquivo carregado")
