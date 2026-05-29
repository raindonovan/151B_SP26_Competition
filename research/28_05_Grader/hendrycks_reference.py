"""
Hendrycks math_equivalence.py — EXACT reproduction from SHA b5c066f.
Use this to test format hypotheses before burning a submission.

Usage:
    from hendrycks_reference import is_equiv, _strip_string
    
    # Test if two answers are equivalent under Hendrycks grader
    is_equiv("0.5", "\\frac{1}{2}")  # True
    is_equiv("1.50", "1.5")          # False (trailing zeros not normalized)
    
    # See what normalization does to a string
    _strip_string("y = 5x^4")        # "5x^4"
"""

def _fix_fracs(string):
    substrs = string.split("\\frac")
    new_str = substrs[0]
    if len(substrs) > 1:
        substrs = substrs[1:]
        for substr in substrs:
            new_str += "\\frac"
            if substr[0] == "{":
                new_str += substr
            else:
                try:
                    assert len(substr) >= 2
                except:
                    return string
                a = substr[0]
                b = substr[1]
                if b != "{":
                    if len(substr) > 2:
                        post_substr = substr[2:]
                        new_str += "{" + a + "}{" + b + "}" + post_substr
                    else:
                        new_str += "{" + a + "}{" + b + "}"
                else:
                    if len(substr) > 2:
                        post_substr = substr[2:]
                        new_str += "{" + a + "}" + b + post_substr
                    else:
                        new_str += "{" + a + "}" + b
    string = new_str
    return string

def _fix_a_slash_b(string):
    if len(string.split("/")) != 2:
        return string
    a = string.split("/")[0]
    b = string.split("/")[1]
    try:
        a = int(a)
        b = int(b)
        assert string == "{}/{}".format(a, b)
        new_string = "\\frac{" + str(a) + "}{" + str(b) + "}"
        return new_string
    except:
        return string

def _remove_right_units(string):
    if "\\text{ " in string:
        splits = string.split("\\text{ ")
        assert len(splits) == 2
        return splits[0]
    else:
        return string

def _fix_sqrt(string):
    if "\\sqrt" not in string:
        return string
    splits = string.split("\\sqrt")
    new_string = splits[0]
    for split in splits[1:]:
        if split[0] != "{":
            a = split[0]
            new_substr = "\\sqrt{" + a + "}" + split[1:]
        else:
            new_substr = "\\sqrt" + split
        new_string += new_substr
    return new_string

def _strip_string(string):
    # Step 1: linebreaks
    string = string.replace("\n", "")
    # Step 2: inverse spaces
    string = string.replace("\\!", "")
    # Step 3: double backslash
    string = string.replace("\\\\", "\\")
    # Step 4: tfrac/dfrac
    string = string.replace("tfrac", "frac")
    string = string.replace("dfrac", "frac")
    # Step 5: left/right
    string = string.replace("\\left", "")
    string = string.replace("\\right", "")
    # Step 6: degrees
    string = string.replace("^{\\circ}", "")
    string = string.replace("^\\circ", "")
    # Step 7: dollar signs
    string = string.replace("\\$", "")
    # Step 8: units
    string = _remove_right_units(string)
    # Step 9: percent (NOTE: bare % is NOT removed, only \%)
    string = string.replace("\\%", "")
    string = string.replace("\%", "")
    # Step 10: leading zeros before decimals
    string = string.replace(" .", " 0.")
    string = string.replace("{.", "{0.")
    if len(string) == 0:
        return string
    if string[0] == ".":
        string = "0" + string
    # Step 11: equation prefix strip (LHS <= 2 chars, exactly one =)
    if len(string.split("=")) == 2:
        if len(string.split("=")[0]) <= 2:
            string = string.split("=")[1]
    # Step 12: sqrt fix
    string = _fix_sqrt(string)
    # Step 13: ALL spaces removed
    string = string.replace(" ", "")
    # Step 14: frac fix
    string = _fix_fracs(string)
    # Step 15: 0.5 hardcode (STANDALONE only)
    if string == "0.5":
        string = "\\frac{1}{2}"
    # Step 16: a/b fix (STANDALONE integers only)
    string = _fix_a_slash_b(string)
    return string

def is_equiv(str1, str2, verbose=False):
    if str1 is None and str2 is None:
        print("WARNING: Both None")
        return True
    if str1 is None or str2 is None:
        return False
    try:
        ss1 = _strip_string(str1)
        ss2 = _strip_string(str2)
        if verbose:
            print(ss1, ss2)
        return ss1 == ss2
    except:
        return str1 == str2


if __name__ == "__main__":
    # Quick sanity tests
    tests = [
        ("\\dfrac{1}{2}", "\\frac{1}{2}", True, "dfrac→frac"),
        ("0.5", "\\frac{1}{2}", True, "0.5 hardcode"),
        ("3/5", "\\frac{3}{5}", True, "slash standalone"),
        ("3/5, 7", "\\frac{3}{5}, 7", False, "slash in multi-answer (WON'T convert)"),
        ("0.5, 3", "\\frac{1}{2}, 3", False, "0.5 in multi-answer (WON'T convert)"),
        ("-\\frac{2}{3}", "\\frac{-2}{3}", False, "negative sign placement"),
        ("1.50", "1.5", False, "trailing zeros"),
        ("\\text{A}", "A", False, "text wrap preserved"),
        ("x=5", "5", True, "equation prefix stripped"),
        ("Mean=228", "228", False, "long prefix NOT stripped"),
    ]
    
    all_pass = True
    for s1, s2, expected, desc in tests:
        result = is_equiv(s1, s2)
        status = "PASS" if result == expected else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"  {status}: {desc} — is_equiv('{s1}', '{s2}') = {result} (expected {expected})")
    
    print(f"\n{'All tests passed!' if all_pass else 'SOME TESTS FAILED'}")
