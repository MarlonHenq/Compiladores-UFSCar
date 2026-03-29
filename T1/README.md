# Construção de Compiladores

## Trabalho 1 (T1)

**Docente:** Daniel Lucrédio  
**Documento:** Especificação e critérios de notas do Trabalho 1  
**Última revisão:** mar/2026
**Alunos** - Marlon Henrique Sanches - RA819464 | Samuel Gerga Martins - RA821772

## Objetivo

O trabalho 1 (T1) da disciplina consiste em implementar um analisador léxico para a linguagem LA (Linguagem Algorítmica), desenvolvida pelo prof. Jander, no âmbito do DC/UFSCar.

O analisador léxico deve ler um programa-fonte e produzir uma lista de tokens identificados.

## Guia de uso (DE - Documentação Externa)

### Requisitos
- Python 3.10+ instalado (testado no Linux).

### Estrutura do projeto
- [main.py](main.py): ponto de entrada em linha de comando.
- [src/lexer.py](src/lexer.py): implementação do analisador léxico.
- [Makefile](Makefile): automatiza execução e testes.
- [casos_de_teste/](casos_de_teste): entradas e saídas esperadas fornecidas.

### Compilar/interpretar e executar
O analisador é interpretado em Python, sem dependências externas.

Execução direta:
```bash
python3 main.py <caminho/para/entrada> <caminho/para/saida>
```

Execução via Makefile (recomendado):
```bash
make run INPUT=caminho/para/entrada OUTPUT=caminho/para/saida
```

### Testes automáticos
Roda todos os casos em `casos_de_teste/` e compara com as saídas esperadas, gravando resultados em `build/`:
```bash
make test
```

### Observações
- O programa **não imprime no terminal**: sempre grava no arquivo de saída informado.
- Erros léxicos encerram a análise e gravam apenas a mensagem de erro no arquivo de saída.
- Atualize esta seção com os nomes dos integrantes do grupo, se aplicável.
