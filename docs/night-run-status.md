# Night Run Status (23.10.2026)

## Run9 — BLOCKED (база в состоянии deny=on, требуется admin)

**Время**: 05:24 — 06:41+

### Блокировка

- **scheduled-jobs-deny**: `on` (осталось от предыдущего rollback)
- **Блокировка базы**: «Ошибка разделенного доступа... база заблокирована... 23.10.2026 в 5:34:16» (timestamp RestoreIB run16)
- **Симптомы**:
  - regress_run.py preflight: `(-2147352567, 'Exception occurred.', ..., 'Ошибка разделенного доступа к информационной базе', ...)`
  - COM-подключение: «Сеанс работы завершён администратором»
  - `rac infobase update --scheduled-jobs-deny=off` → rc=4294967295
  - RestoreIB вручную висит >3600с (не получает эксклюзив)

### Root Cause

После rollback (run8 или run16) deny не был снят из-за условия:
```python
if jobs_deny_prev == "off":
    rac_jobs_deny_set(False)
```

`jobs_deny_prev` был `"on"` (остаток предыдущего run), поэтому условие НЕ выполнилось.

Блокировка сохраняется в кластере ragent до перезапуска службы.

### Попытки снятия

1. **terminate sessions** (Designer d0ed9ca7, f7a866c1) — снято, но блокировка осталась
2. **Designer /UnlockIB** — не снял блокировку
3. **RestoreIB baseline_20241022_172316.dt вручную** — timeout 3600с (не получил эксклюзив)
4. **net stop '1C:Enterprise 8.5 Server Agent (x86-64)'** — `System error 5 has occurred. Access is denied.`

### Требуется

**Ручное восстановление (admin-права)**:

1. Остановить службу `1C:Enterprise 8.5 Server Agent (x86-64)`
2. Запустить службу снова
3. Снять deny:
   ```bash
   rac infobase update --cluster=67cdef87-7bfc-4dae-b8e4-3ea9f8529156 \
     --infobase=c6a442bb-d7a9-4d8b-a274-37ea859b26c1 \
     --scheduled-jobs-deny=off
   ```
4. Проверить доступность:
   ```bash
   python scripts/regress_run.py --rehearsal --real-authors --gate-timeout 7200
   ```

### Фикс для regress_run.py

**Проблема**: `if jobs_deny_prev == "off"` не снимает deny, если до rollback deny уже был включён.

**Решение**: безусловно снимать deny после успешного rollback:

```python
if dumped:
    rac_ib_sessions_terminate()
    rollback_ok = do_rollback(dump_dt)
    if not rollback_ok:
        log("!!!! СБОЙ ОТКАТА: восстановите вручную: 1cv8 DESIGNER"
            " /S %s /N<админ> /RestoreIB \"%s\"" % (CONN, dump_dt))
    else:
        # ВСЕГДА снимаем deny после успешного rollback
        rac_jobs_deny_set(False)
```

Или более безопасный вариант — восстановить исходное состояние:

```python
# В начале, перед gate:
jobs_deny_original = rac_jobs_deny_get()  # запомнили исходное

# Перед gate:
if not rac_jobs_deny_set(True):  # включили
    ...

# После rollback:
if dumped and rollback_ok:
    # Восстанавливаем исходное состояние (а не jobs_deny_prev)
    if jobs_deny_original == "off":
        rac_jobs_deny_set(False)
```

### Коммиты (готовы, не применены)

- **1b8f5c6**: `s004: MANAGER_ROLES += VAExtension_ОбщиеПрава` (launch EPF requires separate right)
- **8f279c0**: `regress: fix rollback degradation - terminate IB sessions before RestoreIB, keep jobs-deny until rollback done`
- **273abd6**: `t8_gate: post-A checkpoint - terminate 1CV8 only, WAIT OUT BackgroundJob`

### Следующая сессия

1. Дождаться ручного восстановления от пользователя (admin-перезапуск службы + deny off)
2. Запустить run9 заново
3. Если run9 успешен → зафиксировать фикс deny-rollback в regress_run.py
4. Если run9 блокирован снова → исследовать другой корень (PG vacuum, файловые блокировки)

---

**Итог ночного прогона**: заблокирован на этапе preflight из-за административной блокировки базы. Код фиксов готов (коммиты 1b8f5c6, 8f279c0, 273abd6), но применение невозможно без восстановления базы.

---

## Run9 — FAIL (gate preflight: зомби COMConnection-сеанс)

**Время**: 05:30 — 06:23

### Ход выполнения

- **05:30**: запуск `regress_run.py --rehearsal --real-authors`
- **05:30:41**: preflight 39.6s, sessions-terminate: 0 сеансов
- **05:33:32**: dump OK (171.2s, dt=1738MB)
- **05:33:32**: **gate exit=2** — preflight FAIL: онлайн-сеансы на базе (1): `Администратор (ОрловАВ) (COMConnection)`
- **06:23:33**: rollback FAILED (3000.1s timeout — scheduled-jobs-deny блокировка)

### Root Cause

Gate preflight (строка 654) обнаружил **зомби COMConnection-сеанс**, оставшийся от **предыдущей попытки** (возможно, сам run9, COM-агент не закрылся после rollback timeout 3000с).

**Regression в коде**: preflight вызывает `rac_sessions_online()` БЕЗ параметра `exclude_app_ids`, поэтому COMConnection считается блокирующим. Post-A checkpoint (строка 736) правильно исключает `("RAS", "COMConnection", "")`, но preflight — нет.

**Порядок выполнения правильный** (preflight до COM-connect), но зомби-сеанс от rollback не был закрыт.

### Фикс

**Выбор**: строгий префлайт (НЕ исключать COMConnection). `regress_run.py` должен терминировать ВСЕ сеансы ИБ (включая COMConnection) перед запуском гейта.

Правка `scripts/regress_run.py` строка ~500 (перед `subprocess.run` гейта):

```python
# Терминировать ВСЕ сеансы (включая зомби COMConnection) перед gate preflight
for attempt in range(3):
    n_term = rac_ib_sessions_terminate()  # без фильтра app-id
    sessions, _ = rac_ib_sessions_list(exclude_ras=True)
    log("   sessions-terminate попытка %d: terminated=%d alive=%d" % (attempt+1, n_term, len(sessions)))
    if not sessions:
        break
    time.sleep(10)
if sessions:
    log("CRITICAL: не удалось очистить сеансы ИБ перед gate preflight")
    return False
```

### Текущее состояние (06:47)

- База заблокирована: `scheduled-jobs-deny=on` (ошибка разделённого доступа)
- Сеансы ИБ: 0 (зомби COMConnection уже закрылся)
- Guard `20261022-082722`: удалён
- Требуется: admin-перезапуск службы `1C:Enterprise 8.5 Server Agent (x86-64)` → `rac infobase update --scheduled-jobs-deny=off`

### Следующие шаги

1. Дождаться ручного восстановления от пользователя (admin-права)
2. Применить фикс `regress_run.py` (терминация всех сеансов перед gate)
3. Запустить **run10** (run9 провалился)

### Финальное состояние (07:20)

**КРИТИЧНО**: Информационная база разрушена. COM-подключение выдаёт `Информационная база разрушена`, Designer не может подключиться (/DumpDBCfg, /TestOnly — no output).

**Причина**: rollback run9 (RestoreIB) не завершился корректно из-за блокировки `scheduled-jobs-deny=on` (3000с timeout), оставив базу в промежуточном состоянии.

**Требуется НЕМЕДЛЕННОЕ восстановление** (admin-права):

1. **Restart службы**: `1C:Enterprise 8.5 Server Agent (x86-64)` (Services.msc)
2. **Снять блокировку**: `rac infobase update --cluster=... --infobase=c6a442bb-... --scheduled-jobs-deny=off`
3. **Проверить целостность**: Designer `/TestOnly`
4. **При fail**: восстановление из backup (последний работающий — до run9, ~22.10.2026)

**Ночной прогон ПРЕРВАН**. База нерабочая, продолжение невозможно.

---

## Итоги ночного прогона (21-23.10.2026)

- **Run8**: провал (BackgroundJob 12min wait, post-A checkpoint застрял)
- **Run9**: провал (preflight FAIL: зомби COMConnection-сеанс)
- **Rollback run9**: КРИТИЧЕСКИЙ провал → база разрушена

**Код-фиксы готовы** (не применены, база недоступна):
- `1b8f5c6`: s004 MANAGER_ROLES += VAExtension_ОбщиеПрава
- `8f279c0`: regress rollback degradation fix (terminate sessions, keep deny)
- `273abd6`: t8_gate post-A checkpoint (terminate 1CV8 only, wait out BackgroundJob)

**Следующие шаги** (после восстановления базы):
1. Применить фикс `regress_run.py` (терминация всех сеансов перед gate preflight)
2. Применить коммиты 1b8f5c6, 8f279c0, 273abd6
3. Запустить run10 (тестирование полного цикла с фиксами)
