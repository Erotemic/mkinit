# -*- coding: utf-8 -*-
"""
Dynamically generate the import exec
"""
from __future__ import absolute_import, division, print_function, unicode_literals
from os.path import dirname, join, exists
import sys
import multiprocessing
import textwrap


def dynamic_init(modname, submodules=None, dump=False, verbose=False):
    """
    MAIN ENTRY POINT

    Dynamically import listed util libraries and their attributes.
    Create reload_subs function.

    Using __import__ like this is typically not considered good style However,
    it is better than import * and this will generate the good file text that
    can be used when the module is 'frozen"

    Example:
        >>> # The easiest way to use this in your code is to add these lines
        >>> # to the module __init__ file
        >>> from mkinit import dynamic_init
        >>> execstr = dynamic_init('mkinit')
        >>> print(execstr)
        >>> exec(execstr)  # xdoc: +SKIP
    """
    if verbose:
        print("[MKINIT] Running Dynamic Imports for modname=%r " % modname)
    # Get the module that will be imported into
    try:
        module = sys.modules[modname]
    except Exception:
        module = __import__(modname)

    if submodules is None:
        pkgpath = dirname(module.__file__)
        submodules = _find_local_submodule_names(pkgpath)

    imports = submodules

    # Import the modules
    _excecute_imports(module, modname, imports, verbose=verbose)
    # If developing do explicit import stars
    from_imports = _execute_fromimport_star(module, modname, imports, verbose=verbose)

    # If requested: print what the __init__ module should look like
    dump_requested = (
        ("--dump-%s-init" % modname) in sys.argv
        or ("--print-%s-init" % modname) in sys.argv
    ) or dump
    overwrite_requested = ("--update-%s-init" % modname) in sys.argv
    if verbose:
        print("[MKINIT] Finished Dynamic Imports for modname=%r " % modname)

    initstr = _make_initstr(modname, imports, from_imports, withheader=False)

    if dump_requested:
        is_main_proc = multiprocessing.current_process().name == "MainProcess"
        if is_main_proc:
            _initstr = _make_initstr(modname, imports, from_imports)
            print(_indent(_initstr))
    # Overwrite the __init__.py file with new explicit imports
    if overwrite_requested:
        is_main_proc = multiprocessing.current_process().name == "MainProcess"
        if is_main_proc:
            modpath = module.__path__[0]
            _autogen_write(modpath, _indent(initstr))

    return initstr


def _indent(str_, indent="    "):
    return indent + str_.replace("\n", "\n" + indent)


def _excecute_imports(module, modname, imports, verbose=False):
    """ Module Imports """
    # level: -1 is a the Python2 import strategy
    # level:  0 is a the Python3 absolute import
    if verbose:
        print("[MKINIT] EXECUTING %d IMPORT TUPLES" % (len(imports),))
    level = 0
    for name in imports:
        if level == -1:
            tmp = __import__(name, globals(), locals(), fromlist=[], level=level)
        elif level == 0:
            # FIXME: should support unicode. Maybe just a python2 thing
            tmp = __import__(
                modname, globals(), locals(), fromlist=[str(name)], level=level
            )


def _execute_fromimport_star(
    module, modname, imports, check_not_imported=False, verbose=False
):
    """
    Effectively import * statements

    The dynamic_init must happen before any * imports otherwise it wont catch
    anything.
    """
    if verbose:
        print("[MKINIT] EXECUTE %d FROMIMPORT STAR TUPLES." % (len(imports),))
    from_imports = []
    # Explicitly ignore these special functions (usually stdlib functions)
    # FIXME: find a better way to do this
    ignoreset = set(
        [
            "print",
            "print_function",
            "absolute_import",
            "division",
            "zip",
            "map",
            "range",
            "list",
            "zip_longest",
            "filter",
            "filterfalse",
            "dirname",
            "realpath",
            "join",
            "exists",
            "normpath",
            "splitext",
            "expanduser",
            "relpath",
            "isabs",
            "commonprefix",
            "basename",
            "input",
            "reduce",
        ]
    )

    for name in imports:
        # absname = modname + '.' + name
        child_module = sys.modules[modname + "." + name]
        # Check if the variable already belongs to the module
        varset = set(vars(module)) if check_not_imported else set()
        fromset = set()  # set(fromlist) if fromlist is not None else set()

        def valid_attrname(attrname):
            """
            Guess if the attrname is valid based on its name
            """
            is_forced = attrname in fromset
            is_private = attrname.startswith("_")
            is_conflit = attrname in varset
            is_module = attrname in sys.modules  # Isn't fool proof (next step is)
            is_ignore = attrname in ignoreset
            is_valid = not any((is_ignore, is_private, is_conflit, is_module))
            return is_forced or is_valid

        if hasattr(child_module, "__all__"):
            from_imports.append((name, getattr(child_module, "__all__")))
            continue

        allattrs = dir(child_module)
        fromlist_ = [attrname for attrname in allattrs if valid_attrname(attrname)]
        valid_fromlist_ = []
        for attrname in fromlist_:
            attrval = getattr(child_module, attrname)
            try:
                # Disallow fromimport modules
                forced = attrname in fromset
                if not forced and getattr(attrval, "__name__") in sys.modules:
                    if verbose > 1:
                        print("[MKINIT] not importing: %r" % attrname)
                    continue
            except AttributeError:
                pass
            if verbose > 1:
                print("[MKINIT] %s is importing: %r" % (modname, attrname))
            valid_fromlist_.append(attrname)
            setattr(module, attrname, attrval)
        if verbose:
            print(
                "[MKINIT]     name=%r, len(valid_fromlist_)=%d"
                % (name, len(valid_fromlist_))
            )
        from_imports.append((name, valid_fromlist_))
    return from_imports


def _make_initstr(modname, imports, from_imports, withheader=True):
    """ Calls the other string makers """
    header = _make_module_header() if withheader else ""
    import_str = _make_imports_str(imports, modname)
    fromimport_str = _make_fromimport_str(from_imports, modname)
    initstr = "\n".join(
        [
            str_
            for str_ in [
                header,
                import_str,
                fromimport_str,
            ]
            if len(str_) > 0
        ]
    )
    return initstr


def _make_module_header():
    return "\n".join(
        [
            "# flake8:" + " noqa",  # the plus prevents it from triggering on this file
            "from __future__ import absolute_import, division, print_function, unicode_literals",
        ]
    )


def _make_imports_str(imports, rootmodname="."):
    imports_fmtstr = "from {rootmodname} import %s".format(rootmodname=rootmodname)
    return "\n".join([imports_fmtstr % (name,) for name in imports])


def _make_fromimport_str(from_imports, rootmodname="."):
    if rootmodname == ".":
        # dot is already taken care of in fmtstr
        rootmodname = ""

    def _pack_fromimport(tup):
        name, fromlist = tup[0], tup[1]
        from_module_str = "from {rootmodname}.{name} import (".format(
            rootmodname=rootmodname, name=name
        )
        newline_prefix = " " * len(from_module_str)
        if len(fromlist) > 0:
            rawstr = from_module_str + ", ".join(fromlist) + ",)"
        else:
            rawstr = ""

        # not sure why this isn't 76? >= maybe?
        packstr = "\n".join(
            textwrap.wrap(
                rawstr,
                break_long_words=False,
                width=79,
                initial_indent="",
                subsequent_indent=newline_prefix,
            )
        )
        return packstr

    from_str = "\n".join(map(_pack_fromimport, from_imports))
    return from_str


def _find_local_submodule_names(pkgpath):
    # Automatically find the imports if they are not specified
    from mkinit import static_mkinit

    import_paths = dict(static_mkinit._find_local_submodules(pkgpath))
    imports = list(import_paths.keys())
    return imports


def _autogen_write(modpath, initstr):
    """
    TODO:
        - [ ] : replace with code in mkinit/formatting.py
    """
    # Get path to init file so we can overwrite it
    init_fpath = join(modpath, "__init__.py")
    print("attempting to update: %r" % init_fpath)
    assert exists(init_fpath)
    new_lines = []
    editing = False
    updated = False
    with open(init_fpath, "r") as file_:
        lines = file_.readlines()
        for line in lines:
            if not editing:
                new_lines.append(line)
            if line.strip().startswith("# <AUTOGEN_INIT>"):
                new_lines.append("\n" + initstr + "\n    # </AUTOGEN_INIT>\n")
                editing = True
                updated = True
            if line.strip().startswith("# </AUTOGEN_INIT>"):
                editing = False
    if updated:
        print("writing updated file: %r" % init_fpath)
        new_text = "".join(new_lines)
        with open(init_fpath, "w") as file_:
            file_.write(new_text)
    else:
        print("no write hook for file: %r" % init_fpath)
