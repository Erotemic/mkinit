from _typeshed import Incomplete
from collections.abc import MutableSet, Sequence


def is_iterable(obj):
    ...


SLICE_ALL: Incomplete


class OrderedSet(MutableSet, Sequence):
    items: Incomplete
    map: Incomplete

    def __init__(self, iterable: Incomplete | None = ...) -> None:
        ...

    def __len__(self):
        ...

    def __getitem__(self, index):
        ...

    def copy(self):
        ...

    def __contains__(self, key):
        ...

    def add(self, key):
        ...

    append = add

    def update(self, sequence):
        ...

    def index(self, key):
        ...

    get_loc = index
    get_indexer = index

    def pop(self):
        ...

    def discard(self, key) -> None:
        ...

    def clear(self) -> None:
        ...

    def __iter__(self):
        ...

    def __reversed__(self):
        ...

    def __eq__(self, other):
        ...

    def union(self, *sets):
        ...

    def __and__(self, other):
        ...

    def intersection(self, *sets):
        ...

    def difference(self, *sets):
        ...

    def issubset(self, other):
        ...

    def issuperset(self, other):
        ...

    def symmetric_difference(self, other):
        ...

    def difference_update(self, *sets) -> None:
        ...

    def intersection_update(self, other) -> None:
        ...

    def symmetric_difference_update(self, other) -> None:
        ...
