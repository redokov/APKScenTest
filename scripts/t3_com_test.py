# -*- coding: utf-8 -*-
"""T3 compile-gate + COM-run of НачатьПрогон/Сканировать on dev_erpapk_demo.

1. Connect via V85.COMConnector as admin (Администратор (ОрловАВ), no password).
2. ВнешниеОбработки.Подключить(epf, БезопасныйРежим=Ложь) -> объект.
3. Создать + ПолучитьФорму (без исполнения) — compile-gate.
4. НачатьПрогон(settings, runsDir) -> КаталогПрогона.
5. Сканировать(КаталогПрогона, "") -> итог (scan.json внутри run-каталога).
Artefacts: tmp/t3/compile-gate.log, tmp/t3/run.log, tmp/t3/scan.json (copy).
"""
import glob
import io
import json
import os
import shutil
import sys
import time

import win32com.client

ADMIN_USR = "Администратор (ОрловАВ)"
BASE = "localhost"
REF = "dev_erpapk_demo"
OUT_DIR = r"C:\MyProjects\APKScenTest\tmp\t3"
RUNS_BASE = r"C:\MyProjects\APKScenTest\tests"
SETTINGS = r"C:\MyProjects\APKScenTest\tests\preprocessor-settings.json"

log_lines = []


def log(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    print(line.encode("ascii", errors="replace").decode("ascii"))
    log_lines.append(line)


def main():
    epf_files = glob.glob(r"C:\MyProjects\APKScenTest\build\*.epf")
    assert epf_files, "build/*.epf not found"
    epf_path = epf_files[0]
    log("EPF: " + epf_path)

    log("connecting COM ...")
    agent = win32com.client.Dispatch("V85.COMConnector").Connect(
        "Srvr='%s';Ref='%s';Usr='%s';" % (BASE, REF, ADMIN_USR))
    log("connected")

    # --- compile-gate: Подключить + Создать + ПолучитьФорму ---
    obj = agent.ВнешниеОбработки.Подключить(epf_path, False)
    log("connected object: " + str(obj))

    obj_data = obj.Создать()
    log("object created (Создать)")
    form = obj_data.ПолучитьФорму()
    log("form obtained: " + str(form))

    # --- run pipeline ---
    run_dir = obj_data.НачатьПрогон(SETTINGS, RUNS_BASE)
    log("run dir: " + str(run_dir))

    summary = obj_data.Сканировать(run_dir, "")
    log("scan summary: " + str(summary))

    scan_path = os.path.join(str(run_dir), "scan.json")
    run_json = os.path.join(str(run_dir), "run.json")
    log("scan.json exists: %s" % os.path.isfile(scan_path))
    shutil.copy(scan_path, os.path.join(OUT_DIR, "scan.json"))
    shutil.copy(run_json, os.path.join(OUT_DIR, "run.json"))
    log("copied scan.json + run.json to tmp/t3/")

    with io.open(os.path.join(OUT_DIR, "last-run-dir.txt"), "w", encoding="utf-8") as f:
        f.write(str(run_dir))
    log("VERDICT: PASS")
    return 0


if __name__ == "__main__":
    try:
        rc = main()
        verdict = "PASS"
    except Exception:
        import traceback
        traceback.print_exc()
        verdict = "FAIL (exception)"
        rc = 2
    log_lines.append("VERDICT: " + verdict)
    with io.open(os.path.join(OUT_DIR, "compile-gate.log"), "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
    print("FINAL " + verdict)
    sys.exit(rc)
