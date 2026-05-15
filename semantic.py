"""
semantic.py — Symbol table construction and semantic analysis for MiniLang.

Checks:
  • Variable declared before use
  • No redeclaration in the same scope
  • Type compatibility for assignments and binary operations
  • Function parameter count / type checking on call sites
  • Return-type consistency
  • Boolean conditions in if / while / for
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple

from ast_nodes import (
    ASTNode, Program,
    VarDecl, AssignStmt, IfStmt, WhileStmt, ForStmt,
    FuncDef, ReturnStmt, PrintStmt, ExprStmt,
    BinaryExpr, UnaryExpr, CallExpr,
    Identifier, IntLiteral, FloatLiteral, BoolLiteral, StringLiteral,
)


# ─────────────────────────────── symbol table ────────────────────────────────

class Symbol:
    """An entry in the symbol table."""
    __slots__ = ("name", "sym_type", "scope_level", "line")

    def __init__(self, name: str, sym_type: str, scope_level: int, line: int):
        self.name        = name
        self.sym_type    = sym_type     # 'int' | 'float' | 'bool' | 'string' | 'func'
        self.scope_level = scope_level
        self.line        = line

    def __repr__(self) -> str:
        return f"Symbol({self.name!r}: {self.sym_type}, scope={self.scope_level})"


class FunctionSymbol(Symbol):
    """Extended symbol for function definitions."""
    __slots__ = ("param_types", "return_type")

    def __init__(self, name: str, param_types: List[str],
                 return_type: str, scope_level: int, line: int):
        super().__init__(name, "func", scope_level, line)
        self.param_types = param_types
        self.return_type = return_type


class SymbolTable:
    """
    Scoped symbol table implemented as a stack of dicts.
    Level 0 = global scope.
    """

    def __init__(self):
        self._scopes: List[Dict[str, Symbol]] = [{}]

    @property
    def current_level(self) -> int:
        return len(self._scopes) - 1

    def push_scope(self):
        self._scopes.append({})

    def pop_scope(self) -> Dict[str, Symbol]:
        return self._scopes.pop()

    def declare(self, symbol: Symbol) -> bool:
        """
        Add symbol to current scope.
        Returns False (duplicate) if name already exists in this scope.
        """
        scope = self._scopes[-1]
        if symbol.name in scope:
            return False
        scope[symbol.name] = symbol
        return True

    def lookup(self, name: str) -> Optional[Symbol]:
        """Search from inner-most to global scope."""
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        return None

    def dump(self) -> str:
        """Pretty-print every scope for debugging."""
        lines = []
        for level, scope in enumerate(self._scopes):
            lines.append(f"  Scope {level}:")
            if not scope:
                lines.append("    (empty)")
            for sym in scope.values():
                extra = ""
                if isinstance(sym, FunctionSymbol):
                    extra = (f" params={sym.param_types}"
                             f" returns={sym.return_type}")
                lines.append(f"    {sym.name}: {sym.sym_type}{extra}"
                             f"  (line {sym.line})")
        return "\n".join(lines)


# ─────────────────────────────── error type ──────────────────────────────────

class SemanticError:
    def __init__(self, message: str, line: int):
        self.message = message
        self.line    = line

    def __str__(self) -> str:
        return f"[SemanticError] Line {self.line}: {self.message}"


# ─────────────────────────────── type rules ──────────────────────────────────

# Numeric promotion: int op float → float
_NUMERIC = {"int", "float"}

def _numeric_result(t1: str, t2: str) -> Optional[str]:
    """Return the result type of an arithmetic op, or None if incompatible."""
    if t1 in _NUMERIC and t2 in _NUMERIC:
        return "float" if "float" in (t1, t2) else "int"
    return None

def _compatible_assign(declared: str, expr_type: str) -> bool:
    """Can *expr_type* be assigned to a variable of *declared* type?"""
    if declared == expr_type:
        return True
    # int → float widening
    if declared == "float" and expr_type == "int":
        return True
    return False


# ─────────────────────────────── analyser ────────────────────────────────────

class SemanticAnalyser:
    """
    Walks the AST, builds symbol table, infers expression types,
    and records all semantic errors.

    Usage
    -----
        sa = SemanticAnalyser()
        sa.analyse(program_node)
        if sa.errors: ...
        print(sa.symbol_table.dump())
    """

    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors: List[SemanticError] = []
        self._current_func_return: Optional[str] = None   # type expected by current func

    # ──────────────────────────── public API ─────────────────────────────────

    def analyse(self, node: Program):
        self._visit_stmt_list(node.statements)

    # ──────────────────────────── error helpers ───────────────────────────────

    def _err(self, msg: str, line: int):
        self.errors.append(SemanticError(msg, line))

    # ──────────────────────────── statement visitors ─────────────────────────

    def _visit_stmt_list(self, stmts: List[ASTNode]):
        for stmt in stmts:
            self._visit_stmt(stmt)

    def _visit_stmt(self, node: ASTNode):
        if   isinstance(node, VarDecl):    self._visit_var_decl(node)
        elif isinstance(node, AssignStmt): self._visit_assign(node)
        elif isinstance(node, IfStmt):     self._visit_if(node)
        elif isinstance(node, WhileStmt):  self._visit_while(node)
        elif isinstance(node, ForStmt):    self._visit_for(node)
        elif isinstance(node, FuncDef):    self._visit_func_def(node)
        elif isinstance(node, ReturnStmt): self._visit_return(node)
        elif isinstance(node, PrintStmt):  self._visit_print(node)
        elif isinstance(node, ExprStmt):   self._visit_expr(node.expr)
        else:
            self._err(f"Unknown statement node: {type(node).__name__}", 0)

    def _visit_var_decl(self, node: VarDecl):
        # Check initialiser first (may refer to outer-scope vars)
        init_type: Optional[str] = None
        if node.init is not None:
            init_type = self._visit_expr(node.init)
            if init_type and not _compatible_assign(node.var_type, init_type):
                self._err(
                    f"Cannot assign '{init_type}' to variable '{node.name}' "
                    f"of type '{node.var_type}'",
                    node.line,
                )

        sym = Symbol(node.name, node.var_type,
                     self.symbol_table.current_level, node.line)
        if not self.symbol_table.declare(sym):
            self._err(
                f"Variable '{node.name}' already declared in this scope",
                node.line,
            )

    def _visit_assign(self, node: AssignStmt):
        sym = self.symbol_table.lookup(node.name)
        if sym is None:
            self._err(f"Undefined variable '{node.name}'", node.line)
            self._visit_expr(node.value)
            return
        if isinstance(sym, FunctionSymbol):
            self._err(f"'{node.name}' is a function, cannot assign to it", node.line)
            return
        val_type = self._visit_expr(node.value)
        if val_type and not _compatible_assign(sym.sym_type, val_type):
            self._err(
                f"Type mismatch: cannot assign '{val_type}' to "
                f"'{node.name}' (type '{sym.sym_type}')",
                node.line,
            )

    def _visit_if(self, node: IfStmt):
        cond_type = self._visit_expr(node.condition)
        if cond_type and cond_type != "bool":
            self._err(
                f"If-condition must be 'bool', got '{cond_type}'", node.line
            )
        self.symbol_table.push_scope()
        self._visit_stmt_list(node.then_body)
        self.symbol_table.pop_scope()
        if node.else_body is not None:
            self.symbol_table.push_scope()
            self._visit_stmt_list(node.else_body)
            self.symbol_table.pop_scope()

    def _visit_while(self, node: WhileStmt):
        cond_type = self._visit_expr(node.condition)
        if cond_type and cond_type != "bool":
            self._err(
                f"While-condition must be 'bool', got '{cond_type}'", node.line
            )
        self.symbol_table.push_scope()
        self._visit_stmt_list(node.body)
        self.symbol_table.pop_scope()

    def _visit_for(self, node: ForStmt):
        self.symbol_table.push_scope()
        self._visit_var_decl(node.init)
        cond_type = self._visit_expr(node.condition)
        if cond_type and cond_type != "bool":
            self._err(
                f"For-condition must be 'bool', got '{cond_type}'", node.line
            )
        self._visit_assign(node.update)
        self._visit_stmt_list(node.body)
        self.symbol_table.pop_scope()

    def _visit_func_def(self, node: FuncDef):
        param_types = [pt for _, pt in node.params]
        fsym = FunctionSymbol(
            name=node.name,
            param_types=param_types,
            return_type=node.return_type,
            scope_level=self.symbol_table.current_level,
            line=node.line,
        )
        if not self.symbol_table.declare(fsym):
            self._err(
                f"Function '{node.name}' already declared in this scope",
                node.line,
            )

        self.symbol_table.push_scope()
        prev_return = self._current_func_return
        self._current_func_return = node.return_type

        for pname, ptype in node.params:
            psym = Symbol(pname, ptype,
                          self.symbol_table.current_level, node.line)
            if not self.symbol_table.declare(psym):
                self._err(
                    f"Duplicate parameter name '{pname}' in function '{node.name}'",
                    node.line,
                )

        self._visit_stmt_list(node.body)
        self._current_func_return = prev_return
        self.symbol_table.pop_scope()

    def _visit_return(self, node: ReturnStmt):
        ret_type = self._visit_expr(node.value)
        if self._current_func_return is None:
            self._err("'return' outside of a function", node.line)
            return
        if ret_type and not _compatible_assign(self._current_func_return, ret_type):
            self._err(
                f"Return type mismatch: function expects "
                f"'{self._current_func_return}', got '{ret_type}'",
                node.line,
            )

    def _visit_print(self, node: PrintStmt):
        self._visit_expr(node.value)   # any type is printable

    # ──────────────────────────── expression visitors ─────────────────────────

    def _visit_expr(self, node: ASTNode) -> Optional[str]:
        """Return the inferred type of *node*, or None on error."""
        if   isinstance(node, IntLiteral):     return "int"
        elif isinstance(node, FloatLiteral):   return "float"
        elif isinstance(node, BoolLiteral):    return "bool"
        elif isinstance(node, StringLiteral):  return "string"
        elif isinstance(node, Identifier):     return self._visit_identifier(node)
        elif isinstance(node, BinaryExpr):     return self._visit_binary(node)
        elif isinstance(node, UnaryExpr):      return self._visit_unary(node)
        elif isinstance(node, CallExpr):       return self._visit_call(node)
        else:
            self._err(f"Unknown expression node: {type(node).__name__}", 0)
            return None

    def _visit_identifier(self, node: Identifier) -> Optional[str]:
        sym = self.symbol_table.lookup(node.name)
        if sym is None:
            self._err(f"Undefined variable '{node.name}'", node.line)
            return None
        if isinstance(sym, FunctionSymbol):
            self._err(
                f"'{node.name}' is a function; expected a variable", node.line
            )
            return None
        return sym.sym_type

    def _visit_binary(self, node: BinaryExpr) -> Optional[str]:
        lt = self._visit_expr(node.left)
        rt = self._visit_expr(node.right)

        if lt is None or rt is None:
            return None

        op = node.operator

        # Arithmetic
        if op in ("+", "-", "*", "/", "%"):
            if op == "+" and lt == "string" and rt == "string":
                return "string"
            result = _numeric_result(lt, rt)
            if result is None:
                self._err(
                    f"Operator '{op}' not applicable to types "
                    f"'{lt}' and '{rt}'",
                    node.line,
                )
                return None
            return result

        # Relational
        if op in ("<", ">", "<=", ">="):
            if lt not in _NUMERIC or rt not in _NUMERIC:
                self._err(
                    f"Operator '{op}' requires numeric operands, "
                    f"got '{lt}' and '{rt}'",
                    node.line,
                )
                return None
            return "bool"

        # Equality
        if op in ("==", "!="):
            if lt != rt and not (lt in _NUMERIC and rt in _NUMERIC):
                self._err(
                    f"Cannot compare '{lt}' and '{rt}' with '{op}'",
                    node.line,
                )
                return None
            return "bool"

        # Logical
        if op in ("&&", "||"):
            if lt != "bool" or rt != "bool":
                self._err(
                    f"Operator '{op}' requires bool operands, "
                    f"got '{lt}' and '{rt}'",
                    node.line,
                )
                return None
            return "bool"

        self._err(f"Unknown binary operator '{op}'", node.line)
        return None

    def _visit_unary(self, node: UnaryExpr) -> Optional[str]:
        t = self._visit_expr(node.operand)
        if t is None:
            return None
        if node.operator == "-":
            if t not in _NUMERIC:
                self._err(
                    f"Unary '-' requires a numeric operand, got '{t}'",
                    node.line,
                )
                return None
            return t
        if node.operator == "!":
            if t != "bool":
                self._err(
                    f"Unary '!' requires a bool operand, got '{t}'",
                    node.line,
                )
                return None
            return "bool"
        self._err(f"Unknown unary operator '{node.operator}'", node.line)
        return None

    def _visit_call(self, node: CallExpr) -> Optional[str]:
        sym = self.symbol_table.lookup(node.callee)
        if sym is None:
            self._err(f"Undefined function '{node.callee}'", node.line)
            return None
        if not isinstance(sym, FunctionSymbol):
            self._err(f"'{node.callee}' is not a function", node.line)
            return None

        if len(node.args) != len(sym.param_types):
            self._err(
                f"Function '{node.callee}' expects "
                f"{len(sym.param_types)} argument(s), "
                f"got {len(node.args)}",
                node.line,
            )
            # still visit args for cascading errors
            for arg in node.args:
                self._visit_expr(arg)
            return sym.return_type

        for i, (arg, expected) in enumerate(
                zip(node.args, sym.param_types), start=1):
            arg_type = self._visit_expr(arg)
            if arg_type and not _compatible_assign(expected, arg_type):
                self._err(
                    f"Argument {i} of '{node.callee}': "
                    f"expected '{expected}', got '{arg_type}'",
                    node.line,
                )
        return sym.return_type
