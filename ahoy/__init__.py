"""
Regenerate Input Command
python -m ahoy ahoy
"""
# flake8: noqa
__version__ = '0.0.1'
__DYNAMIC__ = False
if __DYNAMIC__:
    from ahoy import dynamic_make_init
    dynamic_make_init.dynamic_import()
else:
    # <AUTOGEN_INIT>
    from ahoy import dynamic_make_init
    from ahoy import static_autogen
    from ahoy.dynamic_make_init import (dynamic_import,)
    from ahoy.static_autogen import (autogen_init,)
    # </AUTOGEN_INIT>
