# -*- coding: utf-8 -*-
"""T1 probe: DESIGNER batch DumpIB на dev_erpapk_demo (спека 003, tasks T1).

Фиксирует: работоспособность /DumpIB на серверной ИБ, время, размер dt,
код результата (/DumpResult), поведение /Out-лога. RestoreIB проверяется
в T5 на реальном цикле; здесь только dump-факты.
"""
import io
import os
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

V8 = r"C:\Program Files\1cv8\8.5.4.1683\bin\1cv8.exe"
CONN = r"localhost\dev_erpapk_demo"
ADMIN = "Администратор (ОрловАВ)"

ROOT = r"C:\MyProjects\APKScenTest"
PROBE_DIR = os.path.join(ROOT, "tmp", "regress", "probe")
DT = os.path.join(PROBE_DIR, "pre-update-probe.dt")
OUT_LOG = os.path.join(PROBE_DIR, "dump.log")
DUMP_RESULT = os.path.join(PROBE_DIR, "dump-result.txt")
FACTS = os.path.join(PROBE_DIR, "t1-facts.md")


def main():
    os.makedirs(PROBE_DIR, exist_ok=True)
    for p in (DT, OUT_LOG, DUMP_RESULT):
        if os.path.exists(p):
            os.remove(p)

    free = shutil_free(PROBE_DIR)
    print("[preflight] free space on probe dir volume: %.1f GB" % free)

    cmd = [V8, "DESIGNER", "/S", CONN, "/N" + ADMIN,
           "/DumpIB", DT, "/Out", OUT_LOG, "/DumpResult", DUMP_RESULT]
    print("[dump] starting: 1cv8 DESIGNER /S %s /N*** /DumpIB %s" % (CONN, DT))
    t0 = time.time()
    proc = subprocess.run(cmd, capture_output=True, timeout=1500)
    dur = time.time() - t0
    print("[dump] exit=%s duration=%.1fs" % (proc.returncode, dur))

    result_code = None
    if os.path.exists(DUMP_RESULT):
        result_code = io.open(DUMP_RESULT, encoding="utf-8-sig",
                              errors="replace").read().strip()
    size_mb = os.path.getsize(DT) / 1024.0 / 1024.0 if os.path.exists(DT) else 0
    print("[dump] DumpResult=%s dt_size=%.1f MB" % (result_code, size_mb))

    tail = ""
    if os.path.exists(OUT_LOG):
        lines = io.open(OUT_LOG, encoding="utf-8-sig",
                        errors="replace").read().splitlines()
        tail = "\n".join(lines[-12:])

    with io.open(FACTS, "w", encoding="utf-8") as f:
        f.write(u"# T1 facts: DESIGNER batch DumpIB probe\n\n")
        f.write(u"- date: %s\n" % time.strftime("%Y-%m-%d %H:%M"))
        f.write(u"- command: 1cv8 DESIGNER /S %s /N*** /DumpIB <dt> "
                u"/Out <log> /DumpResult <file>\n" % CONN)
        f.write(u"- exit code: %s\n" % proc.returncode)
        f.write(u"- DumpResult: %s\n" % result_code)
        f.write(u"- duration: %.1f s\n" % dur)
        f.write(u"- dt size: %.1f MB\n" % size_mb)
        f.write(u"- free space before: %.1f GB\n" % free)
        f.write(u"\n## /Out tail\n\n```\n%s\n```\n" % tail)
    print("[facts] written: %s" % FACTS)
    if tail:
        print("[out-tail]\n%s" % tail)
    return 0 if (proc.returncode == 0 and size_mb > 0) else 1


def shutil_free(path):
    import shutil
    total, used, free = shutil.disk_usage(path)
    return free / 1024.0 / 1024.0 / 1024.0


if __name__ == "__main__":
    sys.exit(main())
