def main():
    from mkinit import static_mkinit
    # from os.path import exists, join, isdir
    import textwrap
    import os
    import six
    import argparse
    description = textwrap.dedent(
        '''
        discover and run doctests within a python package
        ''').strip('\n')

    parser = argparse.ArgumentParser(prog='python -m mkinit', description=description)
    parser.add_argument('modname_or_path', nargs='?', help='module or path to generate __init__.py for', default='.')
    parser.add_argument('--dry', action='store_true', default=False)

    parser.add_argument('--noattrs', action='store_true', default=False,
                        help='Do not generate attribute from imports')
    parser.add_argument('--nomods', action='store_true', default=False,
                        help='Do not generate modules imports')
    parser.add_argument('--noall', action='store_true', default=False,
                        help='Do not generate an __all__ variable')

    parser.add_argument('--relative', action='store_true', default=False,
                        help='Use relative . imports instead of <modname>')

    parser.add_argument('--ignore_all', action='store_true', default=False,
                        help='Ignores __all__ variables when parsing')

    args, unknown = parser.parse_known_args()
    ns = args.__dict__.copy()

    # modpath_or_name = sys.argv[1]
    print('ns = {!r}'.format(ns))
    modname_or_path = ns['modname_or_path']

    def touch(fpath):
        if six.PY2:  # nocover
            with open(fpath, 'a'):
                os.utime(fpath, None)
        else:
            flags = os.O_CREAT | os.O_APPEND
            with os.fdopen(os.open(fpath, flags=flags, mode=0o666)) as f:
                os.utime(f.fileno() if os.utime in os.supports_fd else fpath)

    # Hack in the ability to handle the case where __init__ does not exist yet
    # if isdir(modname_or_path) and not exists(join(modname_or_path, '__init__.py')):
    #     touch(join(modname_or_path, '__init__.py'))

    use_all = not ns['ignore_all']

    # Formatting options
    options = {
        'with_attrs': not ns['noattrs'],
        'with_mods': not ns['nomods'],
        'with_all': not ns['noall'],
        'relative': ns['relative'],
    }
    static_mkinit.autogen_init(modname_or_path, use_all=use_all,
                               options=options, dry=ns['dry'])

if __name__ == '__main__':
    main()
