# -*- coding: utf-8 -*-
"""T3 Gate 5: собрать гейт-раннер-EPF (tmp/t3/runner_src/АпкРаннер).

Копирует готовый гейт-гейт (tmp/t3/gate_src/ГейтАпк, внутреннее имя
КомпиляторГейт НЕ меняется) и подставляет модуль формы-раннера
(tmp/t3/runner_module_src.bsl, utf-8-sig + CRLF). Никаких byte-патчей —
модуль целиком наш.
"""
import sys
from pathlib import Path

PROJECT = Path(r"C:\MyProjects\APKScenTest")
SRC_DIR = PROJECT / "tmp" / "t3" / "gate_src" / "ГейтАпк"
SRC_XML = PROJECT / "tmp" / "t3" / "gate_src" / "ГейтАпк.xml"
MOD = PROJECT / "tmp" / "t3" / "runner_module_src.bsl"
DST_DIR = PROJECT / "tmp" / "t3" / "runner_src" / "АпкРаннер"
DST_XML = PROJECT / "tmp" / "t3" / "runner_src" / "АпкРаннер.xml"


def main() -> int:
    for p in (SRC_DIR, SRC_XML, MOD):
        if not p.exists():
            print("[FAIL] not found: %s" % p)
            return 1
    if DST_DIR.exists():
        import shutil
        shutil.rmtree(DST_DIR)
    import shutil
    DST_DIR.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SRC_DIR, DST_DIR)
    shutil.copyfile(SRC_XML, DST_XML)

    text = MOD.read_text(encoding="utf-8-sig")
    # нормализуем EOL и пишем с BOM (1C-конвенция)
    text = text.replace("\r\n", "\n").replace("\n", "\r\n")
    mod = DST_DIR / "Forms" / "Форма" / "Ext" / "Form" / "Module.bsl"
    mod.write_text(text, encoding="utf-8-sig", newline="")
    print("[OK] runner source ready: tmp/t3/runner_src/АпкРаннер.*")
    return 0


if __name__ == "__main__":
    sys.exit(main())
