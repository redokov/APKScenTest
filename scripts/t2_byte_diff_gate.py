# -*- coding: utf-8 -*-
"""T2 gate (spec 005): byte-diff 1C patcher vs python etalon.

Run A: Stage-A generation WITHOUT scenario-patches.json (harness-driven).
Etalon: python _patch_scenarios (t8_gate.py) applied to run A features,
        normalized to LF (python text-mode writes CRLF on Windows).
Run B: Stage-A generation WITH scenario-patches.json (new EPF patcher).
GATE PASS: run B feature files byte-equal to etalon for patched templates.
"""
import ast
import io
import json
import os
import re
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"C:\MyProjects\APKScenTest"
V8 = r"C:\Program Files\1cv8\8.5.4.1683\bin\1cv8.exe"
CONN = r"localhost\dev_erpapk_demo"
ADMIN = u"Администратор (ОрловАВ)"
TARGET = os.path.join(ROOT, "build", u"АпкПодготовкаСценарныхТестов.epf")
SETTINGS = os.path.join(ROOT, "tmp", "t8", "preprocessor-settings.json")
RUNS_DIR = os.path.join(ROOT, "tmp", "s005", "runs")
STAGE_A_EPF = os.path.join(ROOT, "tmp", "t8", "epf", u"АпкРаннер.epf")
STAGE_A_TASK = os.path.join(ROOT, "tmp", "t8", "runner_task.json")
STAGE_A_RESULT = os.path.join(ROOT, "tmp", "t8", "runner_result.json")
STAGE_A_LOG = os.path.join(ROOT, "tmp", "s005", "client-a.log")
PATCHES = os.path.join(ROOT, "tests", "templates", "scenario-patches.json")
PATCHES_HIDDEN = PATCHES + ".hidden"
GATE_TEMPLATES = ("02-pl-auto", "05-weighing")
TIMEOUT = 900


def log(msg):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg))
    sys.stdout.flush()


def read_json(path):
    try:
        return json.loads(io.open(path, encoding="utf-8-sig").read())
    except Exception:
        return None


def kill_tree(pid):
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                   capture_output=True)


def stage_a(tag):
    """One Stage-A generation run; returns run dir or None."""
    if os.path.exists(STAGE_A_RESULT):
        os.remove(STAGE_A_RESULT)
    with io.open(STAGE_A_TASK, "w", encoding="utf-8") as f:
        json.dump({"target": TARGET, "settings": SETTINGS,
                   "runsDir": RUNS_DIR}, f, ensure_ascii=False)
    fp = open(STAGE_A_LOG, "wb")
    proc = subprocess.Popen(
        [V8, "/S", CONN, "/RunModeManagedApplication", "/N", ADMIN,
         "/DisableStartupDialogs", "/Execute", STAGE_A_EPF],
        stdout=fp, stderr=subprocess.STDOUT)
    try:
        start = time.time()
        ok = False
        while time.time() - start < TIMEOUT:
            data = read_json(STAGE_A_RESULT)
            if data is not None and data.get("step") == "done":
                ok = True
                break
            if proc.poll() is not None:
                break
            time.sleep(3)
    finally:
        kill_tree(proc.pid)
        try:
            proc.wait(timeout=10)
        except Exception:
            pass
        fp.close()
    data = read_json(STAGE_A_RESULT)
    if not ok or not data or data.get("errorsCount", 1) != 0:
        log("FAIL: stage-A %s not done or has errors: %s" % (tag, data))
        return None
    log("stage-A %s done: %s" % (tag, {k: data.get(k) for k in
        ("runDir", "scanSummary", "fixturesSummary", "featuresSummary")}))
    return data.get("runDir")


def load_python_patcher():
    """Exec SCENARIO_PATCHES + _patch_scenarios from t8_gate.py source."""
    with io.open(os.path.join(ROOT, "scripts", "t8_gate.py"),
                 encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"^SCENARIO_PATCHES = (\{.*?^\}\,?\n)", text, re.S | re.M)
    if not m:
        m = re.search(r"^SCENARIO_PATCHES = (\{.*?\n\}\n)", text, re.S | re.M)
    ns = {"io": io, "os": os}
    exec("SCENARIO_PATCHES = " + m.group(1).strip().rstrip(",") + "\n", ns)
    fm = re.search(r"^def _patch_scenarios\(.*?^    return n_scen, n_pat, pat_log, dropped\n",
                   text, re.S | re.M)
    exec(fm.group(0), ns)
    return ns


def norm_lf(b):
    return b.replace(b"\r\n", b"\n")


def main():
    os.makedirs(RUNS_DIR, exist_ok=True)
    ns = load_python_patcher()

    # Run A: no patches
    if os.path.exists(PATCHES):
        os.rename(PATCHES, PATCHES_HIDDEN)
    try:
        run_a = stage_a("A(no-patches)")
    finally:
        if os.path.exists(PATCHES_HIDDEN):
            os.rename(PATCHES_HIDDEN, PATCHES)
    if not run_a:
        return 2
    feats_a = os.path.join(run_a, "features")

    # Etalon: python-patch run A copies for gate templates
    etalon_dir = os.path.join(ROOT, "tmp", "s005", "etalon")
    if not os.path.exists(etalon_dir):
        os.makedirs(etalon_dir)
    checked = []
    for fn in sorted(os.listdir(feats_a)):
        tpl = fn.split("--")[0]
        if tpl not in GATE_TEMPLATES or not fn.endswith(".feature"):
            continue
        src = os.path.join(feats_a, fn)
        dst = os.path.join(etalon_dir, fn)
        with io.open(src, "rb") as f:
            raw = f.read()
        with io.open(dst, "wb") as f:
            f.write(raw)
        n_scen, n_pat, pat_log, dropped = ns["_patch_scenarios"](
            dst, ns["SCENARIO_PATCHES"][tpl])
        with io.open(dst, "rb") as f:
            raw = f.read()
        with io.open(dst, "wb") as f:
            f.write(norm_lf(raw))
        log("etalon %s: scenarios=%d patched=%d dropped=%s %s"
            % (fn, n_scen, n_pat, dropped, pat_log))
        checked.append((tpl, fn, n_pat, dropped))

    # Run B: with patches (new EPF patcher)
    run_b = stage_a("B(with-patches)")
    if not run_b:
        return 2
    feats_b = os.path.join(run_b, "features")

    # Byte-diff
    fails = 0
    for tpl, fn, n_pat, dropped in checked:
        eb = io.open(os.path.join(etalon_dir, fn), "rb").read()
        bb = io.open(os.path.join(feats_b, fn), "rb").read()
        if eb == bb:
            log("DIFF OK  %s (%d bytes)" % (fn, len(bb)))
            continue
        fails += 1
        log("DIFF FAIL %s: etalon %d bytes vs run B %d bytes" % (fn, len(eb), len(bb)))
        # first mismatch offset
        n = min(len(eb), len(bb))
        off = next((i for i in range(n) if eb[i] != bb[i]), n)
        log("  first diff at byte %d:" % off)
        log("  etalon: %r" % eb[max(0, off - 60):off + 60])
        log("  run B : %r" % bb[max(0, off - 60):off + 60])

    # sanity: run A vs run B for non-patched templates must be equal too
    extra_fail = 0
    for fn in sorted(os.listdir(feats_a)):
        if fn in [c[1] for c in checked] or not fn.endswith(".feature"):
            continue
        a = io.open(os.path.join(feats_a, fn), "rb").read()
        b = io.open(os.path.join(feats_b, fn), "rb").read()
        if a != b:
            extra_fail += 1
            log("EXTRA DIFF FAIL (non-patched template changed!): %s" % fn)
    log("run A=%s run B=%s" % (run_a, run_b))
    if fails == 0 and extra_fail == 0:
        log("GATE PASS: %d patched files byte-equal, %d non-patched unchanged"
            % (len(checked), len(os.listdir(feats_a)) - len(checked)))
        return 0
    log("GATE FAIL: %d patched diffs, %d extra diffs" % (fails, extra_fail))
    return 1


if __name__ == "__main__":
    sys.exit(main())
