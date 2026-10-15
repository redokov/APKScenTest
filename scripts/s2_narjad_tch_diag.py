# -*- coding: utf-8 -*-
"""s2_narjad_tch_diag.py — T5: ТЧ нарядов (Задание vs ВыполненныеРаботы) + ТипЗатрат.

Проверка гипотезы: почему наряды не дали представителя — ось ТипЗатрат
задана в tabular.Задание, а у нарядов заполнена только ВыполненныеРаботы.
Результат: tmp/s2/narjad-tch-diag.json. STDOUT ascii-only.
"""
import io
import json
import sys

OUT_JSON = r"C:\MyProjects\APKScenTest\tmp\s2\narjad-tch-diag.json"


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
        "ВЫБРАТЬ Д.Ссылка КАК Ref, Д.Номер КАК Num, Д.Дата КАК DDate, "
        "КОЛИЧЕСТВО(З.НомерСтроки) КАК ZadanieCnt "
        "ИЗ Документ.АпкНарядНаСдельнуюРаботу КАК Д "
        "ЛЕВОЕ СОЕДИНЕНИЕ Документ.АпкНарядНаСдельнуюРаботу.Задание КАК З "
        "ПО З.Ссылка = Д.Ссылка "
        "ГДЕ Д.Проведен "
        "СГРУППИРОВАТЬ ПО Д.Ссылка, Д.Номер, Д.Дата "
        "УПОРЯДОЧИТЬ ПО Д.Дата")
    rows = {}
    sel = q.Execute().Choose()
    while sel.Next():
        rows[s(sel.Num)] = {"num": s(sel.Num), "zadanie": int(sel.ZadanieCnt), "vr": 0}

    qb = agent.NewObject("Query")
    qb.Text = (
        "ВЫБРАТЬ Д.Номер КАК Num, КОЛИЧЕСТВО(R.НомерСтроки) КАК VrCnt "
        "ИЗ Документ.АпкНарядНаСдельнуюРаботу КАК Д "
        "ЛЕВОЕ СОЕДИНЕНИЕ Документ.АпкНарядНаСдельнуюРаботу.ВыполненныеРаботы КАК R "
        "ПО R.Ссылка = Д.Ссылка "
        "ГДЕ Д.Проведен "
        "СГРУППИРОВАТЬ ПО Д.Ссылка, Д.Номер")
    selb = qb.Execute().Choose()
    while selb.Next():
        n = s(selb.Num)
        if n in rows:
            rows[n]["vr"] = int(selb.VrCnt)
        else:
            rows[n] = {"num": n, "zadanie": 0, "vr": int(selb.VrCnt)}
    rows = list(rows.values())

    # ТипЗатрат в Задание и ВыполненныеРаботы (первые 30 строк каждого)
    q2 = agent.NewObject("Query")
    q2.Text = (
        "ВЫБРАТЬ ПЕРВЫЕ 30 З.ТипЗатрат КАК TZ "
        "ИЗ Документ.АпкНарядНаСдельнуюРаботу.Задание КАК З")
    tz_z = []
    sel2 = q2.Execute().Choose()
    while sel2.Next():
        tz_z.append(s(sel2.TZ))

    q3 = agent.NewObject("Query")
    q3.Text = (
        "ВЫБРАТЬ ПЕРВЫЕ 30 R.ТипЗатрат КАК TZ "
        "ИЗ Документ.АпкНарядНаСдельнуюРаботу.ВыполненныеРаботы КАК R")
    tz_v = []
    sel3 = q3.Execute().Choose()
    while sel3.Next():
        tz_v.append(s(sel3.TZ))

    with io.open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump({"rows": rows, "tzZadanie": tz_z, "tzVR": tz_v},
                  f, ensure_ascii=False, indent=1)

    z_cnt = sum(1 for r in rows if r["zadanie"] > 0)
    v_cnt = sum(1 for r in rows if r["vr"] > 0)
    print("OK posted=%d withZadanie=%d withVR=%d" % (len(rows), z_cnt, v_cnt))
    print("TZ zadanie:", tz_z[:5])
    print("TZ VR:", tz_v[:5])


if __name__ == "__main__":
    main()
