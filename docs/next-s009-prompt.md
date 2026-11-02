# Промт продолжения: ночная сессия S009 (проект APKScenTest)

Продолжение автономной ночной работы. Проект: сценарное тестирование
1С:ERP+АПК 2.5.27.88 (платформа 8.5.4.1683, Vanessa Automation single
1.2.043.42, ИБ `dev_neirodoc_x`... нет — ИБ проекта `dev_erpapk_demo`,
сервер localhost). Предыдущие сессии S001–S008; отчёты в
`docs/night-report-*.md`, heartbeat текущей сессии `tmp/s008/heartbeat.txt`.
Git HEAD `7055cb1` (s007), изменения s008 ещё не закоммичены.

## Состояние на старте S009

**E2E-прогон #2 (s008-t7-e2e2, run-20261101-213316): 42 passed / 1 failed /
neg-passed 1, регрессий 0.** Все три фикса СВН зелёные:
- опорос (МассаОпоросившихся=0) — зелёный;
- падёж НВ00-000004 (Продукция.СтатусЖивотных) — зелёный;
- поступление-истина НВ00-000001 (Контрагент/Партнер=PIC) — зелёный;
- ТаймаутЗапуска1С=90 устранил connect-флейк батча СоколовМИ;
- neg-pl-denied зелёный.

**Единственный FAIL: arm-fuel-expense (батч 3 ОрловАВ, 33 с)** — флейк
диалога периода: шаг «Тогда открылось окно "Рабочее место..."» после ENTER
нашёл активным окно «Выберите период» (dialog не закрылся по ENTER,
таймаут поиска окна 10 с). Лог:
`tests/run-20261101-213316/logs/va-3-Administrator-OrlovAV.log`,
фича-строка №37. В E2E#1 тот же шаблон проходил. В шаблоне
`tests/templates/arm-fuel-expense.feature` каденс пауз быстрее, чем у
arm-fuel-receipt (Пауза 1 перед ENTER vs Пауза 2 там).

## Задачи S009 (по порядку)

### T1. Фикс флейка fuel-expense + контрольный прогон #3
1. Выровнять каденс пауз в `tests/templates/arm-fuel-expense.feature`
   под arm-fuel-receipt (Пауза 2 перед ENTER; сравнить точный паттерн
   по `tests/templates/arm-fuel-receipt.feature`). Заодно обновить
   устаревший заголовочный комментарий шаблона (пишет «ШАБЛОН ПОКА НЕ
   РАБОЧИЙ», а он уже включён и зелёный в E2E#1).
2. Restore по протоколу: `regress_run.rac_jobs_deny_set(on)` →
   `python scripts/s005_restore_ib.py` (~12 мин, выход designer = 0) →
   jobs-deny off → `python scripts/t8_gate.py`-функцией
   `rac_terminate_ib_sessions()` убить сессии →
   `python scripts/s005_make_neguser.py`.
   **НИКОГДА**: sessions-deny, убийство Designer-процесса (skill
   1c-destructive-ops-guard).
3. Запустить E2E #3: `nohup python scripts/s005_va_run.py
   tests/features/s006/t6-e2e.feature s009-t7-e2e3 5400 >
   tmp/s009/e2e3_launch.out 2>&1 &`. Артефакты `tmp/s005/va/s009-t7-e2e3/`,
   суммария в `tests/run-*/summary.json`, вердикт-строка
   «[verdict] PASS/FAIL (ReturnStatus=…), N sec».

### T2. ЗАДАЧА 4 (АРМ-цепочка) — верификация на ноябре
E2E#3 — ПЕРВЫЙ прогон с АРМ-цепочкой (dist s008 уже включает все правки):
- новые шаблоны `tests/templates/arm-service-issue.feature` (Выпуск услуг,
  идемпотентный блок настройки РС АпкПараметрыОтраженияЗатратРастениеводства
  для «Загрузка удобрений», копия полей донора «Загрузка посадочного
  материала (зерновые)» через ЗаполнитьЗначенияСвойств) и
  `tests/templates/arm-plant-production.feature` (Производство продукции
  растениеводства, идемпотентная запись РС АпкНоменклатураПоступающаяСПолей
  «Пшеница озимая», ГодУрожая=Год(ТекущаяДатаСеанса())).
- coverage-map.json: оба АРМа «always» под АпкПутевойЛистТракториста.
- Порядок в генераторе: `ПорядокЦепочкиАРМов` + `ОтсортироватьПланАРМовПоЦепочке`
  в `src/АпкПодготовкаСценарныхТестов/Ext/ObjectModule.bsl` — ранги:
  fuel-receipt=10 → fuel-expense=20 → service-*=30 → plant-production=40
  → прочее=50 → payroll=99 (выработка последняя).
Ожидаемый порядок батчей: батч1 СоколовМИ (…, arm-fuel-receipt),
батч3 ОрловАВ (…, arm-fuel-expense, arm-service-issue,
arm-plant-production, arm-payroll).
После E2E#3 COM-проверкой (`win32com.client`, паттерн
`tmp/s008/mort_receipt_com.py`, коннект-строка в `scripts/t8_gate.py`)
проверить: ПБЗ (Документ.ПроизводствоБезЗаказа) за ноябрь создан,
ВыработкаСотрудников за ноябрь > 0.
**Известный риск**: выработка может молча не создать документ — root cause
`tmp/t9/arm-vyusotr-final/root-cause.md`: ПБЗ от Выпуска услуг имеет
ПУСТУЮ ТЧ ВыходныеИзделия → нет ПартииПроизводства → silent no-op
АРМ выработки. Правка в T9 была внешним скриптом
`scripts/t9_upd_pbz_vyrabotka.py`. Если на ноябре воспроизведётся —
перенести правку идемпотентным серверным блоком в
`tests/templates/arm-payroll.feature` (добавить строку ВыходныеИзделия в
ПБЗ: Номенклатура «Услуги машино-тракторного парка», Количество=1,
НомерГруппыЗатрат=1 + элемент Справочник.ПартииПроизводства
Документ=ПБЗ, Код="1"), затем контрольный прогон #4.

### T3. Live-верификация контур-фильтра раннера (после зелёного E2E)
`src/АпкРаннер/.../Module.bsl` + Form.xml: чекбоксы контуров, таблица
«ПланПрогона» (модульная переменная переименована в ПланБатчей),
команды ОбновитьПлан/ВключитьВыделенные/ИсключитьВыделенные, фильтр
(Контуры + Отключены «Шаблон--Пользователь»), выбор хранится в
tests/test-selection.json. Пробный прогон с одним отключённым контуром.

### T4. Закрытие T7-tails (после устойчивого зелёного)
- baseline `tests/baseline/baseline-real.json` — только через
  ЗафиксироватьЭталон (см. с007-отчёт §T7);
- ИНСТРУКЦИЯ.md: убрать known-issue §5.3 (МассаОпоросившихся) и
  упоминания трёх СВН-фейлов, добавить новые arm-шаблоны в перечень;
- commit s008+s009 изменений.

### T5. Финал сессии
Heartbeat `tmp/s009/heartbeat.txt` (формат `HH:MM:SS T1/T2: текст`),
отчёт `docs/night-report-2026-11-02-s009.md`, этот файл обновить →
`docs/next-s010-prompt.md`.

## Жёсткие правила (не нарушать)

- Перед КАЖДЫМ запуском VA: `t8_gate.rac_terminate_ib_sessions()`.
- `scripts/t8_gate.py` БЕЗ аргументов запускает весь probe-пайплайн (~8 мин)
  — не запускать без args.
- Кириллица в bash/powershell аргументах манглится — русские тексты только
  через write-tool (UTF-8 файлы), python-вывод с u2a/reconfigure.
- Правки BSL → `mcp__bsl_ls` bsl_analyze (src, severities=Error, «0 файлов»
  = проверка НЕ выполнена) → `scripts/build_preprocessor.py` /
  `build_runner.py` → `scripts/build_dist.py`.
- В BSL-комментариях не использовать длинное тире U+2014 (bsl-ls Error
  InvalidCharacterInFile) — только ASCII "-".
- Restore: только `scripts/s005_restore_ib.py`; 2-attempt stop rule.
- Коммит/деструктив — с явным подтверждением в отчёте, не авто.

## Ключевые пути/команды

- Шаблоны `tests/templates/*.feature`; патчи `scenario-patches.json`
  (генератор `scripts/s006_write_patches.py`); coverage `tests/coverage-map.json`.
- Прогоны: `python scripts/s005_va_run.py <feature> <build-name> <timeout>`;
  вердикты в конце `*.out` / суммарии `tests/run-*/summary.json`.
- COM: `win32com.client.Dispatch("V85.COMConnector").Connect(...)`;
  коннект-строка/ADMIN в `scripts/t8_gate.py`.
- Сборка: `python scripts/build_preprocessor.py` (препроцессор),
  `python scripts/build_dist.py` (dist kit, 28 файлов).
- Спека-история: `docs/next-s008-prompt.md`, `docs/night-report-2026-11-01-s007.md`.

Начни с T1 (фикс fuel-expense → restore → запуск E2E#3), параллельно читая
вердикт по мере готовности.
