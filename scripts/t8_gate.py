# -*- coding: utf-8 -*-
"""T8 Gate: E2E полного конвейера (dev_erpapk_demo).

Цепочка (свежий run-каталог, runId по контракту):
1. Stage-A раннер (tmp/t8/epf) - НачатьПрогон -> Сканировать ->
   СформироватьФикстуры -> СгенерироватьФичи;
2. Ограничение E2E (безопасность): манифест переписывается на временных
   пользователей АпкСценТест_Зонд1/2 (smoke + 01-pl-tractor), реальные
   авторы плана - pending user confirmation;
3. Батчи через T6-раннер (tmp/t6/epf): порты per-batch (48501/48502),
   зачистка сирот, finally-восстановление, ReturnStatus - единственный вердикт;
4. Отчёт через T7-раннер (tmp/t7/epf): СобратьОтчет -> summary.json/md.

Проверки: ReturnStatus=0, артефакты run-каталога полные, пароли
(исходный принят / тестовый отвергнут, COM только чтение), summary.md
с "passed". Логи: tmp/t8/t8-gate.log, чеклист: tmp/t8/e2e-checklist.md.
"""
import glob
import io
import datetime
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
SETTINGS = os.path.join(ROOT, "tmp", "t8", "preprocessor-settings.json")
RUNS_DIR = os.path.join(ROOT, "tests")

STAGE_A_EPF = os.path.join(ROOT, "tmp", "t8", "epf", "АпкРаннер.epf")
STAGE_A_TASK = os.path.join(ROOT, "tmp", "t8", "runner_task.json")
STAGE_A_RESULT = os.path.join(ROOT, "tmp", "t8", "runner_result.json")
STAGE_A_LOG = os.path.join(ROOT, "tmp", "t8", "client-a.log")
T6_EPF = os.path.join(ROOT, "tmp", "t6", "epf", "АпкРаннер.epf")
T6_TASK = os.path.join(ROOT, "tmp", "t6", "runner_task.json")
T6_RESULT = os.path.join(ROOT, "tmp", "t6", "runner_result.json")
T7_EPF = os.path.join(ROOT, "tmp", "t7", "epf", "АпкРаннер.epf")
T7_TASK = os.path.join(ROOT, "tmp", "t7", "runner_task.json")
T7_RESULT = os.path.join(ROOT, "tmp", "t7", "runner_result.json")

GATE_LOG = os.path.join(ROOT, "tmp", "t8", "t8-gate.log")
CHECKLIST = os.path.join(ROOT, "tmp", "t8", "e2e-checklist.md")

TIMEOUT_STAGE_A = 900
TIMEOUT_BATCHES = 1800
TIMEOUT_REPORT = 600

ZOND1 = "АпкСценТест_Зонд1"
ZOND2 = "АпкСценТест_Зонд2"
P1 = {ZOND1: "ApkSct-Z1-Orig-2026!q",
      ZOND2: "ApkSct-Z2-Orig-2026!w"}
FULLNAME = {ZOND1: "Зонд T8-1 (удаляется)",
            ZOND2: "Зонд T8-2 (удаляется)"}
NEED_ROLES = ["ПолныеПрава", "АдминистраторСистемы"]

# s004 (FR-004): негативный пользователь и его детерминированный состав
# (зонд-факт tmp/s004/facts-neg-composition.md: права аддитивны, Апк-прав
# нет ни у одной роли; АдминистраторСистемы обязателен для /Execute).
NEG_USER = "АпкСценТест_Негатив1"
NEG_PWD = "ApkSct-Neg1-2026!n"
NEG_FULLNAME = "Негатив s004 (удаляется)"
NEG_ROLES = ["АдминистраторСистемы", "БазовыеПраваБСП", "ЗапускТонкогоКлиента",
             "ИнтерактивноеОткрытиеВнешнихОтчетовИОбработок",
             "VAExtension_ОбщиеПрава"]
NEG_TEMPLATE = "neg-pl-denied"
NEG_TEMPLATE_FILE = os.path.join(ROOT, "tests", "templates", "neg-pl-denied.feature")
SMOKE_TEMPLATE_FILE = os.path.join(ROOT, "tests", "templates", "00-smoke.feature")

# s004: режим реальных авторов — флаг CLI; guard-файлы парольной опасности
REAL_MODE = "--real-authors" in sys.argv
GUARD_DIR = os.path.join(ROOT, "tests", "pwd-guard")
RAC = r"C:\Program Files\1cv8\8.5.4.1683\bin\rac.exe"
RAC_CLUSTER = "67cdef87-7bfc-4dae-b8e4-3ea9f8529156"
RAC_INFOBASE = "c6a442bb-d7a9-4d8b-a274-37ea859b26c1"  # dev_erpapk_demo

log_lines = []


def log(m):
    print(m, flush=True)
    log_lines.append(m)


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


def conn_str(usr, pwd):
    return "Srvr='localhost';Ref='dev_erpapk_demo';Usr='%s';Pwd='%s';" % (usr, pwd)


def auth_accepted(usr, pwd):
    """True = вход принят; False = отвергнут (Неверн...)."""
    try:
        win32com.client.Dispatch("V85.COMConnector").Connect(conn_str(usr, pwd))
        return True
    except Exception as e:
        err = str(e)
        if "Неверн" in err or "неверн" in err.lower():
            return False
        log("      auth(%s): неопределённая ошибка: %s" % (usr, err[:120]))
        return True


def find_user(users, name):
    for u in users.ПолучитьПользователей():
        if u.Имя == name:
            return u
    return None


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


def delete_user(users, name):
    u = find_user(users, name)
    if u is not None:
        u.Удалить()
    log("[cleanup] %s: пользователь удалён=%s" % (name, find_user(users, name) is None))


def cleanup_today_counters(agent):
    """T9: удаляет записи АпкСчетчикТранспортныхСредств за сегодня.

    Фича 01-pl-tractor при каждом прогоне создаёт НОВЫЙ путевой лист
    датой «сегодня»; запись счётчика от утреннего прогона
    (напр., run-T6/T7-эры) даёт коллизию при повторном проведении
    («Запись с такими ключевыми полями существует»). Регистр
    подчинён регистратору - удаляем набором записей по Регистратору
    (записи 17.10.2026 - probe-residue; реальные данные 2015-2023
    не затрагиваются).
    """
    q = agent.NewObject("Query")
    q.Text = ("ВЫБРАТЬ АпкСчетчикТранспортныхСредств.Регистратор КАК Регистратор "
              "ИЗ РегистрСведений.АпкСчетчикТранспортныхСредств "
              "КАК АпкСчетчикТранспортныхСредств "
              "ГДЕ АпкСчетчикТранспортныхСредств.Период МЕЖДУ &Д1 И &Д2")
    today = datetime.date.today()
    d1 = datetime.datetime(today.year, today.month, today.day)
    d2 = d1 + datetime.timedelta(hours=23, minutes=59, seconds=59)
    q.УстановитьПараметр("Д1", d1)
    q.УстановитьПараметр("Д2", d2)
    sel = q.Execute().Choose()
    recorders = []
    while sel.Next():
        r = sel.Регистратор
        if r not in recorders:
            recorders.append(r)
    rs = agent.РегистрыСведений.АпкСчетчикТранспортныхСредств
    for rec in recorders:
        nabor = rs.СоздатьНаборЗаписей()
        el = nabor.Отбор.Get(0)  # ПутьКДанным = Регистратор
        el.Значение = rec
        el.Использование = True
        nabor.Записать(True)
    log("[setup] счётчики ТС за сегодня очищены: %d регистраторов" % len(recorders))
    return len(recorders)


def kill_tree(pid):
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)


# --- s004: режим реальных авторов -------------------------------------

def rac_sessions_online():
    """Онлайн-сеансы на dev_erpapk_demo (FR-003, exit 2 у вызывающего).

    Возвращает (список_строк_описаний, код_ошибки|None).
    """
    try:
        out = subprocess.run([RAC, "session", "list", "--cluster=" + RAC_CLUSTER],
                             capture_output=True, timeout=60)
    except Exception as e:
        return None, "rac недоступен: %s" % str(e)[:150]
    txt = out.stdout.decode("cp866", errors="replace")
    sessions = []
    for block in txt.split("\n\n"):
        fields = {}
        for line in block.splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                fields[k.strip()] = v.strip()
        if fields.get("infobase") == RAC_INFOBASE:
            sessions.append("%s (%s)" % (fields.get("user-name"),
                                         fields.get("app-id")))
    return sessions, None


def guard_write(run_id, payload):
    """Guard-файл активного опасного окна (FR-006, 3-уровневая защита)."""
    os.makedirs(GUARD_DIR, exist_ok=True)
    path = os.path.join(GUARD_DIR, "%s.active.json" % run_id)
    with io.open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    return path


def guard_active_files():
    if not os.path.isdir(GUARD_DIR):
        return []
    return sorted(f for f in os.listdir(GUARD_DIR) if f.endswith(".active.json"))


def guard_clear(run_id):
    path = os.path.join(GUARD_DIR, "%s.active.json" % run_id)
    if os.path.exists(path):
        os.remove(path)


def create_neg_user(agent, users):
    """Негативный пользователь: 5 СУЩЕСТВУЮЩИХ ролей (TD-002), без Апк-прав."""
    md_roles = agent.Метаданные.Роли
    for rn in NEG_ROLES:
        if getattr(md_roles, rn, None) is None:
            raise RuntimeError("роль neg-состава не найдена в базе: %s" % rn)
    old = find_user(users, NEG_USER)
    if old is not None:
        old.Удалить()
    u = users.СоздатьПользователя()
    u.Имя = NEG_USER
    u.ПолноеИмя = NEG_FULLNAME
    u.Пароль = NEG_PWD
    for rn in NEG_ROLES:
        u.Роли.Добавить(getattr(md_roles, rn))
    try:
        u.ЗащитаОтОпасныхДействий.ПредупреждатьОбОпасныхДействиях = False
    except Exception as e:
        log("[setup] ЗОД off fail (%s): %s" % (NEG_USER, str(e)[:80]))
    u.Записать()
    h1 = find_user(users, NEG_USER).СохраняемоеЗначениеПароля
    log("[setup] %s создан (роли: %s), H1 len=%d"
        % (NEG_USER, "+".join(NEG_ROLES), len(h1)))
    return h1


def prepare_real_manifest(run_dir, checks):
    """Real-режим: манифест НЕ ограничивается (реальные авторы),
    smoke маршрутизируется первому автору (D-003), добавляется
    neg-батч (FR-004). Возвращает (авторы, ошибка)."""
    manifest_path = os.path.join(run_dir, "features-manifest.json")
    manifest = read_json(manifest_path)
    if not manifest:
        return None, "features-manifest.json не читается"
    shutil.copyfile(manifest_path,
                    os.path.join(run_dir, "features-manifest.generated.json"))
    files = manifest.get("files") or []
    if not files:
        return None, "сгенерированный манифест пуст"
    fdir = os.path.join(run_dir, "features")

    # D-003: smoke как первый батч под первым автором
    first_author = files[0].get("user", "")
    if not first_author:
        return None, "первая запись манифеста без пользователя"
    has_smoke = any(e.get("template") == "00-smoke" for e in files)
    if not has_smoke:
        smoke_dst = os.path.join(fdir, "00-smoke--real.feature")
        shutil.copyfile(SMOKE_TEMPLATE_FILE, smoke_dst)
        files.insert(0, {"file": smoke_dst.replace("\\", "/"),
                         "template": "00-smoke", "user": first_author,
                         "scenarios": 1, "documents": []})
        log("[real] smoke добавлен под первого автора: %s" % first_author)

    # FR-004: neg-батч последним (временный пользователь, метка negative)
    neg_dst = os.path.join(fdir, "neg-pl-denied--ApkSctNeg1.feature")
    shutil.copyfile(NEG_TEMPLATE_FILE, neg_dst)
    files.append({"file": neg_dst.replace("\\", "/"),
                  "template": NEG_TEMPLATE, "user": NEG_USER,
                  "scenarios": 1, "documents": [], "negative": True})

    manifest["files"] = files
    manifest["realAuthors"] = True
    with io.open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)

    authors = sorted(set(e.get("user", "") for e in files
                         if e.get("user") and e.get("user") != NEG_USER))
    checks["realAuthors"] = authors
    checks["restricted"] = False
    log("[real] манифест: реальные авторы (%d) + neg-батч (%s)"
        % (len(authors), NEG_USER))
    return authors, None


def real_snapshot(agent, users, authors):
    """Уровень-1 защиты: снимок исходного состояния паролей авторов
    ДО Stage B (COM, чтение)."""
    snap = {}
    for name in authors:
        u = find_user(users, name)
        if u is None:
            raise RuntimeError("автор плана не найден в ИБ: %s" % name)
        snap[name] = {"pwdSet": bool(u.ПарольУстановлен),
                      "hash": str(u.СохраняемоеЗначениеПароля)}
    return snap


def read_json(path):
    try:
        return json.loads(io.open(path, encoding="utf-8-sig").read())
    except Exception:
        return None


def run_1c_session(runner_epf, timeout, client_log, result_file=None):
    """Старт 1cv8 /Execute runner-EPF с UIA-watchdog и ожиданием завершения.

    Если задан result_file - драйвер выходит по step=done (паттерн T6/T7:
    клиентский сеанс после Финал(Закрыть) может не завершаться сам).
    """
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
            log("[runner] FAIL: таймаут драйвера %dc (%s)" % (timeout, runner_epf))
            return False
    finally:
        kill_tree(proc.pid)
        try:
            proc.wait(timeout=10)
        except Exception:
            pass
        fp.close()
    return True


def start_watchdog(duration, log_name):
    wd_log = os.path.join(ROOT, "tmp", "t8", log_name)
    if os.path.exists(wd_log):
        os.remove(wd_log)
    wd_ps = WATCHDOG_PS.replace("{duration}", str(duration)).replace("{log}", wd_log)
    return subprocess.Popen(["powershell", "-NoProfile", "-Command", wd_ps],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def restrict_manifest(run_dir, checks):
    """Переписывает features-manifest.json на временных пользователей.

    Сохраняет сгенерированный манифест в features-manifest.generated.json.
    Возвращает (описание ограничений, None/строка ошибки).
    """
    manifest_path = os.path.join(run_dir, "features-manifest.json")
    manifest = read_json(manifest_path)
    if not manifest:
        return None, "features-manifest.json не читается"
    gen_path = os.path.join(run_dir, "features-manifest.generated.json")
    shutil.copyfile(manifest_path, gen_path)

    files = manifest.get("files") or []
    smoke_src = None
    tractor_src = None
    arm_entries = []
    for entry in files:
        tmpl = entry.get("template", "")
        if tmpl == "00-smoke" and smoke_src is None:
            smoke_src = entry.get("file", "")
        if tmpl == "01-pl-tractor" and tractor_src is None:
            tractor_src = entry.get("file", "")
        if tmpl.startswith("arm-") and os.path.exists(entry.get("file", "")):
            f = entry.get("file", "")
            if f:
                arm_entries.append((tmpl, f))
    if not smoke_src or not os.path.exists(smoke_src):
        return None, "сгенерированный smoke-файл не найден"
    if not tractor_src or not os.path.exists(tractor_src):
        return None, "сгенерированный 01-pl-tractor файл не найден"

    fdir = os.path.join(run_dir, "features")
    smoke_dst = os.path.join(fdir, "00-smoke--ApkSct-Zond1.feature")
    tractor_dst = os.path.join(fdir, "01-pl-tractor--ApkSct-Zond2.feature")
    shutil.copyfile(smoke_src, smoke_dst)
    shutil.copyfile(tractor_src, tractor_dst)

    restricted_files = [
        {"file": smoke_dst.replace("\\", "/"), "template": "00-smoke",
         "user": ZOND1, "scenarios": 1, "documents": []},
        {"file": tractor_dst.replace("\\", "/"), "template": "01-pl-tractor",
         "user": ZOND2, "scenarios": 1, "documents": []},
    ]
    # T9: arm-* шаблоны включаются в прогон зондов round-robin;
    # arm-fuel-expense зависит от закрытого ПЛ тракториста из 01-pl-tractor,
    # поэтому всегда маршрутизируется в батч Зонд2 (после 01-pl-tractor).
    zonds = (ZOND1, ZOND2)
    zond1_n = 0
    for tmpl, src in arm_entries:
        if tmpl == "arm-fuel-expense":
            zond = ZOND2
            zond_idx = 1
        else:
            zond = zonds[zond1_n % 2]
            zond_idx = zond1_n % 2
            zond1_n += 1
        dst = os.path.join(fdir, "%s--ApkSct-Zond%d.feature" % (tmpl, zond_idx + 1))
        shutil.copyfile(src, dst)
        restricted_files.append(
            {"file": dst.replace("\\", "/"), "template": tmpl,
             "user": zond, "scenarios": 1, "documents": []})

    restricted = {
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "files": restricted_files,
        "warnings": [
            "T8/T9 E2E restriction: батчи ограничены временными пользователями "
            "(безопасность); реальные авторы плана - pending user confirmation",
        ],
    }
    with io.open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(restricted, f, ensure_ascii=False, indent=1)

    orig_users = sorted(set(e.get("user", "") for e in files if e.get("user")))
    checks["generatedUsers"] = orig_users
    checks["armTemplates"] = [t for t, _ in arm_entries]
    checks["restricted"] = True
    return orig_users, None


def main():
    checks = {}
    # s004: префлайт режима реальных авторов (до любых изменений базы)
    if REAL_MODE:
        active = guard_active_files()
        if active:
            log("[preflight] FAIL: активные guard-файлы (незавершённый прогон): %s"
                % ", ".join(active))
            log("[preflight] см. docs/runbook.md § восстановление")
            io.open(GATE_LOG, "w", encoding="utf-8").write("\n".join(log_lines))
            sys.exit(2)
        sessions, rac_err = rac_sessions_online()
        if rac_err:
            log("[preflight] FAIL: %s" % rac_err)
            io.open(GATE_LOG, "w", encoding="utf-8").write("\n".join(log_lines))
            sys.exit(2)
        if sessions:
            log("[preflight] FAIL: онлайн-сеансы на базе (%d): %s"
                % (len(sessions), "; ".join(sessions)))
            io.open(GATE_LOG, "w", encoding="utf-8").write("\n".join(log_lines))
            sys.exit(2)
        log("[preflight] OK: guard чист, онлайн-сеансов нет")
        settings_data = read_json(SETTINGS) or {}
        if settings_data.get("alwaysSubstitutePwd") is not True:
            log("[preflight] FAIL: settings без alwaysSubstitutePwd=true "
                "(запускайте через regress_run.py --real-authors)")
            io.open(GATE_LOG, "w", encoding="utf-8").write("\n".join(log_lines))
            sys.exit(2)
        log("[preflight] OK: alwaysSubstitutePwd=true в настройках")
    agent = win32com.client.Dispatch("V85.COMConnector").Connect(conn_str(ADMIN, ""))
    users = agent.ПользователиИнформационнойБазы
    hashes = {}
    snapshot = {}
    ok = False
    try:
        # --- Stage A: конвейер генерации -------------------------------
        log("[stage-a] запуск конвейера генерации (НачатьПрогон->...->Фичи)")
        with io.open(STAGE_A_TASK, "w", encoding="utf-8") as f:
            json.dump({"target": TARGET, "settings": SETTINGS,
                       "runsDir": RUNS_DIR}, f, ensure_ascii=False)
        if os.path.exists(STAGE_A_RESULT):
            os.remove(STAGE_A_RESULT)
        wd = start_watchdog(TIMEOUT_STAGE_A + 60, "watchdog-a.log")
        try:
            if not run_1c_session(STAGE_A_EPF, TIMEOUT_STAGE_A, STAGE_A_LOG,
                                   STAGE_A_RESULT):
                log("[stage-a] FAIL: клиентская сессия не завершилась")
                return finish(False)
        finally:
            wd.kill()
        data_a = read_json(STAGE_A_RESULT)
        if not data_a:
            log("[stage-a] FAIL: результат недоступен")
            return finish(False)
        log("[stage-a] step=%s errors=%s" % (data_a.get("step"), data_a.get("errorsCount")))
        for e in (data_a.get("errors") or [])[:5]:
            log("   error: %s" % e[:300])
        if data_a.get("step") != "done" or data_a.get("errorsCount"):
            return finish(False)
        run_dir = data_a.get("runDir", "")
        run_id = os.path.basename(run_dir).replace("run-", "") if run_dir else ""
        checks["runDir"] = run_dir
        checks["runId"] = run_id
        log("[stage-a] runId=%s runDir=%s" % (run_id, run_dir))
        log("[stage-a] scan=%s" % (data_a.get("scanSummary", "")[:200],))
        log("[stage-a] fixtures=%s" % (data_a.get("fixturesSummary", "")[:200],))
        log("[stage-a] features=%s" % (data_a.get("featuresSummary", "")[:200],))

        # --- Ограничение E2E: временные пользователи --------------------
        if REAL_MODE:
            # s004: реальные авторы (restrict_manifest не выполняется),
            # второй рубеж rac-проверки ПОСЛЕ Stage A (окно могло открыться)
            sessions, rac_err = rac_sessions_online()
            if rac_err or sessions:
                log("[real] FAIL: онлайн-сеансы после Stage A: %s"
                    % (rac_err or "; ".join(sessions)))
                return finish(False)
            authors, err = prepare_real_manifest(run_dir, checks)
            if err:
                log("[real] FAIL: %s" % err)
                return finish(False)
            snapshot = real_snapshot(agent, users, authors)
            for name in authors:
                log("[real] автор %s: pwdSet=%s hashLen=%d"
                    % (name, snapshot[name]["pwdSet"], len(snapshot[name]["hash"])))
            hashes[NEG_USER] = create_neg_user(agent, users)
            guard_write(run_id, {"runId": run_id, "mode": "real-authors",
                                  "authors": authors,
                                  "snapshot": snapshot,
                                  "negUser": NEG_USER,
                                  "startedAt": time.strftime("%Y-%m-%dT%H:%M:%S")})
            log("[real] guard-файл записан: %s.active.json" % run_id)
            cleanup_today_counters(agent)
        else:
            hashes[ZOND1] = create_user(agent, users, ZOND1)
            hashes[ZOND2] = create_user(agent, users, ZOND2)
            orig_users, err = restrict_manifest(run_dir, checks)
            if err:
                log("[restrict] FAIL: %s" % err)
                return finish(False)
            log("[restrict] манифест ограничен: Зонд1=smoke, Зонд2=01-pl-tractor")
            log("[restrict] arm-шаблоны в прогоне зондов: %s"
                % (", ".join(checks.get("armTemplates", [])) or "нет"))
            log("[restrict] реальные авторы (pending user confirmation): %s"
                % "; ".join(orig_users))
            cleanup_today_counters(agent)

        # --- Stage B: батчи T6-раннером --------------------------------
        # Ретрай: сбой подключения TestClient (rs=2) недетерминирован
        # (T6: холодный старт / модальное окно); до 2 запусков стадии.
        log("[stage-b] батчи (T6-механизм: порты, сироты, finally)")
        with io.open(T6_TASK, "w", encoding="utf-8") as f:
            json.dump({"target": TARGET, "runDir": run_dir,
                       "timeoutOverrideSec": 0}, f, ensure_ascii=False)
        if os.path.exists(T6_RESULT):
            os.remove(T6_RESULT)
        wd = start_watchdog(TIMEOUT_BATCHES * 2 + 120, "watchdog-b.log")
        data_b = None
        try:
            for attempt in (1, 2):
                if os.path.exists(T6_RESULT):
                    os.remove(T6_RESULT)
                log("[stage-b] попытка %d" % attempt)
                if not run_1c_session(T6_EPF, TIMEOUT_BATCHES,
                                      os.path.join(ROOT, "tmp", "t6", "client.log"),
                                      T6_RESULT):
                    log("[stage-b] FAIL: клиентская сессия не завершилась")
                    return finish(False)
                data_b = read_json(T6_RESULT)
                if data_b is None:
                    log("[stage-b] FAIL: результат T6-раннера недоступен (runner crashed/timed out)")
                    return finish(False)
                if not data_b:  # empty dict / no step
                    log("[stage-b] FAIL: результат T6-раннера пустой")
                    return finish(False)
                log("[stage-b] step=%s errors=%s" % (data_b.get("step"), data_b.get("errorsCount")))
                for b in (data_b.get("batches") or []):
                    log("[stage-b] batch %s (%s): status=%s rs=%s verdict=%s dur=%.1fs "
                        "pwd=%s zod=%s err=%s"
                        % (b.get("batch"), b.get("user"), b.get("status"),
                           b.get("returnStatus"), b.get("verdict"),
                           b.get("durationSec", 0), b.get("passwordRestored"),
                           b.get("zodRestored"), (b.get("error") or "")[:120]))
                if all(b.get("returnStatus") == "0"
                        for b in (data_b.get("batches") or [])) \
                        and (data_b.get("batches") or []):
                    break
                if any(b.get("returnStatus") == "2"
                        for b in (data_b.get("batches") or [])):
                    log("[stage-b] сбой подключения (rs=2) - повтор попытки")
                    continue
                break
        finally:
            wd.kill()

        # --- Stage C: отчёт T7-раннером --------------------------------
        log("[stage-c] СобратьОтчет (T7-раннер)")
        with io.open(T7_TASK, "w", encoding="utf-8") as f:
            json.dump({"target": TARGET, "runDir": run_dir}, f, ensure_ascii=False)
        if os.path.exists(T7_RESULT):
            os.remove(T7_RESULT)
        wd = start_watchdog(TIMEOUT_REPORT + 60, "watchdog-c.log")
        try:
            if not run_1c_session(T7_EPF, TIMEOUT_REPORT,
                                  os.path.join(ROOT, "tmp", "t7", "client.log"),
                                  T7_RESULT):
                log("[stage-c] FAIL: клиентская сессия не завершилась")
                return finish(False)
        finally:
            wd.kill()
        data_c = read_json(T7_RESULT)
        if not data_c:
            log("[stage-c] FAIL: результат T7-раннера недоступен")
            return finish(False)
        log("[stage-c] step=%s errors=%s" % (data_c.get("step"), data_c.get("errorsCount")))
        log("[stage-c] summaryJson=%s" % data_c.get("summaryJson"))
        log("[stage-c] totals=%s" % json.dumps(data_c.get("totals"), ensure_ascii=False))
        checks["report"] = data_c

        # COM-соединение жило ~30 минут (stage-a/b/c) и может упасть -
        # для verify/cleanup берём свежее
        try:
            agent = win32com.client.Dispatch("V85.COMConnector").Connect(conn_str(ADMIN, ""))
            users = agent.ПользователиИнформационнойБазы
        except Exception as e:
            log("[verify] FAIL: переподключение COM: %s" % str(e)[:150])
            return finish(False)

        # --- Верификация -----------------------------------------------
        try:
            if REAL_MODE:
                ok = verify_real(agent, users, checks, data_b, hashes, snapshot)
            else:
                ok = verify(agent, users, checks, data_b, hashes)
        except Exception as e:
            log("[verify] FAIL: исключение: %s" % str(e)[:200])
            ok = False
        # s004: guard снимается ТОЛЬКО при зелёной верификации;
        # при FAIL guard остаётся — следующий прогон откажет (exit 2)
        if REAL_MODE and ok:
            guard_clear(run_id)
            log("[real] guard снят (прогон зелёный)")
    finally:
        cleanup_names = [NEG_USER] if REAL_MODE else [ZOND1, ZOND2]
        for name in cleanup_names:
            for attempt in (1, 2):
                try:
                    u = find_user(users, name)
                    if u is not None:
                        u.Удалить()
                        log("[cleanup] %s удалён" % name)
                    break
                except Exception as e:
                    if attempt == 2:
                        log("[cleanup] fail %s: %s" % (name, str(e)[:120]))
                    else:
                        try:
                            agent = win32com.client.Dispatch("V85.COMConnector").Connect(
                                conn_str(ADMIN, ""))
                            users = agent.ПользователиИнформационнойБазы
                        except Exception:
                            pass
        io.open(GATE_LOG, "w", encoding="utf-8").write("\n".join(log_lines))
    return finish(ok)


def verify(agent, users, checks, data_b, hashes):
    ok = True

    def check(cond, label):
        nonlocal ok
        log("  [%s] %s" % ("OK" if cond else "FAIL", label))
        if not cond:
            ok = False

    run_dir = checks.get("runDir", "")

    scan = read_json(os.path.join(run_dir, "scan.json"))
    check(scan is not None, "scan.json читается")
    reps = (scan or {}).get("representatives") or []
    scan_users = (scan or {}).get("users") or []
    check(len(reps) >= 1, "представителей >=1 (%d)" % len(reps))
    check(len(scan_users) >= 1, "пользователей скана >=1 (%d)" % len(scan_users))
    doc_types = set(r.get("type", "") for r in reps)
    check(len(doc_types) >= 1, "типов документов >=1 (%s)" % ", ".join(sorted(doc_types)))

    fixtures = read_json(os.path.join(run_dir, "fixtures.json"))
    check(fixtures is not None, "fixtures.json читается")
    plan_users = (fixtures or {}).get("plan") or (fixtures or {}).get("users") or []
    if not plan_users and fixtures:
        # структура: возможно, план лежит внутри другой секции
        plan_users = fixtures.get("plan", [])
    check(len(plan_users) >= 1, "план: пользователей >=1 (%d)" % len(plan_users))

    feature_files = glob.glob(os.path.join(run_dir, "features", "*.feature"))
    check(len(feature_files) >= 2, "фичи сгенерированы (>=2, есть %d)" % len(feature_files))

    batches = data_b.get("batches") or []
    check(len(batches) == 2, "батчей 2 (%d)" % len(batches))
    for b in batches:
        check(b.get("returnStatus") == "0",
              "батч %s (%s): ReturnStatus=0 (=%s)"
              % (b.get("batch"), b.get("user"), b.get("returnStatus")))
        check(b.get("status") == "ok", "батч %s: status=ok" % b.get("batch"))
        check(b.get("passwordRestored") is True,
              "батч %s: пароль восстановлен" % b.get("batch"))
        check(b.get("zodRestored") is True, "батч %s: ЗОД восстановлен" % b.get("batch"))

    bj = os.path.join(run_dir, "batches.json")
    check(os.path.exists(bj), "batches.json записан")
    params_left = glob.glob(os.path.join(run_dir, "params", "vaparams-*.json"))
    check(not params_left, "VAParams-файлы удалены (%d осталось)" % len(params_left))

    allure = glob.glob(os.path.join(run_dir, "allure", "**", "*-result.json"),
                       recursive=True)
    check(len(allure) >= 2, "allure result.json >=2 (%d)" % len(allure))

    # Пароли: исходный принят / тестовый отвергнут (COM, только чтение)
    test_pwd = data_b.get("testPassword", "")
    for name in (ZOND1, ZOND2):
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

    summary_json = os.path.join(run_dir, "summary.json")
    summary_md = os.path.join(run_dir, "summary.md")
    summary = read_json(summary_json)
    check(summary is not None, "summary.json читается")
    md_text = ""
    if os.path.exists(summary_md):
        md_text = io.open(summary_md, encoding="utf-8-sig").read()
    check("passed" in md_text.lower(), "summary.md содержит 'passed'")

    # T9: arm-* фичи обязаны присутствовать в манифесте прогона и отчёте
    rmanifest = read_json(os.path.join(run_dir, "features-manifest.json"))
    rfiles = (rmanifest or {}).get("files") or []
    arm_in_manifest = sorted(str(f.get("template", "")) for f in rfiles
                             if str(f.get("template", "")).startswith("arm-"))
    check(len(arm_in_manifest) >= 1,
          "ограниченный манифест содержит arm-шаблоны (%s)"
          % (", ".join(arm_in_manifest) or "нет"))
    check("Отражение выработки" in md_text,
          "summary.md: сценарий АРМ выработки присутствует")
    check("Отражение заправок" in md_text,
          "summary.md: сценарий АРМ заправок присутствует")
    check("Отражение расхода топлива" in md_text,
          "summary.md: сценарий АРМ расхода топлива присутствует")

    totals = (summary or {}).get("totals") or {}
    expected = sum(int(f.get("scenarios") or 0) for f in rfiles)
    check(expected >= 4, "ожидается не менее 4 сценариев (= %d)" % expected)
    check(totals.get("passed", 0) >= expected,
          "totals.passed >= %d (=%s)" % (expected,
          json.dumps(totals, ensure_ascii=False)))

    checks["verify"] = {"scan": len(reps), "users": len(scan_users),
                        "docTypes": sorted(doc_types), "allure": len(allure),
                        "totals": totals}
    return ok


def verify_real(agent, users, checks, data_b, hashes, snapshot):
    """s004: верификация режима реальных авторов.

    Уровни защиты паролей: (1) snapshot гейта до Stage B,
    (2) флаги passwordRestored/pwdSubstituted батчей, (3) COM-чтение
    исходного состояния авторов после прогона. Негатив: инверсия на
    уровне отчёта (СобратьОтчет) — здесь проверяем итоги summary.
    """
    ok = True

    def check(cond, label):
        nonlocal ok
        log("  [%s] %s" % (["FAIL", "OK"][bool(cond)], label))
        if not cond:
            ok = False

    run_dir = checks.get("runDir", "")
    authors = checks.get("realAuthors") or []

    scan = read_json(os.path.join(run_dir, "scan.json"))
    check(scan is not None, "scan.json читается")
    fixtures = read_json(os.path.join(run_dir, "fixtures.json"))
    check(fixtures is not None, "fixtures.json читается")
    feature_files = glob.glob(os.path.join(run_dir, "features", "*.feature"))
    check(len(feature_files) >= 2, "фичи сгенерированы (>=2, есть %d)" % len(feature_files))

    rmanifest = read_json(os.path.join(run_dir, "features-manifest.json"))
    rfiles = (rmanifest or {}).get("files") or []
    neg_entries = [f for f in rfiles if f.get("negative")]
    check(len(neg_entries) == 1, "neg-запись в манифесте (= %d)" % len(neg_entries))
    check(all(f.get("user") != NEG_USER or f.get("negative") for f in rfiles),
          "NEG-пользователь только в neg-записи")

    batches = data_b.get("batches") or []
    expected_batches = len(authors) + 1
    check(len(batches) == expected_batches,
          "батчей == авторы+neg (= %d, ожидается %d)" % (len(batches), expected_batches))
    for b in batches:
        is_neg = b.get("user") == NEG_USER
        check(b.get("pwdSubstituted") is True,
              "батч %s (%s): пароль подменён (pwdSubstituted)"
              % (b.get("batch"), b.get("user")))
        check(b.get("passwordRestored") is True,
              "батч %s: пароль восстановлен" % b.get("batch"))
        if not is_neg:
            check(b.get("returnStatus") == "0",
                  "батч %s (%s): ReturnStatus=0 (=%s)"
                  % (b.get("batch"), b.get("user"), b.get("returnStatus")))
        # neg-батч: VA-вердикт failed ОЖИДАЕМ (честно красный сценарий);
        # инверсия проверяется ниже по summary
    check(all(b.get("user") in authors or b.get("user") == NEG_USER for b in batches),
          "все батчи - авторы плана или NEG-пользователь")

    params_left = glob.glob(os.path.join(run_dir, "params", "vaparams-*.json"))
    check(not params_left, "VAParams-файлы удалены (%d осталось)" % len(params_left))

    # Уровень-3: COM-чтение исходного состояния авторов
    for name in authors:
        u = find_user(users, name)
        if u is None:
            check(False, "%s: пользователь исчез" % name)
            continue
        snap = snapshot.get(name, {})
        check(bool(u.ПарольУстановлен) == snap.get("pwdSet"),
              "%s: ПарольУстановлен == исходному" % name)
        if snap.get("pwdSet"):
            check(str(u.СохраняемоеЗначениеПароля) == snap.get("hash"),
                  "%s: хэш == исходному (COM)" % name)
        else:
            check(not u.ПарольУстановлен, "%s: пароля нет (COM)" % name)

    # NEG-пользователь: создан, пароль восстановлен раннером, будет
    # удалён в finally (проверка удаления - лог cleanup)
    neg_u = find_user(users, NEG_USER)
    check(neg_u is not None, "%s существует на момент verify" % NEG_USER)
    if neg_u is not None:
        check(str(neg_u.СохраняемоеЗначениеПароля) == hashes.get(NEG_USER),
              "%s: хэш == созданному (раннер вернул тестовый)" % NEG_USER)

    summary = read_json(os.path.join(run_dir, "summary.json"))
    check(summary is not None, "summary.json читается")
    totals = (summary or {}).get("totals") or {}
    check(totals.get("negativePassed", 0) >= 1,
          "totals.negativePassed >= 1 (=%s)"
          % json.dumps(totals, ensure_ascii=False))
    check(totals.get("negativeFailed", 0) == 0,
          "totals.negativeFailed == 0 (=%s)"
          % json.dumps(totals, ensure_ascii=False))
    expected_positive = sum(int(f.get("scenarios") or 0) for f in rfiles
                            if not f.get("negative"))
    check(totals.get("passed", 0) >= expected_positive,
          "totals.passed >= %d (позитивные сценарии) (= %s)"
          % (expected_positive, json.dumps(totals, ensure_ascii=False)))

    md_path = os.path.join(run_dir, "summary.md")
    md_text = ""
    if os.path.exists(md_path):
        md_text = io.open(md_path, encoding="utf-8-sig").read()
    check("neg-passed" in md_text, "summary.md содержит neg-passed")

    checks["verify"] = {"authors": authors, "totals": totals}
    return ok


def finish(ok):
    verdict = "PASS" if ok else "FAIL"
    log("VERDICT: %s" % verdict)
    io.open(GATE_LOG, "w", encoding="utf-8").write("\n".join(log_lines))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
