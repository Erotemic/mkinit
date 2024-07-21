"""
Statically ports utilities from ubelt needed by mkinit.

Similar Scripts:
    ~/code/xdoctest/dev/maintain/port_ubelt_utils.py
    ~/code/mkinit/dev/maintain/port_ubelt_code.py
    ~/code/line_profiler/dev/maintain/port_utilities.py
"""
import ubelt as ub


def postprocess_ported_code(text):
    prefix = ub.codeblock(
        '''
        """
        This file was autogenerated based on code in :py:mod:`ubelt` via
        dev/maintain/port_ubelt_code.py in the mkinit repo.
        """
        ''')

    # Remove doctest references to ubelt
    new_lines = []
    import re
    for line in text.split('\n'):
        if line.strip().startswith('>>> from ubelt'):
            continue
        if line.strip().startswith('>>> import ubelt as ub'):
            line = re.sub('>>> .*', '>>> # xdoctest: +SKIP("ubelt dependency")', line)
        new_lines.append(line)

    text = '\n'.join(new_lines)
    text = prefix + '\n' + text + '\n'
    return text


def autogen_mkint_utils():
    import liberator
    lib = liberator.Liberator()

    from ubelt import util_import
    lib.add_dynamic(util_import.split_modpath)
    lib.add_dynamic(util_import.modpath_to_modname)
    lib.add_dynamic(util_import.modname_to_modpath)
    lib.expand(['ubelt'])
    text = lib.current_sourcecode()
    print(text)
    """
    pip install rope
    pip install parso
    """
    import parso
    import mkinit
    target_fpath = ub.Path(mkinit.util.util_import.__file__)
    if target_fpath.exists():
        new_module = parso.parse(text)
        old_module = parso.parse(target_fpath.read_text())
        new_names = [child.name.value for child in new_module.children if child.type in {'funcdef', 'classdef'}]
        old_names = [child.name.value for child in old_module.children if child.type in {'funcdef', 'classdef'}]
        print(set(old_names) - set(new_names))
        print(set(new_names) - set(old_names))
    text = postprocess_ported_code(text)
    target_fpath.write_text(text)

    # Vendor in ordered set
    lib = liberator.Liberator()
    from ubelt import orderedset
    lib.add_dynamic(orderedset.OrderedSet)
    lib.expand(["ubelt"])
    text = lib.current_sourcecode()
    text = postprocess_ported_code(text)
    target_fpath = ub.Path("~/code/mkinit/mkinit/util/orderedset.py").expand()
    target_fpath.write_text(text)


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/mkinit/dev/port_ubelt_code.py
    """
    autogen_mkint_utils()
