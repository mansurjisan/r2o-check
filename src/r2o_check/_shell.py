"""Shell text utilities for rule parsers.

Small helpers used by rules that pattern-match against shell-script
text. Not a full shell parser — scope is limited to preventing
commented-out code from satisfying compliance checks.
"""

from __future__ import annotations


def strip_shell_comments(content: str) -> str:
    """Remove shell comments while preserving the shebang.

    Handles single- and double-quoted strings so a ``#`` inside a
    string literal is not treated as a comment. The very first line
    is left intact if it begins with ``#!`` so shebangs survive.
    """
    lines = content.split("\n")
    out: list[str] = []
    for idx, line in enumerate(lines):
        if idx == 0 and line.startswith("#!"):
            out.append(line)
            continue
        out.append(_strip_line_comment(line))
    return "\n".join(out)


def _strip_line_comment(line: str) -> str:
    in_single = False
    in_double = False
    i = 0
    n = len(line)
    while i < n:
        ch = line[i]
        if ch == "\\" and i + 1 < n and not in_single:
            i += 2
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            if i == 0 or line[i - 1].isspace():
                return line[:i].rstrip()
        i += 1
    return line
