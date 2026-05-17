/*
 * Gramática da linguagem LA (Linguagem Algorítmica)
 * ===================================================
 * Trabalho 4 – analisador semântico avançado (DC/UFSCar)
 *
 * A sintaxe é idêntica à usada no T2/T3.  O T4 acrescenta verificações
 * semânticas sobre ponteiros, registros, funções, procedimentos e o
 * comando 'retorne'.  Esta gramática é lida pelo ANTLR4 para gerar
 * LALexer, LAParser, LABaseVisitor e LAListener em Python 3.
 *
 * Regras léxicas importantes:
 *   IDENT               – identificadores (letras, dígitos, sublinhado)
 *   NUM_INT / NUM_REAL  – literais numéricos
 *   CADEIA              – cadeia de caracteres entre aspas duplas
 *   COMENTARIO          – bloco entre { } descartado (skip)
 *   COMENTARIO_NAO_FECHADO / CADEIA_NAO_FECHADA / ERRO – erros léxicos
 *
 * Regras sintáticas importantes:
 *   programa            – ponto de entrada: declarações globais + corpo
 *   declaracao_global   – procedimento ou função (com parâmetros tipados)
 *   declaracao_local    – declare / constante / tipo (incluindo registro)
 *   tipo_estendido      – suporta ponteiro ('^') para tipo_basico_ident
 *   cmdRetorne          – 'retorne' expressao (válido só em funções – T4)
 *   cmdAtribuicao       – '^'? identificador '<-' expressao
 *   parcela_nao_unario  – '&' identificador (endereço de variável)
 */
grammar LA;

programa
    : declaracoes 'algoritmo' corpo 'fim_algoritmo'
    ;

declaracoes
    : (decl_local_global)*
    ;

decl_local_global
    : declaracao_local
    | declaracao_global
    ;

/* Declarações locais: variáveis, constantes e aliases de tipo */
declaracao_local
    : 'declare' variavel
    | 'constante' IDENT ':' tipo_basico '=' valor_constante
    | 'tipo' IDENT ':' tipo
    ;

variavel
    : identificador (',' identificador)* ':' tipo
    ;

/* Identificador pode ser qualificado (registro.campo) e indexado (vetor[i]) */
identificador
    : IDENT ('.' IDENT)* dimensao
    ;

dimensao
    : ('[' exp_aritmetica ']')*
    ;

tipo
    : registro
    | tipo_estendido
    ;

tipo_basico
    : 'literal'
    | 'inteiro'
    | 'real'
    | 'logico'
    ;

tipo_basico_ident
    : tipo_basico
    | IDENT
    ;

/* Tipo estendido: '^' indica ponteiro */
tipo_estendido
    : '^'? tipo_basico_ident
    ;

valor_constante
    : CADEIA
    | NUM_INT
    | NUM_REAL
    | 'verdadeiro'
    | 'falso'
    ;

registro
    : 'registro' variavel+ 'fim_registro'
    ;

/* Declarações globais: procedimento (sem retorno) ou função (com tipo de retorno) */
declaracao_global
    : 'procedimento' IDENT '(' parametros? ')' declaracao_local* cmd* 'fim_procedimento'
    | 'funcao' IDENT '(' parametros? ')' ':' tipo_estendido declaracao_local* cmd* 'fim_funcao'
    ;

/* Parâmetro pode ser passado por referência ('var') */
parametro
    : 'var'? identificador (',' identificador)* ':' tipo_estendido
    ;

parametros
    : parametro (',' parametro)*
    ;

corpo
    : declaracao_local* cmd*
    ;

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

cmdLeia
    : 'leia' '(' '^'? identificador (',' '^'? identificador)* ')'
    ;

cmdEscreva
    : 'escreva' '(' expressao (',' expressao)* ')'
    ;

cmdSe
    : 'se' expressao 'entao' cmd* ('senao' cmd*)? 'fim_se'
    ;

cmdCaso
    : 'caso' exp_aritmetica 'seja' selecao ('senao' cmd*)? 'fim_caso'
    ;

cmdPara
    : 'para' IDENT '<-' exp_aritmetica 'ate' exp_aritmetica 'faca' cmd* 'fim_para'
    ;

cmdEnquanto
    : 'enquanto' expressao 'faca' cmd* 'fim_enquanto'
    ;

cmdFaca
    : 'faca' cmd* 'ate' expressao
    ;

/* Atribuição: '^' antes do identificador significa desreferência de ponteiro */
cmdAtribuicao
    : '^'? identificador '<-' expressao
    ;

/* Chamada de procedimento/função como comando (mínimo um argumento) */
cmdChamada
    : IDENT '(' expressao (',' expressao)* ')'
    ;

/* 'retorne' só é semânticamente válido dentro de funções (verificado no T4) */
cmdRetorne
    : 'retorne' expressao
    ;

selecao
    : item_selecao*
    ;

item_selecao
    : constantes ':' cmd*
    ;

constantes
    : numero_intervalo (',' numero_intervalo)*
    ;

numero_intervalo
    : op_unario? NUM_INT ('..' op_unario? NUM_INT)?
    ;

op_unario
    : '-'
    ;

expressao
    : termo_logico (op_logico_1 termo_logico)*
    ;

termo_logico
    : fator_logico (op_logico_2 fator_logico)*
    ;

fator_logico
    : 'nao'? parcela_logica
    ;

parcela_logica
    : ('verdadeiro' | 'falso')
    | exp_relacional
    ;

exp_relacional
    : exp_aritmetica (op_relacional exp_aritmetica)?
    ;

op_relacional
    : '='
    | '<>'
    | '>='
    | '<='
    | '>'
    | '<'
    ;

exp_aritmetica
    : termo (op1 termo)*
    ;

termo
    : fator (op2 fator)*
    ;

fator
    : parcela (op3 parcela)*
    ;

op1 : '+' | '-' ;
op2 : '*' | '/' ;
op3 : '%' ;

parcela
    : op_unario? parcela_unario
    | parcela_nao_unario
    ;

parcela_unario
    : IDENT '(' expressao (',' expressao)* ')'
    | '^'? identificador
    | NUM_INT
    | NUM_REAL
    | '(' expressao ')'
    ;

/* '&' identificador produz o endereço da variável (tipo ponteiro) */
parcela_nao_unario
    : '&' identificador
    | CADEIA
    ;

op_logico_1 : 'ou' ;
op_logico_2 : 'e' ;

NUM_INT
    : ('0'..'9')+
    ;

NUM_REAL
    : ('0'..'9')+ '.' ('0'..'9')+
    ;

CADEIA
    : '"' ~["\r\n]* '"'
    ;

IDENT
    : [a-zA-Z_][a-zA-Z0-9_]*
    ;

COMENTARIO
    : '{' ~[}]* '}' -> skip
    ;

WS
    : [ \t\r\n]+ -> skip
    ;

/* Tokens de erro léxico: capturados em main.py antes de iniciar o parser */
COMENTARIO_NAO_FECHADO
    : '{' ~[}]*
    ;

CADEIA_NAO_FECHADA
    : '"' ~["\r\n]*
    ;

ERRO
    : .
    ;
