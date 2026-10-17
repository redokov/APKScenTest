# -*- coding: utf-8 -*-
"""T9.1: Stage-A smoke (StartRun->Scan->Fixtures->GenerateFeatures).

Runs the T8 Stage-A runner EPF against dev_erpapk_demo with the freshly
rebuilt build/*.epf, into a fresh runs dir under tmp/t9/gen-verify/runs.
Then summarizes features-manifest.json -> tmp/t9/gen-verify/manifest-summary.txt.
No batch E2E (that is the next task). ASCII output only.
"""
import io
import json
import os
import subprocess
import time

ROOT = r"C:\MyProjects\APKScenTest"
V8 = r"C:\Program Files\1cv8\8.5.4.1683\bin\1cv8.exe"
CONN = r"localhost\dev_erpapk_demo"
ADMIN = "Администратор (ОрловАВ)"

TARGET = os.path.join(ROOT, "build", "АпкПодготовкаСценарныхТестов.epf")
SETTINGS = os.path.join(ROOT, "tmp", "t8", "preprocessor-settings.json")
RUNS_DIR = os.path.join(ROOT, "tmp", "t9", "gen-verify", "runs")
STAGE_A_EPF = os.path.join(ROOT, "tmp", "t8", "epf", "АпкРаннер.epf")
TASK = os.path.join(ROOT, "tmp", "t8", "runner_task.json")
RESULT = os.path.join(ROOT, "tmp", "t8", "runner_result.json")
CLIENT_LOG = os.path.join(ROOT, "tmp", "t9", "client-a.log")
SUMMARY = os.path.join(ROOT, "tmp", "t9", "gen-verify", "manifest-summary.txt")
TIMEOUT = 900

def read_json(path):
    try:
        return json.loads(io.open(path, encoding="utf-8-sig").read())
    except Exception:
        return None

def main():
    out = []

    def log(m):
        print(m, flush=True)
        out.append(str(m))

    if not os.path.exists(TARGET):
        log("[FAIL] target EPF not found: %s" % TARGET)
        raise SystemExit(1)
    if not os.path.exists(STAGE_A_EPF):
        log("[FAIL] Stage-A runner not found: %s" % STAGE_A_EPF)

    os.makedirs(RUNS_DIR, exist_ok=True)
    with io.open(TASK, "w", encoding="utf-8") as f:
        json.dump({"target": TARGET, "settings": SETTINGS, "runsDir": RUNS_DIR},
                  f, ensure_ascii=False)
    if os.path.exists(RESULT):
        os.remove(RESULT)

    log("[stage-a] launching 1C /Execute runner ...")
    fp = open(CLIENT_LOG, "wb")
    proc = subprocess.Popen(
        [V8, "/S", CONN, "/RunModeManagedApplication", "/N", ADMIN,
         "/DisableStartupDialogs", "/Execute", STAGE_A_EPF],
        stdout=fp, stderr=subprocess.STDOUT)
    ok_exit = False
    try:
        start = time.time()
        while time.time() - start < TIMEOUT:
            data = read_json(RESULT)
            if data is not None and data.get("step") == "done":
                ok_exit = True
                break
            if proc.poll() is not None:
                data = read_json(RESULT)
                if data is not None and data.get("step") == "done":
                    ok_exit = True
                break
            time.sleep(3)
    finally:
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
        try:
            proc.wait(timeout=10)
        except Exception:
            pass
        fp.close()

    data = read_json(RESULT)
    if not data:
        log("[FAIL] no runner result")
        raise SystemExit(1)
    log("[stage-a] step=%s errorsCount=%s" % (data.get("step"), data.get("errorsCount")))
    for e in (data.get("errors") or [])[:5]:
        log("   error: %s" % str(e)[:300])
    if data.get("step") != "done" or data.get("errorsCount"):
        log("[stage-a] FAIL")
        raise SystemExit(1)
    run_dir = data.get("runDir", "")
    log("[stage-a] runDir=%s" % run_dir)
    log("[stage-a] features=%s" % data.get("featuresSummary", ""))

    manifest_path = os.path.join(run_dir, "features-manifest.json")
    manifest = read_json(manifest_path)
    if not manifest:
        log("[FAIL] manifest not readable: %s" % manifest_path)
        raise SystemExit(1)

    lines = []
    lines.append("runDir: %s" % run_dir)
    lines.append("featuresSummary: %s" % data.get("featuresSummary", ""))
    lines.append("")
    lines.append("== arm entries in manifest ==")
    arm_count = 0
    for entry in manifest.get("files", []):
        if str(entry.get("template", "")).startswith("arm-"):
            arm_count += 1
            lines.append("ARM %s | user=%s | scenarios=%s | file=%s"
                         % (entry.get("template"), entry.get("user"),
                            entry.get("scenarios"), os.path.basename(str(entry.get("file", "")))))
    lines.append("arm entries: %d" % arm_count)
    lines.append("total files: %d" % len(manifest.get("files", [])))

    lines.append("")
    lines.append("== warnings ==")
    arm_missing = set()
    for w in manifest.get("warnings", []):
        lines.append("WARN: %s" % w)
        if "Шаблон не найден" in str(w) and "arm-" in str(w):
            arm_missing.add(str(w))
    lines.append("warnings total: %d" % len(manifest.get("warnings", [])))

    with io.open(SUMMARY, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log("[OK] summary written: %s (arm entries=%d)" % (SUMMARY, arm_count))

if __name__ == "__main__":
    main()
