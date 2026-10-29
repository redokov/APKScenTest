# -*- coding: utf-8 -*-
"""s005 live acceptance: run ONE Vanessa feature via VA single (TESTMANAGER
pattern of run_va_smoke.py), verdict from ReturnStatus + /Out log.
Usage: python scripts/s005_va_run.py <feature.bsl.feature> <run-name> [timeout_sec]"""
import io, json, os, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V8C = r"C:\Program Files\1cv8\8.5.4.1683\bin\1cv8c.exe"
EPF = r"C:\MyProjects\APKTechPlan\tests\vanessa\vanessa-automation-single.epf"
BASE = r"localhost\dev_erpapk_demo"
ADMIN = "Администратор (ОрловАВ)"

PASS_LINE = "Выполнение сценариев закончено. Ошибок не было"
FAIL_LINE = "Выполнение сценариев закончено. БЫЛИ ОШИБКИ"
VERDICTS = {"0": "PASS", "1": "FAIL", "2": "FAIL/CONNECT",
            "3": "FAIL/NO-SCENARIOS", "4": "FAIL/ADDIN"}


def log(m):
    print(m, flush=True)


def main():
    feature = os.path.normpath(os.path.join(ROOT, sys.argv[1]))
    run_name = sys.argv[2]
    timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 900
    run_dir = os.path.join(ROOT, "tmp", "s005", "va", run_name)
    os.makedirs(run_dir, exist_ok=True)
    vap_path = os.path.join(run_dir, "VAParams.json")
    onec_log = os.path.join(run_dir, "va_1c.log")
    run_log = os.path.join(run_dir, "va_run.log")
    status_log = os.path.join(run_dir, "va_status.log")

    vap = {
        "ИмяСборки": "s005-" + run_name,
        "ВерсияПлатформы": "8.5.4",
        "КаталогПоискаВерсииПлатформы": r"C:\Program Files\1cv8",
        "СтрокаПодключенияКБазе": 'ENTERPRISE /S "%s" /N "%s" /P ""' % (BASE, ADMIN),
        "ПутьКVanessaAutomation": EPF,
        "КаталогФич": feature.replace("\\", "/"),
        "КаталогиБиблиотек": [],
        "КлиентыТестирования": [{
            "Имя": "Основной",
            "ПутьКИнфобазе": '/S "%s" /N "%s" /P ""' % (BASE, ADMIN),
            "ДопПараметры": "/DisableStartupMessages /DisableStartupDialogs",
            "ТипКлиента": "Тонкий",
            "ИмяКомпьютера": "localhost",
            "ПортЗапускаТестКлиента": "1538",
        }],
        "ВыполнитьСценарии": "Истина",
        "ЗавершитьРаботуСистемы": "Истина",
        "ЗакрытьTestClientПослеЗапускаСценариев": "Истина",
        "ДелатьЛогВыполненияСценариевВТекстовыйФайл": "Истина",
        "ИмяФайлаЛогВыполненияСценариев": run_log.replace("\\", "/"),
        "ВыгружатьСтатусВыполненияСценариевВФайл": "Истина",
        "ПутьКФайлуДляВыгрузкиСтатусаВыполненияСценариев":
            status_log.replace("\\", "/"),
        "ДелатьОтчетВФорматеАллюр": "Истина",
        "КаталогВыгрузкиAllureБазовый": os.path.join(run_dir, "allure").replace("\\", "/"),
        "ИмяТекущейСборки": "s005-" + run_name,
    }
    with io.open(vap_path, "w", encoding="utf-8") as f:
        json.dump(vap, f, ensure_ascii=False, indent=1)

    cmd = [V8C, "ENTERPRISE", "/TESTMANAGER", "/S", BASE, "/N", ADMIN, "/P", "",
           "/Out", onec_log, "/Execute", EPF,
           "/C", "StartFeaturePlayer;VAParams=" + vap_path.replace("\\", "/"),
           "/DisableStartupDialogs", "/DisableStartupMessages"]
    log("[run] " + " ".join(cmd))
    t0 = time.time()
    proc = subprocess.Popen(cmd)
    rc = None
    try:
        rc = proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)])
        log("[run] TIMEOUT after %ds" % timeout)
    dt = time.time() - t0

    body = ""
    if os.path.exists(onec_log):
        with io.open(onec_log, "r", encoding="utf-8", errors="replace") as f:
            body = f.read()
    status_body = ""
    if os.path.exists(status_log):
        with io.open(status_log, "r", encoding="utf-8-sig", errors="replace") as f:
            status_body = f.read().strip()
    verdict, src = "?", ""
    if status_body in VERDICTS:
        verdict, src = VERDICTS[status_body], "ReturnStatus=" + status_body
    elif PASS_LINE in body:
        verdict, src = "PASS", "out-log"
    elif FAIL_LINE in body:
        verdict, src = "FAIL", "out-log"
    log("[verdict] %s (%s), %.0f sec, rc=%s" % (verdict, src, dt, rc))
    log("[artifacts] %s" % run_dir)
    if verdict != "PASS":
        # print the failing step context for diagnosis
        lines = body.splitlines()
        for i, ln in enumerate(lines):
            if "не выполнен" in ln or "Ошибка" in ln[:40]:
                txt = "\n".join(lines[max(0, i - 2):i + 12])[:3000]
                enc = sys.stdout.encoding or "cp1251"
                print(txt.encode(enc, errors="replace").decode(enc), flush=True)
                break
        sys.exit(1)


if __name__ == "__main__":
    main()
