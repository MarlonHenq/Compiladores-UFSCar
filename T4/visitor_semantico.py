"""
Visitor semântico da linguagem LA (T4).

Percorre a AST gerada pelo ANTLR4 e acumula erros semânticos sem interromper
a análise.  Ao final, os erros são ordenados por linha/coluna e formatados
conforme o padrão dos casos de teste CT4.

Verificações implementadas (T3 + T4):
  1. Identificador já declarado anteriormente (incluindo colisão com escopos
     externos – T4: 'declare x: inteiro' dentro do algoritmo quando 'x' é um
     procedimento ou constante global).
  2. Identificador não declarado (variável, tipo, campo de registro, etc.).
     Mensagem usa o caminho completo: 'vinho.Preco', 'vinhocaro.tipoVinho' (T4).
  3. Incompatibilidade de parâmetros numa chamada de procedimento/função:
     quantidade e tipos exatos (sem promoção inteiro→real) – T4.
  4. Atribuição incompatível com o tipo declarado (ponteiros, registros,
     tipos básicos).  LHS inclui '^' e qualificador: '^ponteiro', 'ponto1.x',
     'valor[0]' (T4).
  5. Comando 'retorne' fora de função – T4.
  6. Tipo não declarado (herança do T3).
"""
from __future__ import annotations

from antlr4.Token import Token
from antlr4.tree.Tree import TerminalNodeImpl

from LAParser import LAParser
from LAVisitor import LAVisitor
from tabela_simbolos import Simbolo, SorteSimbolo, TabelaSimbolos
from tipos import (
    INDEFINIDO,
    INTEIRO,
    LITERAL,
    LOGICO,
    REAL,
    Tipo,
    SorteTipo,
    argumento_compativel_com_parametro,
    atrib_compativel,
    e_literal_basico,
    mesmo_tipo,
    numerico,
    resultado_aritmetica_op1,
    resultado_modulo,
    resultado_termo,
)


class VisitorSemantico(LAVisitor):
    """
    Visitor principal: percorre a AST e acumula erros semânticos.

    Estado interno:
      tb          – tabela de símbolos (pilha de escopos)
      erros       – lista de (linha, coluna, mensagem) ainda não formatada
      _em_funcao  – True quando estamos dentro do corpo de uma 'funcao';
                    controla a validade do comando 'retorne' (T4)
    """

    def __init__(self, ts: TabelaSimbolos) -> None:
        super().__init__()
        self.tb = ts
        self.erros: list[tuple[int, int, str]] = []
        # Flag de escopo: 'retorne' só é válido dentro de funções
        self._em_funcao: bool = False

    def _erro(self, tok: Token | None, msg: str) -> None:
        """Registra um erro semântico com linha e coluna para ordenação posterior."""
        if tok is None:
            return
        self.erros.append((tok.line, tok.column, msg))

    def formatar_erros(self) -> str:
        """
        Ordena todos os erros por (linha, coluna, mensagem) e devolve a string
        completa do arquivo de saída, encerrando com 'Fim da compilacao'.
        """
        ordenado = sorted(self.erros, key=lambda x: (x[0], x[1], x[2]))
        linhas = [f"Linha {ln}: {msg}" for ln, _c, msg in ordenado]
        linhas.append("Fim da compilacao")
        return "".join(x + "\n" for x in linhas)

    # ─────────────────────────── programa / corpo ─────────────────────────────

    def visitPrograma(self, ctx: LAParser.ProgramaContext):
        """
        Ponto de entrada da análise semântica.
        Visita primeiro as declarações globais (funções, procedimentos, tipos,
        constantes) e depois abre um novo escopo para o corpo do algoritmo.
        """
        self.visit(ctx.declaracoes())
        self.tb.push_escopo()  # escopo do corpo do algoritmo
        try:
            self.visit(ctx.corpo())
        finally:
            self.tb.pop_escopo()

    def visitCorpo(self, ctx: LAParser.CorpoContext):
        """Visita declarações locais e comandos do bloco 'algoritmo'."""
        for d in ctx.declaracao_local():
            self.visit(d)
        for c in ctx.cmd():
            self.visit(c)

    # ─────────────────────────── declarações ──────────────────────────────────

    def visitDeclaracao_local(self, ctx: LAParser.Declaracao_localContext):
        """
        Processa 'declare', 'constante' e 'tipo'.

        T4: usa buscar_encadeado (toda a cadeia de escopos visíveis) para
        detectar redeclarações mesmo quando o símbolo original está em um
        escopo externo.  Isso cobre colisões como uma variável no corpo do
        algoritmo cujo nome é o mesmo de um procedimento ou constante global.
        """
        kw = ctx.getChild(0).getText()
        if kw == "declare":
            self._registra_variaveis(ctx.variavel())
        elif kw == "constante":
            nome_tok = ctx.IDENT().symbol
            if self.tb.buscar_encadeado(nome_tok.text) is not None:
                self._erro(nome_tok, f"identificador {nome_tok.text} ja declarado anteriormente")
                return
            tp = self._tipo_de_basico_ctx(ctx.tipo_basico())
            self.tb.inserir(Simbolo(nome_tok.text, SorteSimbolo.CONSTANTE, tp))
        elif kw == "tipo":
            nome_tok = ctx.IDENT().symbol
            if self.tb.buscar_encadeado(nome_tok.text) is not None:
                self._erro(nome_tok, f"identificador {nome_tok.text} ja declarado anteriormente")
                return
            # Passa o alias para que registros nomeados usem o nome do tipo como rótulo
            tp = self._construir_tipo(ctx.tipo(), nome_alias=nome_tok.text)
            self.tb.inserir(Simbolo(nome_tok.text, SorteSimbolo.TIPO_LA, tp))

    def visitDeclaracao_global(self, ctx: LAParser.Declaracao_globalContext):
        """
        Registra procedimento ou função no escopo global e visita o corpo
        em um novo escopo interno.

        T4: ao entrar em uma 'funcao' ativa _em_funcao=True; em 'procedimento'
        mantém False.  O flag é restaurado ao sair do escopo.
        """
        kw = ctx.getChild(0).getText()
        proc = kw == "procedimento"
        nome_tok = ctx.IDENT().symbol
        nome_f = nome_tok.text

        # Coleta tipos e tokens dos parâmetros formais
        tipos_par: list[Tipo] = []
        nom_par: list[tuple[str, Token]] = []
        pctx = ctx.parametros()
        if pctx is not None:
            for pm in pctx.parametro():
                # 'var' não altera o tipo semântico; apenas indica passagem por referência
                t_par = self._tipo_de_estendido_ctx(pm.tipo_estendido())
                for idc in pm.identificador():
                    tok0 = idc.IDENT(0).symbol
                    tipos_par.append(t_par)
                    nom_par.append((tok0.text, tok0))

        # Tipo de retorno (apenas para funções)
        tipo_ret: Tipo = INDEFINIDO
        if not proc:
            tipo_ret = self._tipo_de_estendido_ctx(ctx.tipo_estendido())

        # Registra o símbolo no escopo corrente (global durante declarações)
        if self.tb.buscar_encadeado(nome_f) is not None:
            self._erro(nome_tok, f"identificador {nome_f} ja declarado anteriormente")
        else:
            sk = SorteSimbolo.PROCEDURE if proc else SorteSimbolo.FUNCAO
            self.tb.inserir(
                Simbolo(
                    nome_f,
                    sk,
                    tipo_ret if not proc else INDEFINIDO,
                    parametros_tipos=tuple(tipos_par),
                )
            )

        # Novo escopo para parâmetros e corpo da sub-rotina
        em_funcao_antes = self._em_funcao
        # Apenas funções permitem 'retorne'; procedimentos não
        self._em_funcao = not proc
        self.tb.push_escopo()
        try:
            # Insere parâmetros no escopo interno; verifica redeclarações
            for i, (pn, tk) in enumerate(nom_par):
                if self.tb.buscar_encadeado(pn) is not None:
                    self._erro(tk, f"identificador {pn} ja declarado anteriormente")
                else:
                    self.tb.inserir(Simbolo(pn, SorteSimbolo.VARIAVEL, tipos_par[i]))

            for d in ctx.declaracao_local():
                self.visit(d)
            for cd in ctx.cmd():
                self.visit(cd)
        finally:
            self.tb.pop_escopo()
            self._em_funcao = em_funcao_antes  # restaura o estado do escopo anterior

        return None

    def visitVariavel(self, ctx: LAParser.VariavelContext):
        self._registra_variaveis(ctx)

    def _registra_variaveis(self, ctx: LAParser.VariavelContext):
        """
        Insere variáveis na tabela de símbolos.

        T4: usa buscar_encadeado para detectar colisões com qualquer símbolo
        visível na cadeia de escopos (não apenas o escopo imediato).
        Continua após erros para acumular todos os problemas no arquivo.
        """
        tipo_rhs = self._construir_tipo(ctx.tipo())
        for idc in ctx.identificador():
            t0 = idc.IDENT(0).symbol
            if self.tb.buscar_encadeado(t0.text) is not None:
                self._erro(t0, f"identificador {t0.text} ja declarado anteriormente")
            else:
                self.tb.inserir(Simbolo(t0.text, SorteSimbolo.VARIAVEL, tipo_rhs))

    # ──────────────────────── helpers de resolução de tipos ───────────────────

    def _tipo_de_basico_ctx(self, ctx: LAParser.Tipo_basicoContext) -> Tipo:
        """Converte o token de tipo básico em Tipo singleton."""
        k = ctx.getChild(0).getText()
        return {"inteiro": INTEIRO, "real": REAL, "literal": LITERAL, "logico": LOGICO}[k]

    def _tipo_de_basico_ident_ctx(
        self, ctx: LAParser.Tipo_basico_identContext
    ) -> tuple[Tipo, Token]:
        """
        Resolve tipo_basico_ident: tipo primitivo literal ou alias definido
        com 'tipo'.  Devolve (Tipo, token_de_referência).
        """
        if ctx.tipo_basico():
            tb0 = ctx.tipo_basico()
            return self._tipo_de_basico_ctx(tb0), tb0.start
        ident = ctx.IDENT().symbol
        sb = self.tb.buscar_encadeado(ident.text)
        if sb is None or sb.sorte != SorteSimbolo.TIPO_LA:
            self._erro(ident, f"tipo {ident.text} nao declarado")
            return INDEFINIDO, ident
        return sb.tipo, ident

    def _tipo_de_estendido_ctx(self, ctx: LAParser.Tipo_estendidoContext) -> Tipo:
        """Resolve tipo_estendido: adiciona nível de ponteiro se '^' presente."""
        pont = ctx.getChild(0).getText() == "^"
        tipo_base, _tok = self._tipo_de_basico_ident_ctx(ctx.tipo_basico_ident())
        if pont and tipo_base.sorte != SorteTipo.INDEFINIDO:
            return Tipo.ponteiro(tipo_base)
        return tipo_base

    def _construir_tipo(
        self, ctx: LAParser.TipoContext, nome_alias: str | None = None
    ) -> Tipo:
        """
        Constrói o Tipo a partir da regra 'tipo' da gramática.

        Para registros nomeados (declarados via 'tipo X: registro'), o
        nome_alias X é usado como rótulo do Tipo.registro, permitindo a
        verificação de compatibilidade por nome de tipo.
        Registros anônimos (inline em 'declare') recebem tag interna '@r<id>'.
        """
        if ctx.registro():
            campos_l: list[tuple[str, Tipo]] = []
            for vc in ctx.registro().variavel():
                campo_t = self._construir_tipo(vc.tipo())
                for idc in vc.identificador():
                    campos_l.append((idc.IDENT(0).symbol.text, campo_t))
            # Usa alias explícito para registro nomeado; tag anônima caso contrário
            tag = nome_alias if nome_alias else ("@r" + hex(id(ctx.registro()))[2:])
            return Tipo.registro(tag, tuple(campos_l))
        return self._tipo_de_estendido_ctx(ctx.tipo_estendido())

    # ─────────────────────────────── comandos ─────────────────────────────────

    def visitCmd(self, ctx: LAParser.CmdContext):
        if ctx.cmdLeia():
            self.visit(ctx.cmdLeia())
        elif ctx.cmdEscreva():
            self.visit(ctx.cmdEscreva())
        elif ctx.cmdSe():
            self.visit(ctx.cmdSe())
        elif ctx.cmdCaso():
            self.visit(ctx.cmdCaso())
        elif ctx.cmdPara():
            self.visit(ctx.cmdPara())
        elif ctx.cmdEnquanto():
            self.visit(ctx.cmdEnquanto())
        elif ctx.cmdFaca():
            self.visit(ctx.cmdFaca())
        elif ctx.cmdChamada():
            self.visit(ctx.cmdChamada())
        elif ctx.cmdAtribuicao():
            self.visit(ctx.cmdAtribuicao())
        elif ctx.cmdRetorne():
            self.visit(ctx.cmdRetorne())

    def visitCmdLeia(self, ctx: LAParser.CmdLeiaContext):
        """Verifica identificadores usados em 'leia', incluindo desreferência '^'."""
        ptr = False
        for child in ctx.getChildren():
            if isinstance(child, TerminalNodeImpl) and child.getText() == "^":
                ptr = True
            elif isinstance(child, LAParser.IdentificadorContext):
                self._tipo_de_ident_uso(child, permite_deref_ponteiro=ptr)
                ptr = False

    def visitCmdEscreva(self, ctx: LAParser.CmdEscrevaContext):
        for ex in ctx.expressao():
            self._tipo_expressao(ex)

    def visitCmdSe(self, ctx: LAParser.CmdSeContext):
        self._tipo_expressao(ctx.expressao())
        for c in ctx.cmd():
            self.visit(c)

    def visitCmdEnquanto(self, ctx: LAParser.CmdEnquantoContext):
        self._tipo_expressao(ctx.expressao())
        for c in ctx.cmd():
            self.visit(c)

    def visitCmdFaca(self, ctx: LAParser.CmdFacaContext):
        for c in ctx.cmd():
            self.visit(c)
        self._tipo_expressao(ctx.expressao())

    def visitCmdPara(self, ctx: LAParser.CmdParaContext):
        itk = ctx.IDENT().symbol
        self._verifica_simbolo_leitura(itk.text, itk)
        self._tipo_exp_arit(ctx.exp_aritmetica(0))
        self._tipo_exp_arit(ctx.exp_aritmetica(1))
        for c in ctx.cmd():
            self.visit(c)

    def visitCmdCaso(self, ctx: LAParser.CmdCasoContext):
        self._tipo_exp_arit(ctx.exp_aritmetica())
        self.visit(ctx.selecao())
        after_senao = False
        for ch in ctx.getChildren():
            if isinstance(ch, TerminalNodeImpl) and ch.getText() == "senao":
                after_senao = True
            elif after_senao and isinstance(ch, LAParser.CmdContext):
                self.visit(ch)

    def visitSelecao(self, ctx: LAParser.SelecaoContext):
        for item in ctx.item_selecao():
            self.visit(item)

    def visitItem_selecao(self, ctx: LAParser.Item_selecaoContext):
        for c in ctx.cmd():
            self.visit(c)

    def visitCmdChamada(self, ctx: LAParser.CmdChamadaContext):
        """Chamada de procedimento como comando; valida parâmetros (T4)."""
        self._tipo_chamada(ctx.IDENT().symbol, ctx.expressao())

    def visitCmdAtribuicao(self, ctx: LAParser.CmdAtribuicaoContext):
        """
        Verifica compatibilidade de tipos numa atribuição.

        T4: a mensagem de erro usa o texto completo do LHS, incluindo o '^'
        de desreferência, qualificadores e índices de vetor, por exemplo:
          '^ponteiro'  →  atribuicao nao compativel para ^ponteiro
          'ponto1.x'   →  atribuicao nao compativel para ponto1.x
          'valor[0]'   →  atribuicao nao compativel para valor[0]
        """
        circunf = ctx.getChild(0).getText() == "^"
        idctx = ctx.identificador()
        # Texto completo do LHS para a mensagem de erro (T4)
        lhs_text = ("^" if circunf else "") + idctx.getText()
        primeiro_nome = idctx.IDENT(0).symbol.text

        existe_lado = self._simbolo_valor_primeiro(primeiro_nome)
        lhs_t = self._tipo_de_ident_uso(idctx, permite_deref_ponteiro=circunf)

        # Se houver '^' e o tipo ainda for ponteiro (não desreferenciado internamente)
        if circunf and lhs_t.sorte == SorteTipo.PONTEIRO and lhs_t.interno:
            lhs_t = lhs_t.interno

        rhs_t = self._tipo_expressao(ctx.expressao())

        pode_checar_atrib = existe_lado is not None and existe_lado.sorte not in (
            SorteSimbolo.PROCEDURE,
            SorteSimbolo.FUNCAO,
            SorteSimbolo.TIPO_LA,
        )
        if pode_checar_atrib and not atrib_compativel(lhs_t, rhs_t):
            t0 = idctx.IDENT(0).symbol
            self._erro(t0, f"atribuicao nao compativel para {lhs_text}")

    def visitCmdRetorne(self, ctx: LAParser.CmdRetorneContext):
        """
        Verifica uso do comando 'retorne' (T4).
        Válido apenas dentro do corpo de uma 'funcao'; proibido em
        procedimentos e no bloco principal do algoritmo.
        """
        self._tipo_expressao(ctx.expressao())
        if not self._em_funcao:
            # ctx.start é o token 'retorne'; sua linha é usada na mensagem
            self._erro(ctx.start, "comando retorne nao permitido nesse escopo")

    # ──────────────────── chamada de função/procedimento ──────────────────────

    def _tipo_chamada(
        self, id_tok: Token, exprs: list[LAParser.ExpressaoContext]
    ) -> Tipo:
        """
        Verifica e resolve uma chamada de função ou procedimento (T4).

        Etapas:
          1. Confirma que o identificador existe e é função/procedimento.
          2. Avalia todos os argumentos (permite detectar erros dentro deles).
          3. Verifica quantidade e tipos dos argumentos vs parâmetros formais.
             Usa argumento_compativel_com_parametro (sem promoção inteiro→real).
          4. Emite UMA mensagem de incompatibilidade por chamada, se necessário.
        """
        nome = id_tok.text
        sb = self.tb.buscar_encadeado(nome)
        if sb is None or sb.sorte not in (SorteSimbolo.FUNCAO, SorteSimbolo.PROCEDURE):
            self._erro(id_tok, f"identificador {nome} nao declarado")
            # Avalia expressões mesmo assim para capturar erros internos
            for ea in exprs:
                self._tipo_expressao(ea)
            return INDEFINIDO

        # Avalia todos os argumentos antes de checar compatibilidade
        tipos_reais = [self._tipo_expressao(ea) for ea in exprs]

        # Valida quantidade e tipos dos argumentos contra os parâmetros formais (T4)
        if sb.parametros_tipos is not None:
            incompativel = len(tipos_reais) != len(sb.parametros_tipos)
            if not incompativel:
                for formal, actual in zip(sb.parametros_tipos, tipos_reais):
                    if not argumento_compativel_com_parametro(formal, actual):
                        incompativel = True
                        break
            if incompativel:
                self._erro(
                    id_tok,
                    f"incompatibilidade de parametros na chamada de {nome}",
                )

        return sb.tipo if sb.sorte == SorteSimbolo.FUNCAO else INDEFINIDO

    # ──────────────────────────── expressões ──────────────────────────────────

    def _tipo_expressao(self, ctx: LAParser.ExpressaoContext) -> Tipo:
        tl = ctx.termo_logico()
        acc = self._tipo_termo_logico(tl[0])
        for i in range(1, len(tl)):
            b = self._tipo_termo_logico(tl[i])
            acc = LOGICO if (mesmo_tipo(acc, LOGICO) and mesmo_tipo(b, LOGICO)) else INDEFINIDO
        return acc

    def _tipo_termo_logico(self, ctx: LAParser.Termo_logicoContext) -> Tipo:
        fl = ctx.fator_logico()
        acc = self._tipo_fator_logico(fl[0])
        for i in range(1, len(fl)):
            b = self._tipo_fator_logico(fl[i])
            acc = LOGICO if (mesmo_tipo(acc, LOGICO) and mesmo_tipo(b, LOGICO)) else INDEFINIDO
        return acc

    def _tipo_fator_logico(self, ctx: LAParser.Fator_logicoContext) -> Tipo:
        neg = ctx.getChild(0).getText() == "nao"
        tl = ctx.parcela_logica()
        if tl.getChild(0).getText() in ("verdadeiro", "falso"):
            tp = LOGICO
        else:
            tp = self._tipo_exp_rel(tl.exp_relacional())
        if neg:
            return tp if mesmo_tipo(tp, LOGICO) else INDEFINIDO
        return tp

    def _tipo_exp_rel(self, ctx: LAParser.Exp_relacionalContext) -> Tipo:
        ears = ctx.exp_aritmetica()
        left = self._tipo_exp_arit(ears[0])
        if ctx.op_relacional() is None:
            return left
        right = self._tipo_exp_arit(ears[1])
        if numerico(left) and numerico(right):
            return LOGICO
        if e_literal_basico(left) and e_literal_basico(right):
            if ctx.op_relacional().getChild(0).getText() == "=":
                return LOGICO
        return INDEFINIDO

    def _tipo_exp_arit(self, ctx: LAParser.Exp_aritmeticaContext) -> Tipo:
        ts = ctx.termo()
        acc = self._tipo_termo(ts[0])
        j = 0
        for i in range(1, len(ts)):
            op_t = ctx.op1(j).getChild(0).getText()
            j += 1
            b = self._tipo_termo(ts[i])
            acc = resultado_aritmetica_op1(op_t, acc, b)
        return acc

    def _tipo_termo(self, ctx: LAParser.TermoContext) -> Tipo:
        fs = ctx.fator()
        acc = self._tipo_fator(fs[0])
        j = 0
        for i in range(1, len(fs)):
            op_t = ctx.op2(j).getChild(0).getText()
            j += 1
            b = self._tipo_fator(fs[i])
            acc = resultado_termo(op_t, acc, b)
        return acc

    def _tipo_fator(self, ctx: LAParser.FatorContext) -> Tipo:
        ps = ctx.parcela()
        acc = self._tipo_parcela(ps[0])
        for i in range(1, len(ps)):
            b = self._tipo_parcela(ps[i])
            acc = resultado_modulo(acc, b)
        return acc

    def _tipo_parcela(self, ctx: LAParser.ParcelaContext) -> Tipo:
        if ctx.parcela_nao_unario() is not None:
            pn = ctx.parcela_nao_unario()
            if pn.CADEIA() is not None:
                return LITERAL
            # '&' identificador → endereço; resulta em tipo ponteiro para o tipo do ident
            t_var = self._tipo_de_ident_uso(pn.identificador(), permite_deref_ponteiro=False)
            return Tipo.ponteiro(t_var)

        pun = ctx.parcela_unario()
        neg = ctx.op_unario()
        tipo_u = self._tipo_parcela_unario(pun)
        if neg:
            return tipo_u if numerico(tipo_u) else INDEFINIDO
        return tipo_u

    def _tipo_parcela_unario(self, pu: LAParser.Parcela_unarioContext) -> Tipo:
        if pu.NUM_INT() is not None:
            return INTEIRO
        if pu.NUM_REAL() is not None:
            return REAL
        exprs_list = pu.expressao()
        primeiro = pu.getChild(0)
        txt0 = primeiro.getText()

        if txt0 == "(" and exprs_list:
            return self._tipo_expressao(exprs_list[0])

        # Chamada de função em expressão: IDENT '(' expressao ... ')' (T4: valida parâmetros)
        if pu.IDENT() is not None and len(pu.children) > 1 and pu.getChild(1).getText() == "(":
            tt = pu.IDENT().symbol
            return self._tipo_chamada(tt, exprs_list)

        # Identificador com possível desreferência de ponteiro ('^' antes do ident)
        usar_ptr = txt0 == "^"
        idc = pu.identificador()
        assert idc is not None
        return self._tipo_de_ident_uso(idc, permite_deref_ponteiro=usar_ptr)

    # ─────────────────────── helpers de identificadores ───────────────────────

    def _simbolo_valor_primeiro(self, nome: str) -> Simbolo | None:
        """
        Retorna o símbolo correspondente ao nome se for utilizável como LHS
        de atribuição (variável, constante, procedure ou função).
        Retorna None para aliases de tipo (TIPO_LA) ou identificadores inexistentes.
        """
        sb = self.tb.buscar_encadeado(nome)
        if sb is None:
            return None
        return sb if sb.sorte != SorteSimbolo.TIPO_LA else None

    def _verifica_simbolo_leitura(self, nome: str, tok: Token) -> Simbolo | None:
        """
        Verifica se 'nome' pode ser lido (variável ou constante).
        Emite erro se não declarado, for alias de tipo ou for sub-rotina.
        Usada em visitCmdPara (variável de controle do loop).
        """
        sb = self.tb.buscar_encadeado(nome)
        if sb is None:
            self._erro(tok, f"identificador {nome} nao declarado")
            return None
        if sb.sorte == SorteSimbolo.TIPO_LA:
            self._erro(tok, f"identificador {nome} nao declarado")
            return None
        if sb.sorte in (SorteSimbolo.PROCEDURE, SorteSimbolo.FUNCAO):
            self._erro(tok, f"identificador {nome} nao declarado")
            return None
        return sb

    def _tipo_de_ident_uso(
        self,
        idctx: LAParser.IdentificadorContext,
        *,
        permite_deref_ponteiro: bool,
    ) -> Tipo:
        """
        Resolve o tipo de um identificador (simples, qualificado ou indexado).

        T4: erros de 'não declarado' usam o texto COMPLETO do identificador:
          'vinho.Preco'         → campo Preco não existe no registro
          'vinhocaro.tipoVinho' → base 'vinhocaro' não declarada
          'valor[0]'            → usado via texto do idctx em atribuição
        O texto completo é obtido via idctx.getText() (ANTLR concatena tokens
        sem espaços, preservando '.', '[' e ']' do fonte).
        """
        toks = idctx.IDENT()
        if not toks:
            return INDEFINIDO

        # Texto completo do identificador para mensagens de erro (T4)
        full_ident = idctx.getText()
        base_tok = toks[0].symbol

        # Resolução do símbolo base (primeiro IDENT da cadeia)
        base_sym = self.tb.buscar_encadeado(base_tok.text)
        if base_sym is None or base_sym.sorte in (
            SorteSimbolo.TIPO_LA,
            SorteSimbolo.PROCEDURE,
            SorteSimbolo.FUNCAO,
        ):
            self._erro(base_tok, f"identificador {full_ident} nao declarado")
            return INDEFINIDO

        tipo_atual = base_sym.tipo

        # Desreferência de ponteiro ('^' em cmdLeia ou em parcela_unario)
        if permite_deref_ponteiro:
            if tipo_atual.sorte == SorteTipo.PONTEIRO and tipo_atual.interno:
                tipo_atual = tipo_atual.interno

        # Navegação por sub-campos: 'vinho.preco', 'registro.campo.subcampo'
        partes = [t.symbol.text for t in toks]
        k = 1
        while k < len(partes):
            campo = partes[k]
            tok_c = toks[k].symbol
            if tipo_atual.sorte == SorteTipo.REGISTRO and tipo_atual.campos is not None:
                cmap = {n: tp for n, tp in tipo_atual.campos}
                if campo not in cmap:
                    self._erro(tok_c, f"identificador {full_ident} nao declarado")
                    return INDEFINIDO
                tipo_atual = cmap[campo]
            else:
                self._erro(tok_c, f"identificador {full_ident} nao declarado")
                return INDEFINIDO
            k += 1

        # Avalia expressões de índice (e.g. vetor[i]) para verificar tipos internos
        dc = idctx.dimensao()
        if dc is not None:
            for exp_dim in dc.exp_aritmetica():
                self._tipo_exp_arit(exp_dim)

        return tipo_atual
