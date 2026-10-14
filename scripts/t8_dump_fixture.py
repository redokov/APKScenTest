# -*- coding: utf-8 -*-
# Dump tractor fixture (01-pl-tractor) header + tabular + the COM probe results (if run later).
import json, sys, io

run = sys.argv[1] if len(sys.argv) > 1 else "20261012-193446"
fx = json.load(open(rf"c:/MyProjects/APKScenTest/tests/run-{run}/fixtures.json", encoding="utf-8"))
out = io.StringIO()

for d in fx["documents"]:
    if "Тракторист" in d["type"]:
        out.write(f"type={d['type']} ref={d['ref']} number={d['number']}\n")
        out.write("header:\n")
        for k, v in d["data"]["header"].items():
            out.write(f"  {k} = {v!r}\n")
        out.write("tabular:\n")
        for tn, rows in d["data"]["tabular"].items():
            out.write(f"  [{tn}] rows={len(rows)}\n")
            for r in rows[:3]:
                out.write(f"    {r!r}\n")

open(r"c:/MyProjects/APKScenTest/tmp/t8/fixture-tractor.txt", "w", encoding="utf-8").write(out.getvalue())
print("written", len(out.getvalue()))
