from os.path import join


def make_dummy_package(dpath):
    """
    Creates a dummy package structure with or without __init__ files
    """
    import ubelt as ub
    root = ub.ensuredir(join(dpath, 'mkinit_dummy_module'))
    ub.delete(root)
    ub.ensuredir(root)
    paths = {
        'submod1': ub.touch(join(root, 'submod1.py')),
        'submod2': ub.touch(join(root, 'submod2.py')),
        'subdir1': ub.ensuredir(join(root, 'subdir1')),
        'subdir2': ub.ensuredir(join(root, 'subdir1')),
    }
    ub.writeto(paths['submod1'], ub.codeblock(
        '''
        import six

        attr1 = True
        attr2 = six.moves.zip

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
        import foobar
        # This is static, so maybe another_val exists as a global
        if foobar.someval == another_val:
            good_attr_08 = None
            bad_attr_uncommon5_1 = None
            bad_attr_uncommon5_0 = None
        elif foobar:
            good_attr_08 = None
            bad_attr_uncommon5_1 = None
        else:
            good_attr_08 = None
            bad_attr_uncommon5_0 = None

        # ------------------------

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
            good_attr_09 = 1
        else:
            bad_attr13 = 1

        # ------------------------

        if 'foobar':
            good_attr_10 = 1

        if not 'foobar':
            bad_attr_str7 = 1
        elif (1, 2):
            good_attr_11 = 1
        elif True:
            bad_attr_true8 = 1


        # ------------------------

        def func1():
            pass

        class class1():
            pass

        if __name__ == '__main__':
            bad_attr_main = None

        if __name__ == 'something_else':
            bad_something_else = None
        '''))
    paths['root'] = root
    return paths


def test_static_import_without_init():
    """
    python ~/code/mkinit/tests/test_static.py test_static_import_without_init
    """
    import ubelt as ub
    import mkinit
    cache_dpath = ub.ensure_app_cache_dir('mkinit/tests')
    paths = make_dummy_package(cache_dpath)
    modpath = paths['root']
    fpath, text = mkinit.autogen_init(modpath, dry=True)  # NOQA
    for i in range(1, 12):
        want = 'good_attr_{:02d}'.format(i)
        assert want in text
    assert 'bad_attr' not in text
    # print('ans = {!r}'.format(ans))


def test_static_find_locals():
    """
    python ~/code/mkinit/tests/test_static.py test_static_find_locals
    """
    import ubelt as ub
    import mkinit
    cache_dpath = ub.ensure_app_cache_dir('mkinit/tests')
    paths = make_dummy_package(cache_dpath)
    modpath = paths['root']
    imports = list(mkinit.static_mkinit._find_local_submodules(modpath))
    print('imports = {!r}'.format(imports))


if __name__ == '__main__':
    """
    CommandLine:
        python -B %HOME%/code/mkinit/tests/test_static.py all
    """
    import xdoctest
    xdoctest.doctest_module(__file__)
