
import lazy_loader


__getattr__, __dir__, __all__ = lazy_loader.attach(
    __name__,
    submodules={
        'submod',
        'subpkg',
    },
    submod_attrs={
        'submod': [
            'submod_func',
        ],
        'subpkg': [
            'nested',
            'nested_func',
        ],
    },
)

__all__ = ['nested', 'nested_func', 'submod', 'submod_func', 'subpkg']
