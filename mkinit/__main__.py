def main():
    """
    The mkinit CLI main
    """
    from mkinit import static_mkinit
    import textwrap
    import argparse
    import logging

    description = textwrap.dedent(
        """
        Autogenerate an `__init__.py` that exposes a top-level API.

        Behavior is modified depending on the existing content of the
        `__init__.py` file (subsequent runs of mkinit are idempotent).

        The following `__init__.py` variables modify autogeneration behavior:

            `__submodules__` (List[str] | Dict[str, List[str])) -
                Indicates the list of submodules to be introspected, if
                unspecified all submodules are introspected. Can be a list
                of submodule names, or a dictionary mapping each submodule name
                to a list of attribute names to expose. If the value is None,
                then all attributes are exposed (or __all__) is respected).

            `__external__` - Specify external modules to expose the attributes of.

            `__explicit__` - Add custom explicitly defined names to this, and
                they will be automatically added to the __all__ variable.

            `__protected__` -  Protected modules are exposed, but their attributes are not.

            `__private__` - Private modules and their attributes are not exposed.

            `__ignore__` - Tells mkinit to ignore particular attributes
        """
    ).strip("\n")

    parser = argparse.ArgumentParser(
        prog="python -m mkinit",
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "modname_or_path",
        nargs="?",
        help="module or path to generate __init__.py for",
        default=".",
    )

    parser.add_argument("--dry", dest="_dry_old", action="store_true", default=True)

    parser.add_argument(
        *("-i", "-w", "--write", "--inplace"),
        dest="dry",
        action="store_false",
        help="modify / write to the file inplace",
        default=True
    )

    parser.add_argument(
        "--diff",
        dest="diff",
        action="store_true",
        help="show the diff (forces dry mode)",
        default=False,
    )

    parser.add_argument(
        "--noattrs",
        dest="with_attrs",
        action="store_false",
        default=True,
        help="Do not generate attribute from imports",
    )
    parser.add_argument(
        "--nomods",
        dest="with_mods",
        action="store_false",
        default=True,
        help="Do not generate modules imports",
    )
    parser.add_argument(
        "--noall",
        dest="with_all",
        action="store_false",
        default=True,
        help="Do not generate an __all__ variable",
    )

    parser.add_argument(
        "--relative",
        action="store_true",
        default=False,
        help="Use relative . imports instead of <modname>",
    )

    parser.add_argument(
        "--lazy",
        action="store_true",
        default=False,
        help="Use lazy imports (Python >= 3.7 only!)",
    )

    parser.add_argument(
        "--black",
        action="store_true",
        default=False,
        help="Use black formatting (Python >= 3.6 only!)",
    )

    parser.add_argument(
        "--lazy_boilerplate",
        default=None,
        help="Code that defines a custom lazy_import callable",
    )

    parser.add_argument(
        "--recursive",
        dest="recursive",
        action="store_true",
        default=False,
        help="If specified, runs mkinit on all subpackages in a package",
    )

    parser.add_argument(
        "--norespect_all",
        dest="respect_all",
        action="store_false",
        default=True,
        help="if False does not respect __all__ attributes of submodules when parsing",
    )

    parser.add_argument(
        "--verbose", nargs="?", default=0, type=int, help="Verbosity level"
    )

    parser.add_argument("--version", action="store_true", help="print version and exit")

    args, unknown = parser.parse_known_args()
    ns = args.__dict__.copy()

    if ns["version"]:
        import mkinit
        print(mkinit.__version__)
        return

    modname_or_path = ns["modname_or_path"]
    if ns["verbose"] is None:
        ns["verbose"] = 1

    respect_all = ns["respect_all"]
    verbose = ns["verbose"]
    dry = ns["dry"]

    # Formatting options
    options = {
        "with_attrs": ns["with_attrs"],
        "with_mods": ns["with_mods"],
        "with_all": ns["with_all"],
        "relative": ns["relative"],
        "lazy_import": ns["lazy"],
        "lazy_boilerplate": ns["lazy_boilerplate"],
        "use_black": ns["black"],
    }

    diff = ns["diff"]
    if diff:
        dry = True

    if verbose == 0:
        level = logging.WARNING
    elif verbose == 1:
        level = logging.INFO
    elif verbose >= 2:
        level = logging.DEBUG

    if verbose:
        print("verbose = {!r}".format(verbose))

    logging.basicConfig(
        format="%(levelname)s: %(message)s",
        level=level,
    )

    # print('ns = {!r}'.format(ns))
    static_mkinit.autogen_init(
        modname_or_path, respect_all=respect_all, options=options, dry=dry,
        diff=diff, recursive=ns['recursive'],
    )


if __name__ == "__main__":
    main()
