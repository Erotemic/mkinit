def main():
    from mkinit import static_mkinit
    from xdoctest import utils
    from os.path import exists, join, isdir
    import os
    import six
    import argparse
    description = utils.codeblock(
        '''
        discover and run doctests within a python package
        ''')

    parser = argparse.ArgumentParser(prog='python -m xdoctest', description=description)
    parser.add_argument('modname', help='what files to run')
    args, unknown = parser.parse_known_args()
    ns = args.__dict__.copy()

    # modpath_or_name = sys.argv[1]
    print('ns = {!r}'.format(ns))
    modname = ns['modname']

    def touch(fpath):
        if six.PY2:  # nocover
            with open(fpath, 'a'):
                os.utime(fpath, None)
        else:
            flags = os.O_CREAT | os.O_APPEND
            with os.fdopen(os.open(fpath, flags=flags, mode=0o666)) as f:
                os.utime(f.fileno() if os.utime in os.supports_fd else fpath)

    # Hack in the ability to handle the case where __init__ does not exist yet
    if isdir(modname) and not exists(join(modname, '__init__.py')):
        touch(join(modname, '__init__.py'))

    static_mkinit.autogen_init(modname)

if __name__ == '__main__':
    main()
