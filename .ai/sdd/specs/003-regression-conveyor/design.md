# Design: Регресс-конвейер (спека 003)

> Requirements: @requirements.md
> Status: Draft
> Last Updated: 2026-10-18

## 1. Executive Summary

Тонкий оркестратор `scripts/regress_run.py` вокруг **неизменяемого в v1**
гейта `scripts/t8_gate.py`: preflight → dt-дамп (designer batch) →
применение «обновления» (`--update`: CF или dt) → E2E-гейт подпроцессом →
гарантированный dt-откат в `finally` → отчёт с baseline-сравнением.
Baseline — JSON-сводка в `tests/baseline/` под git; сравнение строится из
`summary.json` прогона (проверено: там уже есть totals, scenarios
[scenario, user, status, returnStatus], batches, artifacts — см.
`tests/run-20261017-084258/summary.json`). Веб-клиент (FR-007) —
опциональная задача после preflight-вопроса о GUI (D-006), в v1
проектируется как слот, не как блокер.

Ключевой компромисс: НЕ встраивать регресс-логику в `t8_gate.py`
(TD-001) — гейт остаётся «чистым» прогоном, жизненным циклом данных
демо-базы управляет отдельная обёртка.

## 2. Requirements Mapping

| Requirement | Design Coverage | Notes |
|-------------|-----------------|-------|
| FR-001 (one-command) | §4.1 CLI + §4.2 конвейер | `regress_run.py --rehearsal \| --update <path>` (D-004, D-007) |
| FR-002 (гарантированный откат) | §4.3, TD-002 | откат в `finally`; дампы не удаляются автоматически |
| FR-003 (отчёт) | §4.4 | из `summary.json` run-каталога + `regress-report.md` |
| FR-004 (baseline-сравнение) | §4.5, TD-004 | diff статусов по ключу «сценарий+пользователь» |
| FR-005 (реестр baseline) | §4.5, D-005 | `tests/baseline/baseline.json` под git |
| FR-006 (runbook) | §4.7 | `docs/runbook.md` |
| FR-007 (веб-клиент) | §4.8, TD-006 | опционально, после GUI-вопроса; слот `--web-client` |
| FR-008 (ретро) | §9 T-ретро | задача без кода |
| NFR-001 (≤40 мин) | §4.6 | замеряется rehearsal-прогоном; дамп/откат — вне лимита, отчёт отдельно |
| NFR-002 (зонды/данные) | §6 | гейт не меняется: зонды, восстановление хэшей — уже внутри t8_gate |
| NFR-003 (надёжность) | §4.2, §8 | exit-коды, watchdog-паттерны наследуются, `finally`-откат |
| NFR-004 (usability) | §4.1 | один вход, сводка в консоль, артефакты в одном каталоге |

## 3. System Architecture

### Component Overview

| Component | Responsibility | Boundaries | Notes |
|-----------|----------------|------------|-------|
| `scripts/regress_run.py` (новый) | жизненный цикл регресса: preflight, дамп, обновление, запуск гейта, откат, отчёт, baseline | не трогает логику гейта; COM не использует (кроме опц. preflight-проверки) | единственный вход (D-004) |
| `scripts/t8_gate.py` (существующий) | E2E-прогон: генерация фич, зонды, батчи, verify, summary | вызывается подпроцессом; выход = exit code + `tests/run-*/summary.json` | в v1 без правок |
| `tests/baseline/baseline.json` (новый) | реестр baseline (D-005) | git; только сводка, без артефактов | обновляется `--set-baseline` |
| `docs/runbook.md` (новый) | инструкция администратора | — | тестируется на rehearsal |
| `tmp/regress/<ts>/` (новый, gitignored) | артефакты регресса: dt-дампы, лог фаз, regress-report.md/-summary.json | локально | дампы не авто-удаляются |

### Data / Control Flow

```mermaid
flowchart TD
    A[CLI: --rehearsal | --update path] --> B[preflight: база доступна,\nартефакт валиден, сессии?]
    B -->|fail| X[abort, код 2, база не тронута]
    B --> C[dt-дамп: 1cv8 DESIGNER /DumpIB]
    C -->|fail| X
    C --> D{--update?}
    D -->|нет: rehearsal| F
    D -->|.cf: /LoadCfg + /UpdateDBCfg| E[обновление конфигурации]
    D -->|.dt: /RestoreIB| E
    E -->|fail| R
    E --> F[t8_gate.py подпроцессом\nE2E: генерация -> зонды -> батчи -> verify]
    F --> G[откат: /RestoreIB dump.dt — В FINALLY,\nпри любом исходе]
    R[откат в finally] --> H
    G --> H[отчёт: summary.json прогона\n+ baseline-сравнение -> regress-report.md]
    H --> I[сводка в консоль + exit code]\nH -.->|опция --set-baseline| J[tests/baseline/baseline.json]
```

## 4. Implementation Design

### 4.1 CLI-контракт (D-004, D-007)

```text
python scripts/regress_run.py --rehearsal
python scripts/regress_run.py --update <path.cf | path.dt>
    [--set-baseline]        # зафиксировать прогон как baseline (только при зелёном гейте)
    [--no-compare]          # пропустить baseline-сравнение
    [--keep-dump <dir>]     # куда класть dt (по умолчанию tmp/regress/<ts>/)
    [--gate-timeout N]      # override таймаута стадии батчей (сек)
```

- Режимы `--rehearsal` / `--update` взаимоисключающие (argparse
  mutually exclusive group).
- Exit codes: `0` — гейт зелёный, регрессий нет; `1` — гейт красный
  или есть REGRESSION против baseline; `2` — инфраструктурный сбой
  (дамп/обновление/откат/preflight). База во всех случаях откачена
  (кроме abort до дампа — она и не менялась).
- Лог фаз: `tmp/regress/<ts>/regress.log` — по строке на фазу с
  длительностью (dump/update/gate/rollback/report), паттерн как в
  t8-gate.log.

### 4.2 Конвейер (FR-001)

1. **Preflight**: COM-подключение (read-only, существующий паттерн
   `conn_str`) — база отвечает; артефакт `--update` существует, размер >0,
   суффикс `.cf`/`.dt` распознан (иначе abort код 2 **до дампа**);
   свободное место на диске ≥ 2× размера базы (оценка по факту в T1);
   проверка активных сеансов — v1: попытка дампа сама падает при занятой
   базе, ошибку транслируем в понятное сообщение + инструкция убить
   сессии (runbook); T1-разведка: `rac session list` как опция.
2. **Дамп**: `1cv8 DESIGNER /S localhost\dev_erpapk_demo /N "Администратор (ОрловАВ)"`
   `/DumpIB tmp/regress/<ts>/pre-update.dt /Out dump.log` — точные флаги
   8.5.4.1683 сверяются в T1 (скил 1c-cli-ops; альтернатива ibcmd —
   только для файловых баз, нам не подходит).
3. **Обновление** (только `--update`): см. §4.3.
4. **Гейт**: `subprocess` `python scripts/t8_gate.py` — как есть
   (зонды D-001, cleanup счётчиков, ретрай rs=2, verify, summary уже
   внутри). Код возврата и `tests/run-<ts>/summary.json` — вход отчёта.
5. **Откат**: `finally`-блок — `/RestoreIB pre-update.dt`; факт отката
   подтверждается (designer `/Out`-лог + код возврата) и пишется в отчёт.
6. **Отчёт + baseline**: §4.4–4.5; консольная сводка — последняя строка
   `REGRESS <ts>: 5/5 passed, regressions=0, rollback=OK, 23.4 min`.

### 4.3 Применение «обновления» (D-007) и гарантированный откат (FR-002)

| Артефакт | Механизм | Примечание |
|----------|----------|-----------|
| `.cf` | `DESIGNER /LoadCfg <file.cf>` → `DESIGNER /UpdateDBCfg` | конфигурация БД обновляется; расширения (VA) остаются своими, но риск несовместимости расширения с новым CF — риск §15 |
| `.dt` | `DESIGNER /RestoreIB <file.dt>` | полное замещение базы («новая демо-база релиза»); откат нашим pre-update.dt после прогона — тот же механизм |

- **Откат всегда**: в `finally`, независимо от исхода гейта/обновления.
- **Дампы не удаляются автоматически**: `pre-update.dt` остаётся в
  `tmp/regress/<ts>/` до ручной чистки (runbook) — страховка от сбоя
  самого отката.
- **Rehearsal-прогон обновления без риска**: `--update` принимает
  `.dt` той же базы (снятый заранее) — полный цикл Load/Restore
  exercised безопасно; это сценарий проверки FR-002 в E2E.

### 4.4 Отчёт регресса (FR-003)

Источник — `tests/run-<ts>/summary.json` (проверено фактической
структурой: `totals {batches, scenarios, passed, failed, broken,
timeout, unknown}`, `scenarios[] {scenario, user, build, status,
durationMs, batchStatus, returnStatus}`, `batches[] {user, batch,
status, returnStatus, verdict, durationSec, passwordRestored,
zodRestored, ...}`).

Выход: `tmp/regress/<ts>/regress-report.md` (+ `regress-summary.json`):

```text
| Сценарий | Пользователь | Статус | vs baseline | Длительность |
|---|---|---|---|---|
| (Зонд1) Подключение TestClient … | АпкСценТест_Зонд1 | passed | = | 37.2s |
```

- Статусы сценария: passed / failed / broken / timeout / unknown (как в
  summary). Таблица батчей (rs, пароли, ЗОД) — вторым блоком.
- Сводные блоки: totals, факт и длительность rollback, тайминги фаз
  (dump/update/gate/rollback), путь к run-каталогу для деталей.

### 4.5 Baseline-реестр и сравнение (FR-004, FR-005, D-005)

`tests/baseline/baseline.json` (под git):

```json
{
  "baselineOf": "run-20261017-084258",
  "createdAt": "2026-10-18T...",
  "totals": {"scenarios": 5, "passed": 5, "failed": 0},
  "scenarios": [{"scenario": "...", "user": "...", "status": "passed"}],
  "runDir": "tests/run-20261017-084258",
  "comment": "после релиза-репетиции 17.10"
}
```

- Ключ сравнения: `(scenario, user)`. Статусы: passed/failed/broken/
  timeout/unknown.
- Классы diff: `REGRESSION` (pass→fail/broken/timeout), `IMPROVED`
  (fail→pass), `NEW` (нет в baseline), `MISSING` (есть в baseline,
  нет в прогоне), `=` (без изменений).
- `--set-baseline`: перезаписывает `baseline.json` текущим прогоном —
  только если гейт зелёный; предыдущий baseline переносится в
  `tests/baseline/history/<ts>.json` (история, тоже git).
- Нет baseline или `--no-compare`: колонка vs baseline = `n/a`,
  пометка «нет baseline» в отчёте (требование US-003).

### 4.6 Производительность (NFR-001)

- E2E-часть ≤40 мин (фактически 12.7–18.3 мин). Дамп/откат — отдельные
  строки тайминга, в лимит не входят (замеряются в rehearsal; при
  неприлично долгом дампе — пересмотр цели с пользователем).
- Все таймауты — с watchdog-паттерном t8_gate (kill-tree), плюс
  таймаут на dump/restore/update (T1 подбирает по факту размера базы).

### 4.7 Runbook (FR-006)

`docs/runbook.md`: подготовка (что такое артефакт обновления, где
взять CF/dt релиза), запуск (обе команды + флаги), чтение отчёта
(расшифровка статусов и REGRESSION), действия при сбоях (abort до
дампа, красный гейт, сбой отката — где лежит pre-update.dt и как
восстановить руками `/RestoreIB`), ручная чистка дампов, ограничения
(зонды, демо-данные, статичный период окт-2026, веб-клиент).

### 4.8 Веб-клиент (FR-007, TD-006 / D-006)

- Слот в `regress_run.py`: флаг `--web-client` → модифицирует
  preprocessor-settings/VAParams (ТипКлиента=web) перед stage-A —
  реализуется ТОЛЬКО после: (а) веб-публикации `dev_erpapk_demo`
  (скил web-publish, Apache), (б) preflight-вопроса пользователю о
  интерактивной сессии (GUI). При headless — откладывается, фиксация
  здесь: **v1 спеки 003 идёт тонким клиентом, веб-клиент = отдельная
  задача с явным флагом готовности**.

## 5. Integration Points

| System | Purpose | Auth / Permissions | Failure Handling |
|--------|---------|--------------------|------------------|
| 1cv8 DESIGNER batch | дамп/откат/обновление | `/N Администратор (ОрловАВ)`, без пароля | ненулевой код → транслируем в сообщение фазы; abort/rollback |
| t8_gate.py (subprocess) | E2E | внутренние механизмы гейта | exit≠0 → код 1, отчёт по summary.json |
| COM-коннектор | preflight (read-only) | как в t8_gate | недоступна → abort код 2 |
| rac/ras (опционально, T1) | список/kill сессий перед RestoreIB | cluster admin | v1: только диагностика, kill — руками по runbook |
| Apache (отложено) | веб-публикация для --web-client | — | D-006 |

## 6. Security / Permissions / Privacy

- **Пользователи прогона**: только временные зонды (D-001 спеки 002) —
  логика целиком внутри t8_gate, не дублируется.
- **Хэши паролей**: восстановление — внутри гейта; обёртка не работает
  с паролями пользователей вообще.
- **Данные**: dt-дампы содержат данные демо-базы → `tmp/` (gitignored),
  предупреждение в runbook «не коммитить и не выносить из машины».
- **COM**: preflight — read-only, существующий безопасный паттерн.
- **Реальные данные 2015–2023**: не затрагиваются (откат гарантирует).

## 7. UX / Accessibility

Не применимо (CLI-инструмент + markdown-отчёт). Консольная сводка —
последняя строка с вердиктом; все детали — в файлах.

## 8. Edge Cases

| Case | Expected Behavior |
|------|-------------------|
| Артефакт `--update` не существует / неизвестный суффикс | abort код 2 ДО дампа, база не тронута |
| База недоступна (COM preflight) | abort код 2 |
| Занятая база (активные сессии) при dump/restore | ошибка дизайнера → понятное сообщение «завершите сессии» (runbook), abort/rollback |
| Дамп упал | abort код 2, база не менялась |
| Обновление упало | откат в finally, код 2, в отчёте фаза=update FAILED |
| Гейт красный (rs≠0) | откат, отчёт с FAIL-строками, код 1 |
- `--set-baseline` при красном гейте | отказ: «baseline не обновлён» (код 1 сохраняется) |
| Baseline пуст/отсутствует | колонка vs = `n/a`, пометка «нет baseline» |
| Сценарий переименован между прогонами | NEW + MISSING (ложная пара) — FAQ §16: ключ сценарий+user, переименование = ручной разбор |
| Сбой самого отката (restore) | КОД 2, ГРОМКО в консоли: путь к pre-update.dt + команда ручного восстановления; дамп не удалялся |
| Нет места на диске | preflight abort (≥2× базы свободно; порог уточняет T1) |

## 9. Development Sequencing

1. **T1 — разведка CLI**: точные флаги 8.5.4 DESIGNER batch для
   DumpIB/RestoreIB/LoadCfg/UpdateDBCfg на серверной базе; поведение при
   активных сессиях; размер базы и время дампа; утилита rac для списка
   сессий. Без кода конвейера (только probe-скрипт).
2. **T2 — `regress_run.py` скелет**: preflight + rehearsal-режим
   (дамп → гейт → откат) + лог фаз + exit-коды.
3. **T3 — путь обновления**: `.cf` и `.dt` ветки §4.3.
4. **T4 — отчёт + baseline**: §4.4–4.5, `--set-baseline`, history.
5. **T5 — E2E-доказательство**: rehearsal на dev_erpapk_demo (полный
   цикл, rollback OK, отчёт, evidence-файл); при зелёном — `--set-baseline`
   фиксирует эталон.
6. **T6 — runbook**: docs/runbook.md по фактическим командам T2–T5.
7. **T7 — веб-клиент (опционально/отложено)**: preflight-вопрос GUI →
   публикация → `--web-client`; иначе — фиксация откладывания здесь.
8. **T8 — ретро релиза 2**: обсуждение с пользователем + PLAN.md.

## 10. Testing / Verification Strategy

- **T5 rehearsal (главный E2E)**: `--rehearsal` на dev_erpapk_demo →
  гейт 5/5 rs=0, rollback=OK (подтверждение дизайнером + повторный
  COM-preflight), regress-report.md с «нет baseline», тайминги фаз.
- **Путь обновления**: `--update <dt-этой-же-базы>` (безопасная
  репетиция) → update OK → гейт → откат к pre-update.dt.
- **Отказоустойчивость**: несуществующий путь (abort до дампа), битый
  cf (abort + rollback), `--set-baseline` при красном (отказ).
- **Baseline-сравнение**: два rehearsal-прогона: первый `--set-baseline`,
  второй — ожидаем 0 регрессий (все `=`); юнит-проверка диффа на
  синтетических summary (passed→failed = REGRESSION и т.д.) — быстрый
  py-тест без базы.
- **Project verification**: `python scripts/pre_load_validate.py` n/a
  (нет правок XML/BSL — гейт и EPF не меняются); bsl-ls — n/a по той же
  причине; проверка — фактические прогоны T5.

## 11. Observability / Operations

- Логи: `tmp/regress/<ts>/regress.log` (фазы, длительности, коды),
  дизайнеровские `/Out`-логи рядом; гейт-логи — в `tmp/t8/` (как есть).
- Отчёт: regress-report.md + regress-summary.json (машинный формат для
  будущих интеграций).
- Heartbeat: `tmp/t9/heartbeat.txt` (существующая дисциплина).

## 12. Migration / Rollout

- Не применимо: новые файлы только добавляются (`scripts/regress_run.py`,
  `tests/baseline/`, `docs/runbook.md`); существующие скрипты/EPF не
  меняются. Rollback = не пользоваться командой; следы — tmp/ (gitignored).

## 13. Technical Decisions

### TD-001: Обёртка, а не модификация гейта

- **Decision:** `regress_run.py` вызывает `t8_gate.py` подпроцессом;
  гейт в v1 не правится.
- **Why:** разделение ответственности (гейт = тест-ран, обёртка =
  data-lifecycle); гейт уже доказан E2E дважды; правки гейта = ре-гейт.
- **Trade-off:** обмен данными через файлы/exit-код, не через импорт.
- **Alternatives:** флаг `--regress` внутри t8_gate (скилл-промт
  предлагал) — отвергнуто: смешение жизненных циклов, риск сломать
  доказанный гейт.

### TD-002: dt-дамп/откат через DESIGNER batch

- **Decision:** `1cv8 DESIGNER /DumpIB` / `/RestoreIB` (серверная база;
  ibcmd неприменим, COM-дампа нет).
- **Why:** единственный штатный пакетный путь для серверной ИБ.
- **Trade-off:** требует отсутствия активных сессий на restore; время
  дампа неизвестно до T1.
- **Alternatives:** резервное копирование PostgreSQL на уровне СУБД —
  отвергнуто (продукт-граница: без прямого доступа к СУБД, steering).

### TD-003: Ключ baseline = (сценарий, пользователь)

- **Decision:** сравнение по паре имя сценария + пользователь-зонд.
- **Why:** пользователь — часть контракта прогона (права влияют на
  результат); имя сценария стабильно (генератор эмитит из шаблона).
- **Trade-off:** переименование шаблона = NEW+MISSING ложная пара.
- **Alternatives:** только имя сценария — теряется ось пользователя.

### TD-004: Дампы не удаляются автоматически

- **Decision:** pre-update.dt остаётся до ручной чистки.
- **Why:** страховка от сбоя отката; диск дешевле данных.
- **Trade-off:** tmp/ растёт; чистка — в runbook.

### TD-005: Rehearsal через dt той же базы

- **Decision:** безопасная репетиция пути обновления — `--update
  <dt-этой-же-базы>`.
- **Why:** exercises Load/Restore без риска (данные идентичны).
- **Trade-off:** не моделирует semantic-эффекты реального релиза.

### TD-006: Веб-клиент — слот, не блокер (D-006)

- **Decision:** `--web-client` проектируется, реализуется после GUI-вопроса
  и публикации; v1 — тонкий клиент.
- **Why:** headless-риск; Apache — внешняя зависимость.
- **Trade-off:** FR-007 может остаться отложенным (допустимо по
  критериям готовности спеки).

## 14. Known Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| RestoreIB требует монопольного доступа — чужие сессии | Medium | High | preflight-сообщение + runbook (kill сессий руками); T1: rac-диагностика |
| CF-обновление несовместимо с расширением VA (объекты исчезли) | Low-Med | High | abort на этапе update + откат; runbook: «проверить расширения после релиза» |
| Время dt-дампа велико (размер демо-базы неизвестен до T1) | Medium | Medium | замер T1; таймаут с watchdog; тайминги в отчёте |
| Долгий полный цикл (дамп+гейт+откат) в рабочие часы | Medium | Medium | runbook: запускать в тихие окна; rehearsal — ориентир времени |
| Ложные REGRESSION из-за flaky (rs=2 ретраится внутри гейта, но не всё) | Medium | Medium | ретрай stage-b уже в гейте; в отчёте пометка flaky-кандидатов (повтор batches) — v1 вручную |
| Переименование сценариев → NEW+MISSING | Low | Low | FAQ + ручной разбор; при смене шаблонов — обновить baseline |

## 15. Implementation FAQ

**Q:** Почему подпроцесс, а не `import t8_gate`?  
**A:** t8_gate написан как скрипт с main(); импорт потянул бы его
глобальные сайд-эффекты. Подпроцесс + exit-код + summary.json — самый
дешёвый и стабильный контракт (TD-001).

**Q:** Где гарантия, что отчёт не потеряется при сбое отката?  
**A:** regress-report.md пишется ПОСЛЕ отката; при сбое отката отчёт
всё равно пишется (фаза rollback=FAILED) — код 2 и ГРОМКОЕ сообщение.

**Q:** Что если гейт оставил мусор (зонды не удалены)?  
**A:** Внутри гейта есть finally-восстановление и verify; обёртка не
дублирует, но отчёт отражает passwordRestored/zodRestored из batches.

**Q:** Можно ли гонять `--rehearsal` без дампа (быстрый прогон)?  
**A:** Нет — rehearsal по определению доказывает безопасность цикла.
Быстрый прогон без жизненного цикла = `python scripts/t8_gate.py`
напрямую (существующая команда, runbook упоминает).

**Q:** `--update <dt>` перезапишет базу целиком — где мои данные?  
**A:** Да, это семантика «новой демо-базы релиза»; pre-update.dt снят
до обновления и восстанавливается в finally — данные вернутся в любом
исходе (TD-004: дамп остаётся на диске).

**Q:** Почему baseline не в run-каталоге?  
**A:** run-каталоги gitignored и растут; baseline — переносимый эталон
в git (D-005), ссылается на run-каталог только как на деталь.

## 16. Open Questions

- Точные флаги DESIGNER batch 8.5.4 для серверной ИБ — закрываются
  разведкой T1 (1c-cli-ops: `/DumpIB`, `/RestoreIB`, `/LoadCfg`,
  `/UpdateDBCfg`).
- Время и размер dt-дампа dev_erpapk_demo — замер T1 (влияет на
  тайминги и preflight-порог места).
- Веб-клиент: интерактивная ли сессия для Apache-публикации —
  preflight-вопрос перед T7 (D-006).
