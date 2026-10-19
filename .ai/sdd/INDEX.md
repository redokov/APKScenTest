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
| Next Feature ID | 003 | Recompute from filesystem before creating a new spec |
| Numbering Issues | none | |

## Specs

| ID | Feature | Status | Requirements | Design | Tasks | Review |
|----|---------|--------|--------------|--------|-------|--------|
| 001 | Обработка препроцессинга (preprocessor-epf) | implementation:complete (T1–T9 закрыты 2026-10-15, E2E доказан run-20261015-003718) | `.ai/sdd/specs/001-preprocessor-epf/requirements.md` | `.ai/sdd/specs/001-preprocessor-epf/design.md` | `.ai/sdd/specs/001-preprocessor-epf/tasks.md` | — |
| 002 | Сценарии растениеводства (rastenievodstvo-scenarios) | implementation:complete (T1–T9 закрыты 2026-10-17, полные E2E-гейты зелёные: run-20261017-060711 = 4/4 rs=0, run-20261017-084258 = 5/5 rs=0, NFR-001 18.3 мин ≤40) | `.ai/sdd/specs/002-rastenievodstvo-scenarios/requirements.md` | `.ai/sdd/specs/002-rastenievodstvo-scenarios/design.md` | `.ai/sdd/specs/002-rastenievodstvo-scenarios/tasks.md` | — |
| 003 | Регресс-конвейер (regression-conveyor) | review:done (Approved with follow-ups, 2026-10-19: T1–T6/T8/T9 закрыты E2E; T7 веб — deferred средой (лицензия), evidence зафиксирован) | `.ai/sdd/specs/003-regression-conveyor/requirements.md` | `.ai/sdd/specs/003-regression-conveyor/design.md` | `.ai/sdd/specs/003-regression-conveyor/tasks.md` | `.ai/sdd/specs/003-regression-conveyor/review.md` |

## Handoff

- `.ai/sdd/handoff/sdd-brief.md`: обновлён 2026-10-15 (ключевые решения реализации, ограничения E2E, кандидаты в спеку 002)

## Next Actions

- [x] Реализация спеки 001 (T1–T9) — завершена 2026-10-15: полный цикл E2E, отчёт `docs/night-report-2026-10-15.md`, продолжение — `docs/next-session-prompt.md`
- [x] Спека 002: T1–T9 — закрыта 2026-10-17 (полный E2E 5/5 rs=0, NFR-001 18.3 мин); продолжение — `docs/next-session-prompt.md` (спека 003)
- [ ] Спека 003 «Регресс-конвейер»: requirements approved 2026-10-18 → design (sdd-spec) → tasks (sdd-tasks) → реализация T1…Tn
- [x] Спека 003: T1–T6 закрыты 2026-10-19 (E2E: rehearsal 20261019-052456 5/5 + update-репетиция 20261019-055846 5/5, regressions=0; baseline 5242814; runbook 2ca929b); остатки: T7 (веб, GUI-вопрос), T8 (ретро с пользователем), TD-007 (--baseline-dt, решение)
- [x] Спека 003 финал 2026-10-19: T9 --baseline-dt E2E зелёный (20261019-094315); T8 чекбокс закрыт; T7 — механика готова, прогон заблокирован лицензией среды (deferred-with-evidence); review.md Approved with follow-ups; .status review:done
- [x] Open Q дизайна «наряд → АРМ ВыработкиСотрудников» — верифицирован по модулям (ManagerModule:209,353,874 → АРМ:117), coverage-map `verified:true`
- [x] coverage-map обогащён: каталожные оси ЗаправочныхВедомостей (docField/valuePath/tabularSources)
