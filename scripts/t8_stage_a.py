# -*- coding: utf-8 -*-
"""T8 F2: stage-A только (скан -> фикстуры -> генерация), без батчей.

Копия stage-a части scripts/t8_gate.py (TA8 же механизм: АпкРаннер.epf +
runner_task.json + UIA-watchdog). Результат в tmp/t8/runner_result.json.
"""
import io
import json
import os
import subprocess
import time

ROOT = r"C:\MyProjects\APKScenTest"
V8 = r"C:\Program Files\1cv8\8.5.4.1683\bin\1cv8.exe"
CONN = r"localhost\dev_erpapk_demo"
ADMIN = "Администратор (ОрловАВ)"
TARGET = os.path.join(ROOT, "build", "АпкПодготовкаСценарныхТестов.epf")
SETTINGS = os.path.join(ROOT, "tmp", "t8", "preprocessor-settings.json")
RUNS_DIR = os.path.join(ROOT, "tests")

STAGE_A_EPF = os.path.join(ROOT, "tmp", "t8", "epf", "АпкРаннер.epf")
STAGE_A_TASK = os.path.join(ROOT, "tmp", "t8", "runner_task.json")
STAGE_A_RESULT = os.path.join(ROOT, "tmp", "t8", "runner_result.json")
STAGE_A_LOG = os.path.join(ROOT, "tmp", "t8", "client-a.log")
TIMEOUT_STAGE_A = 900

WATCHDOG_PS = r"""
$ErrorActionPreference = 'Continue'
Add-Type -AssemblyName UIAutomationClient
$deadline = (Get-Date).AddSeconds({duration})
$log = '{log}'
$modalTitle = '1С:Предприятие'
$btnName = 'Продолжить'
while ((Get-Date) -lt $deadline) {
  Start-Sleep -Milliseconds 1500
  try {
    $root = [System.Windows.Automation.AutomationElement]::RootElement
    $wins = $root.FindAll([System.Windows.Automation.TreeScope]::Children, [System.Windows.Automation.Condition]::TrueCondition)
    foreach ($w in $wins) {
      if ($w.Current.ClassName -notlike 'V8Window*') { continue }
      if ($w.Current.Name -ne $modalTitle) { continue }
      $btncond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Button)
      $btns = $w.FindAll([System.Windows.Automation.TreeScope]::Descendants, $btncond)
      foreach ($b in $btns) {
        if ($b.Name -eq $btnName) {
          try {
            $p = $b.GetPattern([System.Windows.Automation.InvokePattern]::Pattern)
            $p.Invoke()
            Add-Content -Path $log -Value ('{0} dismissed security modal' -f (Get-Date -Format 'HH:mm:ss')) -Encoding UTF8
          } catch {}
        }
      }
    }
  } catch {}
}
"""


def read_json(path):
    try:
        return json.loads(io.open(path, encoding="utf-8-sig").read())
    except Exception:
        return None


def kill_tree(pid):
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)


def run_1c_session(runner_epf, timeout, client_log, result_file=None):
    fp = open(client_log, "wb")
    proc = subprocess.Popen(
        [V8, "/S", CONN, "/RunModeManagedApplication", "/N", ADMIN,
         "/DisableStartupDialogs", "/Execute", runner_epf],
        stdout=fp, stderr=subprocess.STDOUT)
    try:
        start = time.time()
        while time.time() - start < timeout:
            if result_file and read_json(result_file) is not None:
                data = read_json(result_file)
                if data.get("step") == "done":
                    break
            if proc.poll() is not None:
                break
            time.sleep(3)
        else:
            print("[runner] FAIL: timeout")
            return False
    finally:
        kill_tree(proc.pid)
        try:
            proc.wait(timeout=10)
        except Exception:
            pass
        fp.close()
    return True


def main():
    with io.open(STAGE_A_TASK, "w", encoding="utf-8") as f:
        json.dump({"target": TARGET, "settings": SETTINGS, "runsDir": RUNS_DIR},
                  f, ensure_ascii=False)
    if os.path.exists(STAGE_A_RESULT):
        os.remove(STAGE_A_RESULT)
    wd_ps = WATCHDOG_PS.replace("{duration}", str(TIMEOUT_STAGE_A + 60)).replace(
        "{log}", os.path.join(ROOT, "tmp", "t8", "watchdog-a-f2.log"))
    wd = subprocess.Popen(["powershell", "-NoProfile", "-Command", wd_ps],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        if not run_1c_session(STAGE_A_EPF, TIMEOUT_STAGE_A, STAGE_A_LOG, STAGE_A_RESULT):
            return 1
    finally:
        wd.kill()
    data_a = read_json(STAGE_A_RESULT)
    if not data_a:
        print("[stage-a] FAIL: no result")
        return 1
    print("step=%s errors=%s" % (data_a.get("step"), data_a.get("errorsCount")))
    for e in (data_a.get("errors") or [])[:5]:
        print("   error:", e[:300])
    print("runDir=%s" % data_a.get("runDir"))
    print("scan=%s" % (data_a.get("scanSummary", "")[:200]))
    print("fixtures=%s" % (data_a.get("fixturesSummary", "")[:200]))
    print("features=%s" % (data_a.get("featuresSummary", "")[:200]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
