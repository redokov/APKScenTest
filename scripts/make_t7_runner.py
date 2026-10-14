# -*- coding: utf-8 -*-
"""T7 Gate: собрать T7-раннер-EPF (tmp/t7/runner_src/АпкРаннер).

Копирует гейт-EPF (tmp/t3/gate_src/ГейтАпк, внутреннее имя НЕ меняется)
и подставляет модуль формы-раннера (tmp/t7/runner_module_src.bsl ->
utf-8-sig + CRLF). Аналог scripts/make_t4_runner.py.
"""
import shutil
import sys
from pathlib import Path

PROJECT = Path(r"C:\MyProjects\APKScenTest")
SRC_DIR = PROJECT / "tmp" / "t3" / "gate_src" / "ГейтАпк"
SRC_XML = PROJECT / "tmp" / "t3" / "gate_src" / "ГейтАпк.xml"
MOD = PROJECT / "tmp" / "t7" / "runner_module_src.bsl"
DST_DIR = PROJECT / "tmp" / "t7" / "runner_src" / "АпкРаннер"
DST_XML = PROJECT / "tmp" / "t7" / "runner_src" / "АпкРаннер.xml"


def main() -> int:
    for p in (SRC_DIR, SRC_XML, MOD):
        if not p.exists():
            print("[FAIL] not found: %s" % p)
            return 1
    if DST_DIR.exists():
        shutil.rmtree(DST_DIR)
    DST_DIR.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SRC_DIR, DST_DIR)
    shutil.copyfile(SRC_XML, DST_XML)

    text = MOD.read_text(encoding="utf-8")
    text = text.replace("\r\n", "\n").replace("\n", "\r\n")
    mod = DST_DIR / "Forms" / "Форма" / "Ext" / "Form" / "Module.bsl"
    mod.write_text(text, encoding="utf-8-sig", newline="")
    print("[OK] T7 runner source ready: tmp/t7/runner_src/АпкРаннер.*")
    return 0


if __name__ == "__main__":
    sys.exit(main())
