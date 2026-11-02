# S011 — план следующей ночной сессии

Контекст: `docs/night-report-2026-11-02-s010.md` (s010: T1 JSON-выбор +
ревизия s009, T2 baseline 45/46 через форму, T3 контрольный E2E
`s010-e2e1` PASS 45/0/neg-1). **Состояние базы на момент передачи:
пересоздана пользователем после инцидента s010 (см. ниже), архив ЕЩЁ НЕ
загружен** — пользователь загружает вручную.

## ⚠️ Инцидент s010 (не повторять)

Проверка SyntaxWarning случайно запустила `s005_restore_ib.py` в
foreground; bash-таймаут убил процессное дерево вместе с Designer
посреди RestoreIB → «Информационная база разрушена» (второй раз за
проект; первый — 23.10.2026). Правила:
- restore-скрипт — ТОЛЬКО detached (`nohup ... &`), никогда foreground;
- проверять синтаксис — `ast.parse`, не запуск файла;
- НИКОГДА не убивать 1cv8.exe, пока restore не завершился (exit в
  `tmp/s010/restore*.out`); мониторинг — tasklist + размер PG-data,
- если restore >40 мин — скриншот окон (`scripts/s010_shot.py <hwnd>
  <png>` + OCR), модалки закрывать штатно (UIA/ENTER).

## T0. Проверить восстановленную базу (после ручной загрузки архива)

Архив: `tmp/regress/20261028-062041/pre-update.dt` (1.7 ГБ, источник
всех restore). Пользователь грузит сам. Проверка после:
1. rac: `"<rac>" 127.0.0.1:1545 session list --cluster=<id>` — 0 сеансов;
2. COM: `t8_gate.t.conn_str(t.ADMIN, "")` → запрос
   `КОЛИЧЕСТВО(*) ИЗ Документ.ПроизводствоБезЗаказа` — отвечает;
3. jobs-deny off (по протоколу ниже).

## T1. Починить резолв localhost / перейти на 127.0.0.1

После пересоздания базы rac/1cv8 перестали резолвить `localhost`
(«No such host is known»; rac работает только с явным
`127.0.0.1:1545`). Либо починить hosts
(`C:\Windows\System32\drivers\etc\hosts`: строка `127.0.0.1 localhost`),
либо заменить адрес в:
- `scripts/regress_run.py`, `scripts/t8_gate.py` — rac-вызовы
  (добавить префикс адреса `127.0.0.1:1545` ПЕРВОМ аргументом:
  `rac 127.0.0.1:1545 infobase summary-list --cluster=...`
  — синтаксис 8.5: адрес первым позиционным, `infobase list`
  НЕ существует, только `summary-list`!);
- `scripts/s005_restore_ib.py` — `/S localhost\...` → `/S 127.0.0.1\...`.
Проверить: `rac 127.0.0.1:1545 cluster list` → кластер
`67cdef87-7bfc-4dae-b8e4-3ea9f8529156`.

## T2. Commit s008+s009+s010 (только после ЯВНОГО подтверждения!)

Состав — `docs/next-s010-prompt.md` §T4, плюс s010:
- `scripts/s010_com_filter_probe.py`, `scripts/s010_shot.py`,
  `scripts/s005_restore_ib.py` (raw-string фикс),
  `scripts/s009_com_check.py` (багфикс COM-выборки);
- `tests/features/s010/*.feature` (t1-json-diag, t1-flag-trace,
  t2-baseline-fix), ревизия `tests/features/s009/t3-contour-filter.feature`;
- `tests/baseline/baseline-real.json` (новый, 45/46);
- отчёты `docs/night-report-2026-11-02-s010.md`, `next-s011-prompt.md`.
НЕ коммитить: `20261101000000` (388 МБ eventlog-мусор в корне — удалить),
run-каталоги `tests/run-*` (решение пользователя), tmp/.

## T3. Диск C: (96%, 20 ГБ свободно — критично для restore/E2E)

- Удалить `20261101000000` (388 МБ, eventlog-дамп, untracked);
- `AppData/Local/1C` — 19 ГБ (кэши/логи клиентов) — только с
  разрешения пользователя, кэши пересоздаются;
- следить: при restore PG-temp transiently съедает ~15–20 ГБ.

## T4. Мелочи

- `s009_com_check.py`: запрос партий `ПЕРВЫЕ 10` без отбора по дате
  ловит посторонние НВ00-партии — добавить отбор по ПБЗ ноября
  (см. фикс-запрос в heartbeat [07:3x], рабочая версия уже опробована
  в сессии: 5 партий по ПБЗ НВЦБ-000003..000007);
- ПБЗ НВЦБ-000003 создаётся НЕпроведённым сценарием «Загрузка
  удобрений» — известное поведение, не регрессия (партия создаётся,
  выработка проводится).

## Restore-протокол (без изменений, проверен s010: exit 0 с 1-го раза)

1. `regress_run.rac_jobs_deny_set(True)` — возврат True обязателен
   (после пересоздания базы rac-вызовы могут падать — тогда адрес
   127.0.0.1:1545, см. T1; если deny не ставится, а сеансов в базе
   физически быть не может (пустая база) — можно запускать).
2. Терминация сеансов по UUID (`t8_gate.rac_terminate_ib_sessions()`,
   перепроверить `session list`, зомби добивать `session terminate
   --session=<uuid>`).
3. Verify: 0 сеансов, 0 процессов 1cv8 (кроме серверных
   ragent/rphost/1cv8s/ras).
4. `nohup python scripts/s005_restore_ib.py > tmp/<s011>/restore.out
   2>&1 &` — ~20 мин. ВО ВРЕМЯ — НИКАКИХ rac/COM.
5. После exit 0: `rac_jobs_deny_set(False)` → `s005_make_neguser.py`
   → `rac_terminate_ib_sessions()` → VA.
6. Перед КАЖДЫМ VA-запуском: `rac_terminate_ib_sessions()`.

## Жёсткие правила (без изменений)

- Кириллица в bash-аргументах мангалится: русские тексты через
  write-tool; python — `reconfigure utf-8`.
- Правки BSL → bsl-ls (0 Error) → build_preprocessor/build_runner →
  build_dist; без длинного тире U+2014.
- E2E: `python scripts/s005_va_run.py tests/features/s006/t6-e2e.feature
  <build> 7200` (самодостаточен: скан → генерация → прогон → вердикт
  vs baseline; патчи и arm-NN-цепочка уже в dist).
- Деструктив/коммит — только с явного подтверждения пользователя.
- COM-константы: `scripts/t8_gate.py`; ИБ `dev_erpapk_demo`,
  кластер `67cdef87-7bfc-4dae-b8e4-3ea9f8529156`,
  infobase-id уточнить после пересоздания (`rac 127.0.0.1:1545
  infobase summary-list --cluster=...`) — UUID мог измениться!
- Ключевые зонды: `s010_com_filter_probe.py` (контур-фильтр),
  `s009_com_check.py` (ПБЗ/выработка/партии ноября), `s010_shot.py`
  (скриншоты окон Designer).
