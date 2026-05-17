"""
Representação de tipos da linguagem LA e regras de compatibilidade (T4).

Tipos suportados:
  INDEFINIDO  – resultado de operação inválida ou identificador não declarado;
                propagado em expressões para evitar cascata de erros.
  BASICO      – inteiro, real, literal, logico
  PONTEIRO    – '^T' para qualquer tipo base T
  REGISTRO    – conjunto de campos nomeados com um rótulo de tipo

Para registros nomeados (tipo X: registro ... fim_registro), o rótulo
é o próprio alias X, permitindo verificação de compatibilidade por nome.
Registros anônimos (inline) recebem um rótulo interno '@r<id>'.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class SorteTipo(Enum):
    INDEFINIDO = auto()
    BASICO = auto()
    PONTEIRO = auto()
    REGISTRO = auto()


@dataclass(frozen=True)
class Tipo:
    """Descritor imutável de tipo da linguagem LA."""

    sorte: SorteTipo
    nome: str | None = None      # nome do tipo básico ou alias do registro
    interno: Tipo | None = None  # tipo apontado (para ponteiros)
    campos: frozenset[tuple[str, Tipo]] | None = None  # campos do registro

    @staticmethod
    def indefinido() -> Tipo:
        return Tipo(SorteTipo.INDEFINIDO)

    @staticmethod
    def basico(nome_kw: str) -> Tipo:
        return Tipo(SorteTipo.BASICO, nome=nome_kw)

    @staticmethod
    def ponteiro(par: Tipo) -> Tipo:
        return Tipo(SorteTipo.PONTEIRO, interno=par)

    @staticmethod
    def registro(nome_tipo: str, campos_ord: tuple[tuple[str, Tipo], ...]) -> Tipo:
        """
        Cria um tipo registro.
        Para registros nomeados (tipo X: registro), nome_tipo deve ser o alias X.
        Para registros anônimos (declare p: registro ... fim_registro), usa tag interna.
        """
        return Tipo(SorteTipo.REGISTRO, nome=nome_tipo, campos=frozenset(campos_ord))


# Instâncias singleton dos tipos básicos
INTEIRO = Tipo.basico("inteiro")
REAL = Tipo.basico("real")
LOGICO = Tipo.basico("logico")
LITERAL = Tipo.basico("literal")
INDEFINIDO = Tipo.indefinido()


def numerico(t: Tipo) -> bool:
    """Verdadeiro se o tipo é inteiro ou real."""
    return t.sorte == SorteTipo.BASICO and t.nome in ("inteiro", "real")


def e_literal_basico(t: Tipo) -> bool:
    return t.sorte == SorteTipo.BASICO and t.nome == "literal"


def mesmo_tipo(a: Tipo, b: Tipo) -> bool:
    """Igualdade estrutural entre dois tipos."""
    if a.sorte != b.sorte:
        return False
    if a.sorte == SorteTipo.INDEFINIDO:
        return True
    if a.sorte == SorteTipo.BASICO:
        return a.nome == b.nome
    if a.sorte == SorteTipo.PONTEIRO:
        ai = a.interno or INDEFINIDO
        bi = b.interno or INDEFINIDO
        return mesmo_tipo(ai, bi)
    if a.sorte == SorteTipo.REGISTRO:
        return a.nome == b.nome and a.campos == b.campos
    return False


def tipos_registro_compat(lhs: Tipo, rhs: Tipo) -> bool:
    """
    Compatibilidade entre dois registros: mesmo rótulo de tipo.
    Registros nomeados são compatíveis apenas entre si (mesmo alias).
    """
    return (
        lhs.sorte == SorteTipo.REGISTRO
        and rhs.sorte == SorteTipo.REGISTRO
        and lhs.nome == rhs.nome
    )


def resultado_aritmetica_op1(op: str, a: Tipo, b: Tipo) -> Tipo:
    """Tipo resultante de '+' ou '-' entre dois operandos."""
    if a.sorte == SorteTipo.INDEFINIDO or b.sorte == SorteTipo.INDEFINIDO:
        return INDEFINIDO
    if op == "+":
        if e_literal_basico(a) and e_literal_basico(b):
            return LITERAL
        if e_literal_basico(a) or e_literal_basico(b):
            return INDEFINIDO
        if numerico(a) and numerico(b):
            return REAL if (a.nome == "real" or b.nome == "real") else INTEIRO
        return INDEFINIDO
    if op == "-":
        if numerico(a) and numerico(b):
            return REAL if (a.nome == "real" or b.nome == "real") else INTEIRO
        return INDEFINIDO
    return INDEFINIDO


def resultado_termo(op: str, a: Tipo, b: Tipo) -> Tipo:
    """Tipo resultante de '*' ou '/' entre dois operandos."""
    if a.sorte == SorteTipo.INDEFINIDO or b.sorte == SorteTipo.INDEFINIDO:
        return INDEFINIDO
    if numerico(a) and numerico(b):
        if op == "/" or a.nome == "real" or b.nome == "real":
            return REAL
        return INTEIRO
    return INDEFINIDO


def resultado_modulo(a: Tipo, b: Tipo) -> Tipo:
    """Tipo resultante do operador '%' (módulo)."""
    if a.sorte == SorteTipo.INDEFINIDO or b.sorte == SorteTipo.INDEFINIDO:
        return INDEFINIDO
    if a.nome == "inteiro" and b.nome == "inteiro":
        return INTEIRO
    return INDEFINIDO


def atrib_compativel(lhs: Tipo, rhs: Tipo) -> bool:
    """
    Verifica compatibilidade de atribuição (operador '<-').

    Regras (PDF T4):
      ponteiro  ← endereço     (ponteiro de mesmo tipo interno)
      real      ← real | inteiro
      inteiro   ← inteiro
      literal   ← literal
      logico    ← logico
      registro  ← registro     (mesmo nome de tipo)
    """
    if rhs.sorte == SorteTipo.INDEFINIDO or lhs.sorte == SorteTipo.INDEFINIDO:
        return False

    # ponteiro ← endereço: RHS deve ser ponteiro com mesmo tipo interno
    if lhs.sorte == SorteTipo.PONTEIRO and lhs.interno:
        if rhs.sorte == SorteTipo.PONTEIRO and rhs.interno:
            return mesmo_tipo(lhs.interno, rhs.interno)
        return False

    if lhs.sorte == SorteTipo.BASICO and lhs.nome in ("real", "inteiro"):
        # PDF T4: (real | inteiro) ← (real | inteiro) — ambas as direções são válidas
        return rhs.sorte == SorteTipo.BASICO and rhs.nome in ("inteiro", "real")

    if lhs.sorte == SorteTipo.BASICO and lhs.nome == "literal":
        return rhs.sorte == SorteTipo.BASICO and rhs.nome == "literal"

    if lhs.sorte == SorteTipo.BASICO and lhs.nome == "logico":
        return rhs.sorte == SorteTipo.BASICO and rhs.nome == "logico"

    if lhs.sorte == SorteTipo.REGISTRO:
        return tipos_registro_compat(lhs, rhs)

    return mesmo_tipo(lhs, rhs)


def argumento_compativel_com_parametro(formal: Tipo, actual: Tipo) -> bool:
    """
    Verifica compatibilidade de um argumento com o parâmetro formal correspondente.

    A passagem de parâmetros usa correspondência ESTRITA (sem promoção inteiro→real).
    Tabela do PDF T4:
      endereço  → ponteiro   (actual deve ser ponteiro para o mesmo tipo interno)
      real      → real       (inteiro NÃO é promovido a real)
      inteiro   → inteiro
      literal   → literal
      logico    → logico
      registro  → registro   (mesmo nome de tipo)

    Se qualquer dos tipos for INDEFINIDO, retornamos True para evitar reportar
    duplo erro (o erro original já foi registrado ao avaliar o argumento).
    """
    if formal.sorte == SorteTipo.INDEFINIDO or actual.sorte == SorteTipo.INDEFINIDO:
        return True  # propaga silenciosamente; erro já reportado

    if formal.sorte == SorteTipo.PONTEIRO:
        # endereço (ponteiro) → ponteiro: mesmo tipo interno
        return (
            actual.sorte == SorteTipo.PONTEIRO
            and mesmo_tipo(formal.interno or INDEFINIDO, actual.interno or INDEFINIDO)
        )

    if formal.sorte == SorteTipo.BASICO:
        # correspondência exata: real só casa com real, inteiro só com inteiro
        return mesmo_tipo(formal, actual)

    if formal.sorte == SorteTipo.REGISTRO:
        return tipos_registro_compat(formal, actual)

    return False
