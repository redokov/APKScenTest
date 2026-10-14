# -*- coding: utf-8 -*-
"""T4 Gate 4: прогон СформироватьФикстуры + ПостроитьПланПрогона.

Клиентский сеанс 1cv8.exe /Execute tmp/t4/epf/АпкРаннер.epf читает задание
tmp/t4/runner_task.json (target/runDir), подключает целевой EPF через адрес
временного хранилища и вызывает: СформироватьФикстуры(runDir) ->
ПостроитьПланПрогона(runDir). Артефакт tmp/t4/runner_result.json пишется
после КАЖДОГО шага. Драйвер ждёт step=done, затем копирует fixtures.json
из run-каталога в tmp/t4/fixtures.json и пишет итог в tmp/t4/gate.log.

Exit 0 = fixtures-done + plan-done без ошибок; 1 = FAIL.
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
RUNNER_EPF = PROJECT / "tmp" / "t4" / "epf" / "АпкРаннер.epf"
TASK = PROJECT / "tmp" / "t4" / "runner_task.json"
RESULT = PROJECT / "tmp" / "t4" / "runner_result.json"
CLIENT_LOG = PROJECT / "tmp" / "t4" / "client.log"
GATE_LOG = PROJECT / "tmp" / "t4" / "gate.log"
FIXTURES_COPY = PROJECT / "tmp" / "t4" / "fixtures.json"
RUN_DIR = PROJECT / "tests" / "run-20261011-233413"
TIMEOUT = 900

TASK_DEF = {
    "target": str(PROJECT / "build" / "АпкПодготовкаСценарныхТестов.epf"),
    "runDir": str(RUN_DIR),
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

    steps_seen = []
    if data:
        # порядок фиксировался по мере появления артефактов; для лога
        # восстановим по факту содержимого
        pass
    steps_seen = [k for k in ("connected", "fixturesSummary",
                              "planUsers") if k in (data or {})]

    ok = (data is not None
          and data.get("step") == "done"
          and not data.get("errors")
          and "fixturesSummary" in data
          and "planUsers" in data)

    lines = ["[%s] T4 gate run" % ("OK" if ok else "FAIL")]
    lines.append("result: " + json.dumps(data, ensure_ascii=False, indent=1))

    fixtures = RUN_DIR / "fixtures.json"
    if fixtures.exists():
        import shutil
        shutil.copyfile(fixtures, FIXTURES_COPY)
        lines.append("fixtures.json copied: " + str(FIXTURES_COPY)
                     + " (%d bytes)" % fixtures.stat().st_size)
    else:
        lines.append("fixtures.json NOT found in runDir: " + str(fixtures))
        ok = False

    GATE_LOG.write_text("\n".join(lines), encoding="utf-8")
    print(lines[0])
    print(json.dumps(data, ensure_ascii=False, indent=1)[:2000])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
