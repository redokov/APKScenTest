# -*- coding: utf-8 -*-
"""s2-T4: зачистка артефактов probe 05-weighing (между итерациями).

Удаляет ТОЛЬКО документы АпкРегистрацияВзвешиванийНаТоку с датой >=
2026-10-16 — тестовые документы, созданные probe-прогонами фичи
05-weighing (диалоги «Укажите номер талона» занимают талоны
12-000099/12-000100 регистром АпкМассаРаспределеннаяПоТалонам — без
очистки повторный прогон падает «Талон уже использован»). Реальные
документы 2015+ не затрагиваются. COM-паттерн: q.Execute().Choose()
один раз, затем Next().
"""
import json
import sys

CUTOFF_YEAR = 2026
CUTOFF_MONTH = 10
CUTOFF_DAY = 16


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    import win32com.client
    conn = win32com.client.Dispatch("V85.COMConnector").Connect(
        "Srvr='localhost';Ref='dev_erpapk_demo';Usr='Администратор (ОрловАВ)'")
    out = {"cutoff": "%04d-%02d-%02d" % (CUTOFF_YEAR, CUTOFF_MONTH, CUTOFF_DAY),
           "docs": [], "errors": []}

    q = conn.NewObject("Query")
    q.Text = (
        "ВЫБРАТЬ С.Ссылка КАК Ref, С.Номер КАК N, С.Проведен КАК P "
        "ИЗ Документ.АпкРегистрацияВзвешиванийНаТоку КАК С "
        "ГДЕ С.Дата >= ДАТАВРЕМЯ(%d, %d, %d, 0, 0, 0)"
        % (CUTOFF_YEAR, CUTOFF_MONTH, CUTOFF_DAY))
    refs = []
    sel = q.Execute().Choose()
    while sel.Next():
        refs.append((sel.Ref, str(sel.N), bool(sel.P)))
    print("[q] found %d" % len(refs), flush=True)
    for ref, num, posted in refs:
        try:
            ref.GetObject().Delete()
            out["docs"].append({"num": num, "posted": posted})
        except Exception as e:
            out["errors"].append("doc %s: %s" % (num, str(e)[:150]))

    with open(r"C:\MyProjects\APKScenTest\tmp\s2\weighing-cleanup.json", "w",
              encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("docs=%d errors=%d" % (len(out["docs"]), len(out["errors"])))


if __name__ == "__main__":
    main()
