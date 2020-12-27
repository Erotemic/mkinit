# -*- coding: utf-8 -*-
"""
Port of ubelt utilities + difftext wrapper around difflib
"""
from __future__ import print_function, division, absolute_import, unicode_literals
import os
import sys
import six

# Global state that determines if ANSI-coloring text is allowed
# (which is mainly to address non-ANSI complient windows consoles)
# complient with https://no-color.org/
NO_COLOR = bool(os.environ.get("NO_COLOR"))


def ensure_unicode(text):
    r"""
    Casts bytes into utf8 (mostly for python2 compatibility)

    References:
        http://stackoverflow.com/questions/12561063/extract-data-from-file

    Example:
        >>> import codecs  # NOQA
        >>> assert ensure_unicode('my ünicôdé strįng') == 'my ünicôdé strįng'
        >>> assert ensure_unicode('text1') == 'text1'
        >>> assert ensure_unicode('text1'.encode('utf8')) == 'text1'
        >>> assert ensure_unicode('ï»¿text1'.encode('utf8')) == 'ï»¿text1'
        >>> assert (codecs.BOM_UTF8 + 'text»¿'.encode('utf8')).decode('utf8')
    """
    if isinstance(text, six.text_type):
        return text
    elif isinstance(text, six.binary_type):
        return text.decode("utf8")
    else:  # nocover
        raise ValueError("unknown input type {!r}".format(text))


def difftext(text1, text2, context_lines=0, ignore_whitespace=False, colored=False):
    r"""
    Uses difflib to return a difference string between two similar texts

    Args:
        text1 (str): old text
        text2 (str): new text
        context_lines (int): number of lines of unchanged context
        ignore_whitespace (bool):
        colored (bool): if true highlight the diff

    Returns:
        str: formatted difference text message

    References:
        http://www.java2s.com/Code/Python/Utility/IntelligentdiffbetweentextfilesTimPeters.htm

    Example:
        >>> # build test data
        >>> text1 = 'one\ntwo\nthree'
        >>> text2 = 'one\ntwo\nfive'
        >>> # execute function
        >>> result = difftext(text1, text2)
        >>> # verify results
        >>> print(result)
        - three
        + five

    Example:
        >>> # build test data
        >>> text1 = 'one\ntwo\nthree\n3.1\n3.14\n3.1415\npi\n3.4\n3.5\n4'
        >>> text2 = 'one\ntwo\nfive\n3.1\n3.14\n3.1415\npi\n3.4\n4'
        >>> # execute function
        >>> context_lines = 1
        >>> result = difftext(text1, text2, context_lines, colored=True)
        >>> # verify results
        >>> print(result)
    """
    import difflib

    text1 = ensure_unicode(text1)
    text2 = ensure_unicode(text2)
    text1_lines = text1.splitlines()
    text2_lines = text2.splitlines()
    if ignore_whitespace:
        text1_lines = [t.rstrip() for t in text1_lines]
        text2_lines = [t.rstrip() for t in text2_lines]
        ndiff_kw = dict(
            linejunk=difflib.IS_LINE_JUNK, charjunk=difflib.IS_CHARACTER_JUNK
        )
    else:
        ndiff_kw = {}
    all_diff_lines = list(difflib.ndiff(text1_lines, text2_lines, **ndiff_kw))

    if context_lines is None:
        diff_lines = all_diff_lines
    else:
        # boolean for every line if it is marked or not
        ismarked_list = [len(line) > 0 and line[0] in "+-?" for line in all_diff_lines]
        # flag lines that are within context_lines away from a diff line
        isvalid_list = ismarked_list[:]
        for i in range(1, context_lines + 1):
            isvalid_list[:-i] = list(
                map(any, zip(isvalid_list[:-i], ismarked_list[i:]))
            )
            isvalid_list[i:] = list(map(any, zip(isvalid_list[i:], ismarked_list[:-i])))

        USE_BREAK_LINE = True
        if USE_BREAK_LINE:
            # insert a visual break when there is a break in context
            diff_lines = []
            prev = False
            visual_break = "\n <... FILTERED CONTEXT ...> \n"
            # print(isvalid_list)
            for line, valid in zip(all_diff_lines, isvalid_list):
                if valid:
                    diff_lines.append(line)
                elif prev:
                    if False:
                        diff_lines.append(visual_break)
                prev = valid
        else:
            diff_lines = [
                line for line, flag in zip(all_diff_lines, isvalid_list) if flag
            ]
    text = "\n".join(diff_lines)
    if colored:
        text = highlight_code(text, lexer_name="diff")
    return text


def highlight_code(text, lexer_name="python", **kwargs):
    """
    Highlights a block of text using ANSI tags based on language syntax.

    Args:
        text (str): plain text to highlight
        lexer_name (str): name of language. eg: python, docker, c++
        **kwargs: passed to pygments.lexers.get_lexer_by_name

    Returns:
        str: text - highlighted text
            If pygments is not installed, the plain text is returned.

    Example:
        >>> text = 'import mkinit; print(mkinit)'
        >>> new_text = highlight_code(text)
        >>> print(new_text)
    """
    if NO_COLOR:
        return text
    # Resolve extensions to languages
    lexer_name = {
        "py": "python",
        "h": "cpp",
        "cpp": "cpp",
        "cxx": "cpp",
        "c": "cpp",
    }.get(lexer_name.replace(".", ""), lexer_name)
    try:
        import pygments
        import pygments.lexers
        import pygments.formatters
        import pygments.formatters.terminal

        if sys.platform.startswith("win32"):  # nocover
            # Hack on win32 to support colored output
            import colorama

            colorama.init()

        formater = pygments.formatters.terminal.TerminalFormatter(bg="dark")
        lexer = pygments.lexers.get_lexer_by_name(lexer_name, **kwargs)
        new_text = pygments.highlight(text, lexer, formater)

    except ImportError:  # nocover
        import warnings

        warnings.warn("pygments is not installed, code will not be highlighted")
        new_text = text
    return new_text
