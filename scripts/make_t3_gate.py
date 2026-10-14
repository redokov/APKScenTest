# -*- coding: utf-8 -*-
"""T3 Gate 4: подготовить исходники гейт-EPF под APKScenTest.

Копирует generic-гейт (TabDocLoad build/probe_src/ЗондГейт)
Компилирует generic-гейт с ИСПРАВЛЕННЫМ паттерном колбэка
(build/probe_src/ЗондГейт: состояние через ДополнительныеПараметры —
модульная переменная формы в 8.5.4 НЕ видна из колбэка) в
tmp/t3/gate_src/ГейтАпк и делает byte-замены путей:
  - файл-цель:  C:\\MyProjects\\TabDocLoad\\build\\test\\gate_target.txt
                -> C:\\MyProjects\\APKScenTest\\tmp\\t3\\gate_target.txt
  - отчёт:      C:/MyProjects/TabDocLoad/build/test/compile_check.json
                -> C:/MyProjects/APKScenTest/tmp/t3/compile_check.json
  - лог шагов:  C:/MyProjects/TabDocLoad/build/test/checker_steps.log
                -> C:/MyProjects/APKScenTest/tmp/t3/gate_steps.log

Внутреннее имя обработки КомпиляторГейт НЕ меняется (8.5 отклоняет
переименованный корень XML); меняются только имена файла/каталога.
"""
import shutil
import sys
from pathlib import Path

PROJECT = Path(r"C:\MyProjects\APKScenTest")
SRC_DIR = Path(r"C:\MyProjects\TabDocLoad\build\probe_src\ЗондГейт")
SRC_XML = Path(r"C:\MyProjects\TabDocLoad\build\probe_src\ЗондГейт.xml")
DST_DIR = PROJECT / "tmp" / "t3" / "gate_src" / "ГейтАпк"
DST_XML = PROJECT / "tmp" / "t3" / "gate_src" / "ГейтАпк.xml"

REPLACEMENTS = [
    (r"C:\MyProjects\TabDocLoad\build\test\gate_target.txt",
     r"C:\MyProjects\APKScenTest\tmp\t3\gate_target.txt"),
    ("C:/MyProjects/TabDocLoad/build/test/probe_gate.json",
     "C:/MyProjects/APKScenTest/tmp/t3/compile_check.json"),
    ("C:/MyProjects/TabDocLoad/build/test/probe_gate_steps.log",
     "C:/MyProjects/APKScenTest/tmp/t3/gate_steps.log"),
]


def main() -> int:
    for p in (SRC_DIR, SRC_XML):
        if not p.exists():
            print("[FAIL] source not found: %s" % p)
            return 1
    if DST_DIR.exists():
        shutil.rmtree(DST_DIR)
    DST_DIR.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SRC_DIR, DST_DIR)
    shutil.copyfile(SRC_XML, DST_XML)

    mod = DST_DIR / "Forms" / "Форма" / "Ext" / "Form" / "Module.bsl"
    text = mod.read_text(encoding="utf-8-sig")
    for old, new in REPLACEMENTS:
        n = text.count(old)
        if n != 1:
            print("[FAIL] expected 1 occurrence of %r, found %d" % (old, n))
            return 1
        text = text.replace(old, new)
    mod.write_text(text, encoding="utf-8-sig")
    print("[OK] gate source ready: tmp/t3/gate_src/ГейтАпк.*")
    return 0


if __name__ == "__main__":
    sys.exit(main())
