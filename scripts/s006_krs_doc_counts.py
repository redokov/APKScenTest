# -*- coding: utf-8 -*-
"""s006 T4: сколько документов каждого КРС-типа у авторов-фикстур
(Орлов, ФедоровБМ) в текущей базе = сколько сценариев сгенерит
препроцессор на шаблоны 16-23 (для полноты патчей по номерам).
Вывод UTF-8: tmp/s006/krs-doc-counts.txt"""
import io
import sys

sys.path.insert(0, "scripts")
import win32com.client
import t8_gate as t

OUT = "tmp/s006/krs-doc-counts.txt"
out = io.open(OUT, "w", encoding="utf-8")


def w(line=""):
    out.write(line + "\n")


DOCS = [
    u"АпкЖурналНадояМолока",
    u"АпкКРСГрупповойУчетныйЛистДвиженияЖивотных",
    u"АпкКРСГрупповоеПоступлениеЖивотных",
    u"АпкКРСГрупповойПеревод",
    u"АпкКРСГрупповоеВзвешиваниеЖивотных",
    u"АпкКРСГрупповойОтел",
    u"АпкКРСТТНМолоко",
    u"АпкВнутреннийРасходМолока",
]

conn = win32com.client.Dispatch("V85.COMConnector").Connect(t.conn_str(t.ADMIN, ""))


for dt in DOCS:
    q = conn.NewObject("Query")
    q.Text = (
        u"ВЫБРАТЬ Док.Автор.Наименование КАК ИмяА, Док.Автор КАК Автор, КОЛИЧЕСТВО(*) КАК Ц "
        u"ИЗ Документ." + dt + u" КАК Док "
        u"СГРУППИРОВАТЬ ПО Док.Автор"
    )
    sel = q.Execute().Choose()
    w("")
    w("## " + dt)
    while True:
        ok = sel.Next()
        if not ok:
            break
        try:
            uuid = str(sel.Автор.UUID())
        except Exception:
            uuid = "?"
        w("  %s = %s" % (sel.ИмяА, sel.Ц))
out.close()
print("done")
