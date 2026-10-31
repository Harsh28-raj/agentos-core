import ast
import operator

from langchain_core.tools import tool

# Supported operators for our safe calculator
_allowed_operators = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

# Guards against expressions like 9**9**9 that would hang the worker
MAX_EXPONENT = 1000
MAX_MAGNITUDE = 10 ** 100


def _check(value):
    if isinstance(value, (int, float)) and abs(value) > MAX_MAGNITUDE:
        raise ValueError("Result is too large")
    return value


def _eval_ast(node):
    """Safely evaluate an AST node containing basic arithmetic."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise ValueError(f"Unsupported constant: {node.value!r}")
        return node.value
    if isinstance(node, ast.BinOp):
        op = type(node.op)
        if op not in _allowed_operators:
            raise ValueError(f"Unsupported operator: {op.__name__}")
        left, right = _eval_ast(node.left), _eval_ast(node.right)
        if op is ast.Pow and abs(right) > MAX_EXPONENT:
            raise ValueError(f"Exponent is too large (max {MAX_EXPONENT})")
        return _check(_allowed_operators[op](left, right))
    if isinstance(node, ast.UnaryOp):
        op = type(node.op)
        if op not in _allowed_operators:
            raise ValueError(f"Unsupported operator: {op.__name__}")
        return _allowed_operators[op](_eval_ast(node.operand))
    raise ValueError(f"Unsupported expression component: {type(node).__name__}")


@tool
def calculator_tool(expression: str) -> str:
    """
    Safely evaluates a mathematical expression.
    Supports basic arithmetic operators: +, -, *, /, //, **, %
    Example expressions: '4 * (3 + 2)', '100 / 3', '2 ** 8'
    """
    try:
        clean_expr = expression.strip()
        if not clean_expr:
            return "Error: Empty expression"
        result = _eval_ast(ast.parse(clean_expr, mode="eval").body)
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return f"Result: {result}"
    except SyntaxError:
        return f"Error: Invalid syntax in expression '{expression}'"
    except ZeroDivisionError:
        return "Error: Division by zero"
    except Exception as e:
        return f"Error: Failed to evaluate expression - {e}"
