# -*- coding: utf-8 -*-
"""S006 контрольный скан с заполненными осями coverage-map.

Использует t8 Stage-A раннер (tmp/t8/epf/АпкРаннер.epf, task: tmp/t3/runner_task.json,
result: tmp/t3/runner_result.json): 1cv8 /Execute, ожидание step=done,
копия runDir/scan.json -> tmp/s006/scan-axes.json + сводка представителей.
Запуск: python -X utf8 scripts/s006_control_scan.py [timeout]
"""
import io
import json
import os
import sys
import time

sys.path.insert(0, os.path.abspath("scripts"))
sys.stdout.reconfigure(encoding="utf-8")

import t8_gate as t  # run_1c_session, start_watchdog, rac_terminate_ib_sessions, read_json

ROOT = r"C:\MyProjects\APKScenTest"
TASK = os.path.join(ROOT, "tmp", "t8", "runner_task.json")
RESULT = os.path.join(ROOT, "tmp", "t8", "runner_result.json")
RUNNER = os.path.join(ROOT, "tmp", "t8", "epf", "АпкРаннер.epf")
TARGET = os.path.join(ROOT, "build", "АпкПодготовкаСценарныхТестов.epf")
SETTINGS = os.path.join(ROOT, "tests", "preprocessor-settings.json")
RUNS_DIR = os.path.join(ROOT, "tests")
OUT = os.path.join(ROOT, "tmp", "s006", "scan-axes.json")


def u2a(s):
    return s.encode("unicode-escape").decode("ascii")


def main():
    timeout = int(sys.argv[1]) if len(sys.argv) > 1 else 900

    with io.open(TASK, "w", encoding="utf-8") as f:
        json.dump({"target": TARGET, "settings": SETTINGS,
                   "runsDir": RUNS_DIR, "filters": ""}, f,
                  ensure_ascii=False)
    if os.path.exists(RESULT):
        os.remove(RESULT)

    n = t.rac_terminate_ib_sessions()
    print("[scan] terminated sessions:", n)

    wd = t.start_watchdog(timeout + 120, "watchdog-s006-scan.log")
    ok = t.run_1c_session(RUNNER, timeout,
                          os.path.join(ROOT, "tmp", "s006", "control-scan-client.log"),
                          result_file=RESULT)
    wd.kill()
    if not ok:
        print("[scan] FAIL: runner session failed")
        return 1

    res = t.read_json(RESULT)
    if not res or res.get("step") != "done":
        print("[scan] FAIL: no done result:", u2a(json.dumps(res, ensure_ascii=False))[:400]
              if res else "None")
        return 1
    print("[scan] summary:", u2a(res.get("scanSummary", ""))[:300])
    run_dir = res.get("runDir", "")
    scan_path = os.path.join(run_dir, "scan.json")
    if not os.path.isfile(scan_path):
        print("[scan] FAIL: scan.json missing in", run_dir)
        return 1
    import shutil
    shutil.copy(scan_path, OUT)
    print("[scan] copied ->", OUT)

    scan = json.load(io.open(OUT, encoding="utf-8"))
    reps = scan.get("representatives", {})
    total = 0
    for key, lst in sorted(reps.items()):
        if not isinstance(lst, list):
            continue
        total += len(lst)
        print(u2a(key), "->", len(lst), "rep(s)")
        for r in lst:
            print("    #%s axes=%s user=%s" % (
                r.get("number") or r.get("docNumber"),
                u2a(json.dumps(r.get("axes", {}), ensure_ascii=False)),
                u2a(r.get("user", ""))))
    print("TOTAL reps:", total)

    with io.open(os.path.join(ROOT, "tmp", "s006", "last-control-run-dir.txt"),
                 "w", encoding="utf-8") as f:
        f.write(run_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
