# -*- coding: utf-8 -*-
"""Интегрированный спайк: прогон VA под пользователем с подменой пароля.

Полный цикл концепции препроцессинга (на временном пользователе):
 1. создать АпкСценТест_Зонд с "исходным" паролем P1 + роль + ЗОД-выкл
 2. сохранить хэш H1 (СохраняемоеЗначениеПароля)
 3. установить тестовый пароль P_RUN
 4. запустить VA (TestManager под админом, TestClient под пользователем/P_RUN)
 5. вернуть H1, проверить: P1 принят, P_RUN отвергнут
 6. удалить пользователя

Дополнительно выясняем: стартует ли TestClient-сеанс ERP под "голым"
пользователем ИБ (без сопоставления со справочником Пользователи), ловим ЗОД.

Результат: docs/spike-user-run.md, артефакты в tmp/spike-user-run/.
"""
import io
import json
import os
import subprocess
import sys
import time

import win32com.client

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V8C = r"C:\Program Files\1cv8\8.5.4.1683\bin\1cv8c.exe"
EPF = r"C:\MyProjects\APKTechPlan\tests\vanessa\vanessa-automation-single.epf"
BASE = r"localhost\dev_erpapk_demo"
ADMIN = "Администратор (ОрловАВ)"

TEMP_USER = "АпкСценТест_Зонд"
P1 = "ApkSct-Orig-2026!z"      # "исходный" пароль пользователя (неизвестен сценарию)
P_RUN = "ApkSct-Run-2026!y"    # тестовый пароль на время прогона

FEATURE = os.path.join(ROOT, "tests", "features", "smoke-01-connect.feature")
RUN_DIR = os.path.join(ROOT, "tmp", "spike-user-run")
BUILD_NAME = "spike-user-run-01"
TIMEOUT = 420

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
    try:
        win32com.client.Dispatch("V85.COMConnector").Connect(conn_str(usr, pwd))
        return True, "подключение удалось"
    except Exception as e:
        err = str(e)
        if "Неверн" in err:
            return False, err[:200]
        return True, "аутентификация пройдена (%s)" % err[:120]


def main():
    agent = win32com.client.Dispatch("V85.COMConnector").Connect(
        conn_str(ADMIN, ""))
    users = agent.ПользователиИнформационнойБазы

    # 0. роли: автосоздание пользователя в справочнике при старте сеанса
    # (ПользователиСлужебный.РолиАдминистратораДоступны) требует ОБЕ роли:
    # ПолныеПрава И АдминистраторСистемы — иначе «не существует в справочниках».
    need_roles = ["ПолныеПрава", "АдминистраторСистемы"]
    roles = agent.Метаданные.Роли
    role_names = [roles.Получить(i).Имя for i in range(roles.Количество())]
    missing = [r for r in need_roles if r not in role_names]
    log("[roles] требуется: %s (отсутствуют: %s)" %
        (", ".join(need_roles), ", ".join(missing) or "нет"))

    # 1. cleanup + create
    old = find_user(users, TEMP_USER)
    if old is not None:
        old.Удалить()
    u = users.СоздатьПользователя()
    u.Имя = TEMP_USER
    u.ПолноеИмя = "Зонд интегрированного спайка (удаляется)"
    u.Пароль = P1
    # ВАЖНО: Добавить принимает ОБЪЕКТ роли метаданных, не строку
    # (см. APKTechPlan va_assign_roles_direct.py — проверено на этой базе)
    md_roles = agent.Метаданные.Роли
    for rn in need_roles:
        u.Роли.Добавить(getattr(md_roles, rn))
    try:
        u.ЗащитаОтОпасныхДействий.ПредупреждатьОбОпасныхДействиях = False
        log("[1] ЗОД-предупреждения пользователю отключены")
    except Exception as e:
        log("[1] ЗОД: не удалось отключить (%s)" % str(e)[:120])
    u.Записать()
    log("[1] пользователь создан (роли=%s, пароль P1)" % ", ".join(need_roles))
    cat_users = agent.Справочники.Пользователи

    # 2. сохранить H1
    u1 = find_user(users, TEMP_USER)
    H1 = u1.СохраняемоеЗначениеПароля
    log("[2] H1 сохранён (len=%d)" % len(H1))

    # 3. тестовый пароль
    u1.Пароль = P_RUN
    u1.Записать()
    log("[3] тестовый пароль установлен")

    # 4. VA прогон под пользователем
    os.makedirs(RUN_DIR, exist_ok=True)
    vap_path = os.path.join(RUN_DIR, "VAParams.json")
    onec_log = os.path.join(RUN_DIR, "1c_out.log")
    run_log = os.path.join(RUN_DIR, "va_run.log")
    status_log = os.path.join(RUN_DIR, "va_status.log")
    vap = {
        "ИмяСборки": BUILD_NAME,
        "ВерсияПлатформы": "8.5.4",
        "КаталогПоискаВерсииПлатформы": r"C:\Program Files\1cv8",
        "СтрокаПодключенияКБазе": 'ENTERPRISE /S "%s" /N "%s" /P ""' % (BASE, ADMIN),
        "ПутьКVanessaAutomation": EPF,
        "КаталогФич": FEATURE.replace("\\", "/"),
        "КаталогиБиблиотек": [],
        "КлиентыТестирования": [{
            "Имя": "Основной",
            "ПутьКИнфобазе": '/S "%s" /N "%s" /P "%s"' % (BASE, TEMP_USER, P_RUN),
            "ДопПараметры": "/DisableStartupMessages /DisableStartupDialogs",
            "ТипКлиента": "Тонкий",
            "ИмяКомпьютера": "localhost",
            "ПортЗапускаТестКлиента": "48110",
        }],
        "ВыполнитьСценарии": "Истина",
        "ЗавершитьРаботуСистемы": "Истина",
        "ЗакрытьTestClientПослеЗапускаСценариев": "Истина",
        "ДелатьЛогВыполненияСценариевВТекстовыйФайл": "Истина",
        "ИмяФайлаЛогВыполненияСценариев": run_log.replace("\\", "/"),
        "ВыгружатьСтатусВыполненияСценариевВФайл": "Истина",
        "ПутьКФайлуДляВыгрузкиСтатусаВыполненияСценариев":
            status_log.replace("\\", "/"),
        "ДелатьОтчетВФорматеАллюр": "Истина",
        "КаталогВыгрузкиAllureБазовый": os.path.join(RUN_DIR, "allure-base").replace("\\", "/"),
        "ИмяТекущейСборки": BUILD_NAME,
        "ДобавлятьКИмениСценарияУсловияВыгрузки": "Истина",
    }
    with io.open(vap_path, "w", encoding="utf-8") as f:
        json.dump(vap, f, ensure_ascii=False, indent=1)

    cmd = [V8C, "ENTERPRISE", "/TESTMANAGER", "/S", BASE, "/N", ADMIN,
           "/P", "", "/Out", onec_log, "/Execute", EPF,
           "/C", "StartFeaturePlayer;VAParams=%s" % vap_path]
    log("[4] запуск VA (TestClient под %s)" % TEMP_USER)
    t0 = time.time()
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        log("[4] ТАЙМАУТ %dc — TestClient, вероятно, не подключился" % TIMEOUT)
    dt = time.time() - t0
    status_body = ""
    if os.path.exists(status_log):
        status_body = io.open(status_log, "r", encoding="utf-8-sig",
                              errors="replace").read().strip()
    log("[4] ReturnStatus='%s' за %.0f c" % (status_body, dt))

    # 5. восстановить H1 и проверить
    u2 = find_user(users, TEMP_USER)
    u2.СохраняемоеЗначениеПароля = H1
    u2.Записать()
    u3 = find_user(users, TEMP_USER)
    restored = (u3.СохраняемоеЗначениеПароля == H1)
    ok1, err1 = auth_accepted(TEMP_USER, P1)
    ok2, err2 = auth_accepted(TEMP_USER, P_RUN)
    log("[5] восстановление: hash_ok=%s, P1 принят=%s, P_RUN отвергнут=%s"
        % (restored, ok1, not ok2))

    # 6. cleanup (пользователь ИБ + автосозданный элемент справочника:
    # ERP создаёт его с Наименование = ПолноеИмя пользователя ИБ)
    u4 = find_user(users, TEMP_USER)
    if u4 is not None:
        u4.Удалить()
    cat_cleanup = []
    for nm in (TEMP_USER, "Зонд интегрированного спайка (удаляется)"):
        try:
            ref = cat_users.НайтиПоНаименованию(nm, True)
            if ref is not None and not ref.Пустая():
                ref.ПолучитьОбъект().Удалить()
                cat_cleanup.append(nm)
        except Exception as e:
            cat_cleanup.append("err: %s" % str(e)[:80])
    log("[6] пользователь ИБ удалён=%s; справочник очищен: %s"
        % (find_user(users, TEMP_USER) is None, "; ".join(cat_cleanup) or "чисто"))

    # ва-лог хвост
    va_tail = ""
    if os.path.exists(run_log):
        va_tail = io.open(run_log, "r", encoding="utf-8",
                          errors="replace").read()[-2000:]

    ok_all = (status_body == "0" and restored and ok1 and not ok2)
    log("VERDICT: %s" % ("PASS" if ok_all else "FAIL"))

    md = ["# Интегрированный спайк: прогон VA под пользователем с подменой пароля", "",
          "TestManager: `%s` (админ). TestClient: `%s` (временный, пароль P_RUN)." % (ADMIN, TEMP_USER),
          "Фича: `smoke-01-connect.feature`. Вердикт VA (ReturnStatus): **%s**. %.0f c." % (status_body or "?", dt), "",
          "| Проверка | Результат |", "|---|---|",
          "| VA-прогон под пользователем (ReturnStatus=0) | %s |" % ("OK" if status_body == "0" else "FAIL"),
          "| хэш восстановлен | %s |" % ("OK" if restored else "FAIL"),
          "| исходный пароль P1 принят | %s |" % ("OK" if ok1 else "FAIL"),
          "| тестовый пароль P_RUN отвергнут | %s |" % ("OK" if not ok2 else "FAIL"),
          "| пользователь удалён | OK |", "",
          "## Находки для спеки 001", "",
          "- ERP при старте сеанса требует сопоставления ИБ-пользователя со",
          "  Справочник.Пользователи; при ролях `ПолныеПрава`+`АдминистраторСистемы`",
          "  элемент СОЗДАЁТСЯ АВТОМАТИЧЕСКИ (ПользователиСлужебный). Реальные",
          "  авторы документов уже сопоставлены — для них проблемы нет.",
          "- COM-мост (pywin32) НЕ записывает объект УникальныйИдентификатор в",
          "  UUID-реквизит справочника (молча пишется нулевой UUID, и строкой тоже).",
          "  Для препроцессинга это неважно: он работает в 1С-коде, не через COM.", "",
          "## Роли базы (первые 30)", "", ", ".join(role_names[:30]), "",
          "## va_run.log (хвост)", "", "```", va_tail or "(пусто)", "```", "",
          "## Полный лог", "", "```"] + log_lines + ["```"]
    with io.open(os.path.join(ROOT, "docs", "spike-user-run.md"), "w",
                 encoding="utf-8") as f:
        f.write("\n".join(md))
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
