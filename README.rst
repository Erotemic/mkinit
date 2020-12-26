mkinit
======

|CircleCI| |Travis| |Appveyor| |Codecov| |Pypi| |Downloads| |ReadTheDocs|


Read the docs here: http://mkinit.readthedocs.io/en/latest/ (although this is
mostly an API reference, the best getting started docs are currently in this
README)

The ``mkinit`` module helps you write ``__init__`` files that expose all submodule
attributes without ``from ? import *``.

``mkinit`` automatically imports all submodules in a package and their members.

It can do this dynamically, or it can statically autogenerate the ``__init__``
for faster import times. Its kinda like using the ``fromimport *`` syntax, but
its easy to replace with text that wont make other developers lose their hair.

Installation
============

.. code:: bash

    pip install mkinit


The Pitch
---------

Say you have a python module structured like so:

.. code::

    └── mkinit_demo_pkg
        ├── __init__.py
        ├── submod.py
        └── subpkg
            ├── __init__.py
            └── nested.py


And you would like to make all functions inside of ``submod.py`` and
``nested.py`` available at the top-level of the package. 

Imagine the contents of submod.py and nested.py are:

.. code:: python

    # --- submod.py ---

    def submod_func():
        print('This is a submod func in {}'.format(__file__))

    # --- nested.py ---

    def nested_func():
        print('This is a nested func in {}'.format(__file__))

You could manually write:


.. code:: python
    
    from mkinit_demo_pkg.submod import *
    from mkinit_demo_pkg.subpkg.nested import *


But that has a few problems. Using ``import *`` makes it hard for people
reading the code to know what is coming from where. Furthermore, if there were
many submodules you wanted to expose attributes of, writing this would become
tedious and hard to maintain. 

Enter the mkinit package. It has the ability to autogenerate explicit ``__init__.py``
files using static analysis. Normally, the mkinit CLI only works on one file at
a time, but if we specify the ``--recursive`` flag, then mkinit will
recursively generate ``__init__.py`` files for all subpackages in the package.

Thus running ``mkinit mkinit_demo_pkg --recursive`` will result in a root
``__init__.py`` file that looks like this:

.. code:: python

    from mkinit_demo_pkg import submod
    from mkinit_demo_pkg import subpkg

    from mkinit_demo_pkg.submod import (submod_func,)
    from mkinit_demo_pkg.subpkg import (nested, nested_func,)

    __all__ = ['nested', 'nested_func', 'submod', 'submod_func', 'subpkg']


That's pretty cool. The mkinit package was able to recursively parse our
package, find all of the defined names, and then generate ``__init__.py`` files
such that all attributes are exposed at the top level of the package.
Furthermore, this file is **readable**. It is perfectly clear exactly what
names are exposed in this module without having to execute anything.


Of course, this isn't a perfect solution. Perhaps only some submodules should
be exposed, perhaps you would rather use relative import statements, maybe you
only want to expose submodule but not their attributes, or vis-versa. Well good
news, because mkinit has command line flags that allow for all of these modes.
See ``mkinit --help`` for more details.


Lastly, while exposing all attributes can be helpful for larger projects,
import time can start to become a consideration. Thankfully, PEP 0562 outlines
a lazy import specification for Python >= 3.7. As of 2020-12-26 mkinit
supports autogenerating these lazy init files. 

Unfortunately, there is no syntax support for lazy imports, so mkinit must
define a ``lazy_import`` boilerplate function in each ``__init__.py`` file.


.. code:: python

    def lazy_import(module_name, submodules, submod_attrs):
        """
        Boilerplate to define PEP 562 __getattr__ for lazy import
        https://www.python.org/dev/peps/pep-0562/
        """
        import sys
        import importlib
        import importlib.util
        all_funcs = []
        for mod, funcs in submod_attrs.items():
            all_funcs.extend(funcs)
        name_to_submod = {
            func: mod for mod, funcs in submod_attrs.items()
            for func in funcs
        }

        def require(fullname):
            if fullname in sys.modules:
                return sys.modules[fullname]

            spec = importlib.util.find_spec(fullname)
            try:
                module = importlib.util.module_from_spec(spec)
            except Exception:
                raise ImportError(
                    'Could not lazy import module {fullname}'.format(
                        fullname=fullname)) from None
            loader = importlib.util.LazyLoader(spec.loader)

            sys.modules[fullname] = module

            # Make module with proper locking and add to sys.modules
            loader.exec_module(module)

            return module

        def __getattr__(name):
            if name in submodules:
                fullname = '{module_name}.{name}'.format(
                    module_name=module_name, name=name)
                attr = require(fullname)
            elif name in name_to_submod:
                modname = name_to_submod[name]
                module = importlib.import_module(
                    '{module_name}.{modname}'.format(
                        module_name=module_name, modname=modname)
                )
                attr = getattr(module, name)
            else:
                raise AttributeError(
                    'No {module_name} attribute {name}'.format(
                        module_name=module_name, name=name))
            # Set module-level attribute so getattr is not called again
            globals()[name] = attr
            return attr
        return __getattr__
    
    __getattr__ = lazy_import(
        __name__,
        submodules={
            'submod',
            'subpkg',
        },
        submod_attrs={
            'submod': [
                'submod_func',
            ],
            'subpkg': [
                'nested',
                'nested_func',
            ],
        },
    )

    def __dir__():
        return __all__

    __all__ = ['nested', 'nested_func', 'submod', 'submod_func', 'subpkg']



Command Line Usage
------------------

The following command will statically autogenerate an `__init__` file in the
specified path or module name. If one exists, it will only replace text after
the final comment. This means `mkinit` wont clobber your custom logic and can
be used to help maintain customized `__init__.py` files.

.. code:: bash

    mkinit <your_modname_or_modpath> -w


You can also enclose the area allowed to be clobbered in the auto-generation
with special xml-like comments.

Dynamic Usage
-------------

NOTE: Dynamic usage is NOT recommended. 

In most cases, we recommend using mkinit command line tool to statically
generate / update the `__init__.py` file, but there is an option to to use it
dynamically (although this might be considered worse practice than using
``import *``).

.. code:: python

    import mkinit; exec(mkinit.dynamic_init(__name__))


Examples
========

The `mkinit` module is used by the
`ubelt`(https://www.github.com/Erotemic/ubelt) library to explicitly
auto-generate part of the `__init__.py` file. This example walks through the
design of this module to illustrate the usage of `mkinit`.

Step 1 (Optional): Write any custom `__init__` code
----------------------------------------------------

The first section of the `ubelt` module consists of manually written code. It
contains coding, `flake8` directives, a docstring a few comments, a future
import, and a custom `__version__` attribute. Here is an example of this
manually written code in the `0.2.0.dev0` version of `ubelt`.

.. code:: python

    # -*- coding: utf-8 -*-
    # flake8: noqa
    """
    CommandLine:
        # Partially regenerate __init__.py
        mkinit ubelt
    """
    # Todo:
    #     The following functions and classes are candidates to be ported from utool:
    #     * reload_class
    #     * inject_func_as_property
    #     * accumulate
    #     * rsync
    from __future__ import absolute_import, division, print_function, unicode_literals

    __version__ = '0.2.0'

It doesn't particularly matter what the above code is, the point is to
illustrate that `mkinit` does not prevent you from customizing your code. By
default auto-generation will only start clobbering existing code after the
final comment, in the file, which is a decent heuristic, but as we will see,
there are other more explicit ways to define exactly where auto-generated code
is allowed.

Step 2 (Optional): Enumerate relevant submodules
------------------------------------------------

After optionally writing any custom code, you may optionally specify exactly
what submodules should be considered when auto-generating imports. This is done
by setting the `__submodules__` attribute to a list of submodule names. 

In `ubelt` this section looks similar to the following:

.. code:: python

    __submodules__ = [
        'util_arg',
        'util_cmd',
        'util_dict',
        'util_links',
        'util_hash',
        'util_import',
        'orderedset',
        'progiter',
    ]

Note that this step is optional, but recommended. If the `__submodules__`
package is not specified, then all paths matching the glob expressions `*.py`
or `*/__init__.py` are considered as part of the package.

Step 3: Autogenerate explicitly
-------------------------------

To provide the fastest import times and most readable `__init__.py` files, use
the `mkinit` command line script to statically parse the submodules and
populate the `__init__.py` file with the submodules and their top-level
members.

Before running this script it is good practice to paste the XML-like comment
directives into the `__init__.py` file. This restricts where `mkinit` is
allowed to autogenerate code, and it also uses the same indentation of the
comments in case you want to run the auto-generated code conditionally. Note,
if the second tag is not specified, then it is assumed that `mkinit` can
overwrite everything after the first tag.

.. code:: python

    # <AUTOGEN_INIT>
    pass
    # </AUTOGEN_INIT>

Now that we have inserted the auto-generation tags, we can actually run
`mkinit`.  In general this is done by running `mkinit <path-to-pkg-directory>`.

Assuming the `ubelt` repo is checked out in `~/code/`, the command to
autogenerate its `__init__.py` file would be: `mkinit ~/code/ubelt/ubelt`.
Given the previously specified `__submodules__`, the resulting auto-generated
portion of the code looks like this: 


.. code:: python

    # <AUTOGEN_INIT>
    from ubelt import util_arg
    from ubelt import util_cmd
    from ubelt import util_dict
    from ubelt import util_links
    from ubelt import util_hash
    from ubelt import util_import
    from ubelt import orderedset
    from ubelt import progiter
    from ubelt.util_arg import (argflag, argval,)
    from ubelt.util_cmd import (cmd,)
    from ubelt.util_dict import (AutoDict, AutoOrderedDict, ddict, dict_hist,
                                 dict_subset, dict_take, dict_union, dzip,
                                 find_duplicates, group_items, invert_dict,
                                 map_keys, map_vals, odict,)
    from ubelt.util_links import (symlink,)
    from ubelt.util_hash import (hash_data, hash_file,)
    from ubelt.util_import import (import_module_from_name,
                                   import_module_from_path, modname_to_modpath,
                                   modpath_to_modname, split_modpath,)
    from ubelt.orderedset import (OrderedSet, oset,)
    from ubelt.progiter import (ProgIter,)
    __all__ = ['util_arg', 'util_cmd', 'util_dict', 'util_links', 'util_hash',
               'util_import', 'orderedset', 'progiter', 'argflag', 'argval', 'cmd',
               'AutoDict', 'AutoOrderedDict', 'ddict', 'dict_hist', 'dict_subset',
               'dict_take', 'dict_union', 'dzip', 'find_duplicates', 'group_items',
               'invert_dict', 'map_keys', 'map_vals', 'odict', 'symlink',
               'hash_data', 'hash_file', 'import_module_from_name',
               'import_module_from_path', 'modname_to_modpath',
               'modpath_to_modname', 'split_modpath', 'OrderedSet', 'oset',
               'ProgIter']

When running the command-line `mkinit` tool, the target module is inspected
using static analysis, so no code from the target module is ever run. This
avoids unintended side effects, prevents arbitrary code execution, and ensures
that `mkinit` will do something useful even if there would otherwise be a
runtime error.

Step 3 (alternate): Autogenerate dynamically
--------------------------------------------

While running `mkinit` from the command line produces the cleanest and most
readable `__init__.py`, you have to run it every time you make a change to your
library. This is not always desirable especially during rapid development of a
new Python package. In this case it is possible to dynamically execute `mkinit`
on import of your module. To use dynamic initialization simply paste the
following lines into the `__init__.py` file.

.. code:: python

    import mkinit
    exec(mkinit.dynamic_init(__name__, __submodules__))

This is almost equivalent to running the static command line variant.  However,
instead of using static analysis, this will use the Python interpreter to
execute and import all submodules and dynamically inspect the defined members.
This is faster than using static analysis, and in most circumstances there will
be no difference in the resulting imported attributes. To avoid all differences 
simply specify the `__all__` attribute in each submodule.

Note that inclusion of the `__submodules__` attribute is not strictly
necessary. The dynamic version of this function will look in the parent stack
frame for this attribute if it is not specified explicitly as an argument.

It is also possible to achieve a "best of both worlds" trade-off using
conditional logic. Use a conditional block to execute dynamic initialization
and place the static auto-generation tags in the block that is not executed.
This lets you develop without worrying about updating the `__init__.py` file,
and lets you statically generate the code for documentation purposes when you
want to. Once the rapid development phase is over, you can remove the dynamic
conditional, keep the auto-generated portion, and forget you ever used `mkinit`
in the first place!


.. code:: python

    __DYNAMIC__ = True
    if __DYNAMIC__:
        from mkinit import dynamic_mkinit
        exec(dynamic_mkinit.dynamic_init(__name__))
    else:
        # <AUTOGEN_INIT>
        from mkinit import dynamic_mkinit
        from mkinit import static_mkinit
        from mkinit.dynamic_mkinit import (dynamic_init,)
        from mkinit.static_mkinit import (autogen_init,)
        # </AUTOGEN_INIT>


Behavior Notes
--------------

The `mkinit` module is a simple way to execute a complex task. At times it may
seem like magic, although I assure you it is not. To minimize perception of
magic and maximize understanding of its behaviors, please consider the
following:

    * When discovering attributes of submodules `mkinit` will respect the `__all__`
      attribute by default. In general it is good practice to specify this
      property; doing so will also avoid the following caveats.

    * Static analysis currently only extracts top-level module attributes. However, 
      if will also extract attributes defined on all non-error raising paths of
      conditional if-else or try-except statements. 

    * Static analysis currently does not look or account for the usage of the `del`
      operator. Again, these will be accounted for by dynamic analysis.

    * In the case where no `__init__.py` file exists, the `mkinit` command line
      tool will create one.

    * By default we ignore attributes that are marked as non-public by a leading
      underscore

TODO
----

    - [ ] Give `dynamic_init` an options dict to maintain a compatible API with `static_init`.

    - [ ] If an attribute would be defined twice, then don't define it at all.
      Currently, it is defined, but its value is not well-defined.


.. |CircleCI| image:: https://circleci.com/gh/Erotemic/mkinit.svg?style=svg
    :target: https://circleci.com/gh/Erotemic/mkinit
.. |Travis| image:: https://img.shields.io/travis/Erotemic/mkinit/master.svg?label=Travis%20CI
   :target: https://travis-ci.org/Erotemic/mkinit?branch=master
.. |Appveyor| image:: https://ci.appveyor.com/api/projects/status/github/Erotemic/mkinit?branch=master&svg=True
   :target: https://ci.appveyor.com/projegt/Erotemic/mkinit/branch/master
.. |Codecov| image:: https://codecov.io/github/Erotemic/mkinit/badge.svg?branch=master&service=github
   :target: https://codecov.io/github/Erotemic/mkinit?branch=master
.. |Pypi| image:: https://img.shields.io/pypi/v/mkinit.svg
   :target: https://pypi.python.org/pypi/mkinit
.. |Downloads| image:: https://img.shields.io/pypi/dm/mkinit.svg
   :target: https://pypistats.org/packages/mkinit
.. |ReadTheDocs| image:: https://readthedocs.org/projects/mkinit/badge/?version=latest
    :target: http://mkinit.readthedocs.io/en/latest/
