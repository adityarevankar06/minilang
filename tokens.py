"""
tokens.py — Token type definitions for the MiniLang DSL compiler.
"""

from enum import Enum, auto


class TokenType(Enum):
    # ── Literals ──────────────────────────────────────────────────────────────
    INTEGER     = auto()
    FLOAT       = auto()
    STRING      = auto()
    BOOL        = auto()

    # ── Identifiers / Keywords ────────────────────────────────────────────────
    IDENTIFIER  = auto()

    # Keywords
    KW_VAR      = auto()
    KW_FUNC     = auto()
    KW_IF       = auto()
    KW_ELSE     = auto()
    KW_WHILE    = auto()
    KW_FOR      = auto()
    KW_RETURN   = auto()
    KW_PRINT    = auto()

    # Types
    KW_INT      = auto()
    KW_FLOAT    = auto()
    KW_BOOL     = auto()
    KW_STRING   = auto()

    # ── Arithmetic Operators ──────────────────────────────────────────────────
    PLUS        = auto()   # +
    MINUS       = auto()   # -
    STAR        = auto()   # *
    SLASH       = auto()   # /
    PERCENT     = auto()   # %

    # ── Relational Operators ──────────────────────────────────────────────────
    EQ_EQ       = auto()   # ==
    BANG_EQ     = auto()   # !=
    LT          = auto()   # <
    GT          = auto()   # >
    LT_EQ       = auto()   # <=
    GT_EQ       = auto()   # >=

    # ── Logical Operators ─────────────────────────────────────────────────────
    AND_AND     = auto()   # &&
    OR_OR       = auto()   # ||
    BANG        = auto()   # !

    # ── Assignment ────────────────────────────────────────────────────────────
    EQUALS      = auto()   # =

    # ── Delimiters ────────────────────────────────────────────────────────────
    LPAREN      = auto()   # (
    RPAREN      = auto()   # )
    LBRACE      = auto()   # {
    RBRACE      = auto()   # }
    COLON       = auto()   # :
    COMMA       = auto()   # ,
    SEMICOLON   = auto()   # ;

    # ── Special ───────────────────────────────────────────────────────────────
    EOF         = auto()
    ILLEGAL     = auto()


# Map keyword strings → their TokenType
KEYWORDS: dict[str, TokenType] = {
    "var":    TokenType.KW_VAR,
    "func":   TokenType.KW_FUNC,
    "if":     TokenType.KW_IF,
    "else":   TokenType.KW_ELSE,
    "while":  TokenType.KW_WHILE,
    "for":    TokenType.KW_FOR,
    "return": TokenType.KW_RETURN,
    "print":  TokenType.KW_PRINT,
    "int":    TokenType.KW_INT,
    "float":  TokenType.KW_FLOAT,
    "bool":   TokenType.KW_BOOL,
    "string": TokenType.KW_STRING,
    "true":   TokenType.BOOL,
    "false":  TokenType.BOOL,
}

# Human-readable names used in error messages
TOKEN_NAMES: dict[TokenType, str] = {
    TokenType.INTEGER:    "integer literal",
    TokenType.FLOAT:      "float literal",
    TokenType.STRING:     "string literal",
    TokenType.BOOL:       "boolean literal",
    TokenType.IDENTIFIER: "identifier",
    TokenType.KW_VAR:     "'var'",
    TokenType.KW_FUNC:    "'func'",
    TokenType.KW_IF:      "'if'",
    TokenType.KW_ELSE:    "'else'",
    TokenType.KW_WHILE:   "'while'",
    TokenType.KW_FOR:     "'for'",
    TokenType.KW_RETURN:  "'return'",
    TokenType.KW_PRINT:   "'print'",
    TokenType.KW_INT:     "'int'",
    TokenType.KW_FLOAT:   "'float'",
    TokenType.KW_BOOL:    "'bool'",
    TokenType.KW_STRING:  "'string'",
    TokenType.PLUS:       "'+'",
    TokenType.MINUS:      "'-'",
    TokenType.STAR:       "'*'",
    TokenType.SLASH:      "'/'",
    TokenType.PERCENT:    "'%'",
    TokenType.EQ_EQ:      "'=='",
    TokenType.BANG_EQ:    "'!='",
    TokenType.LT:         "'<'",
    TokenType.GT:         "'>'",
    TokenType.LT_EQ:      "'<='",
    TokenType.GT_EQ:      "'>='",
    TokenType.AND_AND:    "'&&'",
    TokenType.OR_OR:      "'||'",
    TokenType.BANG:       "'!'",
    TokenType.EQUALS:     "'='",
    TokenType.LPAREN:     "'('",
    TokenType.RPAREN:     "')'",
    TokenType.LBRACE:     "'{'",
    TokenType.RBRACE:     "'}'",
    TokenType.COLON:      "':'",
    TokenType.COMMA:      "','",
    TokenType.SEMICOLON:  "';'",
    TokenType.EOF:        "end-of-file",
    TokenType.ILLEGAL:    "illegal token",
}


class Token:
    """Represents a single lexeme produced by the lexer."""

    __slots__ = ("type", "value", "line", "column")

    def __init__(self, type_: TokenType, value: str, line: int, column: int):
        self.type   = type_
        self.value  = value
        self.line   = line
        self.column = column

    def __repr__(self) -> str:
        return (f"Token({self.type.name}, {self.value!r}, "
                f"line={self.line}, col={self.column})")
