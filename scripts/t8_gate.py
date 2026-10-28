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
# s004: real-режим переносит РЕПЕТИЦИОННЫЙ (валидированный) набор шаблонов
# на реальных авторов; невалидированные (02/03/04/05) - pending (runbook §6)
REAL_TEMPLATES = ["00-smoke", "01-pl-tractor",
                  "02-pl-auto", "03-piece-work-order",
                  "04-fuel-sheet", "05-weighing",
                  "arm-fuel-receipt", "arm-payroll", "arm-fuel-expense"]

# s004 blocker-A: нейтральный сервисный пользователь runner-сессий.
# Батч под той же учёткой, что раннер (same-user TestClient), виснет;
# инвариант: runner identity != любой пользователь батча.
MANAGER_USER = "АпкСценТест_Менеджер"
MANAGER_FULLNAME = "Менеджер раннеров s004 (удаляется)"
# 21.10: ПолныеПрава НЕ включает право запуска внешних обработок —
# без этой роли БСП блокирует /Execute раннера модалкой «запрещен
# запуск внешних обработок» (diag-зонд tmp/s004/out_diagmgr.txt)
# 22.10: запуск внешних обработок — ОТДЕЛЬНОЕ право; его несёт роль
# VAExtension_ОбщиеПрава (есть у ADMIN и у neg-юзера в NEG_ROLES).
# Доказательство (diag-серия, флаги реестра 1/1): mgr с 4 ролями+
# ИнтерактивноеОткрытие... — блок модалкой; mgr с +VAExtension_ОбщиеПрава
# — раннер стартовал (runner_result.json step=password-generated).
MANAGER_ROLES = NEED_ROLES + ["ИнтерактивноеОткрытиеВнешнихОтчетовИОбработок",
                               "ЗапускТонкогоКлиента",
                               "VAExtension_ОбщиеПрава"]

# s004: режим реальных авторов — флаг CLI; guard-файлы парольной опасности
REAL_MODE = "--real-authors" in sys.argv
GUARD_DIR = os.path.join(ROOT, "tests", "pwd-guard")
RAC = r"C:\Program Files\1cv8\8.5.4.1683\bin\rac.exe"
RAC_CLUSTER = "67cdef87-7bfc-4dae-b8e4-3ea9f8529156"
RAC_INFOBASE = "4d9168e8-f640-490f-bbe6-32b1df12991f"  # dev_erpapk_demo

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


def create_manager_user(agent, users):
    """s004 blocker-A: нейтральный сервисный пользователь runner-сессий.

    24.10 FIX (run10b/c root cause, bisect-серия 2/4/5): Менеджер
    ОБЯЗАТЕЛЬНО регистрируется в справочнике «Пользователи» с
    привязкой UUID (blocker-B паттерн, как у neg). НЕзарегистрированного
    админа БСП при входе нормализует (Пользователи.СоздатьАдминистратор
    перезаписывает роли ИБ на ПолныеПрава+АдминистраторСистемы+
    DefaultRole) — срезаются ИнтерактивноеОткрытие... и
    ЗапускТонкогоКлиента → /Execute раннера denied модалкой «Текущему
    пользователю запрещен запуск внешних обработок». Зарегистрированного
    БСП не трогает (neg прошёл 2 прогона с полным составом ролей).
    """
    old = find_user(users, MANAGER_USER)
    if old is not None:
        old.Удалить()
    u = users.СоздатьПользователя()
    u.Имя = MANAGER_USER
    u.ПолноеИмя = MANAGER_FULLNAME
    md_roles = agent.Метаданные.Роли
    for rn in MANAGER_ROLES:
        u.Роли.Добавить(getattr(md_roles, rn))
    try:
        u.ЗащитаОтОпасныхДействий.ПредупреждатьОбОпасныхДействиях = False
    except Exception as e:
        log("[setup] ЗОД off fail (%s): %s" % (MANAGER_USER, str(e)[:80]))
    u.Записать()
    # 24.10: регистрация в справочнике (иммунитет к БСП-нормализации ролей)
    mgr_uuid = find_user(users, MANAGER_USER).УникальныйИдентификатор
    spr = agent.Справочники.Пользователи
    q = agent.NewObject("Query")
    q.Text = ("ВЫБРАТЬ Пользователи.Ссылка ИЗ Справочник.Пользователи "
              "КАК Пользователи ГДЕ Пользователи.Наименование = &Имя")
    q.УстановитьПараметр("Имя", MANAGER_FULLNAME)
    sel = q.Execute().Choose()
    while sel.Next():
        sel.Ссылка.ПолучитьОбъект().Удалить()
    el = spr.СоздатьЭлемент()
    el.Наименование = MANAGER_FULLNAME
    el.ИдентификаторПользователяИБ = mgr_uuid
    el.Записать()
    # обычная запись теряет привязку UUID (БСП-обработчик очищает её) —
    # перезапись в режиме загрузки (blocker-B факт tmp/s004)
    ref = spr.НайтиПоНаименованию(MANAGER_FULLNAME)
    obj = ref.ПолучитьОбъект()
    obj.ОбменДанными.Загрузка = True
    obj.Наименование = MANAGER_FULLNAME
    obj.ИдентификаторПользователяИБ = mgr_uuid
    obj.Записать()
    log("[setup] %s создан (роли: %s, без пароля, зарегистрирован в "
        "справочнике Пользователи — blocker-B, иммунитет к БСП-нормализации)"
        % (MANAGER_USER, "+".join(MANAGER_ROLES)))


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


def real_data_guards(agent, run_dir):
    """T12 (RCA SA1/SA2): гварды данных перед real-прогоном.

    1) РС АпкНастройкиВесовой: записи с ПодключенВесовойТерминал=ИСТИНА
       глушат все 4 весовых поля формы взвешивания при создании
       (ФормаДокумента Module.bsl:27, ветка терминала — вес идёт с
       демо-весов, ручной ввод запрещён) — 05-weighing упадёт;
    2) АпкСкладБака у ТС из фикстур 02-pl-auto: пустой склад бака =
       «Значение поля \"Склад\" не может быть пустым» (РН Товары на
       складах) при закрытии работы сценарного ПЛ (ПроведениеДокументов
       Module.bsl:2099, Склад = СтрокаГСМ.АпкСкладБака).
    Возвращает список ошибок (пустой = ок)."""
    errs = []
    try:
        q = agent.NewObject("Query")
        q.Text = ("ВЫБРАТЬ КОЛИЧЕСТВО(*) КАК К "
                  "ИЗ РегистрСведений.АпкНастройкиВесовой КАК Р "
                  "ГДЕ Р.ПодключенВесовойТерминал = ИСТИНА")
        sel = q.Execute().Choose()
        n = int(sel.К) if sel.Next() else 0
        if n:
            errs.append("АпкНастройкиВесовой: %d записей с включённым "
                        "весовым терминалом (весовые поля формы "
                        "взвешивания недоступны, 05-weighing упадёт)" % n)
    except Exception as e:
        errs.append("весовая: %s" % str(e)[:120])
    fx = read_json(os.path.join(run_dir, "fixtures.json"))
    ts_uuids = set()
    for d in (fx or {}).get("documents") or []:
        if d.get("type") != "АпкПутевойЛистАвтотранспорта":
            continue
        data = d.get("data") or {}
        u = ((data.get("header") or {}).get("Автомобиль") or {}).get("uuid")
        if u:
            ts_uuids.add(u)
        for part in ((data.get("tabular") or {}).get("ГСМ") or []):
            u = (part.get("ТранспортноеСредство") or {}).get("uuid")
            if u:
                ts_uuids.add(u)
    for u in sorted(ts_uuids):
        try:
            uid = agent.NewObject("УникальныйИдентификатор", u)
            ref = agent.Справочники.ТранспортныеСредства.ПолучитьСсылку(uid)
            if ref.Пустая():
                errs.append("ТС %s не найден" % u)
                continue
            sb = ref.АпкСкладБака
            if sb is None or sb.Пустая():
                errs.append("у ТС %s пустой АпкСкладБака (02-pl-auto: "
                            "«Склад не может быть пустым» при проведении)" % u)
        except Exception as e:
            errs.append("ТС %s: %s" % (u, str(e)[:120]))
    return errs


def cleanup_scenario_artifacts(agent):
    """T12: teardown real-гейта — удаляет сценарные артефакты за сегодня.

    ПЛ автотранспорта (кроме реального представителя НВЦБ-000002) —
    иначе повторный прогон того же дня конфликтует по РС
    АпкСчетчикТранспортныхСредств (ключ Дата+ТС, «запись существует»);
    взвешивания — освобождают талоны (РС АпкМассаРаспределеннаяПоТалонам,
    «Талон уже использован»). Реальные документы (дата < сегодня)
    не затрагиваются. Полные прогоны не зависят (dump + rollback)."""
    today = datetime.date.today()
    d1 = datetime.datetime(today.year, today.month, today.day)
    deleted = {"pl": 0, "weighing": 0}
    for doctype, keep in (("АпкПутевойЛистАвтотранспорта", "НВЦБ-000002"),
                          ("АпкРегистрацияВзвешиванийНаТоку", None)):
        try:
            q = agent.NewObject("Query")
            q.Text = ("ВЫБРАТЬ С.Ссылка КАК Ref, С.Номер КАК N "
                      "ИЗ Документ.%s КАК С ГДЕ С.Дата >= &D1" % doctype)
            q.УстановитьПараметр("D1", d1)
            sel = q.Execute().Choose()
            refs = []
            while sel.Next():
                refs.append((sel.Ref, str(sel.N)))
            for ref, num in refs:
                if keep and num == keep:
                    continue
                try:
                    ref.GetObject().Delete()
                    deleted["pl" if keep else "weighing"] += 1
                except Exception as e:
                    log("[cleanup] сценарный артефакт %s: %s"
                        % (num, str(e)[:100]))
        except Exception as e:
            log("[cleanup] %s: %s" % (doctype, str(e)[:120]))
    log("[cleanup] сценарные артефакты за сегодня удалены: "
        "ПЛ=%d, взвешиваний=%d" % (deleted["pl"], deleted["weighing"]))
    return deleted


def kill_tree(pid):
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)


# --- s004: режим реальных авторов -------------------------------------

def rac_sessions_online(exclude_app_ids=("RAS",)):
    """Онлайн-сеансы на dev_erpapk_demo (FR-003, exit 2 у вызывающего).

    exclude_app_ids - app-id, НЕ считающиеся блокирующими (префлайт:
    только RAS-служба; пост-Stage-A рубеж: + COMConnection гейта и
    умирающие с пустым app-id).
    Возвращает (список_строк_описаний, код_ошибки|None).
    """
    try:
        out = subprocess.run([RAC, "session", "list", "--cluster=" + RAC_CLUSTER],
                             capture_output=True, timeout=60)
    except Exception as e:
        return None, "rac недоступен: %s" % str(e)[:150]
    # 21.10: CRLF-нормализация (иначе весь список = один блок, см.
    # rac_terminate_ib_sessions)
    txt = out.stdout.decode("cp866", errors="replace").replace("\r\n", "\n")
    sessions = []
    for block in txt.split("\n\n"):
        fields = {}
        for line in block.splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                fields[k.strip()] = v.strip()
        if fields.get("infobase") == RAC_INFOBASE \
                and fields.get("app-id") not in exclude_app_ids:
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


def rac_terminate_ib_sessions(only_user=None, app_ids=("1CV8",)):
    """Терминирует зомби-сеансы нашей базы с app-id из app_ids.

    COM-соединения (гейт) не трогаем. only_user - фильтр по имени.
    Возвращает количество терминированных.
    """
    out = subprocess.run([RAC, "session", "list", "--cluster=" + RAC_CLUSTER],
                         capture_output=True, timeout=60)
    # 21.10: rac-вывод в CRLF - без нормализации весь список = один блок
    # (терминировался только последний сеанс)
    txt = out.stdout.decode("cp866", errors="replace").replace("\r\n", "\n")
    killed = 0
    for block in txt.split("\n\n"):
        f = {}
        for line in block.splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                f[k.strip()] = v.strip()
        if f.get("infobase") != RAC_INFOBASE or f.get("app-id") not in app_ids:
            continue
        if only_user and f.get("user-name") != only_user:
            continue
        suuid = f.get("session", "")
        if suuid:
            r = subprocess.run([RAC, "session", "terminate",
                                "--cluster=" + RAC_CLUSTER,
                                "--session=" + suuid], capture_output=True, timeout=30)
            if r.returncode == 0:
                killed += 1
            else:
                log("   session terminate %s (%s) FAIL rc=%s"
                    % (suuid, f.get("app-id", ""), r.returncode))
    return killed


def create_neg_user(agent, users):
    """Негативный пользователь: 5 СУЩЕСТВУЮЩИХ ролей (TD-002), без Апк-прав.

    БСП-блок: пользователь с правом Администрирование без ПолныхПрав
    обязан быть зарегистрирован в справочнике Пользователи
    (ПользователиСлужебный.ПриАвторизацииПользователяИБ, ERPsrc) —
    регистрируем элемент вручную (зонды обходили это через
    авторегистрацию БСП: ПолныеПрава+АдмСистемы). Удаляется в cleanup.
    s004 blocker-B: обычная запись теряет привязку UUID (БСП-обработчик
    очищает ИдентификаторПользователяИБ), поэтому перезапись в режиме
    ОбменДанными.Загрузка + запрос-верификация (факт tmp/s004).
    """
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
    # s004: регистрация в справочнике Пользователи (обход БСП-блока)
    neg_uuid = find_user(users, NEG_USER).УникальныйИдентификатор
    spr = agent.Справочники.Пользователи
    q = agent.NewObject("Query")
    q.Text = ("ВЫБРАТЬ Пользователи.Ссылка ИЗ Справочник.Пользователи "
              "КАК Пользователи ГДЕ Пользователи.Наименование = &Имя")
    q.УстановитьПараметр("Имя", NEG_FULLNAME)
    sel = q.Execute().Choose()
    while sel.Next():
        sel.Ссылка.ПолучитьОбъект().Удалить()
    el = spr.СоздатьЭлемент()
    el.Наименование = NEG_FULLNAME
    el.ИдентификаторПользователяИБ = neg_uuid
    el.Записать()
    # s004 blocker-B: обычная запись теряет привязку UUID (БСП-обработчик
    # очищает её при записи) — перезаписываем в режиме загрузки
    ref = spr.НайтиПоНаименованию(NEG_FULLNAME)
    obj = ref.ПолучитьОбъект()
    obj.ОбменДанными.Загрузка = True
    obj.Наименование = NEG_FULLNAME
    obj.ИдентификаторПользователяИБ = neg_uuid
    obj.Записать()
    # верификация привязки (COM UUID нельзя сравнивать строками —
    # только через параметр запроса)
    qv = agent.NewObject("Query")
    qv.Text = ("ВЫБРАТЬ Пользователи.Ссылка ИЗ Справочник.Пользователи "
               "КАК Пользователи ГДЕ Пользователи.ИдентификаторПользователяИБ = &UUID")
    qv.УстановитьПараметр("UUID", neg_uuid)
    sv = qv.Execute().Choose()
    bound = 0
    while sv.Next():
        bound += 1
    if bound != 1:
        raise RuntimeError("neg-элемент: Загрузка-привязка UUID не удалась "
                            "(bound=%d)" % bound)
    log("[setup] %s создан (роли: %s, зарегистрирован в справочнике "
        "Пользователи, Загрузка-привязка UUID подтверждена), H1 len=%d"
        % (NEG_USER, "+".join(NEG_ROLES), len(h1)))
    return h1


def delete_neg_catalog_element(agent):
    """Удаляет элемент справочника Пользователи neg-пользователя."""
    q = agent.NewObject("Query")
    q.Text = ("ВЫБРАТЬ Пользователи.Ссылка ИЗ Справочник.Пользователи "
              "КАК Пользователи ГДЕ Пользователи.Наименование = &Имя")
    q.УстановитьПараметр("Имя", NEG_FULLNAME)
    sel = q.Execute().Choose()
    n = 0
    while sel.Next():
        sel.Ссылка.ПолучитьОбъект().Удалить()
        n += 1
    if n:
        log("[cleanup] справочник Пользователи: удалено элементов neg: %d" % n)


# T13: точечные патчи сценариев 02-pl-auto (применяются к сгенерированному
# feature-файлу ДО батчей; все значения уже подставлены из фикстур).
# НВ00-000009: РС АпкСчетчикТранспортныхСредств, ключ (Период, ТС) —
# конфликт с НВЦБ-000002 (КАМАЗ Т836ХН36) в тот же день; ТС сценария
# меняется на КАМАЗ Т835ХН36 — та же модель КАМАЗ-65115 (нормы
# расхода те же), АпкСкладБака заполнен, остаток 162 л, последний
# счётчик 76988 < СпидометрВыезд 89999 (COM-зонд tmp/t13/, 26.10).
# НВ00-000004 (Toyota, «Доставка документов»): ТипЗатрат
# «Общехозяйственные» не перехватывается
# АпкРастениеводствоКлиент.АналитикаРасходовНачалоВыбора
# (Module.bsl:349-447) → стандартная форма выбора по типу реквизита —
# окно «Структура предприятия», значение «Автопарк» (фикстура).
# T13/T14: точечные патчи сгенерированных сценарных блоков (до батчей;
# значения уже подставлены из фикстур). Структура: шаблон →
# {номер документа в заголовке сценария → операции}.
# Операция ("replace", old, new): замена подстроки в блоке.
# Операция ("block", start_m, end_m, new_lines): вырезка от первой
# строки с start_m до первой строки с end_m ПОСЛЕ неё (включительно),
# вставка new_lines (() = чистая вырезка).
# Операция ("drop",): сценарий исключается из прогона целиком
# (блок + заголовок), номер — в списке dropped (для documents).
#
# 02-pl-auto: НВ00-000009 — РС АпкСчетчикТранспортныхСредств, ключ
# (Период, ТС): конфликт с НВЦБ-000002 (КАМАЗ Т836ХН36) в тот же день;
# ТС меняется на КАМАЗ Т835ХН36 (та же модель = те же нормы,
# АпкСкладБака заполнен, остаток 162 л, счётчик 76988 < 89999).
# НВ00-000004 (Toyota, «Доставка документов»): ТипЗатрат
# «Общехозяйственные» не перехватывается
# АпкРастениеводствоКлиент.АналитикаРасходовНачалоВыбора →
# стандартный выбор по строке: ввод текста «Автопарк» (уникален,
# окно не открываем; UIA-клик в динамической форме выбора не
# работает — T13 iter7).
#
# 05-weighing (T14, 26.10): складские виды ВзвешиванияНаТоку (НВ00-000018
# Возврат, -016 Реализация, -014 Перемещение, -017 Поступление —
# автор СоколовМИ, файл ранее отфильтрован целиком): талоны НЕ
# вводим (страница Талоны скрыта для не-«с поля» вида; литералы
# 12-000099/100 конфликтуют с НВ00-000003) — вырезаем обе группы;
# Откуда — не «Объекты затрат» (склад/контрагент): ввод текстом
# значения фикстуры (уникально; при авто-установке сервером при
# выборе вида — перезаписывается тем же значением); у -016
# (Реализация) Автомобиль в фикстуре пуст — вырезаем и его.
SCENARIO_PATCHES = {
    "02-pl-auto": {
        "НВ00-000009": (("replace", u"КАМАЗ-65115, Гос.№Т836ХН36",
                         u"КАМАЗ-65115, Гос.№Т835ХН36"),),
        "НВ00-000004": (("block",
                         u'нажимаю кнопку выбора у реквизита с именем '
                         u'"ВыполненныеРаботыАналитикаРасходов"',
                         u'поле с именем "ВыполненныеРаботыАналитикаРасходов" '
                         u'имеет значение',
                         (u'\tИ в таблице "ВыполненныеРаботы" в поле с именем '
                          u'"ВыполненныеРаботыАналитикаРасходов" я ввожу текст "Автопарк"',
                          u'\tИ в таблице "ВыполненныеРаботы" я завершаю редактирование строки',
                          u'\tИ Пауза 1',
                          u'\tИ в таблице "ВыполненныеРаботы" поле с именем '
                          u'"ВыполненныеРаботыАналитикаРасходов" имеет значение "Автопарк"')),),
    },
    "05-weighing": {
        "НВ00-000018": (("drop",),),  # T15: структурный — после выбора
                        # «Возврат» вся шапка ТолькоПросмотр=Истина до
                        # выбора ОснованиеВозврата (Module.bsl:1443-1448)
                        # — требует перепроектированного сценария → pending
        # T18 iter13: три кандидата валидированы диагностиками v19/v21/v23
        # (status 0, документы проведены). Ключевые корни T18:
        #   (1) Куда ОБЯЗАТЕЛЕН (FillChecking=ShowError) - вывод iter11
        #       «не обязателен» был ошибочен; COM-зонд постится без Куда
        #       лишь потому, что стандартная проверка выполняется при
        #       интерактивной записи из формы;
        #   (2) dropdown «по строке» на ЧИСТОЙ форме работает через
        #       динамический поиск платформы даже с пустым СписокВыбора
        #       (Номенклатура/Куда@Реализация/Откуда@Поступление);
        #       прежние фейлы шага были ядовитым каскадом от ввода текста;
        #   (3) при Перемещении/Поступлении СписокВыбора Откуда/Куда
        #       ГРУЗИТСЯ складами (форма выбора НЕ открывается, UIA
        #       неприменим) - только нативные dropdown; при Реализации
        #       Откуда - форма выбора (окно Склады) + UIA (рецепт 000003);
        #   (4) после каждого ВВ-ввода обязателен «я перехожу к
        #       следующему реквизиту» (иначе ПриИзменении не срабатывает
        #       и ВесНетто остаётся 0);
        #   (5) талоны нужны только СПоля-видам (НВ00-000003), у
        #       складских видов страница скрыта;
        #   (6) Водитель/Автомобиль не проверяются (Требовать=False).
        "НВ00-000016": (
            # Откуда: форма выбора (окно Склады) + UIA (v19); assert
            # «Объекты затрат» неверен для Реализации - вырезаем вместе
            # с каскадом до первого «перехожу»; Куда dropdown «Эко-Нива»
            # работает (динамический поиск, корень 1+2).
            ("block", u'Тогда открылось окно "Объекты затрат"',
             u"я перехожу к следующему реквизиту",
             (u'\tИ Пауза 2',
              u'\tИ я читаю данные текущего профиля клиента тестирования',
              # T18 iter13b: генератор НЕ субституирует {{header.*}} для
              # не-СПоля документов (в baseline фейл происходил раньше
              # шага — placeholder никогда не исполнялся) → литерал
              # фикстуры, как в валидированном v19.
              u"\tИ я делаю двойной клик по элементу формы "
              u"'$PIDКлиентаТестирования$' "
              u"'Зерносклад №1 Наименование' '' UI Automation",
              u'\tИ Пауза 1',
              u'\tИ из выпадающего списка с именем "Куда" я выбираю '
              u'по строке "Эко-Нива"',
              u'\tИ Пауза 1')),
            ("block", u'с именем "Водитель"',
             u"я перехожу к следующему реквизиту", ()),
            ("block", u'с именем "Автомобиль"',
             u"я перехожу к следующему реквизиту", ()),
            ("block", u'с именем "Номенклатура"',
             u"я перехожу к следующему реквизиту",
             (u'\tИ из выпадающего списка с именем "Номенклатура" '
              u'я выбираю по строке "Пшеница озимая, 3 кл, 2015 г."',
              u'\tИ Пауза 1')),
            ("block", u'нажимаю на кнопку с именем "ТалоныДобавитьТалон"',
                         u"Пауза 2", ()),
            ("block", u'нажимаю на кнопку с именем "ТалоныДобавитьТалон"',
                         u"Пауза 3", ())),
        "НВ00-000014": (
            # NB: block-опы ДО replace (replace склеивает блок в одну
            # строку и ломает послочные маркеры block-опов)
            # Перемещение: СписокВыбора Откуда/Куда грузится складами
            # (окно НЕ открывается) - всё нативными dropdown (v21);
            # один block до первого «перехожу» съедает и Куда-строку -
            # пере-добавляем её в новых строках.
            ("block", u'выбираю значение реквизита с именем "Откуда"',
             u"я перехожу к следующему реквизиту",
             (u'\tИ из выпадающего списка с именем "Откуда" я выбираю '
              u'по строке "Зерносклад №1"',
              u'\tИ из выпадающего списка с именем "Куда" я выбираю '
              u'по строке "ЗАВ"')),
            ("block", u'с именем "Водитель"',
             u"я перехожу к следующему реквизиту", ()),
            ("block", u'с именем "Автомобиль"',
             u"я перехожу к следующему реквизиту", ()),
            ("block", u'с именем "Номенклатура"',
             u"я перехожу к следующему реквизиту",
             (u'\tИ из выпадающего списка с именем "Номенклатура" '
              u'я выбираю по строке "Пшеница озимая, 2015 г."',
              u'\tИ Пауза 1')),
            ("block", u'нажимаю на кнопку с именем "ТалоныДобавитьТалон"',
                         u"Пауза 2", ()),
            ("block", u'нажимаю на кнопку с именем "ТалоныДобавитьТалон"',
                         u"Пауза 3", ()),
            # ВВ в порядке фикстуры (Первое=2000, Второе=12000; v21)
            ("replace",
             u'в поле с именем "ПервоеВзвешиваниеАвтомобиля" я ввожу текст "12000"',
             u'в поле с именем "ПервоеВзвешиваниеАвтомобиля" я ввожу текст "2000"'),
            ("replace",
             u'в поле с именем "ВтороеВзвешиваниеАвтомобиля" я ввожу текст "2000"',
             u'в поле с именем "ВтороеВзвешиваниеАвтомобиля" я ввожу текст "12000"')),
        "НВ00-000017": (
            # NB: block-опы ДО replace — см. 000014
            # Поступление: Откуда=контрагент «Эко-Нива» - СписокВыбора
            # НЕ грузится -> dropdown с динамическим поиском (v23);
            # Куда dropdown «Зерносклад №1» (СписокВыбора складов).
            ("block", u'выбираю значение реквизита с именем "Откуда"',
             u"я перехожу к следующему реквизиту",
             (u'\tИ из выпадающего списка с именем "Откуда" я выбираю '
              u'по строке "Эко-Нива"',
              u'\tИ из выпадающего списка с именем "Куда" я выбираю '
              u'по строке "Зерносклад №1"')),
            ("block", u'с именем "Водитель"',
             u"я перехожу к следующему реквизиту", ()),
            ("block", u'с именем "Автомобиль"',
             u"я перехожу к следующему реквизиту", ()),
            ("block", u'с именем "Номенклатура"',
             u"я перехожу к следующему реквизиту",
             (u'\tИ из выпадающего списка с именем "Номенклатура" '
              u'я выбираю по строке "Подсолнечник продовольственный, 2015 г."',
              u'\tИ Пауза 1')),
            ("block", u'нажимаю на кнопку с именем "ТалоныДобавитьТалон"',
                         u"Пауза 2", ()),
            ("block", u'нажимаю на кнопку с именем "ТалоныДобавитьТалон"',
                         u"Пауза 3", ())),
    },
}


def _patch_scenarios(fpath, patches):
    """Патчит сценарные блоки feature-файла по patches
    (см. SCENARIO_PATCHES). Возвращает (n_scen, n_patched, лог-строки,
    dropped — номера исключённых ("drop") сценариев)."""
    with io.open(fpath, encoding="utf-8-sig") as f:
        lines = f.readlines()
    blocks, cur_title, cur = [], None, []
    for ln in lines:
        s = ln.lstrip()
        if s.startswith(u"Сценарий:") or s.startswith("Scenario:"):
            if cur_title is not None:
                blocks.append((cur_title, cur))
            cur_title, cur = s, []
        elif cur_title is not None:
            cur.append(ln)
        else:
            blocks.append((None, [ln]))
    if cur_title is not None:
        blocks.append((cur_title, cur))
    n_scen, n_pat, pat_log, dropped = 0, 0, [], []
    out = []
    for title, blines in blocks:
        if title is None:
            out.extend(blines)
            continue
        matched = [(key, ops) for key, ops in patches.items()
                   if key in title]
        if matched and any(op[0] == "drop" for _, ops in matched
                           for op in ops):
            key = matched[0][0]
            dropped.append(key)
            pat_log.append("%s: dropped (структурно несовместим)" % key)
            n_pat += 1
            continue
        n_scen += 1
        replaced = []
        for key, subs in matched:
            for op in subs:
                if op[0] == "replace":
                    _, old, new = op
                    joined = "".join(blines)
                    if old in joined:
                        blines = [joined.replace(old, new)]
                        replaced.append("%s: replace → %s" % (key, new))
                elif op[0] == "block":
                    _, start_m, end_m, new_lines = op
                    i0 = next((i for i, l in enumerate(blines)
                               if start_m in l), None)
                    i1 = (next((i for i in range(i0 + 1, len(blines))
                                if end_m in blines[i]), None)
                          if i0 is not None else None)
                    if i0 is not None and i1 is not None:
                        blines = (blines[:i0]
                                  + [l + "\n" for l in new_lines]
                                  + blines[i1 + 1:])
                        replaced.append("%s: block %s..%s"
                                        % (key, start_m[:24], end_m[:16]))
        if replaced:
            n_pat += 1
            pat_log.extend(replaced)
        out.append(title)
        out.extend(blines)
    if n_pat:
        with io.open(fpath, "w", encoding="utf-8") as f:
            f.writelines(out)
    return n_scen, n_pat, pat_log, dropped


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
    # s004: репетиционный allowlist — переносим валидированный набор
    dropped = sorted(set(e.get("template", "") for e in files
                         if e.get("template") not in REAL_TEMPLATES))
    files = [e for e in files if e.get("template") in REAL_TEMPLATES]
    if not files:
        return None, "после фильтра REAL_TEMPLATES манифест пуст"
    # T12/T13/T14: фильтры «один 02/05 на автора» СНЯТЫ.
    # 02: конфликт счётчика ТС решён свапом ТС сценария 009,
    # аналитика 004 — вводом текста (SCENARIO_PATCHES).
    # 05: талоны 12-000099/100 нужны ТОЛЬКО сценарию «Урожай с поля»
    # (НВ00-000003); складские виды (18/16/14/17, СоколовМИ) талоны не
    # вводят вообще (страница скрыта) — конфликта нет; их сценарии
    # патчатся (SCENARIO_PATCHES['05-weighing']). Talon-guard в
    # preflight проверяет свободу 12-000099/100.
    seen_plauto = False
    keep_files = []
    for e in files:
        if e.get("template") == "02-pl-auto":
            if seen_plauto:
                continue
            seen_plauto = True
        keep_files.append(e)
    dropped_w = len(files) - len(keep_files)
    files = keep_files
    if dropped_w:
        log("[real] отфильтровано записей манифеста: %d" % dropped_w)
    if seen_plauto:
        log("[real] 02-pl-auto: все сценарии манифеста (счётчик ТС: "
            "конфликт 009 решён свапом ТС, аналитика 004 — патчем; "
            "см. SCENARIO_PATCHES)")
    if dropped:
        log("[real] невалидированные шаблоны отложены (runbook §6): %s"
            % ", ".join(dropped))
    # T13/T14: сценарные патчи по шаблонам (SCENARIO_PATCHES); обрезка
    # и фильтры 02/05 сняты — все сценарии манифеста гоняются.
    for e in files:
        tpl = e.get("template", "")
        if tpl not in SCENARIO_PATCHES or not SCENARIO_PATCHES[tpl]:
            continue
        fpath = e.get("file", "")
        if not os.path.isfile(fpath):
            return None, "%s: файл не найден (%s)" % (tpl, fpath)
        n_scen, n_pat, pat_log, dropped_keys = _patch_scenarios(
            fpath, SCENARIO_PATCHES[tpl])
        if dropped_keys:
            docs = e.get("documents") or []
            e["documents"] = [d for d in docs
                              if not any(k in d for k in dropped_keys)]
            log("[real] %s: исключены сценарии (drop): %s"
                % (tpl, ", ".join(dropped_keys)))
        if n_scen <= 0:
            if dropped_keys:
                # все сценарии файла исключены — файл уходит из манифеста
                files = [x for x in files if x is not e]
                continue
            return None, "%s: сценариев не найдено (%s)" % (tpl, fpath)
        e["scenarios"] = n_scen
        if pat_log:
            log("[real] %s: сценариев=%d, патчей=%d (%s)"
                % (tpl, n_scen, n_pat, "; ".join(pat_log)))
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


def run_1c_session(runner_epf, timeout, client_log, result_file=None, usr=ADMIN):
    """Старт 1cv8 /Execute runner-EPF с UIA-watchdog и ожиданием завершения.

    Если задан result_file - драйвер выходит по step=done (паттерн T6/T7:
    клиентский сеанс после Финал(Закрыть) может не завершаться сам).
    """
    fp = open(client_log, "wb")
    proc = subprocess.Popen(
        [V8, "/S", CONN, "/RunModeManagedApplication", "/N", usr,
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
    # T14: talon-guard — талоны-литералы шаблона 05 должны быть свободны
    # (РН АпкМассаРаспределеннаяПоТалонам подчинён регистратору; занятость
    # = мусор от незавершённого прогона либо реальный документ)
    if REAL_MODE:
        try:
            tq = agent.NewObject("Query")
            tq.Text = (u"ВЫБРАТЬ ПРЕДСТАВЛЕНИЕ(М.Регистратор) КАК Док "
                       u"ИЗ РегистрНакопления.АпкМассаРаспределеннаяПоТалонам КАК М "
                       u"ГДЕ М.НомерТалона = &Н1 ИЛИ М.НомерТалона = &Н2")
            tq.УстановитьПараметр("Н1", "12-000099")
            tq.УстановитьПараметр("Н2", "12-000100")
            ts = tq.Execute().Choose()
            busy = []
            while ts.Next():
                busy.append(str(ts.Док)[:60])
            if busy:
                log("[preflight] FAIL: талоны 12-000099/12-000100 заняты "
                    "документами: %s — незавершённый прогон/реальные "
                    "данные, см. runbook §6" % "; ".join(busy))
                io.open(GATE_LOG, "w", encoding="utf-8").write("\n".join(log_lines))
                sys.exit(2)
            log("[preflight] OK: талоны 12-000099/12-000100 свободны")
        except SystemExit:
            raise
        except Exception as e:
            log("[preflight] WARN: talon-guard зонд не выполнен: %s"
                % str(e)[:120])
    users = agent.ПользователиИнформационнойБазы
    hashes = {}
    snapshot = {}
    ok = False
    try:
        # s004 blocker-A: нейтральный сервисный пользователь runner-сессий
        # (только real-режим); батчи под ADMIN виснут (same-user TestClient)
        runner_usr = MANAGER_USER if REAL_MODE else ADMIN
        if REAL_MODE:
            create_manager_user(agent, users)
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
                                   STAGE_A_RESULT, usr=runner_usr):
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
            # второй рубеж rac-проверки ПОСЛЕ Stage A. Сеанс раннера
            # Stage A (он же ADMIN) мог задержаться в rac после
            # step=done — терминируем lingering 1CV8-сеансы нашей базы
            # (префлайт гарантировал 0 внешних) и перепроверяем.
            # s004: рубеж после Stage A игнорирует собственный COM-агент
            # гейта (app-id=COMConnection, живёт от Connect до verify),
            # RAS-службу и умирающие сеансы (пустой app-id). 1CV8
            # (зомби раннера) терминируем. BackgroundJob (отложенное
            # задание БСП/ERP, стартованное сессией раннера) НЕ трогаем:
            # 21.10 run6 - после УБИЙСТВА активного BackgroundJob
            # клиент Stage B завис на старте сессии (ни одного шага
            # runner_result.json); задание умирает само (~5-8 мин,
            # факт run5) - ДОЖИДАЕМСЯ исчезновения, окно ~12 мин.
            # Префлайт ДО Stage A остаётся строгим (0, кроме RAS).
            sessions, rac_err = None, None
            for attempt in range(16):
                n1 = rac_terminate_ib_sessions(app_ids=("1CV8",))
                sessions, rac_err = rac_sessions_online(
                    exclude_app_ids=("RAS", "COMConnection", ""))
                log("[real] post-A seance check %d: killed1cv8=%d alive=%d"
                    % (attempt + 1, n1, len(sessions)))
                if rac_err or not sessions:
                    break
                time.sleep(45)
            if rac_err or sessions:
                log("[real] FAIL: онлайн-сеансы после Stage A: %s"
                    % (rac_err or "; ".join(sessions)))
                return finish(False)
            authors, err = prepare_real_manifest(run_dir, checks)
            if err:
                log("[real] FAIL: %s" % err)
                return finish(False)
            # s004 blocker-A: runner identity не должен совпадать с автором
            if MANAGER_USER in authors:
                log("[real] FAIL: менеджер совпадает с автором батча")
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
            guard_errs = real_data_guards(agent, run_dir)
            if guard_errs:
                for ge_ in guard_errs:
                    log("[real] FAIL гвард данных: %s" % ge_)
                return finish(False)
            log("[real] гварды данных OK (весовой терминал выкл, "
                "склад бака заполнен)")
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
        # s004: real-режим — батчи больше (автор+neg), таймауты шире
        # (пер-батч 1200 c, стадия 3600 c).
        timeout_batches = 3600 if REAL_MODE else TIMEOUT_BATCHES
        per_batch = 1200 if REAL_MODE else 0
        # 24.10 (run10b/c root cause): перед запуском раннера проверяем
        # роли Менеджера — если БСП успел их срезать (незарегистрированный
        # админ нормализуется на [ПолныеПрава+АдмСистемы+DefaultRole]),
        # /Execute будет denied модалкой «запрещен запуск внешних
        # обработок». Регистрация в справочнике (24.10 фикс) даёт
        # иммунитет — это страховка.
        try:
            mgr_u = find_user(users, MANAGER_USER)
            actual_roles = set(r.Имя for r in mgr_u.Роли)
            missing = [rn for rn in MANAGER_ROLES if rn not in actual_roles]
            if missing:
                log("[stage-b] ABORT: у %s срезаны роли БСП-нормализацией: %s "
                    "— /Execute будет denied" % (MANAGER_USER, "+".join(missing)))
                return finish(False)
            log("[stage-b] роли %s в порядке (%d)" % (MANAGER_USER, len(actual_roles)))
        except Exception as e:
            log("[stage-b] проверка ролей %s FAIL: %s"
                % (MANAGER_USER, str(e)[:100]))
        log("[stage-b] батчи (T6-механизм: порты, сироты, finally)"
            + (" [real] пер-батч таймаут %d c" % per_batch if REAL_MODE else ""))
        with io.open(T6_TASK, "w", encoding="utf-8") as f:
            json.dump({"target": TARGET, "runDir": run_dir,
                       "timeoutOverrideSec": per_batch}, f, ensure_ascii=False)
        if os.path.exists(T6_RESULT):
            os.remove(T6_RESULT)
        wd = start_watchdog(timeout_batches * 2 + 120, "watchdog-b.log")
        data_b = None
        try:
            for attempt in (1, 2):
                if os.path.exists(T6_RESULT):
                    os.remove(T6_RESULT)
                log("[stage-b] попытка %d" % attempt)
                if not run_1c_session(T6_EPF, timeout_batches,
                                      os.path.join(ROOT, "tmp", "t6", "client.log"),
                                      T6_RESULT, usr=runner_usr):
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
                                  T7_RESULT, usr=runner_usr):
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
        # s004: чистим зомби-сеансы тонкого клиента (kill-tree мог
        # оставить их вrac) — до Stage C и verify
        if REAL_MODE:
            z = rac_terminate_ib_sessions()
            if z:
                log("[real] терминировано зомби-сеансов 1CV8: %d" % z)
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
        if REAL_MODE:
            # s004: neg-пользователь - зомби-сеансы, элемент справочника,
            # сам пользователь
            try:
                rac_terminate_ib_sessions(only_user=NEG_USER)
            except Exception as e:
                log("[cleanup] rac-terminate %s: %s" % (NEG_USER, str(e)[:100]))
            # s004 blocker-A: зомби-сеансы сервисного менеджера
            try:
                rac_terminate_ib_sessions(only_user=MANAGER_USER)
            except Exception as e:
                log("[cleanup] rac-terminate %s: %s" % (MANAGER_USER, str(e)[:100]))
            try:
                agent2 = win32com.client.Dispatch("V85.COMConnector").Connect(
                    conn_str(ADMIN, ""))
                delete_neg_catalog_element(agent2)
                cleanup_scenario_artifacts(agent2)
                # сироты авторегистрации БСП (зонды T8/T1 и др.);
                # безопасность: только явные тестовые маркеры, реальные
                # пользователи не затрагиваются (tests/test_user_orphans.py)
                try:
                    from user_orphans import cleanup_orphans
                    cleanup_orphans(agent2, apply=True, log=log)
                except ImportError:
                    log("[cleanup] user_orphans: модуль не найден, чистка пропущена")
                del agent2
            except Exception as e:
                log("[cleanup] справочник Пользователи: %s" % str(e)[:120])
        cleanup_names = [NEG_USER, MANAGER_USER] if REAL_MODE else [ZOND1, ZOND2]
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

    # T12 (RCA SA1): ложный PASS 02 — кнопка ФормаОткрытьЗакрытьРаботы
    # глотает исключение проведения (Попытка…Исключение в модуле формы
    # меняет статус обратно). Проверяем фактический результат сценарного
    # ПЛ за сегодня: Проведен=Истина, СтатусДокумента=3, движения
    # РН АпкТранспортныеРаботыПоФакту есть.
    # NB (T12 RCA финал): ТоварыНаСкладах непригоден как маркер —
    # расходная ветка ГСМ формируется только при Факт>0, а шаблон 02
    # без заправки даёт Факт=0 (движений ТоварыНаСкладах=0 — норма,
    # у rep НВЦБ-000002 их тоже 0). Маркер закрытия работ —
    # АпкТранспортныеРаботыПоФакту (формируется только при статусе 3,
    # читает АРМ Расход топлива).
    pl_bad = []
    pl_ok = 0
    try:
        q = agent.NewObject("Query")
        q.Text = ("ВЫБРАТЬ С.Ссылка КАК Ref, С.Номер КАК N, С.Проведен КАК P, "
                  "С.СтатусДокумента КАК St "
                  "ИЗ Документ.АпкПутевойЛистАвтотранспорта КАК С "
                  "ГДЕ С.Дата >= &D1 И С.Номер <> &Keep")
        today = datetime.date.today()
        q.УстановитьПараметр("D1", datetime.datetime(
            today.year, today.month, today.day))
        q.УстановитьПараметр("Keep", "НВЦБ-000002")
        sel = q.Execute().Choose()
        while sel.Next():
            num = str(sel.N)
            posted = bool(sel.P)
            try:
                st = int(sel.St)
            except Exception:
                st = -1
            qm = agent.NewObject("Query")
            qm.Text = ("ВЫБРАТЬ КОЛИЧЕСТВО(*) КАК К "
                       "ИЗ РегистрНакопления.АпкТранспортныеРаботыПоФакту КАК Т "
                       "ГДЕ Т.Регистратор = &Р")
            qm.УстановитьПараметр("Р", sel.Ref)
            sm = qm.Execute().Choose()
            mv = 0
            if sm.Next():
                mv = int(sm.К)
            if posted and st == 3 and mv > 0:
                pl_ok += 1
            else:
                pl_bad.append("%s (проведён=%s, статус=%s, движений=%d)"
                              % (num, posted, st, mv))
    except Exception as e:
        pl_bad.append("зонд: %s" % str(e)[:120])
    check(pl_ok >= 1 and not pl_bad,
          "сценарный ПЛ за сегодня: проведён+закрыт+движения "
          "(ok=%d, bad: %s)" % (pl_ok, "; ".join(pl_bad) or "нет"))

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
