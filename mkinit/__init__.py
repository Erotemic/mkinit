"""
Regenerate Input Command
mkinit mkinit
"""
# flake8: noqa
__version__ = '0.0.2'
__DYNAMIC__ = False
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
