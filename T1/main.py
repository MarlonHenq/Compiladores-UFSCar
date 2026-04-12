#!/usr/bin/env python3
"""CLI de execução do analisador léxico da linguagem LA.

Recebe dois argumentos obrigatórios: caminho do arquivo de entrada e caminho de saída.
Lê o código-fonte, passa pelo lexer e grava o resultado no arquivo de saída.
"""
from __future__ import annotations

import sys
from pathlib import Path

from src.lexer import LexicalError, Lexer


def main() -> None:
    if len(sys.argv) != 3:
        sys.stderr.write("Uso: python3 main.py <arquivo_entrada> <arquivo_saida>\n")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    try:
        source = input_path.read_text(encoding="utf-8")
    except OSError as exc:  # IO problems should abort early
        sys.stderr.write(f"Erro ao ler entrada: {exc}\n")
        sys.exit(1)

    lexer = Lexer()
    try:
        tokens = lexer.tokenize(source)
        error_message: str | None = None
    except LexicalError as err:
        tokens = err.partial_tokens
        error_message = err.message

    def format_token(lexeme: str, token: str) -> str:
        # Tokens de classe (IDENT, NUM_INT, NUM_REAL, CADEIA) ficam sem aspas; demais usam aspas.
        needs_quotes = token not in {"IDENT", "NUM_INT", "NUM_REAL", "CADEIA"}
        token_repr = f"'{token}'" if needs_quotes else token
        return f"<'{lexeme}',{token_repr}>"

    lines = [format_token(lexeme, token) for lexeme, token in tokens]
    if error_message:
        lines.append(error_message)

    # Sempre adiciona newline final (tanto para tokens quanto para erros)
    trailing_newline = "\n" if lines else ""
    output_path.write_text("\n".join(lines) + trailing_newline, encoding="utf-8")


if __name__ == "__main__":
    main()
