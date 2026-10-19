# Промт для новой сессии: релиз 2 — реальные авторы + негативные сценарии (спека 004)

## Кто ты и где

Пи-агент, проект `c:/MyProjects/APKScenTest` (1С:ERP+АПК 2.5, Vanessa
Automation, GitHub, MCP `v8std`). База: `localhost\dev_erpapk_demo`
(PostgreSQL, пользователь `Администратор (ОрловАВ)` без пароля). Платформа:
`C:\Program Files\1cv8\8.5.4.1683\bin`. VA EPF:
`C:\MyProjects\APKTechPlan\tests\vanessa\vanessa-automation-single.epf`.
Исходники конфигурации: `C:/MyProjects/APKModSrc/`. Сессия интерактивная.

## Контекст: что сделано (обязательно прочитать)

1. `docs/night-report-2026-10-19-day.md` — финал спеки 003: review:done
   (Approved with follow-ups), T9 baseline-dt E2E зелёный, T7 вердикт,
   инцидент с убитым RestoreIB и цепочка восстановления.
2. `docs/night-report-2026-10-19.md` — T1–T6 спеки 003.
3. `.ai/sdd/specs/003-regression-conveyor/review.md` — Follow-Ups.
4. Решения пользователя: **релиз 2 = (а) реальные авторы вместо зондов
   (снятие D-001 спеки 002) + (д) негативные сценарии** (PLAN.md Фаза 5);
   животноводство/планирование/arm-fuel-expense — бэклог.

## БЛОКЕР ПРЕЖДЕ ВСЕГО: лицензии

Сервер лицензий (`C:\ProgramData\1C\Licence\3.0\`, лог `licenceserver.*.log`)
19.10: серия 4135 `ELicenceNotFound`, затем 1 одновременное место
(`UseCount: 0`). Конвейеру нужно ≥2 параллельных сеанса (два батча per-user),
веб-прогону ≥3. **Первым делом проверить логи лицензий и спросить
пользователя о статусе лицензий.** Без этого любые прогоны краснеют на
`status=connect rs=2` (см. runbook §4 последняя строка).

## Задачи этой сессии

### 0. Быстрые хвосты спеки 003 (пока нет прогонов)

- `TIMEOUT_RESTORE` в `scripts/regress_run.py`: 1500 → 3000 с (Issue 1
  review). Коммит +一行 runbook (тайминги фаз).
- Повторить веб-прогон T7 (`--rehearsal --web-client --web-url
  http://localhost:9091/dev_erpapk_demo`) ТОЛЬКО когда лицензий хватает:
  публикация через скилл web-publish, ApachePath `C:\1cweb\apache24`,
  Port 9091, wrapper base64 для кириллического UserName — см.
  `tmp/t7/publish.ps1` (механика уже доказана). После — web-unpublish +
  восстановление `httpd.conf.pre-s003T7.bak`.

### 1. Спека 004 «Реальные авторы» (sdd-prd → sdd-spec → sdd-tasks → реализация)

Ядро (из PLAN.md Фаза 5 и комментариев гейта `[restrict] реальные авторы
(pending user confirmation)`):
- Запуск сценариев под авторами документов (ОрловАВ/СоколовМИ и др.), а не
  под зондами: регресс проверяет права/RLS. Механизм подмены/восстановления
  хэшей паролей УЖЕ внутри t8_gate (спека 001) — снять ограничение
  restrict_manifest (Зонд1=smoke, Зонд2=01-pl-tractor) на полный манифест.
- Окно прогона — тихие часы; baseline переснимается (реальные авторы ≠
  зонды по времени/поведению).
- Негативные сценарии: пользователь без полных прав → ожидаемая ошибка
  (нет прав). Нужен выбор носителя прав (роль «только чтение»? конкретный
  реальный пользователь?) — обсудить с пользователем в requirements.
- Данные: демо-база деградирует (баки −31.5 л/прогон) — после каждого
  зелёного прогона снимать свежий baseline-dt (runbook §2) и гонять
  `--baseline-dt` для воспроизводимости.

### 2. Дисциплина прогонов (обновлённая после инцидента 19.10)

- НИКОГДА не обрывать RestoreIB/DumpIB раньше >3000 с; признаки жизни:
  рост pg data dir (`du -sh "C:\Program Files\PostgreSQL\18.3-5.1C\data\base"`),
  подключения rphost→5432 (netstat). /Out пишется только по завершении!
- При «тихом» зависании клиента — сначала `C:\ProgramData\1C\Licence\3.0\logs`
  (лицензии), потом `rac session list --cluster=67cdef87-…` + terminate.
- rac требует ad-hoc ras: `ras.exe cluster` (слушает 1545). Синтаксис:
  `rac infobase info --cluster=<id> --name dev_erpapk_demo` (НЕ --infobase
  для info; --infobase=<uuid> для update). Вывод rac — cp866.
- Кириллица в CLI: только файлы/write-tool или base64-wrapper'ы; проверка
  байтов. COM pywin32: методы через getattr-цепочки иногда падают
  AttributeError — проверенные паттерны в scripts/*.py; вывод Execute() —
  `.Выгрузить()` + `r[i][j]`.
- Free space ≥5 ГБ (дамп 1.7 ГБ + restore ~2×); чистка старых pre-update.dt
  кроме baseline-кандидатов.

## Ключевые факты (не переоткрывать)

- Спека 003: конвейер доказан 3 зелёными E2E (rehearsal/update/baseline-dt),
  exit-коды/abort-пути проверены, baseline релиза 1 в git (run-20261019-053203),
  runbook живой. NFR-001: gate ≤14.5 мин.
- Тайминги: preflight ≤70 с, dump ~200 с, baseline-restore ~850 с, gate
  840–870 с, rollback ~800 с; rehearsal ≈33 мин, +update ≈46 мин,
  +baseline-dt ≈47 мин.
- Веб-публикация базы: порт 9091 (8081 занят посторонним Apache; erpuh3
  трогать нельзя — общий конфиг C:\1cweb\apache24, бэкап httpd.conf.pre-s003T7.bak).
- EPF собран из src/АпкПодготовкаСценарныхТестов (build_t6.py; содержит
  clientType/webUrl поддержку). Гейт t8_gate читает tmp/t8/preprocessor-settings.json.
- Регистр топлива в баках называется `АпкГСМвБаках` (не ТопливоВСкладскихЗапасах).
- Деградация: заправочная ведомость датой РАНЕЕ дня прогона (образец НВЦБ-0004);
  штатный ввод остатков не повторится (ПоТехникеУжеВводилсяОстаток).

## Первая команда сессии

`cat docs/night-report-2026-10-19-day.md` → heartbeat → проверить лицензии
(спросить пользователя) → мелкий фикс TIMEOUT_RESTORE → старт SDD-цикла
спеки 004 (sdd-prd: реальные авторы + негативные сценарии).
