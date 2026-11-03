# -*- coding: utf-8 -*-
"""Тесты фильтра онлайн-сеансов (scripts/t8_gate.rac_sessions_online).

Ключевые гарантии (s014, решение 03.11.2026):
1. Фоновые сессии DefUser (BackgroundJob) НЕ блокируют префлайт -
   их нельзя убивать (урок 21.10: kill вешает старт клиента).
2. Интерактивные сессии 1CV8 под пользователями блокируют как раньше.
3. Рубеж post-Stage-A сохраняет свою семантику (COMConnection и
   пустой app-id исключены, BackgroundJob - нет: задание умирает само).
Запуск: python tests/test_rac_sessions_filter.py (без сети - rac
подменяется).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

import t8_gate

IB = t8_gate.RAC_INFOBASE

SYNTH = (
    "session : 111\r\ninfobase : " + IB + "\r\napp-id : BackgroundJob\r\n"
    "user-name : DefUser\r\n\r\n"
    "session : 222\r\ninfobase : " + IB + "\r\napp-id : 1CV8\r\n"
    "user-name : ИвановИИ\r\n\r\n"
    "session : 333\r\ninfobase : " + IB + "\r\napp-id : RAS\r\n"
    "user-name : \r\n\r\n"
    "session : 444\r\ninfobase : other-ib\r\napp-id : 1CV8\r\n"
    "user-name : ЧужойБазе\r\n\r\n"
    "session : 555\r\ninfobase : " + IB + "\r\napp-id : COMConnection\r\n"
    "user-name : Администратор (ОрловАВ)\r\n\r\n"
    "session : 666\r\ninfobase : " + IB + "\r\napp-id : \r\n"
    "user-name : \r\n"
)


class _FakeProc:
    def __init__(self, payload):
        self.stdout = payload.encode("cp866")


def _with_fake(payload, fn):
    """Выполнить fn с подменой subprocess внутри t8_gate (только на время)."""
    orig = t8_gate.subprocess
    class _Stub:
        @staticmethod
        def run(*args, **kwargs):
            return _FakeProc(payload)
    t8_gate.subprocess = _Stub
    try:
        return fn()
    finally:
        t8_gate.subprocess = orig


def test_preflight_ignores_background_job():
    # s014: новый дефолт - RAS + BackgroundJob не блокируют;
    # всё остальное (в т.ч. COMConnection, пустой app-id) - строго блокирует
    sessions, err = _with_fake(SYNTH, lambda: t8_gate.rac_sessions_online())
    assert err is None, "не должно быть ошибки rac: %r" % err
    assert sorted(sessions) == [
        " ()",
        "Администратор (ОрловАВ) (COMConnection)",
        "ИвановИИ (1CV8)",
    ], "префлайт: игнорируются только RAS+BackgroundJob: %r" % sessions
    print("OK: BackgroundJob+RAS игнорируются, прочие сессии блокируют")


def test_old_behavior_documented():
    # прежняя семантика ("только RAS") воспроизводима явным аргументом
    sessions, err = _with_fake(
        SYNTH, lambda: t8_gate.rac_sessions_online(exclude_app_ids=("RAS",)))
    assert err is None
    assert sorted(sessions) == [
        " ()",
        "DefUser (BackgroundJob)",
        "Администратор (ОрловАВ) (COMConnection)",
        "ИвановИИ (1CV8)",
    ], "явный exclude_app_ids=('RAS',) должен показывать BackgroundJob: %r" % sessions
    print("OK: старое поведение воспроизводимо явным аргументом")


def test_post_stage_a_boundary_semantics():
    # рубеж после Stage A: COMConnection и пустой app-id исключены,
    # BackgroundJob - НЕТ (дожидаемся естественного завершения, урок 21.10)
    sessions, err = _with_fake(
        SYNTH,
        lambda: t8_gate.rac_sessions_online(
            exclude_app_ids=("RAS", "COMConnection", "")))
    assert err is None
    assert sorted(sessions) == [
        "DefUser (BackgroundJob)",
        "ИвановИИ (1CV8)",
    ], "post-Stage-A рубеж изменил семантику: %r" % sessions
    print("OK: post-Stage-A рубеж несёт прежнюю семантику")


def test_crlf_normalization():
    # без CRLF-нормализации весь список разбирается как один блок
    payload = (
        "session : 1\r\ninfobase : " + IB + "\r\napp-id : 1CV8\r\n"
        "user-name : Первый\r\n\r\n"
        "session : 2\r\ninfobase : " + IB + "\r\napp-id : 1CV8\r\n"
        "user-name : Второй\r\n")
    sessions, err = _with_fake(
        payload,
        lambda: t8_gate.rac_sessions_online(exclude_app_ids=("RAS",)))
    assert err is None
    assert sessions == ["Первый (1CV8)", "Второй (1CV8)"], \
        "CRLF-блоки должны разбираться по отдельности: %r" % sessions
    print("OK: CRLF-нормализация разбирает блоки по отдельности")


def test_other_infobase_ignored():
    # чужая ИБ кластера не попадает в проверку
    payload = (
        "session : 9\r\ninfobase : other-ib\r\napp-id : 1CV8\r\n"
        "user-name : ЧужойБазе\r\n")
    sessions, err = _with_fake(
        payload,
        lambda: t8_gate.rac_sessions_online(exclude_app_ids=("RAS",)))
    assert err is None and sessions == [], \
        "чужая ИБ не должна попадать в отбор: %r" % sessions
    print("OK: сеансы чужой ИБ игнорируются")


def test_rac_error_reported():
    # недоступность rac - это ошибка (exit 2 у вызывающего), не пустой список
    orig = t8_gate.subprocess
    class _Broken:
        @staticmethod
        def run(*args, **kwargs):
            raise OSError("rac недоступен")
    t8_gate.subprocess = _Broken
    try:
        sessions, err = t8_gate.rac_sessions_online()
    finally:
        t8_gate.subprocess = orig
    assert sessions is None and err, \
        "ошибка rac должна возвращаться как err: %r / %r" % (sessions, err)
    print("OK: недоступность rac возвращается ошибкой")


if __name__ == "__main__":
    test_preflight_ignores_background_job()
    test_old_behavior_documented()
    test_post_stage_a_boundary_semantics()
    test_crlf_normalization()
    test_other_infobase_ignored()
    test_rac_error_reported()
    print("\nВСЕ ТЕСТЫ ПРОШЛИ: префлайт игнорирует BackgroundJob, "
          "интерактивные сессии блокируют как раньше")
