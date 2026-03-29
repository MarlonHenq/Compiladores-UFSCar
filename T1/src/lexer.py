from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class LexicalError(Exception):
    line: int
    message: str
    partial_tokens: List[Tuple[str, str]]

    def __str__(self) -> str:  # pragma: no cover - mensagem já formatada
        return self.message


class Lexer:
    def __init__(self) -> None:
        self.keywords = {
            "algoritmo",
            "fim_algoritmo",
            "declare",
            "constante",
            "literal",
            "inteiro",
            "real",
            "logico",
            "verdadeiro",
            "falso",
            "registro",
            "fim_registro",
            "procedimento",
            "fim_procedimento",
            "funcao",
            "fim_funcao",
            "var",
            "tipo",
            "leia",
            "escreva",
            "se",
            "senao",
            "entao",
            "fim_se",
            "caso",
            "seja",
            "fim_caso",
            "para",
            "ate",
            "faca",
            "fim_para",
            "enquanto",
            "fim_enquanto",
            "retorne",
            "nao",
            "ou",
            "e",
        }
        self.multi_ops = ["<-", ">=", "<=", "<>", ".."]
        self.single_ops = {
            "+",
            "-",
            "*",
            "/",
            "%",
            "(",
            ")",
            ",",
            ".",
            ":",
            ";",
            "[",
            "]",
            "<",
            ">",
            "=",
            "^",
            "&",
        }

    def tokenize(self, source: str) -> List[Tuple[str, str]]:
        tokens: List[Tuple[str, str]] = []

        for line_no, raw_line in enumerate(source.splitlines(), start=1):
            line = raw_line
            i = 0
            length = len(line)

            while i < length:
                ch = line[i]

                # Ignora espaços e tabs
                if ch.isspace():
                    i += 1
                    continue

                # Comentários { ... } precisam fechar na mesma linha
                if ch == "{":
                    end = line.find("}", i + 1)
                    if end == -1:
                        raise LexicalError(line_no, f"Linha {line_no}: comentario nao fechado", tokens)
                    i = end + 1
                    continue

                # Cadeias literais entre aspas duplas, sem escapes
                if ch == "\"":
                    end = line.find("\"", i + 1)
                    if end == -1:
                        raise LexicalError(line_no, f"Linha {line_no}: cadeia literal nao fechada", tokens)
                    lexeme = line[i : end + 1]
                    tokens.append((lexeme, "CADEIA"))
                    i = end + 1
                    continue

                # Operadores de múltiplos caracteres primeiro para evitar ambiguidade
                matched_multi = False
                for op in self.multi_ops:
                    if line.startswith(op, i):
                        tokens.append((op, op))
                        i += len(op)
                        matched_multi = True
                        break
                if matched_multi:
                    continue

                # Números: tenta real antes de inteiro para capturar parte fracionária
                if ch.isdigit():
                    start = i
                    while i < length and line[i].isdigit():
                        i += 1
                    if i < length and line[i] == "." and (i + 1) < length and line[i + 1].isdigit():
                        i += 1  # consome ponto
                        while i < length and line[i].isdigit():
                            i += 1
                        lexeme = line[start:i]
                        tokens.append((lexeme, "NUM_REAL"))
                    else:
                        lexeme = line[start:i]
                        tokens.append((lexeme, "NUM_INT"))
                    continue

                # Identificadores ou palavras-chave
                if ch.isalpha() or ch == "_":
                    start = i
                    i += 1
                    while i < length and (line[i].isalnum() or line[i] == "_"):
                        i += 1
                    lexeme = line[start:i]
                    token = lexeme if lexeme in self.keywords else "IDENT"
                    tokens.append((lexeme, token))
                    continue

                # Operadores/delimitadores de um caractere
                if ch in self.single_ops:
                    tokens.append((ch, ch))
                    i += 1
                    continue

                # Símbolo não identificado
                raise LexicalError(line_no, f"Linha {line_no}: {ch} - simbolo nao identificado", tokens)

        return tokens
