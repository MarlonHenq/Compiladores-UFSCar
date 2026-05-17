"""
Tabela de símbolos com suporte a múltiplos escopos (pilha de escopos).

Cada nível da pilha é um dicionário nome → Simbolo.
O escopo 0 (base) é o escopo global (procedimentos, funções, tipos e constantes
declarados fora do 'algoritmo').
Escopos internos são empurrados/desempilhados ao entrar/sair de sub-rotinas
ou do corpo do 'algoritmo'.

Categorias de símbolo (SorteSimbolo):
  VARIAVEL   – variável comum declarada com 'declare'
  CONSTANTE  – constante declarada com 'constante'
  TIPO_LA    – alias de tipo declarado com 'tipo'
  PROCEDURE  – procedimento declarado com 'procedimento'
  FUNCAO     – função declarada com 'funcao'

Todos os nomes compartilham o mesmo espaço nominal: não é possível ter
uma variável e uma função com o mesmo nome no mesmo escopo visível.
"""
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
    """Entrada na tabela de símbolos."""

    nome: str
    sorte: SorteSimbolo
    tipo: Tipo
    # Tupla ordenada dos tipos dos parâmetros formais (apenas para PROCEDURE/FUNCAO).
    # Usado na T4 para validar chamadas: quantidade e tipos dos argumentos.
    parametros_tipos: tuple[Tipo, ...] | None = None


class TabelaSimbolos:
    """
    Gerenciador de escopos em pilha.

    Regras:
      - push_escopo() abre um novo nível (entrar em sub-rotina ou corpo do algoritmo).
      - pop_escopo()  fecha o nível corrente.
      - inserir()     adiciona ao escopo do topo (ou ao escopo global se global_=True).
      - buscar_encadeado() percorre a pilha do topo para a base, retornando o
        primeiro símbolo que corresponder ao nome buscado.
      - existe_local() verifica apenas o escopo do topo (útil para verificar
        parâmetros duplicados dentro do mesmo escopo de sub-rotina).
    """

    def __init__(self) -> None:
        # Pilha: índice 0 = escopo global, -1 = escopo corrente
        self._pilha: list[dict[str, Simbolo]] = [{}]

    def escopo_profundidade(self) -> int:
        """Retorna a profundidade do escopo atual (0 = global)."""
        return len(self._pilha) - 1

    def push_escopo(self) -> None:
        """Abre um novo nível de escopo."""
        self._pilha.append({})

    def pop_escopo(self) -> None:
        """Fecha o nível corrente (não remove o global)."""
        if len(self._pilha) > 1:
            self._pilha.pop()

    def _no_escopo_atual(self) -> dict[str, Simbolo]:
        return self._pilha[-1]

    def existe_local(self, nome: str) -> bool:
        """Verifica se o nome existe no escopo do topo (sem olhar escopos externos)."""
        return nome in self._no_escopo_atual()

    def inserir(self, simbolo: Simbolo, *, global_: bool = False) -> None:
        """
        Insere um símbolo no escopo corrente.
        Se global_=True, insere no escopo global (índice 0) em vez do topo.
        """
        alvo = self._pilha[0] if global_ else self._no_escopo_atual()
        alvo[simbolo.nome] = simbolo

    def buscar_apenas_escopo_local(self, nome: str) -> Simbolo | None:
        """Retorna o símbolo apenas do escopo do topo, sem percorrer a pilha."""
        return self._no_escopo_atual().get(nome)

    def buscar_encadeado(self, nome: str) -> Simbolo | None:
        """
        Busca um símbolo percorrendo a pilha do escopo mais interno ao global.
        Retorna o primeiro símbolo encontrado, ou None se ausente em todos os escopos.
        Usado nas verificações de 'já declarado' (T4) e de 'não declarado'.
        """
        for nivel in reversed(self._pilha):
            if nome in nivel:
                return nivel[nome]
        return None
