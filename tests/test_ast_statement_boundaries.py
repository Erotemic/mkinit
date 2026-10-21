"""Regressions for AST-based statement boundaries (Python 3.10+)."""

import ast
import sys

import pytest

from mkinit.formatting import _find_insert_points
from mkinit.static_analysis import _locate_ps1_linenos


@pytest.mark.parametrize(
    ('source_lines', 'expected'),
    [
        ([], ([], False)),
        (['>>> x = 1'], ([0], False)),
        (['>>> x + 1'], ([0], True)),
        (
            ['>>> x = (', '... 1,', '... 2)', '>>> x'],
            ([0, 3], True),
        ),
        (
            ['>>> """multiline', '... docstring', '... """', '>>> y = 5'],
            ([0, 3], False),
        ),
        (
            ['>>> # a comment', '>>> x = 1', '>>> # last comment'],
            ([0, 1, 2], False),
        ),
        (
            ['... x = 1', '>>> print(x)'],
            ([1], True),
        ),
        (
            ['>>> __version__ = f"""a{4}', '... b"""', '>>> y = 2'],
            ([0, 2], False),
        ),
        (
            ['>>> def f():', '...     return 1', '>>> f()'],
            ([0, 2], True),
        ),
    ],
)
def test_statement_starts_from_ast(source_lines, expected):
    assert _locate_ps1_linenos(source_lines) == expected


@pytest.mark.parametrize(
    ('lines', 'expected'),
    [
        (
            [
                '"""header',
                'more"""',
                '__version__ = (',
                '    "1.2.3",',
                ')',
                'trash = 1',
            ],
            (5, 6, ''),
        ),
        (
            ['from __future__ import (', '    annotations,', ')', 'junk = 1'],
            (3, 4, ''),
        ),
        (['# first', '# second', 'junk = 1'], (2, 3, '')),
        (
            ['__version__ = f"""v{1}', 'ok"""', 'junk = 1'],
            (2, 3, ''),
        ),
    ],
)
def test_insert_points_skip_complete_multiline_statements(lines, expected):
    assert _find_insert_points(lines) == expected


def test_ast_starts_match_multiline_literal_start():
    code = '"""\nlong\nmultiline\n"""\nvalue = 2\n'
    parsed = ast.parse(code)
    assert [stmt.lineno for stmt in parsed.body] == [1, 5]
    assert _locate_ps1_linenos(
        ['>>> ' + line for line in code.splitlines()]
    ) == ([0, 4], False)


@pytest.mark.skipif(
    sys.version_info < (3, 12), reason='PEP 701 requires Python 3.12'
)
def test_pep701_nested_fstring_quotes():
    # Valid since Python 3.12, whereas the previous vendored tokenizer
    # recognized an older subset of f-string syntax.
    lines = ['>>> version = f"{ {"x": 42}["x"] }"', '>>> other = 3']
    assert _locate_ps1_linenos(lines) == ([0, 1], False)


def test_incomplete_multiline_source_raises_syntax_error_not_index_error():
    with pytest.raises(SyntaxError):
        _locate_ps1_linenos(['>>> version = (', '... 1'])


@pytest.mark.parametrize(
    ('literal', 'expected'),
    [
        ('True', True),
        ('False', False),
        ('None', False),
        ('""', False),
        ('b"bytes"', True),
        ('3j', True),
        ('()', False),
        ('(1,)', True),
    ],
)
def test_modern_ast_constant_truthiness(literal, expected):
    from mkinit.top_level_ast import static_truthiness

    expression = ast.parse(literal, mode='eval').body
    assert static_truthiness(expression) is expected


def test_static_literal_parsers_use_modern_ast_constants():
    from mkinit.static_analysis import _parse_static_node_value as parse_static
    from mkinit.util.util_import import _parse_static_node_value as parse_import

    for literal in ('True', 'None', '3j', 'b"abc"', '[1, 2]', '(1, 2)'):
        node = ast.parse(literal, mode='eval').body
        assert parse_static(node) == parse_import(node)
