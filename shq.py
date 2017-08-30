#!/usr/bin/env python
def shellquote_perfect(s):
    return "'" + s.replace("'", r"'\''") + "'"

shell_special_chars = set('[]{}()!*?|&;= \t\n\'"\\#`$<>~^')
shell_keywords = set(("do", "done", "while", "for", "if", "elif", "else",
                      "then", "fi", "until", "select", "case", "esac",
                      "function", "time", "", "coproc", "in"))

def shellquote_optimal(s):
    if not s:
        return "''"
    if s in shell_keywords:
        return "\\" + s
    quoting = False
    out = ""
    for ind, char in enumerate(s):
        if char == "'":
            if quoting:
                quoting = False
                out += "'"
            out += "\\"
        elif char in shell_special_chars:
            if not quoting:
                if char == '\n':
                    found_special = True
                else:
                    found_special = False
                    for c2 in s[ind+1:]:
                        if c2 == "'":
                            break
                        elif c2 in shell_special_chars:
                            found_special = True
                            break
                if found_special:
                    quoting = True
                    out += "'"
                else:
                    out += "\\"
        out += char
    if quoting:
        out += "'"
    return out
