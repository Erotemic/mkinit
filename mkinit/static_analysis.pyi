from _typeshed import Incomplete
from collections.abc import Generator

IS_PY_GE_308: Incomplete
IS_PY_GE_312: Incomplete


def parse_static_value(key: str,
                       source: str | None = None,
                       fpath: str | None = None):
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
