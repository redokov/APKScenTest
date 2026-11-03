# S015 — план следующей сессии

Контекст: `docs/night-report-2026-11-03-s014.md`. T2 (BackgroundJob)
закрыт — префлайт `t8_gate.py` исключает `BackgroundJob` (дефолт +
явный вызов; защита интерактивных `1CV8`-сеансов сохранена). `t8_gate.py`
прошёл `ast.parse` и unit-верификацию. Web — **блокер: нет публикации
dev_erpapk_demo**.

Не закоммичено: `docs/night-report-2026-11-03-s014.md`,
`docs/next-s015-prompt.md` (+ heartbeat `tmp/s014/`). Ждут
подтверждения пользователя.

## T1. Web-режим (блокер — нужна публикация от пользователя)

Требования к публикации `dev_erpapk_demo` (Apache2.4 `c:\apache`,
`Listen 9094`, модуль `_1cws_module`):

1. wsap24.dll **от платформы 8.5.4.1683** (сейчас в конфиге `8.3.27` —
   с ней 8.5-база не поднимется):
   `LoadModule _1cws_module "C:/Program Files/1cv8/8.5.4.1683/bin/wsap24.dll"`.
2. Alias + Directory + `SetHandler 1c-application` +
   `ManagedApplicationDescriptor "C:/Apache/publish/dev_erpapk_demo/default.vrd"`.
3. Запустить службу `Apache2.4`; сверить порт: `Listen 9094` vs
   `WEB_URL_DEFAULT=9093` в `regress_run.py` (и в настройках гейта).
4. `curl`-проверка: `http://localhost:9094/dev_erpapk_demo/ru` → страница
   1С, не 404.

Затем зонд (лимит 3 итерации):

1. РУЧНАЯ копия настроек прогона: `clientType=Web` + `webUrl` (фактический
   URL, например `http://localhost:9094/dev_erpapk_demo`).
2. Один короткий батч (neg-сценарий) → VA должен поднять web-клиент,
   раннер собрать вердикт.
3. История фейлов 19.10: TestClient Web, connect-таймаут, PID=0
   (`tests/run-20261019-103742/allure/*`).
4. Эксперимент; фейлы документировать, не чинить вслепую.

Если публикации нет — зафиксировать блокер в отчёте, ничего не публиковать.

## T2. Контрольный прогон (опционально)

Единичная восстановительная итерация restore → E2E `s015-e2e1` только
если есть изменения в 1С-комплекте (пока изменений в комплексе нет —
s014 поправил только dev-time-префлайт). Ожидание PASS 45/0/neg-1, 0
регрессий; baseline менять только с подтверждения пользователя.

## T3. Финал сессии

Heartbeat `tmp/s015/heartbeat.txt`, отчёт
`docs/night-report-<дата>-s015.md`, этот файл →
`docs/next-s016-prompt.md`. Commit+push — ТОЛЬКО после явного
подтверждения пользователя (ночью НЕ коммитить).

## Restore-протокол (уроки s009–s014 — НЕ нарушать)

1. `rac_jobs_deny_set(True)` до restore.
2. Терминация ВСЕХ сеансов: `t8_gate.rac_terminate_ib_sessions`.
   Зомби-записи BackgroundJob исчезают асинхронно ~1–12 мин — НЕ убивать
   процессы (урок 21.10), дождаться исчезновения.
3. Verify: 0 не-RAS/не-BackgroundJob сеансов (с s014 префлайт игнорирует
   BackgroundJob сам), 0 клиентских процессов 1cv8.
4. `nohup python scripts/s005_restore_ib.py > tmp/<sess>/restore.out
   2>&1 &` — **ТОЛЬКО detached, НИКОГДА foreground** (инцидент s010).
   ~13 мин; при >40 мин — скриншоты (`scripts/s010_shot.py`), модалки
   штатно, процесс НЕ убивать. ВО ВРЕМЯ RESTORE — никаких rac/COM.
5. После exit 0: `jobs_deny(False)` → `s005_make_neguser.py` → term → VA
   (поле под чисткой префлайта, `jobs_deny=False` — нормальное состояние).
6. E2E: `nohup python scripts/s005_va_run.py
   tests/features/s006/t6-e2e.feature <имя> 7200 &`; вердикт —
   `[verdict]` в `tmp/<sess>/va_run.out`; счётчики —
   `tests/run-*/summary.json`; регрессии — `s005_cmp_runs.py` vs
   `tests/baseline/baseline-real.json`.

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
- Apache: `Apache2.4` (`c:\apache`, `Listen 9094`, есть `/neirodoc`,
  `/erpuh`, `wsap24.dll` от 8.3.27) — остановлена; `Apache`
  (AppData/Roaming/Apache24, 443) — стоковая, без 1С.
- Зонды: `s009_com_check.py`, `s010_com_filter_probe.py`,
  `s010_shot.py`, `s009_click_modal.py`.
- Baseline: `tests/baseline/baseline-real.json` (46 ключей,
  run-20261102-034905); контуры: `tests/test-selection.json`.
- Отчёты: `docs/night-report-2026-11-03-s012.md`…`-s014.md`;
  промты `docs/next-s012…s014-prompt.md`.
