# -*- coding: utf-8 -*-
"""T4 Gate 5: python-сверка fixtures.json с контрактом §3.2 design.md.

Проверяет: ключи контракта, runId, представители == scan.json,
header/tabular по fieldList карты, armPlan учитывает arms.when,
users[].scenarios, булевы значения, отсутствие дат (D-005).
Итог -> tmp/t4/verify.md. Exit 0 = PASS.
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(r"C:\MyProjects\APKScenTest")
RUN_DIR = PROJECT / "tests" / "run-20261011-233413"
FIXTURES_RUN = RUN_DIR / "fixtures.json"
FIXTURES_T4 = PROJECT / "tmp" / "t4" / "fixtures.json"
SCAN = PROJECT / "tmp" / "t3" / "scan.json"
COVMAP = PROJECT / "tests" / "coverage-map.json"
OUT = PROJECT / "tmp" / "t4" / "verify.md"

REQUIRED_KEYS = ["runId", "filters", "common", "users", "documents",
                 "armPlan", "coverageGaps"]
ALLOWED_EXTRA = {"generatedAt", "skippedDocs"}

lines = []
fails = []


def section(title):
    lines.append("\n## " + title)


def check(name, ok, detail=""):
    mark = "OK " if ok else "FAIL"
    if not ok:
        fails.append(name)
    line = "- [%s] %s" % (mark, name)
    if detail:
        line += " — " + detail
    lines.append(line)


def main() -> int:
    fx = json.loads(FIXTURES_T4.read_text(encoding="utf-8-sig"))
    scan = json.loads(SCAN.read_text(encoding="utf-8-sig"))
    cmap = json.loads(COVMAP.read_text(encoding="utf-8-sig"))

    lines.append("# T4 Gate 5 — сверка fixtures.json (§3.2 design.md)\n")
    lines.append("run: %s" % RUN_DIR)

    # 1. файлы
    section("1. Артефакты")
    check("run-каталог fixtures.json существует", FIXTURES_RUN.exists())
    check("tmp/t4 копия byte-identical",
          FIXTURES_RUN.read_bytes() == FIXTURES_T4.read_bytes())

    # 2. ключи контракта
    section("2. Ключи контракта §3.2")
    top = set(fx.keys())
    missing = [k for k in REQUIRED_KEYS if k not in top]
    extra = top - set(REQUIRED_KEYS) - ALLOWED_EXTRA
    check("обязательные ключи на месте", not missing,
          "missing: %s" % missing if missing else str(REQUIRED_KEYS))
    check("только допустимые доп. ключи (%s)" % sorted(ALLOWED_EXTRA),
          not extra, "неожиданные: %s" % sorted(extra))
    check("runId == runId scan.json", fx["runId"] == scan.get("runId"),
          "%s vs scan %s" % (fx.get("runId"), scan.get("runId")))
    check("runId соответствует каталогу прогона",
          RUN_DIR.name.endswith(str(fx.get("runId"))))

    # 3. представители
    section("3. Представители соответствуют scan.json")
    reps = scan.get("representatives", [])
    scan_keys = sorted((r["type"], r["ref"]) for r in reps)
    fx_keys = sorted((d["type"], d["ref"]) for d in fx["documents"])
    check("документы == представители scan (%d шт.)" % len(reps),
          scan_keys == fx_keys)
    by_type = {r["type"]: r for r in reps}
    for doc in fx["documents"]:
        rep = by_type.get(doc["type"])
        check("автор %s == scan" % doc["type"],
              rep is not None and doc["author"] == rep.get("author"))
        check("number %s заполнен" % doc["type"], bool(doc.get("number")))
        cov = doc.get("coverage")
        check("coverage %s — словарь осей" % doc["type"], isinstance(cov, dict))

    # 4. data по fieldList карты
    section("4. data.header / data.tabular по fieldList карты")
    for doc in fx["documents"]:
        dmap = cmap["documents"].get(doc["type"])
        if dmap is None:
            check("тип %s в карте" % doc["type"], False, "нет в карте")
            continue
        fl = dmap.get("fieldList", {})
        hdr_ok = fl.get("header", [])
        check("header %s ⊆ fieldList.header" % doc["type"],
              set(doc["data"]["header"]) <= set(hdr_ok),
              "лишние: %s" % sorted(set(doc["data"]["header"]) - set(hdr_ok)))
        for sect, rows in doc["data"]["tabular"].items():
            check("ТЧ %s.%s ⊆ fieldList.tabular" % (doc["type"], sect),
                  sect in fl.get("tabular", {}),
                  "секции карты: %s" % list(fl.get("tabular", {})))
            check("ТЧ %s.%s ≤ 3 строк" % (doc["type"], sect),
                  len(rows) <= 3, "%d строк" % len(rows))
        date_keys = [k for k in doc["data"]["header"]
                     if "дата" in k.lower() or "date" in k.lower()]
        check("даты НЕ сериализуются (D-005, %s)" % doc["type"],
              not date_keys, str(date_keys))

    # 5. armPlan учитывает arms.when
    section("5. armPlan учитывает arms.when")
    arms_planned = set()
    for row in fx["armPlan"]:
        arms_planned.add((row["user"], row["arm"]))
        for dt in row["docTypes"]:
            dmap = cmap["documents"].get(dt, {})
            arm_defs = {a["arm"]: a.get("when", "") for a in dmap.get("arms", [])}
            check("АРМ %s в карте для %s" % (row["arm"], dt),
                  row["arm"] in arm_defs)
    # условные АРМы: если when != always и ось не покрыта — их в плане быть не должно
    plan_str = json.dumps(fx["armPlan"], ensure_ascii=False)
    check("условный АРМ ПроизводстваПродукции (ТипЗатрат) не в плане, "
          "если ось не покрыта", "ПроизводстваПродукции" not in plan_str,
          "в плане нет ни одного представителя с покрытой осью ТипЗатрат")
    for row in fx["armPlan"]:
        for dt in row["docTypes"]:
            dmap = cmap["documents"].get(dt, {})
            when = {a["arm"]: a.get("when", "") for a in dmap.get("arms", [])}
            check("when %s: 'always' или ось представителя" % row["arm"],
                  when.get(row["arm"]) == "always" or row.get("reason"))

    # 6. users[].scenarios
    section("6. users[].scenarios")
    scan_users = [u for u in scan.get("users", [])
                  if not u.get("excluded", False)]
    scan_ib = sorted(u["ibName"] for u in scan_users)
    fx_ib = sorted(u["ibUser"] for u in fx["users"])
    check("users == не-excluded scan users (%d)" % len(scan_users),
          scan_ib == fx_ib, "%s vs %s" % (scan_ib, fx_ib))
    templates_map = {}
    for u in fx["users"]:
        check("scenarios %s непусты" % u["ibUser"], len(u["scenarios"]) > 0,
              str(u["scenarios"]))
        all_templates = set()
        for a in cmap["documents"].values():
            if a.get("template"):
                all_templates.add(a["template"])
            all_templates.update(x.get("template", "")
                                 for x in a.get("arms", [])
                                 if x.get("template"))
        unknown = [s for s in u["scenarios"] if s not in all_templates]
        check("scenarios %s из карты" % u["ibUser"], not unknown,
              "неизвестные: %s" % unknown)
        templates_map[u["ibUser"]] = set(u["scenarios"])

    # 7. armPlan.user сценарии arm-templates на месте
    section("7. arm-templates в сценариях")
    for row in fx["armPlan"]:
        tmpl = row.get("templates", [])
        check("templates АРМ %s в сценариях пользователя" % row["arm"],
              all(t in templates_map.get(row["user"], set()) for t in tmpl))

    # 8. прочее по контракту
    section("8. Прочее")
    check("common.organization заполнена", bool(fx["common"].get("organization")))
    check("common.subdivision заполнена", bool(fx["common"].get("subdivision")))
    check("filters — словарь", isinstance(fx["filters"], dict))
    check("generatedAt заполнен", bool(fx.get("generatedAt")),
          str(fx.get("generatedAt")))
    check("skippedDocs == 0", fx.get("skippedDocs") == 0)
    scan_gaps = len(scan.get("gaps", scan.get("coverageGaps", [])))
    check("coverageGaps (%d) совпадает с scan (%s)" % (len(fx["coverageGaps"]),
                                                      scan_gaps),
          len(fx["coverageGaps"]) == scan_gaps)

    lines.append("\n## Итог\n")
    lines.append("Checks: %d, FAIL: %d" % (
        len([l for l in lines if l.startswith("- [")]), len(fails)))
    if fails:
        lines.append("FAILED: " + "; ".join(fails))
        lines.append("\nRESULT: FAIL")
    else:
        lines.append("RESULT: PASS")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("FAILs:", len(fails))
    print("verify.md written")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
