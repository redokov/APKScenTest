# -*- coding: utf-8 -*-
"""T6: terminate hanged (hibernated, client-less) sessions on dev_erpapk_demo.

Safety:
- only infobase c6a442bb-d7a9-4d8b-a274-37ea859b26c1 (dev_erpapk_demo)
- only app-id 1CV8 / 1CV8C with hibernate=yes
- never touch app-id BackgroundJob / RAS / JobScheduler / Designer
- prints every decision; refuses to terminate anything else.
Usage: python scripts/t6_cleanup_sessions.py [--dry]
"""
import re
import subprocess
import sys

RAC = r"C:\Program Files\1cv8\8.5.4.1683\bin\rac.exe"
HOST = "127.0.0.1"
CLUSTER = "67cdef87-7bfc-4dae-b8e4-3ea9f8529156"
TARGET_IB = "c6a442bb-d7a9-4d8b-a274-37ea859b26c1"  # dev_erpapk_demo
SAFE_APPIDS = {"1CV8", "1CV8C"}

dry = "--dry" in sys.argv


def rac_session_list():
    out = subprocess.run(
        [RAC, "session", HOST, "list", "--cluster=" + CLUSTER],
        capture_output=True)
    return out.stdout.decode("utf-8", errors="replace")


def field(block, key):
    m = re.search(r"^%s\s*:\s*(.*)$" % key, block, re.M)
    return m.group(1).strip() if m else ""


def main():
    txt = rac_session_list()
    blocks = txt.split("session                          : ")[1:]
    victims, kept = [], []
    for b in blocks:
        sid = b.split("\n")[0].strip()
        ib = field(b, "infobase")
        app = field(b, "app-id")
        hib = field(b, "hibernate")
        last = field(b, "last-active-at")
        if ib == TARGET_IB and app in SAFE_APPIDS and hib == "yes":
            victims.append((sid, app, last))
        elif ib == TARGET_IB:
            kept.append((sid, app, "protected"))
    print("candidates to terminate: %d" % len(victims))
    print("protected on target ib: %s" % (kept,))
    done, failed = 0, []
    for sid, app, last in victims:
        if dry:
            print("[dry] would terminate %s (%s, last %s)" % (sid, app, last))
            continue
        r = subprocess.run(
            [RAC, "session", HOST, "terminate",
             "--cluster=" + CLUSTER, "--session=" + sid],
            capture_output=True)
        ok = r.returncode == 0
        if ok:
            done += 1
        else:
            failed.append((sid, r.returncode,
                           r.stdout.decode("utf-8", "replace")[:100] +
                           r.stderr.decode("utf-8", "replace")[:100]))
        print("terminate %s -> rc=%d" % (sid, r.returncode))
    print("terminated=%d failed=%d" % (done, len(failed)))
    for f in failed:
        print("  FAIL:", f)


if __name__ == "__main__":
    main()
