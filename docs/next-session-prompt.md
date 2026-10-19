# Промт для новой сессии: спека 003 — остатки (T7/T8/TD-007) и ретро

## Кто ты и где

Пи-агент, проект `c:/MyProjects/APKScenTest` (1С:ERP+АПК 2.5, Vanessa
Automation, репо GitHub, MCP `v8std`). База: `localhost\dev_erpapk_demo`.
Платформа: `C:\Program Files\1cv8\8.5.4.1683\bin` (1cv8c / 1cv8).
VA EPF: `C:\MyProjects\APKTechPlan\tests\vanessa\vanessa-automation-single.epf`.
Исходники конфигурации: `C:/MyProjects/APKModSrc/`.

## Текущее состояние

- Спеки 001 (препроцессинг) и 002 (сценарии растениеводства) — complete.
- **Спека 003 «Регресс-конвейер» — T1–T6 ЗАКРЫТЫ** (2026-10-19):
  - `python scripts/regress_run.py --rehearsal [--set-baseline]` и
    `--update <cf|dt>` — обе команды доказаны E2E (5/5, rollback OK,
    regressions=0; детали `docs/night-report-2026-10-19.md`,
    `tmp/regress/EVIDENCE-T5.md`).
  - baseline релиза 1 в git: `tests/baseline/baseline.json`
    (run-20261019-053203).
  - Runbook: `docs/runbook.md`.
- Остатки спеки 003: **T7 (веб-клиент — после GUI-вопроса), T8 (ретро
  релиза 2 — с пользователем), TD-007 (--baseline-dt — решение пользователя)**.

## Первые команды новой сессии

1. Прочитать `docs/night-report-2026-10-19.md` (полный отчёт) и этот файл.
2. Спросить пользователя три вопроса (это и есть остатки):
   - **TD-007**: принимать ли `--baseline-dt <file>` (design.md §13)?
     Green-дамп: `tmp/regress/20261019-052456/pre-update.dt`. Если «да» —
     задача T9: флаг в `regress_run.py` (dump → restore baseline-dt →
     gate → rollback к dump), прогон, runbook.
   - **T7**: «Сессия интерактивная? (Apache-публикация требует видимый
     десктоп)» — если да: web-publish `dev_erpapk_demo`, флаг
     `--web-client` (ТипКлиента в VAParams), rehearsal веб-клиентом;
     если headless — фиксация deferred в design.md и tasks.md, T7 закрыт.
   - **T8**: ретро релиза 2 — кандидаты в `docs/night-report-2026-10-19.md`;
     итог записать в `.ai/sdd/PLAN.md`.
3. После закрытия T7/T8 (+TD-007) — `sdd-review` спеки 003 → review.md,
   INDEX → implementation:done → review:done.

## Ключевые факты (не переоткрывать)

- **Деградация демо-базы**: баки ТС расходуются прогонами (−31,5 л/прогон,
  МТЗ-82-79). Симптом исчерпания: 01-pl-tractor падает на «жду Номер»,
  на форме «Обнаружен отрицательный остаток топлива» (БЕЗ модалки).
  Fix-рецепт: заправочная ведомость 700 л **датой ранее дня прогона**
  (образец: НВЦБ-000004 от 18.10; форма читает остаток на начало дня).
- Диагностика UI-падений: probe-прогон одиночной фичи
  (`tmp/regress/probe/probe_pl_run.py`, VAParams со
  `ДелатьСкриншотПриВозникновенииОшибки`+VanessaExt) → OCR
  (`tmp/regress/probe/ocr1.ps1`, PNG→RGB предварительно; скилл img-ocr
  нестабилен, WinRT транзиентен — повторить).
- COM 8.5: метаданные через `ПустаяСсылка().Метаданные()` (у менеджера
  метода нет); журнал регистрации из COM недоступен; ТЧ перебор —
  `Выгрузить()`/`Получить(i)` (enumeration не работает).
- rac: `--cluster=67cdef87-7bfc-4dae-b8e4-3ea9f8529156` (cluster-id
  обязателен); ras поднят ad-hoc, службы RAS нет.
- Кириллица через bash-transport портится интермиттентно — писать файлы
  write-tool'ом, проверять байты.
- Тайминги: dump ~4 мин (1734MB), RestoreIB ~13–14 мин, gate 14 мин
  (5/5), полный rehearsal ≈33 мин, с update ≈46 мин; NFR-001 (E2E ≤40)
  выполняется с запасом.
- Утверждённые решения спеки 003: D-004…D-008 (requirements.md),
  TD-001…TD-006 (design.md); гейт t8_gate.py НЕ менялся.

## Дисциплина (как раньше)

1. `.ai/sdd/INDEX.md` + heartbeat `tmp/t9/heartbeat.txt` после шага.
2. Коммит с информативным сообщением per шаг.
3. `docs/night-report-<date>.md` по завершении крупного этапа.
4. Верификация (команды/диффы/evidence) перед claim complete.
5. 2-attempt stop; кириллица — write-tool; перед GUI-операциями — вопрос.
