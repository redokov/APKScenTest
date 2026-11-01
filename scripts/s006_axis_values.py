# -*- coding: utf-8 -*-
"""s006 T4: живые значения осей coverage-map по 14 типам животноводства
(для заполнения axes.values) + кандидаты-оси (Enum/Boolean шапки) для типов
с axes=[]. Вывод UTF-8: tmp/s006/axis-values.txt"""
import io
import json
import sys

sys.path.insert(0, "scripts")
import win32com.client
import t8_gate as t

OUT = "tmp/s006/axis-values.txt"
out = io.open(OUT, "w", encoding="utf-8")


def w(line=""):
    out.write(line + "\n")


cm = json.load(io.open("tests/coverage-map.json", encoding="utf-8"))
docs = cm["documents"]

conn = win32com.client.Dispatch("V85.COMConnector").Connect(t.conn_str(t.ADMIN, ""))

for dt, d in docs.items():
    if dt not in [u"АпкГрупповойОпорос", u"АпкГрупповоеВзвешиваниеЖивотных",
                  u"АпкГрупповойПадежЗабой", u"АпкГрупповоеПоступлениеЖивотных",
                  u"АпкГрупповоеПеремещениеЖивотных",
                  u"АпкГрупповойУчетныйЛистДвиженияЖивотных",
                  u"АпкЖурналНадояМолока",
                  u"АпкКРСГрупповойУчетныйЛистДвиженияЖивотных",
                  u"АпкКРСГрупповоеПоступлениеЖивотных", u"АпкКРСГрупповойПеревод",
                  u"АпкКРСГрупповоеВзвешиваниеЖивотных", u"АпкКРСГрупповойОтел",
                  u"АпкКРСТТНМолоко", u"АпкВнутреннийРасходМолока"]:
        continue
    w("")
    w("## " + dt)
    for ax in d.get("axes", []):
        attr = ax["attribute"]
        where = ax.get("where", "header")
        w("  AXIS %s (%s) type=%s" % (attr, where, ax.get("type", "")))
        if where.startswith("tabular"):
            w("    (tabular axis — TODO вручную по данным ТЧ)")
            continue
        q = conn.NewObject("Query")
        q.Text = (u"ВЫБРАТЬ Док." + attr + u" КАК З, КОЛИЧЕСТВО(*) КАК Ц "
                  u"ИЗ Документ." + dt + u" КАК Док СГРУППИРОВАТЬ ПО Док." + attr)
        try:
            sel = q.Execute().Choose()
        except Exception as e:
            w("    ERR " + str(e)[:160])
            continue
        while True:
            ok = sel.Next()
            if not ok:
                break
            try:
                val = str(sel.З)
            except Exception:
                val = "?"
            w("    %r = %s" % (val, sel.Ц))
    if not d.get("axes"):
        w("  (нет осей — кандидаты из метаданных:)")
        md = conn.Метаданные.Документы.Найти(dt)
        for i in range(md.Реквизиты.Количество()):
            r = md.Реквизиты.Получить(i)
            try:
                tstr = str(r.Тип)
            except Exception:
                tstr = ""
            if "Enum." in tstr or "Булево" in tstr:
                w("    CAND %s : %s" % (r.Имя, tstr))
out.close()
print("done")
