from typing import List
from typing import Union
from os import PathLike
from typing import Tuple


def modname_to_modpath(
        modname: str,
        hide_init: bool = True,
        hide_main: bool = False,
        sys_path: Union[None, List[Union[str,
                                         PathLike]]] = None) -> str | None:
    ...


def normalize_modpath(modpath: Union[str, PathLike],
                      hide_init: bool = True,
                      hide_main: bool = False) -> str | PathLike:
    ...


def modpath_to_modname(modpath: str,
                       hide_init: bool = True,
                       hide_main: bool = False,
                       check: bool = True,
                       relativeto: str = None) -> str:
    ...


def split_modpath(modpath: str, check: bool = True) -> Tuple[str, str]:
    ...
