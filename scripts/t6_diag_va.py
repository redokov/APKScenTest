# -*- coding: utf-8 -*-
"""T6 diagnostic: run VA batch manually and watch what the client does.

Mirrors the runner batch exactly (cmd /c line, same VAParams), polls
status/log files, window titles, and takes screenshots.
"""
import glob
import io
import json
import os
import subprocess
import sys
import time

import threading

import win32com.client

ROOT = r"C:\MyProjects\APKScenTest"
V8C = r"C:\Program Files\1cv8\8.5.4.1683\bin\1cv8c.exe"
EPF = r"C:\MyProjects\APKTechPlan\tests\vanessa\vanessa-automation-single.epf"
BASE = r"localhost\dev_erpapk_demo"
ADMIN = "Администратор (ОрловАВ)"
FEATURE = os.path.join(ROOT, "tests", "features", "smoke-01-connect.feature")
DIAG = os.path.join(ROOT, "tmp", "t6", "diag")
USER = "АпкСценТест_Зонд1"
P1 = "ApkSct-Z1-Orig-2026!q"
P_RUN = "ApkSct-Z1-Diag-2026!x"

sys.stdout.reconfigure(encoding="utf-8")


def conn_str(usr, pwd):
    return "Srvr='localhost';Ref='dev_erpapk_demo';Usr='%s';Pwd='%s';" % (usr, pwd)


def find_user(users, name):
    for u in users.ПолучитьПользователей():
        if u.Имя == name:
            return u
    return None


def window_titles():
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-Process | Where-Object {$_.MainWindowTitle} | "
             "Where-Object {$_.Name -like '1cv8*'} | "
             "ForEach-Object { $_.Id.ToString() + ' :: ' + $_.MainWindowTitle }"],
            capture_output=True, timeout=30)
        return out.stdout.decode("utf-8", errors="replace").strip().splitlines()
    except Exception as e:
        return ["<err %s>" % e]


def screenshot(tag):
    path = os.path.join(DIAG, "shot-%s.png" % tag)
    ps = r"""
Add-Type -AssemblyName System.Windows.Forms,System.Drawing
$b = [System.Windows.Forms.SystemInformation]::VirtualScreen
$w = $b.Width; $h = $b.Height
$bmp = New-Object System.Drawing.Bitmap $w, $h
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($b.Left, $b.Top, 0, 0, $bmp.Size)
$bmp.Save('%s')
$g.Dispose(); $bmp.Dispose()
""" % path.replace("\\", "\\")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                   capture_output=True, timeout=60)
    return path


def main():
    os.makedirs(DIAG, exist_ok=True)
    agent = win32com.client.Dispatch("V85.COMConnector").Connect(conn_str(ADMIN, ""))
    users = agent.ПользователиИнформационнойБазы

    # setup user
    old = find_user(users, USER)
    if old is not None:
        old.Удалить()
    u = users.СоздатьПользователя()
    u.Имя = USER
    u.ПолноеИмя = "Зонд T6-1 diag (удаляется)"
    u.Пароль = P1
    md_roles = agent.Метаданные.Роли
    for rn in ("ПолныеПрава", "АдминистраторСистемы"):
        u.Роли.Добавить(getattr(md_roles, rn))
    u.ЗащитаОтОпасныхДействий.ПредупреждатьОбОпасныхДействиях = False
    u.Записать()
    u2 = find_user(users, USER)
    u2.Пароль = P_RUN
    u2.Записать()

    vap = os.path.join(DIAG, "VAParams.json").replace("\\", "/")
    onec_log = os.path.join(DIAG, "1c_out.log")
    run_log = os.path.join(DIAG, "va_run.log")
    status_log = os.path.join(DIAG, "va_status.log")
    vap_d = {
        "ТаймаутЗапуска1С": "300",
        "ИмяСборки": "t6-diag",
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
        "ИмяФайлаЛогВыполненияСценариев": run_log.replace("\\", "/"),
        "ВыгружатьСтатусВыполненияСценариевВФайл": "Истина",
        "ПутьКФайлуДляВыгрузкиСтатусаВыполненияСценариев": status_log.replace("\\", "/"),
        "ДелатьОтчетВФорматеАллюр": "Истина",
        "КаталогВыгрузкиAllureБазовый": os.path.join(DIAG, "allure").replace("\\", "/"),
        "ИмяТекущейСборки": "t6-diag",
        "ДобавлятьКИмениСценарияУсловияВыгрузки": "Истина",
    }
    with io.open(vap, "w", encoding="utf-8") as f:
        json.dump(vap_d, f, ensure_ascii=False, indent=1)

    cmd = [V8C, "ENTERPRISE", "/TESTMANAGER", "/S", BASE, "/N", ADMIN,
           "/P", "", "/Out", onec_log, "/Execute", EPF,
           "/C", "StartFeaturePlayer;VAParams=%s" % vap]
    logf = io.open(os.path.join(DIAG, "diag.log"), "w", encoding="utf-8")

    def dlog(m):
        print(m)
        logf.write(m + "\n")
        logf.flush()

    bind_events = []

    def bind_monitor():
        import socket as sk
        while True:
            time.sleep(0.5)
            try:
                s = sk.socket(); s.settimeout(1)
                s.connect(("127.0.0.1", 48000)); s.close()
                bind_events.append(("up", time.time()))
                # detect down
                while True:
                    time.sleep(0.5)
                    try:
                        s2 = sk.socket(); s2.settimeout(1)
                        s2.connect(("127.0.0.1", 48000)); s2.close()
                    except Exception:
                        bind_events.append(("down", time.time()))
                        break
            except Exception:
                pass

    th = threading.Thread(target=bind_monitor, daemon=True)
    th.start()
    t_launch = time.time()
    dlog("[diag] launching VA client")
    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    seen_status = None
    shots = 0
    while time.time() - t0 < 600:
        time.sleep(10)
        dt = int(time.time() - t0)
        st = ""
        if os.path.exists(status_log):
            st = io.open(status_log, encoding="utf-8-sig", errors="replace").read().strip()
        onec_size = os.path.getsize(onec_log) if os.path.exists(onec_log) else -1
        va_size = os.path.getsize(run_log) if os.path.exists(run_log) else -1
        alive = proc.poll() is None
        dlog("[t=%3ds] alive=%s status='%s' 1c.log=%d va.log=%d bind=%s"
             % (dt, alive, st, onec_size, va_size,
                [(e, "%.1fs" % (ts - t_launch)) for e, ts in bind_events[-3:]]))
        if not alive:
            dlog("[diag] client exited at t=%d" % dt)
            break
        if st and seen_status is None:
            seen_status = st
            dlog("[diag] status appeared; windows:")
            for w in window_titles():
                dlog("   win: %s" % w)
            screenshot("status-%d" % dt)
            shots += 1
        if dt in (120, 240, 360, 480):
            for w in window_titles():
                dlog("   win: %s" % w)
            screenshot("t%d" % dt)
            shots += 1
    alive = proc.poll() is None
    if alive:
        dlog("[diag] STILL ALIVE after 600s; windows:")
        for w in window_titles():
            dlog("   win: %s" % w)
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                       capture_output=True)
    dlog("[diag] done. status='%s' shots=%d" % (seen_status, shots))

    # teardown user
    uu = find_user(users, USER)
    if uu is not None:
        uu.Удалить()
    cat = agent.Справочники.Пользователи
    for nm in (USER, "Зонд T6-1 diag (удаляется)"):
        ref = cat.НайтиПоНаименованию(nm, True)
        if ref is not None and not ref.Пустая():
            ref.ПолучитьОбъект().Удалить()
    dlog("[diag] user deleted")
    logf.close()


if __name__ == "__main__":
    main()
