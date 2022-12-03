#!/bin/bash
__doc__="
This demo shows how mkinit is used.

In this directory we have a simple package mkinit_demo_pkg with an empty
__init__.py file and we will use mkinit to populate that file so all module
attributes are exposed at the top level.
"

PRINT_TEXT_BLOCK(){
    # helper function so the echos themselves dont trigger the set -x behavior.
    # We color the documentation text in yellow to distinguish it.
    printf "\033[0;33m%s\033[0m" "$1"
    set -x
}



echo "${__doc__}"


set +x 2> /dev/null
PRINT_TEXT_BLOCK "

### Prepare the Demo

Before we run the demo we are going to clobber 
mkinit_demo_pkg/__init__.py and
mkinit_demo_pkg/nested/__init__.py 
to ensure they are empty.
"
echo "" > mkinit_demo_pkg/__init__.py
echo "" > mkinit_demo_pkg/subpkg/__init__.py


{ set +x; } 2> /dev/null
PRINT_TEXT_BLOCK "

### Basic Usage

By default mkinit does not write anything, it just prints the generated python
code to stdout.
"

mkinit mkinit_demo_pkg


{ set +x; } 2> /dev/null
PRINT_TEXT_BLOCK "
You can specify -w to accept the proposed generated text or use --diff to
inspect the diff
"
mkinit mkinit_demo_pkg --diff


{ set +x; } 2> /dev/null
PRINT_TEXT_BLOCK "
If you have Python 3.7+ you generate a lazy init, which exposes all of the
names at the top level but does not do the work to import them until they are
accessed.
"
mkinit mkinit_demo_pkg --lazy --diff


{ set +x; } 2> /dev/null
PRINT_TEXT_BLOCK "
New in mkinit version 1.0 we can use the lazy_loader module to reduce
boilerplate at the cost of a small dependency
"
mkinit mkinit_demo_pkg --lazy_loader --diff


{ set +x; } 2> /dev/null
PRINT_TEXT_BLOCK '
Notice how the above generated functions will import subpkg, but none of its
members. That is because mkinit only operates at one init file at a time by default.
But if you use `--recursive` then it will run on every submodule starting at
the leaves and ending at the root.

Now lets execute mkinit with --write to actually modify the module.  First we
will do explicit eager imports.
'
mkinit mkinit_demo_pkg --recursive --write

cat mkinit_demo_pkg/__init__.py

python -c "import mkinit_demo_pkg; mkinit_demo_pkg.submod_func()"
python -c "import mkinit_demo_pkg; mkinit_demo_pkg.nested_func()"


{ set +x; } 2> /dev/null
PRINT_TEXT_BLOCK '
Now lets do that with the dependency free lazy initialization. 

First just look at the diff
'
mkinit mkinit_demo_pkg --recursive --lazy --diff


{ set +x; } 2> /dev/null
PRINT_TEXT_BLOCK '

Now lets do it for real

'
mkinit mkinit_demo_pkg --recursive --lazy --write

python -c "import mkinit_demo_pkg; mkinit_demo_pkg.submod_func()"
python -c "import mkinit_demo_pkg; mkinit_demo_pkg.nested_func()"


{ set +x; } 2> /dev/null
PRINT_TEXT_BLOCK '

Notice now that we are using --lazy only the print statements in the modules
are are using are actually executed, unlike previously where all modules are 
imported eagerly. 

With lazy loads we can still replicate this original behavior using the
EAGER_IMPROT environment variable. This is useful when debugging.

'

EAGER_IMPORT=1 python -c "import mkinit_demo_pkg; mkinit_demo_pkg.submod_func()"
EAGER_IMPORT=1 python -c "import mkinit_demo_pkg; mkinit_demo_pkg.nested_func()"


{ set +x; } 2> /dev/null
PRINT_TEXT_BLOCK '

Now we will do the same thing but with the new --lazy_loader option.

'
mkinit mkinit_demo_pkg --recursive --lazy_loader --diff
mkinit mkinit_demo_pkg --recursive --lazy_loader --write




{ set +x; } 2> /dev/null
PRINT_TEXT_BLOCK '

Verify the lazy_loader variant works the same.

'
python -c "import mkinit_demo_pkg; mkinit_demo_pkg.submod_func()"
python -c "import mkinit_demo_pkg; mkinit_demo_pkg.nested_func()"


PRINT_TEXT_BLOCK '

Verify the lazy_loader variant works with EAGER_IMPORT.

'
python -c "import mkinit_demo_pkg; mkinit_demo_pkg.submod_func()"
python -c "import mkinit_demo_pkg; mkinit_demo_pkg.nested_func()"
