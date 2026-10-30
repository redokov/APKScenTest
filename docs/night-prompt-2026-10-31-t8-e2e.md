# Ночной прогон 31.10: T8 — финальный зелёный E2E + закрытие спеки 005

Проект: `C:\MyProjects\APKScenTest` (1С:ERP+АПК 2.5, Vanessa Automation 1.2.043).
Это последняя задача спеки 005 (pure-1c-kit): всё остальное (T1-T7 + T5/T4
живьём) закрыто, см. `.ai/sdd/specs/005-pure-1c-kit/tasks.md` и
`docs/night-report-2026-10-30.md` (аддендумы 1-3).

## ЦЕЛЬ НОЧИ

1. Зелёный E2E-прогон `tests/features/s005/t8-e2e.feature` — полная приёмка
   комплекта формами 1С (препроцессор → раннер → отчёт, без python-стенда
   в рабочем цикле) — закрыть T8.
2. Док-часть T8: README (состав dist/), чекбоксы Фазы 6 в `.ai/sdd/PLAN.md`,
   ретро-раздел PLAN.
3. Коммит + пуш.

## ПРЕДПОЛОЖЕНИЯ ОКРУЖЕНИЯ (проверить в преамбуле)

- Десктоп СВОБОДЕН (главное условие — попытка 30.10 днём упала на UI-флейке
  занятого десктопа: два разных interaction-шага в двух прогонах, на idle
  все проходят стабильно).
- База `localhost\dev_erpapk_demo` СЕЙЧАС ГРЯЗНАЯ (попытка 30.10 списала
  топливо: 15 сценариев прошли) → перед E2E ОБЯЗАТЕЛЕН restore.
- Платформа `C:\Program Files\1cv8\8.5.4.1683\bin`; кластер
  `67cdef87-7bfc-4dae-b8e4-3ea9f8529156`; ИБ `4d9168e8-f640-490f-bbe6-32b1df12991f`;
  админ `Администратор (ОрловАВ)` без пароля; `rac session list` — живой способ
  проверки сеансов (`rac infobase list` падает).

## ПОСЛЕДОВАТЕЛЬНОСТЬ (строго, с ловушками)

### 0. Префлайт

- Сеансы на базе: `rac session list` → терминировать все с app-id
  1CV8/1CV8C/Designer (скрипт: `python -c "import sys;sys.path.insert(0,'scripts');import t8_gate as t;print(t.rac_terminate_ib_sessions(app_ids=('1CV8','1CV8C','Designer')))"`).
- U+FFFD-чек фичи: `grep -c $'\xef\xbf\xbd' tests/features/s005/t8-e2e.feature` = 0.
- Десктоп свободен: ни одного пользовательского окна (Chrome/мессенджеры) —
  проверить UIA-списком окон PowerShell (примеры в tmp/s005/uia_windows.txt).

### 1. Restore базы (разрушительная операция — скил 1c-destructive-ops-guard!)

```
python scripts/s005_restore_ib.py
```
- dt: `tmp/regress/20261028-062041/pre-update.dt` (дамп ПЕРЕД baseline — топливо
  на месте). Штатно ~800-900с. НЕ УБИВАТЬ посреди restore.
- ЛОВУШКИ (все пойманы 30.10, задокументированы):
  - bash/MSYS ЛОМАЕТ аргументы 1cv8.exe (`/S` → `S:/`, кириллица /N манглится)
    → restore ТОЛЬКО через python-лаунчер (уже готов).
  - перед запуском: `rac infobase update --cluster=... --infobase=...
    --scheduled-jobs-deny=on`, сеансы = 0.
  - если дизайнер упал с «Ошибка разделенного доступа» → у него остался
    зомби-сеанс app-id=Designer → терминировать rac'ом (скрипт выше) и ретраить.
- Успех = `tmp/s005/t8restore/restore.result` содержит 0, py-вывод `designer exit: 0`.
- После: `--scheduled-jobs-deny=off`.

### 2. neg-пользователь (на dt его НЕТ — python-t8 удалял как временного)

```
python scripts/s005_make_neguser.py
```
Успех: «АпкСценТест_Негатив1 создан … H1 len=57». (COM V85 — headless-безопасно.)

### 3. E2E — решающий прогон

```
python scripts/s005_va_run.py tests/features/s005/t8-e2e.feature t8-e2e-night 1800
```
Ожидание (~15 мин): ReturnStatus=0. В va_1c.log — вывод переменных:
```
КаталогПрогона = C:/MyProjects/APKScenTest/tests/run-YYYYMMDD-HHMMSS
ВердиктE2E = PASS. passed=16 failed=0 broken=0 timeout=0 unknown=0 neg-passed=1 neg-failed=0
регрессий 0 vs baseline run-20261028-062621
```
Ассерты в фиче: PASS., neg-passed=1, neg-failed=0, регрессий 0, пароли
без «НЕ ВОССТАНОВЛЕН», статус «Отчёт: ». Если ВНОВЬ упадёт взвешивание
(НВ00-000003) — НЕ чинить код: сделать 2 зонда
(`s005_va_run.py tests/run-<fresh>/features/05-weighing--Administrator-OrlovAV.feature weigh-probe 600`);
2 разных шага = UI-флейк среды, стоп-правило, эскалация пользователю.

### 4. Улики + док-часть T8

- Улики: `tmp/s005/va/t8-e2e-night/va_1c.log` → `docs/evidence/s005-live-20261030/t8-e2e-verdict-night.txt`;
  итоги свежего run-каталога (summary.json: 17/17) → туда же.
- README.md: секция «Состав комплекта dist/» (2 EPF + VA single + scenarios
  13 файлов + ИНСТРУКЦИЯ.md — точный список `ls dist/`).
- `.ai/sdd/PLAN.md` Фаза 6: закрыть чекбоксы (все 5 критериев теперь доказаны),
  добавить ретро-абзац (миграция цели Фаз 4-5 → возврат, чему научились:
  ловушки модалей/MSYS/зомби-сеансов — материалы в tasks.md T4/T5 и отчёте).
- tasks.md T8 → СТАТУС: закрыт; `.ai/sdd/INDEX.md` спека 005 → done.

### 5. Финал

- Коммит: `T8 closed: green E2E from clean session (verdict PASS 17/17, регрессий 0)` + пуш.
- Heartbeat `tmp/s005/heartbeat.txt` — ДОПОЛНЯТЬ строками каждого этапа.
- Биллинг-арм НЕ нужен (короткая сессия), окно <04:00 не обязательно —
  единственный жёсткий гейт: ДЕСКТОП СВОБОДЕН и подмена паролей на idle-машине.

## СПРАВКА (не перечитывать файлы без нужды)

- VA-раннер: `python scripts/s005_va_run.py <feature> <run-name> [timeout]`;
  вердикт из ReturnStatus (0=PASS) + va_1c.log (UTF-8, читать read()-ом, НЕ cat);
  артефакты `tmp/s005/va/<run-name>/`. Кириллица в bash-выводе манглится —
  всё русское писать в tmp/*.txt python-скриптами и читать read().
- E2E-фича уже содержит ПОЛНЫЙ набор ассертов — править не нужно.
- Базовая ловушка T5 (закрыта): модальные ПоказатьПредупреждение в раннере
  вешают VA-шаг навсегда; если что-то висит >2 мин без признаков работы —
  UIA-снимок окон (PowerShell, пример tmp/s005/restore_win5.txt).
- Git: origin https://github.com/redokov/APKScenTest.git, HEAD на старте =
  коммит T8-подготовки (см. git log -1).
