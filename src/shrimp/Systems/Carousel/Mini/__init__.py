import pprint

from ..Mini.grammar import grammar
from ..Mini.interpreter import MiniInterpreter, MiniVisitor

visitor = MiniVisitor()
interpreter = MiniInterpreter()


def parse_mini(code: str):
    """Parse the given code and return the AST."""
    raw_ast = grammar.parse(code)
    return visitor.visit(raw_ast)


def mini(code: str, print_ast: bool = False):
    """Parse and evaluate the given code."""
    ast = parse_mini(code)
    if print_ast:
        pprint.pp(ast)
    return interpreter.eval(ast)
