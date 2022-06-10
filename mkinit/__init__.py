# -*- coding: utf-8 -*-
"""
The MkInit Module
-----------------

A tool to autogenerate explicit top-level imports
"""

__autogen__ = """
Regenerate Input Command
mkinit ~/code/mkinit/mkinit
"""

__version__ = "1.0.0"

__submodules__ = [
    "dynamic_mkinit",
    "static_mkinit",
]

from mkinit import dynamic_mkinit
from mkinit import static_mkinit

from mkinit.dynamic_mkinit import (
    dynamic_init,
)
from mkinit.static_mkinit import (
    autogen_init,
    static_init,
)

__all__ = [
    "autogen_init",
    "dynamic_init",
    "dynamic_mkinit",
    "static_init",
    "static_mkinit",
]
