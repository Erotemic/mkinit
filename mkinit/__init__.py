# -*- coding: utf-8 -*-
"""
Regenerate Input Command
mkinit ~/code/mkinit/mkinit
"""
__version__ = "0.3.4"

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
