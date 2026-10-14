# -*- coding: utf-8 -*-
"""T8 F2: проверить fixtures.json + сгенерированную фичу."""
import glob
import io
import json
import os

RUN = r"C:\MyProjects\APKScenTest\tests\run-20261013-213758"

fix = json.loads(io.open(os.path.join(RUN, "fixtures.json"), encoding="utf-8-sig").read())
docs = [d for d in fix["documents"] if d["type"] == "АпкПутевойЛистТракториста"]
print("tractor docs:", len(docs))
vr = None
for d in docs:
    rows = d["data"]["tabular"].get("ВыполненныеРаботы") or []
    if rows:
        vr = rows[0]
        break
print("VR row:", json.dumps(vr, ensure_ascii=False, indent=1))

ok = True
def check(cond, label):
    global ok
    print(("PASS " if cond else "FAIL ") + label)
    if not cond:
        ok = False

check(vr is not None, "VR row exists")
if vr:
    check(vr.get("ТипЗатрат") == "Прямые затраты", "ТипЗатрат == Прямые затраты")
    check(vr.get("ТипЗатратСписок") == "На прямые затраты", "ТипЗатратСписок derived")
    check("115" in (vr.get("АналитикаРасходов") or {}).get("presentation", ""),
          "АналитикаРасходов presentation 115...")
    check(vr.get("ХарактеристикаРаботы") == "2-3 цн/га", "ХарактеристикаРаботы == 2-3 цн/га")

# features
for fp in glob.glob(os.path.join(RUN, "features", "*.feature")):
    body = io.open(fp, encoding="utf-8-sig").read()
    name = os.path.basename(fp)
    if "01-pl-tractor" in name:
        print("--- %s ---" % name)
        for line in body.splitlines():
            if "ВТЧ" in line or "АналитикаРасходов" in line or "ХарактеристикаРаботы" in line:
                print("  ", line.strip())
        bad = [l.strip() for l in body.splitlines() if "{{" in l]
        if bad:
            print("PLACEHOLDERS LEFT:")
            for b in bad:
                print("  !", b)
            ok = False
        else:
            print("PASS no placeholders left in tractor feature")

print("VERDICT:", "PASS" if ok else "FAIL")
