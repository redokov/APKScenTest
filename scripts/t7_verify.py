# -*- coding: utf-8 -*-
"""T7: сверка структуры summary.json с контрактом design.md §4.8/§4.9 и
AC («summary.json валиден и содержит статусы всех батчей прогона T6»).
Результат -> tmp/t7/verify.md.
"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"C:\MyProjects\APKScenTest"
SUMMARY = ROOT + r"\tmp\t7\run-report\summary.json"
SUMMARY_MD = ROOT + r"\tmp\t7\run-report\summary.md"

checks = []


def check(name, cond, detail=""):
    checks.append(("OK  " if cond else "FAIL", name, detail))
    return cond


def main():
    raw = open(SUMMARY, "rb").read()

    # 1. JSON валиден
    d = json.loads(raw.decode("utf-8"))
    check("summary.json валидный JSON", True)

    # 2. noBOM + LF (грабля T5: ЗаписьТекста -> BOM/CRLF)
    check("summary.json без BOM", not raw.startswith(b"\xef\xbb\xbf"))
    check("summary.json LF-переводы строк (нет CR)",
          b"\r\n" not in raw[:2000] and b"\r\n" not in raw[-2000:])
    raw_md = open(SUMMARY_MD, "rb").read()
    check("summary.md без BOM", not raw_md.startswith(b"\xef\xbb\xbf"))
    check("summary.md LF-переводы строк", b"\r\n" not in raw_md[:2000])

    # 3. Контракт верхнего уровня (design §4.8, PROGRESS.md T7-решения)
    top = ["runId", "generatedAt", "runDir", "totals", "batches", "scenarios",
           "arms", "passwords", "coverage", "artifacts"]
    check("топ-ключи контракта", list(d.keys()) == top, str(list(d.keys())))

    # 4. totals
    tot = ["batches", "scenarios", "passed", "failed", "broken", "timeout", "unknown"]
    check("totals: поля", list(d["totals"].keys()) == tot)

    # 5. сценарий x пользователь: поля сценария
    sc_fields = ["scenario", "user", "build", "status", "durationMs",
                 "batchStatus", "returnStatus"]
    ok = all(list(s.keys()) == sc_fields for s in d["scenarios"])
    check("сценарии: поля контракта (scenario/user/build/status/durationMs/batchStatus/returnStatus)", ok)
    ok = all(s["status"] in ("passed", "failed", "broken", "timeout", "unknown")
             for s in d["scenarios"])
    check("сценарии: статус из допущенного множества (allure|timeout|unknown)", ok)

    # 6. батчи из batches.json + scenarioCount
    bt_fields = ["user", "batch", "status", "returnStatus", "verdict",
                 "durationSec", "passwordRestored", "zodRestored",
                 "killConfirmed", "error", "scenarioCount"]
    check("батчи: поля (batches.json + scenarioCount)", all(list(b.keys()) == bt_fields for b in d["batches"]))

    # 7. AC: статусы всех батчей прогона T6 (T6-циклы A и B)
    statuses = [(b["user"], b["status"], b["returnStatus"]) for b in d["batches"]]
    ac = (len(statuses) == 3
          and statuses[0][1] == "timeout" and statuses[1][1] == "timeout"
          and statuses[2][1] == "ok" and statuses[2][2] == "0")
    check("AC: все 3 батча прогона T6 (timeout, timeout, ok/RS=0)", ac, str(statuses))
    check("totals.batches == 3 == len(batches)", d["totals"]["batches"] == 3 == len(d["batches"]))
    check("totals: timeout==1 (только Зонд2 без allure)", d["totals"]["timeout"] == 1)

    # 8. пароли: булевы флаги, хэшей нет (NFR-001)
    def find_hash_keys(obj, path=""):
        bad = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                if "hash" in k.lower() or "хэш" in k.lower():
                    bad.append(path + "/" + k)
                bad += find_hash_keys(v, path + "/" + k)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                bad += find_hash_keys(v, path + "/%d" % i)
        return bad
    check("пароли: хэши/пароли в отчёт не попали", not find_hash_keys(d))
    pdet = d["passwords"]["details"]
    ok = all(isinstance(x["restored"], bool) and isinstance(x["zodRestored"], bool)
             and isinstance(x["user"], str) for x in pdet)
    check("пароли: details[{user,restored,zodRestored}] булевы", ok)
    check("пароли: restoredCount==2, mismatch пуст", d["passwords"]["restoredCount"] == 2
          and d["passwords"]["mismatch"] == [])

    # 9. АРМы с batchStatus/returnStatus
    arm_fields = ["user", "arm", "docTypes", "templates", "reason",
                  "batchStatus", "returnStatus"]
    check("АРМы: 3 АРМа плана со статусами батча",
          len(d["arms"]) == 3 and all(list(a.keys()) == arm_fields for a in d["arms"]))

    # 10. покрытие
    cov = d["coverage"]
    check("покрытие: representatives/gaps/users",
          list(cov.keys()) == ["representatives", "gaps", "users"]
          and len(cov["representatives"]) > 0 and len(cov["users"]) == 2
          and len(cov["gaps"]) > 0)

    # 11. артефакты
    art = d["artifacts"]
    check("артефакты: пути runDir/batches/allure/fixtures/summary",
          list(art.keys()) == ["runDir", "batchesJson", "allureDir",
                               "fixturesJson", "summaryJson", "summaryMd"])

    # 12. totals-арифметика согласована со сценариями
    t = d["totals"]
    check("totals.scenarios == len(scenarios)", t["scenarios"] == len(d["scenarios"]))
    check("сумма счётчиков == totals.scenarios",
          t["passed"] + t["failed"] + t["broken"] + t["timeout"] + t["unknown"]
          == t["scenarios"] == 3 and t["passed"] == 2 and t["timeout"] == 1)

    md = open(SUMMARY_MD, encoding="utf-8").read()
    check("summary.md: заголовок, итоги, сценарии, пароли, артефакты",
          md.startswith("# Сводка прогона") and "## Итоги" in md
          and "## Сценарии" in md and "## Пароли" in md and "## Артефакты" in md)

    lines = ["# T7 verify — СобратьОтчет против контракта (design §4.8/§4.9)",
             "",
             "Вход: tmp/t7/run-report (staging артефактов T6, см. tmp/t7/PROGRESS.md, решение T7-1).",
             "",
             "| Вердикт | Проверка | Детали |",
             "|---|---|---|"]
    for status, name, detail in checks:
        lines.append("| %s | %s | %s |" % (status, name, detail.replace("|", "/")[:120]))
    all_ok = all(c[0] == "OK  " for c in checks)
    lines += ["", "Итог: %d/%d проверок пройдено. VERDICT: %s"
              % (sum(1 for c in checks if c[0] == "OK  "), len(checks),
                 "PASS" if all_ok else "FAIL"),
             "",
             "Примечание о counts: батчи Зонд1 два (timeout-цикл A и ok-цикл B),",
             "allure-каталог у сборки ApkScenTest-Zond1 один -> allure-результат",
             "читается обоими батчами Зонд1 (passed x2), Зонд2 без allure даёт",
             "псевдо-сценарий timeout (батч умер до результата VA). Итого:",
             "scenarios=3: passed=2, timeout=1. Статусы ВСЕХ батчей T6 в отчёте:",
             "timeout (Зонд1, цикл A), timeout (Зонд2, цикл A), ok/RS=0 (Зонд1, цикл B)."]
    with open(ROOT + r"\tmp\t7\verify.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines[-3:]))
    print("verify.md written, PASS" if all_ok else "verify.md written, FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
