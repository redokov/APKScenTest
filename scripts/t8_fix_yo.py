# -*- coding: utf-8 -*-
"""T8: убрать букву "ё" из нового BSL-кода (std474)."""
import io
import re

P = r"c:\MyProjects\APKScenTest\src\АпкПодготовкаСценарныхТестов\Ext\ObjectModule.bsl"
src = io.open(P, encoding="utf-8").read()

repl = [
    ("Отображённое", "Отображенное"),
    ("отображённым", "отображенным"),
    ("отображённое", "отображенное"),
]
for a, b in repl:
    src = src.replace(a, b)

io.open(P, "w", encoding="utf-8", newline="").write(src)
yos = re.findall(r"[а-яё]*ё[а-яё]*", src)
print("remaining y0-words:", set(yos))
