# -*- coding: utf-8 -*-
"""T3 спеки 006: дамп структуры ФормыДокумента 14 животноводческих типов
из XML-исходников (C:/MyProjects/APKModSrc/Documents): заголовок окна,
закладки/страницы, поля (name->title), ТЧ-колонки, кнопки команд.
Вывод — UTF-8 tmp/s006/form-dump.txt.
Usage: python scripts/s006_form_dump.py [only-svn|only-krs|all]"""
import io
import os
import re
import sys

SRC = u"C:/MyProjects/APKModSrc/Documents"
SVN = [u"АпкГрупповойОпорос", u"АпкГрупповоеВзвешиваниеЖивотных",
       u"АпкГрупповойПадежЗабой", u"АпкГрупповоеПоступлениеЖивотных",
       u"АпкГрупповоеПеремещениеЖивотных",
       u"АпкГрупповойУчетныйЛистДвиженияЖивотных"]
KRS = [u"АпкЖурналНадояМолока",
       u"АпкКРСГрупповойУчетныйЛистДвиженияЖивотных",
       u"АпкКРСГрупповоеПоступлениеЖивотных", u"АпкКРСГрупповойПеревод",
       u"АпкКРСГрупповоеВзвешиваниеЖивотных", u"АпкКРСГрупповойОтел",
       u"АпкКРСТТНМолоко", u"АпкВнутреннийРасходМолока"]

which = sys.argv[1] if len(sys.argv) > 1 else u"all"
names = {"svn": SVN, "krs": KRS, "all": SVN + KRS}.get(which, SVN + KRS)

out = io.open("tmp/s006/form-dump.txt", "w", encoding="utf-8")


def w(s=u""):
    out.write(s + u"\n")


def attr(tag, name):
    m = re.search(name + r'="([^"]*)"', tag)
    return m.group(1) if m else u""


def title_of(item_body):
    # title может быть элементом <title> или атрибутом
    m = re.search(r'<title[^>]*>\s*<item[^>]*xlink:href="([^"]*)"', item_body)
    if m:
        return m.group(1)
    m = re.search(r'Title="([^"]*)"', item_body)
    return m.group(1) if m else u""


for name in names:
    fx = os.path.join(SRC, name, u"Forms", u"ФормаДокумента",
                      u"Ext", u"Form.xml")
    if not os.path.exists(fx):
        w(u"\n## %s — НЕТ ФормыДокумента" % name)
        continue
    x = io.open(fx, encoding="utf-8").read()
    w(u"\n## %s" % name)
    # заголовок формы
    fm = re.search(r'<Form\b[^>]*>', x)
    if fm:
        t = attr(fm.group(0), "Title")
        if t:
            w(u"  Form.Title: %s" % t)
    md = io.open(os.path.join(SRC, name, u"Forms", u"ФормаДокумента",
                              u"Ext", u"Module.bsl"), encoding="utf-8") \
        if os.path.exists(os.path.join(SRC, name, u"Forms",
                                       u"ФормаДокумента", u"Ext",
                                       u"Module.bsl")) else None
    # страницы
    for pm in re.finditer(r'<page[^>]*>(.*?)</page>', x, re.S):
        head = pm.group(0)[:pm.group(0).find(u">") + 1]
        t = title_of(pm.group(0)) or attr(head, "Title")
        w(u"  Page: %s | title=%s" % (attr(head, "name"), t))
    # поля ввода шапки
    for im in re.finditer(r'<InputField\b[^>]*(?:/>|>.*?</InputField>)',
                           x, re.S):
        head = im.group(0)[:im.group(0).find(u">") + 1]
        nm = attr(head, "name")
        t = title_of(im.group(0))
        w(u"  InputField: %s | title=%s" % (nm, t))
    # ТЧ
    for tm in re.finditer(r'<Table\b[^>]*>(.*?)</Table>', x, re.S):
        head = tm.group(0)[:tm.group(0).find(u">") + 1]
        nm = attr(head, "name")
        t = title_of(tm.group(0))
        w(u"  Table: %s | title=%s" % (nm, t))
        for cm in re.finditer(r'<column[^>]*>.*?</column>', tm.group(0),
                              re.S):
            ch = cm.group(0)[:cm.group(0).find(u">") + 1]
            w(u"    column: %s | title=%s" % (attr(ch, "name"),
                                               title_of(cm.group(0))))
    # флаги
    for cm in re.finditer(r'<CheckBox\b[^>]*(?:/>|>.*?</CheckBox>)', x, re.S):
        head = cm.group(0)[:cm.group(0).find(u">") + 1]
        w(u"  CheckBox: %s | title=%s" % (attr(head, "name"),
                                          title_of(cm.group(0))))
    # кнопки команд
    for bm in re.finditer(r'<Button\b[^>]*(?:/>|>.*?</Button>)', x, re.S):
        head = bm.group(0)[:bm.group(0).find(u">") + 1]
        nm = attr(head, "name")
        cmd = re.search(r'command:name="([^"]*)"', cm.group(0) if False
                        else bm.group(0))
        w(u"  Button: %s | cmd=%s" % (nm, cmd.group(1) if cmd else u""))
    # заголовок из модуля (НСтр / УстановитьЗаголовок)
    if md is not None:
        src = md.read()
        for mm in re.finditer(r"НСтр\([^)]*\"ru=\s*['\"]([^'\"]+)", src):
            w(u"  Module NStr: %s" % mm.group(1))
        for mm in re.finditer(u"УстановитьЗаголовок", src):
            w(u"  Module title-code: %s" % mm.group(0))
out.close()
print("form dump done")
