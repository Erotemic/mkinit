"""Contracts for shared literal evaluation and typed generation interfaces."""

import ast
from collections import OrderedDict

import pytest

from mkinit import dynamic_mkinit, static_analysis, static_mkinit
from mkinit._static_eval import find_static_assignment
from mkinit.formatting import _ensure_options, _initstr
from mkinit.util import util_import


@pytest.mark.parametrize(
    'expression, expected',
    [
        ('None', None),
        ('...', Ellipsis),
        ('False', False),
        ('1', 1),
        ("b'bytes'", b'bytes'),
        ("['a', ('b', None)]", ['a', ('b', None)]),
        (
            "{'b': [1], 'a': {'nested': (2, 3)}}",
            OrderedDict([('b', [1]), ('a', OrderedDict([('nested', (2, 3))]))]),
        ),
    ],
)
def test_restricted_literal_parser_shared_by_both_callers(expression, expected):
    node = ast.parse(expression, mode='eval').body
    first = static_analysis._parse_static_node_value(node)
    second = util_import._parse_static_node_value(node)
    assert first == expected
    assert second == expected
    assert type(first) is type(second)
    if isinstance(expected, dict):
        assert isinstance(first, OrderedDict)
        assert list(first) == list(expected)


@pytest.mark.parametrize(
    'expression', ['fun()', '1 + 2', '-2', '{1, 2}', "{'a': 1, **more}"]
)
def test_restricted_literal_parser_does_not_execute_or_expand_grammar(
    expression,
):
    node = ast.parse(expression, mode='eval').body
    for parser in (
        static_analysis._parse_static_node_value,
        util_import._parse_static_node_value,
    ):
        with pytest.raises(TypeError):
            parser(node)


def test_annotated_and_plain_assignments_agree(tmp_path):
    path = tmp_path / 'module.py'
    cases = (
        ('decl: object = None', 'decl', None),
        ("decl: list[str] = ['alpha', 'beta']", 'decl', ['alpha', 'beta']),
        ('decl = (1, 2, 3)', 'decl', (1, 2, 3)),
        ('decl = {"first": 1, "second": 2}', 'decl', {'first': 1, 'second': 2}),
        ('decl = 1\ndecl: int = 2', 'decl', 2),
        ('if True:\n    decl = 42', 'decl', 42),
    )
    for source, name, expected in cases:
        path.write_text(source)
        assert static_analysis.parse_static_value(name, source) == expected
        assert util_import._static_parse(name, path) == expected
        found, value = find_static_assignment(ast.parse(source), name)
        assert found and value == expected


def test_missing_and_invalid_assignments_preserve_api_errors(tmp_path):
    path = tmp_path / 'module.py'
    path.write_text('other = 1\n')
    with pytest.raises(NameError, match='No static variable'):
        static_analysis.parse_static_value('missing', path.read_text())
    with pytest.raises(AttributeError, match='Unknown missing'):
        util_import._static_parse('missing', path)

    path.write_text('target = 1\ntarget = missing_name\n')
    with pytest.warns(UserWarning, match='Cannot parse a static value'):
        assert (
            static_analysis.parse_static_value('target', path.read_text()) == 1
        )
    with pytest.raises(TypeError, match='Cannot parse a static value'):
        util_import._static_parse('target', path)

    path.write_text('target = missing_name\n')
    with pytest.warns(UserWarning, match='Cannot parse a static value'):
        with pytest.raises(NameError):
            static_analysis.parse_static_value('target', path.read_text())


def test_user_declarations_are_typed_and_alias_order_is_retained(tmp_path):
    pkg = tmp_path / 'pkg'
    pkg.mkdir()
    (pkg / '__init__.py').write_text(
        "__SUBMODULES__ = ['legacy']\n"
        "__submodules__: object = {'alpha': ['one'], 'beta': None}\n"
        "__extra_all__ = ['legacy_attr']\n"
        "__explicit__: list[str] = ['modern_attr']\n"
        "__external__ = ['pathlib']\n"
        "__private__ = ['_hidden*']\n"
        'class __module_properties__:\n'
        '    def sync(self):\n        return 1\n'
        '    async def async_method(self):\n        return 2\n'
    )
    with pytest.warns(DeprecationWarning):
        data = static_mkinit.parse_user_declarations(str(pkg))
    assert data['__submodules__'] == {'alpha': ['one'], 'beta': None}
    assert data['__explicit__'] == ['modern_attr']
    assert data['__external__'] == ['pathlib']
    assert data['__private__'] == ['_hidden*']
    assert data['module_property_names'] == ['sync', 'async_method']


def test_invalid_declarations_warn_without_becoming_unsafe_values(tmp_path):
    pkg = tmp_path / 'pkg'
    pkg.mkdir()
    (pkg / '__init__.py').write_text(
        "__explicit__ = 'not a list'\n"
        "__submodules__ = {'ok': ['name'], 3: []}\n"
    )
    with pytest.warns(UserWarning) as warnings:
        data = static_mkinit.parse_user_declarations(str(pkg))
    assert len(warnings) == 2
    assert data == {}


def test_format_options_are_resolved_without_mutating_input():
    partial = {'relative': True, 'lazy_import': True, 'source_order': True}
    resolved = _ensure_options(partial)
    assert partial == {
        'relative': True,
        'lazy_import': True,
        'source_order': True,
    }
    assert len(resolved) == 10
    assert resolved['with_attrs'] is True
    assert resolved['lazy_boilerplate'] is None
    assert resolved['relative'] is True
    assert resolved['source_order'] is True
    with pytest.raises(KeyError, match='bad key'):
        _ensure_options({'unsupported_key': True})


def test_static_and_dynamic_output_modes_remain_distinct():
    # Dynamic mode has a deliberately different header and import strategy;
    # keep its public generator behavior instead of routing it through the
    # static formatter's lazy-import logic.
    dynamic = dynamic_mkinit._make_initstr(
        'demo', ['alpha'], [('alpha', ['name'])], withheader=True
    )
    assert dynamic.startswith('# flake8: noqa\n')
    assert 'from demo import alpha' in dynamic
    assert 'from demo.alpha import (name,)' in dynamic

    regular = _initstr('demo', ['.alpha'], [('.alpha', ['name'])])
    assert 'from demo import alpha' in regular
    assert 'from demo.alpha import (name,)' in regular
    assert '__all__' in regular

    for options in (
        {
            'lazy_import': True,
            'lazy_boilerplate': 'from importlib import lazy_import',
        },
        {'lazy_loader': True},
    ):
        generated = _initstr(
            'demo', ['.alpha'], [('.alpha', ['name'])], options=options
        )
        assert '__getattr__' in generated
        assert '__all__' in generated
        ast.parse(generated)


def test_attribute_extraction_always_returns_a_list():
    assert static_mkinit._extract_attributes(source='x = 1') == ['x']
    assert static_mkinit._extract_attributes(source='__all__ = []') == []
    assert static_mkinit._extract_attributes(source="__all__ = ['z', 'a']") == [
        'z',
        'a',
    ]


def test_custom_lazy_boilerplate_is_preserved():
    options = {
        'lazy_import': True,
        'lazy_boilerplate': 'from custom import lazy_import',
    }
    generated = _initstr('demo', ['.alpha'], [], options=options)
    assert 'from custom import lazy_import' in generated
    assert '__getattr__' in generated


def test_syspath_search_accepts_pathlike_paths(tmp_path):
    site = tmp_path / 'site'
    pkg = site / 'namedpkg'
    pkg.mkdir(parents=True)
    (pkg / '__init__.py').write_text('')
    assert util_import._syspath_modname_to_modpath(
        'namedpkg', sys_path=[site]
    ) == str(pkg)
    assert (
        util_import._syspath_modname_to_modpath(
            'namedpkg', sys_path=[site], exclude=[site]
        )
        is None
    )


def test_setuptools_editable_finder_mapping(tmp_path):
    site = tmp_path / 'site'
    site.mkdir()
    pkg = tmp_path / 'source' / 'editpkg'
    pkg.mkdir(parents=True)
    (pkg / '__init__.py').write_text('')
    finder = site / '__editable___editpkg_1_finder.py'
    finder.write_text('MAPPING = ' + repr({'editpkg': str(pkg)}))
    assert util_import._syspath_modname_to_modpath(
        'editpkg', sys_path=[site]
    ) == str(pkg)
    assert (
        util_import._syspath_modname_to_modpath(
            'editpkg', sys_path=[site], exclude=[pkg.parent]
        )
        is None
    )
    finder.write_text("MAPPING = {'editpkg': None}")
    assert (
        util_import._syspath_modname_to_modpath('editpkg', sys_path=[site])
        is None
    )
