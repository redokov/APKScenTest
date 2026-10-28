# Tech Stack — APKScenTest

## 1С

- Платформа **8.5.4.1683**, бинарники `C:\Program Files\1cv8\8.5.4.1683\bin`.
- Конфигурация: 1С:ERP + модуль АПК ред. 2.5. Исходники: ERP — `C:\MyProjects\ERPsrc`,
  АПК — `C:\MyProjects\APKModSrc` (источник реальных имён объектов/форм/реквизитов).
- База: `Srvr="localhost";Ref="dev_erpapk_demo"`, PostgreSQL 18.3-5.1C @ localhost
  (db-name `dev_erpapk_demo`). Пользователь: `Администратор (ОрловАВ)`, без пароля.
- В базе уже интегрировано расширение Vanessa Automation, внешняя компонента установлена.
- Автономный режим конфигуратора (designer agent mode) для загрузок/выгрузок.
- Обработка препроцессинга — внешняя обработка (EPF), исходники XML в `src/`,
  сборка/разборка epf-build/epf-dump скилами. Раннер — EPF (исходники
  канонизируются в `src/` в рамках спеки 005; сейчас временно в `tmp/`).

> **Коррекция цели (28.10.2026).** Python-оркестратор (`scripts/regress_run.py`,
> `scripts/t8_gate.py`), COM-зонды и ночные LLM-сессии — это
> **dev-time стенд валидации**, накопивший ценные рецепты. Они НЕ входят
> в поставляемый продукт и не участвуют в рабочем прогоне (см.
> `.ai/steering/product.md`, «Целевая архитектура», и спеку 005).

## Тестовый стек

- **Vanessa Automation** (single): `C:\MyProjects\APKTechPlan\tests\vanessa\vanessa-automation-single.epf`.
  Запуск: `1cv8c ENTERPRISE /TESTMANAGER /S localhost\dev_erpapk_demo /Execute <epf>
  /C"StartFeaturePlayer;VAParams=<json>"` — проверенный паттерн
  `APKTechPlan/scripts/run_va_feature.py` (вердикт по строке
  «Выполнение сценариев закончено. Ошибок не было/БЫЛИ ОШИБКИ»).
  Локальные полные доки VA 1.2.043.42: `c:/MyProjects/MyTasks/NewOil/vanessa/vanessa-automation-1.2.043.42/docs`.
- **Allure**: встроенная генерация VA (Allure-отчёт, метки Allure в сценариях —
  см. доку VA «Закладка Сервис → Отчеты о запуске сценариев → Allure Метки»).

## Инструменты агента

- MCP `v8std` (https://ai.v8std.ru/mcp) — стандарты 1С, гейт после правки BSL.
- MCP `bsl-ls` — синтакс-диагностики BSL (гейт до загрузки в базу).
- MCP `bsl-platform-context` — справка API платформы 8.5.4.
- Скилы: epf-build/epf-dump, vanessa-automation, 1c-cli-ops, 1c-roundtrip-verify.
- Python-хелперы в `scripts/` (ASCII-имена); кириллица в CLI — только через билдеры.
  Всё перечисленное в этом разделе — только разработка и отладка
> (dev-time); рабочий прогон комплекта его не использует.
