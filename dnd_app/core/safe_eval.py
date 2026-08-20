"""
Safe arithmetic evaluation for data-driven formulas.

Replaces bare eval() for companion/statblock/resource formulas that only
need + - * / // % parentheses and integers/floats.

Author: Ethan O'Brien
Date: 2026-08-20
"""

from __future__ import annotations

import ast
import operator
from typing import Any

_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARYOPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


class UnsafeExpression(ValueError):
    """Raised when an expression uses disallowed syntax."""


def _eval_node(node: ast.AST) -> Any:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    # Python 3.9 may still emit Num in some edge cases
    if isinstance(node, ast.Num):  # type: ignore[attr-defined]
        return node.n
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARYOPS:
        return _UNARYOPS[type(node.op)](_eval_node(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return _BINOPS[type(node.op)](left, right)
    raise UnsafeExpression(f"Disallowed expression node: {type(node).__name__}")


def safe_eval_arith(expr: str) -> Any:
    """
    Evaluate a pure arithmetic expression string.

    Accepts digits, +, -, *, /, //, %, **, parentheses, and whitespace.
    Raises UnsafeExpression / SyntaxError / ZeroDivisionError on failure.
    """
    if not isinstance(expr, str):
        raise UnsafeExpression("Expression must be a string")
    cleaned = (
        expr.replace("\u00d7", "*")
        .replace("\u2212", "-")
        .replace("×", "*")
        .strip()
    )
    if not cleaned:
        raise UnsafeExpression("Empty expression")
    tree = ast.parse(cleaned, mode="eval")
    return _eval_node(tree)
