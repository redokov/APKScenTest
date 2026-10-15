# -*- coding: utf-8 -*-
"""s2-T3: зачистка артефактов probe 04-fuel-sheet (между итерациями).

Удаляет ТОЛЬКО документы АпкЗаправочныеВедомости с Дата >= сегодней
(15.10.2026) — тестовые документы, созданные probe-прогонами фичи
04-fuel-sheet. Движения (подчинённые регистратору РН АпкЗаправки и др.)
уходят вместе с документом. Реальные документы 2015+ не затрагиваются.
COM-паттерн: q.Execute().Choose() один раз, затем Next().
"""
import json
import sys

CUTOFF = "2026-10-15"


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    import win32com.client
    conn = win32com.client.Dispatch("V85.COMConnector").Connect(
        "Srvr='localhost';Ref='dev_erpapk_demo';Usr='Администратор (ОрловАВ)'")
    out = {"cutoff": CUTOFF, "docs": [], "errors": []}

    print("[q1] docs...", flush=True)
    q = conn.NewObject("Query")
    q.Text = (
        "ВЫБРАТЬ С.Ссылка КАК Ref, С.Номер КАК N, С.Проведен КАК P "
        "ИЗ Документ.АпкЗаправочныеВедомости КАК С "
        "ГДЕ С.Дата >= ДАТАВРЕМЯ(2026, 10, 15, 0, 0, 0)")
    refs = []
    sel = q.Execute().Choose()
    while sel.Next():
        refs.append((sel.Ref, str(sel.N), bool(sel.P)))
    print("[q1] found %d" % len(refs), flush=True)
    for ref, num, posted in refs:
        try:
            ref.GetObject().Delete()
            out["docs"].append({"num": num, "posted": posted})
        except Exception as e:
            out["errors"].append("doc %s: %s" % (num, str(e)[:150]))

    with open(r"C:\MyProjects\APKScenTest\tmp\s2\fuel-cleanup.json", "w",
              encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("docs=%d errors=%d" % (len(out["docs"]), len(out["errors"])))


if __name__ == "__main__":
    main()
