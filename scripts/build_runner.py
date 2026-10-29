# -*- coding: utf-8 -*-
"""Build ApkRunner EPF from src/ApkRunner canonical sources (spec 005 T5/T4).

TEMP-stub required (short 8.3 $env:TEMP breaks epf-build cleanup).
"""
import os
import subprocess
import sys

SKILL_PS1 = r"C:\MyProjects\PiPack\skills\1c\epf-build\scripts\epf-build.ps1"
V8_BIN = r"C:\Program Files\1cv8\8.5.4.1683\bin"
SRC_XML = r"C:\MyProjects\APKScenTest\src\АпкРаннер\АпкРаннер.xml"
OUT_EPF = r"C:\MyProjects\APKScenTest\build\АпкРаннер.epf"
LOG = r"C:\MyProjects\APKScenTest\tmp\s005\epf-build-runner.log"

os.makedirs(os.path.dirname(LOG), exist_ok=True)
args = [
    "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
    "-File", SKILL_PS1,
    "-V8Path", V8_BIN,
    "-SourceFile", SRC_XML,
    "-OutputFile", OUT_EPF,
]
env = os.environ.copy()
stub_temp = "C:/MyProjects/APKScenTest/tmp/s005/stubtemp"
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
print("[OK] built" if proc.returncode == 0 and "Build completed successfully" in out[-2500:] else "[see log] %s" % LOG)
sys.exit(proc.returncode)
