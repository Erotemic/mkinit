"""Regression tests for the small standard-library export formatter."""

import ast

from mkinit.formatting import (
    _format_export_literal,
    _initstr,
    _make_lazy_boilerplate,
    _make_our_lazy_boilerplate,
)


def test_pretty_export_literals():
    assert _format_export_literal([]) == '[]'
    assert _format_export_literal({}) == '{}'
    assert _format_export_literal(['bar', 'baz']) == (
        "[\n    'bar',\n    'baz',\n]"
    )
    assert _format_export_literal({'bar': ['func1', 'func2']}) == (
        "{\n    'bar': [\n        'func1',\n        'func2',\n    ],\n}"
    )
    assert _format_export_literal({'empty': []}) == ("{\n    'empty': [],\n}")
    assert _format_export_literal(['bar', 'baz'], as_set=True) == (
        "{\n    'bar',\n    'baz',\n}"
    )
    assert _format_export_literal({'beta', 'alpha'}, multiline=False) == (
        "{'alpha', 'beta'}"
    )


def test_literals_retain_legacy_urepr_source_format():
    values = [
        [],
        ['alpha'],
        ['alpha', 'beta'],
        {'foo': ['alpha', 'beta'], 'bar': []},
        {},
        {'alpha', 'beta'},
    ]
    for value in values:
        rendered = _format_export_literal(value)
        assert ast.literal_eval(rendered) == value

    # Match the historical literal bytes, even where an empty set was
    # previously rendered using dict syntax by the source generator.
    assert _format_export_literal([], as_set=True) == '{}'
    assert _format_export_literal(set()) == '{}'


def test_generated_lazy_import_literals():
    options = {
        'lazy_import': True,
        'lazy_boilerplate': 'from importlib import lazy_import',
    }
    generated = _initstr(
        'sample',
        ['.bar', '.baz'],
        [('.bar', ['func1', 'func2'])],
        options=options,
    )
    assert "submodules={\n        'bar',\n        'baz',\n    }," in generated
    assert (
        "submod_attrs={\n        'bar': [\n            'func1',\n"
        "            'func2',\n        ],\n    },"
    ) in generated
    ast.parse(generated)

    # No generated-output changes are authorized in this cleanup PR.
    empty = _initstr('sample', [], [], options=options)
    assert 'submodules={}' in empty
    ast.parse(empty)


def test_lazy_loader_literals_and_module_properties():
    generated = _initstr(
        'sample',
        ['.bar'],
        [('.bar', ['func'])],
        options={'lazy_loader': True},
    )
    assert "submodules={\n        'bar',\n    }," in generated
    assert (
        "submod_attrs={\n        'bar': [\n            'func',\n" in generated
    )
    ast.parse(generated)

    boilerplate, code = _make_lazy_boilerplate(
        ['bar'],
        [('.bar', ['func'])],
        {'lazy_boilerplate': None},
        ['zeta', 'alpha', 'alpha'],
    )
    assert "module_property_names = {'alpha', 'zeta'}" in boilerplate
    assert 'submodules={' in code
    ast.parse(boilerplate + '\n' + code)

    empty_props = _make_our_lazy_boilerplate([])
    assert 'module_property_names = {}' in empty_props
