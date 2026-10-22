"""Regression tests for compatibility cleanup after raising Python minimum to 3.10."""

import importlib
import sys

from mkinit import dynamic_mkinit, static_mkinit
from mkinit.util.util_diff import difftext


def test_dynamic_imports_use_python3_absolute_imports(tmp_path, monkeypatch):
    """The Python 2 import path was dead; current submodules must still load."""
    name = 'mkinit_dynamic_python310_fixture'
    pkg = tmp_path / name
    pkg.mkdir()
    (pkg / '__init__.py').write_text('')
    (pkg / 'one.py').write_text('ONE = 1\n')
    (pkg / 'two.py').write_text('TWO = 2\n')
    monkeypatch.syspath_prepend(str(tmp_path))
    for suffix in ('', '.one', '.two'):
        monkeypatch.delitem(sys.modules, name + suffix, raising=False)

    module = importlib.import_module(name)
    dynamic_mkinit._excecute_imports(module, name, ['one', 'two'])
    assert module.one.ONE == 1
    assert module.two.TWO == 2

    for suffix in ('', '.one', '.two'):
        monkeypatch.delitem(sys.modules, name + suffix)


def test_generated_header_drops_obsolete_future_imports():
    header = dynamic_mkinit._make_module_header()
    assert header == '# flake8: noqa'
    result = dynamic_mkinit._make_initstr(
        'example_pkg', ['one'], [('one', ['name'])], withheader=True
    )
    assert result.startswith(header + '\n')
    assert 'from __future__ import' not in result
    assert 'from example_pkg import one' in result
    assert 'from example_pkg.one import (name,)' in result


def test_parse_user_declarations_still_honors_aliases(tmp_path):
    pkg = tmp_path / 'my_package'
    pkg.mkdir()
    assert static_mkinit.parse_user_declarations(str(pkg)) == {}
    (pkg / '__init__.py').write_text(
        "__SUBMODULES__ = ['legacy']\n"
        "__submodules__ = ['modern']\n"
        "__extra_all__ = ['legacy_attr']\n"
        "__explicit__ = ['modern_attr']\n"
        "__ignore__ = ['private_*']\n"
    )
    declarations = static_mkinit.parse_user_declarations(str(pkg))
    assert declarations['__submodules__'] == ['modern']
    assert declarations['__explicit__'] == ['modern_attr']
    assert declarations['__ignore__'] == ['private_*']


def test_difftext_context_filter_does_not_emit_disabled_break_markers():
    before = 'first\nsecond\nthird\nfourth\nfifth'
    after = 'first\n2nd\nthird\nfourth\n5th'
    output = difftext(before, after, context_lines=0)
    assert '- second' in output
    assert '+ 2nd' in output
    assert '- fifth' in output
    assert '+ 5th' in output
    assert 'FILTERED CONTEXT' not in output
