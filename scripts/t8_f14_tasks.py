# -*- coding: utf-8 -*-
# t8-finish-14: отметить чекбоксы T8 в tasks.md (E2E PASS 2026-10-15).
import io

SRC = r"c:\MyProjects\APKScenTest\.ai\sdd\specs\001-preprocessor-epf\tasks.md"
src = io.open(SRC, encoding="utf-8").read()

edits = [
    ("- [ ] Полный цикл на dev_erpapk_demo: скан → план",
     "- [x] Полный цикл на dev_erpapk_demo: скан → план"),
    ("- [ ] Проверка: восстановление паролей всех пользователей плана",
     "- [x] Проверка: восстановление паролей всех пользователей плана"),
    ("- [ ] ReturnStatus=0 на батчах; summary.md с «passed»; пароли исходные работают",
     "- [x] ReturnStatus=0 на батчах; summary.md с «passed»; пароли исходные работают"),
    ("- [ ] Журнал прогона + summary в run-каталоге; фиксация в отчёте ночи",
     "- [x] Журнал прогона + summary в run-каталоге; фиксация в отчёте ночи"),
]

for o, n in edits:
    assert src.count(o) == 1, "anchor not found: " + o[:40]
    src = src.replace(o, n)

io.open(SRC, "w", encoding="utf-8", newline="").write(src)
print("[ok] 4 T8 checkboxes checked")
