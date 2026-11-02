# S014 — план следующей сессии

Контекст: `docs/night-report-2026-11-03-s012.md` +
`docs/night-report-2026-11-03-s013.md`. Четыре контрольных E2E подряд
зелёные (s010…s013, все 45/0/neg-1, регрессий 0), restore-протокол
стабилен (~13 мин). Reproducibility доказана — **дополнительные
restore→E2E итерации без изменений НЕ нужны** (бессмысленный расход
времени). Дальше — только разблокировки и решения пользователя.

Не закоммичено (ждёт подтверждения): `docs/night-report-2026-11-03-
s012.md`, `docs/night-report-2026-11-03-s013.md`, `docs/next-s013-
prompt.md`, `docs/next-s014-prompt.md`. Всё остальное — в git
(`cbef514`). Утренний вопрос: «Коммитить docs s012+s013+s014?»

## T1. Web-режим (блокер: нужна публикация от пользователя)

Требования к публикации `dev_erpapk_demo` (Apache2.4 `c:\apache`,
`Listen 9094`):

1. ws-модуль от платформы 8.5: `LoadModule _1cws_module
   "C:/Program Files/1cv8/8.5.4.1683/bin/wsap24.dll"` (сейчас в конфиге
   `8.3.27` — с ним 8.5-база не поднимется).
2. Alias + Directory + `SetHandler 1c-application` +
   `ManagedApplicationDescriptor` (по образцу `/neirodoc` в том же
   конфиге) → каталог `C:/Apache/publish/dev_erpapk_demo/default.vrd`.
3. Запустить службу `Apache2.4`. Сверить фактический порт: `Listen 9094`
   vs `WEB_URL_DEFAULT=9093` в `regress_run.py` — при расхождении
   поправить константу.

После публикации — зонд T2 из s012 (лимит 3 итерации):

1. curl-проверка URL (страница 1С, не 404).
2. РУЧНАЯ копия настроек прогона + `clientType=Web` + `webUrl`
   (фактический URL).
3. Один короткий батч (neg-сценарий) — VA должен поднять web-клиент,
   раннер собрать вердикт. История фейлов 19.10: TestClient Web,
   connect-таймаут, PID=0 (`tests/run-20261019-103742/allure/*`).
4. Эксперимент; фейлы по среде документировать, не чинить вслепую.

Если публикации нет — фиксировать в отчёте, ничего не публиковать.

## T2. Решение по BackgroundJob-сессиям (нужен выбор пользователя)

- (а) `jobs_deny=True` на время прогонов — практика s012/s013,
  вердикт подтверждён дважды. Текущий де-факто вариант.
- (б) Правка `t8_gate.py`: `BackgroundJob` в `exclude_app_ids`
  префлайта (REAL_MODE) — фоновые сессии не блокируют запуск.
Выбор → правка (для .py — `ast.parse` + прогон), документация.

## T3. (Только если были изменения кода/данных)

Единичный контроль restore → E2E `s014-e2e1` по протоколу ниже.
Ожидание PASS 45/0/neg-1, 0 регрессий; baseline менять только при
ЯВНОМ изменении состава сценариев (с подтверждения пользователя).

## T4. Финал сессии

Heartbeat `tmp/s014/heartbeat.txt`, отчёт
`docs/night-report-<дата>-s014.md`, этот файл →
`docs/next-s015-prompt.md`. Commit+push — ТОЛЬКО после явного
подтверждения пользователя (ночью НЕ коммитить).

## Restore-протокол (уроки s009–s013 — НЕ нарушать)

1. `regress_run.rac_jobs_deny_set(True)` до restore.
2. Терминация ВСЕХ сеансов: `t8_gate.rac_terminate_ib_sessions
   (app_ids=("BackgroundJob","1CV8",…))`. Зомби-записи фоновых сессий
   могут не терминироваться (rc=4294967295) и исчезают сами за ~1 мин —
   НЕ убивать процессы, дождаться исчезновения.
3. Verify: 0 не-RAS сеансов, 0 клиентских процессов 1cv8.
4. `nohup python scripts/s005_restore_ib.py > tmp/<sess>/restore.out
   2>&1 &` — **ТОЛЬКО detached, НИКОГДА foreground** (инцидент s010).
   ~13 мин; при >40 мин — скриншоты (`scripts/s010_shot.py`), модалки
   закрывать штатно, процесс НЕ убивать. ВО ВРЕМЯ RESTORE — никаких
   rac/COM.
5. После exit 0: `jobs_deny(False)` → `s005_make_neguser.py` →
   чистое поле (`jobs_deny(True)` + term, урок s012) → VA.
6. E2E: `nohup python scripts/s005_va_run.py
   tests/features/s006/t6-e2e.feature <имя> 7200 &`; вердикт —
   `[verdict]` в `tmp/<sess>/va_run.out`; счётчики —
   `tests/run-*/summary.json`; регрессии — `s005_cmp_runs.py` vs
   `tests/baseline/baseline-real.json`.
7. После прогона: `jobs_deny(False)` (нормальное состояние ИБ).

## Жёсткие правила (без изменений)

- Кириллица в bash-аргументах мангалится: русские тексты через
  write-tool / `-F <file>`; python — `sys.stdout.reconfigure
  (encoding='utf-8')`; проверять байты, не отображение.
- Правки BSL → `mcp__bsl_ls` bsl_analyze (0 Error) →
  `build_preprocessor.py` / `build_runner.py` → `build_dist.py`;
  без U+2014 в коде.
- 2-attempt rule: один и тот же фейл дважды → стоп, классифицировать.
- Деструктив (kill 1С, удаление вне tmp, commit, push, публикация) —
  только с явного подтверждения пользователя.
- Мусор-файлы в корне репо не создавать; временные — только tmp/.

## Ключевые пути и константы

- ИБ `dev_erpapk_demo`, `localhost` (COM/клиент), rac —
  `127.0.0.1:1545`. Кластер `67cdef87-7bfc-4dae-b8e4-3ea9f8529156`,
  infobase `cd6af3f6-9740-4d96-97bc-5c5f3a454bec`.
- COM: `win32com.client.Dispatch("V85.COMConnector").Connect(
  t.conn_str(t.ADMIN, ""))`; ВнешниеОбработки.Создать(Путь, Ложь).
- Архив restore: `tmp/regress/20261028-062041/pre-update.dt` (1.7 ГБ,
  НЕ удалять).
- Apache: `Apache2.4` (`c:\apache`, Listen 9094, есть `/neirodoc`,
  `/erpuh`, модуль ws от 8.3.27) — остановлена; `Apache`
  (AppData/Roaming/Apache24, 443) — стоковая, без 1С.
- Зонды: `s009_com_check.py`, `s010_com_filter_probe.py`,
  `s010_shot.py`, `s009_click_modal.py`.
- Baseline: `tests/baseline/baseline-real.json` (45/46,
  run-20261102-034905); контуры: `tests/test-selection.json`.
- Отчёты: `docs/night-report-2026-11-02-s011.md`,
  `docs/night-report-2026-11-03-s012.md`,
  `docs/night-report-2026-11-03-s013.md`; промты `docs/next-s011…
  s013-prompt.md`.
