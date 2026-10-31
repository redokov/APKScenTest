# Промт-продолжение (новая сессия, 01.11): спека 006 — T3 probe-волны → T7 закрытие

Проект: `C:\MyProjects\APKScenTest` (1С:ERP+АПК 2.5, Vanessa Automation 1.2.043).
Вставь этот промт в НОВУЮ сессию pi в каталоге проекта. Работа автономная
(пользователь ушёл): решения принимай сам, стоп-правила жёсткие. Предыдущая
сессия остановлена по переполнению контекста — её взвод снят.

## ПЕРВЫЕ ДЕЙСТВИЯ (в порядке)

1. **Взведи автономность для ЭТОЙ сессии** (пользователь разрешил длинную работу):
   `python C:/Tools/pi-billing-window/scripts/arm_cont_after_reset.py "$PI_SESSION_FILE" --repeat 12 --ttl 26`
   затем `--check`. Взвод снимается в самом конце работы.
2. Прочитай состояние: `tmp/s006/heartbeat.txt` (tail), этот файл, и при
   необходимости `git log --oneline -10`.
3. Если пришло сообщение «продолжи» (от взвода) — это норма, продолжай
   с места остановки по heartbeat/tasks.md.

## СОСТОЯНИЕ НА СТАРТЕ (ночь 31.10, всё закоммичено и запушено)

- **Спека 006 (животноводство СВН+КРС) — requirements/design/tasks все
  approved.** Файлы: `.ai/sdd/specs/006-zhivotnovodstvo-scenarios/`
  (requirements.md, design.md TD-001..006, tasks.md T1..T7).
- **T1 закрыт** (`99a6033`): аудит 14 Must-типов — `tmp/s006/audit-fields.md`
  (fieldList-ы всех типов, оси-кандидаты, ловушки форм).
- **T2 закрыт** (`406f5f2`): coverage-map.json 19 записей (5 старых
  байт-идентичны, +14 животноводства), 14 заготовок шаблонов
  `tests/templates/1*-*.feature … 2*-*.feature` (каркасы с TODO),
  генератор `scripts/t2_extend_covmap_s006.py` (идемпотентен — правки
  fieldList-ов вносить в НЕГО и перегенерить). Скан-гейт
  `scripts/probe_s006_scan.py` = **PASS 0 фейлов** (`tmp/s006/scan-plan.txt`):
  14/14 типов с представителями, все поля валидны. 3 ПУСТО поля —
  опциональные транспортные у ТТН-молока (Заказчик/МаркаАвтомобиля/
  Водитель) — в шаблон НЕ включать.
- Авторы: СВН 100% Орлов; КРС/молоко Орлов + ФедоровБМ (ИБ-пользователь
  `Администратор (ФедоровБМ)` есть). Представители и значения полей —
  в `tmp/s006/scan-plan.txt` (конкретные числа для probe-фич).
- Следующий шаг: **T3 probe-волна СВН ×6**.

## ЦЕЛЬ (порядок严格执行)

T3 (probe СВН ×6) → T4 (probe КРС ×8 + разведка сводного-молока TD-006)
→ T5 (neg-шаблон + neg-гейт) → T6 (restore + объединённый полный прогон)
→ T7 (baseline фиксация + контрольный прогон + dist/ИНСТРУКЦИЯ/README/
статусы + docs/night-report-2026-11-01.md + коммит/пуш) → снять взвод →
итог в чат. Подробности acceptance/файлов — в tasks.md соответствующих задач.

## T3 PLAYBOOK (probe-first, по спеке 002)

1. Прочитай playbook ловушек: `docs/next-session-prompt.md` (грабли 8.5.4,
   рецепт 01-pl-tractor) и образец заполненного шаблона
   `tests/templates/05-weighing.feature` (плейсхолдеры {{header.*}} и шаги).
2. Probe = живой прогон под админом (БЕЗ подмены пароля, БЕЗ записи:
   заполняем форму по значениям представителя из scan-plan.txt и закрываем
   окно без записи). Пишешь probe-фичу `tmp/s006/probe-svn.feature` с
   КОМКРЕТНЫМИ значениями (не плейсхолдеры): навигационная ссылка
   `e1cib/data/Документ.АпкГрупповойОпорос` (создание), шаги заполнения
   шапки (поля из coverage-map записи), ТЧ, затем закрыть окно без записи.
   Можно все 6 сценариев СВН в одной probe-фиче (6 сценариев = один
   TestClient-сеанс, меньше оверхеда).
3. Запуск: `python scripts/s005_va_run.py tmp/s006/probe-svn.feature svn-probe1 1200`
   (последний arg — таймаут сек). Вердикт: ReturnStatus=0 + читать
   `tmp/s005/va/svn-probe1/va_1c.log` ТОЛЬКО read()-ом (кириллица в bash
   манглится). Артефакты: tmp/s005/va/<run>/.
4. Итерации: упавший шаг → смотреть va_1c.log/stdout-лог VA → править шаг
   (другой VA-шаг: «я выбираю значение реквизита ... из формы списка»,
   «я ввожу текст ...», двойной клик UIA — рецепты в 05-weighing.feature
   и docs/next-session-prompt.md) → повтор. Стабилизация шаблона = 2
   зелёных probe подряд.
5. Наполнение боевого шаблона: переносишь стабилизированные шаги в
   `tests/templates/<имя>.feature` с плейсхолдерами {{header.<Поле>}}.
   Патчи-исключения — в `tests/templates/scenario-patches.json`.
6. Перед КАЖДЫМ живым прогоном: `rac session list` → терминировать
   1CV8/1CV8C/Designer на базе (рецепт: `python -c "import sys;sys.path.insert(0,'scripts');import t8_gate as t;print(t.rac_terminate_ib_sessions(app_ids=('1CV8','1CV8C','Designer')))"`).
7. UIA-флейк: 2 зонда; 2 РАЗНЫХ шага в 2 прогонах = среда → шаблон в
   конец волны, дальше следующий; НЕ чинить код вслепую.
8. Зависание >2 мин без признаков работы → UIA-снимок окон PowerShell
   (образец tmp/s005/restore_win5.txt) → классифицировать.
9. Heartbeat `tmp/s006/heartbeat.txt` — строка на каждый прогон/этап.
   Закрытый шаблон → сразу коммит `spec 006 T3: <шаблон> stabilized`
   (или пачкой в конце волны) + статус в tasks.md.

T4 = то же для 8 КРС-типов + `tmp/s006/milk-summary-recon.txt` (почему
АпкКРССводныйДокументПоРеализацииМолока не проведён: журнал регистрации
COM `ЖурналРегистрации` + probe записи под админом; решение Should/skip).
T5: `neg-livestock-denied.feature` (опорос без прав, neg-юзер создаётся
`scripts/s005_make_neguser.py`), neg-гейт — neg-passed=1, MISSING= числу
позитивных сценариев (образец `tests/features/s005/t5-negrun.feature`).
T6: restore (`python scripts/s005_restore_ib.py` ТОЛЬКО отсоединённо:
nohup + watcher-цикл; jobs-deny on→restore→off; НЕ УБИВАТЬ Designer) →
neguser → E2E-фича по образцу `tests/features/s005/t8-e2e.feature`
(адаптировать: препроцессор сам создаст общий план с животноводством) →
PASS: все зелёные (новые=NEW), регрессий 0 vs baseline, mismatch=[],
замер времени ≤60 мин.
T7: фиксация baseline (зелёный прогон T6) → контрольный прогон (регрессий
0, NEW нет) → dist/scenarios пересобрать (шаблоны+патчи+baseline) →
ИНСТРУКЦИЯ.md раздел «Животноводство» → README (состав dist/) →
`.ai/sdd/INDEX.md`+PLAN статусы → улики `docs/evidence/s006-live-*/` →
`docs/night-report-2026-11-01.md` → финальный коммит/пуш →
`python C:/Tools/pi-billing-window/scripts/arm_cont_after_reset.py "$PI_SESSION_FILE" --remove`
→ итог в чат и СТОП.

## ЖЁСТКИЕ ПРАВИЛА

- Кириллица в bash-выводе/args МАНГЛИТСЯ: русские тексты только через
  python → tmp/*.txt (UTF-8), читать read()-ом; имена run/аргументов ASCII.
- Restore — разрушительная операция: только scripts/s005_restore_ib.py,
  отсоединённо, не убивать; jobs-deny off после.
- 2-attempt stop rule: одна ошибка ×2 → классифицировать и обходить,
  не долбить третий раз.
- Прогресс на диск немедленно; tmp/ в gitignore — в коммит только
  скрипты/шаблоны/доки/итоговые улики в docs/evidence/.
- Git: origin https://github.com/redokov/APKScenTest.git, ветка main.
- СНЯТЫЙ ФЛАГ НЕ ВОСКРЕСАЕТ: если после завершения придут НОВЫЕ задачи —
  перевзвести ДО их выполнения.

## ТЕХСПРАВКА

- База `localhost\dev_erpapk_demo`; админ `Администратор (ОрловАВ)` без
  пароля; платформа `C:\Program Files\1cv8\8.5.4.1683\bin`; кластер
  `67cdef87-7bfc-4dae-b8e4-3ea9f8529156`; ИБ `4d9168e8-f640-490f-bbe6-32b1df12991f`;
  `rac session list` работает, `rac infobase list` падает.
- COM V85: `win32com.client.Dispatch("V85.COMConnector").Connect(t.conn_str(t.ADMIN,""))`;
  запросы `q.Execute().Choose()`+`sel.Next()`, алиасы латиницей; ИБ-юзеры
  `ПолучитьПользователей()`, `УникальныйИдентификатор` — свойство.
  Образцы: `scripts/probe_s006_scan.py`, `scripts/probe_livestock_demo.py`.
- dt для restore: `tmp/regress/20261028-062041/pre-update.dt` (животноводство
  в нём есть — разведка это подтвердила на восстановленной базе).
- VA single: `C:\MyProjects\APKTechPlan\tests\vanessa\vanessa-automation-single.epf`.
