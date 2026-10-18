# SDD Handoff Brief: Спека 003 — Регресс-конвейер

> Status: Ready for implementation
> Readiness: requirements + design + tasks approved
> Updated: 2026-10-18

## Metadata

- **Spec ID:** `003-regression-conveyor`
- **Spec Path:** `.ai/sdd/specs/003-regression-conveyor/`
- **Current .status:** `tasks:approved`
- **Source Inputs:** `.ai/sdd/PLAN.md` (Фаза 4, D7), `docs/next-session-prompt.md`,
  `docs/night-report-2026-10-17.md` (спеки 001–002 завершены)

## Product / Feature Summary

- **User:** администратор демо-базы `dev_erpapk_demo`, получающий релизы ERP+АПК.
- **Problem:** процедура регресса после обновления релиза не упакована: нет
  одной команды, безопасного цикла «дамп → обновление → прогон → откат»,
  baseline-эталона и runbook.
- **Outcome:** `python scripts/regress_run.py --rehearsal | --update <path>`
  → отчёт (сценарий × пользователь × статус × vs baseline) при
  гарантированном dt-откате демо-базы.
- **Scope:** новый оркестратор `scripts/regress_run.py`, baseline
  `tests/baseline/`, `docs/runbook.md`. Гейт `t8_gate.py` и EPF НЕ меняются.
- **Out of Scope:** реальное применение релизов из внешних источников,
  реальные авторы (D-001), новые шаблоны, allure-commandline, CI/CD.

## Requirements Summary

- **Must Have:** FR-001 (one-command, режимы --rehearsal/--update),
  FR-002 (гарантированный откат), FR-003 (отчёт), FR-004 (baseline-diff).
- **Should Have:** FR-005 (реестр baseline), FR-006 (runbook).
- **Could Have:** FR-007 (веб-клиент, D-006 отложенный), FR-008 (ретро).
- **Key Decisions:** D-004 (CLI py-раннер), D-005 (baseline JSON в git),
  D-006 (веб отложен при headless), D-007 (rehearsal + update), D-008 (ретро
  задачей), наследие D-001 (зонды), D-002 (веб по флагу), D-003 (без allure-cli).

## Design Summary

- **Approach:** тонкая обёртка над доказанным гейтом (TD-001, подпроцесс);
  dt-lifecycle через `1cv8 DESIGNER /DumpIB`/`/RestoreIB` с откатом в
  `finally` и без авто-удаления дампов (TD-002/TD-004); baseline-ключ
  (scenario, user) с классами REGRESSION/IMPROVED/NEW/MISSING (TD-003);
  безопасная репетиция update — dt той же базы (TD-005); веб-клиент — слот
  после GUI-вопроса (TD-006).
- **Components:** `scripts/regress_run.py` (новый), `scripts/t8_gate.py`
  (без правок), `tests/baseline/{baseline.json,history/}`, `docs/runbook.md`,
  артефакты в `tmp/regress/<ts>/`.
- **Data:** вход — `tests/run-*/summary.json` (проверенная структура:
  totals, scenarios[{scenario,user,status,durationMs,returnStatus}],
  batches[{user,batch,returnStatus,verdict,passwordRestored,zodRestored}]).
- **Risks:** монопольный доступ RestoreIB (чужие сессии), несовместимость
  CF с расширением VA, время дампа — все с митигациями в design §14.

## Implementation Plan

- **Task Source:** `.ai/sdd/specs/003-regression-conveyor/tasks.md`
- **Recommended Order:** T1 → T2 → T4 → T3 → T5 → T6 → T8 → T7 (опц.)
- **Key Tasks:** T1 (флаги/тайминги дизайнера — факты для всего), T5
  (E2E-доказательство + фиксация baseline релиза 1).
- **Likely Files:** см. tasks.md per-task Files.

## Verification Plan

```text
T1: python scripts/t1_probe_dump.py → dump.log + t1-facts.md
T2/T5: реальный rehearsal: гейт 5/5 rs=0, rollback=OK, regress-report.md
T4: python scripts/test_regress_diff.py (синтетика diff-классов) — зелёный
Гейты BSL: n/a (BSL/XML не меняются в спеке 003)
```

## Review / Release Notes

- **Review Artifact:** not yet
- **Review Verdict:** Not reviewed
- **Known Follow-ups:** T7 веб-клиент (GUI-вопрос перед стартом), T8 ретро
  релиза 2 (с пользователем), carried-девиации: авто-ПЛ `when: never`,
  статичный окт-2026.

## Handoff Readiness

- **Ready for Implementation:** yes
- **Ready for QA:** no (после T5)
- **Ready for Release:** no (после T6+review)

## Дисциплина реализации (переносится)

Последовательные шаги, коммиты per задача, heartbeat `tmp/t9/heartbeat.txt`,
PROGRESS per задача, 2-attempt stop, кириллица в CLI только через
heredoc-билдеры, реальная верификация перед claim complete.
