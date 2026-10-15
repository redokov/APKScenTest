# SDD Index

## Upstream Handoffs

- `.ai/strategy/handoff/strategy-brief.md`: missing

## Plan

- `.ai/sdd/PLAN.md`: draft (roadmap v1, ожидает обсуждения с пользователем)

## Ideas

| ID | Name | Status | Path |
|----|------|--------|------|

## Feature Workspace

> Numbering source: actual directories under `.ai/sdd/specs/`, not this index.

| Field | Value | Notes |
|-------|-------|-------|
| Next Feature ID | 002 | Recompute from filesystem before creating a new spec |
| Numbering Issues | none | |

## Specs

| ID | Feature | Status | Requirements | Design | Tasks | Review |
|----|---------|--------|--------------|--------|-------|--------|
| 001 | Обработка препроцессинга (preprocessor-epf) | implementation:complete (T1–T9 закрыты 2026-10-15, E2E доказан run-20261015-003718) | `.ai/sdd/specs/001-preprocessor-epf/requirements.md` | `.ai/sdd/specs/001-preprocessor-epf/design.md` | `.ai/sdd/specs/001-preprocessor-epf/tasks.md` | — |
| 002 | Сценарии растениеводства (rastenievodstvo-scenarios) | implementation:in-progress (T1, T5 закрыты 2026-10-15; следующий — T2, промт: docs/next-session-prompt.md) | `.ai/sdd/specs/002-rastenievodstvo-scenarios/requirements.md` | `.ai/sdd/specs/002-rastenievodstvo-scenarios/design.md` | `.ai/sdd/specs/002-rastenievodstvo-scenarios/tasks.md` | — |

## Handoff

- `.ai/sdd/handoff/sdd-brief.md`: обновлён 2026-10-15 (ключевые решения реализации, ограничения E2E, кандидаты в спеку 002)

## Next Actions

- [x] Реализация спеки 001 (T1–T9) — завершена 2026-10-15: полный цикл E2E, отчёт `docs/night-report-2026-10-15.md`, продолжение — `docs/next-session-prompt.md`
- [ ] Спека 002: T2 → T3 → T4 → T6 → T7 → T8 → T9 (промт: `docs/next-session-prompt.md`)
- [x] Open Q дизайна «наряд → АРМ ВыработкиСотрудников» — верифицирован по модулям (ManagerModule:209,353,874 → АРМ:117), coverage-map `verified:true`
- [x] coverage-map обогащён: каталожные оси ЗаправочныхВедомостей (docField/valuePath/tabularSources)
