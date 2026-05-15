"""
lexer.py — Lexical analyser (scanner) for the MiniLang DSL.

Converts raw source text into a flat list of Token objects.
All lexical errors are collected; scanning continues so that
later passes can report multiple issues in one run.
"""

from __future__ import annotations
from typing import List
from tokens import Token, TokenType, KEYWORDS


class LexerError(Exception):
    """Raised when the lexer encounters an unrecoverable situation."""


class LexerErrorEntry:
    """A single recoverable lexical error."""

    def __init__(self, message: str, line: int, column: int):
        self.message = message
        self.line    = line
        self.column  = column

    def __str__(self) -> str:
        return f"[LexError] Line {self.line}, Col {self.column}: {self.message}"


class Lexer:
    """
    Hand-written, single-pass lexer.

    Usage
    -----
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        if lexer.errors:
            for e in lexer.errors: print(e)
    """

    def __init__(self, source: str):
        self._src    = source
        self._pos    = 0          # current character index
        self._line   = 1
        self._col    = 1
        self.errors: List[LexerErrorEntry] = []
        self.tokens: List[Token]           = []

    # ─────────────────────────────── public API ───────────────────────────────

    def tokenize(self) -> List[Token]:
        """Scan the entire source and return the token list."""
        while not self._at_end():
            self._skip_whitespace_and_comments()
            if self._at_end():
                break
            tok = self._next_token()
            if tok is not None:
                self.tokens.append(tok)

        self.tokens.append(Token(TokenType.EOF, "", self._line, self._col))
        return self.tokens

    # ─────────────────────────────── helpers ──────────────────────────────────

    def _at_end(self) -> bool:
        return self._pos >= len(self._src)

    def _peek(self, offset: int = 0) -> str:
        idx = self._pos + offset
        return self._src[idx] if idx < len(self._src) else "\0"

    def _advance(self) -> str:
        ch = self._src[self._pos]
        self._pos += 1
        if ch == "\n":
            self._line += 1
            self._col = 1
        else:
            self._col += 1
        return ch

    def _match(self, expected: str) -> bool:
        """Consume the next char only if it equals *expected*."""
        if self._at_end() or self._peek() != expected:
            return False
        self._advance()
        return True

    def _make_token(self, type_: TokenType, value: str,
                    line: int, col: int) -> Token:
        return Token(type_, value, line, col)

    def _error(self, msg: str, line: int, col: int):
        self.errors.append(LexerErrorEntry(msg, line, col))

    # ─────────────────────────────── whitespace / comments ────────────────────

    def _skip_whitespace_and_comments(self):
        while not self._at_end():
            ch = self._peek()
            if ch in " \t\r\n":
                self._advance()
            elif ch == "#":              # single-line comment
                while not self._at_end() and self._peek() != "\n":
                    self._advance()
            else:
                break

    # ─────────────────────────────── token dispatch ───────────────────────────

    def _next_token(self) -> Token | None:
        start_line = self._line
        start_col  = self._col
        ch = self._advance()

        # ── Single-char tokens ───────────────────────────────────────────────
        simple = {
            "(": TokenType.LPAREN,
            ")": TokenType.RPAREN,
            "{": TokenType.LBRACE,
            "}": TokenType.RBRACE,
            ":": TokenType.COLON,
            ",": TokenType.COMMA,
            ";": TokenType.SEMICOLON,
            "+": TokenType.PLUS,
            "*": TokenType.STAR,
            "%": TokenType.PERCENT,
        }
        if ch in simple:
            return self._make_token(simple[ch], ch, start_line, start_col)

        # ── Possibly two-char tokens ──────────────────────────────────────────
        if ch == "-":
            return self._make_token(TokenType.MINUS, "-", start_line, start_col)

        if ch == "/":
            return self._make_token(TokenType.SLASH, "/", start_line, start_col)

        if ch == "=":
            if self._match("="):
                return self._make_token(TokenType.EQ_EQ, "==", start_line, start_col)
            return self._make_token(TokenType.EQUALS, "=", start_line, start_col)

        if ch == "!":
            if self._match("="):
                return self._make_token(TokenType.BANG_EQ, "!=", start_line, start_col)
            return self._make_token(TokenType.BANG, "!", start_line, start_col)

        if ch == "<":
            if self._match("="):
                return self._make_token(TokenType.LT_EQ, "<=", start_line, start_col)
            return self._make_token(TokenType.LT, "<", start_line, start_col)

        if ch == ">":
            if self._match("="):
                return self._make_token(TokenType.GT_EQ, ">=", start_line, start_col)
            return self._make_token(TokenType.GT, ">", start_line, start_col)

        if ch == "&":
            if self._match("&"):
                return self._make_token(TokenType.AND_AND, "&&", start_line, start_col)
            self._error(f"Expected '&&' but got '&{self._peek()}'", start_line, start_col)
            return None

        if ch == "|":
            if self._match("|"):
                return self._make_token(TokenType.OR_OR, "||", start_line, start_col)
            self._error(f"Expected '||' but got '|{self._peek()}'", start_line, start_col)
            return None

        # ── String literal ────────────────────────────────────────────────────
        if ch == '"':
            return self._scan_string(start_line, start_col)

        # ── Numeric literal ───────────────────────────────────────────────────
        if ch.isdigit():
            return self._scan_number(ch, start_line, start_col)

        # ── Identifier / keyword ──────────────────────────────────────────────
        if ch.isalpha() or ch == "_":
            return self._scan_identifier(ch, start_line, start_col)

        # ── Illegal ───────────────────────────────────────────────────────────
        self._error(f"Unexpected character '{ch}'", start_line, start_col)
        return self._make_token(TokenType.ILLEGAL, ch, start_line, start_col)

    # ─────────────────────────────── scan helpers ────────────────────────────

    def _scan_string(self, line: int, col: int) -> Token:
        buf: list[str] = []
        while not self._at_end() and self._peek() != '"':
            if self._peek() == "\n":
                self._error("Unterminated string literal", line, col)
                break
            buf.append(self._advance())
        if self._at_end():
            self._error("Unterminated string literal at EOF", line, col)
        else:
            self._advance()   # consume closing "
        return self._make_token(TokenType.STRING, "".join(buf), line, col)

    def _scan_number(self, first_ch: str, line: int, col: int) -> Token:
        buf = [first_ch]
        while not self._at_end() and self._peek().isdigit():
            buf.append(self._advance())

        is_float = False
        if not self._at_end() and self._peek() == "." and self._peek(1).isdigit():
            is_float = True
            buf.append(self._advance())   # consume '.'
            while not self._at_end() and self._peek().isdigit():
                buf.append(self._advance())

        lexeme = "".join(buf)
        ttype  = TokenType.FLOAT if is_float else TokenType.INTEGER
        return self._make_token(ttype, lexeme, line, col)

    def _scan_identifier(self, first_ch: str, line: int, col: int) -> Token:
        buf = [first_ch]
        while not self._at_end() and (self._peek().isalnum() or self._peek() == "_"):
            buf.append(self._advance())
        lexeme = "".join(buf)
        ttype  = KEYWORDS.get(lexeme, TokenType.IDENTIFIER)
        return self._make_token(ttype, lexeme, line, col)
