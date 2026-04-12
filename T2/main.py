#!/usr/bin/env python3
"""
Analisador Sintático da Linguagem LA (Linguagem Algorítmica)
=============================================================
Trabalho 2 – Construção de Compiladores – UFSCar (DC)
Alunos: Marlon Henrique Sanches (RA819464) | Samuel Gerga Martins (RA821772)

Este módulo é o ponto de entrada (CLI) do analisador sintático.
Ele lê um arquivo-fonte em LA, executa a análise léxica e sintática
usando os artefatos gerados pelo ANTLR4 (LALexer, LAParser), e
grava o resultado (erros encontrados) em um arquivo de saída.

Fluxo principal:
  1. Leitura dos argumentos de linha de comando (entrada e saída).
  2. Criação do fluxo de entrada (FileStream) e do lexer (LALexer).
  3. Pré-scan dos tokens: percorre todos os tokens gerados pelo lexer
     buscando erros léxicos (comentário não fechado, cadeia não fechada,
     símbolo não identificado). Se encontrar, grava a mensagem e para.
  4. Se não houver erro léxico, executa o parser (LAParser.programa())
     com um ErrorListener customizado para capturar o primeiro erro
     sintático.
  5. Grava o resultado no arquivo de saída. Nunca imprime no terminal.

Uso:
  python3 main.py <arquivo_entrada> <arquivo_saida>
"""
from __future__ import annotations

import sys
from pathlib import Path

# Importações do ANTLR4 runtime para Python
from antlr4 import CommonTokenStream, FileStream
from antlr4.error.ErrorListener import ErrorListener

# Importações dos artefatos gerados pelo ANTLR4 a partir de LA.g4
from LALexer import LALexer
from LAParser import LAParser


# ---------------------------------------------------------------------------
# Exceção usada para interromper o parser no primeiro erro sintático
# ---------------------------------------------------------------------------
class ErroSintaticoException(Exception):
    """Exceção lançada pelo CustomErrorListener para abortar o parsing
    imediatamente após o primeiro erro sintático ser detectado."""
    pass


# ---------------------------------------------------------------------------
# ErrorListener customizado — intercepta erros do ANTLR e formata a saída
# ---------------------------------------------------------------------------
class CustomErrorListener(ErrorListener):
    """Listener de erros que captura a primeira mensagem de erro sintático
    no formato exigido pelo professor:
        Linha X: erro sintatico proximo a <lexema>

    Ao detectar o primeiro erro, lança ErroSintaticoException para
    interromper imediatamente o parsing (sem recuperação de erros).
    """

    def __init__(self):
        super().__init__()
        # Armazena a mensagem do primeiro erro (úinico relevante)
        self.mensagem_erro: str | None = None

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        """Método chamado pelo ANTLR ao encontrar um erro sintático.

        Parâmetros (providos pelo ANTLR):
            recognizer     – o parser ou lexer que detectou o erro
            offendingSymbol – o token que causou o erro
            line           – número da linha onde o erro ocorreu
            column         – coluna onde o erro ocorreu
            msg            – mensagem de erro padrão do ANTLR
            e              – exceção original (RecognitionException)
        """
        # Ignora erros subsequentes — apenas o primeiro importa
        if self.mensagem_erro is not None:
            raise ErroSintaticoException()

        # Obtém o texto do token problemático
        texto_token = offendingSymbol.text if offendingSymbol else "EOF"

        # Trata o caso especial de fim de arquivo: ANTLR usa '<EOF>',
        # mas a saída esperada usa apenas 'EOF' (sem os sinais < >)
        if texto_token == "<EOF>":
            texto_token = "EOF"

        # Formata a mensagem no padrão exigido
        self.mensagem_erro = f"Linha {line}: erro sintatico proximo a {texto_token}"

        # Interrompe o parsing imediatamente (sem tentar recuperação)
        raise ErroSintaticoException()


# ---------------------------------------------------------------------------
# Função auxiliar para gravar a saída no arquivo
# ---------------------------------------------------------------------------
def gravar_saida(caminho_saida: Path, conteudo: str) -> None:
    """Grava o conteúdo no arquivo de saída indicado.
    Cria diretórios intermediários se necessário."""
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    caminho_saida.write_text(conteudo, encoding="utf-8")


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------
def main() -> None:
    """Ponto de entrada do analisador sintático.

    Espera exatamente dois argumentos de linha de comando:
      argv[1] = caminho do arquivo de entrada (código-fonte LA)
      argv[2] = caminho do arquivo de saída (resultado da análise)
    """

    # --- Validação dos argumentos de linha de comando ---
    if len(sys.argv) != 3:
        sys.stderr.write("Uso: python3 main.py <arquivo_entrada> <arquivo_saida>\n")
        sys.exit(1)

    caminho_entrada = Path(sys.argv[1])
    caminho_saida = Path(sys.argv[2])

    # --- Etapa 1: Criação do fluxo de entrada e do lexer ---
    # FileStream lê o arquivo e fornece os caracteres ao LALexer.
    fluxo_entrada = FileStream(str(caminho_entrada), encoding="utf-8")

    # Cria o lexer gerado pelo ANTLR4 a partir da gramática LA.g4.
    lexer = LALexer(fluxo_entrada)

    # Remove o listener padrão do lexer (que imprime no console)
    # para garantir que nenhuma saída vá para o terminal.
    lexer.removeErrorListeners()

    # --- Etapa 2: Geração do fluxo de tokens ---
    # CommonTokenStream armazena todos os tokens produzidos pelo lexer.
    fluxo_tokens = CommonTokenStream(lexer)

    # Preenche o fluxo com todos os tokens do arquivo de entrada.
    # Isso permite percorrer os tokens antes do parsing (pré-scan).
    fluxo_tokens.fill()

    # --- Etapa 3: Pré-scan para erros léxicos ---
    # Percorre todos os tokens buscando tokens de erro léxico.
    # Erros léxicos têm prioridade sobre erros sintáticos, por isso
    # são verificados antes de iniciar o parsing.
    # Ao encontrar o PRIMEIRO erro léxico, grava a mensagem e encerra.
    for token in fluxo_tokens.tokens:
        tipo_token = token.type

        # Comentário aberto sem fechamento: { ... (sem })
        if tipo_token == LALexer.COMENTARIO_NAO_FECHADO:
            mensagem = f"Linha {token.line}: comentario nao fechado\n"
            mensagem += "Fim da compilacao\n"
            gravar_saida(caminho_saida, mensagem)
            return

        # Cadeia literal não fechada: " ... (sem " de fechamento)
        if tipo_token == LALexer.CADEIA_NAO_FECHADA:
            mensagem = f"Linha {token.line}: cadeia literal nao fechada\n"
            mensagem += "Fim da compilacao\n"
            gravar_saida(caminho_saida, mensagem)
            return

        # Símbolo não identificado: qualquer caractere inválido
        if tipo_token == LALexer.ERRO:
            mensagem = f"Linha {token.line}: {token.text} - simbolo nao identificado\n"
            mensagem += "Fim da compilacao\n"
            gravar_saida(caminho_saida, mensagem)
            return

    # --- Etapa 4: Análise sintática (parsing) ---
    # Se não houve erro léxico, reinicia o fluxo de tokens e executa
    # o parser para verificar a estrutura sintática do programa.
    fluxo_tokens.reset()

    # Cria o parser gerado pelo ANTLR4.
    parser = LAParser(fluxo_tokens)

    # Remove os listeners padrão (que imprimem no console) e adiciona
    # nosso listener customizado para formatar os erros corretamente.
    parser.removeErrorListeners()
    listener_erros = CustomErrorListener()
    parser.addErrorListener(listener_erros)

    # Executa o parsing a partir da regra inicial 'programa'.
    # Se um erro sintático ocorrer, o CustomErrorListener lança
    # ErroSintaticoException para interromper imediatamente.
    try:
        parser.programa()
    except ErroSintaticoException:
        pass  # Erro já foi capturado pelo listener

    # --- Etapa 5: Gravação do resultado ---
    if listener_erros.mensagem_erro:
        # Houve erro sintático: grava a mensagem formatada
        resultado = listener_erros.mensagem_erro + "\n"
        resultado += "Fim da compilacao\n"
        gravar_saida(caminho_saida, resultado)
    else:
        # Programa sem erros: arquivo de saída vazio
        gravar_saida(caminho_saida, "")


# Ponto de entrada quando executado diretamente
if __name__ == "__main__":
    main()
