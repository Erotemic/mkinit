"""Guard PR #67's no-functional-changes contract against its base behavior.

These tests intentionally preserve some permissive and surprising legacy
behaviors. Changing them requires a separate, explicitly approved PR.
"""

import ast
from collections import OrderedDict

import pytest

from mkinit import static_analysis, static_mkinit
from mkinit.formatting import _ensure_options, _initstr
from mkinit.top_level_ast import TopLevelVisitor
from mkinit.util import util_import
from mkinit.util.util_diff import difftext


def test_literal_declarations_do_not_acquire_new_runtime_constraints(tmp_path):
    pkg = tmp_path / 'pkg'
    pkg.mkdir()
    (pkg / '__init__.py').write_text(
        "__ignore__ = 'x'\n"
        "__explicit__ = ('alpha', 'beta')\n"
        "__protected__ = [None, 'private']\n"
        "__submodules__ = {'foo': ('x', 'y'), 42: None}\n"
    )
    decl = static_mkinit.parse_user_declarations(str(pkg))
    assert decl['__ignore__'] == 'x'
    assert decl['__explicit__'] == ('alpha', 'beta')
    assert decl['__protected__'] == [None, 'private']
    assert isinstance(decl['__submodules__'], OrderedDict)
    assert decl['__submodules__'] == {'foo': ('x', 'y'), 42: None}


def test_legacy_declaration_parser_does_not_activate_new_names(tmp_path):
    pkg = tmp_path / 'pkg'
    pkg.mkdir()
    (pkg / '__init__.py').write_text(
        "__external__ = ['pathlib']\n"
        "__explicit__: list[str] = ['annotated']\n"
        "__explicit__ = ('plain', 'tuple')\n"
        'class __module_properties__:\n'
        '    def first(self): pass\n'
        '    class Nested:\n'
        '        def nested(self): pass\n'
        '    def last(self): pass\n'
        '    async def async_method(self): pass\n'
    )
    decl = static_mkinit.parse_user_declarations(str(pkg))
    assert '__external__' not in decl
    assert decl['__explicit__'] == ('plain', 'tuple')
    assert decl['module_property_names'] == ['first']


@pytest.mark.parametrize(
    'declaration, expected',
    [
        ("__all__ = ('first', 'second')", ('first', 'second')),
        ("__all__ = 'item'", 'item'),
        ('__all__ = [1, 2]', [1, 2]),
        ("__all__ = ['first', 2]", ['first', 2]),
    ],
)
def test_existing_all_literals_are_returned_unchanged(declaration, expected):
    result = static_mkinit._extract_attributes(source=declaration + '\n')
    assert result == expected
    assert type(result) is type(expected)


def test_ignore_string_still_affects_generation_without_normalization(tmp_path):
    pkg = tmp_path / 'pkg'
    pkg.mkdir()
    (pkg / '__init__.py').write_text(
        "__submodules__ = {'foo': ['x']}\n__ignore__ = 'x'\n"
    )
    (pkg / 'foo.py').write_text('x = 1\n')
    generated = static_mkinit.static_init(pkg)
    assert 'from pkg import foo' in generated
    assert 'from pkg.foo import (x,)' not in generated
    assert "__all__ = ['foo']" in generated


def test_option_resolution_preserves_original_single_update_behavior():
    original = {'with_all': 1, 'with_mods': 0, 'lazy_import': 0}
    result = _ensure_options(original)  # type: ignore[invalid-argument-type]
    assert original == {'with_all': 1, 'with_mods': 0, 'lazy_import': 0}
    assert result['with_all'] == 1
    assert result['with_mods'] == 0
    assert result['lazy_import'] == 0
    with pytest.raises(KeyError, match='bad key'):
        _ensure_options({'invalid_option': 'value'})  # type: ignore[invalid-argument-type]


def test_original_empty_export_literals_are_byte_for_byte_preserved():
    generated = _initstr(
        'pkg',
        [],
        [],
        options={
            'lazy_import': True,
            'lazy_boilerplate': 'from somewhere import lazy_import',
        },
    )
    assert 'submodules={}' in generated
    assert 'submod_attrs={}' in generated
    assert 'submodules=set()' not in generated
    ast.parse(generated)


def test_shared_ast_parser_retains_distinct_error_side_effects(capsys):
    node = ast.parse('unresolved', mode='eval').body
    with pytest.raises(TypeError):
        util_import._parse_static_node_value(node)
    assert capsys.readouterr().out == ''
    with pytest.raises(TypeError):
        static_analysis._parse_static_node_value(node)
    assert "'id': 'unresolved'" in capsys.readouterr().out

    unpacked = ast.parse('{**unknown}', mode='eval').body
    with pytest.raises(TypeError):
        util_import._parse_static_node_value(unpacked)
    with pytest.raises(AttributeError, match='__dict__'):
        static_analysis._parse_static_node_value(unpacked)


def test_legacy_duplicate_assignment_warning_cardinality():
    with pytest.warns(UserWarning) as emitted:
        with pytest.raises(NameError, match='No static variable'):
            static_analysis.parse_static_value(
                'target', 'target = target = unknown'
            )
    assert len(emitted) == 2


def test_toplevel_register_does_not_expand_supported_inputs():
    visitor = TopLevelVisitor()
    visitor._register(['one', 'two'])
    visitor._register(('three',))
    assert list(visitor.attrnames) == ['one', 'two', 'three']
    with pytest.raises(TypeError):
        visitor._register({'unsupported'})  # type: ignore[invalid-argument-type]


def test_dormant_diff_visual_break_remains_dormant():
    before = '\n'.join(
        'unchanged' if i not in (1, 18) else 'old' for i in range(25)
    )
    after = '\n'.join(
        'unchanged' if i not in (1, 18) else 'new' for i in range(25)
    )
    rendered = difftext(before, after, context_lines=1, colored=False)
    assert 'FILTERED CONTEXT' not in rendered
    assert 'old' in rendered
    assert 'new' in rendered


def test_historic_scope_lookup_is_not_changed_by_typing_refactor():
    source = "__all__ = ['public']\ndef helper():\n    __all__ = ['nested']\n"
    assert static_analysis.parse_static_value('__all__', source) == ['nested']
