The `ahoy` module helps you write `__init__` files without `from ? import *`.

Ahoy automatically imports all submodules in a package and their members.

It can do this dynamically, or it can statically autogenerate the `__init__`
for faster import times. Its kinda like using the `fromimport *` syntax, but
its easy to replace with text that wont make other developers lose their hair.

## Command Line Usage

The following command will autogenerate an `__init__` file in the specified
path or module name.

```bash
ahoy <your_modname_or_modpath>
```


## Python Usage
```python
import ahoy; exec(ahoy.dynamic_init(__name__))
```
