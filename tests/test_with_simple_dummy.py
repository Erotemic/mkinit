import ubelt as ub
from os.path import join
from os.path import dirname
import sys
from distutils.version import LooseVersion


def make_simple_dummy_package():
    """
    Creates a dummy package structure with or without __init__ files

    ANY EXISTING FILES ARE DELETED
    """
    # Fresh start
    dpath = ub.ensure_app_cache_dir('mkinit/test/simple_demo/')
    ub.delete(dpath)
    ub.ensuredir(dpath)
    rel_paths = {
        'root':        'mkinit_demo_pkg',
        'root_init':   'mkinit_demo_pkg/__init__.py',
        'submod':      'mkinit_demo_pkg/submod.py',
        'subpkg':      'mkinit_demo_pkg/subpkg',
        'subpkg_init': 'mkinit_demo_pkg/subpkg/__init__.py',
        'nested':      'mkinit_demo_pkg/subpkg/nested.py',
    }
    paths = {key: join(dpath, path) for key, path in rel_paths.items()}

    for key, path in paths.items():
        if not path.endswith('.py'):
            ub.ensuredir(path)

    for key, path in paths.items():
        if path.endswith('.py'):
            ub.touch(path)

    with open(paths['submod'], 'w') as file:
        file.write(ub.codeblock(
            '''
            print('SUBMOD SIDE EFFECT')

            def submod_func():
                print('This is a submod func in {}'.format(__file__))
            '''))

    with open(paths['nested'], 'w') as file:
        file.write(ub.codeblock(
            '''
            print('NESTED SIDE EFFECT')

            def nested_func():
                print('This is a nested func in {}'.format(__file__))
            '''))
    return paths


def test_simple_lazy_import():
    """
    xdoctest ~/code/mkinit/tests/test_with_simple_dummy.py test_simple_lazy_import
    """
    import mkinit
    import pytest
    paths = make_simple_dummy_package()
    pkg_path = paths['root']

    mkinit.autogen_init(pkg_path, options={'lazy_import': 1}, dry=False, recursive=True)

    if LooseVersion('{}.{}'.format(*sys.version_info[0:2])) < LooseVersion('3.7'):
        pytest.skip()

    dpath = dirname(paths['root'])
    with ub.util_import.PythonPathContext(dpath):
        import mkinit_demo_pkg
        print('mkinit_demo_pkg = {!r}'.format(mkinit_demo_pkg))

        mkinit_demo_pkg.nested_func()
        mkinit_demo_pkg.nested_func()

        mkinit_demo_pkg.submod_func()
        mkinit_demo_pkg.submod_func()

    if 1:
        info = ub.cmd('tree ' + dpath, tee=1)
        info = ub.cmd('cat ' + paths['subpkg_init'], tee=1)
        info = ub.cmd('cat ' + paths['root_init'], tee=1)
