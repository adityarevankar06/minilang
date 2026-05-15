"""
ast_nodes.py — Abstract Syntax Tree node definitions for MiniLang.

Every node is a plain dataclass-style Python class.
The visitor pattern is used by later passes (semantic analysis,
code generation) to traverse the tree without modifying these nodes.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


# ─────────────────────────────── base ────────────────────────────────────────

class ASTNode:
    """Base class for all AST nodes."""

    def accept(self, visitor):
        method = "visit_" + type(self).__name__
        return getattr(visitor, method)(self)


# ─────────────────────────────── program ─────────────────────────────────────

@dataclass
class Program(ASTNode):
    statements: List[ASTNode]
    line: int = 0


# ─────────────────────────────── statements ──────────────────────────────────

@dataclass
class VarDecl(ASTNode):
    """var name : type [ = expr ] ;"""
    name:     str
    var_type: str                      # 'int' | 'float' | 'bool' | 'string'
    init:     Optional[ASTNode]        # initialiser expression, may be None
    line:     int = 0


@dataclass
class AssignStmt(ASTNode):
    """name = expr ;"""
    name:  str
    value: ASTNode
    line:  int = 0


@dataclass
class IfStmt(ASTNode):
    condition:   ASTNode
    then_body:   List[ASTNode]
    else_body:   Optional[List[ASTNode]]
    line:        int = 0


@dataclass
class WhileStmt(ASTNode):
    condition: ASTNode
    body:      List[ASTNode]
    line:      int = 0


@dataclass
class ForStmt(ASTNode):
    """for ( var_decl ; cond ; update ) { body }"""
    init:      VarDecl
    condition: ASTNode
    update:    AssignStmt
    body:      List[ASTNode]
    line:      int = 0


@dataclass
class FuncDef(ASTNode):
    name:        str
    params:      List[tuple[str, str]]   # [(param_name, type_str), ...]
    return_type: str
    body:        List[ASTNode]
    line:        int = 0


@dataclass
class ReturnStmt(ASTNode):
    value: ASTNode
    line:  int = 0


@dataclass
class PrintStmt(ASTNode):
    value: ASTNode
    line:  int = 0


@dataclass
class ExprStmt(ASTNode):
    expr: ASTNode
    line: int = 0


# ─────────────────────────────── expressions ─────────────────────────────────

@dataclass
class BinaryExpr(ASTNode):
    operator: str       # '+', '-', '*', '/', '%', '==', etc.
    left:     ASTNode
    right:    ASTNode
    line:     int = 0


@dataclass
class UnaryExpr(ASTNode):
    operator: str       # '-' or '!'
    operand:  ASTNode
    line:     int = 0


@dataclass
class CallExpr(ASTNode):
    callee: str
    args:   List[ASTNode]
    line:   int = 0


@dataclass
class Identifier(ASTNode):
    name: str
    line: int = 0


@dataclass
class IntLiteral(ASTNode):
    value: int
    line:  int = 0


@dataclass
class FloatLiteral(ASTNode):
    value: float
    line:  int = 0


@dataclass
class BoolLiteral(ASTNode):
    value: bool
    line:  int = 0


@dataclass
class StringLiteral(ASTNode):
    value: str
    line:  int = 0
