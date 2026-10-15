# -*- coding: utf-8 -*-
"""s2-T2 probe: 02-pl-auto фича (НВ00-000009, refs-фильтр) под Vanessa.

Образец: scripts/t8_probe6m2_run.py. Порт 487xx (s2), BUILD_NAME
s2-probe-plauto, VAParams: VanessaExt=Истина, UIAutomation=Истина,
ЭмулироватьДвиженияМышкиVanessaExt=Ложь. Вердикт — только ReturnStatus-файл
(код возврата процесса всегда 0). Итерации: run1/run2 (AC T2: rs=0 дважды).
"""
import io
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V8C = r"C:\Program Files\1cv8\8.5.4.1683\bin\1cv8c.exe"
EPF = r"C:\MyProjects\APKTechPlan\tests\vanessa\vanessa-automation-single.epf"
BASE = r"localhost\dev_erpapk_demo"
ADMIN = "Администратор (ОрловАВ)"

PORT = "48701"
BUILD_NAME = "s2-probe-plauto"
TIMEOUT = 600


def latest_plauto_feature():
    """Самая свежая сгенерённая фича 02-pl-auto-*."""
    runs = os.path.join(ROOT, "tests")
    best = None
    for name in sorted(os.listdir(runs), reverse=True):
        if not name.startswith("run-"):
            continue
        fdir = os.path.join(runs, name, "features")
        if not os.path.isdir(fdir):
            continue
        for f in os.listdir(fdir):
            if f.startswith("02-pl-auto-") and f.endswith(".feature"):
                cand = os.path.join(fdir, f)
                if best is None or os.path.getmtime(cand) > os.path.getmtime(best):
                    best = cand
        if best:
            return best
    return None


def main():
    run_no = "run%d" % int(os.environ.get("S2_PROBE_N", "1"))
    feature = sys.argv[1] if len(sys.argv) > 1 else latest_plauto_feature()
    if not feature or not os.path.exists(feature):
        print("[fail] фича 02-pl-auto не найдена (tests/run-*/features/)")
        return 1
    print("[feature] %s" % feature)

    run_dir = os.path.join(ROOT, "tmp", "s2", "probe-plauto-%s" % run_no)
    os.makedirs(run_dir, exist_ok=True)
    vap_path = os.path.join(run_dir, "VAParams.json")
    onec_log = os.path.join(run_dir, "1c_out.log")
    run_log = os.path.join(run_dir, "va_run.log")
    status_log = os.path.join(run_dir, "va_status.log")

    vap = {
        "ИмяСборки": BUILD_NAME,
        "ВерсияПлатформы": "8.5.4",
        "КаталогПоискаВерсииПлатформы": r"C:\Program Files\1cv8",
        "СтрокаПодключенияКБазе": 'ENTERPRISE /S "%s" /N "%s" /P ""' % (BASE, ADMIN),
        "ПутьКVanessaAutomation": EPF,
        "КаталогФич": feature.replace("\\", "/"),
        "КаталогиБиблиотек": [],
        "ДиапазонПортовTestclient": "%s-%s" % (PORT, PORT),
        "КлиентыТестирования": [{
            "Имя": "Основной",
            "ПутьКИнфобазе": '/S "%s" /N "%s" /P ""' % (BASE, ADMIN),
            "ДопПараметры": "/DisableStartupMessages /DisableStartupDialogs",
            "ТипКлиента": "Тонкий",
            "ИмяКомпьютера": "localhost",
            "ПортЗапускаТестКлиента": PORT,
        }],
        "ИспользоватьКомпонентуVanessaExt": "Истина",
        "ИспользоватьUIAutomation": "Истина",
        "ЭмулироватьДвиженияМышкиVanessaExt": "Ложь",
        "ВыполнитьСценарии": "Истина",
        "ЗавершитьРаботуСистемы": "Истина",
        "ЗакрытьTestClientПослеЗапускаСценариев": "Истина",
        "ДелатьЛогВыполненияСценариевВтекстовыйФайл": "Истина",
        "ИмяФайлаЛогВыполненияСценариев": run_log.replace("\\", "/"),
        "ВыгружатьСтатусВыполненияСценариевВФайл": "Истина",
        "ПутьКФайлуДляВыгрузкиСтатусаВыполненияСценариев": status_log.replace("\\", "/"),
    }
    with io.open(vap_path, "w", encoding="utf-8") as f:
        json.dump(vap, f, ensure_ascii=False, indent=1)

    # зачистка возможного сироты на своём порту
    try:
        out = subprocess.run(
            ["wmic", "process", "where",
             "name='1cv8c.exe'", "get", "ProcessId,CommandLine"],
            capture_output=True, text=True, timeout=15).stdout
        for line in out.splitlines():
            if ("-TPort %s" % PORT) in line or ("-TPort%s" % PORT) in line:
                pid = [p for p in line.split() if p.isdigit()]
                if pid:
                    subprocess.run(["taskkill", "/PID", pid[-1], "/T", "/F"],
                                   capture_output=True, timeout=15)
                    print("[cleanup] killed orphan TestClient pid=%s" % pid[-1])
    except Exception as e:
        print("[cleanup] skip: %s" % e)

    cmd = [
        V8C, "ENTERPRISE", "/TESTMANAGER",
        '/S', BASE, '/N', ADMIN, '/P', '',
        '/Out', onec_log,
        '/Execute', EPF,
        '/C', 'StartFeaturePlayer;VAParams=%s' % vap_path,
    ]
    print("[run] " + " ".join(cmd))
    t0 = time.time()
    try:
        p = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           timeout=TIMEOUT)
        print("[run] exit=%s за %.0f c" % (p.returncode, time.time() - t0))
    except subprocess.TimeoutExpired:
        print("[run] TIMEOUT after %s c" % TIMEOUT)
        return 2

    status_body = ""
    if os.path.exists(status_log):
        with io.open(status_log, "r", encoding="utf-8-sig", errors="replace") as f:
            status_body = f.read().strip()
    print("[verdict] ReturnStatus=%s" % status_body)

    if os.path.exists(run_log):
        with io.open(run_log, "r", encoding="utf-8", errors="replace") as f:
            body = f.read()
        sys.stdout.buffer.write(("\n===== va_run.log (%d b) =====\n" % len(body)).encode("utf-8"))
        sys.stdout.buffer.write(body.encode("utf-8", errors="replace"))
    else:
        print("[log] va_run.log отсутствует")
    return 0


if __name__ == "__main__":
    sys.exit(main())
