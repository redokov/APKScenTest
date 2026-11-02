# -*- coding: utf-8 -*-
"""s009: sync scenario-patches.json section 05-weighing/HBB-000018 with the
updated SCENARIO_PATCHES in scripts/t8_gate.py (slow ENTER cadence + active
window gate step). One-off sync script.
Run: python -X utf8 scripts/s009_sync_patch_weighing.py
"""
import io
import json
import os

P = os.path.abspath("tests/templates/scenario-patches.json")

NEW_LINES = [
    u"\tИ Пауза 1",
    u'\tИ я выбираю значение реквизита с именем "ОснованиеВозврата" из формы списка',
    u"\tИ Пауза 2",
    u'\tТогда открылось окно "Регистрации взвешиваний на току"',
    u'\tИ в таблице "Список" я перехожу к строке по шаблону',
    u"\t\t| 'Номер' |",
    u"\t\t| '*000017*' |",
    u"\tИ Пауза 2",
    u'\tИ я нажимаю сочетание клавиш "ENTER"',
    u"\tИ Пауза 3",
    u'\tТогда открылось окно "Регистрация взвешивания на току*"',
]

with io.open(P, "r", encoding="utf-8") as f:
    d = json.load(f)

blk = d["05-weighing"][u"НВ00-000018"][0]
assert blk["op"] == "block", "unexpected op"
old = blk["lines"]
# sanity: the block we expect (fast cadence, no window gate)
assert u'\tИ Пауза 1' in old and u'\tИ Пауза 2' == old[-1], "unexpected block shape"
blk["lines"] = NEW_LINES

with io.open(P, "w", encoding="utf-8") as f:
    json.dump(d, f, ensure_ascii=False, indent=1)
    f.write("\n")
print("synced: 05-weighing/HB00-000018 block lines=%d" % len(NEW_LINES))
