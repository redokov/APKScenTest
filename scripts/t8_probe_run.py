# -*- coding: utf-8 -*-
# T8 probe: какие VA-шаги работают в ТЧ ВыполненныеРаботы ПОСЛЕ выбора из
# выпадающего списка (attempt 8 упал на Активизировать/Гектаров:
# «Неподходящее состояние элемента управления»).
# 4 сценария-варианта в одной фиче; вердикт по логу шагов (не ReturnStatus).
# База dev_erpapk_demo, пользователь Администратор (ОрловАВ) БЕЗ записи
# документов (Провести в зонде НЕТ). Порт 48503, сироты зачищаются.
import io
import json
import os
import subprocess
import sys
import time

ROOT = r"C:\MyProjects\APKScenTest"
V8C = r"C:\Program Files\1cv8\8.5.4.1683\bin\1cv8c.exe"
EPF = r"C:\MyProjects\APKTechPlan\tests\vanessa\vanessa-automation-single.epf"
BASE = r"localhost\dev_erpapk_demo"
ADMIN = "Администратор (ОрловАВ)"
FEATURE = os.path.join(ROOT, "tmp", "t8", "probe-vr.feature")
RUN_DIR = os.path.join(ROOT, "tmp", "t8", "probe")
PORT = "48503"
TIMEOUT = 420

sys.stdout.reconfigure(encoding="utf-8")


def kill_orphans():
    out = subprocess.run(
        ["wmic", "process", "where", "name='1cv8c.exe'", "get",
         "ProcessId,CommandLine"],
        capture_output=True, text=True).stdout or ""
    for line in out.splitlines():
        if ("-TPort " + PORT) in line:
            pid = line.strip().split()[-1]
            subprocess.run(["taskkill", "/PID", pid, "/T", "/F"],
                           capture_output=True)
            print("[cleanup] killed orphan TestClient pid=%s" % pid)


def main():
    os.makedirs(RUN_DIR, exist_ok=True)
    kill_orphans()
    vap_path = os.path.join(RUN_DIR, "VAParams.json")
    onec_log = os.path.join(RUN_DIR, "1c_out.log")
    run_log = os.path.join(RUN_DIR, "va_run.log")
    status_log = os.path.join(RUN_DIR, "va_status.log")
    vap = {
        "ИмяСборки": "t8-probe-vr",
        "ВерсияПлатформы": "8.5.4",
        "КаталогПоискаВерсииПлатформы": r"C:\Program Files\1cv8",
        "СтрокаПодключенияКБазе": 'ENTERPRISE /S "%s" /N "%s" /P ""' % (BASE, ADMIN),
        "ПутьКVanessaAutomation": EPF,
        "КаталогФич": FEATURE.replace("\\", "/"),
        "КаталогиБиблиотек": [],
        "ДиапазонПортовTestclient": PORT + "-" + PORT,
        "КлиентыТестирования": [{
            "Имя": "Основной",
            "ПутьКИнфобазе": '/S "%s" /N "%s" /P ""' % (BASE, ADMIN),
            "ДопПараметры": "/DisableStartupMessages /DisableStartupDialogs",
            "ТипКлиента": "Тонкий",
            "ИмяКомпьютера": "localhost",
            "ПортЗапускаТестКлиента": PORT,
        }],
        "ВыполнитьСценарии": "Истина",
        "ЗавершитьРаботуСистемы": "Истина",
        "ЗакрытьTestClientПослеЗапускаСценариев": "Истина",
        "ДелатьЛогВыполненияСценариевВТекстовыйФайл": "Истина",
        "ИмяФайлаЛогВыполненияСценариев": run_log.replace("\\", "/"),
        "ВыгружатьСтатусВыполненияСценариевВФайл": "Истина",
        "ПутьКФайлуДляВыгрузкиСтатусаВыполненияСценариев":
            status_log.replace("\\", "/"),
    }
    with io.open(vap_path, "w", encoding="utf-8") as f:
        json.dump(vap, f, ensure_ascii=False, indent=1)
    cmd = [V8C, "ENTERPRISE", "/TESTMANAGER", "/S", BASE, "/N", ADMIN,
           "/P", "", "/Out", onec_log, "/Execute", EPF,
           "/C", "StartFeaturePlayer;VAParams=%s" % vap_path]
    print("[run] VA probe, feature=%s" % FEATURE)
    t0 = time.time()
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        print("[run] TIMEOUT %d c" % TIMEOUT)
    print("[run] done за %.0f c" % (time.time() - t0))
    kill_orphans()
    body = ""
    if os.path.exists(run_log):
        body = io.open(run_log, encoding="utf-8-sig", errors="replace").read()
    print("=== va_run.log (шаги/ошибки) ===")
    for line in body.splitlines():
        s = line.strip()
        if ("Шаг (" in s or "Failed:" in s or "Pending:" in s
                or "Сценарий:" in s or "Ошиб" in s):
            print(line)
    status = ""
    if os.path.exists(status_log):
        status = io.open(status_log, encoding="utf-8-sig",
                         errors="replace").read().strip()
    print("=== ReturnStatus: %s ===" % status)
    return 0


if __name__ == "__main__":
    sys.exit(main())
