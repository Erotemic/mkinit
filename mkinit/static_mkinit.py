"""
Static version of :mod:`mkinit.dynamic_autogen`
"""
import os
from mkinit import static_analysis as static
from mkinit.util import util_import
from mkinit.util.util_diff import difftext
from mkinit.top_level_ast import TopLevelVisitor
from mkinit.formatting import _initstr, _insert_autogen_text, _ensure_options
from os.path import abspath
from os.path import exists
from os.path import join
from os.path import basename
from os.path import dirname
import logging
import fnmatch
import warnings


logger = logging.getLogger(__name__)


__all__ = [
    "autogen_init",
    "static_init",
]


def autogen_init(
    modpath_or_name,
    submodules=None,
    respect_all=True,
    options=None,
    dry=False,
    diff=False,
    recursive=False,
):
    """
    Autogenerates imports for a package __init__.py file.

    Args:
        modpath_or_name (PathLike | str):
            path to or name of a package module.  The path should reference the
            dirname not the __init__.py file.  If specified by name, must be
            findable from the PYTHONPATH.

        submodules (List[str] | None, default=None):
            if specified, then only these specific submodules are used in
            package generation. Otherwise, all non underscore prefixed modules
            are used.

        respect_all (bool, default=True):
            if False the `__all__` attribute is ignored while parsing.

        options (dict | None):
            formatting options; customizes how output is formatted.
            See `formatting._ensure_options` for defaults.

        dry (bool, default=False):
            if True, the autogenerated string is not written

        recursive (bool, default=False):
            if True, we will autogenerate init files for all subpackages.

    Notes:
        This will partially override the __init__ file. By default everything
        up to the last comment / __future__ import is preserved, and everything
        after is overriden.  For more fine grained control, you can specify
        XML-like `# <AUTOGEN_INIT>` and `# </AUTOGEN_INIT>` comments around the
        volitle area. If specified only the area between these tags will be
        overwritten.

        To autogenerate a module on demand, its useful to keep a doctr comment
        in the __init__ file like this:
            python -m mkinit <your_module>

    Example:
        >>> init_fpath, new_text = autogen_init('mkinit', submodules=None,
        >>>                                     respect_all=True,
        >>>                                     dry=True)
        >>> assert 'autogen_init' in new_text
    """
    logger.info(
        "Autogenerating __init__ for modpath_or_name={}".format(modpath_or_name)
    )
    options = _ensure_options(options)
    modpath = _rectify_to_modpath(modpath_or_name)

    if recursive:
        if submodules is not None:
            raise AssertionError("cannot specify submodules in recursive mode")
        all_init_fpaths = list(
            static.package_modpaths(modpath, with_pkg=True, with_mod=False)
        )
        all_init_fpaths = sorted(all_init_fpaths, key=lambda x: x.count(os.sep))
        for fpath in reversed(all_init_fpaths):
            if diff:
                # TODO: use a real diff patch format
                print('--- ' + str(fpath))
                print('+++ ' + str(fpath))
            autogen_init(
                fpath,
                submodules=None,
                respect_all=respect_all,
                options=options,
                dry=dry,
                diff=diff,
                recursive=False,
            )
        return

    if options["lazy_loader_typed"] and options["lazy_loader"]:
        autogen_init(
            modpath,
            submodules=None,
            respect_all=respect_all,
            options={**options, "lazy_loader": False},
            dry=dry,
            diff=diff,
            recursive=False,
        )

    initstr = static_init(
        modpath, submodules=submodules, respect_all=respect_all, options=options
    )
    init_fpath, new_text = _insert_autogen_text(
        modpath,
        initstr,
        interface=options["lazy_loader_typed"] and not options["lazy_loader"],
    )
    if dry:
        logger.info("(DRY) would write updated file: %r" % init_fpath)
        if diff:
            # Display difference
            try:
                with open(init_fpath, "r") as file:
                    old_text = file.read()
            except Exception:
                old_text = ""
            display_text = difftext(old_text, new_text, colored=True, context_lines=3)
            print(display_text)
        else:
            print(new_text)
        return init_fpath, new_text
    else:
        logger.info("writing updated file: %r" % init_fpath)
        # print(new_text)
        with open(init_fpath, "w") as file_:
            file_.write(new_text)


def _rectify_to_modpath(modpath_or_name):
    if exists(modpath_or_name):
        modpath = abspath(modpath_or_name)
    else:
        modpath = util_import.modname_to_modpath(modpath_or_name)
        if modpath is None:
            raise ValueError("Invalid module {}".format(modpath_or_name))
    if basename(modpath) == "__init__.py":
        modpath = dirname(modpath)
    return modpath


def static_init(modpath_or_name, submodules=None, respect_all=True, options=None):
    """
    Returns the autogenerated initialization string.  This can either be
    executed with `exec` or directly copied into the __init__.py file.
    """
    modpath = _rectify_to_modpath(modpath_or_name)

    user_decl = parse_user_declarations(modpath)
    logger.debug('user_decl = {}'.format(user_decl))
    if submodules is not None:
        user_decl["__submodules__"] = submodules

    submodules = user_decl.get("__submodules__", None)
    explicit = user_decl.get("__explicit__", [])
    private = user_decl.get("__private__", [])
    protected = user_decl.get("__protected__", [])
    external = user_decl.get("__external__", [])
    ignore = user_decl.get("__ignore__", [])

    PARSE_USER_TEXT_FOR_OTHER_NAMES = True
    if PARSE_USER_TEXT_FOR_OTHER_NAMES:
        from mkinit.formatting import _find_insert_points  # NOQA
        init_fpath = join(modpath, "__init__.py")
        if exists(init_fpath):
            with open(init_fpath, "r") as file_:
                lines = file_.readlines()
        else:
            lines = []
        startline, endline, init_indent = _find_insert_points(lines)
        user_text = ''.join(lines[:startline] + lines[endline:])

        try:
            user_attrs = _extract_attributes(source=user_text)
        except Exception:
            logger.error('Unable to parse user attributes')
            raise

        logger.debug('Updating explicit with variable names parsed from existing text: {}'.format(user_attrs))
        explicit.extend(user_attrs)

    modname, imports, from_imports = _static_parse_imports(
        modpath, submodules=submodules, respect_all=respect_all,
        external=external, ignore=ignore
    )

    logger.debug("Found {} imports".format(len(imports)))
    logger.debug("Found {} from_imports".format(len(from_imports)))
    logger.debug("modname={}".format(modname))

    initstr = _initstr(
        modname,
        imports,
        from_imports,
        options=options,
        explicit=explicit,
        protected=protected,
        private=private,
    )
    return initstr


def parse_user_declarations(modpath):
    """
    Statically determine special file-specific user options and declarations
    """
    # the __init__ file may have a variable describing the correct imports
    # should imports specify the name of this variable or should it always be
    # __submodules__?
    user_decl = {}

    init_fpath = join(modpath, "__init__.py")
    if exists(init_fpath):
        with open(init_fpath, "r") as file:
            source = file.read()
        try:
            # Include only these submodules
            user_decl["__submodules__"] = static.parse_static_value(
                "__submodules__", source
            )
        except NameError:
            try:
                user_decl["__submodules__"] = static.parse_static_value(
                    "__SUBMODULES__", source
                )
            except NameError:
                pass
            else:
                warnings.warn(
                    "Use __submodules__, __SUBMODULES__ is depricated",
                    DeprecationWarning,
                )

        try:
            user_decl["__explicit__"] = static.parse_static_value(
                "__extra_all__", source
            )
        except NameError:
            pass

        try:
            user_decl["__external__"] = static.parse_static_value(
                "__external__", source
            )
        except NameError:
            pass

        try:
            # Add custom explicitly defined names to this, and they will be
            # automatically added to the __all__ variable.
            user_decl["__explicit__"] = static.parse_static_value(
                "__explicit__", source
            )
        except NameError:
            pass

        try:
            # Protected items are exposed, but their attributes are not
            user_decl["__protected__"] = static.parse_static_value(
                "__protected__", source
            )
        except NameError:
            pass

        try:
            # Private items and their attributes are not exposed
            user_decl["__private__"] = static.parse_static_value("__private__", source)
        except NameError:
            pass

        try:
            # Ignore these modules and attributes
            user_decl["__ignore__"] = static.parse_static_value("__ignore__", source)
        except NameError:
            pass
    return user_decl


def _find_local_submodules(pkgpath):
    """
    Yields all children submodules in a package (non-recursively)

    Args:
        pkgpath (str): path to a package with an __init__.py file

    Example:
        >>> pkgpath = util_import.modname_to_modpath('mkinit')
        >>> import_paths = dict(_find_local_submodules(pkgpath))
        >>> print('import_paths = {!r}'.format(import_paths))
    """
    # Find all the children modules in this package (non recursive)
    pkgname = util_import.modpath_to_modname(pkgpath, check=False)
    if pkgname is None:
        raise Exception("cannot import {!r}".format(pkgpath))
    # TODO:
    # DOES THIS NEED A REWRITE TO HANDLE THE CASE WHEN __init__ does not exist?

    try:
        # Hack to grab the root package
        a, b = util_import.split_modpath(pkgpath, check=False)
        root_pkgpath = join(a, b.replace("\\", "/").split("/")[0])
    except ValueError:
        # Assume that the path is the root package if split_modpath fails
        root_pkgpath = pkgpath

    for sub_modpath in static.package_modpaths(
        pkgpath, with_pkg=True, recursive=False, check=False
    ):
        sub_modname = util_import.modpath_to_modname(
            sub_modpath, check=False, relativeto=root_pkgpath
        )
        rel_modname = sub_modname[len(pkgname) + 1 :]
        if not rel_modname or rel_modname.startswith("_"):
            # Skip private modules
            pass
        else:
            yield rel_modname, sub_modpath


def _extract_attributes(modpath=None, source=None, respect_all=True):
    """
    This is the function that basically simulates import *

    Example:
        >>> modpath = util_import.modname_to_modpath('mkinit', hide_init=False)
        >>> _extract_attributes(modpath)
        >>> modpath = util_import.modname_to_modpath('mkinit.util.util_diff', hide_init=False)
        >>> _extract_attributes(modpath)
    """
    if source is None:
        try:
            with open(modpath, "r", encoding="utf8") as file:
                source = file.read()
        except Exception as ex:  # nocover
            raise IOError("Error reading {}, caused by {}".format(modpath, repr(ex)))
    valid_attrs = None
    if respect_all:  # pragma: nobranch
        try:
            valid_attrs = static.parse_static_value("__all__", source)
        except NameError:
            pass
    if valid_attrs is None:
        import builtins
        # The __all__ variable is not specified or we dont care
        try:
            top_level = TopLevelVisitor.parse(source)
        except SyntaxError as ex:
            msg = "modpath={} has bad syntax: {}".format(modpath, ex)
            raise SyntaxError(msg)
        attrnames = top_level.attrnames
        # list of names we wont export by default
        invalid_callnames = dir(builtins)
        valid_attrs = []
        for attr in attrnames:
            if attr.startswith("_"):
                continue
            if attr in invalid_callnames:  # nocover
                continue
            valid_attrs.append(attr)
    return valid_attrs


def _static_parse_imports(modpath, submodules=None, external=None, respect_all=True, ignore=None):
    """
    Args:
        modpath (PathLike): base path to a package (with an __init__)
        submodules (List[str]): Submodules to look at in the base package.
            This is implicitly generated if not specified.
        respect_all (bool, default=True):
            if False, does not respect the __all__ attributes of submodules

    CommandLine:
        python -m mkinit.static_autogen _static_parse_imports

    Example:
        >>> modpath = util_import.modname_to_modpath('mkinit')
        >>> external = ['textwrap']
        >>> tup = _static_parse_imports(modpath, external=external)
        >>> modname, submodules, from_imports = tup
        >>> print('modname = {!r}'.format(modname))
        >>> print('submodules = {!r}'.format(submodules))
        >>> print('from_imports = {!r}'.format(from_imports))
        >>> # assert 'autogen_init' in submodules

    Example:
        >>> from mkinit.static_mkinit import *  # NOQA
        >>> modpath = util_import.modname_to_modpath('mkinit')
        >>> external = ['textwrap']
        >>> submodules = {'foo': ['bar', 'baz', 'biz']}
        >>> tup = _static_parse_imports(modpath, submodules=submodules, external=external)
        >>> modname, submodules, from_imports = tup
        >>> print('modname = {!r}'.format(modname))
        >>> print('submodules = {!r}'.format(submodules))
        >>> print('from_imports = {!r}'.format(from_imports))
        >>> # assert 'autogen_init' in submodules
    """
    logger.debug("Parse static submodules: {}".format(modpath))
    # FIXME: handle the case where the __init__.py file doesn't exist yet
    modname = util_import.modpath_to_modname(modpath, check=False)
    if submodules is None:
        # Equivalent to case submodules = {'*': ['*']}
        # TODO: refactor to reduce code size and collapse cases
        # TODO: could pull in pattern matching generalization from xdev and
        # allow regex or glob-type matches.
        logger.debug("Parsing implicit submodules!")
        import_paths = dict(_find_local_submodules(modpath))
        submodules = {k: None for k in sorted(import_paths.keys())}
        # logger.debug('Found {} import paths'.format(len(import_paths)))
        # logger.debug('Found {} submodules'.format(len(submodules)))
    else:
        logger.debug("Given explicit submodules")
        if modname is None:
            raise AssertionError("modname is None")

        if isinstance(submodules, list):
            # Make a dict mapping module names to None
            submodules = {m: None for m in submodules}

        # Determine which submodules were given as a pattern
        implicit_submodules = {k: v for k, v in submodules.items() if '*' in k}
        if implicit_submodules:
            submodule_patterns = submodules.copy()
            explicit_keys = set(submodule_patterns) - set(implicit_submodules)
            explicit_submodules = {k: submodules[k] for k in explicit_keys}
            implicit_candidates = {
                k: v for k, v in dict(_find_local_submodules(modpath)).items() if k not in explicit_keys
            }
            matched_submodules = {}
            for pat_key, pat_val in implicit_submodules.items():
                matched_submodules.update({
                    k: pat_val for k, v in implicit_candidates.items()
                    if fnmatch.fnmatch(k, pat_key)
                })
            submodules = explicit_submodules.copy()
            submodules.update(matched_submodules)

        import_paths = {
            m: util_import.modname_to_modpath(modname + "." + m, hide_init=False)
            for m in submodules.keys()
        }
        # FIX for relative nested import_paths
        for m in import_paths.keys():
            oldval = import_paths[m]
            if oldval is None:
                candidates = [
                    join(modpath, m),
                    join(modpath, m) + ".py",
                ]
                for newval in candidates:
                    if exists(newval):
                        import_paths[m] = newval
                        break
    imports = ["." + m for m in submodules.keys()]

    def _lookup_extractable_attrs(rel_modname):
        sub_modpath = import_paths[rel_modname]
        if sub_modpath is None:
            raise Exception("Failed to submodule lookup {!r}".format(rel_modname))
        try:
            extracted_attrs = _extract_attributes(sub_modpath, respect_all=respect_all)
        except SyntaxError as ex:
            warnings.warn(
                "Failed to parse module {!r}, ex = {!r}".format(rel_modname, ex)
            )
            extracted_attrs = None
        return extracted_attrs

    from_imports = []
    for rel_modname, attr_list in submodules.items():
        if attr_list is None:
            # Equivalent to case where attr_list = ['*']
            # TODO: refactor to reduce code size and collapse cases
            valid_attrs = _lookup_extractable_attrs(rel_modname)
            if valid_attrs is not None:
                if ignore:
                    ignore = set(ignore)
                    valid_attrs = [v for v in valid_attrs if v not in ignore]
                from_imports.append(("." + rel_modname, sorted(valid_attrs)))
        else:
            # Determine which attrs were given as a pattern
            implicit_attrs = {a for a in attr_list if '*' in a}
            if implicit_attrs:
                # pattern matching on implicit attrs
                explicit_attrs = set(attr_list) - implicit_attrs
                matched_attrs = set()
                extracted_attrs = _lookup_extractable_attrs(rel_modname)
                if extracted_attrs is not None:
                    for pat in implicit_attrs:
                        matched_attrs.update({
                            cand for cand in extracted_attrs if fnmatch.fnmatch(cand, pat)
                        })
                resolved_attrs = set()
                resolved_attrs.update(explicit_attrs)
                resolved_attrs.update(matched_attrs)
                attr_list = sorted(resolved_attrs)

            valid_attrs = attr_list
            if ignore:
                ignore = set(ignore)
                valid_attrs = [v for v in valid_attrs if v not in ignore]
            from_imports.append(("." + rel_modname, valid_attrs))

    if external:
        for ext_modname in external:
            ext_modpath = util_import.modname_to_modpath(ext_modname, hide_init=False)
            if ext_modpath is None:
                raise Exception("Failed to external lookup {!r}".format(ext_modpath))
            try:
                valid_attrs = _extract_attributes(ext_modpath, respect_all=respect_all)
            except SyntaxError as ex:
                warnings.warn("Failed to parse {!r}, ex = {!r}".format(ext_modname, ex))
            else:
                from_imports.append((ext_modname, sorted(valid_attrs)))

    return modname, imports, from_imports
