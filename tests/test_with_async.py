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
    dpath = ub.ensure_app_cache_dir("mkinit/test/test_async/")
    ub.delete(dpath)
    ub.ensuredir(dpath)
    rel_paths = {
        "root": "mkint_test_async_pkg",
        "root_init": "mkint_test_async_pkg/__init__.py",
        "submod": "mkint_test_async_pkg/submod.py",
        "subpkg": "mkint_test_async_pkg/subpkg",
        "subpkg_init": "mkint_test_async_pkg/subpkg/__init__.py",
        "nested": "mkint_test_async_pkg/subpkg/nested.py",
    }
    paths = {key: join(dpath, path) for key, path in rel_paths.items()}

    for key, path in paths.items():
        if not path.endswith(".py"):
            ub.ensuredir(path)

    for key, path in paths.items():
        if path.endswith(".py"):
            ub.touch(path)

    with open(paths["submod"], "w") as file:
        file.write(
            ub.codeblock(
                """
            print('SUBMOD SIDE EFFECT')

            def submod_func():
                print('This is a submod func in {}'.format(__file__))

            async def async_foo1():
               result = 10
               return
            """
            )
        )

    with open(paths["nested"], "w") as file:
        file.write(
            ub.codeblock(
                """
            print('NESTED SIDE EFFECT')

            def nested_func():
                print('This is a nested func in {}'.format(__file__))

            async def async_foo2():
               result = 10
               return
            """
            )
        )
    return paths


def test_async():
    """
    """
    import mkinit
    import pytest

    paths = make_simple_dummy_package()
    pkg_path = paths["root"]

    mkinit.autogen_init(pkg_path, dry=False, recursive=True)
    paths["root_init"]
    paths["submod"]

    if LooseVersion("{}.{}".format(*sys.version_info[0:2])) < LooseVersion("3.7"):
        pytest.skip()

    dpath = dirname(paths["root"])
    with ub.util_import.PythonPathContext(dpath):
        import mkint_test_async_pkg
        mkint_test_async_pkg.__file__

        assert mkint_test_async_pkg.async_foo1 is not None
        print('mkint_test_async_pkg.async_foo1 = {!r}'.format(mkint_test_async_pkg.async_foo1))

        print("mkint_test_async_pkg = {!r}".format(mkint_test_async_pkg))

        mkint_test_async_pkg.nested_func()
        mkint_test_async_pkg.nested_func()

        mkint_test_async_pkg.submod_func()
        mkint_test_async_pkg.submod_func()

    # if 0:
    #     info = ub.cmd('tree ' + dpath, tee=1)
    #     info = ub.cmd('cat ' + paths['subpkg_init'], tee=1)
    #     info = ub.cmd('cat ' + paths['root_init'], tee=1)
