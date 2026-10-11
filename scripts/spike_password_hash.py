# -*- coding: utf-8 -*-
"""Spike: сохранение/восстановление хэша пароля пользователя ИБ (платформа 8.5).

Механизм: ПользовательИнформационнойБазы.СохраняемоеЗначениеПароля (чтение+запись,
админ) + ТипАлгоритмаХешированияПароля. Проверяем на ВРЕМЕННОМ пользователе
(создаём и удаляем), реальных пользователей базы не трогаем.

Шаги:
 1. cleanup: удалить АпкСценТест_Зонд, если остался с прошлого прогона
 2. создать пользователя с паролем P1
 3. прочитать хэш H1 (+ тип алгоритма, дату установки)
 4. сменить пароль на P2, прочитать хэш H2 (ожидаем H2 != H1)
 5. восстановить: СохраняемоеЗначениеПароля = H1, записать; прочитать хэш
 6. верификация: COM-подключение под пользователем с P1 (ожидаем успех),
    с P2 (ожидаем отказ)
 7. cleanup: удалить пользователя

Результат: docs/spike-password-hash.md
"""
import io
import os
import sys
import traceback

import win32com.client

BASE = "localhost"
REF = "dev_erpapk_demo"
ADMIN_USR = "Администратор (ОрловАВ)"
ADMIN_PWD = ""

TEMP_USER = "АпкСценТест_Зонд"
P1 = "ApkSct-P1-2026!z"
P2 = "ApkSct-P2-2026!z"

OUT_MD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "docs", "spike-password-hash.md")
log_lines = []


def log(msg):
    print(msg)
    log_lines.append(msg)


def conn_str(usr, pwd):
    return "Srvr='%s';Ref='%s';Usr='%s';Pwd='%s';" % (BASE, REF, usr, pwd)


def get_users(agent):
    return agent.ПользователиИнформационнойБазы


def find_user(users, name):
    for u in users.ПолучитьПользователей():
        if u.Имя == name:
            return u
    return None


def user_snapshot(u):
    return {
        "Имя": u.Имя,
        "ПарольУстановлен": u.ПарольУстановлен,
        "СохраняемоеЗначениеПароля": u.СохраняемоеЗначениеПароля,
        "ТипАлгоритмаХешированияПароля": str(u.ТипАлгоритмаХешированияПароля),
        "ДатаУстановкиПароля": str(u.ДатаУстановкиПароля),
        "АутентификацияСтандартная": u.АутентификацияСтандартная,
    }


def fmt(snap):
    h = snap["СохраняемоеЗначениеПароля"]
    h_short = (h[:24] + "...len=%d" % len(h)) if h else "<пусто>"
    return ("ПарольУстановлен=%s, хэш=%s, алго=%s, дата=%s" %
            (snap["ПарольУстановлен"], h_short,
             snap["ТипАлгоритмаХешированияПароля"], snap["ДатаУстановкиПароля"]))


def try_connect(usr, pwd):
    """Возвращает (ok, err_text). ok=True если COM-подключение удалось."""
    try:
        win32com.client.Dispatch("V85.COMConnector").Connect(conn_str(usr, pwd))
        return True, ""
    except Exception as e:
        return False, str(e)[:300]


def auth_accepted(usr, pwd):
    """Пароль принят? Различаем: аутентификация пройдена (сессия не нужна) vs
    неверный пароль. Пользователь без права внешнего соединения всё равно
    проходит аутентификацию — платформа отвечает «Внешнее соединение не
    разрешено...», а не «Неверно указан пользователь или пароль»."""
    ok, err = try_connect(usr, pwd)
    if ok:
        return True, "подключение удалось"
    if "Неверн" in err or "Неверно" in err:
        return False, err
    return True, "аутентификация пройдена (%s)" % err


def main():
    results = []
    agent = win32com.client.Dispatch("V85.COMConnector").Connect(
        conn_str(ADMIN_USR, ADMIN_PWD))
    log("[com] admin connected")
    users = get_users(agent)

    # 1. cleanup
    old = find_user(users, TEMP_USER)
    if old is not None:
        old.Удалить()
        log("[1] старый %s удалён" % TEMP_USER)
    else:
        log("[1] остатков прошлого прогона нет")

    # 2. create with P1
    u = users.СоздатьПользователя()
    u.Имя = TEMP_USER
    u.ПолноеИмя = "Зонд спайка APKScenTest (удаляется автоматически)"
    u.Пароль = P1
    u.Записать()
    log("[2] пользователь создан с паролем P1")

    # 3. read H1
    u1 = find_user(users, TEMP_USER)
    s1 = user_snapshot(u1)
    log("[3] срез после P1: " + fmt(s1))
    results.append(("read H1", s1["СохраняемоеЗначениеПароля"] != ""))

    # 4. change to P2
    u1.Пароль = P2
    u1.Записать()
    u2 = find_user(users, TEMP_USER)
    s2 = user_snapshot(u2)
    log("[4] срез после P2: " + fmt(s2))
    results.append(("H2 != H1", s2["СохраняемоеЗначениеПароля"] != s1["СохраняемоеЗначениеПароля"]))

    # 5. restore H1
    u2.СохраняемоеЗначениеПароля = s1["СохраняемоеЗначениеПароля"]
    u2.Записать()
    u3 = find_user(users, TEMP_USER)
    s3 = user_snapshot(u3)
    log("[5] срез после восстановления: " + fmt(s3))
    results.append(("hash restored == H1",
                    s3["СохраняемоеЗначениеПароля"] == s1["СохраняемоеЗначениеПароля"]))

    # 6. verify auth: P1 accepted, P2 rejected
    ok1, err1 = auth_accepted(TEMP_USER, P1)
    log("[6a] auth P1: принят=%s %s" % (ok1, err1))
    ok2, err2 = auth_accepted(TEMP_USER, P2)
    log("[6b] auth P2: принят=%s %s" % (ok2, err2))
    results.append(("login P1 accepted", ok1))
    results.append(("login P2 rejected", not ok2))

    # 7. cleanup
    u4 = find_user(users, TEMP_USER)
    if u4 is not None:
        u4.Удалить()
    gone = find_user(users, TEMP_USER) is None
    log("[7] cleanup: пользователь удалён=%s" % gone)
    results.append(("cleanup", gone))

    verdict = all(v for _, v in results)
    log("VERDICT: %s" % ("PASS" if verdict else "FAIL"))

    # markdown report
    md = ["# Спайк: хэш пароля пользователя ИБ (8.5, чистый 1С)", "",
          "Механизм: `СохраняемоеЗначениеПароля` (чтение+запись, админ) +",
          "`ТипАлгоритмаХешированияПароля`. Проверка на временном пользователе",
          "`%s` (создан и удалён скриптом). База: %s\\%s." % (TEMP_USER, BASE, REF), "",
          "| Шаг | Результат |", "|---|---|"]
    for name, v in results:
        md.append("| %s | %s |" % (name, "OK" if v else "FAIL"))
    md += ["", "## Лог", "", "```"] + log_lines + ["```", "",
           "Вывод: восстановление хэша `СохраняемоеЗначениеПароля` %s."
           % ("работает — пароль аутентично восстанавливается" if verdict
              else "НЕ работает — см. лог")]
    with io.open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    return 0 if verdict else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        log("VERDICT: FAIL (exception)")
        sys.exit(2)
