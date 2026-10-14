# -*- coding: utf-8 -*-
"""T6 diag: ручное воспроизведение батча cycle B с наблюдением.

Создаёт Зонд1 (COM), ставит ему тестовый пароль из сохранённого VAParams,
запускает 1cv8c TestManager РОВНО как раннер (cmd /c "..."), наблюдает
процессы/логи 240 c, убивает дерево, удаляет пользователя.
"""
import glob
import io
import json
import os
import re
import subprocess
import sys
import time

import win32com.client

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"C:\MyProjects\APKScenTest"
V8C = r"C:\Program Files\1cv8\8.5.4.1683\bin\1cv8c.exe"
CONN = r"localhost\dev_erpapk_demo"
ADMIN = "Администратор (ОрловАВ)"
VAP = os.path.join(ROOT, "tmp", "t6", "run-b", "params", "vaparams-1.json")
ZOND1 = "АпкСценТест_Зонд1"
P1 = "ApkSct-Z1-Orig-2026!q"
OUT1C = os.path.join(ROOT, "tmp", "t6", "run-b", "logs", "1c-1-ApkScenTest-Zond1.log")
VALOG = os.path.join(ROOT, "tmp", "t6", "run-b", "logs", "va-1-ApkScenTest-Zond1.log")
STATUS = os.path.join(ROOT, "tmp", "t6", "run-b", "params", "status-1.txt")
DIAG_LOG = os.path.join(ROOT, "tmp", "t6", "diag_cmd.log")
WAIT = int(os.environ.get("T6_DIAG_WAIT", "240"))


def conn_str(usr, pwd):
    return "Srvr='localhost';Ref='dev_erpapk_demo';Usr='%s';Pwd='%s';" % (usr, pwd)


def find_user(users, name):
    for u in users.ПолучитьПользователей():
        if u.Имя == name:
            return u
    return None


def main():
    vap = json.loads(io.open(VAP, encoding="utf-8-sig").read())
    test_pwd = vap["КлиентыТестирования"][0]["ПутьКИнфобазе"]
    test_pwd = re.search(r'/P "(.*)"', test_pwd).group(1)
    print("test pwd from VAParams:", test_pwd)

    agent = win32com.client.Dispatch("V85.COMConnector").Connect(conn_str(ADMIN, ""))
    users = agent.ПользователиИнформационнойБазы
    try:
        old = find_user(users, ZOND1)
        if old is not None:
            old.Удалить()
        u = users.СоздатьПользователя()
        u.Имя = ZOND1
        u.ПолноеИмя = "Зонд T6-1 (удаляется)"
        u.Пароль = P1
        md = agent.Метаданные.Роли
        for rn in ("ПолныеПрава", "АдминистраторСистемы"):
            u.Роли.Добавить(getattr(md, rn))
        u.ЗащитаОтОпасныхДействий.ПредупреждатьОбОпасныхДействиях = False
        u.Записать()
        u1 = find_user(users, ZOND1)
        u1.Пароль = test_pwd
        u1.Записать()
        print("Зонд1 создан, тестовый пароль установлен")

        for p in (OUT1C, VALOG, STATUS):
            if os.path.exists(p):
                os.remove(p)

        cmd_inner = ('"%s" ENTERPRISE /TESTMANAGER /S "%s" /N "%s" /P "" '
                     '/Out "%s" /Execute "%s" /C "StartFeaturePlayer;VAParams=%s"'
                     % (V8C, CONN, ADMIN, OUT1C.replace("/", "\\"),
                        r"C:\MyProjects\APKTechPlan\tests\vanessa\vanessa-automation-single.epf",
                        VAP.replace("/", "\\")))
        full = 'cmd /c "' + cmd_inner + '"'
        print("CMD:", full)
        fp = open(DIAG_LOG, "wb")
        proc = subprocess.Popen(full, stdout=fp, stderr=subprocess.STDOUT)
        print("pid:", proc.pid)
        t0 = time.time()
        try:
            while time.time() - t0 < WAIT:
                time.sleep(10)
                el = time.time() - t0
                procs = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq 1cv8c.exe"],
                    capture_output=True).stdout.decode("cp866", errors="replace")
                n1cv8c = procs.count("1cv8c.exe")
                sizes = {os.path.basename(p): os.path.getsize(p)
                         for p in (OUT1C, VALOG, STATUS) if os.path.exists(p)}
                print("[%3.0fs] 1cv8c=%d files=%s" % (el, n1cv8c, sizes))
                if os.path.exists(STATUS):
                    print("STATUS:", io.open(STATUS, encoding="utf-8-sig",
                                             errors="replace").read())
                    break
        finally:
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                           capture_output=True)
            time.sleep(2)
            fp.close()
        tail = ""
        if os.path.exists(DIAG_LOG):
            tail = io.open(DIAG_LOG, "rb").read().decode("cp866", errors="replace")[-1500:]
        print("--- diag_cmd.log tail ---")
        print(tail)
    finally:
        u = find_user(users, ZOND1)
        if u is not None:
            u.Удалить()
        try:
            cat = agent.Справочники.Пользователи
            for nm in (ZOND1, "Зонд T6-1 (удаляется)"):
                ref = cat.НайтиПоНаименованию(nm, True)
                if ref is not None and not ref.Пустая():
                    ref.ПолучитьОбъект().Удалить()
        except Exception:
            pass
        print("cleanup done")


if __name__ == "__main__":
    main()
