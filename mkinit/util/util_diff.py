def difftext(text1, text2, context_lines=0, ignore_whitespace=False,
             colored=False):
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
    import ubelt as ub
    import difflib
    text1 = ub.ensure_unicode(text1)
    text2 = ub.ensure_unicode(text2)
    text1_lines = text1.splitlines()
    text2_lines = text2.splitlines()
    if ignore_whitespace:
        text1_lines = [t.rstrip() for t in text1_lines]
        text2_lines = [t.rstrip() for t in text2_lines]
        ndiff_kw = dict(linejunk=difflib.IS_LINE_JUNK,
                        charjunk=difflib.IS_CHARACTER_JUNK)
    else:
        ndiff_kw = {}
    all_diff_lines = list(difflib.ndiff(text1_lines, text2_lines, **ndiff_kw))

    if context_lines is None:
        diff_lines = all_diff_lines
    else:
        # boolean for every line if it is marked or not
        ismarked_list = [len(line) > 0 and line[0] in '+-?'
                         for line in all_diff_lines]
        # flag lines that are within context_lines away from a diff line
        isvalid_list = ismarked_list[:]
        for i in range(1, context_lines + 1):
            isvalid_list[:-i] = list(map(any, zip(
                isvalid_list[:-i], ismarked_list[i:])))
            isvalid_list[i:] = list(map(any, zip(
                isvalid_list[i:], ismarked_list[:-i])))

        USE_BREAK_LINE = True
        if USE_BREAK_LINE:
            # insert a visual break when there is a break in context
            diff_lines = []
            prev = False
            visual_break = '\n <... FILTERED CONTEXT ...> \n'
            #print(isvalid_list)
            for line, valid in zip(all_diff_lines, isvalid_list):
                if valid:
                    diff_lines.append(line)
                elif prev:
                    if False:
                        diff_lines.append(visual_break)
                prev = valid
        else:
            diff_lines = list(ub.compress(all_diff_lines, isvalid_list))
    text = '\n'.join(diff_lines)
    if colored:
        text = ub.highlight_code(text, lexer_name='diff')
    return text
