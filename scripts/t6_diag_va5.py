# -*- coding: utf-8 -*-
"""T6 diag5: production-launch replication via WScript.Shell.Exec from python.

Goal: isolate why the production path (1C client -> WScript.Shell.Exec ->
cmd /c -> 1cv8c ENTERPRISE /TESTMANAGER) hangs while a direct python
Popen launch (tmp/t6/diag4) succeeds.

What this does:
- creates temp user Zond1 (COM), ZOD off, sets test password
- writes VAParams.json into tmp/t6/diag5 (same content as production)
- builds the EXACT command line the BSL runner builds (cmd /c "..." with
  the extra outer quotes) and launches it via WScript.Shell.Exec
  (same COM object WScript.Shell, same StdOut pipe nobody reads)
- polls status/log files, snapshots processes (CIM) and top-level windows
- on timeout kills ONLY the tree it started
- deletes the temp user

Never touches other users / sessions.
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
ADMIN = "Администратор (ОрловАВ)"  # typo fix: was ОловАВ
FEATURE = os.path.join(ROOT, "tests", "features", "smoke-01-connect.feature")
DIAG = os.path.join(ROOT, "tmp", "t6", "diag5")
USER = "АпкСценТест_Зонд1"
P1 = "ApkSct-Z1-Orig-2026!q"
P_RUN = "ApkSct-Z1-Diag-2026!x"

ONEC_LOG = os.path.join(DIAG, "1c_out.log")
RUN_LOG = os.path.join(DIAG, "va_run.log")
STATUS_LOG = os.path.join(DIAG, "va_status.log")
VAP = os.path.join(DIAG, "VAParams.json")

# stdout redirection control: prod replication = no redirect (pipes unread)
REDIRECT = os.environ.get("DIAG5_REDIRECT", "") == "1"

TIMEOUT = 420


def conn_str(usr, pwd):
    return "Srvr='localhost';Ref='dev_erpapk_demo';Usr='%s';Pwd='%s';" % (usr, pwd)


def proc_snapshot(own_pid):
    """CIM snapshot of console/1c processes with command lines."""
    ps = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(1cv8|1cv8c|cmd|conhost)\\.exe$' } | "
         "Select-Object ProcessId,ParentProcessId,Name,CommandLine | ConvertTo-Json -Compress"],
        capture_output=True, text=True, timeout=60)
    try:
        rows = json.loads(ps.stdout)
    except Exception:
        rows = ps.stdout.strip().splitlines()
    if isinstance(rows, dict):
        rows = [rows]
    out = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        out.append("pid=%s ppid=%s %s :: %s" % (
            r.get("ProcessId"), r.get("ParentProcessId"), r.get("Name"),
            (r.get("CommandLine") or "")[:200]))
    return out


def window_titles():
    titles = []

    def cb(hwnd, _):
        import win32gui
        if win32gui.IsWindowVisible(hwnd):
            t = win32gui.GetWindowText(hwnd)
            if t:
                titles.append(t[:80])
    try:
        import win32gui
        win32gui.EnumWindows(cb, None)
    except Exception as e:
        titles.append("enumfail: %s" % str(e)[:60])
    return titles


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

    vap = {
        "ИмяСборки": "t6-diag5",
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
            "ПортЗапускаТестКлиента": "48501",
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
        "ИмяТекущейСборки": "t6-diag5",
        "ДобавлятьКИмениСценарияУсловияВыгрузки": "Истина",
    }
    with io.open(VAP, "w", encoding="utf-8") as f:
        json.dump(vap, f, ensure_ascii=False, indent=1)

    # === EXACT production command construction (Module.bsl КомандаЗапускаБатча) ===
    inner = ('"%s" ENTERPRISE /TESTMANAGER /S "%s" /N "%s" /P "%s" /Out "%s" '
             '/Execute "%s" /C "%s"') % (
        V8C, BASE, ADMIN, "", ONEC_LOG, EPF,
        "StartFeaturePlayer;VAParams=" + VAP)
    cmd = 'cmd /c "' + inner + '"'
    if REDIRECT:
        cmd = 'cmd /c "' + inner + ' > nul 2>&1"'
    print("[cmd] %s" % cmd)

    wsh = win32com.client.Dispatch("WScript.Shell")
    t0 = time.time()
    proc = wsh.Exec(cmd)
    my_pid = proc.ProcessID
    print("[diag5] launched, cmd-pid=%s" % my_pid)

    finished = False
    while time.time() - t0 < TIMEOUT:
        time.sleep(10)
        dt = int(time.time() - t0)
        alive = proc.Status == 0
        st = ""
        if os.path.exists(STATUS_LOG):
            st = io.open(STATUS_LOG, encoding="utf-8-sig", errors="replace").read().strip()
        va_size = os.path.getsize(RUN_LOG) if os.path.exists(RUN_LOG) else -1
        print("[t=%3ds] alive=%s status='%s' va.log=%d" % (dt, alive, st, va_size))
        if dt % 30 == 0:
            for row in proc_snapshot(my_pid):
                print("   proc: %s" % row)
            print("   wins: %s" % (" | ".join(window_titles())[:400]))
        if not alive:
            finished = True
            print("[diag5] cmd exited at t=%d rs=%s" % (dt, proc.ExitCode))
            break

    if not finished:
        print("[diag5] TIMEOUT: killing tree pid=%s" % my_pid)
        subprocess.run(["taskkill", "/PID", str(my_pid), "/T", "/F"], capture_output=True)
        time.sleep(3)

    for x in users.ПолучитьПользователей():
        if x.Имя == USER:
            x.Удалить()
    print("[diag5] user deleted")

    st = ""
    if os.path.exists(STATUS_LOG):
        st = io.open(STATUS_LOG, encoding="utf-8-sig", errors="replace").read().strip()
    print("=== RESULT: finished=%s status='%s' ===" % (finished, st))
    if os.path.exists(RUN_LOG):
        print("=== va_run.log ===")
        print(io.open(RUN_LOG, encoding="utf-8", errors="replace").read()[:2500])


if __name__ == "__main__":
    main()
