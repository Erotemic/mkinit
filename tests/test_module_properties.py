
def test_module_properties():
    import ubelt as ub
    dpath = ub.Path.appdir('mkinit/tests/test_module_props').ensuredir()
    init_fpath = dpath / '__init__.py'
    init_text = ub.codeblock(
        '''
        class __module_properties__:
            my_attr = 3
            def my_method(self):
                 return 'my method'
            @staticmethod
            def my_staticmethod(self):
                 return 'my staticmethod'
            @classmethod
            def my_classmethod(cls):
                 return 'my classmethod'
            @property
            def my_property(self):
                 return 'my property'

        # foo
        ''')
    init_fpath.write_text(init_text)

    import mkinit
    fpath, text = mkinit.autogen_init(init_fpath, options={'lazy_import': True}, dry=True)
    print(text)
    assert 'my_property' in text
