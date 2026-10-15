# SDD Handoff Brief: Спека 002 — Сценарии растениеводства

> Status: Draft
> Readiness: Ready for implementation
> Updated: 2026-10-15

## Metadata

- **Spec ID:** `002-rastenievodstvo-scenarios`
- **Spec Path:** `.ai/sdd/specs/002-rastenievodstvo-scenarios/`
- **Current .status:** `tasks:approved`
- **Source Inputs:** `.ai/sdd/PLAN.md` (Фаза 3), D-013 спеки 001, `docs/night-report-2026-10-15.md`

## Product / Feature Summary

- **User:** инженер АПК, проверяющий обновление релиза ERP/АПК.
- **Problem:** покрыт только один сценарий ввода (01-pl-tractor);
  план Фазы 3 требует наборы по группам документов растениеводства.
- **Outcome:** полный регресс-прогон покрывает путевые листы (трактор/авто),
  заправочные ведомости, взвешивания, наряды и отражение АРМами.
- **Scope:** 6+ новых шаблонов, расширение экстрактора фикстур,
  расширение манифеста батчей. Конвейер спеки 001 — без изменений.
- **Out of Scope:** животноводство, негативные сценарии, веб-клиент,
  реальные авторы (до явного разрешения пользователя).

## Requirements Summary

- **Key User Stories:** US-001 (02-pl-auto), US-002 (04-fuel-sheet),
  US-003 (05-weighing), US-004 (arm-*), US-005 (фикстуры)
- **Must Have:** FR-001, FR-002, FR-003, FR-006, FR-007, FR-008
- **Should Have:** FR-004 (АРМ), FR-005 (наряды)
- **Acceptance Notes:** критерий достаточности D-013: шаблон заполняет
  документ целиком из фикстуры, проверяется probe-прогоном.

## Design Summary

- **Approach:** probe-first per шаблон (раннее правило T8), только
  доказанные механизмы VA (TD-001), расширение экстрактора на месте
  (TD-002), разведка АРМ до шаблонов (TD-003), исследование
  сопоставления авторов нарядов (TD-004).
- **Components / Modules:** `tests/templates/`, экстрактор
  `ObjectModule.bsl`, `tests/coverage-map.json`, probe-раннеры
  `scripts/s2_probe*_run.py`.
- **Data / State:** fixtures.json `documents[].data.tabular` — полный
  состав колонок, ≤3 строки (D-002), производные поля.
- **APIs / Integrations:** манифест фич привязывает шаблоны к типам
  документов (§6 design).
- **Risks / Constraints:** механика АРМ неизвестна (разведка T7);
  авторы нарядов могут не сопоставляться (T5).

## Implementation Plan

- **Task Source:** `.ai/sdd/specs/002-rastenievodstvo-scenarios/tasks.md`
- **Recommended Order:** T1 → (T2, T3, T4, T5, T7 параллельно-последовательно) → T6, T8 → T9
- **Key Tasks:** T1 (экстрактор) — блокирует все шаблоны; T9 (полный цикл) — финал
- **Likely Files / Areas:** см. tasks.md

## Verification Plan

```text
Probe-прогоны per шаблон: ReturnStatus=0 дважды подряд
Полный цикл: python scripts/s2_gate.py (или t8_gate) — все батчи rs=0
Гейты BSL: bsl-ls (bsl_analyze ≠ 0 файлов) + v8std; сборка scripts/build_t6.py
```

## Review / Release Notes

- **Review Artifact:** not yet
- **Review Verdict:** Not reviewed
- **Known Follow-ups:** режим реальных авторов (Q-001/D-001 спеки 002) —
  отдельное решение пользователя; негативные сценарии — вне скоупа.

## Handoff Readiness

- **Ready for Implementation:** yes
- **Ready for QA:** no (после T9)
- **Ready for Release:** no

## Дисциплина реализации (переносится из спеки 001)

Оркестратор + последовательные субагенты (wormsoft/zai/glm-5.3:NVFP4),
PROGRESS.md per задача (`tmp/s2/`), heartbeat, гейты после каждой правки
BSL, probe-first, 2-attempt stop, безопасность: зонды, реальные
пользователи НЕ трогать, конфигурация базы не меняется.
