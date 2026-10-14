# -*- coding: utf-8 -*-
"""T6 diag v3: launch VA, wait, dump UIA tree of 1C windows, try closing ITS monitor."""
import os
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"C:\MyProjects\APKScenTest"
V8C = r"C:\Program Files\1cv8\8.5.4.1683\bin\1cv8c.exe"
EPF = r"C:\MyProjects\APKTechPlan\tests\vanessa\vanessa-automation-single.epf"
BASE = r"localhost\dev_erpapk_demo"
ADMIN = "Администратор (ОрловАВ)"
DIAG = os.path.join(ROOT, "tmp", "t6", "diag3")

UIA_PS = r"""
Add-Type -AssemblyName UIAutomationClient
$root = [System.Windows.Automation.AutomationElement]::RootElement
$cond = [System.Windows.Automation.Condition]::TrueCondition
$wins = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $cond)
if ($wins.Count -gt 6) { $wins = $wins | Select-Object -First 6 }
foreach ($w in $wins) {
  '=== WIN: ' + $w.Current.Name
  $wc = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Window)
  $all = $w.FindAll([System.Windows.Automation.TreeScope]::Descendants, [System.Windows.Automation.Condition]::TrueCondition)
  foreach ($e in $all) {
    $n = $e.Current.Name
    if ($n) {
      $t = $e.Current.ControlType.ProgrammaticName
      '  [' + $t + '] ' + $n.Substring(0, [Math]::Min(160, $n.Length))
    }
  }
}
"""


def uia_dump():
    out = subprocess.run(["powershell", "-NoProfile", "-Command", UIA_PS],
                         capture_output=True, timeout=180)
    return out.stdout.decode("utf-8", errors="replace")


def main():
    os.makedirs(DIAG, exist_ok=True)
    vap = os.path.join(DIAG, "VAParams.json")
    cmd = [V8C, "ENTERPRISE", "/TESTMANAGER", "/S", BASE, "/N", ADMIN,
           "/P", "", "/Out", os.path.join(DIAG, "1c_out.log"),
           "/Execute", EPF]
    print("[diag3] launching VA TestManager (no feature start)")
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(60)
    print("[diag3] UIA dump at t=60s")
    print(uia_dump())
    time.sleep(30)
    print("[diag3] UIA dump at t=90s")
    print(uia_dump())
    subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
    print("[diag3] done")


if __name__ == "__main__":
    main()
