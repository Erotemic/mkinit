# -*- coding: utf-8 -*-
# from collections import OrderedDict
from __future__ import absolute_import, division, print_function, unicode_literals
import ast
import six
from mkinit.orderedset import OrderedSet as oset


_UNHANDLED = None


def static_truthiness(node):
    """
    Extracts static truthiness of a node if possible

    Args:
        node (ast.Node)

    Returns:
        bool or None: True or False if a node can be statically bound to a
        truthy value, otherwise returns None.
    """
    if isinstance(node, ast.Str):
        return bool(node.s)
    elif isinstance(node, ast.Tuple):
        return bool(node.elts)
    elif isinstance(node, ast.Num):
        return bool(node.n)
    elif six.PY3 and isinstance(node, ast.Bytes):  # nocover
        return bool(node.s)
    elif six.PY3 and isinstance(node, ast.NameConstant):
        return bool(node.value)
    elif six.PY2 and isinstance(node, ast.Name):  # nocover
        constants_lookup = {
            'True': True,
            'False': False,
            'None': None,
        }
        try:
            return bool(constants_lookup[node.id])
        except KeyError:
            return _UNHANDLED
    else:
        return _UNHANDLED


def get_conditional_attrnames(nodes):
    """
    Gets attrnames within a list of nodes
    """
    sub_visitor = TopLevelVisitor()
    for node in nodes:
        # Check the attributes defined on this branch
        sub_visitor.visit(node)
    got_attrnames = sub_visitor.attrnames
    return got_attrnames


class TopLevelVisitor(ast.NodeVisitor):
    """
    Parses top-level attribute names

    References:
        # For other visit_<classname> values see
        http://greentreesnakes.readthedocs.io/en/latest/nodes.html

    CommandLine:
        python ~/code/mkinit/mkinit/top_level_ast.py TopLevelVisitor

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
        >>> print('attrnames = {!r}'.format(sorted(self.attrnames)))
        attrnames = ['Spam', 'bar', 'foo']

    Example:
        >>> from xdoctest import utils
        >>> source = utils.codeblock(
        ...    '''
        ...    a = True
        ...    if a:
        ...        b = True
        ...        c = True
        ...    else:
        ...        b = False
        ...    ''')
        >>> self = TopLevelVisitor.parse(source)
        >>> print('attrnames = {!r}'.format(sorted(self.attrnames)))
        attrnames = ['a', 'b']

    Example:
        >>> from xdoctest import utils
        >>> source = utils.codeblock(
        ...    '''
        ...    try:
        ...        d = True
        ...        e = True
        ...    except Exception:
        ...        d = False
        ...    ''')
        >>> self = TopLevelVisitor.parse(source)
        >>> print('attrnames = {!r}'.format(sorted(self.attrnames)))
    """
    def __init__(self):
        super(TopLevelVisitor, self).__init__()
        self.attrnames = oset()

    def _register(self, name):
        if isinstance(name, (list, tuple)):
            for n in name:
                self._register(n)
        else:
            if name not in self.attrnames:
                self.attrnames.append(name)

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
        self._register(node.name)

    def visit_ClassDef(self, node):
        self._register(node.name)

    def visit_Assign(self, node):
        for target in node.targets:
            if hasattr(target, 'id'):
                self._register(target.id)
        # TODO: assign constants to self.const_lookup?
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

        def check_condition_definitions(node, common=None):
            """
            Find definitions from conditionals that always accept or
            that are defined in all possible branches (note this requires an
            else statment)
            """
            has_elseif = len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If)
            has_else = node.orelse and not has_elseif

            # returns True if this branch will unconditionally accept, False,
            # if it will unconditionally reject, and None if it is uncertain.
            truth = static_truthiness(node.test)
            if truth is not _UNHANDLED:
                if truth:
                    # No need to check other conditionals
                    attrnames = get_conditional_attrnames(node.body)
                    return attrnames
            else:
                # Find the attrs in this branch and intersect them with common
                attrnames = oset(get_conditional_attrnames(node.body))
                if common is None:
                    common = attrnames
                else:
                    common = common.intersection(attrnames)

            if has_else:
                # If we get to an else, return the common attributes between
                # all non-rejecting branches
                else_attrs = oset(get_conditional_attrnames(node.orelse))
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
            self._register(list(common))

    def visit_TryExcept(self, node):
        """
        We only care about checking if (a) a variable is defined in the main
        body, and (b) that the variable is defined in all except blacks that
        **don't** immediately re-raise.
        """
        # TODO
        self.generic_visit(node)

    def visit_Del(self, node):
        # TODO
        self.generic_visit(node)

    # def visit_ExceptHandler(self, node):
    #     pass

    # def visit_TryFinally(self, node):
    #     pass

    # def visit_Try(self, node):
    #     TODO: parse a node only if it is visible in all cases
    #     pass
    #     # self.generic_visit(node)  # nocover


if __name__ == '__main__':
    """
    CommandLine:
        python -m mkinit.top_level_ast all
    """
    import xdoctest
    xdoctest.doctest_module(__file__)
