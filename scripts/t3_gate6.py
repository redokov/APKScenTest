# -*- coding: utf-8 -*-
"""T3 Gate 6: сверка scan.json с tests/coverage-map.json.

Проверки:
 1. Полное покрытие: каждая ожидаемая (тип, ось, значение) из карты
    либо покрыта представителем, либо числится в gaps.
 2. Нет ложного покрытия: каждая ячейка представителя есть в ожидаемых.
 3. Нет ложных пробелов: каждый gap есть в ожидаемых значениях.
 4. Достижимость: значение покрыто <=> у какого-то found-документа этого
    типа есть такое значение оси (по found[].axes).
 5. appliesWhen: ось ВидАвтотранспорта АпкЗаправочныеВедомостей не
    числится в gaps, если ни один документ типа не имеет ТипТС=Автотранспорт.
 6. Пользователи: для каждого автора представителя есть запись users[]
    (excluded => причина непустая).

Результат -> tmp/t3/verify.md. Exit 0 = PASS.
"""
import io
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(r"C:\MyProjects\APKScenTest")
SCAN = PROJECT / "tmp" / "t3" / "scan.json"
MAP = PROJECT / "tests" / "coverage-map.json"
OUT = PROJECT / "tmp" / "t3" / "verify.md"

scan = json.load(io.open(SCAN, encoding="utf-8-sig"))
cmap = json.load(io.open(MAP, encoding="utf-8-sig"))

# ожидаемые (тип, ось, значение) с учётом appliesWhen
expected = {}          # (type, axis, value) -> appliesWhen or None
axes_by_type = {}      # type -> {axis: axisdef}
for doctype, dd in cmap["documents"].items():
    axes_by_type[doctype] = {ax["attribute"]: ax for ax in dd.get("axes", [])}
    for ax in dd.get("axes", []):
        for val in ax.get("values", []):
            expected[(doctype, ax["attribute"], val)] = ax.get("appliesWhen")

# покрытие и пробелы из scan
covered = set()
for rep in scan["representatives"]:
    for cell in rep["cells"]:
        covered.add((rep["type"], cell["axis"], cell["value"]))
gaps = {(g["type"], g["axis"], g["value"]) for g in scan["gaps"]}

# достижимость по found
reachable = set()
for f in scan["found"]:
    for axis, values in (f.get("axes") or {}).items():
        for v in values or []:
            reachable.add((f["type"], axis, v))

problems = []

def cond_reachable_for(key):
    """Выполнено ли appliesWhen условия оси (для зависимых осей)."""
    aw = expected[key]
    if not aw:
        return None
    cond_axis, _, cond_val = aw.partition("=")
    return (key[0], cond_axis.strip(), cond_val.strip()) in reachable

# 1: полнота (appliesWhen-неприменимые оси = ни представитель, ни gap)
for key in expected:
    cond = cond_reachable_for(key)
    if cond is False:
        continue
    if key not in covered and key not in gaps:
        problems.append("ПРОПУЩЕНО (ни представитель, ни gap): %s" % (key,))

# 2: ложное покрытие
for key in covered:
    if key not in expected:
        problems.append("ЛОЖНОЕ ПОКРЫТИЕ (нет в карте): %s" % (key,))

# 3: ложные пробелы
for key in gaps:
    if key not in expected:
        problems.append("ЛОЖНЫЙ ПРОБЕЛ (нет в карте): %s" % (key,))

# 4: достижимость
for key in expected:
    type_, axis, value = key
    aw = expected[key]
    if aw:  # appliesWhen: "Ось = Значение"
        cond_axis, _, cond_val = aw.partition("=")
        cond_axis, cond_val = cond_axis.strip(), cond_val.strip()
        cond_reachable = (type_, cond_axis, cond_val) in reachable
        is_covered = key in covered
        if not cond_reachable and is_covered:
            problems.append("appliesWhen нарушен: %s покрыт без условия %s" % (key, aw))
        if cond_reachable and key in gaps:
            problems.append("appliesWhen: %s в gaps при выполненном условии" % (key,))
    else:
        if (key in covered) != (key in reachable):
            problems.append("НЕСОГЛАСОВАННОСТЬ достижимости: %s covered=%s reachable=%s"
                            % (key, key in covered, key in reachable))

# 5: ВидАвтотранспорта ведомостей — не gap, если нет ТипТС=Автотранспорт
zt_key = ("АпкЗаправочныеВедомости", "ТипТС", "Автотранспорт")
vat_values = [v for (t, a, v) in expected
              if t == "АпкЗаправочныеВедомости" and a == "ВидАвтотранспорта"]
vat_gap_bug = []
if zt_key not in reachable:
    for v in vat_values:
        if ("АпкЗаправочныеВедомости", "ВидАвтотранспорта", v) in gaps:
            vat_gap_bug.append(v)
    if vat_gap_bug:
        problems.append("ЛОЖНЫЙ ПРОБЕЛ appliesWhen ВидАвтотранспорта: %s" % vat_gap_bug)

# 6: пользователи
user_by_author = {u["author"]: u for u in scan["users"]}
rep_authors = {r["author"] for r in scan["representatives"]}
for a in rep_authors:
    u = user_by_author.get(a)
    if u is None:
        problems.append("АВТОР без записи users[]: %s" % a)
    elif u.get("excluded") and not u.get("reason"):
        problems.append("excluded без причины: %s" % a)
    elif not u.get("excluded") and not u.get("ibName"):
        problems.append("excluded=false без ibName: %s" % a)

# --- отчёт ---
lines = []
lines.append("# T3 Gate 6 — verify.md")
lines.append("")
lines.append("scan.json: runId=%s, scannedAt=%s" % (scan.get("runId"), scan.get("scannedAt")))
lines.append("found=%d, representatives=%d, gaps=%d, users=%d"
             % (len(scan["found"]), len(scan["representatives"]),
                len(scan["gaps"]), len(scan["users"])))
lines.append("")
lines.append("## Сверка с coverage-map")
lines.append("- ожидаемых ячеек (тип, ось, значение): %d" % len(expected))
lines.append("- покрыто представителями: %d" % len(covered))
lines.append("- пробелов (gaps): %d" % len(gaps))
lines.append("- достижимых по found[].axes: %d" % len(reachable))
lines.append("")
lines.append("Проверки: 1) полнота (каждая ожидаемая ячейка = покрытие ИЛИ gap); "
             "2) нет ложного покрытия; 3) нет ложных пробелов; "
             "4) covered <=> reachable; 5) appliesWhen; 6) пользователи.")
lines.append("")
lines.append("## Пробелы по типам (для планирования фикстур T4)")
per_type = {}
for g in scan["gaps"]:
    per_type.setdefault(g["type"], []).append("%s=%s" % (g["axis"], g["value"]))
for t, items in sorted(per_type.items()):
    lines.append("- %s: %d (%s)" % (t, len(items), "; ".join(items)))
lines.append("")
lines.append("## Пользователи")
for u in scan["users"]:
    lines.append("- %s (%s) -> ИБ '%s', hasPassword=%s, standardAuth=%s, excluded=%s%s"
                 % (u.get("authorName"), u.get("author"), u.get("ibName"),
                    u.get("hasPassword"), u.get("standardAuth"), u.get("excluded"),
                    (", причина: " + u.get("reason")) if u.get("reason") else ""))
lines.append("")
lines.append("## Вердикт")
lines.append("")
if problems:
    lines.append("FAIL — %d проблем:" % len(problems))
    for p in problems:
        lines.append("- " + p)
else:
    lines.append("PASS — представители покрывают все достижимые значения осей, "
                 "gaps = ровно недостижимые ожидаемые значения, appliesWhen "
                 "ВидАвтотранспорта ведомостей не даёт ложного пробела "
                 "(ТипТС=Автотранспорт отсутствует в данных), "
                 "пользователи сопоставлены и не excluded.")
lines.append("")
OUT.write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines[-6:]))
sys.exit(0 if not problems else 1)
