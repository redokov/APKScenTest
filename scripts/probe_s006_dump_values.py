# -*- coding: utf-8 -*-
"""T3/T4 спеки 006: дамп КОНКРЕТНЫХ значений представителей (представления
ссылок через ПРЕДСТАВЛЕНИЕ() в запросе) для наполнения probe-фич.
Вывод — UTF-8 tmp/s006/rep-values.txt.
Usage: python scripts/probe_s006_dump_values.py"""
import io
import json
import sys

sys.path.insert(0, "scripts")
import win32com.client
import t8_gate as t

cm = json.load(io.open("tests/coverage-map.json", encoding="utf-8"))
docs = cm["documents"]

LIVE = [
    u"АпкГрупповойОпорос", u"АпкГрупповоеВзвешиваниеЖивотных",
    u"АпкГрупповойПадежЗабой", u"АпкГрупповоеПоступлениеЖивотных",
    u"АпкГрупповоеПеремещениеЖивотных",
    u"АпкГрупповойУчетныйЛистДвиженияЖивотных",
    u"АпкЖурналНадояМолока",
    u"АпкКРСГрупповойУчетныйЛистДвиженияЖивотных",
    u"АпкКРСГрупповоеПоступлениеЖивотных", u"АпкКРСГрупповойПеревод",
    u"АпкКРСГрупповоеВзвешиваниеЖивотных", u"АпкКРСГрупповойОтел",
    u"АпкКРСТТНМолоко", u"АпкВнутреннийРасходМолока",
]

out = io.open("tmp/s006/rep-values.txt", "w", encoding="utf-8")


def w(s=u""):
    out.write(s + u"\n")


agent = win32com.client.Dispatch("V85.COMConnector").Connect(
    t.conn_str(t.ADMIN, u""))

w(u"=== T3/T4: конкретные значения представителей (представления) ===")
for name in LIVE:
    entry = docs.get(name)
    if not entry:
        continue
    fl = entry["fieldList"]
    header = fl.get("header", [])
    tabular = fl.get("tabular", {})
    try:
        w(u"")
        w(u"## %s" % name)
        q = agent.NewObject(u"Запрос")
        parts = [u"ПРЕДСТАВЛЕНИЕ(Документ." + name + u".Ссылка) КАК Ref"]
        parts.append(u"ПРЕДСТАВЛЕНИЕ(Документ." + name + u".Дата) КАК FDate")
        parts.append(u"ПРЕДСТАВЛЕНИЕ(Документ." + name + u".Номер) КАК FNum")
        for i, f in enumerate(header):
            parts.append(u"ПРЕДСТАВЛЕНИЕ(Документ." + name + u"." + f +
                         u") КАК H%d" % i)
        q.Text = (u"ВЫБРАТЬ ПЕРВЫЕ 1 " + u", ".join(parts) +
                  u" ИЗ Документ." + name +
                  u" УПОРЯДОЧИТЬ ПО Документ." + name + u".Дата УБЫВ")
        sel = q.Execute().Choose()
        if not sel.Next():
            w(u"  НЕТ ДАННЫХ")
            continue
        w(u"  Представитель: %s  (№ %s от %s)" %
          (sel.Ref, getattr(sel, u"FNum", u""), getattr(sel, u"FDate", u"")))
        for i, f in enumerate(header):
            try:
                w(u"  header.%s = [%s]" % (f, getattr(sel, u"H%d" % i, u"")))
            except Exception as e:
                w(u"  header.%s — ERR %s" % (f, e))
        # ТЧ: первая строка с представлениями
        for ts, cols in tabular.items():
            try:
                parts2 = [u"ПРЕДСТАВЛЕНИЕ(Т." + c + u") КАК C%d" % i
                          for i, c in enumerate(cols)]
                q2 = agent.NewObject(u"Запрос")
                q2.Text = (u"ВЫБРАТЬ ПЕРВЫЕ 1 " + u", ".join(parts2) +
                           u" ИЗ Документ." + name + u" КАК ДУ" +
                           u" ЛЕВОЕ СОЕДИНЕНИЕ Документ." + name + u"." + ts +
                           u" КАК Т ПО Т.Ссылка = ДУ.Ссылка" +
                           u" ГДЕ ДУ.Ссылка = &Р" +
                           u" УПОРЯДОЧИТЬ ПО Т.НомерСтроки")
                # ссылку представителя получим отдельным запросом
                q3 = agent.NewObject(u"Запрос")
                q3.Text = (u"ВЫБРАТЬ ПЕРВЫЕ 1 Документ." + name +
                           u".Ссылка КАК R ИЗ Документ." + name +
                           u" УПОРЯДОЧИТЬ ПО Документ." + name + u".Дата УБЫВ")
                s3 = q3.Execute().Choose()
                s3.Next()
                q2.SetParameter(u"Р", s3.R)
                s2 = q2.Execute().Choose()
                if s2.Next():
                    w(u"  ТЧ %s (строка 1):" % ts)
                    for i, c in enumerate(cols):
                        w(u"    %s = [%s]" % (c, getattr(s2, u"C%d" % i, u"")))
                else:
                    w(u"  ТЧ %s: строк 0" % ts)
            except Exception as e:
                w(u"  ТЧ %s — ERR %s" % (ts, e))
    except Exception as e:
        w(u"\n[%s] ОШИБКА: %s" % (name, e))

out.close()
print("dump done")
