# -*- coding: utf-8 -*-
"""S003 Регресс-конвейер: обёртка над t8_gate.py (design.md спеки 003).

Режимы (D-004/D-007):
  --rehearsal          дамп -> E2E-гейт -> откат -> отчёт (без обновления)
  --update <cf|dt>     дамп -> применение обновления -> гейт -> откат -> отчёт

Гейт t8_gate.py вызывается подпроцессом БЕЗ правок (TD-001).
Откат в finally при любом исходе (FR-002, TD-002/TD-004: дампы не удаляются).
Baseline: tests/baseline/baseline.json под git (D-005), ключ (scenario, user)
(TD-003). Exit: 0 = зелёный+без регрессий; 1 = красный гейт/есть REGRESSION;
2 = инфраструктурный сбой (дамп/обновление/откат/preflight).
"""
import argparse
import datetime
import glob
import io
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = r"C:\MyProjects\APKScenTest"
V8 = r"C:\Program Files\1cv8\8.5.4.1683\bin\1cv8.exe"
CONN = r"localhost\dev_erpapk_demo"
COM_CONN = "Srvr='localhost';Ref='dev_erpapk_demo';Usr='%s';Pwd='';"
ADMIN = "Администратор (ОрловАВ)"

GATE = os.path.join(ROOT, "scripts", "t8_gate.py")
GATE_SETTINGS = os.path.join(ROOT, "tmp", "t8", "preprocessor-settings.json")
WEB_URL_DEFAULT = "http://localhost:9093/dev_erpapk_demo"

# rac: запрет регл. заданий на время прогона (эксклюзив Dump/RestoreIB;
# открытие 19.10: фоновое задание базы держало блокировку — дамп не
# получил эксклюзив за 900 с). Кластер/ИБ демо-базы фиксированы.
RAC = r"C:\Program Files\1cv8\8.5.4.1683\bin\rac.exe"
RAC_CLUSTER = "67cdef87-7bfc-4dae-b8e4-3ea9f8529156"
RAC_INFOBASE = "c6a442bb-d7a9-4d8b-a274-37ea859b26c1"  # dev_erpapk_demo
RUNS_DIR = os.path.join(ROOT, "tests")
BASELINE = os.path.join(ROOT, "tests", "baseline", "baseline.json")
BASELINE_HIST = os.path.join(ROOT, "tests", "baseline", "history")

TIMEOUT_DUMP = 900          # факт T1: 207 c, запас x4
TIMEOUT_RESTORE = 3000      # restore ~800-900 штатно; при деградации среды
                              # бывало дольше — kill посреди RestoreIB калечит
                              # авторизацию (инцидент 20261019-103036)
TIMEOUT_UPDATE = 1800       # cf: LoadCfg+UpdateDBCfg / dt: RestoreIB
TIMEOUT_GATE = 45 * 60      # E2E <= 40 мин (NFR-001) + запас
MIN_FREE_GB = 5.0

EXIT_OK, EXIT_RED, EXIT_INFRA = 0, 1, 2

_phases = []   # [(name, dur_sec, note)]
_ts = None
_dir = None
_logf = None


def log(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    print(line)
    if _logf:
        _logf.write(line + "\n")
        _logf.flush()


def phase(name, dur, note=""):
    _phases.append((name, dur, note))
    log("phase %-9s %6.1fs %s" % (name, dur, note))


def designer(ops, log_name, timeout):
    """Пакетная команда Конфигатора. Возвращает (ok, dump_result, tail)."""
    out_log = os.path.join(_dir, log_name)
    res_file = os.path.join(_dir, log_name + ".result")
    for p in (out_log, res_file):
        if os.path.exists(p):
            os.remove(p)
    cmd = [V8, "DESIGNER", "/S", CONN, "/N" + ADMIN] + ops + \
          ["/Out", out_log, "/DumpResult", res_file]
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, "timeout", ""
    dur = time.time() - t0
    code = io.open(res_file, encoding="utf-8-sig",
                   errors="replace").read().strip() \
        if os.path.exists(res_file) else "no-result"
    tail = "\n".join(io.open(out_log, encoding="utf-8-sig",
                             errors="replace").read().splitlines()[-8:]) \
        if os.path.exists(out_log) else ""
    ok = (proc.returncode == 0 and code == "0")
    log("   designer %s: exit=%s result=%s dur=%.1fs"
        % (log_name, proc.returncode, code, dur))
    if not ok and tail:
        log("   /Out tail: %s" % tail.replace("\n", " | ")[:400])
    return ok, code, tail


def preflight(args):
    t0 = time.time()
    free = shutil.disk_usage(_dir).free / 1024.0 ** 3
    if free < MIN_FREE_GB:
        log("[preflight] FAIL: свободно %.1f ГБ < %.1f ГБ" % (free, MIN_FREE_GB))
        return False
    if args.update:
        p = args.update
        if not os.path.isfile(p) or os.path.getsize(p) < 1024:
            log("[preflight] FAIL: артефакт обновления не найден/пуст: %s" % p)
            return False
        if not p.lower().endswith((".cf", ".dt")):
            log("[preflight] FAIL: неизвестный тип артефакта (нужен .cf/.dt): %s" % p)
            return False
    if args.baseline_dt:
        p = args.baseline_dt
        if not os.path.isfile(p) or os.path.getsize(p) < 1024 * 1024:
            log("[preflight] FAIL: baseline-dt не найден/пуст: %s" % p)
            return False
        if not p.lower().endswith(".dt"):
            log("[preflight] FAIL: baseline-dt должен быть .dt: %s" % p)
            return False
    if args.web_client:
        import urllib.error
        import urllib.request
        try:
            urllib.request.urlopen(args.web_url, timeout=15)
        except urllib.error.HTTPError:
            pass  # сервер отвечает (любой HTTP-код) — публикация жива
        except Exception as e:
            log("[preflight] FAIL: веб-публикация недоступна (%s): %s"
                % (args.web_url, str(e)[:150]))
            return False
    try:
        import win32com.client
        agent = win32com.client.Dispatch("V85.COMConnector").Connect(
            COM_CONN % ADMIN)
        del agent
    except Exception as e:
        log("[preflight] FAIL: база недоступна (COM): %s" % str(e)[:200])
        return False
    phase("preflight", time.time() - t0, "free=%.1fGB" % free)
    return True


def do_dump():
    dt = os.path.join(_dir, "pre-update.dt")
    t0 = time.time()
    ok, code, tail = designer(["/DumpIB", dt], "dump.log", TIMEOUT_DUMP)
    phase("dump", time.time() - t0,
          "dt=%.0fMB" % (os.path.getsize(dt) / 1048576.0
                         if os.path.exists(dt) else 0))
    return ok, dt


def do_update(path, dump_dt):
    """Применение 'обновления' (design.md §4.3). Возвращает (ok, kind)."""
    t0 = time.time()
    if path.lower().endswith(".dt"):
        ok, code, tail = designer(["/RestoreIB", path], "update.log",
                                  TIMEOUT_UPDATE)
        kind = "dt-restore"
    else:
        ok1, code, tail = designer(["/LoadCfg", path], "update.log",
                                   TIMEOUT_UPDATE)
        if not ok1:
            phase("update", time.time() - t0, "FAIL LoadCfg")
            return False, "cf-loadcfg"
        ok, code, tail = designer(["/UpdateDBCfg"], "update-dbcfg.log",
                                  TIMEOUT_UPDATE)
        kind = "cf-loadcfg+updatedbcfg"
    phase("update", time.time() - t0, "" if ok else "FAILED")
    return ok, kind


def do_baseline_restore(path):
    """TD-007: RestoreIB known-good dt перед гейтом (design.md §13)."""
    t0 = time.time()
    ok, code, tail = designer(["/RestoreIB", path], "baseline-restore.log",
                              TIMEOUT_UPDATE)
    phase("baseline-restore", time.time() - t0, "OK" if ok else "FAILED")
    return ok


def do_rollback(dump_dt):
    t0 = time.time()
    ok, code, tail = designer(["/RestoreIB", dump_dt], "rollback.log",
                              TIMEOUT_RESTORE)
    phase("rollback", time.time() - t0, "OK" if ok else "FAILED")
    return ok


def rac_jobs_deny_get():
    """Текущее значение scheduled-jobs-deny ИБ ('on'/'off'/None)."""
    try:
        out = subprocess.run(
            [RAC, "infobase", "info", "--cluster=" + RAC_CLUSTER,
             "--infobase=" + RAC_INFOBASE],
            capture_output=True, timeout=60).stdout
    except Exception as e:
        log("   rac infobase info FAIL: %s" % str(e)[:150])
        return None
    for line in out.decode("cp866", errors="replace").splitlines():
        if line.strip().startswith("scheduled-jobs-deny"):
            return line.split(":", 1)[1].strip()
    return None


def rac_jobs_deny_set(on):
    """Установить scheduled-jobs-deny=on/off. Возвращает ok."""
    try:
        rc = subprocess.run(
            [RAC, "infobase", "update", "--cluster=" + RAC_CLUSTER,
             "--infobase=" + RAC_INFOBASE,
             "--scheduled-jobs-deny=" + ("on" if on else "off")],
            capture_output=True, timeout=60)
    except Exception as e:
        log("   rac infobase update FAIL: %s" % str(e)[:150])
        return False
    ok = rc.returncode == 0
    log("   scheduled-jobs-deny=%s: %s" % ("on" if on else "off",
                                           "OK" if ok else "FAIL"))
    return ok


def patch_settings_for_web(args):
    """T7 (FR-007): clientType=Web + webUrl в настройках гейта.

    Гейт (t8_gate.py) читает tmp/t8/preprocessor-settings.json как есть —
    правка файла настроек вместо правки гейта (TD-001). Возвращает путь
    бэкапа для восстановления в finally.
    """
    backup = GATE_SETTINGS + ".regress-bak"
    shutil.copy2(GATE_SETTINGS, backup)
    data = json.loads(io.open(GATE_SETTINGS, encoding="utf-8-sig").read())
    data["clientType"] = "Web"
    data["webUrl"] = args.web_url
    io.open(GATE_SETTINGS, "w", encoding="utf-8").write(
        json.dumps(data, ensure_ascii=False, indent=1))
    log("   gate-settings: clientType=Web, webUrl=%s (backup: %s)"
        % (args.web_url, os.path.basename(backup)))
    return backup


def restore_settings(backup):
    if backup and os.path.exists(backup):
        shutil.copy2(backup, GATE_SETTINGS)
        os.remove(backup)
        log("   gate-settings: восстановлены из backup")


def run_gate(gate_timeout):
    t0 = time.time()
    gate_log = os.path.join(_dir, "gate-console.log")
    with io.open(gate_log, "w", encoding="utf-8") as fp:
        try:
            proc = subprocess.run(
                [sys.executable, GATE], stdout=fp,
                stderr=subprocess.STDOUT, timeout=gate_timeout,
                cwd=ROOT)
            rc = proc.returncode
        except subprocess.TimeoutExpired:
            rc = -1
    phase("gate", time.time() - t0, "exit=%s" % rc)
    return rc


def latest_run_dir():
    dirs = glob.glob(os.path.join(RUNS_DIR, "run-*"))
    if not dirs:
        return None
    return max(dirs, key=os.path.getmtime)


def load_summary():
    rd = latest_run_dir()
    if not rd:
        return None, None
    path = os.path.join(rd, "summary.json")
    if not os.path.exists(path):
        return rd, None
    try:
        return rd, json.loads(io.open(path, encoding="utf-8-sig").read())
    except Exception:
        return rd, None


# ---------------- baseline / diff (TD-003, D-005) ----------------

def diff_classes(base_scen, cur_scen):
    """Классы по ключу (scenario, user): REGRESSION/IMPROVED/NEW/MISSING/="""
    BAD = ("failed", "broken", "timeout", "unknown")
    base = {}
    for s in base_scen or []:
        base[(s.get("scenario"), s.get("user"))] = s.get("status")
    out = []
    for s in cur_scen or []:
        key = (s.get("scenario"), s.get("user"))
        cur_st = s.get("status")
        if key not in base:
            cls = "NEW"
        else:
            b = base[key]
            if b == cur_st:
                cls = "="
            elif b in BAD and cur_st == "passed":
                cls = "IMPROVED"
            elif b == "passed" and cur_st in BAD:
                cls = "REGRESSION"
            else:
                cls = "="
        out.append((key[0], key[1], cur_st, cls))
    cur_keys = {(s.get("scenario"), s.get("user")) for s in cur_scen or []}
    for key, b in base.items():
        if key not in cur_keys:
            out.append((key[0], key[1], None, "MISSING"))
    return out


def read_baseline():
    if not os.path.exists(BASELINE):
        return None
    try:
        return json.loads(io.open(BASELINE, encoding="utf-8-sig").read())
    except Exception:
        return None


def write_baseline(run_dir, summary):
    os.makedirs(os.path.dirname(BASELINE), exist_ok=True)
    old = read_baseline()
    if old:
        os.makedirs(BASELINE_HIST, exist_ok=True)
        hist = os.path.join(BASELINE_HIST,
                            old.get("baselineOf", "unknown") + ".json")
        io.open(hist, "w", encoding="utf-8").write(
            json.dumps(old, ensure_ascii=False, indent=1))
    data = {
        "baselineOf": os.path.basename(run_dir),
        "createdAt": datetime.datetime.now().isoformat(timespec="seconds"),
        "totals": summary.get("totals", {}),
        "scenarios": [
            {"scenario": s.get("scenario"), "user": s.get("user"),
             "status": s.get("status")}
            for s in summary.get("scenarios", [])],
        "runDir": os.path.relpath(run_dir, ROOT).replace("\\", "/"),
    }
    io.open(BASELINE, "w", encoding="utf-8").write(
        json.dumps(data, ensure_ascii=False, indent=1))
    return data


def build_report(run_dir, summary, base, gate_rc, rollback_ok, upd_kind):
    rep_md = os.path.join(_dir, "regress-report.md")
    rep_js = os.path.join(_dir, "regress-summary.json")
    rows = []
    regressions = 0
    if summary:
        diffs = diff_classes(base.get("scenarios") if base else None,
                            summary.get("scenarios")) if base else None
        for s in summary.get("scenarios", []):
            cls = "n/a"
            if diffs:
                cls = next((d[3] for d in diffs
                            if d[0] == s.get("scenario")
                            and d[1] == s.get("user")), "n/a")
            if cls == "REGRESSION":
                regressions += 1
            rows.append((s.get("scenario"), s.get("user"),
                         s.get("status"), cls,
                         round(s.get("durationMs", 0) / 1000.0, 1)))
        if diffs:
            regressions += sum(1 for d in diffs if d[3] == "MISSING")
    with io.open(rep_md, "w", encoding="utf-8") as f:
        f.write(u"# Регресс-отчёт %s\n\n" % _ts)
        f.write(u"- режим: %s\n" % upd_kind)
        f.write(u"- gate exit: %s; rollback: %s\n" %
                (gate_rc, "OK" if rollback_ok else "FAILED"))
        f.write(u"- run-каталог: %s\n" % run_dir)
        f.write(u"- baseline: %s\n\n" %
                (base.get("baselineOf") if base else u"нет (сравнение n/a)"))
        if summary:
            t = summary.get("totals", {})
            f.write(u"## Totals\n\n- сценариев: %s, passed: %s, failed: %s, "
                    u"broken: %s, timeout: %s, unknown: %s\n\n"
                    % (t.get("scenarios"), t.get("passed"), t.get("failed"),
                       t.get("broken"), t.get("timeout"), t.get("unknown")))
        f.write(u"## Сценарии\n\n| Сценарий | Пользователь | Статус |"
                u" vs baseline | Длит., с |\n|---|---|---|---|---|\n")
        for r in rows:
            f.write(u"| %s | %s | %s | %s | %s |\n" % r)
        if base:
            f.write(u"\nРегрессий (REGRESSION+MISSING): %d\n" % regressions)
        f.write(u"\n## Батчи\n\n| Пользователь | rs | verdict | пароли |"
                u" ЗОД | сек |\n|---|---|---|---|---|---|\n")
        for b in (summary or {}).get("batches", []):
            f.write(u"| %s | %s | %s | %s | %s | %s |\n" %
                    (b.get("user"), b.get("returnStatus"), b.get("verdict"),
                     b.get("passwordRestored"), b.get("zodRestored"),
                     b.get("durationSec")))
        f.write(u"\n## Фазы\n\n| Фаза | Сек | Примечание |\n|---|---|---|\n")
        for (n, d, note) in _phases:
            f.write(u"| %s | %.1f | %s |\n" % (n, d, note))
    io.open(rep_js, "w", encoding="utf-8").write(json.dumps({
        "ts": _ts, "runDir": run_dir, "gateExit": gate_rc,
        "rollbackOK": rollback_ok, "regressions": regressions,
        "totals": (summary or {}).get("totals", {}),
        "phases": [{"phase": n, "sec": round(d, 1), "note": s}
                   for (n, d, s) in _phases]},
        ensure_ascii=False, indent=1))
    return regressions, rep_md


def main():
    global _ts, _dir, _logf
    ap = argparse.ArgumentParser(description="S003 регресс-конвейер")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--rehearsal", action="store_true")
    g.add_argument("--update", metavar="PATH.cf|dt")
    ap.add_argument("--baseline-dt", metavar="FILE.dt",
                   help="RestoreIB known-good dt перед гейтом (TD-007, "
                        "только с --rehearsal)")
    ap.add_argument("--web-client", action="store_true",
                   help="T7 (FR-007): ТипКлиента=Web в VAParams батчей")
    ap.add_argument("--web-url", default=WEB_URL_DEFAULT,
                   help="URL веб-публикации базы (по умолчанию %s)"
                        % WEB_URL_DEFAULT)
    ap.add_argument("--set-baseline", action="store_true")
    ap.add_argument("--no-compare", action="store_true")
    ap.add_argument("--gate-timeout", type=int, default=TIMEOUT_GATE)
    args = ap.parse_args()

    _ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    _dir = os.path.join(ROOT, "tmp", "regress", _ts)
    os.makedirs(_dir, exist_ok=True)
    _logf = io.open(os.path.join(_dir, "regress.log"), "w",
                    encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")

    mode = ("--update %s" % args.update) if args.update else "--rehearsal"
    if args.update and args.baseline_dt:
        log("REGRESS %s: ABORT: --baseline-dt и --update взаимоисключаемы "
            "(RestoreIB baseline-dt затёр бы обновление), база не менялась"
            % _ts)
        return EXIT_INFRA
    if args.baseline_dt and not args.rehearsal:
        log("REGRESS %s: ABORT: --baseline-dt допустим только с --rehearsal, "
            "база не менялась" % _ts)
        return EXIT_INFRA
    if args.baseline_dt:
        mode += " --baseline-dt %s" % args.baseline_dt
    if args.web_client:
        mode += " --web-client %s" % args.web_url
    log("REGRESS %s start: %s" % (_ts, mode))

    if not preflight(args):
        log("REGRESS %s: ABORT (preflight), база не менялась" % _ts)
        return EXIT_INFRA

    dumped = False
    dump_dt = None
    settings_bak = None
    jobs_deny_prev = None
    update_ok, upd_kind = True, "rehearsal (без обновления)"
    gate_rc = None
    rollback_ok = None
    try:
        # Фоновые задания ИБ не должны стартовать на время дампа/restore:
        # они держат сеансы/блокировки — эксклюзив не выдаётся (19.10).
        jobs_deny_prev = rac_jobs_deny_get()
        if jobs_deny_prev == "off":
            if not rac_jobs_deny_set(True):
                log("REGRESS %s: WARN: scheduled-jobs-deny не включён — "
                    "дамп может ждать сеансы фоновых заданий" % _ts)
        ok, dump_dt = do_dump()
        if not ok:
            log("REGRESS %s: ABORT (dump FAILED), база не менялась" % _ts)
            return EXIT_INFRA
        dumped = True
        if args.baseline_dt:
            upd_kind = "rehearsal + baseline-dt"
            if not do_baseline_restore(args.baseline_dt):
                log("REGRESS %s: baseline-restore FAILED -> откат" % _ts)
                return EXIT_INFRA
        if args.update:
            update_ok, upd_kind = do_update(args.update, dump_dt)
            if not update_ok:
                log("REGRESS %s: update FAILED -> откат" % _ts)
                return EXIT_INFRA
        if args.web_client:
            upd_kind += " + web-client"
            settings_bak = patch_settings_for_web(args)
        gate_rc = run_gate(args.gate_timeout)
    finally:
        restore_settings(settings_bak)
        if jobs_deny_prev == "off":
            rac_jobs_deny_set(False)
        if dumped:
            rollback_ok = do_rollback(dump_dt)
            if not rollback_ok:
                log("!!!! СБОЙ ОТКАТА: восстановите вручную: 1cv8 DESIGNER"
                    " /S %s /N<админ> /RestoreIB \"%s\"" % (CONN, dump_dt))

    run_dir, summary = load_summary()
    base = None if args.no_compare else read_baseline()
    regressions, rep_md = build_report(run_dir, summary, base,
                                        gate_rc, rollback_ok, upd_kind)

    if args.set_baseline:
        if summary and gate_rc == 0 and summary.get("totals", {}).get("failed", 1) == 0 \
                and summary.get("totals", {}).get("broken", 1) == 0:
            wb = write_baseline(run_dir, summary)
            log("baseline обновлён: %s" % wb.get("baselineOf"))
        else:
            log("baseline НЕ обновлён: гейт не зелёный")

    green = bool(summary) and gate_rc == 0 and \
        summary.get("totals", {}).get("passed") == \
        summary.get("totals", {}).get("scenarios")
    code = EXIT_OK if (green and (args.no_compare or not base
                                  or regressions == 0)) else \
        (EXIT_RED if summary else EXIT_INFRA)
    log("REGRESS %s: %s passed, regressions=%s, rollback=%s, report=%s"
        % (_ts,
           "%s/%s" % (summary.get("totals", {}).get("passed"),
                      summary.get("totals", {}).get("scenarios"))
           if summary else "no-summary",
           regressions if base else "n/a",
           "OK" if rollback_ok else "FAILED", rep_md))
    log("REGRESS %s: exit=%d" % (_ts, code))
    return code


if __name__ == "__main__":
    sys.exit(main())
