# -*- coding: utf-8 -*-
"""T7 Gate: прогон СобратьОтчет на артефактах T6 (staging tmp/t7/run-report).

Механизм (спайк-паттерн T4/T6): клиентский сеанс 1cv8 /Execute раннер-EPF,
который подключает целевой EPF и вызывает его экспортную СобратьОтчет
на каталоге прогона; результат - tmp/t7/runner_result.json.
UIA-watchdog закрывает модальное предупреждение безопасности 1С 8.5.
"""
import json
import os
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"C:\MyProjects\APKScenTest"
V8 = r"C:\Program Files\1cv8\8.5.4.1683\bin\1cv8.exe"
CONN = r"localhost\dev_erpapk_demo"
ADMIN = "Администратор (ОрловАВ)"
TARGET = os.path.join(ROOT, "build", "АпкПодготовкаСценарныхТестов.epf")
RUNNER_EPF = os.path.join(ROOT, "tmp", "t7", "epf", "АпкРаннер.epf")
TASK = os.path.join(ROOT, "tmp", "t7", "runner_task.json")
RESULT = os.path.join(ROOT, "tmp", "t7", "runner_result.json")
CLIENT_LOG = os.path.join(ROOT, "tmp", "t7", "client.log")
GATE_LOG = os.path.join(ROOT, "tmp", "t7", "gate-report.log")
RUN_DIR = os.path.join(ROOT, "tmp", "t7", "run-report")
DRIVER_TIMEOUT = 300

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


def read_result():
    try:
        with open(RESULT, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return None


def main():
    with open(TASK, "w", encoding="utf-8") as f:
        json.dump({"target": TARGET, "runDir": RUN_DIR}, f, ensure_ascii=False, indent=1)
    if os.path.exists(RESULT):
        os.remove(RESULT)

    wd_log = os.path.join(ROOT, "tmp", "t7", "watchdog.log")
    if os.path.exists(wd_log):
        os.remove(wd_log)
    wd_ps = WATCHDOG_PS.replace("{duration}", str(DRIVER_TIMEOUT + 60)).replace("{log}", wd_log)
    wd_proc = subprocess.Popen(["powershell", "-NoProfile", "-Command", wd_ps],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    cmd = [V8, "/S", CONN, "/RunModeManagedApplication", "/N", ADMIN,
           "/DisableStartupDialogs", "/Execute", RUNNER_EPF]
    fp = open(CLIENT_LOG, "wb")
    proc = subprocess.Popen(cmd, stdout=fp, stderr=subprocess.STDOUT)
    data = None
    try:
        start = time.time()
        while time.time() - start < DRIVER_TIMEOUT:
            data = read_result()
            if data and data.get("step") == "done":
                break
            if proc.poll() is not None:
                time.sleep(2)
                data = data or read_result()
                break
            time.sleep(3)
        else:
            print("[runner] FAIL: таймаут драйвера %dc" % DRIVER_TIMEOUT)
    finally:
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
        try:
            proc.wait(timeout=10)
        except Exception:
            pass
        fp.close()
        wd_proc.kill()

    lines = []
    if data is None:
        print("[FAIL] результат недоступен")
        return 1
    lines.append("step=%s errors=%s" % (data.get("step"), data.get("errorsCount")))
    for e in (data.get("errors") or [])[:5]:
        lines.append("  error: %s" % e[:300])
    lines.append("runId=%s" % data.get("runId"))
    lines.append("summaryJson=%s" % data.get("summaryJson"))
    lines.append("summaryMd=%s" % data.get("summaryMd"))
    lines.append("totals=%s" % json.dumps(data.get("totals"), ensure_ascii=False))
    lines.append("scenarioCount=%s" % data.get("scenarioCount"))
    for b in data.get("batchStatuses") or []:
        lines.append("batch: %s" % json.dumps(b, ensure_ascii=False))
    ok = data.get("step") == "done" and not data.get("errorsCount")
    lines.append("VERDICT: %s" % ("PASS" if ok else "FAIL"))
    for ln in lines:
        print(ln)
    with open(GATE_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
