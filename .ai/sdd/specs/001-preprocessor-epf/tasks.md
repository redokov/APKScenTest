# Tasks: 001 — Обработка `АпкПодготовкаСценарныхТестов`

> Requirements: @requirements.md
> Design: @design.md
> Status: Approved (делегировано пользователем 2026-10-11: «продолжай дальше самостоятельно»)
> Last Updated: 2026-10-11

## Requirement Coverage

| Requirement | Tasks | Notes |
|-------------|-------|-------|
| FR-001 | T3 | сканер без ограничения дат |
| FR-002 | T4 | fixtures.json по fieldList |
| FR-003 | T3 | ИдентификаторПользователяИБ |
| FR-004 | T3, T4 | план покрытия + подтверждение |
| FR-005 | T5 | генератор + текущий месяц |
| FR-006 | T6 | хэш + finally |
| FR-007 | T6 | ReturnStatus, таймаут, kill-tree |
| FR-008 | T7 | сводка |
| FR-009 | T6, T7 | частичный сбой |
| FR-010 | T6 | ЗОД (open Q → закрыть в T6) |
| FR-011 | T4 | исключение шаблонов в плане |
| FR-012 | T4, T7 | run-каталоги |
| FR-015 | T2, T3 | coverage-map arms |
| FR-016 | T2, T3 | селектор по осям |
| NFR-001 | T1, T6 | проверка админа, секреты |
| NFR-002 | T6 | верификация хэшей |
| NFR-003 | T6 | таймауты настраиваемые |
| NFR-004 | T2 | настройки файлом |
| NFR-005 | все | гейты в каждом task |
| US-001..003 | T8 | E2E |

## Design Coverage Check

| Requirement | Design Coverage | Status |
|-------------|-----------------|--------|
| FR-001..016 | design §4.1–4.9, §3.3 | Pass |
| NFR-001..005 | design §6, §11, §4.6, §4.7, §4.10 | Pass |

## Implementation Readiness Check

| Check | Status | Notes |
|-------|--------|-------|
| Must Have requirements have tasks | Pass | все FR Must покрыты |
| Tasks map to requirements/design | Pass | |
| Critical Questions answered | Pass | Q-001..005 answered; open Q дизайна закрыть в T2/T6 |
| Tasks have deps/AC/files/verification | Pass | |
| Verification commands identified | Pass | bsl-ls, v8std, epf-build, compile-gate, COM-прогоны |
| No blocking gaps | Pass | |

## Implementation Slices

- **MVP**: T1–T4 — скан → план → fixtures (проверяется COM-вызовами без VA).
- **Прогон**: T5–T6 — feature + VA-батч с паролями.
- **Отчёт/E2E**: T7–T8.

## Task Summary

| Task | Title | Priority | Estimate | Dependencies | Status |
|------|-------|----------|----------|--------------|--------|
| T1 | Scaffold EPF + гейт-пайплайн | P0 | 1h | none | done |
| T2 | coverage-map.json + settings + gitignore | P0 | 1h | none | done |
| T3 | Сканер + селектор + сопоставление пользователей | P0 | 3h | T1, T2 | done |
| T4 | Экстрактор fixtures.json + план покрытия | P0 | 2h | T3 | done |
| T5 | Шаблоны feature + генератор | P1 | 2h | T4 | done |
| T6 | Менеджер паролей + раннер VA | P0 | 4h | T5 | done |
| T7 | Репортёр + сводка | P1 | 2h | T6 | done |
| T8 | E2E smoke полного цикла | P1 | 2h | T7 | done |
| T9 | Отчёт ночи + handoff + docs | P2 | 1h | T8 | done |

## Task T1: Scaffold EPF + гейт-пайплайн

**Priority:** P0 · **Estimate:** 1h · **Dependencies:** none · **Covers:** NFR-001, NFR-005 (enable)

### Work
- [x] epf-init scaffold: `src/AпкПодготовкаСценарныхТестов/` (ObjectModule + Форма)
- [x] Проверка прав администратора при открытии формы (отказ не-админу)
- [x] Настройки: чтение `preprocessor-settings.json` в форму

### Acceptance Criteria
- [x] epf-build собирает EPF; compile-gate (Подключить + ПолучитьФорму) проходит
- [x] bsl-ls `bsl_analyze` ≠ «0 файлов», 0 синтакс-ошибок; v8std без критичных

### Files
- `src/AпкПодготовкаСценарныхТестов/**` — create

### Verification
- [x] `epf-build` (скил) → EPF на диске
- [x] COM: ПодключитьВнешнююОбработку + ПолучитьФорму без исполнения

### Notes
Проверка админа: `Пользователи.ЭтоПолноправныйПользователь()` ERP или
`ПравоДоступа("Администрирование")` — выбрать по факту (ERP-модуль Пользователи есть в базе).

## Task T2: coverage-map.json + settings + gitignore

**Priority:** P0 · **Estimate:** 1h · **Dependencies:** none · **Covers:** FR-015, FR-016, NFR-004

### Work
- [x] `tests/coverage-map.json`: 5 документов — fieldList (по fixture-model + tmp/doc_attrs.md), axes (по §3.4 дизайна), arms (по §3.4 + when-условия)
- [x] `tests/preprocessor-settings.json`: база, пути 1cv8c/VA, каталоги, таймауты, порты
- [x] `.gitignore`: `tests/run-*/`
- [x] Верификация цепочки «наряд → АпкРучныеРаботыПоФакту → АРМ ВыработкиСотрудников» (модуль проведения наряда; если не подтверждается — пометка в карте `verified:false`)

### Acceptance Criteria
- [x] JSON обоих файлов валиден (`python -c json.load`)
- [x] Все значения осей — реальные значения перечислений (tmp/enums.md)

### Files
- `tests/coverage-map.json`, `tests/preprocessor-settings.json`, `.gitignore`

### Verification
- [x] `python -c "import json; json.load(...)"` × 2

## Task T3: Сканер + селектор + сопоставление пользователей

**Priority:** P0 · **Estimate:** 3h · **Dependencies:** T1, T2 · **Covers:** FR-001, FR-003, FR-016, FR-004 (план)

### Work
- [x] Серверный модуль: `СканироватьДокументы(Настройки, Фильтры)` — объединение по 5 типам (проведённые), фильтры опциональны
- [x] `ОтобратьПредставителей(Найденные, Карта)` — группировка по осям, первый по МоментуВремени, coverageGaps
- [x] `СопоставитьПользователей(Представители)` — Автор → ИдентификаторПользователяИБ → ПользовательИБ (имя, ПарольУстановлен, заблокирован)
- [x] Форма: ТЧ представители, ТЧ пользователи, предупреждения

### Acceptance Criteria
- [x] COM-вызов `СканироватьДокументы` на dev_erpapk_demo возвращает представителей и coverageGaps; результат сериализован в файл для проверки
- [x] Авторы сопоставлены; несопоставленные помечены

### Files
- `src/.../Ext/ObjectModule.bsl`, `src/.../Forms/Форма/Ext/Form/Module.bsl`, Form.xml (ТЧ)

### Verification
- [x] bsl-ls + v8std; compile-gate; COM-прогон функции с дампом результата в tmp/ (прогон через гейт-раннер-EPF — COM в 8.5.4 не работает с Подключить)

## Task T4: Экстрактор fixtures.json + план покрытия

**Priority:** P0 · **Estimate:** 2h · **Dependencies:** T3 · **Covers:** FR-002, FR-004, FR-011, FR-012

### Work
- [x] `СформироватьФикстуры(Представители, Карта)` — шапка + ≤3 строк ТЧ по fieldList; представления+UUID; без дат (ввод текущим месяцем)
- [x] `ПостроитьПланПрогона(...)` — пользователь × шаблон × документ × АРМ (arms.when по осям); armPlan + users[].scenarios
- [x] run-каталог `tests/run-<id>/` + `fixtures.json` (UTF-8, ЗаписьJSON)

### Acceptance Criteria
- [x] fixtures.json на диске, валиден, содержит coverage/armPlan/users/documents по контракту §3.2

### Verification
- [x] COM-прогон → `python json.load` + сверка ключей с §3.2 (гейт-раннер-EPF вместо COM; scripts/t4_verify.py, tmp/t4/verify.md: 78 проверок, 0 FAIL)

## Task T5: Шаблоны feature + генератор

**Priority:** P1 · **Estimate:** 2h · **Dependencies:** T4 · **Covers:** FR-005

### Work
- [x] Шаблоны: `00-smoke.feature` (эталон), `01-pl-tractor.feature` (ввод/проведение ПЛ тракториста из фикстур)
- [x] `СгенерироватьФичи(План, Фикстуры)` — плейсхолдеры `{{path}}`, имена форм из синонимов метаданных, датa текущим месяцем; файл на (пользователь × шаблон)

### Acceptance Criteria
- [x] В сгенерированных файлах нет незамещённых `{{`, имена форм совпадают с синонимами метаданных

### Verification
- [x] Ком-прогон генератора → grep `{{` = 0 совпадений; smoke-фича синтаксически валидна (прогон в T6)

## Task T6: Менеджер паролей + раннер VA

**Priority:** P0 · **Estimate:** 4h · **Dependencies:** T5 · **Covers:** FR-006, FR-007, FR-009, FR-010, NFR-002, NFR-003

### Work
- [x] `ПодменитьПароль(ПользовательИБ)` / `ВосстановитьПароль(...)` — хэш+алгоритм, верификация восстановления
- [x] `ВыполнитьБатч(...)` — VAParams (ReturnStatus-файл, allure base/<user>, ЗОД), запуск WScript.Shell.Exec, таймаут, taskkill /T /F; ДиапазонПортовTestclient per-batch + зачистка осиротевших TestClient (-TPort <порт>)
- [x] Цикл батчей: подмена → батч → восстановление (finally-семантика) → следующий; таймаут/сбой не рушат остальные
- [x] Закрыть open Q: имя параметра ЗОД (JsonParamsRU.md / настройки VA) — параметра VAParams нет; ЗОД отключается per-user (TD-009)
- [x] Удаление VAParams-файлов после батча

### Acceptance Criteria
- [x] Батч smoke-фичи под тестовым пользователем: ReturnStatus=0, allure result.json на месте, хэш восстановлен (вход под исходным паролем — ок, тестовый — отвергнут)
- [x] Тест таймаута: искусственно малый таймаут → kill-tree, статус timeout, хэш восстановлен, цикл продолжился

### Verification
- [x] bsl-ls + v8std; compile-gate; гейт-раннер-EPF циклы A/B с дампами в tmp/t6/ (COM в 8.5.4 мёртв)

## Task T7: Репортёр + сводка

**Priority:** P1 · **Estimate:** 2h · **Dependencies:** T6 · **Covers:** FR-008, FR-009, FR-012

### Work
- [x] `СобратьОтчет(RunКаталог)` — ReturnStatus батчей + allure result.json + fixtures → summary.json/md (сценарий×пользователь×статус, покрытие, АРМы, gaps, пароли)
- [x] Отображение в форме (ТЧ отчёта)

### Acceptance Criteria
- [x] summary.json валиден и содержит статусы всех батчей прогона T6

### Verification
- [x] COM-прогон на артефактах T6; python-сверка структуры

## Task T8: E2E smoke полного цикла

**Priority:** P1 · **Estimate:** 2h · **Dependencies:** T7 · **Covers:** US-001..003, NFR-005

### Work
- [x] Полный цикл на dev_erpapk_demo: скан → план (≥1 пользователь, ≥1 тип документа) → генерация → батчи (smoke + сценарий ввода документа) → отчёт
- [x] Проверка: восстановление паролей всех пользователей плана, артефакты run-каталога

### Acceptance Criteria
- [x] ReturnStatus=0 на батчах; summary.md с «passed»; пароли исходные работают

### Verification
- [x] Журнал прогона + summary в run-каталоге; фиксация в отчёте ночи

## Task T9: Отчёт ночи + handoff + docs

**Priority:** P2 · **Estimate:** 1h · **Dependencies:** T8 · **Covers:** enabling

### Work
- [x] `.ai/sdd/handoff/sdd-brief.md`
- [x] Отчёт ночи: `docs/night-report-2026-10-15.md` (сделано/решения/тесты/остаток)
- [x] INDEX.md, next-session-prompt.md — актуализация

## Completion Rules

- Не помечать task выполненным без верификационных доказательств (логи/файлы в tmp/, run-каталоги).
- Гейты bsl-ls + v8std — после каждой правки BSL, до загрузки в базу.
- Если обнаружится разрыв требований/дизайна — остановиться и зафиксировать в отчёте (правки артефактов — с пометкой делегированного утверждения).
