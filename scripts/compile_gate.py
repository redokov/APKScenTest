#!/usr/bin/env python3
"""Compile-gate for external 1C data processors (EPF/ERF).

Connects to the test infobase with a thin client session, executes the gate EPF
(tmp/t3/epf/ГейтАпк.epf), which reads the target path from tmp/t3/gate_target.txt,
attaches the target via ВнешниеОбработки.Подключить(..., , Ложь) and calls
ПолучитьФорму. That compiles the target's modules and builds its form WITHOUT
running ПриОткрытии -- exactly what "compile-gate" means in this project.

Reports formCreated + error text; writes an evidence file.

Usage:
  python scripts/compile_gate.py --target build/АпкПодготовкаСценарныхТестов.epf
  python scripts/compile_gate.py --target dist/АпкРаннер.epf --out tmp/007/gate-runner.txt
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
V8 = Path(r"C:\Program Files\1cv8\8.5.4.1683\bin\1cv8.exe")
CONN = r"localhost\dev_erpapk_demo"
USER = "Администратор (ОрловАВ)"
GATE_EPF = PROJECT / "tmp" / "t3" / "epf" / "ГейтАпк.epf"
TARGET_FILE = PROJECT / "tmp" / "t3" / "gate_target.txt"
REPORT = PROJECT / "tmp" / "t3" / "compile_check.json"
CLIENT_LOG = PROJECT / "tmp" / "t3" / "gate_client.log"
TIMEOUT = 240


def kill_tree(pid):
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True, help="path to EPF/ERF to compile")
    ap.add_argument("--out", default=None, help="evidence file (txt)")
    ap.add_argument("--timeout", type=int, default=TIMEOUT)
    args = ap.parse_args()

    target = Path(args.target)
    if not target.is_absolute():
        target = PROJECT / target
    lines = []
    fail_reason = ""
    ok = False

    for what, path in (("gate EPF", GATE_EPF), ("target", target), ("1cv8.exe", V8)):
        if not path.exists():
            print("[FAIL] %s not found: %s" % (what, path), file=sys.stderr)
            return 1

    if REPORT.exists():
        REPORT.unlink()
    if TARGET_FILE.exists():
        TARGET_FILE.unlink()
    TARGET_FILE.write_text(str(target), encoding="utf-8")

    cmd = [str(V8), "/S", CONN, "/RunModeManagedApplication",
           "/N", USER, "/DisableStartupDialogs", "/Execute", str(GATE_EPF)]
    with open(CLIENT_LOG, "wb") as fp:
        proc = subprocess.Popen(cmd, stdout=fp, stderr=subprocess.STDOUT)
    lines.append("target: %s" % target)
    lines.append("client cmd: 1cv8.exe /S %s /RunModeManagedApplication /N <user> "
                 "/DisableStartupDialogs /Execute %s" % (CONN, GATE_EPF.name))
    try:
        start = time.time()
        while time.time() - start < args.timeout:
            if REPORT.exists():
                time.sleep(1)
                break
            if proc.poll() is not None:
                fail_reason = ("client exited rc=%s without report (see %s)"
                               % (proc.returncode, CLIENT_LOG))
                break
            time.sleep(2)
        else:
            fail_reason = "timeout (%ss): no report" % args.timeout

        if not fail_reason:
            try:
                data = json.loads(REPORT.read_text(encoding="utf-8-sig"))
            except Exception as exc:  # noqa: BLE001
                fail_reason = "invalid report: %s" % exc
            else:
                ok = data.get("formCreated") is True
                lines.append("formCreated: %s" % data.get("formCreated"))
                if not ok:
                    fail_reason = str(data.get("error", "?"))[:3000]
    finally:
        kill_tree(proc.pid)
        try:
            proc.wait(timeout=10)
        except Exception:  # noqa: BLE001
            pass

    if fail_reason:
        lines.append("FAIL: " + fail_reason)
    verdict = "PASS" if ok else "FAIL"
    lines.insert(0, "compile-gate: %s (%s)" % (verdict, target.name))
    text = "\n".join(lines)
    print(text)
    if args.out:
        out_path = Path(args.out)
        if not out_path.is_absolute():
            out_path = PROJECT / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
