# -*- coding: utf-8 -*-
"""T5 probe: определить фактическое поведение ЗаписьТекста/КодировкаТекста
на платформе 8.5.4.1683 (BOM, переводы строк, допустимость параметров
конструктора) — до правки генератора feature-фич.

Шаги:
 1) собрать probe-EPF из tmp/t5/probe_module_src.bsl (по образцу runner);
 2) запустить клиентский сеанс /Execute, дождаться step=done, kill-tree;
 3) разобрать байты p1..p7 -> tmp/t5/probe_gate.log.
"""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(r"C:\MyProjects\APKScenTest")
T5 = PROJECT / "tmp" / "t5"
SRC_DIR = PROJECT / "tmp" / "t3" / "gate_src" / "ГейтАпк"
SRC_XML = PROJECT / "tmp" / "t3" / "gate_src" / "ГейтАпк.xml"
MOD = T5 / "probe_module_src.bsl"
PROBE_DIR = T5 / "probe"
PROBE_SRC_DIR = T5 / "probe_src" / "АпкПроба"
PROBE_SRC_XML = T5 / "probe_src" / "АпкПроба.xml"
SKILL_PS1 = r"C:\MyProjects\PiPack\skills\1c\epf-build\scripts\epf-build.ps1"
V8_BIN = r"C:\Program Files\1cv8\8.5.4.1683\bin"
V8 = Path(V8_BIN) / "1cv8.exe"
PROBE_EPF = T5 / "epf" / "АпкПроба.epf"
RESULT = T5 / "probe_result.json"
GATE_LOG = T5 / "probe_gate.log"
CLIENT_LOG = T5 / "probe_client.log"
STUB_TEMP = T5 / "stubtemp"
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
    if PROBE_SRC_DIR.exists():
        shutil.rmtree(PROBE_SRC_DIR)
    PROBE_SRC_DIR.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SRC_DIR, PROBE_SRC_DIR)
    shutil.copyfile(SRC_XML, PROBE_SRC_XML)
    text = MOD.read_text(encoding="utf-8-sig")
    text = text.replace("\r\n", "\n").replace("\n", "\r\n")
    mod = PROBE_SRC_DIR / "Forms" / "Форма" / "Ext" / "Form" / "Module.bsl"
    mod.write_text(text, encoding="utf-8-sig", newline="")
    print("[OK] probe src prepared")


def build_epf():
    args = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", SKILL_PS1,
            "-V8Path", V8_BIN,
            "-SourceFile", str(PROBE_SRC_XML),
            "-OutputFile", str(PROBE_EPF)]
    env = os.environ.copy()
    STUB_TEMP.mkdir(parents=True, exist_ok=True)
    env["TEMP"] = str(STUB_TEMP)
    env["TMP"] = str(STUB_TEMP)
    proc = subprocess.run(args, capture_output=True, timeout=1800, env=env)
    log = T5 / "epf-build-probe.log"
    log.write_text(
        "CMD: %s\n\nRC: %d\n\n--- STDOUT ---\n%s\n\n--- STDERR ---\n%s" % (
            " ".join(args), proc.returncode,
            proc.stdout.decode("cp866", errors="replace"),
            proc.stderr.decode("cp866", errors="replace")),
        encoding="utf-8")
    if proc.returncode != 0:
        die("probe EPF build failed, see %s" % log)
    print("[OK] probe EPF built")


def kill_tree(pid):
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                   capture_output=True)


def run_probe():
    if PROBE_DIR.exists():
        shutil.rmtree(PROBE_DIR)
    PROBE_DIR.mkdir(parents=True)
    if RESULT.exists():
        RESULT.unlink()

    cmd = [str(V8), "/S", CONN, "/RunModeManagedApplication",
           "/N", USER, "/DisableStartupDialogs", "/Execute", str(PROBE_EPF)]
    fp = open(CLIENT_LOG, "wb")
    proc = subprocess.Popen(cmd, stdout=fp, stderr=subprocess.STDOUT)
    data = None
    try:
        start = time.time()
        while time.time() - start < TIMEOUT:
            try:
                data = json.loads(RESULT.read_text(encoding="utf-8-sig"))
            except Exception:
                data = data
            if data and data.get("step") == "done":
                break
            if proc.poll() is not None:
                break
            time.sleep(3)
        else:
            kill_tree(proc.pid)
            die("timeout waiting for probe result")
    finally:
        kill_tree(proc.pid)
        try:
            proc.wait(timeout=10)
        except Exception:
            pass
        fp.close()

    lines = ["[probe] result: " + json.dumps(data, ensure_ascii=False)]
    for i in range(1, 8):
        p = PROBE_DIR / ("p%d.txt" % i)
        if not p.exists():
            lines.append("p%d: NO FILE" % i)
            continue
        raw = p.read_bytes()
        bom = raw.startswith(b"\xef\xbb\xbf")
        crlf = b"\r\n" in raw
        lf = raw.replace(b"\r\n", b"").count(b"\n") > 0
        lines.append("p%d: bom=%s crlf=%s lone_lf=%s head=%s" % (
            i, bom, crlf, lf, raw[:12].hex()))
    for i in range(1, 5):
        p = PROBE_DIR / ("q%d.txt" % i)
        if not p.exists():
            lines.append("q%d: NO FILE" % i)
            continue
        raw = p.read_bytes()
        bom = raw.startswith(b"\xef\xbb\xbf")
        crlf = b"\r\n" in raw
        lf = raw.replace(b"\r\n", b"").count(b"\n") > 0
        tail_cr = raw.endswith(b"\r\n")
        tail_lf = raw.endswith(b"\n")
        lines.append("q%d: bom=%s crlf=%s lone_lf=%s tail_cr=%s tail_lf=%s head=%s" % (
            i, bom, crlf, lf, tail_cr, tail_lf, raw[:12].hex()))
    print("\n".join(lines))
    GATE_LOG.write_text("\n".join(lines), encoding="utf-8")
    print("[OK] -> %s" % GATE_LOG)


if __name__ == "__main__":
    prepare_src()
    build_epf()
    run_probe()
