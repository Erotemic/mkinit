# -*- coding: utf-8 -*-
# from collections import OrderedDict
from __future__ import absolute_import, division, print_function, unicode_literals
import ast
import six


class TopLevelVisitor(ast.NodeVisitor):
    """
    Parses top-level attribute names

    References:
        # For other visit_<classname> values see
        http://greentreesnakes.readthedocs.io/en/latest/nodes.html

    Example:
        >>> from xdoctest import utils
        >>> source = utils.codeblock(
        ...    '''
        ...    def foo():
        ...        def subfunc():
        ...            pass
        ...    def bar():
        ...        pass
        ...    class Spam(object):
        ...        def eggs(self):
        ...            pass
        ...        @staticmethod
        ...        def hams():
        ...            pass
        ...    ''')
        >>> self = TopLevelVisitor.parse(source)
        >>> attrnames = set(self.attrnames)
        >>> assert attrnames == {'foo', 'bar', 'Spam'}
        >>> assert 'subfunc' not in self.attrnames
    """
    def __init__(self):
        super(TopLevelVisitor, self).__init__()
        self.attrnames = []

    @classmethod
    def parse(TopLevelVisitor, source):
        self = TopLevelVisitor()
        source_utf8 = source.encode('utf8')
        pt = ast.parse(source_utf8)

        self.visit(pt)
        return self

    # def visit(self, node):
    #     super(TopLevelVisitor, self).visit(node)

    def visit_FunctionDef(self, node):
        callname = node.name
        self.attrnames.append(callname)

    def visit_ClassDef(self, node):
        callname = node.name
        self.attrnames.append(callname)

    def visit_Assign(self, node):
        # print('VISIT FunctionDef node = %r' % (node,))
        # print('VISIT FunctionDef node = %r' % (node.__dict__,))
        for target in node.targets:
            if hasattr(target, 'id'):
                self.attrnames.append(target.id)
        # print('node.value = %r' % (node.value,))
        # TODO: assign constants to
        # self.const_lookup
        self.generic_visit(node)

    def visit_If(self, node):
        """
        Notes:
            elif clauses don't have a special representation in the AST, but
            rather appear as extra If nodes within the orelse section of the
            previous one.
        """
        if isinstance(node.test, ast.Compare):  # pragma: nobranch
            try:
                if all([
                    isinstance(node.test.ops[0], ast.Eq),
                    node.test.left.id == '__name__',
                    node.test.comparators[0].s == '__main__',
                ]):
                    # Ignore main block
                    return
            except Exception:  # nocover
                pass

        unhandled = object()

        def static_truthiness(item):
            if isinstance(item, ast.Str):
                return bool(item.s)
            elif isinstance(item, ast.Tuple):
                return bool(item.elts)
            elif isinstance(item, ast.Num):
                return bool(item.n)
            elif six.PY2 and isinstance(item, ast.Bytes):  # nocover
                return bool(item.s)
            elif six.PY2 and isinstance(item, ast.Name):  # nocover
                constants_lookup = {
                    'True': True,
                    'False': False,
                    'None': None,
                }
                return constants_lookup.get(item.value, unhandled)
            elif six.PY3 and isinstance(item, ast.NameConstant):
                return item.value
            else:
                return unhandled

        def get_conditional_attrnames(nodes):
            # Save state
            orig_callnames = self.attrnames
            self.attrnames = []
            for node in nodes:
                # Check the attributes defined on this branch
                self.visit(node)
            got_attrnames = self.attrnames
            # Restore state
            self.attrnames = orig_callnames
            return got_attrnames

        def check_condition_definitions(node, common=None):
            """
            Find definitions from conditionals that always accept or
            that are defined in all possible branches (note this requires an
            else statment)
            """
            try:
                import ubelt as ub
                set_ = ub.oset
            except ImportError:
                set_ = set
            has_elseif = len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If)
            has_else = node.orelse and not has_elseif

            # returns True if this branch will unconditionally accept, False,
            # if it will unconditionally reject, and None if it is uncertain.
            truth = static_truthiness(node.test)
            if truth is not unhandled:
                if truth:
                    # No need to check other conditionals
                    attrnames = get_conditional_attrnames(node.body)
                    return attrnames
            else:
                # Find the attrs in this branch and intersect them with common
                attrnames = set_(get_conditional_attrnames(node.body))
                if common is None:
                    common = attrnames
                else:
                    common = common.intersection(attrnames)

            if has_else:
                # If we get to an else, return the common attributes between
                # all non-rejecting branches
                else_attrs = set_(get_conditional_attrnames(node.orelse))
                if common is None:
                    common = else_attrs
                else:
                    common = common.intersection(else_attrs)
                return common

            if has_elseif:
                # Recurse
                elif_node = node.orelse[0]
                return check_condition_definitions(elif_node, common)

        # FIXME: will not handled deleted attributes
        common = check_condition_definitions(node)
        if common:
            self.attrnames.extend(list(common))

    # def visit_ExceptHandler(self, node):
    #     pass

    # def visit_TryFinally(self, node):
    #     pass

    # def visit_TryExcept(self, node):
    #     pass

    # def visit_Try(self, node):
    #     TODO: parse a node only if it is visible in all cases
    #     pass
    #     # self.generic_visit(node)  # nocover
