# -*- coding: utf-8 -*-
"""s006 T4: кандидаты осей (Enum/Boolean реквизиты шапки) по 14 типам
животноводства из XML-метаданных APKModSrc + живые значения (COM).
Вывод UTF-8: tmp/s006/axis-candidates.txt"""
import io
import os
import sys

sys.path.insert(0, "scripts")
import win32com.client
import t8_gate as t
import xml.etree.ElementTree as ET

OUT = "tmp/s006/axis-candidates.txt"
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

SRC = u"C:/MyProjects/APKModSrc/Documents"


def w(line=""):
    out.write(line + "\n")


conn = win32com.client.Dispatch("V85.COMConnector").Connect(t.conn_str(t.ADMIN, ""))

for dt in DOCS:
    w("")
    w("## " + dt)
    path = os.path.join(SRC, dt + ".xml")
    if not os.path.exists(path):
        path2 = os.path.join(SRC, dt, dt + ".xml")
        path = path2 if os.path.exists(path2) else None
    if not path:
        w("  NO XML")
        continue
    tree = ET.parse(path)
    ns = "{http://v8.1c.ru/8.3/MDClasses}"
    core = "{http://v8.1c.ru/8.1/data/core}"
    ch = tree.getroot().find(ns + "Document").find(ns + "ChildObjects")
    if ch is None:
        w("  no ChildObjects")
        continue
    for a in list(ch):
        if a.tag != ns + "Attribute":
            continue
        props = a.find(ns + "Properties")
        if props is None:
            continue
        name = props.find(ns + "Name")
        tnode = props.find(ns + "Type")
        types = None
        if tnode is not None:
            inner = tnode.find(core + "Type")
            if inner is not None:
                types = inner
        if name is None or types is None:
            continue
        tstr = (types.text or "").strip()
        if tstr.startswith("cfg:EnumRef.") or tstr == "xs:boolean":
            tstr2 = ("Enum." + tstr[len("cfg:EnumRef."):]) if tstr.startswith("cfg:EnumRef.") else "Boolean"
            # live distinct values
            vals = []
            try:
                q = conn.NewObject("Query")
                q.Text = (u"ВЫБРАТЬ Док." + name.text + u" КАК З, КОЛИЧЕСТВО(*) КАК Ц "
                          u"ИЗ Документ." + dt + u" КАК Док СГРУППИРОВАТЬ ПО Док." + name.text)
                sel = q.Execute().Choose()
                while sel.Next():
                    v = sel.З
                    if tstr2.startswith("Enum."):
                        try:
                            vs = v.XMLString() if v is not None else None
                        except Exception:
                            try:
                                vs = str(v)
                            except Exception:
                                vs = "?"
                        vals.append("%s(%s)" % (vs, sel.Ц))
                    else:
                        vals.append("%s(%s)" % (str(v), sel.Ц))
            except Exception as e:
                vals = ["ERR " + str(e)[:100]]
            w("  CAND %s : %s : live=%s" % (name.text, tstr2, "; ".join(vals)))
out.close()
print("done")
