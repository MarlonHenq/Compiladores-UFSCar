"""Visitor LAParser: escopos, inferência parcial e erros semânticos (T3)."""
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
    atrib_compativel,
    e_literal_basico,
    mesmo_tipo,
    numerico,
    resultado_aritmetica_op1,
    resultado_modulo,
    resultado_termo,
)


class VisitorSemantico(LAVisitor):
    def __init__(self, ts: TabelaSimbolos) -> None:
        super().__init__()
        self.tb = ts
        self.erros: list[tuple[int, int, str]] = []

    def _erro(self, tok: Token | None, msg: str) -> None:
        if tok is None:
            return
        self.erros.append((tok.line, tok.column, msg))

    def formatar_erros(self) -> str:
        ordenado = sorted(self.erros, key=lambda x: (x[0], x[1], x[2]))
        linhas = [f"Linha {ln}: {msg}" for ln, _c, msg in ordenado]
        linhas.append("Fim da compilacao")
        return "".join(x + "\n" for x in linhas)

    # --- programa / corpo ---
    def visitPrograma(self, ctx: LAParser.ProgramaContext):
        self.visit(ctx.declaracoes())
        self.tb.push_escopo()
        try:
            self.visit(ctx.corpo())
        finally:
            self.tb.pop_escopo()

    def visitCorpo(self, ctx: LAParser.CorpoContext):
        for d in ctx.declaracao_local():
            self.visit(d)
        for c in ctx.cmd():
            self.visit(c)

    # --- declarações ---
    def visitDeclaracao_local(self, ctx: LAParser.Declaracao_localContext):
        kw = ctx.getChild(0).getText()
        if kw == "declare":
            self._registra_variaveis(ctx.variavel())
        elif kw == "constante":
            nome_tok = ctx.IDENT().symbol
            if self.tb.existe_local(nome_tok.text):
                self._erro(nome_tok, f"identificador {nome_tok.text} ja declarado anteriormente")
                return
            tp = self._tipo_de_basico_ctx(ctx.tipo_basico())
            self.tb.inserir(Simbolo(nome_tok.text, SorteSimbolo.CONSTANTE, tp))
        elif kw == "tipo":
            nome_tok = ctx.IDENT().symbol
            if self.tb.existe_local(nome_tok.text):
                self._erro(nome_tok, f"identificador {nome_tok.text} ja declarado anteriormente")
                return
            self.tb.inserir(
                Simbolo(nome_tok.text, SorteSimbolo.TIPO_LA, self._construir_tipo(ctx.tipo())),
            )

    def visitDeclaracao_global(self, ctx: LAParser.Declaracao_globalContext):
        kw = ctx.getChild(0).getText()
        proc = kw == "procedimento"
        nome_tok = ctx.IDENT().symbol
        nome_f = nome_tok.text

        tipos_par: list[Tipo] = []
        nom_par: list[tuple[str, Token]] = []
        pctx = ctx.parametros()
        if pctx is not None:
            for pm in pctx.parametro():
                t_par = self._tipo_de_estendido_ctx(pm.tipo_estendido())
                for idc in pm.identificador():
                    tok0 = idc.IDENT(0).symbol
                    tipos_par.append(t_par)
                    nom_par.append((tok0.text, tok0))

        tipo_ret: Tipo = INDEFINIDO
        if not proc:
            tipo_ret = self._tipo_de_estendido_ctx(ctx.tipo_estendido())

        if self.tb.existe_local(nome_f):
            self._erro(nome_tok, f"identificador {nome_f} ja declarado anteriormente")
        else:
            sk = SorteSimbolo.PROCEDURE if proc else SorteSimbolo.FUNCAO
            self.tb.inserir(
                Simbolo(nome_f, sk, tipo_ret if not proc else INDEFINIDO, parametros_tipos=tuple(tipos_par)),
            )

        self.tb.push_escopo()
        try:
            for i, (pn, tk) in enumerate(nom_par):
                if self.tb.existe_local(pn):
                    self._erro(tk, f"identificador {pn} ja declarado anteriormente")
                else:
                    self.tb.inserir(Simbolo(pn, SorteSimbolo.VARIAVEL, tipos_par[i]))

            for d in ctx.declaracao_local():
                self.visit(d)
            for cd in ctx.cmd():
                self.visit(cd)
        finally:
            self.tb.pop_escopo()

        return None

    def visitVariavel(self, ctx: LAParser.VariavelContext):
        self._registra_variaveis(ctx)

    def _registra_variaveis(self, ctx: LAParser.VariavelContext):
        tipo_rhs = self._construir_tipo(ctx.tipo())
        for idc in ctx.identificador():
            t0 = idc.IDENT(0).symbol
            if self.tb.existe_local(t0.text):
                self._erro(t0, f"identificador {t0.text} ja declarado anteriormente")
            else:
                self.tb.inserir(Simbolo(t0.text, SorteSimbolo.VARIAVEL, tipo_rhs))

    def _tipo_de_basico_ctx(self, ctx: LAParser.Tipo_basicoContext) -> Tipo:
        k = ctx.getChild(0).getText()
        return {"inteiro": INTEIRO, "real": REAL, "literal": LITERAL, "logico": LOGICO}[k]

    def _tipo_de_basico_ident_ctx(self, ctx: LAParser.Tipo_basico_identContext) -> tuple[Tipo, Token]:
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
        pont = ctx.getChild(0).getText() == "^"
        tipo_base, tok = self._tipo_de_basico_ident_ctx(ctx.tipo_basico_ident())
        if pont and tipo_base.sorte != SorteTipo.INDEFINIDO:
            return Tipo.ponteiro(tipo_base)
        return tipo_base

    def _construir_tipo(self, ctx: LAParser.TipoContext) -> Tipo:
        if ctx.registro():
            campos_l = []
            for vc in ctx.registro().variavel():
                campo_t = self._construir_tipo(vc.tipo())
                for idc in vc.identificador():
                    campos_l.append((idc.IDENT(0).symbol.text, campo_t))
            tag = "@r" + hex(id(ctx.registro()))[2:]
            return Tipo.registro(tag, tuple(campos_l))
        return self._tipo_de_estendido_ctx(ctx.tipo_estendido())

    # --- comandos ---
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
        self._tipo_chamada(ctx.IDENT().symbol, ctx.expressao())

    def visitCmdAtribuicao(self, ctx: LAParser.CmdAtribuicaoContext):
        circunf = ctx.getChild(0).getText() == "^"
        idctx = ctx.identificador()
        primeiro_nome = idctx.IDENT(0).symbol.text
        existe_lado = self._simbolo_valor_primeiro(primeiro_nome)
        lhs_t = self._tipo_de_ident_uso(idctx, permite_deref_ponteiro=circunf)
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
            self._erro(t0, f"atribuicao nao compativel para {primeiro_nome}")

    def visitCmdRetorne(self, ctx: LAParser.CmdRetorneContext):
        self._tipo_expressao(ctx.expressao())

    def _tipo_chamada(self, id_tok: Token, exprs: list[LAParser.ExpressaoContext]) -> Tipo:
        nome = id_tok.text
        sb = self.tb.buscar_encadeado(nome)
        if sb is None:
            self._erro(id_tok, f"identificador {nome} nao declarado")
            return INDEFINIDO
        if sb.sorte not in (SorteSimbolo.FUNCAO, SorteSimbolo.PROCEDURE):
            self._erro(id_tok, f"identificador {nome} nao declarado")
            return INDEFINIDO
        for ea in exprs:
            self._tipo_expressao(ea)

        if sb.sorte == SorteSimbolo.FUNCAO:
            return sb.tipo
        return INDEFINIDO

    # --- expressões ---
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

        if pu.IDENT() is not None and len(pu.children) > 1 and pu.getChild(1).getText() == "(":
            tt = pu.IDENT().symbol
            return self._tipo_chamada(tt, exprs_list)

        usar_ptr = txt0 == "^"
        idc = pu.identificador()
        assert idc is not None
        return self._tipo_de_ident_uso(idc, permite_deref_ponteiro=usar_ptr)

    def _simbolo_valor_primeiro(self, nome: str) -> Simbolo | None:
        sb = self.tb.buscar_encadeado(nome)
        if sb is None:
            return None
        return sb if sb.sorte != SorteSimbolo.TIPO_LA else None

    def _verifica_simbolo_leitura(self, nome: str, tok: Token) -> Simbolo | None:
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
        toks = idctx.IDENT()
        if not toks:
            return INDEFINIDO
        base_sym = self._verifica_simbolo_leitura(toks[0].symbol.text, toks[0].symbol)
        if base_sym is None:
            return INDEFINIDO
        tipo_atual = base_sym.tipo

        if permite_deref_ponteiro:
            if tipo_atual.sorte == SorteTipo.PONTEIRO and tipo_atual.interno:
                tipo_atual = tipo_atual.interno
            elif tipo_atual.sorte != SorteTipo.INDEFINIDO:
                pass

        partes_txt = [t.symbol.text for t in toks]
        dc = idctx.dimensao()
        exps_dims: list[LAParser.Exp_aritmeticaContext] = []
        if dc is not None:
            exps_dims = list(dc.exp_aritmetica())

        k = 1
        idx_dim = 0
        while k < len(partes_txt):
            campo_txt = partes_txt[k]
            tok_c = toks[k].symbol
            if tipo_atual.sorte == SorteTipo.REGISTRO and tipo_atual.campos is not None:
                cmap = {name: tp for name, tp in tipo_atual.campos}
                if campo_txt not in cmap:
                    self._erro(tok_c, f"identificador {campo_txt} nao declarado")
                    return INDEFINIDO
                tipo_atual = cmap[campo_txt]
                k += 1
                continue

            self._erro(tok_c, f"identificador {campo_txt} nao declarado")
            return INDEFINIDO

        while idx_dim < len(exps_dims):
            self._tipo_exp_arit(exps_dims[idx_dim])
            idx_dim += 1

        return tipo_atual
