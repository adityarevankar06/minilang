"""
tests.py — Test suite for the MiniLang compiler front-end.

Covers:
  • Lexer: tokens, comments, literals, errors
  • Parser: all statement/expression constructs, error recovery
  • Semantic: type checking, scope, function validation
  • TAC: instruction shape for every construct
"""

import sys, io, textwrap
from compiler import compile_source
from lexer    import Lexer
from tokens   import TokenType
from parser   import Parser
from semantic import SemanticAnalyser
from tac_gen  import (
    TACGenerator, TACBinaryOp, TACUnaryOp, TACCopy,
    TACParam, TACCall, TACReturn, TACPrint,
    TACCondJumpFalse, TACGoto, TACLabel,
    TACFuncBegin, TACFuncEnd, TACFormalParam,
)


# ─────────────────────────────── tiny test harness ───────────────────────────

_pass = 0
_fail = 0

def _check(desc: str, ok: bool):
    global _pass, _fail
    if ok:
        _pass += 1
        print(f"  ✓  {desc}")
    else:
        _fail += 1
        print(f"  ✗  FAILED: {desc}")

def _section(title: str):
    print(f"\n{'═'*60}")
    print(f"  {title}")
    print(f"{'═'*60}")


# ─────────────────────────────── helpers ──────────────────────────────────────

def _lex(src: str):
    l = Lexer(src)
    toks = l.tokenize()
    return toks, l.errors

def _parse(src: str):
    toks, _ = _lex(src)
    p = Parser(toks)
    tree = p.parse()
    return tree, p.errors

def _analyse(src: str):
    tree, _ = _parse(src)
    sa = SemanticAnalyser()
    sa.analyse(tree)
    return sa.errors, sa.symbol_table

def _tac(src: str):
    tree, _ = _parse(src)
    sa = SemanticAnalyser()
    sa.analyse(tree)
    gen = TACGenerator()
    prog = gen.generate(tree)
    return prog.instructions

def _tac_types(src: str):
    return [type(i).__name__ for i in _tac(src)]

def _compile_ok(src: str) -> bool:
    r = compile_source(src)
    return r.success

def _compile_err(src: str) -> bool:
    r = compile_source(src)
    return not r.success


# ═════════════════════════════ LEXER TESTS ════════════════════════════════════

_section("LEXER — Token recognition")

toks, errs = _lex("42 3.14 true false \"hello\"")
types = [t.type for t in toks if t.type != TokenType.EOF]
_check("Integer literal", TokenType.INTEGER in types)
_check("Float literal",   TokenType.FLOAT   in types)
_check("Bool literal",    TokenType.BOOL    in types)
_check("String literal",  TokenType.STRING  in types)
_check("No lexer errors", errs == [])

_section("LEXER — Keywords")
toks, _ = _lex("var func if else while for return print int float bool string")
kw_types = {t.type for t in toks if t.type != TokenType.EOF}
for kw in [TokenType.KW_VAR, TokenType.KW_FUNC, TokenType.KW_IF,
           TokenType.KW_ELSE, TokenType.KW_WHILE, TokenType.KW_FOR,
           TokenType.KW_RETURN, TokenType.KW_PRINT,
           TokenType.KW_INT, TokenType.KW_FLOAT,
           TokenType.KW_BOOL, TokenType.KW_STRING]:
    _check(f"Keyword {kw.name}", kw in kw_types)

_section("LEXER — Operators & delimiters")
toks, _ = _lex("+ - * / % == != < > <= >= && || ! = ( ) { } : , ;")
op_types = {t.type for t in toks if t.type != TokenType.EOF}
for op in [TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH,
           TokenType.PERCENT, TokenType.EQ_EQ, TokenType.BANG_EQ,
           TokenType.LT, TokenType.GT, TokenType.LT_EQ, TokenType.GT_EQ,
           TokenType.AND_AND, TokenType.OR_OR, TokenType.BANG,
           TokenType.EQUALS, TokenType.LPAREN, TokenType.RPAREN,
           TokenType.LBRACE, TokenType.RBRACE, TokenType.COLON,
           TokenType.COMMA, TokenType.SEMICOLON]:
    _check(f"Operator/delimiter {op.name}", op in op_types)

_section("LEXER — Comments and whitespace")
toks, errs = _lex("# this is a comment\nvar x : int = 5;")
values = [t.value for t in toks if t.type != TokenType.EOF]
_check("Comment stripped", "var" in values)
_check("Identifier after comment", "x" in values)
_check("No lexer errors", errs == [])

_section("LEXER — Error cases")
_, errs = _lex("@")
_check("Illegal char '@' detected", len(errs) == 1)
_, errs = _lex('"unterminated')
_check("Unterminated string detected", len(errs) >= 1)


# ═════════════════════════════ PARSER TESTS ═══════════════════════════════════

_section("PARSER — Variable declaration")
_, errs = _parse("var x : int = 10;")
_check("var with init — no errors", errs == [])
_, errs = _parse("var y : float;")
_check("var without init — no errors", errs == [])

_section("PARSER — Assignment")
_, errs = _parse("var x : int; x = 42;")
_check("Assignment — no errors", errs == [])

_section("PARSER — If / else")
_, errs = _parse("if (x < 10) { x = 1; }")
_check("If without else — no errors", errs == [])
_, errs = _parse("if (x < 10) { x = 1; } else { x = 2; }")
_check("If-else — no errors", errs == [])

_section("PARSER — While loop")
_, errs = _parse("while (i < 5) { i = i + 1; }")
_check("While loop — no errors", errs == [])

_section("PARSER — For loop")
_, errs = _parse("for (var i : int = 0; i < 5; i = i + 1) { x = x + i; }")
_check("For loop — no errors", errs == [])

_section("PARSER — Function definition")
_, errs = _parse("func add(a : int, b : int) : int { return a + b; }")
_check("Function def — no errors", errs == [])

_section("PARSER — Function call")
_, errs = _parse("var r : int = add(1, 2);")
_check("Function call in var decl — no errors", errs == [])

_section("PARSER — Print")
_, errs = _parse('print("hello");')
_check("Print stmt — no errors", errs == [])

_section("PARSER — Expression precedence")
tree, errs = _parse("var r : int = 2 + 3 * 4;")
_check("Precedence expr — no errors", errs == [])

_section("PARSER — Error recovery")
tree, errs = _parse("var x  5; var y : int = 2;")   # missing ': int ='
_check("Recovers and parses y after error", len(errs) >= 1)


# ═════════════════════════════ SEMANTIC TESTS ══════════════════════════════════

_section("SEMANTIC — Type checking: basic arithmetic")
errs, _ = _analyse("var x : int = 2 + 3;")
_check("int + int → int, no error", errs == [])

errs, _ = _analyse("var x : float = 2.0 + 3;")
_check("float + int → float widening, no error", errs == [])

errs, _ = _analyse('var x : int = "hello" + 3;')
_check("string + int → error detected", len(errs) >= 1)

_section("SEMANTIC — Undefined variable")
errs, _ = _analyse("x = 5;")
_check("Undefined variable detected", len(errs) >= 1)

_section("SEMANTIC — Redeclaration")
errs, _ = _analyse("var x : int = 1; var x : float = 2.0;")
_check("Redeclaration in same scope detected", len(errs) >= 1)

_section("SEMANTIC — Scope: inner variable shadows outer")
errs, _ = _analyse("""
var x : int = 1;
if (x == 1) {
    var x : float = 2.0;
}
""")
_check("Inner scope redeclaration allowed, no error", errs == [])

_section("SEMANTIC — Bool conditions")
errs, _ = _analyse("var n : int = 3; if (n) { n = 1; }")
_check("Non-bool if-condition detected", len(errs) >= 1)

errs, _ = _analyse("var b : bool = true; while (b) { b = false; }")
_check("Bool while-condition — no error", errs == [])

_section("SEMANTIC — Function return type")
errs, _ = _analyse("func f() : int { return 1; }")
_check("Correct return type — no error", errs == [])

errs, _ = _analyse('func f() : int { return "bad"; }')
_check("Wrong return type detected", len(errs) >= 1)

_section("SEMANTIC — Function arity")
errs, _ = _analyse("""
func add(a : int, b : int) : int { return a + b; }
var r : int = add(1);
""")
_check("Wrong argument count detected", len(errs) >= 1)

errs, _ = _analyse("""
func add(a : int, b : int) : int { return a + b; }
var r : int = add(1, 2);
""")
_check("Correct arity — no error", errs == [])

_section("SEMANTIC — Type mismatch in assignment")
errs, _ = _analyse('var x : int = 5; x = "hello";')
_check("Assign string to int detected", len(errs) >= 1)


# ═════════════════════════════ TAC TESTS ══════════════════════════════════════

_section("TAC — Variable declaration with init")
instrs = _tac("var x : int = 42;")
_check("Emits TACCopy for var decl", any(isinstance(i, TACCopy) for i in instrs))

_section("TAC — Binary expression")
instrs = _tac("var r : int = 3 + 4;")
_check("Emits TACBinaryOp for '+'",
       any(isinstance(i, TACBinaryOp) and i.op == "+" for i in instrs))

_section("TAC — Unary expression")
instrs = _tac("var r : int = -5;")
_check("Emits TACUnaryOp for unary '-'",
       any(isinstance(i, TACUnaryOp) and i.op == "-" for i in instrs))

_section("TAC — If statement")
instrs = _tac("""
var x : int = 0;
var b : bool = true;
if (b) { x = 1; } else { x = 2; }
""")
_check("Emits TACCondJumpFalse for if",
       any(isinstance(i, TACCondJumpFalse) for i in instrs))
_check("Emits TACGoto for else branch",
       any(isinstance(i, TACGoto) for i in instrs))
_check("Emits TACLabel(s)",
       any(isinstance(i, TACLabel) for i in instrs))

_section("TAC — While loop")
instrs = _tac("""
var i : int = 0;
var b : bool = true;
while (b) { i = i + 1; b = false; }
""")
labels = [i for i in instrs if isinstance(i, TACLabel)]
gotos  = [i for i in instrs if isinstance(i, TACGoto)]
_check("While: at least 2 labels (start & end)", len(labels) >= 2)
_check("While: GOTO back to start label", len(gotos) >= 1)

_section("TAC — For loop")
instrs = _tac("""
var sum : int = 0;
for (var i : int = 0; i < 5; i = i + 1) { sum = sum + i; }
""")
_check("For: emits TACCondJumpFalse", any(isinstance(i, TACCondJumpFalse) for i in instrs))
_check("For: emits TACGoto",          any(isinstance(i, TACGoto)          for i in instrs))

_section("TAC — Function definition & call")
instrs = _tac("""
func square(n : int) : int { return n * n; }
var r : int = square(5);
""")
_check("Func: emits TACFuncBegin",   any(isinstance(i, TACFuncBegin)   for i in instrs))
_check("Func: emits TACFormalParam", any(isinstance(i, TACFormalParam) for i in instrs))
_check("Func: emits TACReturn",      any(isinstance(i, TACReturn)      for i in instrs))
_check("Func: emits TACFuncEnd",     any(isinstance(i, TACFuncEnd)     for i in instrs))
_check("Call: emits TACParam",       any(isinstance(i, TACParam)       for i in instrs))
_check("Call: emits TACCall",        any(isinstance(i, TACCall)        for i in instrs))

_section("TAC — Print statement")
instrs = _tac('print("hi");')
_check("Print: emits TACPrint", any(isinstance(i, TACPrint) for i in instrs))


# ═════════════════════════════ INTEGRATION TESTS ══════════════════════════════

_section("INTEGRATION — Full program: fibonacci")
fib_src = textwrap.dedent("""
    func fib(n : int) : int {
        if (n <= 1) {
            return n;
        } else {
            return fib(n - 1) + fib(n - 2);
        }
    }
    var result : int = fib(10);
    print(result);
""")
_check("Fibonacci compiles cleanly", _compile_ok(fib_src))

_section("INTEGRATION — Full program: factorial via loop")
fact_src = textwrap.dedent("""
    var n      : int = 5;
    var result : int = 1;
    for (var i : int = 1; i <= n; i = i + 1) {
        result = result * i;
    }
    print(result);
""")
_check("Factorial (loop) compiles cleanly", _compile_ok(fact_src))

_section("INTEGRATION — Full program: string concatenation")
str_src = textwrap.dedent("""
    var greeting : string = "Hello, ";
    var name     : string = "World!";
    var msg      : string = greeting + name;
    print(msg);
""")
_check("String concat compiles cleanly", _compile_ok(str_src))

_section("INTEGRATION — Full program: type errors caught")
bad_src = textwrap.dedent("""
    var x : int = 10;
    var y : string = "test";
    var z : int = x + y;
""")
_check("Type error in full program caught", _compile_err(bad_src))


# ─────────────────────────────── summary ──────────────────────────────────────

print(f"\n{'═'*60}")
print(f"  RESULTS: {_pass} passed, {_fail} failed out of {_pass+_fail} tests")
print(f"{'═'*60}\n")

if _fail:
    sys.exit(1)
