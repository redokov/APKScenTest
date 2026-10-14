# -*- coding: utf-8 -*-
"""Dump 1C client error dialog text via UIA (license diagnostics), v2.

Проверяет, жив ли клиентский процесс; если жив — снимает текст окна.
"""
import subprocess
import time

V8C = r"C:\Program Files\1cv8\8.5.4.1683\bin\1cv8c.exe"
CONN = r"localhost\dev_erpapk_demo"

proc = subprocess.Popen(
    [V8C, "ENTERPRISE", "/S", CONN, "/DisableStartupDialogs"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("pid", proc.pid)
alive = []
for i in range(20):
    time.sleep(1)
    rc = proc.poll()
    alive.append(rc)
    if rc is not None:
        break
print("poll:", alive[-1], "seconds alive:", len(alive))

ps = r"""
Add-Type -AssemblyName UIAutomationClient
$root = [System.Windows.Automation.AutomationElement]::RootElement
$wins = $root.FindAll([System.Windows.Automation.TreeScope]::Children, [System.Windows.Automation.Condition]::TrueCondition)
foreach ($w in $wins) {
  if ($w.Current.ClassName -notlike '*V8*' -and $w.Current.Name -notlike '*1*') { continue }
  Write-Output ('WIN: [' + $w.Current.Name + '] class=' + $w.Current.ClassName)
  $texts = $w.FindAll([System.Windows.Automation.TreeScope]::Descendants, [System.Windows.Automation.Condition]::TrueCondition)
  foreach ($t in $texts) {
    try { if ($t.Current.Name) { Write-Output ('  - ' + $t.Current.ControlType.ProgrammaticName + ': ' + $t.Current.Name) } } catch {}
  }
}
"""
p = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                   capture_output=True, timeout=120)
out = p.stdout.decode("cp866", errors="replace")
io = open(r"c:\MyProjects\APKScenTest\tmp\t6\lic_windows.txt", "w", encoding="utf-8")
io.write(out)
io.close()
if proc.poll() is None:
    proc.kill()
print("done")
