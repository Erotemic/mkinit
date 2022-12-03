import ast
from _typeshed import Incomplete


class TopLevelVisitor(ast.NodeVisitor):
    attrnames: Incomplete
    removed: Incomplete

    def __init__(self) -> None:
        ...

    @classmethod
    def parse(TopLevelVisitor, source):
        ...

    def visit_FunctionDef(self, node) -> None:
        ...

    def visit_AsyncFunctionDef(self, node) -> None:
        ...

    def visit_ClassDef(self, node) -> None:
        ...

    def visit_Assign(self, node) -> None:
        ...

    def visit_If(self, node) -> None:
        ...

    def visit_Try(self, node) -> None:
        ...

    visit_TryExcept: Incomplete

    def visit_Delete(self, node) -> None:
        ...


def unpack_if_nodes(if_node):
    ...


def static_truthiness(node):
    ...


def get_conditional_attrnames(body):
    ...
