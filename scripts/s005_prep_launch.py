# -*- coding: utf-8 -*-
"""s005 live: launch preprocessor EPF in dev_erpapk_demo (detached) + watchdog."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s005_uia_lib import launch, watchdog_start, TMP, log

epf = os.path.join(TMP, "..", "..", "dist", "АпкПодготовкаСценарныхТестов.epf")
epf = os.path.normpath(epf)
client_log = os.path.join(TMP, "prep_1c.log")
proc, fp = launch(epf, client_log)
open(os.path.join(TMP, "prep_pid.txt"), "w").write(str(proc.pid))
watchdog_start(3600 * 4, "prep_watchdog.log")
log("launched pid=%d, log=%s" % (proc.pid, client_log))
