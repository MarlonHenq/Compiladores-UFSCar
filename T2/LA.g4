/*
 * Gramática da linguagem LA (Linguagem Algorítmica)
 * ===================================================
 * Trabalho 2 – Construção de Compiladores – UFSCar (DC)
 * Alunos: Marlon Henrique Sanches (RA819464) | Samuel Gerga Martins (RA821772)
 *
 * Baseada na gramática original dos professores:
 *   - Prof. Daniel Lucrédio e Profa. Helena de Medeiros Caseli
 *   - Autor da linguagem LA: Prof. Jander Moreira (DC/UFSCar)
 *   - Versão da gramática: 13/ago/2018
 *
 * Esta gramática combinada (lexer + parser) é usada pelo ANTLR4 para gerar
 * automaticamente o analisador léxico (LALexer) e o analisador sintático
 * (LAParser) em Python 3.
 *
 * Processo de compilação:
 *   antlr4 -Dlanguage=Python3 LA.g4
 *
 * O arquivo gera: LALexer.py, LAParser.py, LAListener.py, LA.tokens, etc.
 */
grammar LA;

/* ================================================================
 * REGRAS SINTÁTICAS (Parser Rules)
 * ================================================================
 * Cada regra define uma produção da gramática. As regras parser
 * começam com letra minúscula e referenciam tokens (lexer rules)
 * e outras regras parser.
 * ================================================================ */

/*
 * Regra inicial: um programa LA começa com declarações opcionais,
 * seguidas da palavra-chave 'algoritmo', o corpo do programa, e
 * encerra com 'fim_algoritmo'.
 */
programa
    : declaracoes 'algoritmo' corpo 'fim_algoritmo'
    ;

/* Conjunto de declarações globais e locais que precedem o algoritmo. */
declaracoes
    : (decl_local_global)*
    ;

/* Uma declaração pode ser local (variáveis, constantes, tipos) ou global (procedimentos, funções). */
decl_local_global
    : declaracao_local
    | declaracao_global
    ;

/*
 * Declaração local:
 *   - 'declare' seguido da declaração de variável(is),
 *   - 'constante' define uma constante tipada com valor,
 *   - 'tipo' define um novo tipo (ex.: registro).
 */
declaracao_local
    : 'declare' variavel
    | 'constante' IDENT ':' tipo_basico '=' valor_constante
    | 'tipo' IDENT ':' tipo
    ;

/*
 * Declaração de variável: uma lista de identificadores separados
 * por vírgula, seguida de ':' e o tipo.
 * Exemplo: x, y, z: inteiro
 */
variavel
    : identificador (',' identificador)* ':' tipo
    ;

/*
 * Identificador: nome composto por IDENT com acesso a campos via '.'
 * e dimensões de vetores/matrizes via '[ ]'.
 * Exemplos: x, pessoa.nome, matriz[i][j]
 */
identificador
    : IDENT ('.' IDENT)* dimensao
    ;

/* Dimensão para vetores/matrizes: zero ou mais pares '[expressão]'. */
dimensao
    : ('[' exp_aritmetica ']')*
    ;

/* Tipo: pode ser um registro ou um tipo estendido (básico ou ponteiro). */
tipo
    : registro
    | tipo_estendido
    ;

/* Tipos básicos da linguagem LA. */
tipo_basico
    : 'literal'
    | 'inteiro'
    | 'real'
    | 'logico'
    ;

/* Tipo básico ou identificador de tipo definido pelo usuário. */
tipo_basico_ident
    : tipo_basico
    | IDENT
    ;

/*
 * Tipo estendido: opcionalmente precedido por '^' (ponteiro).
 * Exemplos: inteiro, ^inteiro, MeuTipo
 */
tipo_estendido
    : '^'? tipo_basico_ident
    ;

/* Valores constantes aceitos em declaração de constantes. */
valor_constante
    : CADEIA
    | NUM_INT
    | NUM_REAL
    | 'verdadeiro'
    | 'falso'
    ;

/*
 * Registro: tipo estruturado com uma ou mais declarações de variável.
 * Exemplo: registro  nome: literal  idade: inteiro  fim_registro
 */
registro
    : 'registro' variavel+ 'fim_registro'
    ;

/*
 * Declarações globais: procedimentos e funções.
 * Procedimentos não retornam valor; funções retornam um tipo_estendido.
 */
declaracao_global
    : 'procedimento' IDENT '(' parametros? ')' declaracao_local* cmd* 'fim_procedimento'
    | 'funcao' IDENT '(' parametros? ')' ':' tipo_estendido declaracao_local* cmd* 'fim_funcao'
    ;

/*
 * Parâmetro formal: opcionalmente precedido por 'var' (passagem por referência),
 * seguido de identificadores e seu tipo.
 */
parametro
    : 'var'? identificador (',' identificador)* ':' tipo_estendido
    ;

/* Lista de parâmetros separados por vírgula. */
parametros
    : parametro (',' parametro)*
    ;

/* Corpo do programa: declarações locais seguidas de comandos. */
corpo
    : declaracao_local* cmd*
    ;

/*
 * Comando: qualquer instrução executável da linguagem LA.
 * IMPORTANTE: cmdChamada vem ANTES de cmdAtribuicao porque ambos
 * podem iniciar com IDENT, e o parser precisa verificar se '(' segue
 * o IDENT (chamada de procedimento) antes de tentar atribuição.
 */
cmd
    : cmdLeia
    | cmdEscreva
    | cmdSe
    | cmdCaso
    | cmdPara
    | cmdEnquanto
    | cmdFaca
    | cmdChamada
    | cmdAtribuicao
    | cmdRetorne
    ;

/* Comando de leitura: leia uma ou mais variáveis. '^' para ponteiros. */
cmdLeia
    : 'leia' '(' '^'? identificador (',' '^'? identificador)* ')'
    ;

/* Comando de escrita: escreva uma ou mais expressões. */
cmdEscreva
    : 'escreva' '(' expressao (',' expressao)* ')'
    ;

/* Comando condicional: se-então-senão com fechamento obrigatório. */
cmdSe
    : 'se' expressao 'entao' cmd* ('senao' cmd*)? 'fim_se'
    ;

/* Comando caso (switch): seleciona com base em expressão aritmética. */
cmdCaso
    : 'caso' exp_aritmetica 'seja' selecao ('senao' cmd*)? 'fim_caso'
    ;

/* Comando para (for): iteração com variável contadora. */
cmdPara
    : 'para' IDENT '<-' exp_aritmetica 'ate' exp_aritmetica 'faca' cmd* 'fim_para'
    ;

/* Comando enquanto (while): repetição com teste no início. */
cmdEnquanto
    : 'enquanto' expressao 'faca' cmd* 'fim_enquanto'
    ;

/* Comando faça-até (do-while): repetição com teste no final. */
cmdFaca
    : 'faca' cmd* 'ate' expressao
    ;

/* Comando de atribuição: atribui valor a variável. '^' para ponteiros. */
cmdAtribuicao
    : '^'? identificador '<-' expressao
    ;

/* Chamada de procedimento/função como comando. */
cmdChamada
    : IDENT '(' expressao (',' expressao)* ')'
    ;

/* Comando de retorno: retorna valor de uma função. */
cmdRetorne
    : 'retorne' expressao
    ;

/* ================================================================
 * Regras de seleção (usadas em cmdCaso)
 * ================================================================ */

/* Lista de itens de seleção (pode ser vazia). */
selecao
    : item_selecao*
    ;

/* Item de seleção: constantes seguidas de ':' e comandos. */
item_selecao
    : constantes ':' cmd*
    ;

/* Lista de constantes numéricas ou intervalos, separadas por vírgula. */
constantes
    : numero_intervalo (',' numero_intervalo)*
    ;

/*
 * Número ou intervalo: um inteiro com sinal opcional,
 * opcionalmente seguido de '..' e outro inteiro (intervalo).
 * Exemplos: 1, -5, 1..10, -3..3
 */
numero_intervalo
    : op_unario? NUM_INT ('..' op_unario? NUM_INT)?
    ;

/* Operador unário: apenas o sinal de negação. */
op_unario
    : '-'
    ;

/* ================================================================
 * Regras de expressões
 * ================================================================
 * Hierarquia de precedência (menor para maior):
 *   expressao      → op_logico_1 ('ou')   → disjunção lógica
 *   termo_logico   → op_logico_2 ('e')    → conjunção lógica
 *   fator_logico   → 'nao' (negação)      → negação lógica
 *   parcela_logica → verdadeiro/falso ou exp_relacional
 *   exp_relacional → comparação aritmética
 *   exp_aritmetica → op1 (+, -)           → soma/subtração
 *   termo          → op2 (*, /)           → multiplicação/divisão
 *   fator          → op3 (%)              → módulo
 *   parcela        → valores e chamadas
 * ================================================================ */

/* Expressão lógica: disjunção (OR) de termos lógicos. */
expressao
    : termo_logico (op_logico_1 termo_logico)*
    ;

/* Termo lógico: conjunção (AND) de fatores lógicos. */
termo_logico
    : fator_logico (op_logico_2 fator_logico)*
    ;

/* Fator lógico: negação opcional de parcela lógica. */
fator_logico
    : 'nao'? parcela_logica
    ;

/* Parcela lógica: valor booleano literal ou expressão relacional. */
parcela_logica
    : ('verdadeiro' | 'falso')
    | exp_relacional
    ;

/* Expressão relacional: comparação opcional entre duas exp. aritméticas. */
exp_relacional
    : exp_aritmetica (op_relacional exp_aritmetica)?
    ;

/* Operadores relacionais. */
op_relacional
    : '='
    | '<>'
    | '>='
    | '<='
    | '>'
    | '<'
    ;

/* Expressão aritmética: soma/subtração de termos. */
exp_aritmetica
    : termo (op1 termo)*
    ;

/* Termo: multiplicação/divisão de fatores. */
termo
    : fator (op2 fator)*
    ;

/* Fator: módulo de parcelas. */
fator
    : parcela (op3 parcela)*
    ;

/* Operadores aritméticos por nível de precedência. */
op1 : '+' | '-' ;
op2 : '*' | '/' ;
op3 : '%' ;

/*
 * Parcela: pode ter operador unário na frente de parcela_unario,
 * ou ser uma parcela_nao_unario (cadeia ou endereço).
 */
parcela
    : op_unario? parcela_unario
    | parcela_nao_unario
    ;

/*
 * Parcela unário: valores e chamadas de função usados em expressões.
 * IMPORTANTE: a alternativa de chamada de função (IDENT '(' ... ')')
 * vem ANTES da alternativa de identificador simples, pois ambas
 * iniciam com IDENT e o parser precisa distinguir pela presença de '('.
 */
parcela_unario
    : IDENT '(' expressao (',' expressao)* ')'
    | '^'? identificador
    | NUM_INT
    | NUM_REAL
    | '(' expressao ')'
    ;

/* Parcela não-unário: endereço de variável ou cadeia literal. */
parcela_nao_unario
    : '&' identificador
    | CADEIA
    ;

/* Operadores lógicos. */
op_logico_1 : 'ou' ;
op_logico_2 : 'e' ;


/* ================================================================
 * REGRAS LÉXICAS (Lexer Rules)
 * ================================================================
 * Regras de lexer começam com letra maiúscula. A ordem importa:
 * em caso de empate de comprimento, a regra definida primeiro vence.
 * O ANTLR4 usa "maximal munch" (maior casamento possível).
 * ================================================================ */

/*
 * Literais numéricos:
 * NUM_REAL vem antes de NUM_INT para que '3.14' seja reconhecido
 * como um único token REAL em vez de INT + ponto + INT.
 * (Na prática, o maximal munch do ANTLR4 resolve, mas a ordem
 * garante desempate se ambos tiverem o mesmo comprimento.)
 */
NUM_INT
    : ('0'..'9')+
    ;

NUM_REAL
    : ('0'..'9')+ '.' ('0'..'9')+
    ;

/*
 * Cadeia de caracteres (string):
 * Delimitada por aspas duplas ("), não pode ultrapassar a linha.
 * Exemplos: "Olá mundo", "123"
 */
CADEIA
    : '"' ~["\r\n]* '"'
    ;

/*
 * Identificador:
 * Começa com letra (a-z, A-Z) ou underscore (_), seguido de
 * letras, dígitos ou underscores. Exemplos: x, _temp, nome1
 *
 * Palavras-chave usadas em string literal nos parser rules
 * (ex.: 'algoritmo') geram tokens implícitos com prioridade
 * maior que IDENT, portanto 'algoritmo' nunca é confundido
 * com um identificador.
 */
IDENT
    : [a-zA-Z_][a-zA-Z0-9_]*
    ;

/*
 * Comentários: delimitados por '{' e '}'. Podem abranger
 * múltiplas linhas. São descartados (-> skip) durante a análise.
 */
COMENTARIO
    : '{' ~[}]* '}' -> skip
    ;

/*
 * Espaços em branco e quebras de linha: descartados.
 * Inclui espaço, tabulação, retorno de carro e nova linha.
 */
WS
    : [ \t\r\n]+ -> skip
    ;

/* ================================================================
 * TOKENS DE ERRO (baixa prioridade — definidos por último)
 * ================================================================
 * Esses tokens capturam situações de erro léxico sem que o lexer
 * do ANTLR lance exceções. Eles ficam no fluxo de tokens e são
 * detectados no pré-scan do main.py antes do parsing.
 * ================================================================ */

/*
 * Comentário aberto sem fechamento: '{' seguido de qualquer
 * coisa até o fim do arquivo, sem encontrar '}'.
 * A regra COMENTARIO (mais longa, pois inclui '}') vence quando
 * o comentário está fechado; esta regra só casa quando não há '}'.
 */
COMENTARIO_NAO_FECHADO
    : '{' ~[}]*
    ;

/*
 * Cadeia literal não fechada: aspas duplas de abertura sem
 * aspas de fechamento na mesma linha. Mesma lógica de prioridade:
 * CADEIA (com fechamento) produz token mais longo e vence.
 */
CADEIA_NAO_FECHADA
    : '"' ~["\r\n]*
    ;

/*
 * Qualquer caractere não reconhecido pelas regras anteriores.
 * Exemplos: @, !, |, #, $, etc.
 * Casa exatamente um caractere — é a regra de menor prioridade.
 */
ERRO
    : .
    ;
