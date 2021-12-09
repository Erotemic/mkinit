# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import ast
import six
from ordered_set import OrderedSet as oset

__all__ = [
    "TopLevelVisitor",
]


_UNHANDLED = None


class TopLevelVisitor(ast.NodeVisitor):
    """
    Parses top-level attribute names

    References:
        # For other visit_<classname> values see
        http://greentreesnakes.readthedocs.io/en/latest/nodes.html

    CommandLine:
        python ~/code/mkinit/mkinit/top_level_ast.py TopLevelVisitor:1

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
        >>> # xdoctest: +REQUIRES(PY3)
        >>> from mkinit.top_level_ast import *  # NOQA
        >>> from xdoctest import utils
        >>> source = utils.codeblock(
        ...    '''
        ...    async def asyncfoo():
        ...        var = 1
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
        attrnames = ['Spam', 'asyncfoo', 'bar']

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
        ...    d = True
        ...    del d
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
        ...    except ImportError:
        ...        raise
        ...    except Exception:
        ...        d = False
        ...        f = False
        ...    else:
        ...        f = True
        ...    ''')
        >>> self = TopLevelVisitor.parse(source)
        >>> print('attrnames = {!r}'.format(sorted(self.attrnames)))
        attrnames = ['d', 'f']
    """

    def __init__(self):
        super(TopLevelVisitor, self).__init__()
        self.attrnames = oset()
        self.removed = oset()  # keep track of which variables were deleted

    def _register(self, name):
        if isinstance(name, (list, tuple, oset)):
            for n in name:
                self._register(n)
        else:
            if name not in self.attrnames:
                self.attrnames.add(name)
                self.removed.discard(name)

    def _unregister(self, name):
        if name in self.attrnames:
            self.attrnames.discard(name)
            self.removed.add(name)

    @classmethod
    def parse(TopLevelVisitor, source):
        self = TopLevelVisitor()

        if six.PY2:
            try:
                source_utf8 = source.encode("utf8")
                pt = ast.parse(source_utf8)
            except UnicodeDecodeError:
                pt = ast.parse(source)
        else:
            source_utf8 = source.encode("utf8")
            pt = ast.parse(source_utf8)

        self.visit(pt)
        return self

    # def visit(self, node):
    #     super(TopLevelVisitor, self).visit(node)

    def visit_FunctionDef(self, node):
        self._register(node.name)

    def visit_AsyncFunctionDef(self, node):
        self._register(node.name)

    def visit_ClassDef(self, node):
        self._register(node.name)

    def visit_Assign(self, node):
        for target in node.targets:
            if hasattr(target, "id"):
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
                if all(
                    [
                        isinstance(node.test.ops[0], ast.Eq),
                        node.test.left.id == "__name__",
                        node.test.comparators[0].s == "__main__",
                    ]
                ):
                    # Ignore main block
                    return
            except Exception:  # nocover
                pass

        # TODO: handled deleted attributes?
        # Find definitions from conditionals that always accept or
        # that are defined in all possible non-rejecting branches (note this
        # requires an else statment). A rejecting branch is one that is
        # unconditionally false or unconditionally raises an exception
        if_node, elif_nodes, else_body = unpack_if_nodes(node)
        test_nodes = [if_node] + elif_nodes

        has_unconditional = False
        required = []

        for item in test_nodes:
            truth = static_truthiness(item.test)
            # if any(isinstance(n, ast.Raise) for n in item.body):
            #     # Ignore branches that simply raise an error
            #     continue
            if truth is _UNHANDLED:
                names = get_conditional_attrnames(item.body)
                required.append(names)
            elif truth is True:
                # Branch is unconditionally true, no need to check others
                names = get_conditional_attrnames(item.body)
                required.append(names)
                has_unconditional = True
                break
            elif truth is False:
                # Ignore branches that are unconditionally false
                continue
            else:
                raise AssertionError("cannot happen")

        if not has_unconditional and else_body:
            # If we havent found an unconditional branch we need an else
            if not any(isinstance(n, ast.Raise) for n in else_body):
                # Ignore else branches that simply raise an error
                names = get_conditional_attrnames(else_body)
                required.append(names)
            has_unconditional = True

        if has_unconditional:
            # We can only gaurentee that something will exist if there is at
            # least one path that must be taken
            if len(required) == 0:
                common = oset()
            elif len(required) == 1:
                common = required[0]
            else:
                common = oset.intersection(*required)
                # common = set.intersection(*map(set, required))
            self._register(sorted(common))

    def visit_Try(self, node):
        """
        We only care about checking if (a) a variable is defined in the main
        body, and (b) that the variable is defined in all except blacks that
        **don't** immediately re-raise.
        """
        body_attrs = get_conditional_attrnames(node.body)

        orelse_attrs = get_conditional_attrnames(node.orelse)
        # body_attrs.extend(orelse_attrs)
        body_attrs.update(orelse_attrs)

        # Require that attributes are defined in all non-error branches
        required = []
        for handler in node.handlers:
            # Ignore any handlers that will always reraise
            if not any(isinstance(n, ast.Raise) for n in handler.body):
                handler_attrs = get_conditional_attrnames(handler.body)
                required.append(handler_attrs)

        if len(required) == 0:
            common = body_attrs
        else:
            common = oset.intersection(body_attrs, *required)
            # common = set.intersection(set(body_attrs), *map(set, required))
        self._register(sorted(common))

    # for python2
    visit_TryExcept = visit_Try

    def visit_Delete(self, node):
        for item in node.targets:
            if isinstance(item, ast.Name):
                self._unregister(item.id)
        self.generic_visit(node)


def unpack_if_nodes(if_node):
    """
    Extract chain of `<if><elif>*<else>?` statements
    """
    elif_nodes = []
    else_body = None

    curr = if_node
    while curr:
        if len(curr.orelse) == 1 and isinstance(curr.orelse[0], ast.If):
            # The current node is followed by an else-if statement
            elif_node = curr.orelse[0]
            elif_nodes.append(elif_node)
            curr = elif_node
        elif curr.orelse:
            # The current node is followed by an else statement
            else_body = curr.orelse
            curr = None
        else:
            curr = None

    return if_node, elif_nodes, else_body


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
            "True": True,
            "False": False,
            "None": None,
        }
        try:
            return bool(constants_lookup[node.id])
        except KeyError:
            return _UNHANDLED
    else:
        return _UNHANDLED


def get_conditional_attrnames(body):
    """
    Gets attrnames within a list of nodes
    """
    sub_visitor = TopLevelVisitor()
    for node in body:
        # Check the attributes defined on this branch
        sub_visitor.visit(node)
    return sub_visitor.attrnames


if __name__ == "__main__":
    """
    CommandLine:
        python -m mkinit.top_level_ast all
    """
    import xdoctest

    xdoctest.doctest_module(__file__)
