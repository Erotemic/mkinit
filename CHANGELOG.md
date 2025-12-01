# Changelog

We are currently working on porting this changelog to the specifications in
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

### Fixed
* Fixed issue #45: `__ignore__` variable is now properly preserved when regenerating `__init__.py` files, regardless of its position relative to other special variables like `__protected__` or `__private__`
* Fixed related issue: `__explicit__` and `__extra_all__` variables are now properly preserved when regenerating `__init__.py` files (same root cause as issue #45)
* Updated `_find_insert_points` docstring to document all preserved special variables


## Version: 1.1.0 Released 2024-01-17

### Added

* Added `--lazy_loader_typed` option, #40.

* Initial support for Python 3.12

### Removed

* Removed support for Python 3.6

### Changed
* Code cleanup

* Workaround Python 3.12 tokenize changes - new format strings may not be supported yet.

### Fixed
* Extra newlines in generated files


## Version: 1.0.0 - Released 2022-12-03

### Added
* Can now specify `"*"` in `__submodules__` to pattern match on available submodules.
* Added `--lazy_loader` option to use the `lazy_loader` package for reduced boilerplate.

### Fixed
* GH Issue #14: async functions are now handled correctly
* Issue with `EAGER_IMPORT`

### Changed
* The CLI now errors on unknown arguments unless the `MKINIT_ARGPARSE_LOOSE` environ is et.
* Drop support for Python 2.7 and 3.5
* Vendored in orderedset
* Can now detect other existing names in the file and insert them into `__all__`



## Version: 0.3.3 - Released 2021-07-19

### Added
* new `__ignore__` special attribute.

### Changed
* Dropped Python 3.4 support
* Modified generated lazy init code
* `__submodules__` can now be a dictionary of submodule names that point to submodule attributes.

### Fixed
* Fixed issues in lazy init
* Fixed issue with ast.Constant


## Version: 0.3.1 - released 2020-02-14


### Changed
* protected modules will still be exposed even if `--nomod` is specified.
* tweaked filtering behavior


## Version: 0.3.0

### Added
* Can now specify `--recursive` on the CLI to generate all `__init__.py` files in a package.
* Can now specify `--lazy` on the CLI to auto-generate PEP 562 lazy imports.

### Fixes
* Fixed a bug where long module names would be incorrectly formatted


## Version: 0.2.1
* Can now specify `__external__`
* Reworked submodules vs imports. 
* Slight API changes.
* Updated CLI docs.


## Version: 0.2.0
* Can now specify __explicit__, __protected__, and __private__.
* Dry by default specify -w to write
* Reworked CLI


## Version: 0.1.1
* Can now specify __init__.py file paths instead in addition to parent directory paths


## Version: 0.1.0
* Fixes and Version bump


## Version: 0.0.4
* Removed clutter from module level API
* generated __all__ is now sorted 
* generated __all__ is now separated from generated imports by a space


## Version: 0.0.3
* Moved formatting code to its own module 
* Improved handling of existing code when `AUTOGEN_INIT` tags are not specified
  by making light use of xdoctest's PS1 line parser.
* An `__all__` variable is now defined by default.
* Formatting is now controlled by an options dict
* Removed attrs kwarg in `static_init`
* Added command line arg `--nomods` to disable generating module imports.
* Added command line arg `--noall` to disable generating of the all variable.
* Added command line arg `--relative` to generate relative instead of absolute imports
* Added command line arg `--ignore_all` to ignore __all__ when parsing.


## Version: 0.0.2
* Changed attribute from `__SUBMODULES__` to `__submodules__`. The former is
  still accepted.
* Can now handle attributes defined in if-else and try-except statements as long as they are
  defined on all non-rejecting paths. (Note: a path is rejecting if it is
  unconditionally false or it unconditionally raises an exception)

## Version: 0.0.1
* Ported from `ubelt` `0.1.1`


## ## Version 0.3.3 - Unreleased
