# -*- coding: utf-8 -*-
"""T6 diag v2: VA run with clean artifacts, full process/port monitoring."""
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time

import win32com.client

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"C:\MyProjects\APKScenTest"
V8C = r"C:\Program Files\1cv8\8.5.4.1683\bin\1cv8c.exe"
EPF = r"C:\MyProjects\APKTechPlan\tests\vanessa\vanessa-automation-single.epf"
BASE = r"localhost\dev_erpapk_demo"
ADMIN = "Администратор (ОрловАВ)"
FEATURE = os.path.join(ROOT, "tests", "features", "smoke-01-connect.feature")
DIAG = os.path.join(ROOT, "tmp", "t6", "diag2")
USER = "АпкСценТест_Зонд1"
P1 = "ApkSct-Z1-Orig-2026!q"
P_RUN = "ApkSct-Z1-Diag-2026!x"

ONEC_LOG = os.path.join(DIAG, "1c_out.log")
RUN_LOG = os.path.join(DIAG, "va_run.log")
STATUS_LOG = os.path.join(DIAG, "va_status.log")
VAP = os.path.join(DIAG, "VAParams.json")


def conn_str(usr, pwd):
    return "Srvr='localhost';Ref='dev_erpapk_demo';Usr='%s';Pwd='%s';" % (usr, pwd)


def proc_snapshot():
    ps = r"""
Get-CimInstance Win32_Process -Filter "Name='1cv8c.exe'" | ForEach-Object {
  'PID=' + $_.ProcessId + ' CMD=' + $_.CommandLine
}
"""
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, timeout=60)
    return [l for l in out.stdout.decode("utf-8", "replace").splitlines()
            if l.startswith("PID=")]


def port_up():
    try:
        s = socket.socket()
        s.settimeout(1)
        s.connect(("127.0.0.1", 48000))
        s.close()
        return True
    except Exception:
        return False


def main():
    if os.path.isdir(DIAG):
        shutil.rmtree(DIAG)
    os.makedirs(DIAG)

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
        "ИмяСборки": "t6-diag2",
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
        "ПутьКФайлуДляВыгрузкиСтатусаВыполненияСценариев":
            STATUS_LOG.replace("\\", "/"),
        "ДелатьОтчетВФорматеАллюр": "Истина",
        "КаталогВыгрузкиAllureБазовый": os.path.join(DIAG, "allure").replace("\\", "/"),
        "ИмяТекущейСборки": "t6-diag2",
        "ДобавлятьКИмениСценарияУсловияВыгрузки": "Истина",
    }
    with io.open(VAP, "w", encoding="utf-8") as f:
        json.dump(vap, f, ensure_ascii=False, indent=1)

    cmd = [V8C, "ENTERPRISE", "/TESTMANAGER", "/S", BASE, "/N", ADMIN,
           "/P", "", "/Out", ONEC_LOG, "/Execute", EPF,
           "/C", "StartFeaturePlayer;VAParams=%s" % VAP]
    print("[diag] launching VA client")
    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    seen_pids = set()
    while time.time() - t0 < 420:
        time.sleep(10)
        dt = int(time.time() - t0)
        alive = proc.poll() is None
        st = ""
        if os.path.exists(STATUS_LOG):
            st = io.open(STATUS_LOG, encoding="utf-8-sig", errors="replace").read().strip()
        va_size = os.path.getsize(RUN_LOG) if os.path.exists(RUN_LOG) else -1
        snaps = proc_snapshot()
        new = [s for s in snaps if s not in seen_pids]
        if new:
            for s in new:
                print("  [proc+] %s" % s[:220])
            seen_pids.update(new)
        print("[t=%3ds] alive=%s status='%s' va.log=%d portup=%s procs=%d"
              % (dt, alive, st, va_size, port_up(), len(snaps)))
        if not alive:
            print("[diag] VA client exited at t=%d" % dt)
            break
    else:
        print("[diag] 420s elapsed, killing tree")
    subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                   capture_output=True)
    time.sleep(2)
    # kill any leftover TestClients (they listen on 48000)
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    "Get-CimInstance Win32_Process -Filter \"Name='1cv8c.exe'\" | "
                    "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"],
                   capture_output=True, timeout=60)
    for x in users.ПолучитьПользователей():
        if x.Имя == USER:
            x.Удалить()
    print("[diag] user deleted")
    if os.path.exists(RUN_LOG):
        print("=== va_run.log ===")
        print(io.open(RUN_LOG, encoding="utf-8", errors="replace").read()[:2500])


if __name__ == "__main__":
    main()
