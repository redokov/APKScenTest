# -*- coding: utf-8 -*-
"""T5 Gate 5: verification of generated .feature files.

Checks (result -> tmp/t5/verify.md):
  - files generated per (user x template), exact filenames (latin, D-002);
  - no unreplaced "{{" placeholders in generated files;
  - smoke features identical to the etalon tests/features/smoke-01-connect.feature;
  - form titles == metadata synonyms (cross-checked against APKModSrc XML);
  - date substituted with current month;
  - fixture data present in the scenario (numbers, presentations);
  - manifest valid; warnings == expected missing templates only;
  - encoding UTF-8 (no BOM), LF endings (as etalon).
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(r"C:\MyProjects\APKScenTest")
RUN = PROJECT / "tests" / "run-20261011-233413"
FEATURES = RUN / "features"
MANIFEST = RUN / "features-manifest.json"
ETALON = PROJECT / "tests" / "features" / "smoke-01-connect.feature"
APK_META = Path(r"C:\MyProjects\APKModSrc") / "Documents" / "АпкПутевойЛистТракториста.xml"

checks = []


def check(name, ok, detail=""):
    checks.append((name, ok, detail))
    print(("[PASS] " if ok else "[FAIL] ") + name + (" — " + detail if detail else ""))


def read_feature(path):
    return path.read_bytes().decode("utf-8")


def main():
    today = date.today()
    expected_files = sorted([
        "00-smoke--Administrator-SokolovMI.feature",
        "00-smoke--Administrator-OrlovAV.feature",
        "01-pl-tractor--Administrator-OrlovAV.feature",
    ])
    files = sorted(p.name for p in FEATURES.glob("*.feature"))
    check("feature files exist exactly as expected", files == expected_files,
          "; ".join(files))

    # --- 1. no unreplaced placeholders ---
    total_braces = 0
    for name in files:
        text = read_feature(FEATURES / name)
        total_braces += text.count("{{")
    check("no unreplaced {{ }} placeholders (grep = 0)", total_braces == 0,
          "total {{ occurrences: %d" % total_braces)

    # --- 2. smoke files identical to etalon (byte-exact) ---
    etalon = ETALON.read_bytes()
    smoke_ok = True
    for name in expected_files:
        if not name.startswith("00-smoke"):
            continue
        if (FEATURES / name).read_bytes() != etalon:
            smoke_ok = False
    check("smoke features identical to etalon syntax", smoke_ok,
          "00-smoke files compared byte-exact to tests/features/smoke-01-connect.feature")

    # --- 3. form title from metadata synonyms ---
    meta_xml = APK_META.read_text(encoding="utf-8-sig")
    m = re.search(
        r"<Synonym>.*?<v8:lang>ru</v8:lang>\s*<v8:content>([^<]+)</v8:content>",
        meta_xml, re.S)
    synonym = m.group(1) if m else None
    check("metadata synonym extracted from APKModSrc", bool(synonym),
          "synonym: %s" % synonym)
    tractor_text = read_feature(FEATURES / "01-pl-tractor--Administrator-OrlovAV.feature")
    check("form title == metadata synonym", ('"%s*"' % synonym) in tractor_text,
          'expected window title: "%s*"' % synonym)

    # --- 4. current month date ---
    expected_date = today.strftime("%d.%m.%Y")
    check("date substituted with current month",
          ('я ввожу текст "%s"' % expected_date) in tractor_text,
          "expected: %s" % expected_date)

    # --- 5. fixture data present ---
    fixtures = json.loads((RUN / "fixtures.json").read_text(encoding="utf-8-sig"))
    pl_doc = [d for d in fixtures["documents"]
              if d["type"] == "АпкПутевойЛистТракторista".replace("ista", "истa")][:]
    pl_doc = [d for d in fixtures["documents"]
              if d["type"] == "АпкПутевойЛистТракториста"][0]
    header = pl_doc["data"]["header"]
    expected_values = [
        header["Организация"]["presentation"],
        header["Подразделение"]["presentation"],
        header["Техника"]["presentation"],
        header["Механизатор"]["presentation"],
        str(header["МоточасовПриВыезде"]),
        "0",  # МоточасовПриВозвращении = 0
    ]
    values_ok = all(v in tractor_text for v in expected_values)
    check("fixture header values substituted", values_ok,
          "; ".join(expected_values))
    check("flag НачислятьЗП=true -> устанавливаю",
          'я устанавливаю флаг "НачислятьЗП"' in tractor_text)
    check("numeric zero rendered as \"0\" (not empty)",
          'МоточасовПриВозвращении" я ввожу текст "0"' in tractor_text)
    check("decimal comma formatting (31,5)",
          'я ввожу текст "31,5"' in tractor_text)
    check("scenario title contains source number",
          "путевого листа тракториста НВ00-000001" in tractor_text)

    # ТЧ rows
    check("ГСМ row: МаркаТоплива presentation",
          'ГСММаркаТоплива" я выбираю по строке "Дизельное топливо"' in tractor_text)
    check("Заправки row: Источник presentation",
          'ЗаправкиИсточник" я выбираю по строке "Склад ГСМ"' in tractor_text)
    check("ВыполненныеРаботы row: enum exact value",
          'ВыполненныеРаботыТипЗатрат" я выбираю точное значение "Прямые затраты"'
          in tractor_text)
    check("empty ТЧ (Задание) produced no steps",
          "ЗаданиеДобавить" not in tractor_text)

    # --- 6. scenario structure ---
    check("one Сценарий block in pl-tractor file",
          tractor_text.count("Сценарий:") == 1,
          "count: %d" % tractor_text.count("Сценарий:"))

    # --- 7. manifest ---
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    check("manifest valid, 3 files", len(manifest["files"]) == 3,
          "files: %d" % len(manifest["files"]))
    warnings = manifest.get("warnings", [])
    expected_warnings = {
        "04-fuel-sheet", "05-weighing", "02-pl-auto",
    }
    warning_names = {Path(w.split(": ")[-1]).stem for w in warnings}
    check("warnings == expected missing templates only",
          warning_names == expected_warnings,
          "; ".join(sorted(warning_names)))
    check("no unknown-placeholder warnings",
          not any("плейсхолдер" in w.lower() for w in warnings))

    # --- 8. encoding / line endings ---
    enc_ok = True
    for name in files:
        raw = (FEATURES / name).read_bytes()
        if raw.startswith(b"\xef\xbb\xbf") or b"\r\n" in raw:
            enc_ok = False
    check("UTF-8 no BOM, LF endings (as etalon)", enc_ok)

    # --- summary ---
    total = len(checks)
    failed = sum(1 for c in checks if not c[1])
    lines = ["# T5 verify — генератор feature-фич", ""]
    lines.append("Run-каталог: %s" % RUN)
    lines.append("Дата прогона: %s" % date.today().isoformat())
    lines.append("")
    lines.append("| # | Проверка | Результат | Комментарий |")
    lines.append("|---|----------|-----------|-------------|")
    for i, (name, ok, detail) in enumerate(checks, 1):
        lines.append("| %d | %s | %s | %s |" % (
            i, name, "PASS" if ok else "FAIL", detail.replace("|", "/")))
    lines.append("")
    lines.append("**Итог: %d проверок, %d FAIL**" % (total, failed))
    lines.append("")
    lines.append("## Ожидаемое поведение (не ошибки)")
    lines.append("- arm-* и 02/04/05-шаблоны ещё не созданы (T5 scope: smoke + pl-tractor),")
    lines.append("  отсутствие = предупреждение в манифесте, файлы не генерируются.")
    lines.append("- АРМ-шаблоны (arm-*) не резолвятся через ТипДокументаШаблона — они не")
    lines.append("  являются шаблонами типов документов карты; генерация для них будет")
    lines.append("  добавлена в последующих задачах при создании АРМ-шаблонов.")
    verify_path = PROJECT / "tmp" / "t5" / "verify.md"
    verify_path.write_text("\n".join(lines), encoding="utf-8")
    print("\n%d checks, %d FAIL -> %s" % (total, failed, verify_path))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
