def main():
    from mkinit import static_mkinit
    from xdoctest import utils
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
    static_mkinit.autogen_init(ns['modname'])

if __name__ == '__main__':
    main()
