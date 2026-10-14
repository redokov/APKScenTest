# -*- coding: utf-8 -*-
"""Fix tab count in t8_f1_value_map.py (7 -> 6 tabs), Cyrillic-safe (regex, no Cyrillic literals)."""
import io
import re

P = r"c:\MyProjects\APKScenTest\scripts\t8_f1_value_map.py"
s = io.open(P, encoding="utf-8").read()

def fix(m):
    return m.group(0).replace("\\t\\t\\t\\t\\t\\t\\t", "\\t\\t\\t\\t\\t\\t")

s2 = re.sub(r'"\\t\\t\\t\\t\\t\\t\\t[^"]*"', fix, s)
io.open(P, "w", encoding="utf-8", newline="").write(s2)
print("7-tab occurrences left:", s2.count('"\\t\\t\\t\\t\\t\\t\\t'))
