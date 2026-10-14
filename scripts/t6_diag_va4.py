# -*- coding: utf-8 -*-
"""T6 diag4: VA run + UIA watchdog that clicks through modal dialogs.

If the smoke completes after the watchdog clicks 'Продолжить', root cause
is confirmed: ЗОД/internet-security modal blocks client startup.
"""
import io
import json
import os
import subprocess
import sys
import time

import win32com.client

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"C:\MyProjects\APKScenTest"
V8C = r"C:\Program Files\1cv8\8.5.4.1683\bin\1cv8c.exe"
EPF = r"C:\MyProjects\APKTechPlan\tests\vanessa\vanessa-automation-single.epf"
BASE = r"localhost\dev_erpapk_demo"
ADMIN = "Администратор (ОрловАВ)"
FEATURE = os.path.join(ROOT, "tests", "features", "smoke-01-connect.feature")
DIAG = os.path.join(ROOT, "tmp", "t6", "diag4")
USER = "АпкСценТест_Зонд1"
P1 = "ApkSct-Z1-Orig-2026!q"
P_RUN = "ApkSct-Z1-Diag-2026!x"

ONEC_LOG = os.path.join(DIAG, "1c_out.log")
RUN_LOG = os.path.join(DIAG, "va_run.log")
STATUS_LOG = os.path.join(DIAG, "va_status.log")

WATCHDOG_PS = r"""
$ErrorActionPreference = 'Continue'
Add-Type -AssemblyName UIAutomationClient
$deadline = (Get-Date).AddSeconds(300)
Add-Content -Path $log -Value ('{0} watchdog started' -f (Get-Date -Format 'HH:mm:ss')) -Encoding UTF8
$scanCount = 0
$buttonSeen = @()
$log = '{log}'
$closed = @()
while ((Get-Date) -lt $deadline) {
  Start-Sleep -Milliseconds 1500
  $scanCount++
  if ($scanCount % 20 -eq 0) { Add-Content -Path $log -Value ('{0} scan={1}' -f (Get-Date -Format 'HH:mm:ss'), $scanCount) -Encoding UTF8 }
  try {
    $root = [System.Windows.Automation.AutomationElement]::RootElement
    $wins = $root.FindAll([System.Windows.Automation.TreeScope]::Children, [System.Windows.Automation.Condition]::TrueCondition)
    foreach ($w in $wins) {
      $cn = $w.Current.ClassName
      if ($cn -notlike 'V8Window*') { continue }
      $btncond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Button)
      $btns = $w.FindAll([System.Windows.Automation.TreeScope]::Descendants, $btncond)
      foreach ($b in $btns) {
        $n = $b.Current.Name
        if ($n -eq 'Продолжить' -or $n -eq 'Да' -or $n -eq 'OK') {
$buttonSeen += $n
            try {
            Add-Content -Path $log -Value ('{0} invoking [{1}]' -f (Get-Date -Format 'HH:mm:ss'), $n) -Encoding UTF8
            $p = $b.GetPattern([System.Windows.Automation.InvokePattern]::Pattern)
            $p.Invoke()
            $line = ('{0} clicked [{1}] in win [{2}]' -f (Get-Date -Format 'HH:mm:ss'), $n, $w.Current.Name)
            Add-Content -Path $log -Value $line -Encoding UTF8
          } catch {
            $line = ('{0} FAILED click [{1}]: {2}' -f (Get-Date -Format 'HH:mm:ss'), $n, $_.Exception.Message)
            Add-Content -Path $log -Value $line -Encoding UTF8
          }
        }
      }
    }
  } catch {}
}
"""


def conn_str(usr, pwd):
    return "Srvr='localhost';Ref='dev_erpapk_demo';Usr='%s';Pwd='%s';" % (usr, pwd)


def main():
    os.makedirs(DIAG, exist_ok=True)
    for f in (ONEC_LOG, RUN_LOG, STATUS_LOG):
        if os.path.exists(f):
            os.remove(f)

    agent = win32com.client.Dispatch("V85.COMConnector").Connect(conn_str(ADMIN, ""))
    users = agent.ПользователиИнформационнойБазы
    for u in list(users.ПолучитьПользователей()):
        if u.Имя == USER:
            u.Удалить()
    u = users.СоздатьПользователя()
    u.Имя = USER
    u.ПолноеИмя = "Зонд T6-1 diag (удаляется)"
    u.Пароль = P1
    md = agent.Метаданные.Роли
    for rn in ("ПолныеПрава", "АдминистраторСистемы"):
        u.Роли.Добавить(getattr(md, rn))
    u.ЗащитаОтОпасныхДействий.ПредупреждатьОбОпасныхДействиях = False
    u.Записать()
    for x in users.ПолучитьПользователей():
        if x.Имя == USER:
            x.Пароль = P_RUN
            x.Записать()
    print("[setup] user ready")

    vap_path = os.path.join(DIAG, "VAParams.json")
    vap = {
        "ИмяСборки": "t6-diag4",
        "ВерсияПлатформы": "8.5.4",
        "КаталогПоискаВерсииПлатформы": r"C:\Program Files\1cv8",
        "СтрокаПодключенияКБазе": 'ENTERPRISE /S "%s" /N "%s" /P ""' % (BASE, ADMIN),
        "ПутьКVanessaAutomation": EPF,
        "КаталогФич": FEATURE.replace("\\", "/"),
        "КаталогиБиблиотек": [],
        "КлиентыТестирования": [{
            "Имя": "Основной",
            "ПутьКИнфобазе": '/S "%s" /N "%s" /P "%s"' % (BASE, USER, P_RUN),
            "ДопПараметры": "/DisableStartupMessages /DisableStartupDialogs",
            "ТипКлиента": "Тонкий",
            "ИмяКомпьютера": "localhost",
            "ПортЗапускаТестКлиента": "48401",
        }],
        "ВыполнитьСценарии": "Истина",
        "ЗавершитьРаботуСистемы": "Истина",
        "ЗакрытьTestClientПослеЗапускаСценариев": "Истина",
        "ДелатьЛогВыполненияСценариевВТекстовыйФайл": "Истина",
        "ИмяФайлаЛогВыполненияСценариев": RUN_LOG.replace("\\", "/"),
        "ВыгружатьСтатусВыполненияСценариевВФайл": "Истина",
        "ПутьКФайлуДляВыгрузкиСтатусаВыполненияСценариев": STATUS_LOG.replace("\\", "/"),
        "ДелатьОтчетВФорматеАллюр": "Истина",
        "КаталогВыгрузкиAllureБазовый": os.path.join(DIAG, "allure").replace("\\", "/"),
        "ИмяТекущейСборки": "t6-diag4",
        "ДобавлятьКИмениСценарияУсловияВыгрузки": "Истина",
    }
    with io.open(vap_path, "w", encoding="utf-8") as f:
        json.dump(vap, f, ensure_ascii=False, indent=1)

    wlog = os.path.join(DIAG, "watchdog.log")
    if os.path.exists(wlog):
        os.remove(wlog)
    wd_ps = WATCHDOG_PS.replace("{log}", wlog)
    wd_proc = subprocess.Popen(
        ["powershell", "-NoProfile", "-Command", wd_ps],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    cmd = [V8C, "ENTERPRISE", "/TESTMANAGER", "/S", BASE, "/N", ADMIN,
           "/P", "", "/Out", ONEC_LOG, "/Execute", EPF,
           "/C", "StartFeaturePlayer;VAParams=%s" % vap_path]
    print("[diag4] launching VA client")
    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    while time.time() - t0 < 420:
        time.sleep(10)
        dt = int(time.time() - t0)
        alive = proc.poll() is None
        st = ""
        if os.path.exists(STATUS_LOG):
            st = io.open(STATUS_LOG, encoding="utf-8-sig", errors="replace").read().strip()
        va_size = os.path.getsize(RUN_LOG) if os.path.exists(RUN_LOG) else -1
        print("[t=%3ds] alive=%s status='%s' va.log=%d" % (dt, alive, st, va_size))
        if not alive:
            print("[diag4] VA client exited at t=%d" % dt)
            break
    else:
        print("[diag4] 420s elapsed, killing tree")
    subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
    try:
        wd_proc.kill()
    except Exception:
        pass
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    "Get-CimInstance Win32_Process -Filter \"Name='1cv8c.exe'\" | "
                    "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"],
                   capture_output=True, timeout=60)
    for x in users.ПолучитьПользователей():
        if x.Имя == USER:
            x.Удалить()
    print("[diag4] user deleted")
    if os.path.exists(wlog):
        print("=== watchdog.log ===")
        print(io.open(wlog, encoding="utf-8", errors="replace").read())
    if os.path.exists(RUN_LOG):
        print("=== va_run.log ===")
        print(io.open(RUN_LOG, encoding="utf-8", errors="replace").read()[:2500])


if __name__ == "__main__":
    main()
