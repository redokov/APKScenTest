# -*- coding: utf-8 -*-
"""s006 T4: XML-имена живых значений enum-осей + прогноз представителей
(мин. МоментВремени на значение оси, автор) для итогового наполнения
axes.values в coverage-map. Вывод UTF-8: tmp/s006/axis-enum-names.txt"""
import io
import sys

sys.path.insert(0, "scripts")
import win32com.client
import t8_gate as t

OUT = "tmp/s006/axis-enum-names.txt"
out = io.open(OUT, "w", encoding="utf-8")

PAIRS = [
    (u"АпкГрупповойПадежЗабой", u"ВидОперации", u"Enum.АпкПадежЗабой"),
    (u"АпкГрупповойУчетныйЛистДвиженияЖивотных", u"УчетнаяГруппа", u"Enum.АпкКатегорииЖивотныхС"),
    (u"АпкКРСГрупповойУчетныйЛистДвиженияЖивотных", u"УчетнаяГруппа", u"Enum.АпкКатегорииЖивотных"),
    (u"АпкКРСГрупповойПеревод", u"ВидОперации", u"Enum.АпкКРСВидыОперацийГрупповогоПеревода"),
    (u"АпкКРСТТНМолоко", u"СортОтправлено", u"Enum.АпкСортаМолока"),
    (u"АпкВнутреннийРасходМолока", u"ВидОперации", u"Enum.АпкВидыОперацийВнутреннийРасходМолока"),
]

# 5 типов с осью Проведен=true: прогноз представителя (мин момент)
POSTED = [
    u"АпкГрупповойОпорос", u"АпкГрупповоеВзвешиваниеЖивотных",
    u"АпкГрупповоеПеремещениеЖивотных",
    u"АпкКРСГрупповоеВзвешиваниеЖивотных", u"АпкКРСГрупповойОтел",
]

BOOL_AXES = [
    (u"АпкГрупповоеПоступлениеЖивотных", u"ВводОстатков"),
    (u"АпкЖурналНадояМолока", u"ВводОстатков"),
    (u"АпкКРСГрупповоеПоступлениеЖивотных", u"ВводОстатков"),
]


def w(line=""):
    out.write(line + "\n")


conn = win32com.client.Dispatch("V85.COMConnector").Connect(t.conn_str(t.ADMIN, ""))

for dt, attr, etp in PAIRS:
    w("## %s.%s (%s)" % (dt, attr, etp))
    q = conn.NewObject("Query")
    q.Text = (u"ВЫБРАТЬ Док." + attr + u" КАК З, КОЛИЧЕСТВО(*) КАК Ц "
              u"ИЗ Документ." + dt + u" КАК Док СГРУППИРОВАТЬ ПО Док." + attr)
    sel = q.Execute().Choose()
    while sel.Next():
        v = sel.З
        try:
            xmlname = str(conn.XMLString(v))
        except Exception:
            xmlname = "ERR"
        # min-moment doc with this value
        q2 = conn.NewObject("Query")
        q2.Text = (u"ВЫБРАТЬ ПЕРВЫЕ 1 Док.Ссылка КАК С, Док.МоментВремени КАК М, "
                   u"Док.Автор.Наименование КАК А, Док.Номер КАК Н "
                   u"ИЗ Документ." + dt + u" КАК Док "
                   u"ГДЕ Док." + attr + u" = &З УПОРЯДОЧИТЬ ПО Док.МоментВремени")
        q2.SetParameter(u"З", v)
        s2 = q2.Execute().Choose()
        if s2.Next():
            w("  %s | n=%s | rep=%s %s [%s]" % (xmlname, sel.Ц, s2.Н, str(s2.М)[:19], s2.А))
        else:
            w("  %s | n=%s | rep=NONE" % (xmlname, sel.Ц))

for dt, attr in BOOL_AXES:
    w("## %s.%s (Boolean)" % (dt, attr))
    q = conn.NewObject("Query")
    q.Text = (u"ВЫБРАТЬ Док." + attr + u" КАК З, КОЛИЧЕСТВО(*) КАК Ц "
              u"ИЗ Документ." + dt + u" КАК Док СГРУППИРОВАТЬ ПО Док." + attr)
    sel = q.Execute().Choose()
    while sel.Next():
        v = sel.З
        vs = "true" if str(v) == "True" else "false"
        q2 = conn.NewObject("Query")
        q2.Text = (u"ВЫБРАТЬ ПЕРВЫЕ 1 Док.Ссылка КАК С, Док.МоментВремени КАК М, "
                   u"Док.Автор.Наименование КАК А, Док.Номер КАК Н "
                   u"ИЗ Документ." + dt + u" КАК Док "
                   u"ГДЕ Док." + attr + u" = &З УПОРЯДОЧИТЬ ПО Док.МоментВремени")
        q2.SetParameter(u"З", v)
        s2 = q2.Execute().Choose()
        if s2.Next():
            w("  %s | n=%s | rep=%s %s [%s]" % (vs, sel.Ц, s2.Н, str(s2.М)[:19], s2.А))
        else:
            w("  %s | n=%s | rep=NONE" % (vs, sel.Ц))

for dt in POSTED:
    w("## %s (axis Проведен=true)" % dt)
    q = conn.NewObject("Query")
    q.Text = (u"ВЫБРАТЬ ПЕРВЫЕ 1 Док.Ссылка КАК С, Док.МоментВремени КАК М, "
              u"Док.Автор.Наименование КАК А, Док.Номер КАК Н "
              u"ИЗ Документ." + dt + u" КАК Док "
              u"ГДЕ Док.Проведен УПОРЯДОЧИТЬ ПО Док.МоментВремени")
    sel = q.Execute().Choose()
    if sel.Next():
        w("  rep=%s %s [%s]" % (sel.Н, str(sel.М)[:19], sel.А))
    else:
        w("  rep=NONE (нет проведённых!)")

out.close()
print("done")
