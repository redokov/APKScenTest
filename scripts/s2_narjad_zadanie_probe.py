# -*- coding: utf-8 -*-
"""s2_narjad_zadanie_probe.py — Т5: какой наряд НВЦБ-000001 имеет строку Задание
и почему ось скана пустая (реплика ВычислитьОсиДокумента по одному документу).
STDOUT ascii-only, детали в tmp/s2/narjad-zadanie-probe.json.
"""
import io
import json
import sys


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    import win32com.client
    agent = win32com.client.Dispatch("V85.COMConnector").Connect(
        "Srvr='localhost';Ref='dev_erpapk_demo';Usr='Администратор (ОрловАВ)'")

    def s(v):
        try:
            return agent.String(v)
        except Exception:
            return str(v)

    q = agent.NewObject("Query")
    q.Text = (
        "ВЫБРАТЬ Д.Ссылка КАК Doc, Д.Номер КАК Num, Д.Дата КАК DDate, "
        "Д.Проведен КАК Posted, КОЛИЧЕСТВО(З.НомерСтроки) КАК ZCnt "
        "ИЗ Документ.АпкНарядНаСдельнуюРаботу КАК Д "
        "ЛЕВОЕ СОЕДИНЕНИЕ Документ.АпкНарядНаСдельнуюРаботу.Задание КАК З "
        "ПО З.Ссылка = Д.Ссылка "
        "ГДЕ Д.Номер ПОДОБНО \"НВЦБ%\" "
        "СГРУППИРОВАТЬ ПО Д.Ссылка, Д.Номер, Д.Дата, Д.Проведен")
    rows = []
    docrefs = []
    sel = q.Execute().Choose()
    while sel.Next():
        rows.append({"num": s(sel.Num), "date": s(sel.DDate)[:10],
                     "posted": bool(sel.Posted), "z": int(sel.ZCnt),
                     "ref": s(sel.Doc)})
        docrefs.append(sel.Doc)
    out = {"rows": rows}

    # Для каждого НВЦБ: строки Задание с ТипЗатрат (передаём COM-ссылку)
    for i, r in enumerate(out["rows"]):
        doc = docrefs[i]
        q2 = agent.NewObject("Query")
        q2.Text = (
            "ВЫБРАТЬ З.НомерСтроки КАК Ln, З.ТипЗатрат КАК TZ, З.АналитикаРасходов КАК An "
            "ИЗ Документ.АпкНарядНаСдельнуюРаботу.Задание КАК З "
            "ГДЕ З.Ссылка = &Док")
        try:
            q2.УстановитьПараметр("Док", doc)
            rr = []
            sel2 = q2.Execute().Choose()
            while sel2.Next():
                rr.append({"ln": int(sel2.Ln), "tz": s(sel2.TZ), "an": s(sel2.An)})
            r["zadanieRows"] = rr
        except Exception as e:
            r["zadanieRows"] = "ERR " + repr(e)[:120]

    with io.open(r"C:\MyProjects\APKScenTest\tmp\s2\narjad-zadanie-probe.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("OK docs=%d" % len(out["rows"]))


if __name__ == "__main__":
    main()
