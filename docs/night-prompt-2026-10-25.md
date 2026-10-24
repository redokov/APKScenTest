# Ночной промт: сессия 25.10.2026 (T11) — baseline-закрытие

Контекст: `docs/night-report-2026-10-23.md` (итоги 23–24.10: E2E PASS
в run10f, три корня закрыты, baseline остался). Факты: `tmp/s004/facts-e2e-runs.md`
(пп. 19–31). Пульс: `tmp/t9/heartbeat.txt`.

## Цель

1. Установить baseline: зелёный прогон `--set-baseline`
   (все фиксы уже в HEAD 5cf9869, пересборка НЕ нужна — EPF актуальны).
2. Если снова флейк arm-fuel-expense — см. «Флейки» ниже; не менять
   ничего кроме периода ожидания.
3. После зелёного baseline: NFR-001 — сравнение длительностей
   (regress-summary.json: dump/gate/rollback по прогонам в tmp/regress/).
4. Отчёт дополнить (night-report-2026-10-23.md — секция «Baseline») +
   commit + heartbeat-финал.
5. Диск: откатить/удалить DT-архивы прогонов после зелёного baseline
   (pre-update.dt по ~1.7GB в tmp/regress/*/).

## Порядок запуска (точно как 24.10)

1. **cont-after-reset**: взводить заново на СТАРТЕ сессии
   (предыдущий взвод истёк 24.10 18:40) — скилл unattended-night-run,
   repeat 8.
2. Проверка базы ДО прогона (COM, 5 мин): deny off/off, авторы
   pwdSet=False, guard-каталог `tests/pwd-guard/` пуст, сеансов ИБ нет
   (11 сессий BackgroundJob = штатные, не трогать).
3. Запуск фоном из utf-8 py-файла (шаблон `tmp/t10/run10g_launch.py`):
   `python scripts/regress_run.py --rehearsal --real-authors
   --gate-timeout 7200 --set-baseline`.
   Тайминги: preflight 30с, dump ~200с, gate ~900с (Stage A ~5 мин,
   Stage B ~15 мин), rollback ~860с. Итого ~35 мин.
4. Мониторинг САМ (tail логов tmp/regress/<ts>/gate-console.log):
   контрольные точки — «роли АпкСценТест_Менеджер в порядке (5)»,
   «батч 1 … ok», «negativePassed»: 1, VERDICT.

## Инструменты (проверены 24.10)

- COM-зонд: `V85.COMConnector`, `Srvr='localhost';Ref='dev_erpapk_demo';
  Usr='Администратор (ОрловАВ)';Pwd='';` — примеры tmp/t10/bisect3.py,
  tmp/t10/cleanup_bisect.py.
- RAC: `"C:/Program Files/1cv8/8.5.4.1683/bin/rac.exe"` (НЕ в PATH),
  вывод cp866 → `iconv -f cp866 -t utf-8`. Кластер
  `67cdef87-7bfc-4dae-b8e4-3ea9f8529156`, ИБ `4d9168e8-f640-490f-bbe6-32b1df12991f`.
- Сборка EPF при правках: `python scripts/build_t6_runner.py` (раннер,
  исходник tmp/t6/runner_src — теперь в git) и `python scripts/build_t6.py`
  (target, src/ → build/). После правок BSL — bsl-ls (MCP) ДО загрузки.
- OCR скриншотов: `C:/MyProjects/PiPack/skills/core/img-ocr/scripts/ocr.ps1`
  (модель изображения не читает).

## Ограничения (все пережиты 23–24.10 — не нарушать)

1. **1c-destructive-ops-guard**: не убивать 1cv8 в эксклюзиве; таймаут
   ≠ смерть; Designer всегда с /DisableStartupDialogs
   /DisableStartupMessages; rollback ~860с — это норма, не трогать.
2. **Во время живого E2E** — никаких зондов/COM/субагентов по базе
   (rac session list пассивно — можно). Мониторинг = tail логов.
3. **НЕ запускать 1cv8 без /Execute** (rc=1 без окон, факт 25) и без
   полных параметров; НЕ заниматься CLI-интроспекцией запусками 1cv8.
4. **НЕ запускать АпкРаннер.epf вне гейта**, пока жив `tmp/t6/runner_task.json`
   (инцидент 24.10 02:00 — подмена пароля автора; при диагностике
   вне гейта — сначала mv runner_task.json в .quarantine).
5. **Guard-протокол**: FAIL → guard-файл остаётся → РУЧНОЙ разбор →
   снятие только по завершённому разбору. Это защита, не баг.
6. **sessions-deny НЕ включается** в prepare_exclusive (9b95fd6);
   защита = jobs-deny + terminate-до-0.
7. Кириллица в bash/powershell — только через utf-8 py-файлы
   (`sys.stdout.reconfigure(encoding="utf-8")`), не инлайн.
8. Отчёты/факты/пульс: tmp/s004/facts-e2e-runs.md, tmp/t9/heartbeat.txt.

## Флейки (если повторятся)

- **arm-fuel-expense «Таблица <СписокСостояния> не найдена»**: ожидание
  уже Пауза 20 (5cf9869). Если упадёт снова — шаблон по автору
  «НЕ РАБОЧИЙ» (фикстуры статус 2, диагностика tmp/t9/arm-rashod/):
  вариант исключить шаблон из манифеста (coverage-map.json / manifest
  builder в target ObjectModule), зафиксировать решение в фактах.
- **TestClient rs=2 (недетерминирован)**: гейт сам ретраит попытку 2.
- **Stale guard после FAIL**: разобрать (tail gate-console.log,
  allure, va-логи), затем `rm tests/pwd-guard/*.active.json`.

## Стоп-условия

- 2 неудачи одного типа подряд → стоп, классифицировать
  (bash-diagnose-fail), зафиксировать, готовить стоп-поинт.
- База должна остаться чистой: deny off, авторы pwdSet=False, guard
  пуст, рабочий git-режим — всё закоммичено.
