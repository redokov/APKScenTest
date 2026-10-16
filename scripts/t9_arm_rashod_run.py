# -*- coding: utf-8 -*-
"""s2-T9 probe: АРМ Расход топлива (период + ВыполнитьОтражение) под Vanessa.

Образец: scripts/t9_arm_zapravki_run.py. Порт 48644, BUILD_NAME
s2-t9-arm-rashod, пользователь — ОрловАВ. Вердикт — ReturnStatus-файл.
Итерации: S2_PROBE_N. Фича по умолчанию:
tmp/t9/arm-rashod/probe-arm-rashod.feature (аргумент argv[1] — override).
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
USER = "Администратор (ОрловАВ)"

PORT = "48644"
BUILD_NAME = "s2-t9-arm-rashod"
TIMEOUT = 600


def main():
    n = os.environ.get("S2_PROBE_N", "1")
    try:
        run_no = "run%d" % int(n)
    except ValueError:
        run_no = n
    feature = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "tmp", "t9", "arm-rashod", "probe-arm-rashod.feature")
    if not feature or not os.path.exists(feature):
        print("[fail] фича не найдена")
        return 1
    print("[feature] %s" % feature)

    run_dir = os.path.join(ROOT, "tmp", "t9", "arm-rashod/run-%s" % run_no)
    os.makedirs(run_dir, exist_ok=True)
    vap_path = os.path.join(run_dir, "VAParams.json")
    onec_log = os.path.join(run_dir, "1c_out.log")
    run_log = os.path.join(run_dir, "va_run.log")
    status_log = os.path.join(run_dir, "va_status.log")

    vap = {
        "ИмяСборки": BUILD_NAME,
        "ВерсияПлатформы": "8.5.4",
        "КаталогПоискаВерсииПлатформы": r"C:\Program Files\1cv8",
        "СтрокаПодключенияКБазе": 'ENTERPRISE /S "%s" /N "%s" /P ""' % (BASE, USER),
        "ПутьКVanessaAutomation": EPF,
        "КаталогФич": feature.replace("\\", "/"),
        "КаталогиБиблиотек": [],
        "ДиапазонПортовTestclient": "%s-%s" % (PORT, PORT),
        "КлиентыТестирования": [{
            "Имя": "Основной",
            "ПутьКИнфобазе": '/S "%s" /N "%s" /P ""' % (BASE, USER),
            "ДопПараметры": "/DisableStartupMessages /DisableStartupDialogs",
            "ТипКлиента": "Тонкий",
            "ИмяКомпьютера": "localhost",
            "ПортЗапускаТестКлиента": PORT,
        }],
        "ИспользоватьКомпонентуVanessaExt": "Истина",
        "ИспользоватьUIAutomation": "Истина",
        "ЭмулироватьДвиженияМышкиVanessaExt": "Ложь",
        "ЭмулироватьДвиженияМышки": "Ложь",
        "ЭмулироватьВводКлавиатурыVanessaExt": "Ложь",
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
        '/S', BASE, '/N', USER, '/P', '',
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
        with io.open(run_log, "r", encoding="utf-8-sig", errors="replace") as f:
            body = f.read()
        sys.stdout.buffer.write(("\n===== va_run.log (%d b) =====\n" % len(body)).encode("utf-8"))
        sys.stdout.buffer.write(body.encode("utf-8", errors="replace"))
    else:
        print("[log] va_run.log отсутствует")
    return 0


if __name__ == "__main__":
    sys.exit(main())
