# S012 — план следующей ночной сессии

Контекст: `docs/night-report-2026-11-02-s011.md` (s011: база
восстановлена пользователем вручную, rac пропатчен под новый UUID,
контрольный E2E `s011-e2e1` PASS 45/0/neg-1). **Всё до s011
закоммичено и запушено: `origin/main` @ `4b15d50`** (s007+s008-s011
+ docs). Комплект в стабильном зелёном состоянии: два контрольных
E2E подряд (s010-e2e1, s011-e2e1) PASS, регрессий 0, baseline 45/46
актуален.

## Т0. Стартовое состояние (проверить перед всем)

1. Диск C: — было 98%/14 ГБ. Если пользователь почистил
   `AppData/Local/1C` (19 ГБ кэшей — его решение) — свободно должно
   быть ≥20 ГБ. При <15 ГБ НИКАКИХ restore (PG-temp на эксклюзиве
   transiently съедает 15–20 ГБ → разрыв соединения посреди
   загрузки).
2. hosts: если пользователь вернул строку `127.0.0.1 localhost` —
   rac заработает без адреса; скрипты уже используют явный
   `RAC_ADDR=127.0.0.1:1545` (t8_gate.py, regress_run.py) — это
   работает в обоих случаях, НЕ откатывать.
3. Состояние базы: `rac 127.0.0.1:1545 infobase summary list
   --cluster=...` — ИБ `dev_erpapk_demo`, UUID
   `cd6af3f6-9740-4d96-97bc-5c5f3a454bec` (НЕ старый 4d9168e8!).
   COM-коннект `t8_gate.t.conn_str(t.ADMIN, "")` — отвечает.
4. Сеансы: `t8_gate.rac_terminate_ib_sessions()` → 0.

## T1. Регресс: restore → E2E `s012-e2e1`

Стандартный контроль третьей reproducibility-итерации после
ручного restore:

1. Restore-протокол (см. ниже, ЖЁСТКО) → designer exit 0.
2. `rac_jobs_deny_set(False)` → `s005_make_neguser.py` → term.
3. `nohup python scripts/s005_va_run.py
   tests/features/s006/t6-e2e.feature s012-e2e1 7200 &`
   → ожидание: PASS, 45 passed/0 failed/neg-1, регрессий 0 vs
   baseline, ~20 мин. Конвейер самодостаточен (патчи и arm-NN-
   цепочка в dist).
4. COM-чек цепочки: `python scripts/s009_com_check.py` → 5 ПБЗ
   ноября (НВЦБ-000003 непроведён — известное), 5 ВыработкаСотрудников
   проведены, ровно 5 партий code=1 по ПБЗ ноября.
5. При PASS: ничего в baseline не менять (эталон актуален).

Если E2E фейлит — НЕ чинить молча: залогировать, диагностировать
(va_1c.log, allure, COM), фиксить по обычному циклу
(bsl-ls → build → dist → перезапуск), каждое изменение в heartbeat.

## T2. (Опционально, если T1 зелёный и время есть) Web-режим прогона

В `preprocessor-settings.json` есть непроверенный путь
`clientType=Web` + `webUrl` (публикация базы). Задача-зонд:

1. Статус публикации: скилл `web-info` (Apache: запущен? база
   опубликована?).
2. Если опубликована: в РУЧНОЙ копии настроек прогона выставить
   `clientType=Web` + `webUrl`, прогнать ОДИН короткий батч
   (например neg-сценарий) — проверить, что VA поднимает web-клиент
   и раннер собирает вердикт. Ожидание: эксперимент, возможны фейлы
   по среде — это нормально, задокументировать.
3. Если публикации нет — НЕ публиковать самостоятельно (нужен
   пользователь), записать как блокер в отчёт.

Лимит на T2: 3 итерации макс (2-attempt rule на каждый фейл).

## T3. Финал сессии

Heartbeat `tmp/s011/heartbeat.txt` (продолжать общий лог) или
`tmp/s012/heartbeat.txt` (новый), отчёт
`docs/night-report-<дата>-s012.md`, этот файл →
`docs/next-s013-prompt.md`. Commit+push — ТОЛЬКО после явного
подтверждения пользователя (в ночном режиме: НЕ коммитить, спросить
утром).

## Restore-протокол (уроки s009/s010 — НЕ нарушать)

1. `regress_run.rac_jobs_deny_set(True)` — возврат True обязателен
   (False → повторять; бесконечно → стоп и разбираться).
2. Терминация ВСЕХ сеансов по UUID: `t8_gate
   .rac_terminate_ib_sessions()` → перепроверить `rac 127.0.0.1:1545
   session list --cluster=...`; зомби/RAS-фантомы добивать вручную
   `session terminate --session=<uuid>`.
3. Verify: 0 сеансов, 0 процессов 1cv8 (кроме серверных
   ragent/rphost/1cv8s/ras).
4. `nohup python scripts/s005_restore_ib.py > tmp/<sess>/restore.out
   2>&1 &` — **ТОЛЬКО detached, НИКОГДА foreground** (инцидент
   s010: таймаут bash убил Designer посреди RestoreIB → «ИБ
   разрушена», пересоздание вручную). ~20 мин; при >40 мин —
   скриншот окон (`scripts/s010_shot.py <hwnd> <png>`), модалки
   закрывать штатно (UIA/ENTER), процесс НЕ убивать.
   ВО ВРЕМЯ RESTORE — НИКАКИХ rac/COM-запросов.
5. После exit 0: `rac_jobs_deny_set(False)` → neguser → term → VA.
6. Перед КАЖДЫМ VA-запуском: `rac_terminate_ib_sessions()`.

## Жёсткие правила (без изменений)

- Кириллица в bash-аргументах мангалится: русские тексты через
  write-tool / `-F <file>`; python — `sys.stdout.reconfigure
  (encoding='utf-8')`; проверять байты, не отображение.
- Правки BSL → `mcp__bsl_ls` bsl_analyze (0 Error) →
  `build_preprocessor.py` / `build_runner.py` → `build_dist.py`;
  без длинного тире U+2014 в коде.
- E2E-вердикт читается в конце лаунчер-лога (`[verdict] PASS/FAIL`),
  детали — `tmp/s005/va/<build>/va_run.log` + `va_1c.log`.
- 2-attempt rule: один и тот же фейл дважды → стоп, классифицировать,
   не ретраить вслепую.
- Деструктив (kill процессов 1С, удаление файлов вне tmp, commit,
  push, публикация web) — только с явного подтверждения
  пользователя; ночью — не делать, спросить утром.
- Мусор-файлы в корне репо не создавать; временные — только tmp/.

## Ключевые пути и константы

- ИБ: `dev_erpapk_demo`, сервер `localhost` (1C-клиент/COM
  работают и с localhost — через IPv6; rac — только
  `127.0.0.1:1545`).
- Кластер `67cdef87-7bfc-4dae-b8e4-3ea9f8529156`,
  infobase `cd6af3f6-9740-4d96-97bc-5c5f3a454bec`.
- rac-синтаксис 8.5: `rac 127.0.0.1:1545 <mode> <subcmd>
  --cluster=<uuid>`; список ИБ — `infobase summary list` (НЕ
  `summary-list`).
- COM: `win32com.client.Dispatch("V85.COMConnector").Connect(
  t.conn_str(t.ADMIN, ""))`; ВнешниеОбработки.Создать(Путь, Ложь)
  (иначе безопасный режим режет Новый Файл).
- Архив restore: `tmp/regress/20261028-062041/pre-update.dt`
  (1.7 ГБ, НЕ удалять; dt-дубли в tmp/regress чистить можно).
- Зонды: `s010_com_filter_probe.py` (контур-фильтр),
  `s009_com_check.py` (ПБЗ/выработка/партии), `s010_shot.py`
  (скриншоты окон), `s009_click_modal.py` (UIA-клик модалки).
- Baseline: `tests/baseline/baseline-real.json` (45/46, run-20261102-
  034905); выбор контуров: `tests/test-selection.json` (all-true).
- Отчёты-история: `docs/night-report-2026-11-02-s009/s010/s011.md`;
  промты: `docs/next-s009/s010/s011-prompt.md`.
