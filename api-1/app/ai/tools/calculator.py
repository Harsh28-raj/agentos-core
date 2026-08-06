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

def _eval_ast(node):
    """
    Safely evaluate an AST node containing basic arithmetic.
    """
    if isinstance(node, ast.Num):  # <number>
        return node.n
    elif isinstance(node, ast.Constant): # Python 3.8+ Constant
        return node.value
    elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
        op = type(node.op)
        if op not in _allowed_operators:
            raise ValueError(f"Unsupported operator: {op}")
        return _allowed_operators[op](_eval_ast(node.left), _eval_ast(node.right))
    elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
        op = type(node.op)
        if op not in _allowed_operators:
            raise ValueError(f"Unsupported operator: {op}")
        return _allowed_operators[op](_eval_ast(node.operand))
    else:
        raise ValueError(f"Unsupported expression component: {type(node)}")

@tool
def calculator_tool(expression: str) -> str:
    """
    Safely evaluates a mathematical expression.
    Supports basic arithmetic operators: +, -, *, /, //, **, %
    Example expressions: '4 * (3 + 2)', '100 / 3', '2 ** 8'
    """
    try:
        # Clean the string (remove spaces, etc., though ast.parse handles it)
        clean_expr = expression.strip()
        if not clean_expr:
            return "Error: Empty expression"

        # Parse the expression into an AST
        node = ast.parse(clean_expr, mode='eval').body
        
        # Evaluate the AST safely
        result = _eval_ast(node)
        
        # Format the result nicely
        if isinstance(result, float) and result.is_integer():
            result = int(result)
            
        return f"Result: {result}"
        
    except SyntaxError:
        return f"Error: Invalid syntax in expression '{expression}'"
    except ZeroDivisionError:
        return "Error: Division by zero"
    except Exception as e:
        return f"Error: Failed to evaluate expression - {str(e)}"
