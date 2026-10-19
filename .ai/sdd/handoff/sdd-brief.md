# SDD Handoff Brief — спека 004 (реальные авторы + негативные сценарии)

> readiness: ready for implementation (требования/дизайн/задачи approved;
> ночь 2026-10-19 — решения делегированы агенту до утра)

- Requirements: `.ai/sdd/specs/004-real-authors-negative/requirements.md` (approved)
- Design: `.ai/sdd/specs/004-real-authors-negative/design.md` (approved, night-delegation)
- Tasks: `.ai/sdd/specs/004-real-authors-negative/tasks.md` (approved, T1–T10)
- Status: `.ai/sdd/specs/004-real-authors-negative/.status` = `tasks:approved`

## Ключевые решения (для ночного исполнителя = меня)

1. Подмена паролей ВСЕГДА в real-режиме (решение пользователя): новый экспорт
   `ПодменитьПарольБезусловно`; замороженный `ПодменитьПароль` байт-в-байт;
   `ВосстановитьПароль` + ветка «исход без пароля» (`Пароль=""`).
2. Neg-роль — постоянная в micro-CFE `src/cfe/АпкСценТестНегРоль` (из COM роли
   не создаются — факт зондов); neg-пользователь временный, состав
   [БазовыеПраваБСП, АпкСценТестНегатив].
3. Режим: `--real-authors` → patch preprocessor-settings.json (один канал);
   гейт: без restrict_manifest/Зондов; smoke под первым автором.
4. Вердикт негатива: инверсия в СобратьОтчет по ПАТТЕРНОТКАЗА (зондируется);
   любое расхождение = FAIL.
5. Baseline: `tests/baseline/baseline-real.json`; зелёность = позитивы +
   negativePassed + все passwordRestored.
6. Онлайн-проверка: rac_sessions_online, два рубежа, exit 2 до изменений.
7. Лицензии: тонкие неограниченно; веб — эксклюзивно отдельно (FR-009 Could).

## Блокеры/зонды до кода

- T3: роль CFE видна/назначаема из COM? (fallback: роль в APKModSrc).
- ПАТТЕРНОТКАЗА: фактический текст ошибки под neg-составом.
- COM-подключение под neg-пользователем невозможно (нет права
  ВнешнееСоединение у БазовыеПраваБСП) → зонды под neg-составом через
  тонкий клиент /Execute, не COM.

## Верификация

- BSL: pre_load_validate → bsl-ls bsl_analyze (0 файлов = не выполнено) →
  epf-build; python: py-тесты; E2E: только main-агент, эксклюзивно,
  --baseline-dt (эталон 052456), RestoreIB не убивать <3000 c.
- Прогоны: `python scripts/regress_run.py --rehearsal --real-authors
  --baseline-dt <эталон>/pre-update.dt`.
