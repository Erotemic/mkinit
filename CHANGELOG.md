version: 0.3.2
---------------

### Changed
* `__submodules__` can now be a dictionary of submodule names that point to submodule attributes.


version: 0.3.1 - released 2020-02-14
---------------


### Changed
* protected modules will still be exposed even if `--nomod` is specified.
* tweaked filtering behavior


version: 0.3.0
---------------

### Added
* Can now specify `--recursive` on the CLI to generate all `__init__.py` files in a package.
* Can now specify `--lazy` on the CLI to auto-generate PEP 562 lazy imports.

### Fixes
* Fixed a bug where long module names would be incorrectly formatted


version: 0.2.1
---------------
* Can now specify `__external__`
* Reworked submodules vs imports. 
* Slight API changes.
* Updated CLI docs.


version: 0.2.0
---------------
* Can now specify __explicit__, __protected__, and __private__.
* Dry by default specify -w to write
* Reworked CLI


version: 0.1.1
---------------
* Can now specify __init__.py file paths instead in addition to parent directory paths


version: 0.1.0
---------------
* Fixes and version bump


version: 0.0.4
---------------
* Removed clutter from module level API
* generated __all__ is now sorted 
* generated __all__ is now separated from generated imports by a space


version: 0.0.3
---------------
* Moved formatting code to its own module 
* Improved handling of existing code when AUTOGEN_INIT tags are not specified
  by making light use of xdoctest's PS1 line parser.
* An __all__ variable is now defined by default.
* Formatting is now controlled by an options dict
* Removed attrs kwarg in static_init
* Added command line arg `--nomods` to disable generating module imports.
* Added command line arg `--noall` to disable generating of the all variable.
* Added command line arg `--relative` to generate relative instead of absolute imports
* Added command line arg `--ignore_all` to ignore __all__ when parsing.


version: 0.0.2
---------------
* Changed attribute from `__SUBMODULES__` to `__submodules__`. The former is
  still accepted.
* Can now handle attributes defined in if-else and try-except statements as long as they are
  defined on all non-rejecting paths. (Note: a path is rejecting if it is
  unconditionally false or it unconditionally raises an exception)

version: 0.0.1
---------------
* Ported from `ubelt` `0.1.1`
