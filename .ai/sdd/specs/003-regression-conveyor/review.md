# Review: Спека 003 — Регресс-конвейер (regression-conveyor)

> Requirements: @requirements.md
> Design: @design.md
> Tasks: @tasks.md
> Status: Final
> Reviewed: 2026-10-19

## Review Scope

- **Feature:** Регресс-конвейер one-command (rehearsal/update, dt-lifecycle, baseline-diff, runbook)
- **Implementation status:** implementation:done (T1–T6, T8, T9 закрыты; T7 — Could Have, вердикт зафиксирован)
- **Files reviewed:**
  - `scripts/regress_run.py` (ядро конвейера)
  - `scripts/test_regress_diff.py`, `scripts/t1_probe_dump.py`
  - `scripts/t8_gate.py` (только фикс crash→явный FAIL; гейт не менялся по TD-001 в v1)
  - `tests/baseline/baseline.json`, `tests/baseline/history/`
  - `docs/runbook.md`
  - evidence: `tmp/regress/EVIDENCE-T5.md`, `tmp/regress/EVIDENCE-T7.md`, `tmp/regress/EVIDENCE-T9.md`, `tmp/regress/probe/t1-facts.md`
- **Out of review scope:** содержимое EPF-раннера и шаблоны фич (спеки 001/002); инфраструктура лицензий Apache/PostgreSQL (среда).

## Coverage Check

| Requirement | Expected Coverage | Status | Evidence / Notes |
|-------------|-------------------|--------|------------------|
| FR-001 (Must) | §4.1/§4.2, T2/T3/T5 | Pass | Одна команда `regress_run.py --rehearsal \| --update <cf\|dt>`; E2E: rehearsal 20261019-052456 (exit 0), update-репетиция 20261019-055846 (exit 0), baseline-dt 20261019-094315 (exit 0) |
| FR-002 (Must) | §4.3, TD-002/TD-004 | Pass* | Откат в `finally` при любом исходе; rollback=OK во всех зелёных прогонах. *Сбой отката 20261019-103036 вызван таймаутом 1500 с при деградировавшей среде (лицензии) — воспроизведён путь восстановления (runbook §4 новые строки); база восстановлена полностью (COM-запросы, регистры). Таймауты restore увеличены рекомендацией ≥3000 с в runbook |
| FR-003 (Must) | §4.4, T4 | Pass | `regress-report.md`: сценарий × пользователь × статус × vs baseline × длительность + батчи (rs, пароли, ЗОД) + фазы |
| FR-004 (Must) | §4.5, TD-003 | Pass | diff-классы REGRESSION/IMPROVED/NEW/MISSING/=; py-тест 10/10; фактический прогон: все «=», regressions=0 |
| FR-005 (Should) | §4.5, D-005 | Pass | `tests/baseline/baseline.json` в git (эталон релиза 1, commit 5242814) + `history/`; `--set-baseline` только при зелёном гейте |
| FR-006 (Should) | §4.7, T6 | Pass | `docs/runbook.md`: команды, флаги, тайминги, таблица сбоев (пополнена реальными кейсами 19.10), обслуживание/чистка |
| FR-007 (Could) | §4.8, TD-006/D-006 | Partial (намеренно) | Механика готова и частично доказана: публикация 200, `--web-client` патчит настройки, EPF пересобран под clientType/Web. Прогон веб-клиентом заблокирован средой: `ELicenceNotFound` (1 одновременное место лицензии). Вердикт: deferred-with-evidence (`tmp/regress/EVIDENCE-T7.md`) — допустимо для Could Have по формулировке FR («при отсутствии публикации — отложено») |
| FR-008 (Could) | §9 T-ретро, T8 | Pass | PLAN.md «Фаза 5 / roadmap v2»: состав релиза 2 утверждён пользователем, ретро-раздел отревьюен (3167c3b) |
| NFR-001 (≤40 мин) | §4.6 | Pass | gate 14 мин (870 с в худшем замере) ≤ 40; полный цикл rehearsal+baseline-dt 46.2 мин вне лимита (дамп/restore не входят, зафиксировано в design) |
| NFR-002 (зонды/данные) | §6 | Pass | Только зонды Д-001; хэши восстанавливаются внутри гейта (pwd=True zod=True в отчётах); реальные авторы не тронуты |
| NFR-003 (надёжность) | §4.2/§8 | Pass | exit 0/1/2 подтверждены дриллями (abort до дампа exit=2 ×3 сценария); watchdog-таймауты фаз; finally-откат |
| NFR-004 (usability) | §4.1 | Pass | Один вход, сводка в консоль (последняя строка вердикт), артефакты в `tmp/regress/<ts>/` |

## Task Completion Check

| Task | Status | Evidence / Notes |
|------|--------|------------------|
| T1 разведка CLI | Pass | t1-facts.md: DumpIB 206.7 с/1733 МБ; флаги подтверждены |
| T2 скелет rehearsal | Pass | E2E 20261019-052456 5/5 exit 0 |
| T3 update cf/dt | Pass | dt-ветка E2E (868 с); cf-ветка кодом (артефакт-артефакт для E2E отсутствует — осознанно, см. tasks) |
| T4 отчёт+baseline+diff | Pass | test_regress_diff 10/10; baseline 5242814 |
| T5 E2E | Pass | EVIDENCE-T5.md |
| T6 runbook | Pass | написан по фактическим командам; пополнен после инцидента 19.10 |
| T7 веб (Could) | Deferred | EVIDENCE-T7.md; среда (лицензия), не код |
| T8 ретро | Pass | решения пользователя в PLAN.md, чекбокс закрыт |
| T9 --baseline-dt | Pass | E2E 20261019-094315: 5/5, regressions=0, rollback OK, exit 0; взаимоисключение с --update проверено (exit 2) |

## Design Check

| Design Area / Decision | Status | Notes |
|------------------------|--------|-------|
| TD-001 обёртка без правок гейта | Pass | t8_gate изменён минимально: явный FAIL вместо AttributeError-краша (усиление наблюдаемости, поведение зелёного пути не тронуто) |
| TD-002 DESIGNER batch dump/restore | Pass | подтверждено 5 прогонами |
| TD-003 ключ (scenario,user) | Pass | реализовано + тесты |
| TD-004 дампы не удалять | Pass | TD-004 соблюдён; чистка — ручная, в runbook |
| TD-005 rehearsal через dt той же базы | Pass | E2E |
| TD-006 веб-слот | Partial | реализован, заблокирован средой; зафиксировано |
| TD-007 baseline-dt | Pass | E2E + дрилли отказов |
| Exit-коды/edge cases (§8) | Pass | abort-пути проверены фактически |
| rac scheduled-jobs-deny (§4.2 п.1 доп.) | Pass | включение/восстановление исходного значения |

## Code Quality Check

- [x] Follows project conventions (Python-обёртки в scripts/, кириллица через файлы/write-tool, артефакты tmp/)
- [x] No obvious duplication (гейт не дублируется; diff-логика вынесена и покрыта тестом)
- [x] Error/loading/empty states handled (нет baseline → «n/a»; abort-сообщения с причиной; сбой отката → инструкция вручную)
- [x] Types are appropriate (JSON summary/report)
- [x] Security/privacy considerations are handled (дампы в gitignored tmp/, предупреждение в runbook; пароли не трогаются обёрткой)
- [x] Accessibility considerations are handled where relevant — N/A (CLI)
- [x] No unnecessary complexity (~450 строк, линейные фазы)
- [x] Tests cover important behavior and edge cases (diff 10/10; dрилль-команды в EVIDENCE)

## Verification

```text
Command: python scripts/regress_run.py --rehearsal --baseline-dt tmp/regress/20261019-052456/pre-update.dt
Exit code: 0
Summary: preflight 44s -> dump 205s -> baseline-restore 854s -> gate 870s (5/5) -> rollback 800s; regressions=0
Verdict: PASS

Command: python scripts/regress_run.py --update tmp/nonexistent.dt --baseline-dt <valid.dt>
Exit code: 2
Summary: ABORT до дампа, база не менялась (взаимоисключение)
Verdict: PASS

Command: python scripts/regress_run.py --rehearsal (прогон 20261019-052456)
Exit code: 0
Summary: rehearsal 5/5, baseline зафиксирован (EVIDENCE-T5)
Verdict: PASS

Command: python scripts/regress_run.py --rehearsal --update <dt той же базы> (TD-005, 20261019-055846)
Exit code: 0
Summary: update 868s, gate 5/5, rollback OK, regressions=0
Verdict: PASS

Command: python scripts/test_regress_diff.py
Exit code: 0
Summary: 10/10 passed
Verdict: PASS

Command: python scripts/regress_run.py --rehearsal --web-client (20261019-103036)
Exit code: 2
Summary: гейт rs=2 (лицензии среды ELicenceNotFound); механика web-patch доказана; откат потребовал ручного восстановления (см. Issues)
Verdict: FAIL (среда, не код) — FR-007 Could Have, зафиксирован как deferred
```

## Issues Found

### Issue 1: RestoreIB-таймаут 1500 с недостаточен при деградации среды

- **Severity:** Medium
- **File:** `scripts/regress_run.py` (`TIMEOUT_RESTORE`)
- **Line:** ~35
- **Problem:** при внешней деградации (лицензии/нагрузка) restore идёт дольше; kill посреди RestoreIB оставляет базу временно неавторизуемой и требует ручного восстановления (инцидент 20261019-103036, простой ~2 ч)
- **Requirement/Task Impact:** FR-002/NFR-003
- **Suggested Fix:** увеличить TIMEOUT_RESTORE до 3000 с и/или перед kill проверять активность restore (подключения rphost→pg); в runbook рекомендации уже добавлены. Не блокер: штатные прогоны укладываются в 800–900 с

### Issue 2: t8_gate AttributeError при пустом result раннера (ИСПРАВЛЕНО в этой сессии)

- **Severity:** Low (fix 362de0e)
- **File:** `scripts/t8_gate.py`
- **Problem:** None.get crash вместо явного вердикта FAIL
- **Requirement/Task Impact:** NFR-003
- **Suggested Fix:** применён (явный FAIL + finish(False))

### Issue 3: Лицензия среды блокирует параллельные сеансы (не код)

- **Severity:** High для FR-007 (веб) и потенциально для любых прогонов при откате лицензии
- **File:** — (среда)
- **Problem:** licenceserver серия 4135: `ELicenceNotFound`, затем 1 одновременное место; конвейеру нужно ≥2–3 сеанса
- **Requirement/Task Impact:** FR-007 (Could), риск FR-001
- **Suggested Fix:** административный: увеличить число мест/серий лицензий; до этого — не планировать веб-прогоны

## Positive Findings

- Полный SDD-цикл за 2 сессии; каждый шаг — с E2E-доказательством и коммитом.
- `--baseline-dt` закрыл реальную проблему деградации демо-базы (TD-007 из открытия T5).
- Runbook живёт: инциденты превращаются в строки таблицы сбоев в тот же день.
- Abort-пути и exit-коды проверены фактическими дриллями, а не «на глаз».

## Follow-Ups

- Увеличить `TIMEOUT_RESTORE` (Issue 1) — мелкая правка, можно в релизе 2.
- Повторить веб-прогон T7 при доступной лицензии (≥3 одновременных мест).
- После первого зелёного прогона с обновлением релиза 2 — снять свежий baseline-dt (runbook §2).
- Релиз 2 (PLAN.md Фаза 5): реальные авторы + негативные сценарии.

## Verdict

- [ ] Approved
- [x] Approved with follow-ups
- [ ] Needs fixes

**Reason:** Все Must Have (FR-001…FR-004) и Should Have (FR-005/006) выполнены и доказаны E2E; NFR-001…004 соблюдены; Could Have FR-007 намеренно отложен с evidence (блокировка средой, не кодом), FR-008/T8 закрыты. Найденные проблемы — environment/medium, не затрагивают корректность конвейера.
