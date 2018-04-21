[![Travis](https://img.shields.io/travis/Erotemic/mkinit/master.svg?label=Travis%20CI)](https://travis-ci.org/Erotemic/mkinit)
[![Codecov](https://codecov.io/github/Erotemic/mkinit/badge.svg?branch=master&service=github)](https://codecov.io/github/Erotemic/mkinit?branch=master)
[![Appveyor](https://ci.appveyor.com/api/projects/status/github/Erotemic/mkinit?svg=True)](https://ci.appveyor.com/project/Erotemic/mkinit/branch/master)
[![Pypi](https://img.shields.io/pypi/v/mkinit.svg)](https://pypi.python.org/pypi/mkinit)


Read the docs here: http://mkinit.readthedocs.io/en/latest/

The `mkinit` module helps you write `__init__` files without `from ? import *`.

`mkinit` automatically imports all submodules in a package and their members.

It can do this dynamically, or it can statically autogenerate the `__init__`
for faster import times. Its kinda like using the `fromimport *` syntax, but
its easy to replace with text that wont make other developers lose their hair.

## Command Line Usage

The following command will statically autogenerate an `__init__` file in the
specified path or module name. If one exists, it will only replace text after
the final comment. This means `mkinit` wont clobber your custom logic and can
be used to help maintain customized `__init__.py` files.

```bash
mkinit <your_modname_or_modpath>
```

You can also enclose the area allowed to be clobbered in the autogeneration
with special xml-like comments.


## Python Usage
```python
import mkinit; exec(mkinit.dynamic_init(__name__))
```
