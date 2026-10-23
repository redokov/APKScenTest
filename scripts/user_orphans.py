# -*- coding: utf-8 -*-
"""Чистка сирот авторегистрации БСП в справочнике «Пользователи».

Сироты — элементы справочника «Пользователи», оставшиеся от тестовых
пользователей (зонды T8/T1, АпкСценТест_*, neg/менеджер s004) после
их удаления из пользователей ИБ. Их авторегистрирует БСП при входе.

БЕЗОПАСНОСТЬ (главное требование): чистка НЕ должна затрагивать
реальных пользователей базы. Отбор ведётся ТОЛЬКО по явным тестовым
маркерам в наименовании; никаких удалений по «мёртвой привязке» или
прочим косвенным признакам.

Использование:
    python scripts/user_orphans.py            # показать сирот (read-only)
    python scripts/user_orphans.py --apply    # удалить сирот

Тесты безопасности: tests/test_user_orphans.py (без базы, чистый python).
"""
import sys

# Явные маркеры тестовых записей. Пополнение списка = осознанное решение.
TEST_MARKERS = (
    "АпкСценТест",       # сервисные пользователи s004 (менеджер, neg, зонды)
    "Зонд T8",           # сироты авторегистрации зондов T8
    "Зонд T1",           # сирота зонда T1 (zTemp004_neg)
    "(удаляется)",       # пометка «удаляется» в полном имени
    "Негатив s004",      # neg-пользователь спеки 004
    "Менеджер раннеров s004",  # менеджер раннеров
)


def is_test_orphan(name, full_name=None):
    """True только для явно тестовой записи.

    name/full_name — строки (наименование элемента справочника и его
    полное имя). Пустые значения не признаются сиротами.
    """
    for val in (name, full_name):
        if not val:
            continue
        low = val.strip().lower()
        for marker in TEST_MARKERS:
            if marker.lower() in low:
                return True
    return False


def collect_orphans(items):
    """items: итерируемое пар (name, full_name) -> список сирот [(name, full_name)]."""
    return [(n, f) for (n, f) in items if is_test_orphan(n, f)]


def cleanup_orphans(agent, apply=False, log=print):
    """COM-режим: сканирует справочник Пользователи, удаляет сироты.

    Возвращает число найденных (и удалённых при apply=True) сирот.
    """
    q = agent.NewObject("Query")
    q.Text = ("ВЫБРАТЬ Пользователи.Ссылка, Пользователи.Наименование "
              "ИЗ Справочник.Пользователи КАК Пользователи")
    sel = q.Execute().Choose()
    found = 0
    deleted = 0
    while sel.Next():
        nm = sel.Наименование
        if not is_test_orphan(nm):
            continue
        found += 1
        if apply:
            sel.Ссылка.ПолучитьОбъект().Удалить()
            deleted += 1
            log("[orphans] удалена сирота: %s" % nm)
        else:
            log("[orphans] найдена сирота: %s (не удаляется, без --apply)" % nm)
    log("[orphans] сирот: %d, удалено: %d" % (found, deleted))
    return found


def main():
    apply = "--apply" in sys.argv
    sys.stdout.reconfigure(encoding="utf-8")
    import win32com.client
    conn = ("Srvr='localhost';Ref='dev_erpapk_demo';"
            "Usr='Администратор (ОрловАВ)';Pwd='';")
    agent = win32com.client.Dispatch("V85.COMConnector").Connect(conn)
    cleanup_orphans(agent, apply=apply)


if __name__ == "__main__":
    main()
