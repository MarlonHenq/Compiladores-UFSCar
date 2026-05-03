"""Pilha de escopos: variáveis, constantes, tipos, procedures e funções compartilham o mesmo espaço nominal."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from tipos import Tipo


class SorteSimbolo(Enum):
    VARIAVEL = auto()
    CONSTANTE = auto()
    TIPO_LA = auto()
    PROCEDURE = auto()
    FUNCAO = auto()


@dataclass
class Simbolo:
    nome: str
    sorte: SorteSimbolo
    tipo: Tipo
    # Lista de Tipos esperados nos parâmetros (var ref ignored na LA para tipagem simples aqui).
    parametros_tipos: tuple[Tipo, ...] | None = None


class TabelaSimbolos:
    def __init__(self) -> None:
        self._pilha: list[dict[str, Simbolo]] = [{}]

    def escopo_profundidade(self) -> int:
        return len(self._pilha) - 1

    def push_escopo(self) -> None:
        self._pilha.append({})

    def pop_escopo(self) -> None:
        if len(self._pilha) > 1:
            self._pilha.pop()

    def _no_escopo_atual(self) -> dict[str, Simbolo]:
        return self._pilha[-1]

    def existe_local(self, nome: str) -> bool:
        return nome in self._no_escopo_atual()

    def inserir(self, simbolo: Simbolo, *, global_: bool = False) -> None:
        alvo = self._pilha[0] if global_ else self._no_escopo_atual()
        alvo[simbolo.nome] = simbolo

    def buscar_apenas_escopo_local(self, nome: str) -> Simbolo | None:
        s = self._no_escopo_atual().get(nome)
        return s

    def buscar_encadeado(self, nome: str) -> Simbolo | None:
        for nivel in reversed(self._pilha):
            if nome in nivel:
                return nivel[nome]
        return None
