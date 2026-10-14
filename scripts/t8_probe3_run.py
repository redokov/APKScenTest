# -*- coding: utf-8 -*-
"""T8 probe2: полный поток (шапка+ГСМ+Заправки+ВР-рецепт), 2 сценария порядка.

Прогоняет tmp/t8/probe3-gektarov.feature через VA single как
Администратор (ОрловАВ) БЕЗ подмены пароля, без записи/проведения,
порт 48604 (свой, изолированный). Вердикт по ReturnStatus-файлу.
Копия scripts/t8_probe_gektarov_run.py с другими константами.
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

FEATURE = os.path.join(ROOT, "tmp", "t8", "probe3-gektarov.feature")
RUN_DIR = os.path.join(ROOT, "tmp", "t8", "probe3-run-gektarov")
BUILD_NAME = "t8-probe3-gektarov"
PORT = "48605"

TIMEOUT = 420


def main():
    os.makedirs(RUN_DIR, exist_ok=True)
    vap_path = os.path.join(RUN_DIR, "VAParams.json")
    onec_log = os.path.join(RUN_DIR, "1c_out.log")
    run_log = os.path.join(RUN_DIR, "va_run.log")
    status_log = os.path.join(RUN_DIR, "va_status.log")

    vap = {
        "ИмяСборки": BUILD_NAME,
        "ВерсияПлатформы": "8.5.4",
        "КаталогПоискаВерсииПлатформы": r"C:\Program Files\1cv8",
        "СтрокаПодключенияКБазе": 'ENTERPRISE /S "%s" /N "%s" /P ""' % (BASE, ADMIN),
        "ПутьКVanessaAutomation": EPF,
        "КаталогФич": FEATURE.replace("\\", "/"),
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
        "ВыполнитьСценарии": "Истина",
        "ЗавершитьРаботуСистемы": "Истина",
        "ЗакрытьTestClientПослеЗапускаСценариев": "Истина",
        "ДелатьЛогВыполненияСценариевВТекстовыйФайл": "Истина",
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
    p = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=TIMEOUT)
    dt = time.time() - t0
    print("[run] exit=%s за %.0f c" % (p.returncode, dt))

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
