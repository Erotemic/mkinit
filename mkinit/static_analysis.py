# -*- coding: utf-8 -*-
"""
A paired down version of static_anslysis from xdoctest
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import os
import sys
import ast
import six
from collections import OrderedDict
from mkinit.util import util_import
from os.path import join, exists, splitext, isfile


def _parse_static_node_value(node):
    """
    Extract a constant value from an ast node if possible

    Args:
        node (ast.Node)

    Returns:
        object: static value of the node
    """
    if isinstance(node, ast.Num):
        value = node.n
    elif isinstance(node, ast.Str):
        value = node.s
    elif isinstance(node, ast.List):
        value = list(map(_parse_static_node_value, node.elts))
    elif isinstance(node, ast.Tuple):
        value = tuple(map(_parse_static_node_value, node.elts))
    elif isinstance(node, (ast.Dict)):
        keys = map(_parse_static_node_value, node.keys)
        values = map(_parse_static_node_value, node.values)
        value = OrderedDict(zip(keys, values))
        # value = dict(zip(keys, values))
    elif hasattr(ast, 'Constant') and isinstance(node, (ast.Constant)):
        # Constant added in 3.6?
        # https://bugs.python.org/issue26146
        value = node.value
    else:
        raise TypeError(
            "Cannot parse a static value from non-static node "
            "of type: {!r}".format(type(node))
        )
    return value


def parse_static_value(key, source=None, fpath=None):
    """
    Statically parse a constant variable's value from python code.

    TODO: This does not belong here. Move this to an external static analysis
    library.

    Args:
        key (str): name of the variable
        source (str): python text
        fpath (str): filepath to read if source is not specified

    Example:
        >>> key = 'foo'
        >>> source = 'foo = 123'
        >>> assert parse_static_value(key, source=source) == 123
        >>> source = 'foo = "123"'
        >>> assert parse_static_value(key, source=source) == '123'
        >>> source = 'foo = [1, 2, 3]'
        >>> assert parse_static_value(key, source=source) == [1, 2, 3]
        >>> source = 'foo = (1, 2, "3")'
        >>> assert parse_static_value(key, source=source) == (1, 2, "3")
        >>> source = 'foo = {1: 2, 3: 4}'
        >>> assert parse_static_value(key, source=source) == {1: 2, 3: 4}
        >>> #parse_static_value('bar', source=source)
        >>> #parse_static_value('bar', source='foo=1; bar = [1, foo]')
    """
    if source is None:  # pragma: no branch
        with open(fpath, "rb") as file_:
            source = file_.read().decode("utf-8")
    pt = ast.parse(source)

    class AssignentVisitor(ast.NodeVisitor):
        def visit_Assign(self, node):
            for target in node.targets:
                target_id = getattr(target, "id", None)
                if target_id == key:
                    try:
                        self.value = _parse_static_node_value(node.value)
                    except TypeError as ex:
                        import warnings
                        warnings.warn(repr(ex))

    sentinal = object()
    visitor = AssignentVisitor()
    visitor.value = sentinal
    visitor.visit(pt)
    if visitor.value is sentinal:
        raise NameError("No static variable named {!r}".format(key))
    return visitor.value


def package_modpaths(
    pkgpath,
    with_pkg=False,
    with_mod=True,
    followlinks=True,
    recursive=True,
    with_libs=False,
    check=True,
):
    r"""
    Finds sub-packages and sub-modules belonging to a package.

    Args:
        pkgpath (str): path to a module or package
        with_pkg (bool): if True includes package __init__ files (default =
            False)
        with_mod (bool): if True includes module files (default = True)
        exclude (list): ignores any module that matches any of these patterns
        recursive (bool): if False, then only child modules are included
        with_libs (bool): if True then compiled shared libs will be returned as well
        check (bool): if False, then then pkgpath is considered a module even
            if it does not contain an __init__ file.

    Yields:
        str: module names belonging to the package

    References:
        http://stackoverflow.com/questions/1707709/list-modules-in-py-package

    Example:
        >>> from mkinit.static_analysis import *
        >>> pkgpath = util_import.modname_to_modpath('mkinit')
        >>> paths = list(package_modpaths(pkgpath))
        >>> print('\n'.join(paths))
        >>> names = list(map(util_import.modpath_to_modname, paths))
        >>> assert 'mkinit.static_mkinit' in names
        >>> assert 'mkinit.__main__' in names
        >>> assert 'mkinit' not in names
        >>> print('\n'.join(names))
    """
    if isfile(pkgpath):
        # If input is a file, just return it
        yield pkgpath
    else:
        if with_pkg:
            root_path = join(pkgpath, "__init__.py")
            if not check or exists(root_path):
                yield root_path

        valid_exts = [".py"]
        if with_libs:
            valid_exts += util_import._platform_pylib_exts()

        for dpath, dnames, fnames in os.walk(pkgpath, followlinks=followlinks):
            ispkg = exists(join(dpath, "__init__.py"))
            if ispkg or not check:
                check = True  # always check subdirs
                if with_mod:
                    for fname in fnames:
                        if splitext(fname)[1] in valid_exts:
                            # dont yield inits. Handled in pkg loop.
                            if fname != "__init__.py":
                                path = join(dpath, fname)
                                yield path
                if with_pkg:
                    for dname in dnames:
                        path = join(dpath, dname, "__init__.py")
                        if exists(path):
                            yield path
            else:
                # Stop recursing when we are out of the package
                del dnames[:]
            if not recursive:
                break


def is_balanced_statement(lines):
    """
    Checks if the lines have balanced parens, brakets, curlies and strings

    Args:
        lines (list): list of strings

    Returns:
        bool: False if the statement is not balanced

    Doctest:
        >>> assert is_balanced_statement(['print(foobar)'])
        >>> assert is_balanced_statement(['foo = bar']) is True
        >>> assert is_balanced_statement(['foo = (']) is False
        >>> assert is_balanced_statement(['foo = (', "')(')"]) is True
        >>> assert is_balanced_statement(
        ...     ['foo = (', "'''", ")]'''", ')']) is True
        >>> #assert is_balanced_statement(['foo = ']) is False
        >>> #assert is_balanced_statement(['== ']) is False

    """
    from six.moves import cStringIO as StringIO
    import tokenize

    block = "\n".join(lines)
    if six.PY2:
        block = block.encode("utf8")
    stream = StringIO()
    stream.write(block)
    stream.seek(0)
    try:
        for t in tokenize.generate_tokens(stream.readline):
            pass
    except tokenize.TokenError as ex:
        message = ex.args[0]
        if message.startswith("EOF in multi-line"):
            return False
        raise
    else:
        # Note: trying to use ast.parse(block) will not work
        # here because it breaks in try, except, else
        return True


def _locate_ps1_linenos(source_lines):
    """
    Determines which lines in the source begin a "logical block" of code.

    Notes:
        implementation taken from xdoctest.parser

    Args:
        source_lines (list): lines belonging only to the doctest src
            these will be unindented, prefixed, and without any want.

    Returns:
        (list, bool): a list of indices indicating which lines
           are considered "PS1" and a flag indicating if the final line
           should be considered for a got/want assertion.

    Example:
        >>> source_lines = ['>>> def foo():', '>>>     return 0', '>>> 3']
        >>> linenos, eval_final = _locate_ps1_linenos(source_lines)
        >>> assert linenos == [0, 2]
        >>> assert eval_final is True

    Example:
        >>> source_lines = ['>>> x = [1, 2, ', '>>> 3, 4]', '>>> print(len(x))']
        >>> linenos, eval_final = _locate_ps1_linenos(source_lines)
        >>> assert linenos == [0, 2]
        >>> assert eval_final is True
    """
    # print('source_lines = {!r}'.format(source_lines))
    # Strip indentation (and PS1 / PS2 from source)
    exec_source_lines = [p[4:] for p in source_lines]

    # Hack to make comments appear like executable statements
    # note, this hack never leaves this function because we only are
    # returning line numbers.
    exec_source_lines = [
        "_._  = None" if p.startswith("#") else p for p in exec_source_lines
    ]

    source_block = "\n".join(exec_source_lines)
    try:
        pt = ast.parse(source_block, filename="<source_block>")
    except SyntaxError as syn_ex:
        # Assign missing information to the syntax error.
        if syn_ex.text is None:
            if syn_ex.lineno is not None:
                # Grab the line where the error occurs
                # (why is this not populated in SyntaxError by default?)
                # (because filename does not point to a valid loc)
                line = source_block.split("\n")[syn_ex.lineno - 1]
                syn_ex.text = line + "\n"
        raise syn_ex

    statement_nodes = pt.body
    ps1_linenos = [node.lineno - 1 for node in statement_nodes]
    NEED_16806_WORKAROUND = True
    if NEED_16806_WORKAROUND:  # pragma: nobranch
        ps1_linenos = _workaround_16806(ps1_linenos, exec_source_lines)
    # Respect any line explicitly defined as PS2 (via its prefix)
    ps2_linenos = {x for x, p in enumerate(source_lines) if p[:4] != ">>> "}
    ps1_linenos = sorted(ps1_linenos.difference(ps2_linenos))

    if len(statement_nodes) == 0:
        eval_final = False
    else:
        # Is the last statement evaluatable?
        if sys.version_info.major == 2:  # nocover
            eval_final = isinstance(statement_nodes[-1], (ast.Expr, ast.Print))
        else:
            # This should just be an Expr in python3
            # (todo: ensure this is true)
            eval_final = isinstance(statement_nodes[-1], ast.Expr)

    return ps1_linenos, eval_final


def _workaround_16806(ps1_linenos, exec_source_lines):
    """
    workaround for python issue 16806 (https://bugs.python.org/issue16806)

    Issue causes lineno for multiline strings to give the line they end on,
    not the line they start on.  A patch for this issue exists
    `https://github.com/python/cpython/pull/1800`

    Notes:
        Starting from the end look at consecutive pairs of indices to
        inspect the statment it corresponds to.  (the first statment goes
        from ps1_linenos[-1] to the end of the line list.

        Implementation taken from xdoctest.parser
    """
    new_ps1_lines = []
    b = len(exec_source_lines)
    for a in ps1_linenos[::-1]:
        # the position of `b` is correct, but `a` may be wrong
        # is_balanced_statement will be False iff `a` is wrong.
        while not is_balanced_statement(exec_source_lines[a:b]):
            # shift `a` down until it becomes correct
            a -= 1
        # push the new correct value back into the list
        new_ps1_lines.append(a)
        # set the end position of the next string to be `a` ,
        # note, because this `a` is correct, the next `b` is
        # must also be correct.
        b = a
    ps1_linenos = set(new_ps1_lines)
    return ps1_linenos


if __name__ == "__main__":
    """
    CommandLine:
        python -m mkinit.static_analysis all
    """
    import xdoctest

    xdoctest.doctest_module(__file__)
