# -*- coding: utf-8 -*-
"""s2_narjad_tz_probe.py — Т5: ТипЗатрат строк ТЧ нарядов СТРОГО по проведённым.

ВЫБРАТЬ З.ТипЗатрат ИЗ ...Задание КАК З ГДЕ З.Ссылка.Проведен (и для ВыполненныеРаботы).
Результат: tmp/s2/narjad-tz-probe.json. STDOUT ascii-only.
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

    out = {}
    for name, tch in (("zadanie", "Задание"), ("vr", "ВыполненныеРаботы")):
        q = agent.NewObject("Query")
        q.Text = (
            "ВЫБРАТЬ З.Ссылка КАК Doc, З.Ссылка.Номер КАК Num, З.ТипЗатрат КАК TZ "
            "ИЗ Документ.АпкНарядНаСдельнуюРаботу." + tch + " КАК З "
            "ГДЕ З.Ссылка.Проведен")
        rows = []
        sel = q.Execute().Choose()
        while sel.Next():
            tz = s(sel.TZ)
            if tz:
                rows.append({"num": s(sel.Num), "tz": tz})
        out[name] = rows
        print("OK %s postedTZrows=%d" % (name, len(rows)))

    with io.open(r"C:\MyProjects\APKScenTest\tmp\s2\narjad-tz-probe.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
