#!/usr/bin/env python3
"""
A safe, expression-based command-line calculator.

Features:
  - Operators: + - * / // % ** and parentheses
  - Functions: sqrt, sin, cos, tan, asin, acos, atan, log, log10, log2,
               exp, abs, round, floor, ceil, factorial, radians, degrees
  - Constants: pi, e, tau
  - `ans` holds the previous result
  - Variable assignment: x = 5 * 3
  - Commands: help, vars, history, clear, quit

Expressions are parsed with `ast` and evaluated against a whitelist,
so there is no use of eval() on raw input.
"""

import ast
import math
import operator

BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

FUNCTIONS = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "log": math.log,
    "log10": math.log10,
    "log2": math.log2,
    "exp": math.exp,
    "abs": abs,
    "round": round,
    "floor": math.floor,
    "ceil": math.ceil,
    "factorial": math.factorial,
    "radians": math.radians,
    "degrees": math.degrees,
}

CONSTANTS = {"pi": math.pi, "e": math.e, "tau": math.tau}

MAX_EXPONENT = 10_000  # guard against huge computations like 9**9**9


class CalcError(Exception):
    """Raised for any user-facing calculation problem."""


class Calculator:
    def __init__(self):
        self.variables = dict(CONSTANTS)
        self.variables["ans"] = 0
        self.history = []

    # ---------- evaluation ----------
    def evaluate(self, expression: str):
        try:
            tree = ast.parse(expression, mode="eval")
        except SyntaxError:
            raise CalcError("Invalid syntax")
        return self._eval(tree.body)

    def _eval(self, node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise CalcError("Only numbers are allowed")

        if isinstance(node, ast.BinOp):
            op = BINARY_OPS.get(type(node.op))
            if op is None:
                raise CalcError("Unsupported operator")
            left, right = self._eval(node.left), self._eval(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > MAX_EXPONENT:
                raise CalcError("Exponent too large")
            try:
                return op(left, right)
            except ZeroDivisionError:
                raise CalcError("Division by zero")
            except OverflowError:
                raise CalcError("Result too large")

        if isinstance(node, ast.UnaryOp):
            op = UNARY_OPS.get(type(node.op))
            if op is None:
                raise CalcError("Unsupported operator")
            return op(self._eval(node.operand))

        if isinstance(node, ast.Name):
            if node.id in self.variables:
                return self.variables[node.id]
            raise CalcError(f"Unknown variable: {node.id}")

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in FUNCTIONS:
                name = getattr(node.func, "id", "?")
                raise CalcError(f"Unknown function: {name}")
            if node.keywords:
                raise CalcError("Keyword arguments are not supported")
            args = [self._eval(a) for a in node.args]
            try:
                return FUNCTIONS[node.func.id](*args)
            except (ValueError, TypeError) as exc:
                raise CalcError(f"{node.func.id}(): {exc}")
            except OverflowError:
                raise CalcError("Result too large")

        raise CalcError("Unsupported expression")

    # ---------- input handling ----------
    def process(self, line: str):
        """Handle one line: either `name = expr` or a plain expression."""
        target = None
        if "=" in line and "==" not in line:
            name, _, line = line.partition("=")
            target = name.strip()
            if not target.isidentifier():
                raise CalcError("Invalid variable name")
            if target in CONSTANTS or target in FUNCTIONS:
                raise CalcError(f"'{target}' is reserved")

        result = self.evaluate(line.strip())
        self.variables["ans"] = result
        if target:
            self.variables[target] = result
        self.history.append((line.strip(), result))
        return result


def fmt(value) -> str:
    if isinstance(value, float):
        if value.is_integer() and abs(value) < 1e15:
            return str(int(value))
        return f"{value:.10g}"
    return str(value)


HELP = """\
Operators : + - * / // % **   and ( )
Functions : sqrt sin cos tan asin acos atan log log10 log2 exp abs round
            floor ceil factorial radians degrees
Constants : pi e tau
Variables : ans (last result), or define your own:  x = 4 * 2.5
Commands  : help, vars, history, clear, quit
Examples  : sqrt(16) + 2**3     sin(radians(30))     log(100, 10)"""


def main():
    calc = Calculator()
    print("Python Calculator  (type 'help' for usage, 'quit' to exit)")

    while True:
        try:
            line = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line:
            continue

        cmd = line.lower()
        if cmd in {"quit", "exit", "q"}:
            break
        if cmd == "help":
            print(HELP)
            continue
        if cmd == "vars":
            for k, v in calc.variables.items():
                print(f"  {k} = {fmt(v)}")
            continue
        if cmd == "history":
            if not calc.history:
                print("  (empty)")
            for i, (expr, res) in enumerate(calc.history, 1):
                print(f"  {i}. {expr} = {fmt(res)}")
            continue
        if cmd == "clear":
            calc = Calculator()
            print("Cleared.")
            continue

        try:
            print(fmt(calc.process(line)))
        except CalcError as exc:
            print(f"Error: {exc}")


if __name__ == "__main__":
    main()