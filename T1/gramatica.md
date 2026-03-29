### Informações do Documento

* [cite_start]**Instituição**: UFSCar Departamento de Computação [cite: 1]
* [cite_start]**Disciplina**: Construção de Compiladores [cite: 1]
* [cite_start]**Título**: Gramática da linguagem LA [cite: 2]
* **Autor da linguagem LA**: prof. [cite_start]Jander Moreira [cite: 3]
* **Autores da gramática**: Prof. Daniel Lucrédio e Profa. [cite_start]Helena de Medeiros Caseli [cite: 3]
* [cite_start]**Data desta versão**: 13/ago/2018 [cite: 4]

---

### Notação Adotada

| Elemento | Significado |
| :--- | :--- |
[cite_start]| texto simples | não-terminais [cite: 5] |
| [cite_start]""texto em negrito entre aspas"" | terminais literais [cite: 5] |
| [cite_start]Texto negrito iniciando em maiúscula | terminais [cite: 5] |
| [cite_start][ ] | opcionalidade [cite: 5] |
| [cite_start]{ } | repetição 0 ou mais vezes [cite: 5] |
| [cite_start]| simbolo de definição de regra de produção [cite: 5] |
| [cite_start]| alternância [cite: 5] |
| [cite_start]| agrupamento [cite: 5] |

---

### Observações

* [cite_start]**Obs1**: O manual da linguagem LA descreve as regras de formação de identificadores (IDENT), na página 11, e expressões literais (CADEIA), na página 16. [cite: 6]
* [cite_start]**Obs2**: `NUM_INT` e `NUM_REAL` representam, respectivamente, números inteiros e números reais, que utilizam ponto como separador decimal. [cite: 7] [cite_start]Na definição léxida de `NUM_INT` e `NUM_REAL` não é necessário incluir o sinal, pois o mesmo está previsto nas regras sintáticas. [cite: 8]

---

### Regras da Gramática

* [cite_start]**programa**: declaracoes "algoritmo" corpo "fim_algoritmo" [cite: 9]
* [cite_start]**declaracoes**: {decl_local_global} [cite: 9]
* [cite_start]**decl_local_global** [cite: 10]
* [cite_start]**declaracao_local** [cite: 11]
* **variavel** [cite: 12]
* [cite_start]**declaracao_local** [cite: 13]
* **"declare"** variavel [cite: 14]
* [cite_start]**declaracao_global** [cite: 15]
* | "constante" IDENT":" tipo_basico "=" valor_constante [cite: 16]
* [cite_start]"tipo" IDENT":" tipo [cite: 17]
* [cite_start]**identificador**: {"," identificador} ":" tipo [cite: 18]
* **identificador**: IDENT {"." IDENT} dimensao [cite: 19]
* [cite_start]**dimensao**: {"[" exp_aritmetica "]"} [cite: 20]
* **tipo**: registro tipo_estendido [cite: 21]
* **tipo_basico**: "literal" | "inteiro" | "real" | [cite_start]"logico" [cite: 22]
* **tipo_basico_ident**: tipo_basico | IDENT [cite: 23]
* [cite_start]**tipo_estendido**: - ["^"] tipo_basico_ident [cite: 24]
* **valor_constante**: CADEIA | NUM_INT | NUM_REAL | "verdadeiro" | [cite_start]"falso" [cite: 25]
* [cite_start]**registro**: "registro" (variavel) "fim_registro" [cite: 25]
* [cite_start]**declaracao_global** [cite: 26]
* [cite_start]"procedimento" IDENT "(" [parametros ")" (declaracao_local} {cmd} "fim_procedimento" [cite: 27]
* [cite_start]"funcao" IDENT "(" [parametros] ")" ":" tipo_estendido (declaracao_local} cmd "fim_funcao" [cite: 28]
* [cite_start]**parametro**: ["var"] identificador ("," identificador} ":" tipo_estendido [cite: 29]
* [cite_start]**parametros** [cite: 29]
* **corpo** [cite: 30]
* [cite_start]parametro {"," parametro} [cite: 31]
* [cite_start]{declaracao_local} {cmd} [cite: 32]
* [cite_start]**cmd**: cmdLeia | cmdEscreva | cmdSe cmdCaso | cmdPara | cmdEnquanto [cite: 33]
* | cmdFaca | cmdAtribuicao | cmdChamada | cmdRetorne [cite: 34]
* [cite_start]**cmdLeia** [cite: 34]
* [cite_start]"leia" "(" ["^"] identificador {"," ["^"] identificador} ")" [cite: 35]
* **cmdEscreva**: "escreva" "(" expressao {"," expressao} ")" [cite: 36]
* [cite_start]**cmdSe** [cite: 36]
* [cite_start]"se" expressao "entao" cmd) ["senao" cmd}] "fim_se" [cite: 37]
* [cite_start]**cmdCaso** [cite: 38]
* **cmdPara** [cite: 39]
* [cite_start]"caso" exp_aritmetica "seja" selecao ["senao" (cmd)] "fim_caso" [cite: 40]
* [cite_start]"para" IDENT "<-" exp_aritmetica "ate" exp_aritmetica "faca" (cmd) "fim_para" [cite: 41]
* [cite_start]**cmdEnquanto**: "enquanto" expressao "faca" cmd "fim_enquanto" [cite: 42]
* [cite_start]**cmdFaca**: "faca" (cmd) "ate" expressao [cite: 43]
* **cmdAtribuicao** [cite: 44]
* [cite_start]**cmdChamada** [cite: 45]
* [cite_start]["A"] identificador "<-" expressao [cite: 46]
* [cite_start]IDENT "(" expressao {"," expressao) ")" [cite: 47]
* **cmdRetorne**: "retorne" expressao [cite: 48]
* [cite_start]**selecao**: {item_selecao} [cite: 49]
* **item_selecao**: constantes ":" {cmd} [cite: 50]
* **constantes**: numero_intervalo {"," numero_intervalo [cite: 51]
* [cite_start]**numero_intervalo**: [op_unario] NUM_INT [".." [op_unario] NUM_INT] [cite: 52]
* **op_unario** [cite: 53]
* **exp_aritmetica**: termo (op1 termo} [cite: 54]
* **termo** [cite: 55]
* [cite_start]fator op2 fator} [cite: 56]
* [cite_start]**fator**: parcela (op3 parcela) [cite: 57]
* **op1** [cite: 58]
* [cite_start]"+""" [cite: 59]
* [cite_start]**op2** [cite: 60]
* "*" | [cite_start]"/" [cite: 61]
* [cite_start]**op3** [cite: 62]
* "%" [cite: 63]
* [cite_start]**parcela**: [op_unario] parcela_unario | parcela_nao_unario [cite: 64]
* [cite_start]**parcela_unario** [cite: 65]
* [cite_start][" "] identificador [cite: 66]
* | [cite: 67]
* [cite_start]IDENT "(" expressao {"," expressao}")" [cite: 68]
* [cite_start]NUM_INT [cite: 69]
* | [cite_start]NUM_REAL [cite: 70]
* | [cite_start]"(" expressao ")" [cite: 71]
* **parcela_nao_unario**: "&" identificador | CADEIΑ [cite: 72]
* [cite_start]**exp_relacional** [cite: 73]
* **op_relacional** [cite: 74]
* exp_aritmetica [op_relacional exp_aritmetica] [cite: 75]
* "=" | "<>" | ">=" | "<=" | ">" | [cite_start]"<" [cite: 76]
* [cite_start]**termo_logico** [cite: 77]
* [cite_start]**expressao**: termo_logico {op_logico_1 termo_logico} [cite: 78]
* [cite_start]**fator_logico**: {op_logico_2 fator_logico) [cite: 79]
* **fator_logico** [cite: 80]
* [cite_start]["nao"] parcela_logica [cite: 81]
* [cite_start]**parcela_logica** [cite: 82]
* ("verdadeiro" | "falso") [cite_start][cite: 83]
* [cite_start]| exp_relacional [cite: 84]
* **op_logico_1** [cite: 85]
* [cite_start]"ou" [cite: 86]
* [cite_start]**op_logico_2**: "e" [cite: 87]