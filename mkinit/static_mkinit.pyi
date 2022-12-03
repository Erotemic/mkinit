from typing import Union
from os import PathLike
from typing import List
from _typeshed import Incomplete

logger: Incomplete


def autogen_init(modpath_or_name: Union[PathLike, str],
                 submodules: List[str] = None,
                 respect_all: bool = True,
                 options: dict = None,
                 dry: bool = False,
                 diff: bool = ...,
                 recursive: bool = False):
    ...


def static_init(modpath_or_name,
                submodules: Incomplete | None = ...,
                respect_all: bool = ...,
                options: Incomplete | None = ...):
    ...


def parse_user_declarations(modpath):
    ...
