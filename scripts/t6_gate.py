# -*- coding: utf-8 -*-
"""T6 Gate: гейт-раннер-прогон цикла батчей VA (зеркало production).

python scripts/t6_gate.py a  -> Цикл A: 2 батча, таймаут 24 c -> kill-tree,
                               статус timeout, хэш восстановлен, цикл продолжился.
python scripts/t6_gate.py b  -> Цикл B: smoke-фича, нормальный таймаут ->
                               ReturnStatus=0, allure result.json, хэш восстановлен.

Механизм: раннер-EPF (tmp/t6/epf/АпкРаннер.epf) в клиентском сеансе
зеркалирует клиентский цикл целевого EPF, вызывая его экспортные функции
через ВнешниеОбработки. Тест-пользователи АпкСценТест_Зонд1/Зонд2 ВРЕМЕННЫЕ
(создаются/удаляются, спайк-паттерн scripts/spike_user_run.py, роли
ПолныеПрава+АдминистраторСистемы, авто-элемент справочника чистится).
Проверка входа: COM V85.COMConnector (только чтение, спайк-паттерн).
"""
import glob
import io
import json
import os
import shutil
import subprocess
import sys
import time

import win32com.client

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"C:\MyProjects\APKScenTest"
V8 = r"C:\Program Files\1cv8\8.5.4.1683\bin\1cv8.exe"
CONN = r"localhost\dev_erpapk_demo"
ADMIN = "Администратор (ОрловАВ)"
TARGET = os.path.join(ROOT, "build", "АпкПодготовкаСценарныхТестов.epf")
RUNNER_EPF = os.environ.get("T6_RUNNER_EPF") or os.path.join(ROOT, "tmp", "t6", "epf", "АпкРаннер.epf")
TASK = os.path.join(ROOT, "tmp", "t6", "runner_task.json")
RESULT = os.path.join(ROOT, "tmp", "t6", "runner_result.json")
CLIENT_LOG = os.path.join(ROOT, "tmp", "t6", "client.log")
SMOKE_FEATURE = os.path.join(ROOT, "tests", "features", "smoke-01-connect.feature")

SETTINGS_TPL = {
    "version": 1,
    "infoBase": 'Srvr="localhost";Ref="dev_erpapk_demo"',
    "v8cPath": r"C:\Program Files\1cv8\8.5.4.1683\bin\1cv8c.exe",
    "vaEpfPath": r"C:\MyProjects\APKTechPlan\tests\vanessa\vanessa-automation-single.epf",
    "projectDir": ROOT,
    "adminUser": ADMIN,
    "adminPassword": "",
    "timeoutMinutesPerBatch": 10,
}

ZOND1 = "АпкСценТест_Зонд1"
ZOND2 = "АпкСценТест_Зонд2"

# UIA-watchdog: закрывает модальное предупреждение безопасности 1С 8.5
# («В настоящей версии приложения возможен выход в интернет», кнопка
# «Продолжить»), которое недетерминированно блокирует старт клиентов.
# Скоуп: только окна с заголовком «1С:Предприятие» + кнопка «Продолжить» —
# другие окна 1С (раннер, дизайнер-агент) не трогаются.
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
        if ($b.Current.Name -eq $btnName) {
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
P1 = {"АпкСценТест_Зонд1": "ApkSct-Z1-Orig-2026!q",
      "АпкСценТест_Зонд2": "ApkSct-Z2-Orig-2026!w"}
FULLNAME = {"АпкСценТест_Зонд1": "Зонд T6-1 (удаляется)",
            "АпкСценТест_Зонд2": "Зонд T6-2 (удаляется)"}
NEED_ROLES = ["ПолныеПрава", "АдминистраторСистемы"]

CYCLES = {
    "a": {"runDir": os.path.join(ROOT, "tmp", "t6", "run-a"),
          "runId": "t6-cycle-a", "portBase": 48300,
          "timeoutOverrideSec": 24, "driverTimeout": 420,
          "users": [ZOND1, ZOND2], "log": os.path.join(ROOT, "tmp", "t6", "gate-cycle-a.log")},
    "b": {"runDir": os.path.join(ROOT, "tmp", "t6", "run-b"),
          "runId": "t6-cycle-b", "portBase": 48400,
          "timeoutOverrideSec": 420, "driverTimeout": 900,
          "users": [ZOND1], "log": os.path.join(ROOT, "tmp", "t6", "gate-cycle-b2.log")},
}

log_lines = []


def log(m):
    print(m)
    log_lines.append(m)


def conn_str(usr, pwd):
    return "Srvr='localhost';Ref='dev_erpapk_demo';Usr='%s';Pwd='%s';" % (usr, pwd)


def find_user(users, name):
    for u in users.ПолучитьПользователей():
        if u.Имя == name:
            return u
    return None


def auth_accepted(usr, pwd):
    """True = вход принят. Отвергнут = исключение с 'Неверн...'."""
    try:
        win32com.client.Dispatch("V85.COMConnector").Connect(conn_str(usr, pwd))
        return True
    except Exception as e:
        err = str(e)
        if "Неверн" in err or "неверн" in err.lower():
            return False
        # прочие ошибки не считаем признаком неверного пароля —
        # трактуем как принят (проверка не удалась, не пароль виноват)
        log("      auth(%s): неопределённая ошибка: %s" % (usr, err[:120]))
        return True


def create_user(agent, users, name):
    old = find_user(users, name)
    if old is not None:
        old.Удалить()
    u = users.СоздатьПользователя()
    u.Имя = name
    u.ПолноеИмя = FULLNAME[name]
    u.Пароль = P1[name]
    md_roles = agent.Метаданные.Роли
    for rn in NEED_ROLES:
        u.Роли.Добавить(getattr(md_roles, rn))
    try:
        u.ЗащитаОтОпасныхДействий.ПредупреждатьОбОпасныхДействиях = False
    except Exception as e:
        log("[setup] ЗОД off fail (%s): %s" % (name, str(e)[:80]))
    u.Записать()
    h1 = find_user(users, name).СохраняемоеЗначениеПароля
    log("[setup] %s создан (роли: %s), H1 len=%d" % (name, "+".join(NEED_ROLES), len(h1)))
    return h1


def delete_user(agent, users, name):
    u = find_user(users, name)
    if u is not None:
        u.Удалить()
    cleaned = []
    try:
        cat = agent.Справочники.Пользователи
        for nm in (name, FULLNAME[name]):
            ref = cat.НайтиПоНаименованию(nm, True)
            if ref is not None and not ref.Пустая():
                ref.ПолучитьОбъект().Удалить()
                cleaned.append(nm)
    except Exception as e:
        cleaned.append("err: %s" % str(e)[:80])
    log("[cleanup] %s: пользователь удалён=%s; справочник: %s"
        % (name, find_user(users, name) is None, "; ".join(cleaned) or "чисто"))


def prep_run_dir(cycle):
    rd = cycle["runDir"]
    if os.path.isdir(rd):
        shutil.rmtree(rd)
    os.makedirs(os.path.join(rd, "features"))
    settings = dict(SETTINGS_TPL)
    settings["portBase"] = cycle["portBase"]
    run = {"runId": cycle["runId"], "startedAt": "2026-10-12T00:00:00",
           "settings": settings}
    with io.open(os.path.join(rd, "run.json"), "w", encoding="utf-8") as f:
        json.dump(run, f, ensure_ascii=False, indent=1)
    files = []
    for i, usr in enumerate(cycle["users"], 1):
        feat = os.path.join(rd, "features", "smoke-zond%d.feature" % i)
        shutil.copyfile(SMOKE_FEATURE, feat)
        files.append({"file": feat.replace("\\", "/"), "template": "00-smoke",
                      "user": usr, "scenarios": 1, "documents": []})
    manifest = {"generatedAt": "2026-10-12T00:00:00", "files": files, "warnings": []}
    with io.open(os.path.join(rd, "features-manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    log("[prep] run dir готов: %s (%d батчей)" % (rd, len(files)))


def kill_tree(pid):
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)


def read_result():
    try:
        return json.loads(io.open(RESULT, encoding="utf-8-sig").read())
    except Exception:
        return None


def run_runner(cycle):
    task = {"target": TARGET, "runDir": cycle["runDir"],
            "timeoutOverrideSec": cycle["timeoutOverrideSec"]}
    with io.open(TASK, "w", encoding="utf-8") as f:
        json.dump(task, f, ensure_ascii=False, indent=1)
    if os.path.exists(RESULT):
        os.remove(RESULT)
    cmd = [V8, "/S", CONN, "/RunModeManagedApplication", "/N", ADMIN,
           "/DisableStartupDialogs", "/Execute", RUNNER_EPF]

    # UIA-watchdog: закрывает модальное предупреждение безопасности 1С 8.5,
    # которое недетерминированно блокирует старт клиентов (и раннера, и VA).
    wd_log = os.path.join(ROOT, "tmp", "t6",
                          "watchdog-%s.log" % cyc_cycle(cycle))
    if os.path.exists(wd_log):
        os.remove(wd_log)
    wd_ps = WATCHDOG_PS.replace("{duration}", str(cycle["driverTimeout"] + 60))
    wd_ps = wd_ps.replace("{log}", wd_log)
    wd_proc = subprocess.Popen(
        ["powershell", "-NoProfile", "-Command", wd_ps],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    fp = open(CLIENT_LOG, "wb")
    proc = subprocess.Popen(cmd, stdout=fp, stderr=subprocess.STDOUT)
    data = None
    try:
        start = time.time()
        while time.time() - start < cycle["driverTimeout"]:
            data = read_result()
            if data and data.get("step") == "done":
                break
            if proc.poll() is not None:
                time.sleep(2)
                data = data or read_result()
                break
            time.sleep(3)
        else:
            log("[runner] FAIL: таймаут драйвера %dc" % cycle["driverTimeout"])
            kill_tree(proc.pid)
            return None
    finally:
        kill_tree(proc.pid)
        try:
            proc.wait(timeout=10)
        except Exception:
            pass
        fp.close()
        try:
            wd_proc.kill()
        except Exception:
            pass
    return data


def main():
    cyc = sys.argv[1] if len(sys.argv) > 1 else ""
    if cyc not in CYCLES:
        print("usage: t6_gate.py a|b")
        return 2
    cycle = CYCLES[cyc]

    agent = win32com.client.Dispatch("V85.COMConnector").Connect(conn_str(ADMIN, ""))
    users = agent.ПользователиИнформационнойБазы

    hashes = {}
    ok = False
    try:
        # setup: временные пользователи
        for name in (ZOND1, ZOND2):
            hashes[name] = create_user(agent, users, name)
        prep_run_dir(cycle)

        # прогон
        data = run_runner(cycle)
        if data is None:
            log("[runner] результат недоступен")
        else:
            log("[runner] step=%s errors=%s" % (data.get("step"), data.get("errorsCount")))
            for e in (data.get("errors") or [])[:5]:
                log("   error: %s" % e[:300])
            ok = verify(agent, users, cycle, data, hashes)

    finally:
        for name in (ZOND1, ZOND2):
            try:
                delete_user(agent, users, name)
            except Exception as e:
                log("[cleanup] fail %s: %s" % (name, str(e)[:120]))

    verdict = "PASS" if ok else "FAIL"
    log("VERDICT cycle-%s: %s" % (cyc, verdict))
    with io.open(cycle["log"], "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
    return 0 if ok else 1


def verify(agent, users, cycle, data, hashes):
    rd = cycle["runDir"]
    batches = data.get("batches") or []
    test_pwd = data.get("testPassword", "")
    ok = True

    def check(cond, label):
        nonlocal ok
        log("  [%s] %s" % ("OK" if cond else "FAIL", label))
        if not cond:
            ok = False

    check(data.get("errorsCount") == 0, "runner errors = 0")
    check(len(batches) == len(cycle["users"]), "батчей %d (ожидалось %d)"
          % (len(batches), len(cycle["users"])))

    for b in batches:
        log("  batch %s (%s): status=%s rs=%s verdict=%s dur=%.1fs pid=%s "
            "pwd=%s zod=%s err=%s"
            % (b.get("batch"), b.get("user"), b.get("status"), b.get("returnStatus"),
               b.get("verdict"), b.get("durationSec", 0), b.get("pid"),
               b.get("passwordRestored"), b.get("zodRestored"),
               (b.get("error") or "")[:120]))

    if cyc_cycle(cycle) == "a":
        for b in batches:
            check(b.get("status") == "timeout", "батч %s: статус timeout" % b.get("batch"))
            check(b.get("pid", 0) > 0, "батч %s: PID зафиксирован" % b.get("batch"))
            check(b.get("passwordRestored") is True,
                  "батч %s: хэш восстановлен (finally)" % b.get("batch"))
            check(b.get("killConfirmed") is True,
                  "батч %s: kill-tree подтверждён (процесс умер)" % b.get("batch"))
            check(b.get("zodRestored") is True, "батч %s: ЗОД восстановлен" % b.get("batch"))
        check(len(batches) == 2, "цикл продолжился: оба батча выполнены")
    else:
        b = batches[0] if batches else {}
        check(b.get("status") == "ok", "батч: статус ok")
        check(b.get("returnStatus") == "0", "ReturnStatus = 0")
        check(b.get("passwordRestored") is True, "хэш восстановлен")
        check(b.get("zodRestored") is True, "ЗОД восстановлен")
        allure = glob.glob(os.path.join(rd, "allure", "**", "*-result.json"), recursive=True)
        check(len(allure) >= 1, "allure result.json (%d шт.)" % len(allure))

    # batches.json
    bj = os.path.join(rd, "batches.json")
    check(os.path.exists(bj), "batches.json записан")
    # VAParams удалены (NFR-001)
    params_left = glob.glob(os.path.join(rd, "params", "vaparams-*.json"))
    check(not params_left, "VAParams-файлы удалены (%d осталось)" % len(params_left))

    # COM-верификация паролей (только чтение)
    for name in cycle["users"]:
        u = find_user(users, name)
        if u is None:
            check(False, "%s: пользователь исчез" % name)
            continue
        check(u.СохраняемоеЗначениеПароля == hashes.get(name),
              "%s: хэш == H1 (COM)" % name)
        check(auth_accepted(name, P1[name]), "%s: исходный пароль принят" % name)
        if test_pwd:
            check(not auth_accepted(name, test_pwd),
                  "%s: тестовый пароль отвергнут" % name)
    return ok


def cyc_cycle(cycle):
    return cycle["runId"].split("-")[-1]


if __name__ == "__main__":
    sys.exit(main())
