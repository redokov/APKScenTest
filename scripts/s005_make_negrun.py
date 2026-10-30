# -*- coding: utf-8 -*-
"""s005 T5: build a neg-only run dir (manifest = single neg entry) for the
runner gate. Recreates tests/run-negonly-t5 from tests/run-20261030-001311
run.json/scan.json (scan emptied) + empty fixtures + embedded negUser
settings. Usage: python scripts/s005_make_negrun.py"""
import io, json, os, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tests", "run-20261030-001311")
DST = os.path.join(ROOT, "tests", "run-negonly-t5")


def main():
    os.makedirs(DST, exist_ok=True)
    for f in ("run.json", "scan.json"):
        shutil.copyfile(os.path.join(SRC, f), os.path.join(DST, f))
    # empty scan: plan builder sees no users/representatives
    with io.open(os.path.join(DST, "scan.json"), "w", encoding="utf-8") as f:
        json.dump({"users": [], "representatives": []}, f, ensure_ascii=False, indent=1)
    with io.open(os.path.join(DST, "fixtures.json"), "w", encoding="utf-8") as f:
        json.dump({"users": [], "documents": [], "armPlan": []}, f, ensure_ascii=False, indent=1)
    # run.json: embedded settings snapshot must carry negUser/negTemplate
    # (settings are frozen into run.json at scan time; the live file
    # tests/preprocessor-settings.json is NOT re-read by generation)
    p = os.path.join(DST, "run.json")
    r = json.load(io.open(p, encoding="utf-8"))
    st = r.get("settings")
    if isinstance(st, dict):
        st["negUser"] = u"\u0410\u043f\u043a\u0421\u0446\u0435\u043d\u0422\u0435\u0441\u0442_\u041d\u0435\u0433\u0430\u0442\u0438\u04321"
        st["negTemplate"] = "neg-pl-denied"
        r["settings"] = st
    r["paths"]["runDir"] = DST.replace("\\", "/")
    with io.open(p, "w", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=1)
    for junk in ("features-manifest.json",):
        q = os.path.join(DST, junk)
        if os.path.exists(q):
            os.remove(q)
    fd = os.path.join(DST, "features")
    if os.path.isdir(fd):
        shutil.rmtree(fd)
    print("neg-only run dir ready:", DST)


if __name__ == "__main__":
    main()
