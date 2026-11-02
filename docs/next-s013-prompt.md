# S013 — план следующей сессии

Контекст: `docs/night-report-2026-11-03-s012.md` (s012: restore → E2E
`s012-e2e1` PASS 45/0/neg-1, регрессий 0, COM-чек в эталоне; web-проба —
БЛОКЕР «нет публикации dev_erpapk_demo»). Три reproducibility-итерации
подряд зелёные (s010-e2e1, s011-e2e1, s012-e2e1), baseline 45/46
актуален. Git: `origin/main` @ `cbef514` (s008–s012-промт); не
закоммичены только docs сессии s012 (отчёт + этот файл) — ждут
подтверждения пользователя.

## T0. Стартовое состояние (проверить перед всем)

1. Диск C: — в s012 свободно 71 ГБ (пользователь почистил
   `AppData/Local/1C`). При <15 ГБ НИКАКИХ restore (PG-temp на
   эксклюзиве съедает 15–20 ГБ).
2. rac — только явный `RAC_ADDR=127.0.0.1:1545` (не откатывать;
   localhost в s012 снова резолвится, но единообразие важнее).
3. ИБ `dev_erpapk_demo`, UUID `cd6af3f6-9740-4d96-97bc-5c5f3a454bec`
   (НЕ старый 4d9168e8). COM `t8_gate.conn_str(t.ADMIN, "")` — отвечает.
4. Сеансы: `t8_gate.rac_terminate_ib_sessions()` → 0. Особенность s012:
   после restore при `jobs_deny=False` возрождаются `DefUser
   (BackgroundJob)` — для чистого поля терминировать все app-id и/или
   держать `jobs_deny=True` на время прогона (в s012 так и сделано,
   вердикт не пострадал).

## T1. Web-режим (главная тема s013 — если пользователь разблокировал)

Блокер s012: публикации `dev_erpapk_demo` нет. Пользователю при
публикации: (1) ws-модуль от своей платформы
(`C:\Program Files\1cv8\8.5.4.1683\bin\wsap24.dll` — в конфиге
`c:\apache` сейчас `8.3.27`; с ним 8.5-база не поднимется);
(2) порт: `Listen 9094` в конфиге vs `WEB_URL_DEFAULT=9093` в
`regress_run.py` — сверить и зафиксировать фактический URL.

Если публикация появилась:

1. Проверить URL (curl → страница 1С, не 404).
2. В РУЧНОЙ копии настроек прогона (не `tmp/t8/preprocessor-settings.json`
   основной!) выставить `clientType=Web` + `webUrl` (фактический URL).
3. Один короткий батч (neg-сценарий) через конвейер — проверить, что VA
   поднимает web-клиент и раннер собирает вердикт. Ожидание:
   эксперимент, фейлы по среде нормальны — задокументировать.
4. История ошибок: 19.10 web-попытка падала «Не получилось подключить
   TestClient … Тип клиента=Web, PID=0» (connect-таймаут) —
   `tests/run-20261019-103742/allure/*`; при повторе смотреть сюда.
5. Лимит: 3 итерации макс (2-attempt rule на каждый фейл).

Если публикации всё ещё нет — НЕ публиковать самостоятельно, отметить
в отчёте и перейти к T2.

## T2. Решение по BackgroundJob-сессиям (нужен выбор пользователя)

- (а) Оставить практику s012: `jobs_deny=True` на время E2E-прогонов
  (фоновые задания базы не мешают; вердикт подтверждён — 45/46).
- (б) Добавить `BackgroundJob` в `exclude_app_ids` префлайта
  `t8_gate.py` (REAL_MODE) — фоновые сессии не блокируют запуск.
Выбор пользователя → внести правку (по циклу: правка → `mcp__bsl_ls`
для BSL, для .py — `ast.parse`/прогон → документация).

## T3. (Опционально) Четвёртая контрольная итерация

Если T1/T2 закрыты и время есть: стандартный контроль restore → E2E
`s013-e2e1` (см. Restore-протокол), ожидание PASS 45/0/neg-1, 0
регрессий. При PASS — baseline не менять.

## T4. Финал сессии

Heartbeat `tmp/s013/heartbeat.txt` (новый), отчёт
`docs/night-report-<дата>-s013.md`, этот файл →
`docs/next-s014-prompt.md`. Commit+push — ТОЛЬКО после явного
подтверждения пользователя (ночью НЕ коммитить).

## Restore-протокол (уроки s009–s012 — НЕ нарушать)

1. `regress_run.rac_jobs_deny_set(True)` — обязателен до restore.
2. Терминация ВСЕХ сеансов (включая `BackgroundJob`):
   `t8_gate.rac_terminate_ib_sessions(app_ids=("BackgroundJob","1CV8",…))`
   → перепроверить `rac 127.0.0.1:1545 session list --cluster=…`;
   зомби добивать `session terminate --session=<uuid>`.
3. Verify: 0 сеансов (кроме RAS), 0 клиентских процессов 1cv8.
4. `nohup python scripts/s005_restore_ib.py > tmp/<sess>/restore.out
   2>&1 &` — **ТОЛЬКО detached, НИКОГДА foreground** (инцидент s010).
   ~13 мин штатно; при >40 мин — скриншоты (`scripts/s010_shot.py`),
   модалки закрывать штатно (UIA/ENTER), процесс НЕ убивать.
   ВО ВРЕМЯ RESTORE — НИКАКИХ rac/COM-запросов.
5. После exit 0: `rac_jobs_deny_set(False)` → `s005_make_neguser.py` →
   term → VA. Перед КАЖДЫМ VA-запуском: 0 сеансов (см. T0.4 про
   BackgroundJob).
6. E2E-запуск: `nohup python scripts/s005_va_run.py
   tests/features/s006/t6-e2e.feature <имя> 7200 &`; вердикт — в конце
   `tmp/s012|s013/va_run.out` (`[verdict] PASS/FAIL`), детали —
   `tmp/s005/va/<имя>/va_run.log` + `va_1c.log`; счётчики —
   `tests/run-*/summary.json` (totals) + `s005_cmp_runs.py` vs
   `tests/baseline/baseline-real.json`.

## Жёсткие правила (без изменений)

- Кириллица в bash-аргументах мангалится: русские тексты через
  write-tool / `-F <file>`; python — `sys.stdout.reconfigure
  (encoding='utf-8')`; проверять байты, не отображение.
- Правки BSL → `mcp__bsl_ls` bsl_analyze (0 Error) →
  `build_preprocessor.py` / `build_runner.py` → `build_dist.py`;
  без длинного тире U+2014 в коде.
- 2-attempt rule: один и тот же фейл дважды → стоп, классифицировать.
- Деструктив (kill процессов 1С, удаление вне tmp, commit, push,
  публикация web) — только с явного подтверждения пользователя.
- Мусор-файлы в корне репо не создавать; временные — только tmp/.

## Ключевые пути и константы

- ИБ: `dev_erpapk_demo`, сервер `localhost` (COM/клиент — localhost),
  rac — `127.0.0.1:1545`.
- Кластер `67cdef87-7bfc-4dae-b8e4-3ea9f8529156`, infobase
  `cd6af3f6-9740-4d96-97bc-5c5f3a454bec`.
- rac-синтаксис 8.5: `rac 127.0.0.1:1545 <mode> <subcmd>
  --cluster=<uuid>`; список ИБ — `infobase summary list`.
- COM: `win32com.client.Dispatch("V85.COMConnector").Connect(
  t.conn_str(t.ADMIN, ""))`; ВнешниеОбработки.Создать(Путь, Ложь).
- Архив restore: `tmp/regress/20261028-062041/pre-update.dt` (1.7 ГБ,
  НЕ удалять).
- Apache: служба `Apache2.4` (`c:\apache`, Listen 9094, публикации
  `/neirodoc`, `/erpuh`) — остановлена; служба `Apache`
  (AppData/Roaming/Apache24, 443) — стоковая, без 1С.
- Зонды: `s009_com_check.py`, `s010_com_filter_probe.py`,
  `s010_shot.py`, `s009_click_modal.py`.
- Baseline: `tests/baseline/baseline-real.json` (45/46,
  run-20261102-034905); контуры: `tests/test-selection.json` (all-true).
- Отчёты: `docs/night-report-2026-11-02-s009/s010/s011.md`,
  `docs/night-report-2026-11-03-s012.md`; промты: `docs/next-s009…
  s012-prompt.md`.
