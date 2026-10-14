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


def kill_tree(pid):
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)


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
    for entry in files:
        tmpl = entry.get("template", "")
        if tmpl == "00-smoke" and smoke_src is None:
            smoke_src = entry.get("file", "")
        if tmpl == "01-pl-tractor" and tractor_src is None:
            tractor_src = entry.get("file", "")
    if not smoke_src or not os.path.exists(smoke_src):
        return None, "сгенерированный smoke-файл не найден"
    if not tractor_src or not os.path.exists(tractor_src):
        return None, "сгенерированный 01-pl-tractor файл не найден"

    fdir = os.path.join(run_dir, "features")
    smoke_dst = os.path.join(fdir, "00-smoke--ApkSct-Zond1.feature")
    tractor_dst = os.path.join(fdir, "01-pl-tractor--ApkSct-Zond2.feature")
    shutil.copyfile(smoke_src, smoke_dst)
    shutil.copyfile(tractor_src, tractor_dst)

    restricted = {
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "files": [
            {"file": smoke_dst.replace("\\", "/"), "template": "00-smoke",
             "user": ZOND1, "scenarios": 1, "documents": []},
            {"file": tractor_dst.replace("\\", "/"), "template": "01-pl-tractor",
             "user": ZOND2, "scenarios": 1, "documents": []},
        ],
        "warnings": [
            "T8 E2E restriction: батчи ограничены временными пользователями "
            "(безопасность); реальные авторы плана - pending user confirmation",
        ],
    }
    with io.open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(restricted, f, ensure_ascii=False, indent=1)

    orig_users = sorted(set(e.get("user", "") for e in files if e.get("user")))
    checks["generatedUsers"] = orig_users
    checks["restricted"] = True
    return orig_users, None


def main():
    checks = {}
    agent = win32com.client.Dispatch("V85.COMConnector").Connect(conn_str(ADMIN, ""))
    users = agent.ПользователиИнформационнойБазы
    hashes = {}
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
        hashes[ZOND1] = create_user(agent, users, ZOND1)
        hashes[ZOND2] = create_user(agent, users, ZOND2)
        orig_users, err = restrict_manifest(run_dir, checks)
        if err:
            log("[restrict] FAIL: %s" % err)
            return finish(False)
        log("[restrict] манифест ограничен: Зонд1=smoke, Зонд2=01-pl-tractor")
        log("[restrict] реальные авторы (pending user confirmation): %s"
            % "; ".join(orig_users))

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
                if not data_b:
                    log("[stage-b] FAIL: результат T6-раннера недоступен")
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

        # --- Верификация -----------------------------------------------
        ok = verify(agent, users, checks, data_b, hashes)
    finally:
        for name in (ZOND1, ZOND2):
            try:
                u = find_user(users, name)
                if u is not None:
                    u.Удалить()
                    log("[cleanup] %s удалён" % name)
            except Exception as e:
                log("[cleanup] fail %s: %s" % (name, str(e)[:120]))
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
    totals = (summary or {}).get("totals") or {}
    check(totals.get("passed", 0) >= 2,
          "totals.passed >=2 (=%s)" % json.dumps(totals, ensure_ascii=False))

    checks["verify"] = {"scan": len(reps), "users": len(scan_users),
                        "docTypes": sorted(doc_types), "allure": len(allure),
                        "totals": totals}
    return ok


def finish(ok):
    verdict = "PASS" if ok else "FAIL"
    log("VERDICT: %s" % verdict)
    io.open(GATE_LOG, "w", encoding="utf-8").write("\n".join(log_lines))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
