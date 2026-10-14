# -*- coding: utf-8 -*-
"""T6 Gate: собрать раннер-EPF (runner_src -> tmp/t6/epf/АпкРаннер.epf).

TEMP-патч обязателен (8.3-короткий $env:TEMP ломает epf-build cleanup).
"""
import os
import subprocess
import sys

SKILL_PS1 = r"C:\MyProjects\PiPack\skills\1c\epf-build\scripts\epf-build.ps1"
V8_BIN = r"C:\Program Files\1cv8\8.5.4.1683\bin"
SRC_XML = r"C:\MyProjects\APKScenTest\tmp\t6\runner_src\АпкРаннер.xml"
OUT_EPF = r"C:\MyProjects\APKScenTest\tmp\t6\epf\АпкРаннер.epf"
LOG = r"C:\MyProjects\APKScenTest\tmp\t6\epf-build-runner.log"

args = [
    "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
    "-File", SKILL_PS1,
    "-V8Path", V8_BIN,
    "-SourceFile", SRC_XML,
    "-OutputFile", OUT_EPF,
]

env = os.environ.copy()
stub_temp = "C:/MyProjects/APKScenTest/tmp/t6/stubtemp"
os.makedirs(stub_temp, exist_ok=True)
env["TEMP"] = stub_temp
env["TMP"] = stub_temp
proc = subprocess.run(args, capture_output=True, timeout=1800, env=env)
out = proc.stdout.decode("cp866", errors="replace")
err = proc.stderr.decode("cp866", errors="replace")
with open(LOG, "w", encoding="utf-8") as f:
    f.write("CMD: " + " ".join(args) + "\n\n")
    f.write("RC: %d\n\n--- STDOUT ---\n%s\n\n--- STDERR ---\n%s\n" % (proc.returncode, out, err))
print("rc=%d" % proc.returncode)
tail = out[-2500:]
print("Build completed successfully" in tail and "[OK] built" or "[see log]")
sys.exit(proc.returncode)
