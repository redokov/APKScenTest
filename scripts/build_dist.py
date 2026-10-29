# -*- coding: utf-8 -*-
"""Assemble the dist/ kit (spec 005, T6):
- build/*.epf (runner + preprocessor) -> dist/
- Vanessa Automation single (external path) -> dist/ if present
- tests/templates/ (*.feature + scenario-patches.json) -> dist/scenarios/
- tests/baseline/ (baseline.json, baseline-real.json) -> dist/scenarios/
Every copy is byte-verified. Idempotent, refreshes dist/scenarios/."""
import os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
SCEN = os.path.join(DIST, "scenarios")
VA_SINGLE = r"C:\MyProjects\APKTechPlan\tests\vanessa\vanessa-automation-single.epf"

def copy_file(src, dst):
    if not os.path.isfile(src):
        print("[MISS] %s" % src)
        return False
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)
    with open(src, "rb") as a, open(dst, "rb") as b:
        if a.read() != b.read():
            print("[DIFF] %s" % dst)
            return False
    print("[OK] %s (%d b)" % (os.path.relpath(dst, ROOT), os.path.getsize(dst)))
    return True

ok = True

# 1. EPF from build/
ok &= copy_file(os.path.join(ROOT, "build", "АпкРаннер.epf"),
                os.path.join(DIST, "АпкРаннер.epf"))
ok &= copy_file(os.path.join(ROOT, "build", "АпкПодготовкаСценарныхТестов.epf"),
                os.path.join(DIST, "АпкПодготовкаСценарныхТестов.epf"))

# 2. Vanessa single (external, shipped)
ok &= copy_file(VA_SINGLE, os.path.join(DIST, "vanessa-automation-single.epf"))

# 3. Scenarios: refresh whole dir from sources
if os.path.isdir(SCEN):
    shutil.rmtree(SCEN)
os.makedirs(SCEN)
templates = os.path.join(ROOT, "tests", "templates")
copied = 0
for name in sorted(os.listdir(templates)):
    if name.endswith(".feature") or name == "scenario-patches.json":
        ok &= copy_file(os.path.join(templates, name), os.path.join(SCEN, name))
        copied += 1
baseline = os.path.join(ROOT, "tests", "baseline")
for name in ("baseline.json", "baseline-real.json"):
    ok &= copy_file(os.path.join(baseline, name), os.path.join(SCEN, name))
    copied += 1
print("scenarios: %d files" % copied)

if not ok:
    sys.exit(1)
print("[OK] dist kit assembled")
