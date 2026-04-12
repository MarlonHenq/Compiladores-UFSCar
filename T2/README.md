# Construção de Compiladores

## Trabalho 2 (T2) — Analisador Sintático

**Docente:** Daniel Lucrédio  
**Disciplina:** Construção de Compiladores – DC/UFSCar  
**Última revisão:** mar/2026  
**Alunos:** Marlon Henrique Sanches – RA819464 | Samuel Gerga Martins – RA821772

## Objetivo

O trabalho 2 (T2) consiste em implementar um **analisador sintático** para a linguagem LA (Linguagem Algorítmica), desenvolvida pelo Prof. Jander Moreira (DC/UFSCar). O analisador lê um programa-fonte e detecta o primeiro erro léxico ou sintático, indicando a linha e o lexema que causou o erro.

A gramática da linguagem LA foi transcrita no arquivo `LA.g4` no formato ANTLR4, que gera automaticamente o lexer (`LALexer`) e o parser (`LAParser`) em Python 3.

## Guia de Uso (DE — Documentação Externa)

### Requisitos / Dependências

| Dependência                | Versão mínima | Instalação                                   |
|---------------------------|---------------|----------------------------------------------|
| Python                    | 3.10+         | `sudo apt install python3` (Linux)           |
| antlr4-tools              | 0.2+          | `pip install antlr4-tools`                   |
| antlr4-python3-runtime    | 4.13.x        | `pip install antlr4-python3-runtime`         |
| Java (JRE)                | 11+           | `sudo apt install default-jre` (necessário pelo antlr4-tools) |

> **Nota:** a versão do `antlr4-python3-runtime` deve ser compatível com a versão do comando `antlr4`. Recomenda-se usar `pip install antlr4-python3-runtime==4.13.2`.

### Estrutura do Projeto

```
T2/
├── LA.g4                   # Gramática ANTLR4 (lexer + parser rules)
├── main.py                 # Ponto de entrada CLI do analisador
├── Makefile                # Automação: gerar parser, executar, testar
├── README.md               # Este arquivo (documentação externa)
├── LALexer.py              # (gerado) Analisador léxico
├── LAParser.py             # (gerado) Analisador sintático
├── LAListener.py           # (gerado) Listener do parser
└── 2.casos_teste_t2/       # Casos de teste fornecidos pelo professor
    ├── entrada/            #   62 arquivos de entrada
    └── saida/              #   62 arquivos de saída esperada
```

### Como compilar (gerar o lexer e o parser)

O ANTLR4 lê a gramática `LA.g4` e gera os arquivos Python necessários para o lexer e o parser:

```bash
cd T2/
make generate
```

Ou diretamente:

```bash
antlr4 -Dlanguage=Python3 LA.g4
```

Isso gera os arquivos `LALexer.py`, `LAParser.py`, `LAListener.py`, entre outros.

### Como executar

O analisador recebe **dois argumentos obrigatórios**: o caminho do arquivo de entrada e o caminho do arquivo de saída.

```bash
python3 main.py <caminho/para/entrada> <caminho/para/saida>
```

Exemplo:

```bash
python3 main.py 2.casos_teste_t2/entrada/1-algoritmo_2-2_apostila_LA_1_erro_linha_3_acusado_linha_10.txt /tmp/saida.txt
```

Via Makefile:

```bash
make run INPUT=2.casos_teste_t2/entrada/1-algoritmo_2-2_apostila_LA_1_erro_linha_3_acusado_linha_10.txt OUTPUT=/tmp/saida.txt
```

### Testes automáticos

Para executar todos os 62 casos de teste e comparar automaticamente com as saídas esperadas:

```bash
make test
```

As saídas geradas são armazenadas em `build/` para não poluir o diretório original.

### Limpeza

Para remover todos os arquivos gerados (ANTLR + testes):

```bash
make clean
```

### Observações

- O programa **nunca imprime no terminal**: toda saída vai para o arquivo indicado.
- Ao detectar o **primeiro** erro (léxico ou sintático), a análise é interrompida imediatamente.
- Erros léxicos (símbolo não identificado, cadeia não fechada, comentário não fechado) são verificados antes dos erros sintáticos.
- Formato de erro sintático: `Linha X: erro sintatico proximo a <lexema>` seguido de `Fim da compilacao`.
