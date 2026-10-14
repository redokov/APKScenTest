# -*- coding: utf-8 -*-
"""T8: собрать Stage-A раннер-EPF (tmp/t8/runner_src/АпкРаннер).

Копирует гейт-EPF (tmp/t3/gate_src/ГейтАпк, внутреннее имя НЕ меняется)
и подставляет модуль формы-раннера (tmp/t8/runner_module_src.bsl ->
utf-8-sig + CRLF). Аналог scripts/make_t7_runner.py.
"""
import shutil
import sys
from pathlib import Path

PROJECT = Path(r"C:\MyProjects\APKScenTest")
SRC_DIR = PROJECT / "tmp" / "t3" / "gate_src" / "ГейтАпк"
SRC_XML = PROJECT / "tmp" / "t3" / "gate_src" / "ГейтАпк.xml"
MOD = PROJECT / "tmp" / "t8" / "runner_module_src.bsl"
DST_DIR = PROJECT / "tmp" / "t8" / "runner_src" / "АпкРаннер"
DST_XML = PROJECT / "tmp" / "t8" / "runner_src" / "АпкРаннер.xml"


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
    print("[OK] T8 runner source ready: tmp/t8/runner_src/АпкРаннер.*")
    return 0


if __name__ == "__main__":
    sys.exit(main())
