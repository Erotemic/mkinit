from mkinit_dummy_module import subdir1
from mkinit_dummy_module import submod1
from mkinit_dummy_module import submod2

from mkinit_dummy_module.submod1 import (
    func1,
    func2,
)
from mkinit_dummy_module.submod2 import (
    class1,
    class2,
)

__all__ = ["class1", "class2", "func1", "func2", "subdir1", "submod1", "submod2"]
