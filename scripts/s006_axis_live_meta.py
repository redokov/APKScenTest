# -*- coding: utf-8 -*-
"""s006 T4: ЖИВЫЕ метаданные (COM): Enum/Boolean реквизиты шапки 14 типов
животноводства + реквизиты каталога АпкСтатусыЖивотныхГрупповогоУчета
(ищем Enum-свойство для valuePath catalog-оси).
Вывод UTF-8: tmp/s006/axis-live-meta.txt"""
import io
import sys

sys.path.insert(0, "scripts")
import win32com.client
import t8_gate as t

OUT = "tmp/s006/axis-live-meta.txt"
out = io.open(OUT, "w", encoding="utf-8")

DOCS = [
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


def w(line=""):
    out.write(line + "\n")


def dump_attrs(w, mgr, name, live_types):
    md = mgr.Найти(name)
    if md is None:
        w("  NOT FOUND " + name)
        return
    try:
        cnt = md.Реквизиты.Количество()
    except Exception as e:
        w("  ERR Количество " + str(e)[:100])
        cnt = 0
    for i in range(cnt):
        r = md.Реквизиты.Получить(i)
        try:
            ts = []
            for ty in r.Тип.Типы():
                ts.append(str(ty))
        except Exception:
            ts = ["?"]
        for s in ts:
            if ("Enum" in s) or ("Булево" in s):
                w("  %s : %s" % (r.Имя, ",".join(ts)))
                break


conn = win32com.client.Dispatch("V85.COMConnector").Connect(t.conn_str(t.ADMIN, ""))

for dt in DOCS:
    w("")
    w("## DOC " + dt)
    dump_attrs(w, conn.Метаданные.Документы, dt, None)

w("")
w("## CATALOG АпкСтатусыЖивотныхГрупповогоУчета (все реквизиты)")
md = conn.Метаданные.Справочники.Найти(u"АпкСтатусыЖивотныхГрупповогоУчета")
try:
    cnt = md.Реквизиты.Количество()
    for i in range(cnt):
        r = md.Реквизиты.Получить(i)
        ts = []
        try:
            for ty in r.Тип.Типы():
                ts.append(str(ty))
        except Exception:
            ts = ["?"]
        w("  %s : %s" % (r.Имя, ",".join(ts)))
except Exception as e:
    w("  ERR " + str(e)[:150])

out.close()
print("done")
