"""
Representação de tipos LA e compatibilidade de atribuição (T3).
Tipos indefinidos propagam após erro semântico (mistura ilegal ou nome indefinido em expressões).
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
    """Descritor imutável de tipo."""

    sorte: SorteTipo
    nome: str | None = None
    interno: Tipo | None = None
    campos: frozenset[tuple[str, Tipo]] | None = None

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
    def registro(nome_tipo_alias: str, campos_ord: tuple[tuple[str, Tipo], ...]) -> Tipo:
        return Tipo(SorteTipo.REGISTRO, nome=nome_tipo_alias, campos=frozenset(campos_ord))


INTEIRO = Tipo.basico("inteiro")
REAL = Tipo.basico("real")
LOGICO = Tipo.basico("logico")
LITERAL = Tipo.basico("literal")
INDEFINIDO = Tipo.indefinido()


def numerico(t: Tipo) -> bool:
    return t.sorte == SorteTipo.BASICO and t.nome in ("inteiro", "real")


def e_literal_basico(t: Tipo) -> bool:
    return t.sorte == SorteTipo.BASICO and t.nome == "literal"


def resultado_aritmetica_op1(op: str, a: Tipo, b: Tipo) -> Tipo:
    """Nível op1 +/- em exp_aritmetica."""
    if a.sorte == SorteTipo.INDEFINIDO or b.sorte == SorteTipo.INDEFINIDO:
        return INDEFINIDO
    if op == "+":
        if e_literal_basico(a) and e_literal_basico(b):
            return LITERAL
        if e_literal_basico(a) or e_literal_basico(b):
            return INDEFINIDO
        if numerico(a) and numerico(b):
            if a.nome == "real" or b.nome == "real":
                return REAL
            return INTEIRO
        return INDEFINIDO
    if op == "-":
        if numerico(a) and numerico(b):
            if a.nome == "real" or b.nome == "real":
                return REAL
            return INTEIRO
        return INDEFINIDO
    return INDEFINIDO


def resultado_termo(op: str, a: Tipo, b: Tipo) -> Tipo:
    if a.sorte == SorteTipo.INDEFINIDO or b.sorte == SorteTipo.INDEFINIDO:
        return INDEFINIDO
    if numerico(a) and numerico(b):
        if op == "/" or a.nome == "real" or b.nome == "real":
            return REAL
        return INTEIRO
    return INDEFINIDO


def resultado_modulo(a: Tipo, b: Tipo) -> Tipo:
    if a.sorte == SorteTipo.INDEFINIDO or b.sorte == SorteTipo.INDEFINIDO:
        return INDEFINIDO
    if a.nome == "inteiro" and b.nome == "inteiro":
        return INTEIRO
    return INDEFINIDO


def tipos_registro_compat(lhs: Tipo, rhs: Tipo) -> bool:
    return (
        lhs.sorte == SorteTipo.REGISTRO
        and rhs.sorte == SorteTipo.REGISTRO
        and lhs.nome == rhs.nome
    )


def atrib_compativel(lhs: Tipo, rhs: Tipo) -> bool:
    if rhs.sorte == SorteTipo.INDEFINIDO or lhs.sorte == SorteTipo.INDEFINIDO:
        return False

    if lhs.sorte == SorteTipo.PONTEIRO and lhs.interno:
        if rhs.sorte == SorteTipo.PONTEIRO and rhs.interno:
            return mesmo_tipo(lhs.interno, rhs.interno)
        return False

    if lhs.sorte == SorteTipo.BASICO and lhs.nome == "real":
        return rhs.sorte == SorteTipo.BASICO and rhs.nome in ("inteiro", "real")

    if lhs.sorte == SorteTipo.BASICO and lhs.nome == "literal":
        return rhs.sorte == SorteTipo.BASICO and rhs.nome == "literal"

    if lhs.sorte == SorteTipo.BASICO and lhs.nome == "logico":
        return rhs.sorte == SorteTipo.BASICO and rhs.nome == "logico"

    if lhs.sorte == SorteTipo.BASICO and lhs.nome == "inteiro":
        return rhs.sorte == SorteTipo.BASICO and rhs.nome == "inteiro"

    if lhs.sorte == SorteTipo.REGISTRO:
        return tipos_registro_compat(lhs, rhs)

    return mesmo_tipo(lhs, rhs)


def mesmo_tipo(a: Tipo, b: Tipo) -> bool:
    if a.sorte != b.sorte:
        return False
    if a.sorte == SorteTipo.INDEFINIDO:
        return True
    if a.sorte == SorteTipo.BASICO:
        return a.nome == b.nome
    if a.sorte == SorteTipo.PONTEIRO:
        ai, bi = a.interno or INDEFINIDO, b.interno or INDEFINIDO
        return mesmo_tipo(ai, bi)
    if a.sorte == SorteTipo.REGISTRO:
        return a.nome == b.nome and a.campos == b.campos
    return False
