# -*- coding: utf-8 -*-
"""T3 Gate 4 (compile-gate): клиентский сеанс 1cv8.exe /Execute гейт-EPF.

Гейт-EPF (tmp/t3/epf/ГейтАпк.epf) читает цель из tmp/t3/gate_target.txt,
подключает её через ВнешниеОбработки.Подключить(Адрес, , Ложь) и вызывает
ПолучитьФорму — компиляция БЕЗ исполнения ПриОткрытии целевой обработки.
Отчёт: tmp/t3/compile_check.json, шаги: tmp/t3/gate_steps.log.

Цель по умолчанию: build/АпкПодготовкаСценарныхТестов.epf.
Вердикт: exit 0 = formCreated true; 1 = FAIL.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

PROJECT = Path(r"C:\MyProjects\APKScenTest")
V8 = Path(r"C:\Program Files\1cv8\8.5.4.1683\bin\1cv8.exe")
CONN = "localhost\\dev_erpapk_demo"
USER = "Администратор (ОрловАВ)"
GATE_EPF = PROJECT / "tmp" / "t3" / "epf" / "ГейтАпк.epf"
TARGET = PROJECT / "build" / "АпкПодготовкаСценарныхТестов.epf"
REPORT = PROJECT / "tmp" / "t3" / "compile_check.json"
TARGET_FILE = PROJECT / "tmp" / "t3" / "gate_target.txt"
CLIENT_LOG = PROJECT / "tmp" / "t3" / "gate4_client.log"
TIMEOUT = 180


def kill_tree(pid):
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                   capture_output=True)


def main() -> int:
    for p, what in ((TARGET, "target EPF"), (GATE_EPF, "gate EPF"), (V8, "1cv8.exe")):
        if not p.exists():
            print("[FAIL] %s not found: %s" % (what, p), file=sys.stderr)
            return 1
    if REPORT.exists():
        REPORT.unlink()
    if TARGET_FILE.exists():
        TARGET_FILE.unlink()
    TARGET_FILE.write_text(str(TARGET), encoding="utf-8")

    cmd = [str(V8), "/S", CONN, "/RunModeManagedApplication",
           "/N", USER, "/DisableStartupDialogs", "/Execute", str(GATE_EPF)]
    fp = open(CLIENT_LOG, "wb")
    proc = subprocess.Popen(cmd, stdout=fp, stderr=subprocess.STDOUT)
    rc = 1
    try:
        start = time.time()
        while time.time() - start < TIMEOUT:
            if REPORT.exists():
                time.sleep(1)
                break
            if proc.poll() is not None:
                print("[FAIL] client exited rc=%s without report"
                      % proc.returncode, file=sys.stderr)
                kill_tree(proc.pid)
                return 1
            time.sleep(2)
        else:
            print("[FAIL] timeout (%ss): no report" % TIMEOUT, file=sys.stderr)
            return 1
        try:
            data = json.loads(REPORT.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            print("[FAIL] invalid report: %s" % exc, file=sys.stderr)
            return 1
        ok = data.get("formCreated") is True
        print("[%s] compile check: %s" % ("OK" if ok else "FAIL", TARGET.name))
        if not ok:
            print("ERROR REPORT:")
            print(str(data.get("error", "?"))[:3000])
        rc = 0 if ok else 1
    finally:
        kill_tree(proc.pid)
        try:
            proc.wait(timeout=10)
        except Exception:
            pass
        fp.close()
    return rc


if __name__ == "__main__":
    sys.exit(main())
