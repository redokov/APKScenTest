# -*- coding: utf-8 -*-
"""T3 Gate 5: гейт-раннер-прогон НачатьПрогон -> Сканировать -> ВернутьРезультат.

Клиентский сеанс 1cv8.exe /Execute tmp/t3/epf/АпкРаннер.epf читает задание
tmp/t3/runner_task.json (target/settingsPath/runsDir/filtersPath), подключает
целевой EPF через адрес временного хранилища, вызывает его серверные
функции и пишет step-артефакт tmp/t3/runner_result.json после каждого шага.
Драйвер ждёт step=done, затем копирует scan.json из run-каталога в
tmp/t3/scan.json и пишет итог в tmp/t3/gate5.log.

Exit 0 = scan-done без ошибок; 1 = FAIL.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(r"C:\MyProjects\APKScenTest")
V8 = Path(r"C:\Program Files\1cv8\8.5.4.1683\bin\1cv8.exe")
CONN = "localhost\\dev_erpapk_demo"
USER = "Администратор (ОрловАВ)"
RUNNER_EPF = PROJECT / "tmp" / "t3" / "epf" / "АпкРаннер.epf"
TASK = PROJECT / "tmp" / "t3" / "runner_task.json"
RESULT = PROJECT / "tmp" / "t3" / "runner_result.json"
CLIENT_LOG = PROJECT / "tmp" / "t3" / "gate5_client.log"
GATE5_LOG = PROJECT / "tmp" / "t3" / "gate5.log"
SCAN_COPY = PROJECT / "tmp" / "t3" / "scan.json"
TIMEOUT = 900

TASK_DEF = {
    "target": str(PROJECT / "build" / "АпкПодготовкаСценарныхТестов.epf"),
    "settingsPath": str(PROJECT / "tests" / "preprocessor-settings.json"),
    "runsDir": str(PROJECT / "tests"),
    "filtersPath": "",
}


def kill_tree(pid):
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                   capture_output=True)


def read_result():
    try:
        return json.loads(RESULT.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def main() -> int:
    if not RUNNER_EPF.exists():
        print("[FAIL] runner EPF not found", file=sys.stderr)
        return 1
    TASK.write_text(json.dumps(TASK_DEF, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    if RESULT.exists():
        RESULT.unlink()

    cmd = [str(V8), "/S", CONN, "/RunModeManagedApplication",
           "/N", USER, "/DisableStartupDialogs", "/Execute", str(RUNNER_EPF)]
    fp = open(CLIENT_LOG, "wb")
    proc = subprocess.Popen(cmd, stdout=fp, stderr=subprocess.STDOUT)
    data = None
    try:
        start = time.time()
        while time.time() - start < TIMEOUT:
            data = read_result()
            if data and data.get("step") == "done":
                break
            if proc.poll() is not None:
                time.sleep(2)
                data = data or read_result()
                break
            time.sleep(3)
        else:
            print("[FAIL] timeout (%ss): no done-step" % TIMEOUT,
                  file=sys.stderr)
            kill_tree(proc.pid)
            return 1
    finally:
        kill_tree(proc.pid)
        try:
            proc.wait(timeout=10)
        except Exception:
            pass
        fp.close()

    ok = (data is not None
          and data.get("step") == "done"
          and data.get("scanSummary") is not None
          and not data.get("errors"))

    lines = ["[%s] gate5 run" % ("OK" if ok else "FAIL")]
    lines.append("result: " + json.dumps(data, ensure_ascii=False, indent=1))

    # скопировать scan.json из run-каталога
    if data and data.get("runDir"):
        scan = Path(str(data["runDir"])) / "scan.json"
        if scan.exists():
            import shutil
            shutil.copyfile(scan, SCAN_COPY)
            lines.append("scan.json copied: " + str(SCAN_COPY))
        else:
            lines.append("scan.json NOT found in runDir: " + str(scan))
    GATE5_LOG.write_text("\n".join(lines), encoding="utf-8")
    print(lines[0])
    print(json.dumps(data, ensure_ascii=False, indent=1)[:2000])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
