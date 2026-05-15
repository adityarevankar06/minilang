"""
parser.py — Recursive-descent parser for MiniLang.

Produces an AST from the token stream emitted by the Lexer.
Errors are collected (panic-mode recovery at statement boundaries)
so that multiple syntax problems are reported in one pass.
"""

from __future__ import annotations
from typing import List, Optional

from tokens import Token, TokenType, TOKEN_NAMES
from ast_nodes import (
    ASTNode, Program,
    VarDecl, AssignStmt, IfStmt, WhileStmt, ForStmt,
    FuncDef, ReturnStmt, PrintStmt, ExprStmt,
    BinaryExpr, UnaryExpr, CallExpr,
    Identifier, IntLiteral, FloatLiteral, BoolLiteral, StringLiteral,
)


# ─────────────────────────────── error type ──────────────────────────────────

class ParseError(Exception):
    def __init__(self, message: str, token: Token):
        super().__init__(message)
        self.token = token


class ParseErrorEntry:
    def __init__(self, message: str, line: int, col: int):
        self.message = message
        self.line    = line
        self.col     = col

    def __str__(self) -> str:
        return f"[ParseError] Line {self.line}, Col {self.col}: {self.message}"


# ─────────────────────────────── parser ──────────────────────────────────────

class Parser:
    """
    Recursive-descent parser.

    Usage
    -----
        parser = Parser(tokens)
        tree   = parser.parse()
        if parser.errors:
            for e in parser.errors: print(e)
    """

    # Tokens that introduce a new statement — used for panic-mode recovery
    _SYNC_TOKENS = {
        TokenType.KW_VAR, TokenType.KW_FUNC, TokenType.KW_IF,
        TokenType.KW_WHILE, TokenType.KW_FOR, TokenType.KW_RETURN,
        TokenType.KW_PRINT, TokenType.RBRACE, TokenType.EOF,
    }

    def __init__(self, tokens: List[Token]):
        self._tokens  = tokens
        self._current = 0
        self.errors: List[ParseErrorEntry] = []

    # ──────────────────────────── public API ─────────────────────────────────

    def parse(self) -> Program:
        stmts = self._stmt_list(stop_at=TokenType.EOF)
        return Program(statements=stmts, line=1)

    # ──────────────────────────── token navigation ───────────────────────────

    def _peek(self) -> Token:
        return self._tokens[self._current]

    def _previous(self) -> Token:
        return self._tokens[self._current - 1]

    def _at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _advance(self) -> Token:
        if not self._at_end():
            self._current += 1
        return self._previous()

    def _check(self, *types: TokenType) -> bool:
        return self._peek().type in types

    def _match(self, *types: TokenType) -> bool:
        if self._check(*types):
            self._advance()
            return True
        return False

    def _expect(self, ttype: TokenType, msg: str | None = None) -> Token:
        if self._check(ttype):
            return self._advance()
        tok = self._peek()
        expected_name = TOKEN_NAMES.get(ttype, ttype.name)
        got_name      = TOKEN_NAMES.get(tok.type, tok.type.name)
        message = msg or f"Expected {expected_name}, got {got_name}"
        raise ParseError(message, tok)

    # ──────────────────────────── error recovery ─────────────────────────────

    def _record_error(self, exc: ParseError):
        self.errors.append(
            ParseErrorEntry(str(exc), exc.token.line, exc.token.column)
        )

    def _synchronize(self):
        """Discard tokens until a safe synchronisation point."""
        self._advance()
        while not self._at_end():
            if self._previous().type == TokenType.SEMICOLON:
                return
            if self._peek().type in self._SYNC_TOKENS:
                return
            self._advance()

    # ──────────────────────────── grammar rules ──────────────────────────────

    # <stmt_list>
    def _stmt_list(self, stop_at: TokenType) -> List[ASTNode]:
        stmts: List[ASTNode] = []
        while not self._at_end() and self._peek().type != stop_at:
            if self._peek().type == TokenType.RBRACE:
                break
            try:
                s = self._statement()
                if s is not None:
                    stmts.append(s)
            except ParseError as e:
                self._record_error(e)
                self._synchronize()
        return stmts

    # <stmt>
    def _statement(self) -> Optional[ASTNode]:
        tok = self._peek()

        if tok.type == TokenType.KW_VAR:
            return self._var_decl()
        if tok.type == TokenType.KW_FUNC:
            return self._func_def()
        if tok.type == TokenType.KW_IF:
            return self._if_stmt()
        if tok.type == TokenType.KW_WHILE:
            return self._while_stmt()
        if tok.type == TokenType.KW_FOR:
            return self._for_stmt()
        if tok.type == TokenType.KW_RETURN:
            return self._return_stmt()
        if tok.type == TokenType.KW_PRINT:
            return self._print_stmt()

        # Could be assign or expression statement
        return self._assign_or_expr_stmt()

    # ── var declaration ───────────────────────────────────────────────────────
    def _var_decl(self) -> VarDecl:
        kw   = self._advance()          # consume 'var'
        name = self._expect(TokenType.IDENTIFIER).value
        self._expect(TokenType.COLON)
        vtype = self._type_name()
        init  = None
        if self._match(TokenType.EQUALS):
            init = self._expr()
        self._expect(TokenType.SEMICOLON)
        return VarDecl(name=name, var_type=vtype, init=init, line=kw.line)

    def _type_name(self) -> str:
        tok = self._peek()
        if self._match(TokenType.KW_INT, TokenType.KW_FLOAT,
                       TokenType.KW_BOOL, TokenType.KW_STRING):
            return self._previous().value
        raise ParseError(
            f"Expected a type keyword (int|float|bool|string), got '{tok.value}'", tok
        )

    # ── function definition ───────────────────────────────────────────────────
    def _func_def(self) -> FuncDef:
        kw   = self._advance()           # consume 'func'
        name = self._expect(TokenType.IDENTIFIER).value
        self._expect(TokenType.LPAREN)
        params = self._param_list()
        self._expect(TokenType.RPAREN)
        self._expect(TokenType.COLON)
        rtype = self._type_name()
        self._expect(TokenType.LBRACE)
        body = self._stmt_list(stop_at=TokenType.RBRACE)
        self._expect(TokenType.RBRACE)
        return FuncDef(name=name, params=params, return_type=rtype,
                       body=body, line=kw.line)

    def _param_list(self) -> list[tuple[str, str]]:
        params: list[tuple[str, str]] = []
        if self._check(TokenType.RPAREN):
            return params
        while True:
            pname = self._expect(TokenType.IDENTIFIER).value
            self._expect(TokenType.COLON)
            ptype = self._type_name()
            params.append((pname, ptype))
            if not self._match(TokenType.COMMA):
                break
        return params

    # ── if statement ──────────────────────────────────────────────────────────
    def _if_stmt(self) -> IfStmt:
        kw = self._advance()             # consume 'if'
        self._expect(TokenType.LPAREN)
        cond = self._expr()
        self._expect(TokenType.RPAREN)
        self._expect(TokenType.LBRACE)
        then_body = self._stmt_list(stop_at=TokenType.RBRACE)
        self._expect(TokenType.RBRACE)
        else_body = None
        if self._match(TokenType.KW_ELSE):
            self._expect(TokenType.LBRACE)
            else_body = self._stmt_list(stop_at=TokenType.RBRACE)
            self._expect(TokenType.RBRACE)
        return IfStmt(condition=cond, then_body=then_body,
                      else_body=else_body, line=kw.line)

    # ── while statement ───────────────────────────────────────────────────────
    def _while_stmt(self) -> WhileStmt:
        kw = self._advance()
        self._expect(TokenType.LPAREN)
        cond = self._expr()
        self._expect(TokenType.RPAREN)
        self._expect(TokenType.LBRACE)
        body = self._stmt_list(stop_at=TokenType.RBRACE)
        self._expect(TokenType.RBRACE)
        return WhileStmt(condition=cond, body=body, line=kw.line)

    # ── for statement ─────────────────────────────────────────────────────────
    def _for_stmt(self) -> ForStmt:
        kw = self._advance()             # consume 'for'
        self._expect(TokenType.LPAREN)
        init = self._var_decl()          # already consumes ';'
        cond = self._expr()
        self._expect(TokenType.SEMICOLON)
        upd_name = self._expect(TokenType.IDENTIFIER).value
        self._expect(TokenType.EQUALS)
        upd_val  = self._expr()
        update   = AssignStmt(name=upd_name, value=upd_val, line=self._previous().line)
        self._expect(TokenType.RPAREN)
        self._expect(TokenType.LBRACE)
        body = self._stmt_list(stop_at=TokenType.RBRACE)
        self._expect(TokenType.RBRACE)
        return ForStmt(init=init, condition=cond, update=update,
                       body=body, line=kw.line)

    # ── return / print ────────────────────────────────────────────────────────
    def _return_stmt(self) -> ReturnStmt:
        kw  = self._advance()
        val = self._expr()
        self._expect(TokenType.SEMICOLON)
        return ReturnStmt(value=val, line=kw.line)

    def _print_stmt(self) -> PrintStmt:
        kw = self._advance()
        self._expect(TokenType.LPAREN)
        val = self._expr()
        self._expect(TokenType.RPAREN)
        self._expect(TokenType.SEMICOLON)
        return PrintStmt(value=val, line=kw.line)

    # ── assign-or-expr ────────────────────────────────────────────────────────
    def _assign_or_expr_stmt(self) -> ASTNode:
        tok = self._peek()
        if tok.type == TokenType.IDENTIFIER:
            # look-ahead: is next token '='?
            if (self._current + 1 < len(self._tokens)
                    and self._tokens[self._current + 1].type == TokenType.EQUALS):
                name = self._advance().value
                self._advance()          # consume '='
                val  = self._expr()
                self._expect(TokenType.SEMICOLON)
                return AssignStmt(name=name, value=val, line=tok.line)
        # fall-through: expression statement
        e = self._expr()
        self._expect(TokenType.SEMICOLON)
        return ExprStmt(expr=e, line=tok.line)

    # ──────────────────────── expression parsing (Pratt-style precedence) ─────

    def _expr(self) -> ASTNode:
        return self._or_expr()

    def _or_expr(self) -> ASTNode:
        left = self._and_expr()
        while self._match(TokenType.OR_OR):
            op    = self._previous()
            right = self._and_expr()
            left  = BinaryExpr("||", left, right, line=op.line)
        return left

    def _and_expr(self) -> ASTNode:
        left = self._eq_expr()
        while self._match(TokenType.AND_AND):
            op    = self._previous()
            right = self._eq_expr()
            left  = BinaryExpr("&&", left, right, line=op.line)
        return left

    def _eq_expr(self) -> ASTNode:
        left = self._rel_expr()
        while self._match(TokenType.EQ_EQ, TokenType.BANG_EQ):
            op    = self._previous()
            right = self._rel_expr()
            left  = BinaryExpr(op.value, left, right, line=op.line)
        return left

    def _rel_expr(self) -> ASTNode:
        left = self._add_expr()
        while self._match(TokenType.LT, TokenType.GT,
                          TokenType.LT_EQ, TokenType.GT_EQ):
            op    = self._previous()
            right = self._add_expr()
            left  = BinaryExpr(op.value, left, right, line=op.line)
        return left

    def _add_expr(self) -> ASTNode:
        left = self._mul_expr()
        while self._match(TokenType.PLUS, TokenType.MINUS):
            op    = self._previous()
            right = self._mul_expr()
            left  = BinaryExpr(op.value, left, right, line=op.line)
        return left

    def _mul_expr(self) -> ASTNode:
        left = self._unary_expr()
        while self._match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op    = self._previous()
            right = self._unary_expr()
            left  = BinaryExpr(op.value, left, right, line=op.line)
        return left

    def _unary_expr(self) -> ASTNode:
        if self._match(TokenType.MINUS):
            op  = self._previous()
            opr = self._unary_expr()
            return UnaryExpr("-", opr, line=op.line)
        if self._match(TokenType.BANG):
            op  = self._previous()
            opr = self._unary_expr()
            return UnaryExpr("!", opr, line=op.line)
        return self._primary()

    def _primary(self) -> ASTNode:
        tok = self._advance()

        if tok.type == TokenType.INTEGER:
            return IntLiteral(value=int(tok.value), line=tok.line)

        if tok.type == TokenType.FLOAT:
            return FloatLiteral(value=float(tok.value), line=tok.line)

        if tok.type == TokenType.BOOL:
            return BoolLiteral(value=(tok.value == "true"), line=tok.line)

        if tok.type == TokenType.STRING:
            return StringLiteral(value=tok.value, line=tok.line)

        if tok.type == TokenType.IDENTIFIER:
            # function call?
            if self._match(TokenType.LPAREN):
                args = self._arg_list()
                self._expect(TokenType.RPAREN)
                return CallExpr(callee=tok.value, args=args, line=tok.line)
            return Identifier(name=tok.value, line=tok.line)

        if tok.type == TokenType.LPAREN:
            inner = self._expr()
            self._expect(TokenType.RPAREN)
            return inner

        raise ParseError(
            f"Unexpected token '{tok.value}' in expression", tok
        )

    def _arg_list(self) -> List[ASTNode]:
        args: List[ASTNode] = []
        if self._check(TokenType.RPAREN):
            return args
        while True:
            args.append(self._expr())
            if not self._match(TokenType.COMMA):
                break
        return args
