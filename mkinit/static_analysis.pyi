from typing import Union
from collections.abc import Generator


def parse_static_value(key: str,
                       source: Union[str, None] = None,
                       fpath: Union[str, None] = None):
    ...


def package_modpaths(pkgpath: str,
                     with_pkg: bool = False,
                     with_mod: bool = True,
                     followlinks: bool = ...,
                     recursive: bool = True,
                     with_libs: bool = False,
                     check: bool = True) -> Generator[str, None, None]:
    ...


def is_balanced_statement(lines: list) -> bool:
    ...
