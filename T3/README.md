# Construção de Compiladores

## Trabalho 3 (T3) — Analisador Semântico

**Docente:** Daniel Lucrédio  
**Disciplina:** Construção de Compiladores – DC/UFSCar  
**Última revisão:** mar/2026  
**Alunos:** Marlon Henrique Sanches – RA819464 | Samuel Gerga Martins – RA821772

## Objetivo

O trabalho 3 (T3) consiste em implementar parte de um **analisador semântico** para a linguagem LA (Linguagem Algorítmica), desenvolvida pelo Prof. Jander Moreira (DC/UFSCar). O programa lê um fonte LA, reutiliza o léxico e o sintático do T2 (ANTLR4) e, sobre a árvore sintática, aplica um `Visitor` que mantém tabela de símbolos por escopos, detecta erros semânticos (tipo não declarado, identificador já declarado, não declarado, atribuição incompatível) **sem interromper** a análise até o fim do arquivo, e grava as mensagens no formato dos casos de teste CT3, encerrando com `Fim da compilacao`.

## Guia de Uso (DE — Documentação Externa)

### Requisitos / Dependências

| Dependência                | Versão mínima | Instalação                                   |
|---------------------------|---------------|----------------------------------------------|
| Python                    | 3.10+         | `sudo apt install python3` (Linux)           |
| antlr4-tools              | 0.2+          | `pip install antlr4-tools`                   |
| antlr4-python3-runtime    | 4.13.x        | `pip install -r requirements.txt` ou `pip install antlr4-python3-runtime==4.13.2` |
| Java (JRE)                | 11+           | `sudo apt install default-jre` (necessário pelo antlr4-tools) |

> **Nota:** a versão do `antlr4-python3-runtime` deve ser compatível com a versão do comando `antlr4`. Recomenda-se `4.13.2`. Se o `antlr4` não baixar o JAR sozinho na primeira vez: `export ANTLR4_TOOLS_ANTLR_VERSION=4.13.2`.

### Estrutura do Projeto

```
T3/
├── LA.g4                   # Gramática ANTLR4 (lexer + parser; igual conceito ao T2)
├── main.py                 # Ponto de entrada CLI (léxico → sintático → visitor semântico)
├── Makefile                # generate (-visitor), run, test, clean
├── requirements.txt        # antlr4-python3-runtime
├── README.md               # Este arquivo (documentação externa)
├── tipos.py                # Descritores de tipo e compatibilidade de atribuição
├── tabela_simbolos.py      # Pilha de escopos / símbolos
├── visitor_semantico.py    # Visitor semântico (LAVisitor)
├── LALexer.py              # (gerado) Lexer
├── LAParser.py             # (gerado) Parser
├── LAVisitor.py            # (gerado) Base do visitor
├── LAListener.py           # (gerado)
└── 3.casos_teste_t3/       # Casos de teste do professor
    ├── entrada/
    └── saida/
```

### Como compilar (gerar o lexer, o parser e o visitor)

O ANTLR4 lê a gramática `LA.g4` e gera os arquivos Python necessários (incluindo `LAVisitor.py`):

```bash
cd T3/
make generate
```

Ou diretamente:

```bash
antlr4 -Dlanguage=Python3 -visitor LA.g4
```

Isso gera `LALexer.py`, `LAParser.py`, `LAVisitor.py`, `LAListener.py`, entre outros.

### Como executar

O analisador recebe **dois argumentos obrigatórios**: o caminho do arquivo de entrada e o caminho do arquivo de saída.

```bash
python3 main.py <caminho/para/entrada> <caminho/para/saida>
```

Exemplo:

```bash
python3 main.py 3.casos_teste_t3/entrada/1.algoritmo_2-2_apostila_LA.txt /tmp/saida.txt
```

Via Makefile:

```bash
make run INPUT=3.casos_teste_t3/entrada/1.algoritmo_2-2_apostila_LA.txt OUTPUT=/tmp/saida.txt
```

### Testes automáticos

Para executar todos os 9 casos de teste semânticos e comparar com as saídas esperadas:

```bash
make test
```

As saídas geradas ficam em `build/`.

### Limpeza

Para remover arquivos gerados pelo ANTLR e a pasta de testes:

```bash
make clean
```

### Observações

- O programa **não imprime no terminal** (salvo mensagem de uso de argv): toda saída útil vai para o arquivo indicado.
- Erros **léxicos** e o **primeiro** erro **sintático** interrompem como no T2; se o parse concluir, a análise semântica acumula todos os erros até o fim e ordena por linha/coluna.
- Formato das mensagens semânticas e linha final `Fim da compilacao` seguem exatamente os gabaritos em `3.casos_teste_t3/saida/`.

## Documentação interna (DI)

- `tipos.py`: tipos básicos, ponteiros, registros anônimos, `INDEFINIDO` e regras de `<-`.
- `tabela_simbolos.py`: escopos empilhados; variável, constante, tipo nominado, procedure e função compartilham o mesmo espaço nominal no escopo atual.
- `visitor_semantico.py`: visita declarações globais, corpo do `algoritmo` (novo escopo), `procedimento`/`funcao` (escopo interno para parâmetros e locais); expressões e comandos para checagem de uso e tipos.
