[![Travis](https://img.shields.io/travis/Erotemic/mkinit/master.svg?label=Travis%20CI)](https://travis-ci.org/Erotemic/mkinit)
[![Codecov](https://codecov.io/github/Erotemic/mkinit/badge.svg?branch=master&service=github)](https://codecov.io/github/Erotemic/mkinit?branch=master)
[![Appveyor](https://ci.appveyor.com/api/projects/status/github/Erotemic/mkinit?svg=True)](https://ci.appveyor.com/project/Erotemic/mkinit/branch/master)
[![Pypi](https://img.shields.io/pypi/v/mkinit.svg)](https://pypi.python.org/pypi/mkinit)


Read the docs here: http://mkinit.readthedocs.io/en/latest/

The `mkinit` module helps you write `__init__` files that expose all submodule
attributes without `from ? import *`.

`mkinit` automatically imports all submodules in a package and their members.

It can do this dynamically, or it can statically autogenerate the `__init__`
for faster import times. Its kinda like using the `fromimport *` syntax, but
its easy to replace with text that wont make other developers lose their hair.

## Installation:

```
pip install mkinit
```

## Command Line Usage

The following command will statically autogenerate an `__init__` file in the
specified path or module name. If one exists, it will only replace text after
the final comment. This means `mkinit` wont clobber your custom logic and can
be used to help maintain customized `__init__.py` files.

```bash
mkinit <your_modname_or_modpath>
```

You can also enclose the area allowed to be clobbered in the auto-generation
with special xml-like comments.


## Python Usage
```python
import mkinit; exec(mkinit.dynamic_init(__name__))
```


## Examples

The `mkinit` module is used by the
`ubelt`(https://www.github.com/Erotemic/ubelt) library to explicitly
auto-generate part of the `__init__.py` file. This example walks through the
design of this module to illustrate the usage of `mkinit`.

### Step 1 (Optional): Write any custom `__init__` code

The first section of the `ubelt` module consists of manually written code. It
contains coding, `flake8` directives, a docstring a few comments, a future
import, and a custom `__version__` attribute. Here is an example of this
manually written code in the `0.2.0.dev0` version of `ubelt`.

```python
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
```
It doesn't particularly matter what the above code is, the point is to
illustrate that `mkinit` does not prevent you from customizing your code. By
default auto-generation will only start clobbering existing code after the
final comment, in the file, which is a decent heuristic, but as we will see,
there are other more explicit ways to define exactly where auto-generated code
is allowed.

### Step 2 (Optional): Enumerate relevant submodules

After optionally writing any custom code, you may optionally specify exactly
what submodules should be considered when auto-generating imports. This is done
by setting the `__submodules__` attribute to a list of submodule names. 

In `ubelt` this section looks similar to the following:

```python
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
```

Note that this step is optional, but recommended. If the `__submodules__`
package is not specified, then all paths matching the glob expressions `*.py`
or `*/__init__.py` are considered as part of the package.

### Step 3: Autogenerate explicitly

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

```python
# <AUTOGEN_INIT>
pass
# </AUTOGEN_INIT>
```

Now that we have inserted the auto-generation tags, we can actually run
`mkinit`.  In general this is done by running `mkinit <path-to-pkg-directory>`.

Assuming the `ubelt` repo is checked out in `~/code/`, the command to
autogenerate its `__init__.py` file would be: `mkinit ~/code/ubelt/ubelt`.
Given the previously specified `__submodules__`, the resulting auto-generated
portion of the code looks like this: 

```python
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
# </AUTOGEN_INIT>
```

When running the command-line `mkinit` tool, the target module is inspected
using static analysis, so no code from the target module is ever run. This
avoids unintended side effects, prevents arbitrary code execution, and ensures
that `mkinit` will do something useful even if there would otherwise be a
runtime error.

### Step 3 (alternate): Autogenerate dynamically

While running `mkinit` from the command line produces the cleanest and most
readable `__init__.py`, you have to run it every time you make a change to your
library. This is not always desirable especially during rapid development of a
new Python package. In this case it is possible to dynamically execute `mkinit`
on import of your module. To use dynamic initialization simply paste the
following lines into the `__init__.py` file.

```
import mkinit
exec(mkinit.dynamic_init(__name__, __submodules__))
```

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


```python
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
```




## Behavior Notes

The `mkinit` module is a simple way to execute a complex task. At times it may
seem like magic, although I assure you it is not. To minimize perception of
magic and maximize understanding of its behaviors, please consider the
following:

* When discovering attributes of submodules `mkinit` will respect the `__all__`
  attribute by default. In general it is good practice to specify this
  property; doing so will also avoid the following caveats.
* Static analysis currently only extracts top-level module attributes. However, 
  if will also extract attributes defined on all paths of conditional
  if-else statements. (try except statements don't work yet)
* Static analysis currently does not look or account for the usage of the `del`
  operator. Again, these will be accounted for by dynamic analysis.
* In the case where no `__init__.py` file exists, the `mkinit` command line
  tool will create one.
* By default we ignore attributes that are marked as non-public by a leading
  underscore
