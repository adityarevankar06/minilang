"""
tac_gen.py — Three-Address Code (TAC) generation for MiniLang.

TAC instructions:
  t = a OP b          BinaryOp
  t = OP a            UnaryOp
  t = a               Copy
  PARAM a             push call argument
  t = CALL f, n       call function f with n args, result in t
  RETURN a            return value
  PRINT a             print value
  IF a GOTO L         conditional branch (truthy)
  GOTO L              unconditional jump
  LABEL L:            label definition
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Union

from ast_nodes import (
    ASTNode, Program,
    VarDecl, AssignStmt, IfStmt, WhileStmt, ForStmt,
    FuncDef, ReturnStmt, PrintStmt, ExprStmt,
    BinaryExpr, UnaryExpr, CallExpr,
    Identifier, IntLiteral, FloatLiteral, BoolLiteral, StringLiteral,
)


# ─────────────────────────────── TAC instructions ────────────────────────────

@dataclass
class TACLabel:
    name: str
    def __str__(self): return f"{self.name}:"

@dataclass
class TACBinaryOp:
    result: str; op: str; left: str; right: str
    def __str__(self): return f"    {self.result} = {self.left} {self.op} {self.right}"

@dataclass
class TACUnaryOp:
    result: str; op: str; operand: str
    def __str__(self): return f"    {self.result} = {self.op}{self.operand}"

@dataclass
class TACCopy:
    result: str; source: str
    def __str__(self): return f"    {self.result} = {self.source}"

@dataclass
class TACParam:
    value: str
    def __str__(self): return f"    PARAM {self.value}"

@dataclass
class TACCall:
    result: str; func: str; arg_count: int
    def __str__(self): return f"    {self.result} = CALL {self.func}, {self.arg_count}"

@dataclass
class TACReturn:
    value: str
    def __str__(self): return f"    RETURN {self.value}"

@dataclass
class TACPrint:
    value: str
    def __str__(self): return f"    PRINT {self.value}"

@dataclass
class TACCondJump:
    condition: str; label: str
    def __str__(self): return f"    IF {self.condition} GOTO {self.label}"

@dataclass
class TACCondJumpFalse:
    condition: str; label: str
    def __str__(self): return f"    IFFALSE {self.condition} GOTO {self.label}"

@dataclass
class TACGoto:
    label: str
    def __str__(self): return f"    GOTO {self.label}"

@dataclass
class TACFuncBegin:
    name: str
    def __str__(self): return f"\nFUNC_BEGIN {self.name}:"

@dataclass
class TACFuncEnd:
    name: str
    def __str__(self): return f"FUNC_END {self.name}\n"

@dataclass
class TACFormalParam:
    name: str; type_: str
    def __str__(self): return f"    FORMAL {self.name} : {self.type_}"

TACInstruction = Union[
    TACLabel, TACBinaryOp, TACUnaryOp, TACCopy,
    TACParam, TACCall, TACReturn, TACPrint,
    TACCondJump, TACCondJumpFalse, TACGoto,
    TACFuncBegin, TACFuncEnd, TACFormalParam,
]


# ─────────────────────────────── TAC programme ───────────────────────────────

class TACProgram:
    def __init__(self):
        self.instructions: List[TACInstruction] = []

    def emit(self, instr: TACInstruction):
        self.instructions.append(instr)

    def __str__(self) -> str:
        return "\n".join(str(i) for i in self.instructions)


# ─────────────────────────────── generator ───────────────────────────────────

class TACGenerator:
    """
    Walks the AST (after semantic analysis) and emits TAC instructions.

    Usage
    -----
        gen = TACGenerator()
        tac = gen.generate(program_node)
        print(tac)
    """

    def __init__(self):
        self._program   = TACProgram()
        self._tmp_count = 0
        self._lbl_count = 0

    # ──────────────────────────── public API ─────────────────────────────────

    def generate(self, node: Program) -> TACProgram:
        self._gen_stmt_list(node.statements)
        return self._program

    # ──────────────────────────── helpers ────────────────────────────────────

    def _new_tmp(self) -> str:
        self._tmp_count += 1
        return f"_t{self._tmp_count}"

    def _new_label(self, hint: str = "L") -> str:
        self._lbl_count += 1
        return f"{hint}_{self._lbl_count}"

    def _emit(self, instr: TACInstruction):
        self._program.emit(instr)

    # ──────────────────────────── statement generation ───────────────────────

    def _gen_stmt_list(self, stmts: List[ASTNode]):
        for stmt in stmts:
            self._gen_stmt(stmt)

    def _gen_stmt(self, node: ASTNode):
        if   isinstance(node, VarDecl):    self._gen_var_decl(node)
        elif isinstance(node, AssignStmt): self._gen_assign(node)
        elif isinstance(node, IfStmt):     self._gen_if(node)
        elif isinstance(node, WhileStmt):  self._gen_while(node)
        elif isinstance(node, ForStmt):    self._gen_for(node)
        elif isinstance(node, FuncDef):    self._gen_func_def(node)
        elif isinstance(node, ReturnStmt): self._gen_return(node)
        elif isinstance(node, PrintStmt):  self._gen_print(node)
        elif isinstance(node, ExprStmt):   self._gen_expr(node.expr)

    def _gen_var_decl(self, node: VarDecl):
        if node.init is not None:
            src = self._gen_expr(node.init)
            self._emit(TACCopy(node.name, src))
        else:
            # Default initialisation
            default = {"int": "0", "float": "0.0", "bool": "false", "string": '""'}
            self._emit(TACCopy(node.name, default.get(node.var_type, "0")))

    def _gen_assign(self, node: AssignStmt):
        src = self._gen_expr(node.value)
        self._emit(TACCopy(node.name, src))

    def _gen_if(self, node: IfStmt):
        cond = self._gen_expr(node.condition)
        else_label = self._new_label("else")
        end_label  = self._new_label("endif")

        self._emit(TACCondJumpFalse(cond, else_label))
        self._gen_stmt_list(node.then_body)

        if node.else_body:
            self._emit(TACGoto(end_label))
            self._emit(TACLabel(else_label))
            self._gen_stmt_list(node.else_body)
            self._emit(TACLabel(end_label))
        else:
            self._emit(TACLabel(else_label))

    def _gen_while(self, node: WhileStmt):
        start_label = self._new_label("while_start")
        end_label   = self._new_label("while_end")

        self._emit(TACLabel(start_label))
        cond = self._gen_expr(node.condition)
        self._emit(TACCondJumpFalse(cond, end_label))
        self._gen_stmt_list(node.body)
        self._emit(TACGoto(start_label))
        self._emit(TACLabel(end_label))

    def _gen_for(self, node: ForStmt):
        # Init
        self._gen_var_decl(node.init)

        start_label = self._new_label("for_start")
        end_label   = self._new_label("for_end")

        self._emit(TACLabel(start_label))
        cond = self._gen_expr(node.condition)
        self._emit(TACCondJumpFalse(cond, end_label))
        self._gen_stmt_list(node.body)
        self._gen_assign(node.update)
        self._emit(TACGoto(start_label))
        self._emit(TACLabel(end_label))

    def _gen_func_def(self, node: FuncDef):
        self._emit(TACFuncBegin(node.name))
        for pname, ptype in node.params:
            self._emit(TACFormalParam(pname, ptype))
        self._gen_stmt_list(node.body)
        self._emit(TACFuncEnd(node.name))

    def _gen_return(self, node: ReturnStmt):
        val = self._gen_expr(node.value)
        self._emit(TACReturn(val))

    def _gen_print(self, node: PrintStmt):
        val = self._gen_expr(node.value)
        self._emit(TACPrint(val))

    # ──────────────────────────── expression generation ──────────────────────

    def _gen_expr(self, node: ASTNode) -> str:
        """Generate TAC for an expression and return the name of its result."""

        if isinstance(node, IntLiteral):
            return str(node.value)

        if isinstance(node, FloatLiteral):
            return str(node.value)

        if isinstance(node, BoolLiteral):
            return "true" if node.value else "false"

        if isinstance(node, StringLiteral):
            return f'"{node.value}"'

        if isinstance(node, Identifier):
            return node.name

        if isinstance(node, BinaryExpr):
            return self._gen_binary(node)

        if isinstance(node, UnaryExpr):
            return self._gen_unary(node)

        if isinstance(node, CallExpr):
            return self._gen_call(node)

        raise RuntimeError(f"TACGenerator: unknown expr node {type(node).__name__}")

    def _gen_binary(self, node: BinaryExpr) -> str:
        left  = self._gen_expr(node.left)
        right = self._gen_expr(node.right)
        tmp   = self._new_tmp()
        self._emit(TACBinaryOp(tmp, node.operator, left, right))
        return tmp

    def _gen_unary(self, node: UnaryExpr) -> str:
        operand = self._gen_expr(node.operand)
        tmp     = self._new_tmp()
        self._emit(TACUnaryOp(tmp, node.operator, operand))
        return tmp

    def _gen_call(self, node: CallExpr) -> str:
        for arg in node.args:
            val = self._gen_expr(arg)
            self._emit(TACParam(val))
        tmp = self._new_tmp()
        self._emit(TACCall(tmp, node.callee, len(node.args)))
        return tmp
