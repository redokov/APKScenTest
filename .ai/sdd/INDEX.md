# SDD Index

## Upstream Handoffs

- `.ai/strategy/handoff/strategy-brief.md`: missing

## Plan

- `.ai/sdd/PLAN.md`: draft (roadmap v1, ожидает обсуждения с пользователем)

## Ideas

| ID | Name | Status | Path |
|----|------|--------|------|
| — | (пусто) | — | — |

## Feature Workspace

> Numbering source: actual directories under `.ai/sdd/specs/`, not this index.

| Field | Value | Notes |
|-------|--------|-------|
| Next Feature ID \| 007 \| Recompute from filesystem before creating a new spec |
| Numbering Issues \| created 007 by agent this session \| |

## Specs

| ID | Feature | Status | Requirements | Design | Tasks | Review |
|----|---------|--------|--------------|--------|-------|--------|
| 001 | Обработка препроцессинга (preprocessor-epf) | implementation:complete (T1–T9 закрыты 2026-10-15, E2E доказан run-20261015-003718) | `.ai/sdd/specs/001-preprocessor-epf/requirements.md` | `.ai/sdd/specs/001-preprocessor-epf/design.md` | `.ai/sdd/specs/001-preprocessor-epf/tasks.md` | — |
| 002 | Сценарии растениеводства (rastenievodstvo-scenarios) | implementation:complete (T1–T9 закрыты 2026-10-17, полные E2E-гейты зелёные: run-20261017-060711 = 4/4 rs=0, run-20261017-084258 = 5/5 rs=0, NFR-001 18.3 мин ≤40) | `.ai/sdd/specs/002-rastenievodstvo-scenarios/requirements.md` | `.ai/sdd/specs/002-rastenievodstvo-scenarios/design.md` | `.ai/sdd/specs/002-rastenievodstvo-scenarios/tasks.md` | — |
| 003 | Регресс-конвейер (regression-conveyor) | review:done (Approved with follow-ups, 2026-10-19: T1–T6/T8/T9 закрыты E2E; T7 веб — deferred средой (лицензия), evidence зафиксирован) | `.ai/sdd/specs/003-regression-conveyor/requirements.md` | `.ai/sdd/specs/003-regression-conveyor/design.md` | `.ai/sdd/specs/003-regression-conveyor/tasks.md` | `.ai/sdd/specs/003-regression-conveyor/review.md` |
| 004 | Реальные авторы + негативные (real-authors-negative) | tasks:approved (механизмы реализованы в BSL-раннере и подтверждены ночными гейтами T13–T18: 16/16 + neg, baseline run-20261028-062621) | `.ai/sdd/specs/004-real-authors-negative/requirements.md` | `.ai/sdd/specs/004-real-authors-negative/design.md` | `.ai/sdd/specs/004-real-authors-negative/tasks.md` | — |
| 005 | Чистый 1С-комплект (pure-1c-kit, Фаза 6 — коррекция миграции цели 28.10) | **done** 31.10: T1–T8 закрыты, T3/T4/T5/T8 — живьём. Финал: E2E из чистой сессии на idle-десктопе — PASS 17/17 (16 passed + neg-passed=1), регрессий 0 vs baseline, пароли восстановлены (mismatch=[]), улика docs/evidence/s005-live-20261030/t8-e2e-verdict-night.txt; README «Состав комплекта dist/», чекбоксы Фазы 6 + ретро в PLAN | `.ai/sdd/specs/005-pure-1c-kit/requirements.md` | `.ai/sdd/specs/005-pure-1c-kit/design.md` | `.ai/sdd/specs/005-pure-1c-kit/tasks.md` | — |
| 007 | Code Review Fixes (v2, после аудита) | **revised** 06.11: аудит 23 замечаний — критичных нет, `major` 1 (CR-05); план сокращён 27→11 задач, 12 замечаний отклонено с обоснованием (`docs/code-review-007-audit-2026-11-06.md`); ночной промт `docs/night-prompt-2026-11-06-007-fixes-v2.md` | `.ai/sdd/specs/007-code-review-fixes/requirements.md` | `.ai/sdd/specs/007-code-review-fixes/design.md` | `.ai/sdd/specs/007-code-review-fixes/tasks.md` | — |
| 006 | Животноводство — сценарии группового учёта СВН и КРС (главы 3+5 АПК) | **done** 03.11.2026: T1–T7 закрыты; 14 сценариев (6 СВН + 8 КРС) зелёные в полном E2E-конвейере, neg-гейт зелёный; 4 контрольных прогона подряд (s010…s013) 45/0/neg-1, регрессий 0 vs baseline (run-20261102-034905); улики docs/evidence/s006-live-20261101/ + night-report-2026-11-02-s009…night-report-2026-11-03-s013 | `.ai/sdd/specs/006-zhivotnovodstvo-scenarios/requirements.md` | `.ai/sdd/specs/006-zhivotnovodstvo-scenarios/design.md` | `.ai/sdd/specs/006-zhivotnovodstvo-scenarios/tasks.md` | — |

## Handoff

- `.ai/sdd/handoff/sdd-brief.md`: обновлён 03.11.2026 (текущее состояние, recipes proгона, блокеры)

## Next Actions

- [x] Реализация спеки 001 (T1–T9) — завершена 2026-10-15: полный цикл E2E, отчёт `docs/night-report-2026-10-15.md`, продолжение — `docs/next-session-prompt.md`
- [x] Спека 002: T1–T9 — закрыта 2026-10-17 (полный E2E 5/5 rs=0, NFR-001 18.3 мин); продолжение — `docs/next-session-prompt.md` (спека 003)
- [x] Спека 003 «Регресс-конвейер»: закрыта 2026-10-19 (детали — строками ниже; T7 deferred-with-evidence — лицензия среды)
- [x] Спека 003: T1–T6 закрыты 2026-10-19 (E2E: rehearsal 20261019-052456 5/5 + update-репетиция 20261019-055846 5/5, regressions=0; baseline 5242814; runbook 2ca929b); остатки: T7 (веб, GUI-вопрос), T8 (ретро с пользователем), TD-007 (--baseline-dt, решение)
- [x] Спека 003 финал 2026-10-19: T9 --baseline-dt E2E зелёный (20261019-094315); T8 чекбокс закрыт; T7 — механика готова, прогон заблокирован лицензией среды (deferred-with-evidence); review.md Approved with follow-ups; .status review:done
- [x] Open Q дизайна «наряд → АРМ ВыработкиСотрудников» — верифицирован по модулям (ManagerModule:209,353,874 → АРМ:117), coverage-map `verified:true`
- [x] coverage-map обогащён: каталожные оси ЗаправочныхВедомостей (docField/valuePath/tabularSources)
- [x] Спека 005 «Чистый 1С-комплект» (Фаза 6): **ЗАКРЫТА 31.10.2026** — все T1–T8; T1 (аудит, fe91d07), T2 (патчи в 1С, byte-diff гейт 0, fa6adff), T3 (prep-гейт живьём 103с), T4-код (раннер-драйвер, 355a6d5) + полный прогон живьём 16/16 + отчёт-форма, T5 (src/АпкРаннер 460a2ce + neg-раннер PASS 103с, паритет MISSING=16), T6 (сборка dist/), T7 (ИНСТРУКЦИЯ.md), T8 (E2E из чистой сессии PASS 17/17, регрессий 0, ночь 31.10, idle-десктоп). Чекбоксы Фазы 6 PLAN закрыты, ретро добавлено, README — состав dist/
- [x] Спека 006 «Животноводство»: **ЗАКРЫТА 03.11.2026** — T1 аудит, T2 coverage-map (19 записей) + скан-гейт, T3 СВН ×6, T4 КРС ×8, T5 neg-гейт (s006-negrun-final зелёный), T6/T7 — контрольные E2E s010…s013 (45/0/neg-1, регрессий 0), dist/ пересобран (baseline 46 ключей), ИНСТРУКЦИЯ §5
- [ ] Открытые вопросы (нужно решение пользователя): web-режим — нет веб-публикации dev_erpapk_demo (wsap24.dll от 8.5.4, порт 9094 vs WEB_URL_DEFAULT 9093; см. night-report-2026-11-03-s012.md)
- [x] Фоновые DefUser (BackgroundJob) сессии после restore — решено в s014: префлайт t8_gate.py исключает BackgroundJob (как RAS); интерактивные сеансы блокируют как раньше; unit-тест tests/test_rac_sessions_filter.py
