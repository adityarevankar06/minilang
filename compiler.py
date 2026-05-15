"""
compiler.py — Main driver for the MiniLang DSL compiler front-end.

Pipeline
--------
  Source text
    → Lexer         → token list
    → Parser        → AST
    → SemanticAnalyser  → annotated AST + symbol table
    → TACGenerator  → Three-Address Code
"""

from __future__ import annotations
import sys
from typing import Optional

from lexer    import Lexer
from parser   import Parser
from semantic import SemanticAnalyser
from tac_gen  import TACGenerator, TACProgram


class CompilerResult:
    """Holds all artefacts produced by a compilation run."""

    def __init__(self):
        self.tokens          = []
        self.ast             = None
        self.symbol_table    = None
        self.tac: Optional[TACProgram] = None
        self.lexer_errors    = []
        self.parse_errors    = []
        self.semantic_errors = []

    @property
    def success(self) -> bool:
        return not (self.lexer_errors or
                    self.parse_errors or
                    self.semantic_errors)

    @property
    def all_errors(self) -> list:
        return self.lexer_errors + self.parse_errors + self.semantic_errors


def compile_source(source: str, verbose: bool = False) -> CompilerResult:
    """
    Run all front-end passes on *source*.
    Returns a CompilerResult regardless of whether errors occurred.
    """
    result = CompilerResult()

    # ── Pass 1: Lexical analysis ──────────────────────────────────────────────
    lexer = Lexer(source)
    result.tokens = lexer.tokenize()
    result.lexer_errors = lexer.errors

    if verbose:
        print("=" * 60)
        print("TOKENS")
        print("=" * 60)
        for tok in result.tokens:
            print(f"  {tok}")

    if result.lexer_errors:
        print("\n── Lexer Errors ──")
        for e in result.lexer_errors:
            print(e)
        # Continue to parser anyway (errors in token stream are marked ILLEGAL)

    # ── Pass 2: Syntax analysis ───────────────────────────────────────────────
    parser = Parser(result.tokens)
    result.ast = parser.parse()
    result.parse_errors = parser.errors

    if verbose:
        print("\n" + "=" * 60)
        print("AST (repr)")
        print("=" * 60)
        _print_ast(result.ast, indent=0)

    if result.parse_errors:
        print("\n── Parse Errors ──")
        for e in result.parse_errors:
            print(e)
        # Cannot run semantic / TAC on broken AST reliably
        return result

    # ── Pass 3: Semantic analysis ─────────────────────────────────────────────
    analyser = SemanticAnalyser()
    analyser.analyse(result.ast)
    result.symbol_table    = analyser.symbol_table
    result.semantic_errors = analyser.errors

    if verbose:
        print("\n" + "=" * 60)
        print("SYMBOL TABLE")
        print("=" * 60)
        print(result.symbol_table.dump())

    if result.semantic_errors:
        print("\n── Semantic Errors ──")
        for e in result.semantic_errors:
            print(e)
        return result

    # ── Pass 4: TAC generation ────────────────────────────────────────────────
    gen = TACGenerator()
    result.tac = gen.generate(result.ast)

    return result


# ─────────────────────────────── AST pretty-printer ──────────────────────────

def _print_ast(node, indent: int):
    prefix = "  " * indent
    name = type(node).__name__
    from dataclasses import fields, is_dataclass
    if not is_dataclass(node):
        print(f"{prefix}{node!r}")
        return
    flds = fields(node)
    parts = []
    children = []
    for f in flds:
        val = getattr(node, f.name)
        if isinstance(val, list):
            children.append((f.name, val))
        elif hasattr(val, "__dataclass_fields__"):
            children.append((f.name, [val]))
        else:
            parts.append(f"{f.name}={val!r}")
    print(f"{prefix}{name}({', '.join(parts)})")
    for fname, items in children:
        print(f"{prefix}  [{fname}]")
        for item in items:
            _print_ast(item, indent + 2)


# ─────────────────────────────── CLI entry-point ─────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python compiler.py <source_file> [--verbose]")
        sys.exit(1)

    src_path = sys.argv[1]
    verbose  = "--verbose" in sys.argv or "-v" in sys.argv

    try:
        with open(src_path, "r", encoding="utf-8") as fh:
            source = fh.read()
    except FileNotFoundError:
        print(f"Error: file not found: {src_path}")
        sys.exit(1)

    print(f"\nCompiling: {src_path}")
    print("=" * 60)

    result = compile_source(source, verbose=verbose)

    if result.success:
        print("\n✓ Compilation successful — no errors.\n")
        print("=" * 60)
        print("THREE-ADDRESS CODE (TAC)")
        print("=" * 60)
        print(result.tac)
        if verbose and result.symbol_table:
            print("\n" + "=" * 60)
            print("FINAL SYMBOL TABLE")
            print("=" * 60)
            print(result.symbol_table.dump())
    else:
        total = len(result.all_errors)
        print(f"\n✗ Compilation failed with {total} error(s).")
        sys.exit(1)


if __name__ == "__main__":
    main()
