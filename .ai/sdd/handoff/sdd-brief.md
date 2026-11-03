# SDD Handoff Brief — текущее состояние проекта (03.11.2026)

> readiness: **зелёный комплект, reproducibility доказана (4 E2E подряд)** —
> для новых сессий: продолжение `docs/next-s014-prompt.md`.
> Ключевые решения реализованы в спеках 001–006 (требования/дизайн/задачи
> утверждены, реализация завершена; спека 003 имеет follow-ups — см. review.md).

## Что завершено

- **001** препроцессинг (EPF, скан АПК, генерация `.feature`, хэши паролей)
- **002** сценарии растениеводства (5 типов + smoke, 16/16 + neg)
- **003** регресс-конвейер (`regress_run.py`: `--rehearsal`, `--update`,
  `--baseline-dt`; one-command dump → прогон → отчёт; web-требует публикации)
- **004** реальные авторы + негативные сценарии (neg-роль в micro-CFE,
  подмена/восстановление хэшей, `--real-authors`, neg-passed)
- **005** чистый 1С-комплект (препроцессор → раннер → отчёт в одной
  сессии 1С, без python/COM; dist/; ИНСТРУКЦИЯ.md)
- **006** животноводство СВН + КРС (14 сценариев + neg, контрольные
  E2E s010…s013: 45/0/neg-1, регрессий 0)

Baseline: `tests/baseline/baseline-real.json` (46 ключей, run-20261102-
034905); эталон E2E-прогона — `dist/`.

## Как запустить (user-инструкция: docs/manual-start-and-new-base.md)

1. Сервер 1С, база `dev_erpapk_demo`, сеансов=0 (кроме RAS), диск ≥20 ГБ.
2. `rac 127.0.0.1:1545 infobase summary list --cluster=...` — UUID
   `cd6af3f6-9740-4d96-97bc-5c5f3a454bec`.
3. Python-стенд (dev-time обвязка): restore dt (detached, `s005_restore_ib.py`)
   → jobs_deny(False) → neguser (`s005_make_neguser.py`) → E2E
   (`s005_va_run.py` / `regress_run.py`), COM-чек `s009_com_check.py`.
   Python **не входит** в комплект — только dev/CI.
4. Чистый 1С-комплект: препроцессор (от админа) → раннер → отчёт в сессии.

## Ключевые решения (операционные)

- **Пароли**: `ПодменитьПарольБезусловно` (real-режим),
  `ПодменитьПароль` (заморожен, байт-в-байт) — `ВосстановитьПароль`.
- **rac**: адрес `127.0.0.1:1545`, `infobase summary list` (не `summary-list`),
  синтаксис 8.5: `rac <addr> <mode> <subcmd> --cluster=<uuid>`.
- **restore-протокол**: jobs_deny=True → терминация всех сеансов (зомби-
  записи BackgroundJob исчезают асинхронно ~1 мин — не убивать процессы) →
  `nohup s005_restore_ib.py` detached → exit 0 → jobs_deny(False) → neguser
  → чистое поле (jobs_deny=True + term, чтобы фоновые сессии не мешали) → VA.
  ~13 мин; никогда не убивать 1cv8 посреди restore (инцидент s010).
- **Кириллица**: мангалится в bash-аргументах; python-лаунчеры всегда
  UTF-16 (t8_gate.py, s005_restore_ib.py).
- **Web**: `clientType=Web` + `webUrl` в настройках; нужен Apache
  (_1cws_module от той же платформы 8.5.4.1683, `Listen 9094`); база пока
  НЕ опубликована — блокер.
- **E2E-вердикт**: `[verdict] PASS/FAIL` в конце лаунчер-лога;
  `ReturnStatus` + summary.json (totals) + `s005_cmp_runs.py` vs baseline.

## Блокеры / нужны решения пользователя

1. **Web-режим**: нет публикации `dev_erpapk_demo`. Требования:
   wsap24.dll от 8.5.4.1683, `Listen 9094`, Alias `/dev_erpapk_demo`,
   сверить `WEB_URL_DEFAULT` (9093) vs конфиг (9094).
2. **Фоновые DefUser (BackgroundJob) сессии** после restore:
   решено в s014 — префлайт `t8_gate.py` исключает `BackgroundJob`
   (как `RAS`); их нельзя убивать (урок 21.10: kill вешает старт
   клиента). Ранее решалось запретом регл. заданий (`jobs_deny=True`)
   на прогон; оба варианта дают зелёный E2E (s011 vs s012/s013).

## Бэклог (не в работе без явной санкции)

- планирование; arm-fuel-expense для авто-ПЛ (ждёт ТС со складом бака —
  `when: never`); разведка «главы 2 АПК» по желанию.

## Улики

- night-reports: `docs/night-report-2026-10-15.md`…`night-report-2026-11-03-
  s013.md`; отчёты s009/s010/s011/s012/s013
- evidence: `docs/evidence/s005-live-20261030/`, `docs/evidence/s006-
  live-20261101/`
- промты: `docs/next-s011…s014-prompt.md`
