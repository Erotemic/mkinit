"""
Tests run on a dummy package
"""
import ubelt as ub
import sys
import os
from os.path import join
from os.path import dirname
import pytest
try:
    from packaging.version import parse as LooseVersion
except ImportError:
    from distutils.version import LooseVersion


def make_dummy_package(dpath, pkgname="mkinit_dummy_module", side_effects=0):
    """
    Creates a dummy package structure with or without __init__ files

    ANY EXISTING FILES ARE DELETED
    """
    root = ub.ensuredir(join(dpath, pkgname))
    ub.delete(root)
    ub.ensuredir(root)
    paths = {
        "root": root,
        "submod1": ub.touch(join(root, "submod1.py")),
        "submod2": ub.touch(join(root, "submod2.py")),
        "subdir1": ub.ensuredir(join(root, "subdir1")),
        "subdir2": ub.ensuredir(join(root, "subdir2")),
        "longsubdir": ub.ensuredir(
            join(root, "avery/long/subdir/that/goes/over80chars")
        ),
    }
    paths["subdir1_init"] = ub.touch(join(paths["subdir1"], "__init__.py"))
    paths["subdir2_init"] = ub.touch(join(paths["subdir2"], "__init__.py"))
    paths["root_init"] = ub.touch(join(paths["root"], "__init__.py"))
    paths["long_subdir_init"] = ub.touch(join(paths["longsubdir"], "__init__.py"))
    paths["long_submod"] = ub.touch(join(paths["longsubdir"], "long_submod.py"))

    ub.Path(paths["subdir1_init"]).write_text(
        ub.codeblock(
            """
        simple_subattr1 = "hello world"
        simple_subattr2 = "hello world"
        _private_attr = "hello world"
        """
        ),
    )

    ub.Path(paths["subdir2_init"]).write_text(
        ub.codeblock(
            """
        __all__ = ['public_attr']

        public_attr = "hello world"
        private_attr = "hello world"
        """
        ),
    )

    ub.Path(paths["submod1"]).write_text(
        ub.codeblock(
            """
        attr1 = True
        attr2 = zip

        # ------------------------

        if True:
            good_attr_01 = None

        if False:
            bad_attr_false1 = None

        if None:
            bad_attr_none1 = None

        # ------------------------

        if True:
            good_attr_02 = None
        else:
            bad_attr_true2 = None

        if False:
            bad_attr_false2 = None
        else:
            good_attr_03 = None

        if None:
            bad_attr_none2 = None
        else:
            good_attr_04 = None

        # ------------------------

        if True:
            good_attr_05 = None
        elif False:
            bad_attr3 = None
        else:
            bad_attr3 = None

        if False:
            bad_attr_elif_True3_0 = None
        elif True:
            good_attr_06 = None
        else:
            bad_attr_elif_True3_1 = None

        # ------------------------
        import sys

        if sys.version_info.major == 3:
            good_attr_07 = 'py3'
            bad_attr_uncommon4_1 = None
        else:
            good_attr_07 = 'py2'
            bad_attr_uncommon4_0 = None

        # ------------------------
        # This is static, so maybe another_val exists as a global
        if sys.version_info.major == good_attr_07:
            good_attr_08 = None
            bad_attr_uncommon5_1 = None
            bad_attr_uncommon5_0 = None
        elif sys:
            good_attr_08 = None
            bad_attr_uncommon5_1 = None
        else:
            good_attr_08 = None
            bad_attr_uncommon5_0 = None

        # ------------------------
        flag1 = sys.version_info.major < 10
        flag2 = sys.version_info.major > 10
        flag3 = sys.version_info.major > 10

        if flag1:
            bad_attr_num6 = 1
        elif flag2:
            bad_attr_num6 = 1
        elif flag3:
            bad_attr_num6 = 1

        if flag1:
            bad_attr_num6_0 = 1
        elif 0:
            bad_attr_num0 = 1
        elif 1:
            bad_attr_09 = 1
        else:
            bad_attr13 = 1

        if flag1:
            good_attr_09 = 1
        elif 1:
            good_attr_09 = 1
            bad_attr_09_1 = 1
        elif 2 == 3:
            pass

        # ------------------------

        if 'foobar':
            good_attr_10 = 1

        if False:
            bad_attr_str7 = 1
        elif (1, 2):
            good_attr_11 = 1
        elif True:
            bad_attr_true8 = 1

        # ------------------------

        if flag1 != flag2:
            good_attr_12 = None
        else:
            bad_attr_12 = None
            raise Exception

        # ------------------------

        try:
            good_attr_13 = None
            bad_attr_13 = None
        except Exception:
            good_attr_13 = None

        # ------------------------

        try:
            good_attr_14 = None
        except Exception:
            bad_attr_14 = None
            raise

        # ------------------------

        def func1():
            pass

        class class1():
            pass

        if __name__ == '__main__':
            bad_attr_main = None

        if __name__ == 'something_else':
            bad_something_else = None
        """
        ),
    )

    # Ensure that each submodule has an __init__
    # (do we need this with PEP 420 anymore?)
    root = paths["root"]
    from os.path import relpath, exists, dirname
    import os

    dpath = dirname(root)
    init_fpaths = set()
    for key, path in paths.items():
        relative = relpath(path, dpath)
        suffix = []
        parts = relative.split(os.sep)
        for part in parts:
            if "." not in part:
                suffix.append(part)
                middir = join(dpath, os.sep.join(suffix))
                fpath = join(middir, "__init__.py")
                init_fpaths.add(fpath)

    for fpath in init_fpaths:
        if not exists(fpath):
            ub.touch(fpath)

    ub.Path(paths["long_submod"]).write_text(
        ub.codeblock(
            """
        def a_very_nested_function():
            print('a_very_nested_function in {}'.format(__file__))
        def another_func1():
            pass
        def another_func2():
            pass
        def another_func3():
            pass
        def another_func4():
            pass
        """
        ),
    )

    if side_effects:
        with open(paths["long_submod"], "a") as file:
            file.write(
                ub.codeblock(
                    """
                print('NESTED SIDE EFFECT')
                """
                )
            )
    return paths


def check_dummy_root_init(text):
    for i in range(1, 15):
        want = "good_attr_{:02d}".format(i)
        assert want in text, "missing {}".format(want)
    assert "bad_attr" not in text
    assert "public_attr" in text
    assert "private_attr" not in text
    assert "simple_subattr1" in text
    assert "simple_subattr2" in text
    assert "_private_attr" not in text
    # print('ans = {!r}'.format(ans))


def test_static_import_without_init():
    """
    python ~/code/mkinit/tests/test_with_dummy.py test_static_import_without_init
    """
    import mkinit

    cache_dpath = ub.Path.appdir("mkinit/tests").ensuredir()
    paths = make_dummy_package(cache_dpath)
    ub.delete(paths["root_init"])

    text = mkinit.static_init(paths["long_subdir_init"])
    print(text)
    # check_dummy_root_init(text)

    modpath = paths["root"]
    text = mkinit.static_init(modpath)
    print(text)
    check_dummy_root_init(text)


def test_static_init():
    """
    python ~/code/mkinit/tests/test_with_dummy.py test_static_import_without_init
    """
    import mkinit

    cache_dpath = ub.Path.appdir("mkinit/tests").ensuredir()
    paths = make_dummy_package(cache_dpath)

    modpath = paths["root"]
    text = mkinit.static_init(modpath)
    check_dummy_root_init(text)


def test_static_find_locals():
    """
    python ~/code/mkinit/tests/test_with_dummy.py test_static_find_locals
    """
    import mkinit

    cache_dpath = ub.Path.appdir("mkinit/tests").ensuredir()
    paths = make_dummy_package(cache_dpath)
    ub.delete(paths["root_init"])
    modpath = paths["root"]
    imports = list(mkinit.static_mkinit._find_local_submodules(modpath))
    print("imports = {!r}".format(imports))


def test_dynamic_init():
    """
    python ~/code/mkinit/tests/test_with_dummy.py test_dynamic_init
    """
    import mkinit

    cache_dpath = ub.Path.appdir("mkinit/tests").ensuredir()
    paths = make_dummy_package(cache_dpath, "dynamic_dummy_mod1")
    module = ub.import_module_from_path(paths["root"])
    text = mkinit.dynamic_mkinit.dynamic_init(module.__name__)
    print(text)
    for i in range(1, 15):
        want = "good_attr_{:02d}".format(i)
        assert want in text, "missing {}".format(want)


@pytest.mark.parametrize(["option", "typed"], [
    ("lazy_import", False),
    ("lazy_loader", False),
    ("lazy_loader", True),
])
def test_lazy_import(option, typed):
    """
    python ~/code/mkinit/tests/test_with_dummy.py test_lazy_import
    """
    import pytest
    import mkinit

    if sys.version_info[0:2] < (3, 7):
        pytest.skip('Only 3.7+ has lazy imports')

    cache_dpath = ub.Path.appdir("mkinit/tests").ensuredir()
    paths = make_dummy_package(cache_dpath)

    pkg_path = paths["root"]
    mkinit.autogen_init(
        pkg_path,
        options={option: 1, "lazy_loader_typed": typed, "relative": typed},
        dry=False,
        recursive=True
    )

    if LooseVersion("{}.{}".format(*sys.version_info[0:2])) < LooseVersion("3.7"):
        pytest.skip()

    dpath = dirname(paths["root"])
    with ub.util_import.PythonPathContext(os.fspath(dpath)):
        import mkinit_dummy_module

        print("mkinit_dummy_module = {!r}".format(mkinit_dummy_module))
        print(dir(mkinit_dummy_module))
        print(
            "mkinit_dummy_module.a_very_nested_function = {!r}".format(
                mkinit_dummy_module.a_very_nested_function
            )
        )
        mkinit_dummy_module.a_very_nested_function()


@pytest.mark.parametrize(["option", "typed"], [
    ("lazy_import", False),
    ("lazy_loader", False),
    ("lazy_loader", True),
])
def test_recursive_lazy_autogen(option, typed):
    """
    xdoctest ~/code/mkinit/tests/test_with_dummy.py test_recursive_lazy_autogen
    """
    import mkinit
    import os

    if sys.version_info[0:2] < (3, 7):
        pytest.skip('Only 3.7+ has lazy imports')

    cache_dpath = ub.Path.appdir("mkinit/tests").ensuredir()
    paths = make_dummy_package(
        cache_dpath, pkgname="mkinit_rec_lazy_autogen", side_effects=True
    )
    pkg_path = paths["root"]

    mkinit.autogen_init(
        pkg_path,
        options={option: 1, "lazy_loader_typed": typed, "relative": typed},
        dry=False,
        recursive=True
    )

    if LooseVersion("{}.{}".format(*sys.version_info[0:2])) < LooseVersion("3.7"):
        pytest.skip()

    print(f'cache_dpath={cache_dpath}')
    with ub.util_import.PythonPathContext(os.fspath(cache_dpath)):
        print('sys.path = {}'.format(ub.urepr(sys.path, nl=1)))
        import mkinit_rec_lazy_autogen

        print("mkinit_rec_lazy_autogen = {!r}".format(mkinit_rec_lazy_autogen))
        print(
            "mkinit_rec_lazy_autogen.good_attr_01 = {!r}".format(
                mkinit_rec_lazy_autogen.good_attr_01
            )
        )
        print(
            "mkinit_rec_lazy_autogen.a_very_nested_function = {!r}".format(
                mkinit_rec_lazy_autogen.a_very_nested_function
            )
        )
        print(
            "mkinit_rec_lazy_autogen.a_very_nested_function = {!r}".format(
                mkinit_rec_lazy_autogen.a_very_nested_function
            )
        )
        print(
            "mkinit_rec_lazy_autogen.a_very_nested_function = {!r}".format(
                mkinit_rec_lazy_autogen.a_very_nested_function
            )
        )
        mkinit_rec_lazy_autogen.a_very_nested_function()

def test_typed_pyi_file():
    """
    xdoctest ~/code/mkinit/tests/test_with_dummy.py test_recursive_lazy_autogen
    """
    import mkinit
    import os

    if sys.version_info[0:2] < (3, 7):
        pytest.skip('Only 3.7+ has lazy imports')

    cache_dpath = ub.Path.appdir("mkinit/tests").ensuredir()
    paths = make_dummy_package(cache_dpath)
    pkg_path = paths["root"]

    mkinit.autogen_init(
        pkg_path,
        options={"lazy_loader": 1, "lazy_loader_typed": True, "relative": True},
        dry=False,
        recursive=True
    )
    if LooseVersion("{}.{}".format(*sys.version_info[0:2])) < LooseVersion("3.7"):
        pytest.skip()

    dpath = dirname(paths["root"])
    with ub.util_import.PythonPathContext(os.fspath(dpath)):
        import mkinit_dummy_module
        text = ub.Path(*mkinit_dummy_module.__path__, "__init__.pyi").read_text()
        assert "from . import avery" in text
        assert "from . import subdir1" in text
        assert "from .submod1 import (attr1, attr2" in text
        assert "__all__ = ['a_very_nested_function'" in text


def test_recursive_eager_autogen():
    """
    xdoctest ~/code/mkinit/tests/test_with_dummy.py test_recursive_eager_autogen
    """
    import mkinit

    cache_dpath = ub.Path.appdir("mkinit/tests").ensuredir()
    paths = make_dummy_package(
        cache_dpath, pkgname="mkinit_rec_eager_autogen", side_effects=True
    )
    pkg_path = paths["root"]

    mkinit.autogen_init(pkg_path, options={"lazy_import": 0}, dry=False, recursive=True)

    with ub.util_import.PythonPathContext(os.fspath(cache_dpath)):
        import mkinit_rec_eager_autogen

        print("mkinit_rec_eager_autogen = {!r}".format(mkinit_rec_eager_autogen))
        print("mkinit_rec_eager_autogen = {!r}".format(mkinit_rec_eager_autogen))
        print(
            "mkinit_rec_eager_autogen.good_attr_01 = {!r}".format(
                mkinit_rec_eager_autogen.good_attr_01
            )
        )
        print(
            "mkinit_rec_eager_autogen.a_very_nested_function = {!r}".format(
                mkinit_rec_eager_autogen.a_very_nested_function
            )
        )
        print(
            "mkinit_rec_eager_autogen.a_very_nested_function = {!r}".format(
                mkinit_rec_eager_autogen.a_very_nested_function
            )
        )
        print(
            "mkinit_rec_eager_autogen.a_very_nested_function = {!r}".format(
                mkinit_rec_eager_autogen.a_very_nested_function
            )
        )
        mkinit_rec_eager_autogen.a_very_nested_function()


def test_private_module_filtering():
    """Test that __private__ filters module imports, not just attributes."""
    import mkinit
    cache_dpath = ub.Path.appdir("mkinit/tests").ensuredir()
    root = ub.ensuredir(join(cache_dpath, "test_private_pkg"))
    ub.delete(root)
    ub.ensuredir(root)

    # Create modules
    ub.Path(join(root, "regular.py")).write_text("def func(): pass")
    ub.Path(join(root, "test_foo.py")).write_text("def test(): pass")
    ub.Path(join(root, "__init__.py")).write_text("__private__ = ['test_*']")

    text = mkinit.static_init(root)
    # Key test: module itself should be excluded, not just its attributes
    assert 'test_foo' not in text


if __name__ == "__main__":
    """
    CommandLine:
        python -B %HOME%/code/mkinit/tests/test_with_dummy.py all
    """
    import xdoctest

    xdoctest.doctest_module(__file__)
