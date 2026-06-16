# EarthSolver-GUI

Interface web (NiceGUI) para o [EarthSolver](https://github.com/jeffersonpimenta/EarthSolver) —
suite de analise de aterramento eletrico. Cobre todo o pipeline:

1. **Estratificacao** do solo a partir de uma sondagem de Wenner (NBR 7117);
2. **Estudo analitico** de malha pelo IEEE Std 80;
3. **Solver numerico** de segmentacao de condutores (geometria arbitraria,
   incluindo importacao de DXF com mapeamento de layers);
4. **Visualizador** de resultados exportados.

A GUI vive em um repositorio separado e consome **apenas a API publica** do
pacote `earthsolver` — o nucleo permanece intocado. O estado do projeto e
compartilhado entre as paginas durante a sessao (por aba do navegador).

## Arquitetura

```
gui/
  main.py          ponto de entrada (ui.run); importa as paginas
  layout.py        moldura comum (cabecalho + gaveta de navegacao)
  estado.py        Projeto por aba (app.storage.tab)
  solver.py        funcoes picaveis sobre o nucleo (run.cpu_bound)
  graficos.py      figuras Plotly (curva Wenner, mapa, 3D, geometria)
  componentes.py   cartoes de resultado reutilizados
  campos.py        parsing de campos | sondagem.py  parsing de Wenner
  paginas/         inicio, estratificacao, analitico, numerico, visualizador
```

Calculos pesados (estratificacao, solver numerico) rodam em subprocesso via
`nicegui.run.cpu_bound`, sem travar a interface. Os graficos sao construidos a
partir dos dados crus (raster numpy, condutores) — independentes do matplotlib
do nucleo.

## Desenvolvimento

Pre-requisito: o nucleo `earthsolver` no repositorio vizinho.

```powershell
# 1. nucleo em modo editavel (repo vizinho)
pip install -e ..\EarthSolver

# 2. este pacote sem rebaixar o nucleo editavel (deps de UI ja vem do passo 3)
pip install -e . --no-deps

# 3. dependencias de runtime e desenvolvimento
pip install nicegui plotly numpy pytest pytest-asyncio httpx ruff

# rodar o app (abre o navegador em http://localhost:8080)
python -m gui.main

# testes e lint
pytest -v
ruff check .
```

Variaveis de ambiente:

| Variavel | Default | Efeito |
|---|---|---|
| `PORT` | 8080 | porta do servidor |
| `STORAGE_SECRET` | dev | segredo do armazenamento por aba |
| `EARTHGUI_HEADLESS` | (vazio) | `1` nao tenta abrir o navegador (servidor/Docker) |
| `EARTHGUI_MAX_SEG` | 0 | teto de segmentos do solver (0 = ilimitado) |

## Demo publico (Docker)

```bash
docker build -t earthsolver-gui .
docker run -p 8080:8080 earthsolver-gui
```

A imagem instala o pacote (que puxa o `earthsolver` via `git+https`) e sobe o
app em modo headless com teto de segmentos para proteger o servidor.

### Hugging Face Spaces (Docker, gratis)

1. Crie um Space do tipo **Docker**.
2. Suba este repositorio. O HF usa o `Dockerfile`; exponha a porta `8080`
   (ou ajuste `PORT`/`EXPOSE` para `7860`, padrao do HF).

### Render / Railway / Fly.io

Servico web a partir do `Dockerfile`; defina `PORT` conforme a plataforma e,
opcionalmente, `STORAGE_SECRET` e `EARTHGUI_MAX_SEG`.

## Licenca

GPL-3.0-or-later (mesma do nucleo EarthSolver).
