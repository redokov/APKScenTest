# -*- coding: utf-8 -*-
"""Spike: Allure-отчёт из Vanessa Automation (single) на dev_erpapk_demo.

Запускает tests/features/smoke-01-connect.feature через TestManager c
VAParams, включающими Allure (КаталогВыгрузкиAllureБазовый — подкаталог на
сборку), затем инспектирует структуру allure-каталога для нашей сводки.

Результат: docs/spike-allure.md + артефакты в tmp/spike-allure/ (gitignored).
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

FEATURE = os.path.join(ROOT, "tests", "features", "smoke-01-connect.feature")
RUN_DIR = os.path.join(ROOT, "tmp", "spike-allure")
ALLURE_BASE = os.path.join(RUN_DIR, "allure-base")
BUILD_NAME = "spike-allure-01"

PASS_LINE = "Выполнение сценариев закончено. Ошибок не было"
FAIL_LINE = "Выполнение сценариев закончено. БЫЛИ ОШИБКИ"
TIMEOUT = 420


def log(m):
    print(m)


def main():
    os.makedirs(ALLURE_BASE, exist_ok=True)
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
        # --- Allure ---
        "ДелатьОтчетВФорматеАллюр": "Истина",
        "КаталогВыгрузкиAllureБазовый": ALLURE_BASE.replace("\\", "/"),
        "ИмяТекущейСборки": BUILD_NAME,
        "ДобавлятьКИмениСценарияУсловияВыгрузки": "Истина",
    }
    with io.open(vap_path, "w", encoding="utf-8") as f:
        json.dump(vap, f, ensure_ascii=False, indent=1)

    cmd = [
        V8C, "ENTERPRISE", "/TESTMANAGER",
        '/S', BASE, '/N', ADMIN, '/P', '',
        '/Out', onec_log,
        '/Execute', EPF,
        '/C', 'StartFeaturePlayer;VAParams=%s' % vap_path,
    ]
    log("[run] " + " ".join(cmd))
    t0 = time.time()
    p = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=TIMEOUT)
    dt = time.time() - t0
    log("[run] exit=%s за %.0f c" % (p.returncode, dt))

    body = ""
    if os.path.exists(onec_log):
        with io.open(onec_log, "r", encoding="utf-8", errors="replace") as f:
            body = f.read()
    # verdict: ReturnStatus file is authoritative (0=OK, 1=scenario errors,
    # 2=testclient/connect problems, 3=no scenarios, 4=addin install fail)
    status_body = ""
    if os.path.exists(status_log):
        with io.open(status_log, "r", encoding="utf-8-sig",
                     errors="replace") as f:
            status_body = f.read().strip()
    verdict = "?"
    verdict_src = ""
    if status_body in ("0", "1", "2", "3", "4"):
        verdict = {"0": "PASS", "1": "FAIL", "2": "FAIL/CONNECT",
                   "3": "FAIL/NO-SCENARIOS", "4": "FAIL/ADDIN"}[status_body]
        verdict_src = "ReturnStatus-файл: %s" % status_body
    elif PASS_LINE in body:
        verdict, verdict_src = "PASS", "строка в /Out-логе"
    elif FAIL_LINE in body:
        verdict, verdict_src = "FAIL", "строка в /Out-логе"
    log("[verdict] %s (%s)" % (verdict, verdict_src))

    # inspect allure
    allure_files = []
    for dirpath, _dirs, files in os.walk(ALLURE_BASE):
        for fn in files:
            allure_files.append(os.path.relpath(os.path.join(dirpath, fn),
                                                ALLURE_BASE))
    log("[allure] файлов: %d" % len(allure_files))
    sample = None
    for rel in sorted(allure_files, key=lambda r: (0 if r.endswith("-result.json") else 1, r)):
        if rel.endswith(".json"):
            with io.open(os.path.join(ALLURE_BASE, rel), "r",
                         encoding="utf-8", errors="replace") as f:
                sample = (rel, f.read())
            break

    md = ["# Спайк: Allure-отчёт из VA (single 1.2.043)", "",
          "Фича: `%s`. База: `%s`. Вердикт: **%s** (%s; %.0f c)." %
          (os.path.basename(FEATURE), BASE, verdict, verdict_src, dt), "",
          "## Коды ReturnStatus (первичный вердикт)", "",
          "0=ок · 1=ошибки сценариев · 2=проблемы подключения TestClient ·",
          "3=нет сценариев · 4=не встала компонента.", "",
          "## Структура allure-каталога (`КаталогВыгрузкиAllureБазовый`)", ""]
    if allure_files:
        md.append("Всего файлов: %d. Примеры:" % len(allure_files))
        md += ["- " + rel for rel in allure_files[:20]]
    else:
        md.append("Каталог ПУСТ — отчёт не сформировался (см. вердикт/лог).")
    md += ["", "## Образец result-json", ""]
    if sample:
        md += ["`%s`:" % sample[0], "", "```json",
               sample[1][:4000], "```"]
    md += ["", "## Лог 1С (хвост)", "", "```",
           body[-1500:] if body else "(пусто)", "```"]
    out_md = os.path.join(ROOT, "docs", "spike-allure.md")
    with io.open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    log("[report] " + out_md)
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
