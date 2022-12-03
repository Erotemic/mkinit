
import lazy_loader


__getattr__, __dir__, __all__ = lazy_loader.attach(
    __name__,
    submodules={
        'nested',
    },
    submod_attrs={
        'nested': [
            'nested_func',
        ],
    },
)

__all__ = ['nested', 'nested_func']
