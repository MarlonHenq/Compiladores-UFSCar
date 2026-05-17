# Construção de Compiladores

## Trabalho 4 (T4) — Analisador Semântico (parte 2)

**Docente:** Daniel Lucrédio  
**Disciplina:** Construção de Compiladores – DC/UFSCar  
**Última revisão:** mai/2026  
**Alunos:** Marlon Henrique Sanches – RA819464 | Samuel Gerga Martins – RA821772

## Objetivo

O trabalho 4 (T4) consiste em implementar a segunda parte do **analisador semântico** para a linguagem LA (Linguagem Algorítmica), desenvolvida pelo Prof. Jander Moreira (DC/UFSCar). O programa reutiliza o léxico e o sintático gerados pelo ANTLR4 (herdados do T2/T3) e, sobre a árvore sintática, aplica um `Visitor` que estende as verificações do T3 com cinco novos grupos de erros:

1. **Identificador já declarado** — incluindo colisão com símbolos de escopos externos (ex.: variável no corpo do algoritmo cujo nome repete um procedimento global).
2. **Identificador não declarado** — mensagem com caminho completo do identificador (`vinho.Preco`, `vinhocaro.tipoVinho`).
3. **Incompatibilidade de parâmetros** — quantidade e tipos exatos na chamada de função/procedimento; sem promoção `inteiro → real` em passagem de parâmetros.
4. **Atribuição incompatível** — cobertura de ponteiros (`^var ← literal`) e registros; LHS inclui o prefixo e qualificadores (`^ponteiro`, `ponto1.x`, `valor[0]`).
5. **`retorne` fora de função** — válido apenas dentro de `funcao`; proibido em `procedimento` e no corpo do `algoritmo`.

A análise **não interrompe** ao encontrar um erro: todos os problemas são acumulados e gravados no arquivo de saída, encerrando com `Fim da compilacao`.

## Guia de Uso (DE — Documentação Externa)

### Requisitos / Dependências

| Dependência                | Versão mínima | Instalação                                   |
|---------------------------|---------------|----------------------------------------------|
| Python                    | 3.10+         | `sudo apt install python3` (Linux)           |
| antlr4-tools              | 0.2+          | `pip install antlr4-tools`                   |
| antlr4-python3-runtime    | 4.13.x        | `pip install -r requirements.txt`            |
| Java (JRE)                | 11+           | `sudo apt install default-jre` (requerido pelo antlr4-tools) |

> **Nota:** a versão do `antlr4-python3-runtime` deve ser compatível com o JAR do ANTLR. Recomenda-se `4.13.2`. Se o `antlr4` não baixar o JAR sozinho na primeira execução: `export ANTLR4_TOOLS_ANTLR_VERSION=4.13.2`.

### Estrutura do Projeto

```
T4/
├── LA.g4                   # Gramática ANTLR4 (lexer + parser; mesma base do T2/T3)
├── main.py                 # Ponto de entrada CLI (léxico → sintático → visitor semântico)
├── Makefile                # generate (-visitor), run, test (CT4), clean
├── requirements.txt        # antlr4-python3-runtime
├── README.md               # Este arquivo (documentação externa)
├── tipos.py                # Descritores de tipo, atrib_compativel, argumento_compativel_com_parametro
├── tabela_simbolos.py      # Pilha de escopos / tabela de símbolos
├── visitor_semantico.py    # Visitor semântico (T4)
├── LALexer.py              # (gerado) Lexer
├── LAParser.py             # (gerado) Parser
├── LAVisitor.py            # (gerado) Base do visitor
├── LAListener.py           # (gerado)
└── 4.casos_teste_t4/       # Casos de teste do professor
    ├── entrada/
    └── saida/
```

### Como compilar (gerar o lexer, o parser e o visitor)

O ANTLR4 lê a gramática `LA.g4` e gera os arquivos Python necessários (incluindo `LAVisitor.py`):

```bash
cd T4/
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
python3 main.py 4.casos_teste_t4/entrada/1.algoritmo_7-2_apostila_LA.txt /tmp/saida.txt
```

Via Makefile:

```bash
make run INPUT=4.casos_teste_t4/entrada/1.algoritmo_7-2_apostila_LA.txt OUTPUT=/tmp/saida.txt
```

### Testes automáticos

Para executar todos os 9 casos de teste semânticos (CT4) e comparar com as saídas esperadas:

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

- O programa **não imprime no terminal**: toda saída vai para o arquivo indicado.
- Erros **léxicos** (símbolo não identificado, cadeia/comentário não fechado) e o **primeiro** erro **sintático** interrompem como no T2/T3.
- A análise semântica acumula todos os erros até o fim do arquivo e ordena por linha/coluna.
- Formato das mensagens e linha final `Fim da compilacao` seguem exatamente os gabaritos em `4.casos_teste_t4/saida/`.

## Documentação Interna (DI)

### `tipos.py`

Contém os descritores de tipo da linguagem LA:

- `Tipo` (dataclass imutável): representa tipos básicos (`inteiro`, `real`, `literal`, `logico`), ponteiros (`^T`) e registros (conjunto de campos com rótulo de tipo).
- `INDEFINIDO`: tipo sentinela propagado quando uma expressão contém erros; evita cascata de mensagens.
- `atrib_compativel(lhs, rhs)`: regras de atribuição (`<-`) segundo o PDF T4. Permite `(real|inteiro) ← (real|inteiro)`, `literal ← literal`, `logico ← logico`, `registro ← registro` (mesmo nome), `ponteiro ← endereço`.
- `argumento_compativel_com_parametro(formal, actual)` (**novo em T4**): igual à tabela do PDF mas sem promoção `inteiro → real` — passagem de parâmetros exige tipos exatos.
- Registros nomeados (declarados com `tipo X: registro`) usam `X` como rótulo; registros anônimos (inline) usam tag interna `@r<id>`. Isso permite verificar compatibilidade por nome de tipo em vez de estrutura.

### `tabela_simbolos.py`

Gerencia escopos em pilha (`list[dict[str, Simbolo]]`):

- Escopo 0 = global (procedimentos, funções, tipos e constantes declarados antes do `algoritmo`).
- `push_escopo` / `pop_escopo`: abre/fecha um nível ao entrar/sair de sub-rotinas ou do corpo do `algoritmo`.
- `buscar_encadeado(nome)`: percorre do topo para a base — usado **em T4** para detectar redeclarações mesmo entre escopos (ex.: variável no `algoritmo` que repete um procedimento global).
- `existe_local(nome)`: verifica apenas o topo (usado internamente; os checks de T4 usam `buscar_encadeado`).

### `visitor_semantico.py`

Implementa `VisitorSemantico(LAVisitor)`. Estado principal:

- `tb`: tabela de símbolos
- `erros`: lista de `(linha, coluna, mensagem)` acumulados
- `_em_funcao` (**novo em T4**): `True` apenas dentro do corpo de uma `funcao`; controla a validade do `retorne`

Decisões de projeto relevantes:

| Aspecto | Implementação |
|---------|---------------|
| Já declarado (T4) | `buscar_encadeado` em todas as inserções; detecta colisão com qualquer escopo visível |
| Não declarado – mensagem | `idctx.getText()` devolve o caminho completo (`vinho.Preco`); usado em todos os erros de `_tipo_de_ident_uso` |
| LHS de atribuição | `("^" if circunf else "") + idctx.getText()` — inclui `^`, campos e índices |
| Parâmetros (T4) | `_tipo_chamada` avalia os argumentos, compara count e tipos com `argumento_compativel_com_parametro`; emite uma única mensagem por chamada |
| `retorne` (T4) | `visitCmdRetorne` verifica `_em_funcao`; token `ctx.start` fornece a linha |
| Registro nomeado | `_construir_tipo` aceita `nome_alias`; `visitDeclaracao_local` passa o alias para tipo registro |
