# -*- coding: utf-8 -*-
"""s2-T2: зачистка артефактов probe 02-pl-auto (между итерациями и после probe).

Удаляет ТОЛЬКО документы АпкПутевойЛистАвтотранспорта с Дата >= сегодней
(15.10.2026) — тестовые документы, созданные probe-прогонами фичи 02-pl-auto.
Движения (в т.ч. подчинённый РС АпкСчетчикТранспортныхСредств — ключ
Период+ТС, коллизия «Запись с такими ключевыми полями существует» на
повторном прогоне) уходят вместе с документом.

Чужие записи НЕ трогаем (например, счётчик 2026-10-15 00:00:00 ТС 36ВА33-79
от других прогонов — остаётся). Реальные документы 2016-2023 не затрагиваются.
COM-паттерн: q.Execute().Choose() один раз, затем Next() (НЕ вызывать
Choose() в цикле — выборка всегда truthy, бесконечный цикл).
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
        "ИЗ Документ.АпкПутевойЛистАвтотранспорта КАК С "
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

    with open(r"C:\MyProjects\APKScenTest\tmp\s2\plauto-cleanup.json", "w",
              encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("docs=%d errors=%d" % (len(out["docs"]), len(out["errors"])))


if __name__ == "__main__":
    main()
