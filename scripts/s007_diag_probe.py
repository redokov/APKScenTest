# -*- coding: utf-8 -*-
"""S007 TASK3: диагностический EPF-зонд Опороса (по рецепту t5_probe.py).
src -> epf-build -> /Execute -> result JSON."""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

PROJECT = Path(r"C:\MyProjects\APKScenTest")
T = PROJECT / "tmp" / "s007"
SRC_DIR = PROJECT / "tmp" / "t3" / "gate_src" / "ГейтАпк"
SRC_XML = PROJECT / "tmp" / "t3" / "gate_src" / "ГейтАпк.xml"
MOD = T / "diag_module_src.bsl"
DIAG_SRC_DIR = T / "diag_src" / "АпкЗондS007"
DIAG_SRC_XML = T / "diag_src" / "АпкЗондS007.xml"
SKILL_PS1 = r"C:\MyProjects\PiPack\skills\1c\epf-build\scripts\epf-build.ps1"
V8_BIN = r"C:\Program Files\1cv8\8.5.4.1683\bin"
V8 = Path(V8_BIN) / "1cv8.exe"
EPF = T / "epf" / "АпкЗондS007.epf"
RESULT = T / "diag_result.json"
CLIENT_LOG = T / "diag_client.log"
STUB_TEMP = T / "stubtemp"
CONN = "localhost\\dev_erpapk_demo"
USER = "Администратор (ОрловАВ)"
TIMEOUT = 900


def die(msg):
    print("[FAIL] " + msg)
    sys.exit(1)


def prepare_src():
    for p in (SRC_DIR, SRC_XML, MOD):
        if not p.exists():
            die("not found: %s" % p)
    if DIAG_SRC_DIR.exists():
        shutil.rmtree(DIAG_SRC_DIR)
    DIAG_SRC_DIR.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SRC_DIR, DIAG_SRC_DIR)
    shutil.copyfile(SRC_XML, DIAG_SRC_XML)
    text = MOD.read_text(encoding="utf-8-sig")
    text = text.replace("\r\n", "\n").replace("\n", "\r\n")
    mod = DIAG_SRC_DIR / "Forms" / "Форма" / "Ext" / "Form" / "Module.bsl"
    mod.write_text(text, encoding="utf-8-sig", newline="")
    print("[OK] diag src prepared")


def build_epf():
    args = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", SKILL_PS1,
            "-V8Path", V8_BIN,
            "-SourceFile", str(DIAG_SRC_XML),
            "-OutputFile", str(EPF)]
    env = os.environ.copy()
    STUB_TEMP.mkdir(parents=True, exist_ok=True)
    env["TEMP"] = str(STUB_TEMP)
    env["TMP"] = str(STUB_TEMP)
    proc = subprocess.run(args, capture_output=True, timeout=1800, env=env)
    log = T / "epf-build-diag.log"
    log.write_text(
        "CMD: %s\n\nRC: %d\n\n--- STDOUT ---\n%s\n\n--- STDERR ---\n%s" % (
            " ".join(args), proc.returncode,
            proc.stdout.decode("cp866", errors="replace"),
            proc.stderr.decode("cp866", errors="replace")),
        encoding="utf-8")
    if proc.returncode != 0:
        die("diag EPF build failed, see %s" % log)
    print("[OK] diag EPF built")


def kill_tree(pid):
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)


def run_probe():
    if RESULT.exists():
        RESULT.unlink()
    cmd = [str(V8), "/S", CONN, "/RunModeManagedApplication",
           "/N", USER, "/DisableStartupDialogs", "/Execute", str(EPF)]
    fp = open(CLIENT_LOG, "wb")
    proc = subprocess.Popen(cmd, stdout=fp, stderr=subprocess.STDOUT)
    data = None
    try:
        start = time.time()
        while time.time() - start < TIMEOUT:
            try:
                data = json.loads(RESULT.read_text(encoding="utf-8-sig"))
            except Exception:
                data = None
            if data and data.get("step") == "done":
                break
            if proc.poll() is not None:
                break
            time.sleep(3)
        else:
            kill_tree(proc.pid)
            die("timeout waiting for diag result")
    finally:
        kill_tree(proc.pid)
        try:
            proc.wait(timeout=10)
        except Exception:
            pass
        fp.close()
    if data is None:
        die("no result file; client log: %s" % CLIENT_LOG)
    (T / "diag_pretty.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("[OK] -> %s" % (T / "diag_pretty.json"))


if __name__ == "__main__":
    prepare_src()
    build_epf()
    run_probe()
