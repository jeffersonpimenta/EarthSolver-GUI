"""Localizacao dos arquivos de exemplo (compartilhados com o nucleo).

`exemplos/` fica na raiz do repo (irmao do pacote `gui`); funciona no layout de
desenvolvimento (instalacao editavel) e na imagem Docker (COPY . do repo).
"""

from pathlib import Path

DIR_EXEMPLOS = Path(__file__).resolve().parent.parent / "exemplos"


def caminho_exemplo(nome: str) -> Path:
    return DIR_EXEMPLOS / nome
