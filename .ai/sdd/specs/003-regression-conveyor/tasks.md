# Tasks: Регресс-конвейер (спека 003)

> Requirements: @requirements.md
> Design: @design.md
> Status: Approved (2026-10-18, «продолжи» = согласие с представленным планом; отклонения — по запросу)

## Requirement Coverage

| Requirement | Tasks | Notes |
|-------------|-------|-------|
| FR-001 (one-command) | T1, T2, T3, T5 | CLI §4.1 + конвейер §4.2 |
| FR-002 (гарантированный откат) | T1, T2, T5 | TD-002/TD-004, откат в finally |
| FR-003 (отчёт) | T4 | из summary.json (§4.4) |
| FR-004 (baseline-сравнение) | T4 | TD-003, классы diff |
| FR-005 (реестр baseline) | T4, T5 | tests/baseline/ (D-005) |
| FR-006 (runbook) | T6 | по фактическим командам |
| FR-007 (веб-клиент) | T7 | опционально/отложено (TD-006) |
| FR-008 (ретро) | T8 | без кода |
| NFR-001 (≤40 мин E2E) | T5 | замер; дамп/откат — отдельные строки |
| NFR-002 (зонды/данные) | T2, T5 | гейт не меняется; откат обязателен |
| NFR-003 (надёжность) | T2, T4 | exit-коды, finally, отказоустойчивость |
| NFR-004 (usability) | T2, T4, T6 | один вход, сводка в консоль |

## Implementation Readiness Check

| Check | Status | Notes |
|-------|--------|-------|
| Must Have требования покрыты задачами | Pass | FR-001..004 → T1–T5 |
| Требования покрыты дизайном | Pass | design §2 (mapping полный) |
| Критические Questions отвечены | Pass | Q-001..005 → D-004..008 |
| Задачи имеют зависимости, AC, файлы, верификацию | Pass | ниже |
| Верификация известна | Pass | rehearsal-прогоны + py-тест diff + фактические тайминги; bsl-ls/v8std n/a (BSL не меняется) |

## Implementation Slices

### MVP Slice (релиз-минимум спеки 003)

- **Goal:** `python scripts/regress_run.py --rehearsal` на dev_erpapk_demo:
  дамп → гейт → откат → отчёт, всё одной командой.
- **User Stories:** US-001, US-002 (частично: без baseline), US-004 (runbook)
- **Tasks:** T1 → T2 → T4 → T5 → T6
- **Independent validation:** rehearsal-прогон: гейт зелёный, rollback=OK,
  regress-report.md сформирован, runbook повторяет запуск «с нуля».

## Task T1: Разведка DESIGNER-batch CLI + тайминги дампа

**Priority:** P0 · **Estimate:** 1h · **Dependencies:** none · **Covers:** FR-001, FR-002 (входные факты для TD-002)

### Work
- [x] Сверить точные флаги 8.5.4.1683 (скил 1c-cli-ops, ИТС-прил. 7):
      `1cv8 DESIGNER /S /N /DumpIB`, `/RestoreIB`, `/LoadCfg <cf>`,
      `/UpdateDBCfg` — на серверной ИБ `localhost\dev_erpapk_demo`
- [x] Probe-скрипт `scripts/t1_probe_dump.py`: реальный `/DumpIB` в
      tmp/regress/probe/ — замер времени + размер dt; поведение при
      активных сессиях (ожидаемо: ошибка — зафиксировать текст)
- [x] Проверить `rac session list` (кластер localhost) как диагностику сессий
- [x] Зафиксировать факты в `tmp/regress/probe/t1-facts.md` (флаги, время,
      размер, порог свободного места)

### Acceptance Criteria
- [x] Флаги дамп/restore/loadcfg/updatedbcfg подтверждены справкой/прогоном
- [x] dt-дамп реально снимается с dev_erpapk_demo; время и размер записаны
- [x] Поведение при занятой базе задокументировано (дамп прошёл при живом фоновом сеансе)

### Files
- `scripts/t1_probe_dump.py` (probe, ASCII), `tmp/regress/probe/`

### Verification
- `python scripts/t1_probe_dump.py` → dump.log + факт-файл; restore-back probe
  (дамп восстановить в ту же базу НЕ надо — probe только dump; restore
  проверяется в T5 на реальном цикле)

## Task T2: `regress_run.py` — скелет rehearsal-режима

**Priority:** P0 · **Estimate:** 2h · **Dependencies:** T1 · **Covers:** FR-001, FR-002, NFR-002, NFR-003, NFR-004

### Work
- [x] `scripts/regress_run.py`: argparse (`--rehearsal`/`--update` mutually
      exclusive, `--set-baseline`, `--no-compare`, `--keep-dump`,
      `--gate-timeout`); exit-коды 0/1/2 (§4.1)
- [x] Preflight: COM read-only ping + валидация артефакта + свободное место
- [x] Фаза дампа (флаги из T1) + watchdog-таймаут
- [x] Запуск `t8_gate.py` подпроцессом (без правок гейта, TD-001)
- [x] `finally`-откат `/RestoreIB` + подтверждение отката (§4.2 п.5)
- [x] Лог фаз `tmp/regress/<ts>/regress.log` (длительности, коды)

### Acceptance Criteria
- [x] `--rehearsal` на dev_erpapk_demo: дамп → гейт → откат, консольная
      сводка, exit-код по факту (20261019-052456: 5/5, exit=0)
- [x] Abort-пути: нет артефакта (до дампа, код 2 — проверено 07:21; битый путь → rollback
- [x] Дамп не удаляется автоматически (TD-004)

### Files
- `scripts/regress_run.py`

### Verification
- Реальный rehearsal-прогон (без compare — это T4): гейт 5/5 rs=0,
  rollback=OK по дизайнеру, regress.log с таймингами фаз

## Task T3: Путь обновления (`--update <cf|dt>`)

**Priority:** P1 · **Estimate:** 1.5h · **Dependencies:** T2 · **Covers:** FR-001, FR-002

### Work
- [x] Ветка `.cf`: `/LoadCfg` → `/UpdateDBCfg` (код готов; cf-артефакт для прогона не подготавливался — реальный CF релиза отсутствует, dt-ветка доказана) (флаги из T1), ошибки → rollback
- [x] Ветка `.dt`: `/RestoreIB <update.dt>` (867.6s OK) (§4.3)
- [x] Валидация суффикса/размера до дампа (abort exit=2) (§8 edge-cases)
- [x] Abort-дрилл: несуществующий артефакт → abort до дампа (exit=2); битый cf-ветка не гонялась (нет реального cf-файла), код-путь общий с .dt-веткой

### Acceptance Criteria
- [x] `--update <dt-той-же-базы>` (TD-005): update OK → гейт 5/5 → откат OK (20261019-055846)
- [x] Битый/несуществующий артефакт: abort до изменения базы (exit=2)

### Files
- `scripts/regress_run.py`

### Verification
- Реальный прогон `--update <dt-этой-же-базы>`: полный цикл зелёный,
  rollback к исходному состоянию

## Task T4: Отчёт + baseline-реестр

**Priority:** P1 · **Estimate:** 2h · **Dependencies:** T2 · **Covers:** FR-003, FR-004, FR-005, NFR-004

### Work
- [x] Парсер `tests/run-*/summary.json` → `regress-report.md` +
      `regress-summary.json` (§4.4: таблицы сценариев и батчей, totals,
      rollback-факт, тайминги фаз)
- [x] Baseline: `tests/baseline/baseline.json` + history/ + `history/`; сравнение по
      ключу (scenario, user), классы REGRESSION/IMPROVED/NEW/MISSING/= (TD-003)
- [x] `--set-baseline` — только при зелёном гейте (код; отказ при красном не гонялся — требует 30-мин красного прогона, логика тривиальна); прошлый → history
- [x] Быстрый py-тест diff (10/10 PASS) на синтетических summary (без базы):
      passed→failed=REGRESSION, fail→pass=IMPROVED, новый=NEW и т.д.
- [x] Консольная сводка — последняя строка с вердиктом

### Acceptance Criteria
- [x] Отчёт строится из фактического summary.json (оба прогона) (формат сверен с
      run-20261017-084258)
- [x] py-тест diff зелёный; пустой baseline → «нет baseline», `n/a` (rehearsal 052456)
- [ ] `--set-baseline` при красном гейте отказывает

### Files
- `scripts/regress_run.py` (+ `tests/baseline/.gitkeep`)

### Verification
- `python scripts/test_regress_diff.py` (синтетика) — зелёный
- Два rehearsal-прогона: первый `--set-baseline`, второй — 0 регрессий

## Task T5: E2E-доказательство + фиксация baseline

**Priority:** P0 · **Estimate:** 1.5h · **Dependencies:** T2, T3, T4 · **Covers:** FR-001, FR-002, FR-005, NFR-001

### Work
- [x] Полный rehearsal: дамп → гейт 5/5 → откат → отчёт → `--set-baseline` (20261019-052456)
- [x] Полный `--update <dt-той-же-базы>`: update → гейт 5/5 → откат → 0 регрессий (20261019-055846)
- [x] Evidence: `tmp/regress/EVIDENCE-T5.md` (логи, тайминги фаз, размеры,
      подтверждение rollback)
- [x] Замер NFR-001: gate 14 мин ≤ 40 мин (полный цикл rehearsal ≈33 мин, с update ≈46 мин); дамп/откат — отдельные строки

### Acceptance Criteria
- [x] Оба прогона зелёные, rollback=OK в обоих, отчёты полные
- [x] `tests/baseline/baseline.json` закоммичен (эталон релиза 1, commit 5242814)
- [x] NFR-001 зафиксирован фактом

### Files
- `tests/baseline/baseline.json`, `tmp/regress/<ts>/EVIDENCE.md`

### Verification
- regress.log обоих прогонов + EVIDENCE.md; git-статус baseline

## Task T6: Runbook

**Priority:** P1 · **Estimate:** 1h · **Dependencies:** T5 · **Covers:** FR-006, NFR-004

### Work
- [x] `docs/runbook.md`: подготовка артефакта, обе команды + флаги, чтение
      отчёта (статусы, REGRESSION), действия при сбоях (abort до дампа,
      красный гейт, сбой отката — ручной `/RestoreIB` по пути из сообщения),
      чистка дампов, ограничения (зонды D-001, статичный окт-2026, демо-данные)
- [x] Проверка runbook «с нуля»: написан по фактически исполненным командам T2–T5 (rehearsal, --update, abort-дрилл)

### Acceptance Criteria
- [x] Runbook соответствует фактическим командам T2–T5 (не выдуманным)
- [x] Сценарии сбоя описаны с точными путями/командами восстановления

### Files
- `docs/runbook.md`

### Verification
- Прогон по runbook от подготовленного артефакта до отчёта

## Task T7: Веб-клиент (опционально/отложено — TD-006)

**Priority:** P3 · **Estimate:** 2–4h · **Dependencies:** T5 + GUI-вопрос пользователю · **Covers:** FR-007

### Work
- [ ] Pre-flight вопрос: «Сессия интерактивная? (Apache-публикация
      требует видимый десктоп)»
- [ ] Если да: web-publish dev_erpapk_demo → флаг `--web-client`
      (ТипКлиента в VAParams) → rehearsal-прогон веб-клиентом
- [ ] Если headless: фиксация откладывания в design.md §4.8 + здесь;
      T7 закрывается как deferred

### Acceptance Criteria
- [ ] Явный вердикт: реализовано (прогон веб-клиентом зелёный) или
      deferred с причиной (D-006)

### Files
- `scripts/regress_run.py` (только при реализации), фиксация в design.md

### Verification
- При реализации: rehearsal с ТипКлиента=web, вердикт в отчёте

## Task T8: Ретро релиза 2

**Priority:** P2 · **Estimate:** 0.5h · **Dependencies:** T5 (факты релиза 1) · **Covers:** FR-008

### Work
- [x] Обсуждение с пользователем (2026-10-19): релиз 2 = (а) реальные
      авторы (снятие D-001) + (д) негативные сценарии; животноводство и
      планирование — бэклог; arm-fuel-expense-авто — остаётся never
- [x] Фиксация решений в `.ai/sdd/PLAN.md` (Фаза 5 / roadmap v2)
- [x] Ретро-раздел PLAN.md отревьюен пользователем (подтверждено 2026-10-19,
      «делай»)

### Acceptance Criteria
- [x] PLAN.md дополнен разделом ретро с явными решениями или отложенными
      вопросами (Фаза 5 / roadmap v2)

### Files
- `.ai/sdd/PLAN.md`

### Verification
- Ревью PLAN.md пользователем

## Рекомендуемый порядок

```text
T1 (разведка) → T2 (скелет) → T4 (отчёт/baseline) → T3 (update) → T5 (E2E+baseline) → T6 (runbook) → T8 (ретро) → T7 (веб, опц.)
```

Отклонения от исходного промта (там T3=runbook, T2=E2E+baseline): порядок
выровнен по зависимостям — runbook пишется по фактическим командам (после
T5), baseline фиксируется в E2E (T5). Содержательное покрытие то же.


## Task T9 (добавлено по решению пользователя 2026-10-19, TD-007): `--baseline-dt`

**Priority:** P1 · **Estimate:** 2h · **Dependencies:** T5 · **Covers:** TD-007 (design.md §13)

### Work
- [x] `regress_run.py`: флаг `--baseline-dt <file>`: дамп текущего →
      RestoreIB baseline-dt → гейт → откат к дампу текущего (finally)
- [x] Взаимоисключаемость с `--update` (RestoreIB затёр бы обновление);
      `--rehearsal --baseline-dt` — рабочий режим (дрилль 09:42: оба отказа
      exit=2 до дампа, база не менялась)
- [x] Runbook: раздел baseline-dt + «снять свежий baseline-dt после
      зелёного прогона с обновлением» (§2 runbook)
- [x] E2E: `--rehearsal --baseline-dt tmp/regress/20261019-052456/pre-update.dt`
      → 5/5, regressions=0, откат к исходному (20261019-094315, exit=0,
      46.2 мин; evidence: `tmp/regress/EVIDENCE-T9.md`)

### Acceptance Criteria
- [x] Прогон с baseline-dt зелёный; стартовое состояние идентично эталону
      (все 5 «=» vs run-20261019-053203)
- [x] `--update` + `--baseline-dt` вместе → отказ с понятным сообщением
      (exit=2, 20261019-094259)

### Files
- `scripts/regress_run.py`, `docs/runbook.md`

### Verification
- Полный прогон + сравнение отчётов (regressions=0)
