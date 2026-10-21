# Промт для новой сессии: спека 004 — T10 E2E (последний rac-рубеж → зелёный прогон)

> Вставь этот файл целиком в первую реплику новой сессии pi.
> Запуск: `pi --model wormsoft/zai/glm-5.3:NVFP4` (рабочая папка
> `c:/MyProjects/APKScenTest`). Это надстройка над историей: сначала
> коротко — ГЛАВНОЕ, затем контекст.

## Кто ты и где

Пи-агент, проект `c:/MyProjects/APKScenTest` (1С:ERP+АПК 2.5, Vanessa
Automation, GitHub, MCP `bsl-ls`, `v8std`). База:
`localhost\dev_erpapk_demo` (PostgreSQL, админ `Администратор (ОрловАВ)`
без пароля). Платформа: `C:\Program Files\1cv8\8.5.4.1683\bin`.
Сессия интерактивная (GUI доступен). Лицензия: тонких клиентов
неограниченно, веб — 1 место (не совмещать с тонким клиентом).

## СТАРТ: сделай сразу (5 минут)

1. Взведи cont-after-reset (скил `unattended-night-run`):
   `python C:/Tools/pi-billing-window/scripts/arm_cont_after_reset.py
   "$PI_SESSION_FILE" --repeat 8 --ttl 24`, затем `--check`.
2. Прочитай `tmp/s004/facts-e2e-runs.md` (хвост «Ночь 21.10») —
   полная история прогонов и фиксов ночи.
3. Проверь: `ls tests/pwd-guard/` (должно быть пусто), rac-сеансы на
   нашей ИБ = 0 (кроме RAS), процессов 1cv8 нет.

## Текущее состояние (после ночи 20→21.10)

База ЧИСТАЯ: откачена к пре-run-состоянию, пароли авторов не тронуты
(pwdSet=false у всех), временных пользователей нет, guard пуст,
зомби-сеансы сняты, ras запущен (`ras cluster localhost:1540`,
DECTACHED_PROCESS — если умер, подними так же).

Сделано и закоммичено (git log с 71d5f93):
- **Блокер A (same-user hang)**: сервисный пользователь
  `АпкСценТест_Менеджер` для runner-сессий Stage A/B/C в real-режиме
  (71d5f93), роли расширены (d0c71ca): ПолныеПрава+
  АдминистраторСистемы+ИнтерактивноеОткрытиеВнешнихОтчетовИОбработок+
  ЗапускТонкогоКлиента. БЕЗ пароля, БЕЗ элемента справочника.
- **Блокер B (neg БСП-блок)**: запись ИдентификаторПользователяИБ в
  режиме `ОбменДанными.Загрузка=Истина` + запрос-верификация (c3ac98d).
  Доказано: neg-клиент APP-STARTED (out_negprobe_diag7.txt).
- **Инфра-фиксы**: чистка сеансов ИБ перед дампом (9e33cca); CRLF-
  нормализация rac-парсеров в t8_gate+regress_run + исключение
  RAS-сеанса (2adeff9); terminate по UUID, не session-id (1114dec).
- **Stage A под менеджером ЗЕЛЁНЫЙ**: step=done, errors=0, 91с,
  11 фич/16 сценариев (tmp/s004/out_diagmgr.txt).

## ЕДИНСТВЕННЫЙ оставшийся фикс (до E2E)

**Rac-рубеж после Stage A в real-ветке t8_gate.py (main, ~строка 685).**
Лог run6: `[real] FAIL: онлайн-сеансы после Stage A: Администратор
(ОрловАВ) (COMConnection); АпкСценТест_Менеджер`.

Причина: рубеж требует 0 сеансов, но честный (после CRLF-фикса) парсер
видит: (а) COMConnection ОрловАВ — СОБСТВЕННЫЙ COM-агент гейта (живёт
от Connect до verify — это легитимно); (б) сеанс менеджера 1CV8 —
зомби kill_tree (rac_terminate_ib_sessions должен снимать; если в
списке умирающий сеанс с пустым app-id — не терминируется и висит).
До CRLF-фикса рубеж всегда ложно проходил (парсер-блок-коллапс).

Фикс (реализуй сам, правка ~10 строк):
- В real-ветке после `rac_terminate_ib_sessions()`: проверять
  отсутствие сеансов с app-id в {1CV8, BackgroundJob} (TestClient-
  авторские и фоновые), ИГНОРИРУЯ app-id=COMConnection (гейт) и
  app-id=RAS (служба), и пустой app-id (умирающие) — либо терминировать
  их отдельным проходом и только потом требовать 0.
- НЕ ослаблять префлайт-рубеж ДО Stage A (там 0 сеансов обязателен,
  COM-агент гейта создаётся после префлайта).
- Гейты: `python -c ast.parse` обоих скриптов; commit.

## Затем — план T10 (без изменений)

1. E2E: `python scripts/regress_run.py --rehearsal --real-authors
   --gate-timeout 7200` фоном из utf-8 файла (шаблон
   tmp/s004/run4_launch.py). Ожидание: 3 батча (2 автора + neg) зелёные.
   Запуск и мониторинг — САМ, без субагентов, без COM-зондов.
2. Зелёный → повторный прогон с `--set-baseline`
   (tests/baseline/baseline-real.json).
3. Краш-дрилл: kill t8_gate.py посреди Stage B → regress-finally
   rollback → guard остаётся → guard-recovery вручную (runbook §4) →
   в отчёт.
4. NFR-001: длительность real vs репетиция (regress-summary.json).
5. Отчёт `docs/night-report-2026-10-21.md` (образец 10-19): все
   попытки run4 (6 шт), фиксы, run-финал, open items.
6. Commit + heartbeat-финал.

## Модели (ТОЛЬКО wormsoft)

| Роль | Модель |
|---|---|
| Оркестратор (ты) | `wormsoft/zai/glm-5.3:NVFP4` (text-only! картинки — субагенту) |
| general-purpose / Explore / bsl-linter | `wormsoft/zai/glm-5.3-flash:NVFP4` (text+image) |

Fallback при 429: оркестратор → `wormsoft/zai/glm-5.3` (1M),
субагенты → `wormsoft/deepseek-ai/deepseek-v4-flash`. Фиксируй в
heartbeat. Код-правки по спеку — субагенту flash; сам — читаешь diff,
гейтишь (ast.parse), коммитишь. Поиск «где X» — сначала grep/bash сам,
потом Explore (≤200 слов).

## Инструменты и приёмы (проверено, не изобретай)

- **COM к базе**: только utf-8 .py-файл + `win32com`,
  `Usr='Администратор (ОрловАВ)'`. Inline-кириллица в bash/powershell/
  python -c — МАНГЛИТСЯ. Python datetime в параметр 1С не конвертируется
  (журнал регистрации не выгрузить — не трать время).
- **COM UUID** (УникальныйИдентификатор) нельзя str() — сравнение
  только через параметр запроса.
- **1cv8 клиент**: ENTERPRISE-запуск БЕЗ /Execute не работает («Не
  определен режим запуска», rc=1). Всегда /RunModeManagedApplication +
  /Execute. DESIGNER batch (/DumpIB, /RestoreIB) — ок, /Out пишется по
  завершении; пустой лог + rc=1 = модалка/блокировка (смотри окна).
- **rac/ras**: ras поднимается `ras cluster localhost:1540`
  (DETACHED_PROCESS из python). rac: `session list/terminate
  --cluster=67cdef87-7bfc-4dae-b8e4-3ea9f8529156` — terminate по
  UUID (поле `session`), вывод CRLF (нормализуй до сплита по \n\n);
  инфобазы: `rac infobase summary list --cluster=...`. Наш UUID
  c6a442bb-d7a9-4d8b-a274-37ea859b26c1. RAS-служебный сеанс (app-id
  RAS, появляется при scheduled-jobs-deny=on) — не терминировать и не
  считать блокирующим.
- **Окна/UIA**: EnumWindows-callback в PS — собирай в ArrayList
  ($out+= в делегате НЕ мутирует массив); скриншот: PS CopyFromScreen,
  путь без r''; распознавание — скил img-ocr
  (`powershell -File C:/MyProjects/PiPack/skills/core/img-ocr/scripts/
  ocr.ps1 <png>`), т.к. модель оркестратора text-only.
- **RestoreIB вручную**: шаблон tmp/s004/manual_restore4.py (utf-8,
  subprocess-список, timeout 3600). Мониторинг: окна (probe_restore_
  windows.py) + `netstat -an | grep 5432 | grep -c EST` (паттерн
  «5432.*EST», не наоборот). Факт: ручной restore ~920-1010с; regress-
  rollback падал по 3000с-таймауту ДВАЖДЫ (деградация — open item).
- **Диск**: C: критичен (99%). Дампы архивируются на D:
  (D:\apkscen-archive\dt-dumps, D: уже полон — новые места не искать
  там). Перед прогоном проверяй `df -h /` — нужно ≥5 ГБ (префлайт
  тоже проверит).

## Правила (не менять)

- Подмена паролей авторов ОБЯЗАТЕЛЬНА в каждом real-прогоне (решение
  пользователя). Пароли не трогать вне прогона.
- Замороженные механизмы спеки 001 (`ПодменитьПароль`) не трогать.
- E2E-прогоны — эксклюзивно main-агентом; во время E2E никаких
  COM-зондов и субагентов, задевающих базу.
- Кириллица в командах — только utf-8 файлами (write-tool/python).
- Гейты: BSL-правки → MCP `bsl-ls bsl_analyze` (0 errors); python →
  `ast.parse`; пересборка EPF → `scripts/build_t3.py`,
  `scripts/build_t6_runner.py`.
- Одна ошибка дважды → стоп, классифицируй (bash-diagnose-fail),
  третья попытка только с новым диагнозом.
- Никаких `-y/--yes` к деструктивным операциям вне мандата этого
  промта. RestoreIB/dump/терминация сеансов в рамках T10 — разрешены.
- Прогресс — сразу на диск: heartbeat `tmp/t9/heartbeat.txt` (строка
  каждые 2-5 мин), факты — `tmp/s004/facts-e2e-runs.md`. tmp/ в
  gitignore — facts НЕ коммитить, они переживают сессию на диске.
- «продолжи» от billing-window — норма: состояние бери с диска.
- Плановое самозавершение: всё готово (или упёрся в решение за
  пользователем) → итог, heartbeat, стоп.

## Open items (в отчёт)

- REAL_TEMPLATES allowlist: шаблоны 02/03/04/05 отложены до валидации
  по авторам (решение принято автономно — подтвердить у пользователя).
- Сироты автозарегистрации БСП в справочнике «Пользователи» — вычистить.
- Деградация rollback (3000с vs 920с ручного): chdbfl/vacuum после
  серий restore; возможно остаточный rollback в PG после kill.
- Ночные фоновые задания ERP спавнятся любым клиентом сессии базы —
  чистка сеансов перед эксклюзивами обязательна (уже в коде).
