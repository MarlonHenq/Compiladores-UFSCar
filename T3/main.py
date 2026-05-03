#!/usr/bin/env python3
"""Analisador léxico/sintático/semántico LA (T3) — entrada e saída em arquivo."""
from __future__ import annotations

import sys
from pathlib import Path

from antlr4 import CommonTokenStream, FileStream
from antlr4.error.ErrorListener import ErrorListener

from LALexer import LALexer
from LAParser import LAParser

from tabela_simbolos import TabelaSimbolos
from visitor_semantico import VisitorSemantico


class ErroSintaticoException(Exception):
    pass


class CustomErrorListener(ErrorListener):
    def __init__(self) -> None:
        super().__init__()
        self.mensagem_erro: str | None = None

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        if self.mensagem_erro is not None:
            raise ErroSintaticoException()
        texto_token = offendingSymbol.text if offendingSymbol else "EOF"
        if texto_token == "<EOF>":
            texto_token = "EOF"
        self.mensagem_erro = f"Linha {line}: erro sintatico proximo a {texto_token}"
        raise ErroSintaticoException()


def gravar_saida(path: Path, conteudo: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(conteudo, encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 3:
        sys.stderr.write("Uso: python3 main.py <arquivo_entrada> <arquivo_saida>\n")
        sys.exit(1)

    caminho_entrada = Path(sys.argv[1])
    caminho_saida = Path(sys.argv[2])

    fluxo = FileStream(str(caminho_entrada), encoding="utf-8")
    lexer = LALexer(fluxo)
    lexer.removeErrorListeners()
    fts = CommonTokenStream(lexer)
    fts.fill()

    for token in fts.tokens:
        if token.type == LALexer.COMENTARIO_NAO_FECHADO:
            gravar_saida(
                caminho_saida,
                f"Linha {token.line}: comentario nao fechado\nFim da compilacao\n",
            )
            return
        if token.type == LALexer.CADEIA_NAO_FECHADA:
            gravar_saida(
                caminho_saida,
                f"Linha {token.line}: cadeia literal nao fechada\nFim da compilacao\n",
            )
            return
        if token.type == LALexer.ERRO:
            gravar_saida(
                caminho_saida,
                f"Linha {token.line}: {token.text} - simbolo nao identificado\nFim da compilacao\n",
            )
            return

    fts.reset()
    parser = LAParser(fts)
    parser.removeErrorListeners()
    lst = CustomErrorListener()
    parser.addErrorListener(lst)

    tree = None
    try:
        tree = parser.programa()
    except ErroSintaticoException:
        pass

    if lst.mensagem_erro:
        gravar_saida(
            caminho_saida,
            lst.mensagem_erro + "\nFim da compilacao\n",
        )
        return

    ts = TabelaSimbolos()
    vis = VisitorSemantico(ts)
    vis.visit(tree)
    gravar_saida(caminho_saida, vis.formatar_erros())


if __name__ == "__main__":
    main()
