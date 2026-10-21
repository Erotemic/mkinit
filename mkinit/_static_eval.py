"""Shared, non-executing AST evaluation for mkinit's static import analysis.

This intentionally supports a *smaller* grammar than ``ast.literal_eval``.
Only constants, lists, tuples, and dictionaries were supported by mkinit's
legacy evaluators. Keeping that grammar avoids silently broadening what
user declarations or imported ``__all__`` assignments can contain.
"""

from __future__ import annotations

import ast
import warnings
from collections import OrderedDict
from types import EllipsisType
from typing import Literal, TypeAlias

StaticScalar: TypeAlias = (
    None | bool | int | float | complex | str | bytes | EllipsisType
)
StaticValue: TypeAlias = (
    StaticScalar
    | list['StaticValue']
    | tuple['StaticValue', ...]
    | OrderedDict[object, 'StaticValue']
)


def parse_static_node_value(node: ast.AST | None) -> StaticValue:
    """Parse the restricted mkinit literal grammar without executing source.

    Dictionary keys are returned in an ``OrderedDict`` for compatibility
    with the previous static parsers. ``None`` nodes, which represent ``**``
    dictionary unpacking, are deliberately rejected.
    """
    if node is None:
        raise TypeError('Cannot statically parse dictionary unpacking')
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.List):
        return [parse_static_node_value(item) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(parse_static_node_value(item) for item in node.elts)
    if isinstance(node, ast.Dict):
        result: OrderedDict[object, StaticValue] = OrderedDict()
        for key, value in zip(node.keys, node.values):
            result[parse_static_node_value(key)] = parse_static_node_value(
                value
            )
        return result
    raise TypeError(
        'Cannot parse a static value from non-static node of type: {!r}'.format(
            type(node)
        )
    )


def find_static_assignment(
    tree: ast.AST,
    name: str,
    *,
    on_invalid: Literal['raise', 'warn'] = 'raise',
) -> tuple[bool, StaticValue | None]:
    """Find a literal assignment, including annotated assignments.

    Return an explicit found flag: ``None`` is itself a valid literal value.
    The warning policy is used by ``static_analysis.parse_static_value``;
    ``util_import._static_parse`` keeps its historic strict exception policy.
    """

    class AssignmentVisitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.found = False
            self.value: StaticValue | None = None

        def _record(self, value: ast.expr) -> None:
            try:
                parsed = parse_static_node_value(value)
            except TypeError as ex:
                if on_invalid == 'raise':
                    raise
                warnings.warn(repr(ex))
            else:
                self.value = parsed
                self.found = True

        def visit_Assign(self, node: ast.Assign) -> None:
            if any(
                isinstance(target, ast.Name) and target.id == name
                for target in node.targets
            ):
                self._record(node.value)

        def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
            if (
                isinstance(node.target, ast.Name)
                and node.target.id == name
                and node.value is not None
            ):
                self._record(node.value)

    visitor = AssignmentVisitor()
    visitor.visit(tree)
    return visitor.found, visitor.value
