# Промт для новой сессии: спека 003 — финал (T7 веб, T9 baseline-dt, T8 закрыть, review)

## Кто ты и где

Пи-агент, проект `c:/MyProjects/APKScenTest` (1С:ERP+АПК 2.5, Vanessa
Automation, репо GitHub, MCP `v8std`). База: `localhost\dev_erpapk_demo`
(демо-база, PostgreSQL, пользователь `Администратор (ОрловАВ)` без пароля).
Платформа: `C:\Program Files\1cv8\8.5.4.1683\bin` (1cv8c — тонкий клиент,
1cv8 — DESIGNER batch).
VA EPF: `C:\MyProjects\APKTechPlan\tests\vanessa\vanessa-automation-single.epf`.
Исходники конфигурации: `C:/MyProjects/APKModSrc/`.
**Сессия интерактивная** (видимый десктоп — GUI-операции разрешены).

## Контекст: что сделано (обязательно прочитать)

1. `docs/night-report-2026-10-19.md` — полный отчёт: спека 003 T1–T6 закрыты
   (rehearsal 5/5 + `--update`-репетиция 5/5 regressions=0, baseline в git,
   runbook `docs/runbook.md`).
2. `tmp/regress/EVIDENCE-T5.md`, `tmp/regress/probe/t1-facts.md` — evidence.
3. Решения пользователя (2026-10-19, коммит 3b3969e):
   - **TD-007 `--baseline-dt` ПРИНЯТ** → задача T9 в tasks.md;
   - **Релиз 2 = (а) реальные авторы + (д) негативные сценария** (PLAN.md,
     Фаза 5); животноводство/планирование — бэклог;
   - T7 (веб-клиент) — РАЗБЛОКИРОВАН (сессия интерактивная).

## Задачи этой сессии (по приоритету)

### T9 — `--baseline-dt` (TD-007, design.md §13)

- `scripts/regress_run.py`: флаг `--baseline-dt <file>`: дамп текущего →
  RestoreIB baseline-dt → гейт → откат к дампу текущего (finally).
- Взаимоисключаемость с `--update` (RestoreIB затёр бы обновление) — отказ
  с понятным сообщением.
- Runbook: раздел baseline-dt + «снять свежий baseline-dt после зелёного
  прогона с обновлением».
- E2E: `--rehearsal --baseline-dt tmp/regress/20261019-052456/pre-update.dt`
  → ожидаем 5/5, regressions=0, откат к исходному. (Файл существует,
  ~46 мин прогон; ФИКСИРОВАННЫЙ дизайн-порядок фаз см. design.md §4.2.)

### T7 — веб-клиент (TD-006, сессия интерактивная)

- **Apache найден: `C:\1cweb\apache24`** (экземпляр erpuh3). web-publish
  был ЗАПУЩЕН в прошлой сессии, но **команда прервана (aborted)** —
  состояние публикации НЕИЗВЕСТНО. Первым делом:
  `powershell.exe -NoProfile -File
  "C:/MyProjects/PiPack/skills/1c/web-info/scripts/web-info.ps1"
  -ApachePath "C:\1cweb\apache24"` — проверить статус/порт/конфиг.
- Затем web-publish (скилл `web-publish`, ApachePath `C:\1cweb\apache24`):
  `-InfoBaseServer localhost -InfoBaseRef dev_erpapk_demo
  -UserName "Администратор (ОрловАВ)" -AppName dev_erpapk_demo -Port 8081
  -V8Path "C:\Program Files\1cv8\8.5.4.1683\bin"`. NB: кириллический
  UserName в bash-команде — риск манглинга; если упадёт авторизация —
  повторить с UserName без кириллицы или через ps1-обёртку.
- Флаг `--web-client` в `regress_run.py`: меняет ТипКлиента в VAParams
  батчей на «Веб» (T6-раннер формирует VAParams — посмотреть, как
  t8_gate.py/t6-раннер его собирают; возможно, правка настроек
  preprocessor-settings.json или runner_task.json). Проверка: rehearsal
  `--rehearsal --web-client` → явный вердикт (зелёный или документированный
  отказ веб-клиента VA).
- Если веб-прогон стабильно зелёный — T7 закрыт; в runbook — раздел.
- После всех прогонов: web-unpublish (убрать публикацию) — аккуратно,
  Apache используется erpuh3 (КОМУС), не ломать его конфиг: AppName строго
  `dev_erpapk_demo`.

### T8 — закрыть ретро

Ретро-раздел PLAN.md уже написан (3b3969e). Осталось: пометить чекбокс
«Ретро-раздел PLAN.md отревьюен пользователем» после его подтверждения.

### Финал спеки 003

- sdd-review → `review.md` (requirements/design/tasks ↔ evidence).
- `.status`: implementation:done → review:done; INDEX обновить.
- `docs/night-report-<date>.md` + этот файл (next-session-prompt) —
  на следующий рубеж (релиз 2: реальные авторы + негативные сценарии).

## Ключевые факты (не переоткрывать — из отчёта 2026-10-19)

- **Деградация демо-базы**: баки ТС пустеют (−31,5 л/прогон, МТЗ-82-79,
  сейчас +583 л ≈ 18 прогонов). Симптом: 01-pl-tractor падает на
  «жду Номер», на форме «Обнаружен отрицательный остаток топлива» (БЕЗ
  модалки). Fix-рецепт: заправочная ведомость 700 л **датой ранее дня
  прогона** (образец НВЦБ-000004 от 18.10; форма читает остаток на начало
  дня). Структурно лечится T9 (--baseline-dt).
- Диагностика UI-падений: одиночный probe
  `tmp/regress/probe/probe_pl_run.py` (VAParams:
  `ДелатьСкриншотПриВозникновенииОшибки`+`СниматьСкриншотКаждогоОкна1С`
  +VanessaExt) → PNG→RGB (PIL) → OCR `tmp/regress/probe/ocr1.ps1`
  (скилл img-occ нестабилен; WinRT транзиентен — повторить при AggregateException).
- COM 8.5: метаданные через `ПустаяСсылка().Метаданные()`; журнал
  регистрации из COM недоступен; ТЧ — `Выгрузить()`/`Получить(i)`;
  справочники: `ТранспортныеСредства`, `СтруктураПредприятия`,
  `Сотрудники`, `Номенклатура`, `Склады`, `Организации`.
- rac: `--cluster=67cdef87-7bfc-4dae-b8e4-3ea9f8529156` (только cluster-id);
  ras поднят ad-hoc (`ras.exe cluster`).
- Кириллица через bash-transport портится интермиттентно — файлы писать
  write-tool'ом, проверять байты; никогда `python -c` с кириллицей.
- Тайминги: preflight ~1 мин, dump ~3–4 мин (1734 МБ), RestoreIB ~13–14 мин,
  gate 14 мин (5/5), rollback ~13 мин. Полный rehearsal ≈33 мин, с update
  ≈46 мин, с baseline-dt будет ≈47 мин. NFR-001 (E2E ≤40 мин) — с запасом.
- Гейт `t8_gate.py` и EPF НЕ менять (TD-001); зонды D-001; VN БД:
  база уже с расширением VA, компонента VanessaExt установлена.
- Free space: было 19.7–28 ГБ — следить (каждый прогон +1.7 ГБ дампов;
  чистка: `tmp/regress/*/pre-update*.dt`, кроме baseline-кандидата).

## Дисциплина

1. Прочитал контекст → heartbeat `tmp/t9/heartbeat.txt`.
2. Коммит per шаг с информативным сообщением; INDEX/PROGRESS актуализировать.
3. `docs/night-report-<date>.md` по завершении; этот файл переписать на
   следующую точку.
4. Верификация (команды/evidence) перед claim complete; 2-attempt stop.
5. Перед чем-либо разрушительным — спросить; Apache общий с erpuh3 (КОМУС).

## Первая команда сессии

`cat docs/night-report-2026-10-19.md` (я уже прочитал промт) →
heartbeat → **T9** (реализация --baseline-dt, ~1 ч) → E2E-прогон T9 (~47 мин)
→ **T7** (web-info → web-publish → --web-client → прогон) → T8 чекбокс →
sdd-review → night-report + этот промт на релиз 2.
