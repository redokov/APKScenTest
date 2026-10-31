# -*- coding: utf-8 -*-
"""T1 спеки 006: аудит метаданных 14 Must-типов животноводства.
Парсит Documents/<Тип>.xml (атрибуты шапки, ТЧ, типы полей) и
Forms/ФормаДокумента/Ext/Form.xml (ChoiceForm-ловушки подбора).
Вывод — UTF-8 в tmp/s006/audit-fields.md.
Usage: python scripts/audit_s006_docs.py"""
import io
import os
import sys
import xml.etree.ElementTree as ET

DOCS = [
    # СВН (6)
    (u"АпкГрупповойОпорос", u"10-svn-farrowing"),
    (u"АпкГрупповоеВзвешиваниеЖивотных", u"11-svn-weighing"),
    (u"АпкГрупповойПадежЗабой", u"12-svn-mortality"),
    (u"АпкГрупповоеПоступлениеЖивотных", u"13-svn-receipt"),
    (u"АпкГрупповоеПеремещениеЖивотных", u"14-svn-movement"),
    (u"АпкГрупповойУчетныйЛистДвиженияЖивотных", u"15-svn-accounting-sheet"),
    # КРС + молоко (8)
    (u"АпкЖурналНадояМолока", u"16-krs-milk-journal"),
    (u"АпкКРСГрупповойУчетныйЛистДвиженияЖивотных", u"17-krs-accounting-sheet"),
    (u"АпкКРСГрупповоеПоступлениеЖивотных", u"18-krs-receipt"),
    (u"АпкКРСГрупповойПеревод", u"19-krs-transfer"),
    (u"АпкКРСГрупповоеВзвешиваниеЖивотных", u"20-krs-weighing"),
    (u"АпкКРСГрупповойОтел", u"21-krs-calving"),
    (u"АпкКРСТТНМолоко", u"22-krs-milk-ttn"),
    (u"АпкВнутреннийРасходМолока", u"23-krs-milk-internal"),
]
BASE = r"C:\MyProjects\APKModSrc\Documents"
NS = {"md": "http://v8.1c.ru/8.3/MDClasses",
      "xr": "http://v8.1c.ru/8.3/xcf/readable",
      "v8": "http://v8.1c.ru/8.1/data/core"}

os.makedirs("tmp/s006", exist_ok=True)
out = io.open("tmp/s006/audit-fields.md", "w", encoding="utf-8")


def w(s=u""):
    out.write(s + u"\n")


def attr_type(attr_el):
    """Тип атрибута: список <Type> внутри <Properties><Type>."""
    types = []
    tp = attr_el.find("md:Properties/md:Type", NS)
    for t in (tp if tp is not None else []):
        if t.text:
            types.append(t.text)
    return types


def short_type(types):
    res = []
    for t in types:
        for pref in ("CatalogRef.", "EnumRef.", "ChartOfCharacteristicTypesRef."):
            if t.startswith(pref):
                res.append(t[len(pref):])
                break
        else:
            if t.startswith("{"):
                # v8 UUID types (xs: types inside braces)
                inner = t
                for token in ("xs:decimal", "xs:boolean", "xs:dateTime", "xs:string",
                              "xs:int", "xs:integer"):
                    if token in inner:
                        res.append(token.split(":")[1])
                        break
                else:
                    res.append(u"uuid-type")
            else:
                res.append(t)
    return u", ".join(res) if res else u"?"


w(u"# T1 спеки 006: аудит метаданных 14 Must-типов животноводства")
w(u"")
w(u"Источник: C:\\MyProjects\\APKModSrc\\Documents (XML метаданных + Form.xml).")
w(u"Пометка «уточнить на probe» — эмпирическая проверка на живой базе (T2/T3/T4).")
w(u"")

for name, tpl in DOCS:
    path = os.path.join(BASE, name + ".xml")
    if not os.path.exists(path):
        w(u"## %s — XML НЕ НАЙДЕН" % name)
        continue
    tree = ET.parse(path)
    root = tree.getroot()
    doc = root.find("md:Document", NS)
    w(u"## %s (шаблон: %s)" % (name, tpl))
    child = doc.find("md:ChildObjects", NS)

    def emit_attrs(container, label):
        rows = []
        if container is not None:
            for a in container.findall("md:Attribute", NS):
                an = a.find("md:Properties/md:Name", NS)
                rows.append((an.text if an is not None else u"?",
                             short_type(attr_type(a))))
        if rows:
            w(u"**%s:**" % label)
            for n, t in rows:
                w(u"- %s: %s" % (n, t))
        else:
            w(u"**%s:** (нет)" % label)

    emit_attrs(child, u"Реквизиты шапки")
    ts_list = child.findall("md:TabularSection", NS)
    if ts_list:
        for ts in ts_list:
            tsn = ts.find("md:Properties/md:Name", NS)
            w(u"")
            w(u"**ТЧ %s:**" % (tsn.text if tsn is not None else u"?"))
            trows = []
            for a in ts.findall(".//md:Attribute", NS):
                an = a.find("md:Properties/md:Name", NS)
                trows.append((an.text if an is not None else u"?",
                              short_type(attr_type(a))))
            for n, t in trows:
                w(u"- %s: %s" % (n, t))
    else:
        w(u"**ТЧ:** (нет)")

    # ChoiceForm-ловушки в форме документа
    form_path = os.path.join(BASE, name, "Forms", u"ФормаДокумента", "Ext", "Form.xml")
    traps = []
    if os.path.exists(form_path):
        ftxt = io.open(form_path, encoding="utf-8", errors="replace").read()
        for marker in (u"АпкПодборЖивотных", u"АпкФормаВыбора", u"ChoiceForm",
                       u"ФормаВыбора"):
            cnt = ftxt.count(marker)
            if cnt:
                traps.append(u"%s ×%d" % (marker, cnt))
    w(u"")
    if traps:
        w(u"**Ловушки формы (кандидаты):** " + u"; ".join(traps))
    else:
        w(u"**Ловушки формы:** не найдено (уточнить на probe)")
    w(u"")

out.close()
print("audit done -> tmp/s006/audit-fields.md")
