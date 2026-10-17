# Tasks: Сценарии растениеводства (спека 002)

> Requirements: @requirements.md
> Design: @design.md
> Status: Approved (2026-10-15, «продолжи» = согласие с представленным планом; отклонения — по запросу)

## Requirement Coverage

| Requirement | Tasks | Notes |
|-------------|-------|-------|
| FR-001 (02-pl-auto) | T1, T2, T9 | шаблон + экстрактор |
| FR-002 (04-fuel-sheet) | T1, T3, T9 | самый простой шаблон |
| FR-003 (05-weighing) | T1, T4, T9 | талоны/серии |
| FR-004 (arm-*) | T7, T8, T9 | разведка до шаблонов (TD-003) |
| FR-005 (наряды) | T5, T6, T9 | сопоставление авторов (TD-004) |
| FR-006 (достаточность) | T1 | критерий D-013 |
| FR-007 (отчёт) | T9 | код не меняется, проверка |
| FR-008 (N=3) | T1 | D-002 |
| NFR-001 (≤40 мин) | T9 | замер полного цикла |
| NFR-002 (безопасность) | T1–T9 | режим зондов D-001; беcопасность arm-* (design §7) |

## Implementation Readiness Check

| Check | Status | Notes |
|-------|--------|-------|
| Must Have требования покрыты задачами | Pass | FR-001..003, FR-006..008 |
| Требования покрыты дизайном | Pass | design §2 |
| Критические Questions отвечены | Pass | Q-001..Q-003 → D-001..D-002, FR-005 |
| Задачи имеют зависимости, AC, файлы, верификацию | Pass | ниже |
| Верификация известна | Pass | probe-раннеры + t8_gate + гейты bsl-ls/v8std |

## Implementation Slices

### MVP Slice

- **Goal:** Шаблоны трёх простых документов (авто ПЛ, заправочная ведомость,
  взвешивание) стабильны в probe и включены в полный цикл.
- **User Stories:** US-001, US-002, US-003, US-005
- **Tasks:** T1 → T2, T3, T4 → T9
- **Independent validation:** полный цикл с 3 новыми шаблонами, все батчи rs=0

## Task T1: Экстрактор фикстур: полный состав ТЧ, N=3, производные поля

**Priority:** P0 · **Estimate:** 2h · **Dependencies:** none · **Covers:** FR-006, FR-008

### Work
- [x] `tests/coverage-map.json`: fieldList.tabular для АпкПутевойЛистАвтотранспорта,
      АпкЗаправочныеВедомости, АпкРегистрацияВзвешиванийНаТоку — полный состав
      колонок, нужных шаблонам (сверка с Form.xml каждого)
- [x] `src/.../ObjectModule.bsl`: ограничение строк ТЧ → 3 (D-002)
- [x] Производные поля для новых типов: `ТипЗатратСписок` (valueMaps),
      `АналитикаРасходовТекущий` (если у типа есть колонка Аналитика)
- [x] Гейты: bsl-ls + v8std; пересборка `scripts/build_t6.py`

### Acceptance Criteria
- [x] fixtures.json: у всех трёх типов полные ТЧ-структуры (3 строки max),
      производные поля присутствуют/отсутствуют корректно по типам
      (доказано прогоном `tests/run-20261015-100446/`; NB: N=3 и производные
      поля уже были генеричными в коде спеки 001 — правка потребовалась
      только данным карты: колонки 02-ПЛавто + valueMaps + Спидометры;
      попутно исправлен латентный баг `Метаданные().Имя()` ×2, срывавший
      формирование фикстур на новых представителях)

### Files
- `tests/coverage-map.json`, `src/АпкПодготовкаСценарныхТестов/Ext/ObjectModule.bsl`

### Verification
- [ ] Stage-a прогон (t8_gate или временный runner): fixtures.json проверен
- [ ] bsl-ls 0 Error; v8std критичные замечания исправлены

## Task T2: Шаблон 02-pl-auto + probe
**Priority:** P0 · **Estimate:** 2h · **Dependencies:** T1 · **Covers:** FR-001

### Work
- [x] `tests/templates/02-pl-auto.feature`: по playbook 01-pl-tractor
      (e1cib/data, dropdown «по строке», ТипЗатрат «с выбором» при наличии,
      UIA-двойной клик для Аналитики если колонка есть)
- [x] Проверка Form.xml: наличие/отсутствие Аналитика Расходов у
      автотранспортного ПЛ (design §3.1)
- [x] Probe-раннер `scripts/s2_probe*_run.py` (образец t8_probe6m2_run.py,
      порты 487xx, флаги: Мышки=Ложь)
- [x] Итерации probe до стабильного ReturnStatus=0

### Acceptance Criteria
- [x] Probe rs=0; шаблон генерирует фичу без unresolved-плейсхолдеров
- [x] Фича проводит документ-представителя

### Files
- `tests/templates/02-pl-auto.feature`, `scripts/s2_probe_plauto_run.py`

### Verification
- [x] Probe-прогон ReturnStatus=0 (два раза подряд)

## Task T3: Шаблон 04-fuel-sheet + probe
**Priority:** P0 · **Estimate:** 1h · **Dependencies:** T1 · **Covers:** FR-002

### Work
- [x] `tests/templates/04-fuel-sheet.feature`: шапка + ТЧ ГСМ по образцу
      (dropdown МаркаТоплива, Количество)
- [x] Probe-раннер + итерации до rs=0

### Acceptance Criteria
- [x] Probe rs=0; документ проводится

### Files
- `tests/templates/04-fuel-sheet.feature`, `scripts/s2_probe_fuel_run.py`

### Verification
- [x] Probe-прогон ReturnStatus=0 (два раза подряд: run10, run11)

## Task T4: Шаблон 05-weighing + probe
**Priority:** P0 · **Estimate:** 1h · **Dependencies:** T1 · **Covers:** FR-003

### Work
- [x] `tests/templates/05-weighing.feature`: шапка (ВидВзвешивания dropdown,
      Откуда/Куда, Номенклатура) + ТЧ Талоны
- [x] Проверить: вводится ли «Откуда» стандартным dropdown «по строке»
      (если форма выбора как у Аналитики — UIA-рецепт, design §3.3)
      [dropdown «по строке» НЕ работает — UIA-рецепт]
- [x] Probe-раннер + итерации до rs=0

### Acceptance Criteria
- [x] Probe rs=0; документ проводится

### Files
- `tests/templates/05-weighing.feature`, `scripts/s2_probe_weighing_cleanup.py`

### Verification
- [x] Probe-прогон ReturnStatus=0 (два раза подряд: run12, run13)

## Task T5: Наряды: сопоставление авторов (research)
**Priority:** P1 · **Estimate:** 1h · **Dependencies:** none · **Covers:** FR-005 (TD-004)

### Work
- [x] COM read-only (V85, timeout, отдельный процесс): авторы 28 нарядов,
      их `Пользователи.ИдентификаторПользователяИБ` → существующие ИБ-пользователи
- [x] Найти наряд с сопоставленным автором → кандидат в представители;
      если нет — документировать и пометить FR-005 отклоняемым
- [x] При успехе: представитель наряда в плане (расширение селектора —
      проверить, нужен ли правка селектора, или он уже покрывает 5-й тип)

### Acceptance Criteria
- [x] Ответ: сопоставим ли наряд с автором-пользователем ИБ (да/нет + данные)
- [x] При «да»: представитель зафиксирован в fixtures.json прогонa

### Files
- `scripts/s2_narjad_diag.py`, `tmp/s2/PROGRESS.md`

### Verification
- [ ] COM-диагностика выполнена; вывод зафиксирован в PROGRESS

## Task T6: Шаблон 03-piecework + probe
**Priority:** P1 · **Estimate:** 1h · **Dependencies:** T5 (успех) · **Covers:** FR-005

### Work
- [x] `tests/templates/03-piecework.feature`: шапка (Исполнитель) +
      ТЧ Задание (ВидРаботы, Часы/Тонны/Гектары, ТипЗатрат «с выбором»,
      Аналитика по Form.xml)
- [x] Probe-раннер + итерации до rs=0
- [ ] При провале T5 (нет сопоставимого автора): задача отменяется,
      фиксация в отчёте [неактуально: T5 успешен]

### Acceptance Criteria
- [x] Probe rs=0; документ проводится

### Files
- `tests/templates/03-piece-work-order.feature` (шаблон = 03-piece-work-order
  по coverage-map), `scripts/s2_probe_fuel_run.py` (probe-раннер)

### Verification
- [x] Probe-прогон ReturnStatus=0 (два раза подряд: run19, run20)

## Task T7: АРМ: разведка форм отражения (research)
**Priority:** P1 · **Estimate:** 2h · **Dependencies:** none · **Covers:** FR-004 (TD-003)

### Work
- [x] По исходникам APKModSrc: формы АРМ (ВыработкиСотрудников /
      РасходаТоплива / ЗаправокТоплива) — открытие, кнопки, что отражают,
      в чём результат
- [x] Пробное открытие формы под админом (probe «открылась форма») —
      только чтение
- [x] Вывод: перечень возможных шагов и решение, какие arm-шаблоны пишем;
      если механика несовместима с probe-first — отклонение FR-004
      с пояснением

### Acceptance Criteria
- [x] Зафиксировано: механика отражения, возможные шаги, безопасность
      (design §7), список реализуемых arm-шаблонов

### Files
- `tmp/s2/PROGRESS.md`, `tmp/s2/arm-research.md`

### Verification
- [x] Сводка в PROGRESS; решение по FR-004

## Task T8: arm-* шаблоны + probe
**Priority:** P1 · **Estimate:** 2h · **Dependencies:** T7 · **Covers:** FR-004

### Work
- [x] arm-payroll, arm-fuel-expense, arm-fuel-receipt по итогам T7;
      отражаем только копии документов (design §7)
- [x] Probe-раннеры; итерации до rs=0

### Acceptance Criteria
- [x] Каждый arm-шаблон стабилен в probe (или отклонён по T7 — задокументировано)
  (arm-fuel-receipt и arm-payroll: rs=0 ×2; arm-fuel-expense — отклонён: данные
  АРМ формируют только закрытые ПЛ (статус 3), фикстуры 04-fuel-sheet на статусе 2,
  задокументировано в header шаблона и tmp/t9/arm-rashod/)

### Files
- `tests/templates/arm-*.feature`, `scripts/s2_probe_arm*_run.py`

### Verification
- [x] Probe-прогоны ReturnStatus=0 (два раза подряд)
  (arm-fuel-receipt: va_status=0 run1+run2; arm-payroll: va_status=0 run7+run8)

## Task T9: Полный цикл + AC + отчёт
**Priority:** P0 · **Estimate:** 2h · **Dependencies:** T2, T3, T4, T6/T8 (или их отклонения) · **Covers:** FR-007, NFR-001, US-005

### Work
- [x] Расширить манифест/ограничение батчей: новые шаблоны включаются
      в прогон зондов (D-001: реальных авторов НЕ подключаем)
- [x] Полный цикл: все батчи rs=0, пароли/ЗОД восстановлены, сирот нет
- [x] NFR-001: замерить длительность полного цикла (цель ≤40 мин) — 18.3 мин
- [x] summary.json/md: все сценарии спеки видны в отчёте
- [x] Чекбоксы tasks.md; отчёт `docs/night-report-<date>.md`;
      обновить handoff/next-session-prompt

### Acceptance Criteria
- [x] Все включённые батчи ReturnStatus=0 (runId 20261017-060711: batch1 rs=0 124s,
      batch2 rs=0 255s; 4/4 сценария passed)
- [x] summary.md «passed»; пароли исходные работают
- [x] Длительность ≤40 мин (или зафиксированное объяснение) — 1099 с ≈ 18.3 мин
- [x] Все отклонённые шаблоны (если есть) задокументированы в отчёте
      (arm-fuel-expense — отклонён: закрытые ПЛ, диагностика tmp/t9/arm-rashod/)

### Files
- `scripts/s2_gate.py` (или расширение `t8_gate.py`), отчёты в `docs/`

### Verification
- [x] Run-каталог: журнал + summary + allure; heartbeat-записи
      (tests/run-20261017-060711/, tmp/t9/gate-run/EVIDENCE.md — 32/32 checks OK)
