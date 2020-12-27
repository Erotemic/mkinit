from xdoctest import utils
from mkinit.formatting import _find_insert_points


def test_explicit_insert_points():
    lines = utils.codeblock(
        """
        preserved1 = True
        if True:
            # <AUTOGEN_INIT>
            clobbered2 = True
            # </AUTOGEN_INIT>
        preserved3 = True
        """
    ).split("\n")
    start, end, indent = _find_insert_points(lines)
    assert (start, end, indent) == (3, 4, "    ")


def test_implicit_version_insert_points():
    lines = utils.codeblock(
        """
        preserved1 = True
        __version__ = '1.0'
        clobbered2 = True
        """
    ).split("\n")
    start, end, indent = _find_insert_points(lines)
    assert (start, end, indent) == (2, 3, "")

    lines = ['__version__ = "0.0.1"']
    start, end, indent = _find_insert_points(lines)
    assert (start, end, indent) == (1, 1, "")


def test_implicit_future_insert_points():
    lines = utils.codeblock(
        """
        from __future__ import (
            absolute_import, division, print_function,
            unicode_literals)
        clobbered2 = True
        clobbered3 = True
        """
    ).split("\n")
    start, end, indent = _find_insert_points(lines)
    assert (start, end, indent) == (3, 5, "")


def test_implicit_multiline_comment_insert_points():
    lines = utils.codeblock(
        """
        foo = \'\'\'
        \'\'\'
        bar = 1
        \'\'\' baz =
        biz \'\'\'  # comment
        """
    ).split("\n")
    start, end, indent = _find_insert_points(lines)
    assert (start, end, indent) == (5, 5, "")
    lines += ["blah"]
    start, end, indent = _find_insert_points(lines)
    assert (start, end, indent) == (5, 6, "")
    lines += ["blah"]
    start, end, indent = _find_insert_points(lines)
    assert (start, end, indent) == (5, 7, "")


def test_empty_insert_points():
    start, end, indent = _find_insert_points(lines=[])
    assert (start, end, indent) == (0, 0, "")


def test_implicit_stacked_insert_points():
    lines = utils.codeblock(
        '''
        """
        Some multiline comment
        """
        __version__ = '1.0'
        clobbered2 = True
        '''
    ).split("\n")
    start, end, indent = _find_insert_points(lines)
    assert (start, end, indent) == (4, 5, "")
