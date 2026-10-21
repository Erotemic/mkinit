"""
Static analysis helpers for mkinit
"""

import ast
import os
from collections.abc import Iterator
from os.path import exists, isfile, join, splitext

from mkinit import _static_eval
from mkinit._static_eval import StaticValue, find_static_assignment
from mkinit.util import util_import

# Kept as a compatibility alias for existing private API consumers.
_parse_static_node_value = _static_eval.parse_static_node_value


def parse_static_value(
    key: str, source: str | None = None, fpath: str | None = None
) -> StaticValue:
    """
    Statically parse a constant variable's value from python code.

    TODO: This does not belong here. Move this to an external static analysis
    library.

    Args:
        key (str): name of the variable
        source (str | None): python text
        fpath (str | None): filepath to read if source is not specified

    Returns:
        StaticValue: a supported Python literal value

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
        assert fpath is not None
        with open(fpath, 'rb') as file_:
            source = file_.read().decode('utf-8')

    pt = ast.parse(source)

    found, value = find_static_assignment(pt, key, on_invalid='warn')
    if not found:
        raise NameError('No static variable named {!r}'.format(key))
    return value


def package_modpaths(
    pkgpath: str,
    with_pkg: bool = False,
    with_mod: bool = True,
    followlinks: bool = True,
    recursive: bool = True,
    with_libs: bool = False,
    check: bool = True,
) -> Iterator[str]:
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
        .. [SO1707709] https://stackoverflow.com/questions/1707709/list-modules-in-py-package

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
            root_path = join(pkgpath, '__init__.py')
            if not check or exists(root_path):
                yield root_path

        valid_exts = ['.py']
        if with_libs:
            valid_exts += util_import._platform_pylib_exts()

        for dpath, dnames, fnames in os.walk(pkgpath, followlinks=followlinks):
            ispkg = exists(join(dpath, '__init__.py'))
            if ispkg or not check:
                check = True  # always check subdirs
                if with_mod:
                    for fname in fnames:
                        if splitext(fname)[1] in valid_exts:
                            # dont yield inits. Handled in pkg loop.
                            if fname != '__init__.py':
                                path = join(dpath, fname)
                                yield path
                if with_pkg:
                    for dname in dnames:
                        path = join(dpath, dname, '__init__.py')
                        if exists(path):
                            yield path
            else:
                # Stop recursing when we are out of the package
                del dnames[:]
            if not recursive:
                break


def _locate_ps1_linenos(source_lines: list[str]) -> tuple[list[int], bool]:
    """
    Determines which lines in the source begin a "logical block" of code.

    Uses the starting line numbers on Python 3.10+ AST statements.

    Args:
        source_lines (List[str]): lines belonging only to the doctest src
            these will be unindented, prefixed, and without any want.

    Returns:
        Tuple[List, bool]:
            a list of indices indicating which lines are considered "PS1" and a
            flag indicating if the final line should be considered for a
            got/want assertion.

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
        '_._  = None' if p.startswith('#') else p for p in exec_source_lines
    ]

    source_block = '\n'.join(exec_source_lines)
    try:
        pt = ast.parse(source_block, filename='<source_block>')
    except SyntaxError as syn_ex:
        # Assign missing information to the syntax error.
        if syn_ex.text is None:
            source_parts = source_block.split('\n')
            if syn_ex.lineno is not None and 1 <= syn_ex.lineno <= len(
                source_parts
            ):
                syn_ex.text = source_parts[syn_ex.lineno - 1] + '\n'
        raise

    statement_nodes = pt.body
    # Python >= 3.10 reports the *start* of every statement, including
    # multiline strings. The old tokenize-based workaround for CPython issue
    # 16806 is no longer needed. Inspect each AST node once instead of
    # re-tokenizing progressively larger blocks of source.
    ps1_linenos = {node.lineno - 1 for node in statement_nodes}
    # Respect any line explicitly defined as PS2 (via its prefix)
    ps2_linenos = {x for x, p in enumerate(source_lines) if p[:4] != '>>> '}
    ps1_linenos = sorted(ps1_linenos.difference(ps2_linenos))

    # Only a final expression can produce an interactive result.
    eval_final = bool(statement_nodes) and isinstance(
        statement_nodes[-1], ast.Expr
    )
    return ps1_linenos, eval_final
