"""Estado de projeto compartilhado entre as paginas (uma instancia por aba).

O `Projeto` agrega as entradas do pipeline (sondagem -> solo -> geometria ->
falta) e os resultados calculados. As secoes de entrada espelham o schema de
`exemplos/projeto.json`, entao `to_dict()`/`from_dict()` dao import/export de
projeto de graca. Os resultados nao entram no `to_dict()` (sao downloads a
parte e recalculaveis).

`obter_projeto()` guarda o `Projeto` no armazenamento por aba do NiceGUI
(`app.storage.tab`), que sobrevive a navegacao entre paginas na mesma aba. Para
testes, passe um dicionario como `armazem`.
"""

from __future__ import annotations

from dataclasses import dataclass

# Secoes de entrada persistidas/compartilhaveis (espelham projeto.json + solo).
_CAMPOS_ENTRADA = ("sondagem", "solo", "malha", "eletrodo", "falta")

_CHAVE = "projeto"


@dataclass
class Projeto:
    """Entradas e resultados do pipeline de aterramento, por aba do navegador."""

    # entradas
    sondagem: dict | None = None   # {espacamentos, resistencias|resistividades, camadas, ...}
    solo: dict | None = None       # {rho: [...], espessura: [...]}
    malha: dict | None = None      # params IEEE-80 derivados da malha retangular (+ brita);
                                   # so {rho_s, h_s} quando a geometria e DXF
    eletrodo: dict | None = None   # geometria: {malha_retangular: ...} ou {dxf, mapa}
    falta: dict | None = None      # {Ig, t, peso}
    # resultados (nao persistidos no projeto)
    resultado_analitico: dict | None = None
    resultado_numerico: dict | None = None
    raster: dict | None = None     # {x, y, phi, GPR}

    def to_dict(self) -> dict:
        """Secoes de entrada definidas, no schema de projeto.json (+ solo)."""
        return {c: getattr(self, c) for c in _CAMPOS_ENTRADA if getattr(self, c) is not None}

    @classmethod
    def from_dict(cls, d: dict) -> Projeto:
        """Cria um Projeto a partir de um dict de projeto (campos ausentes -> None)."""
        return cls(**{c: d.get(c) for c in _CAMPOS_ENTRADA})


def obter_projeto(armazem=None) -> Projeto:
    """Devolve o Projeto da aba atual, criando-o na primeira chamada.

    `armazem` e um mapeavel (default: `app.storage.tab`); injetavel nos testes.
    """
    if armazem is None:
        from nicegui import app
        armazem = app.storage.tab
    proj = armazem.get(_CHAVE)
    if not isinstance(proj, Projeto):
        proj = Projeto()
        armazem[_CHAVE] = proj
    return proj
