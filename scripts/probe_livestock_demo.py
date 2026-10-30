# -*- coding: utf-8 -*-
"""Разведка животноводства (главы 3-5 АПК): есть ли данные в демо-базе
dev_erpapk_demo. Парсит составы подсистем (СВН/КРС групповой, свинокомплекс
индивидуальный) из APKModSrc, затем через COM V85 считает документы и
справочники в базе, семплит последние документы (дата/номер/автор).
Вывод — UTF-8 в tmp/livestock_probe.txt (bash-вывод кириллицы нечитаем).
Usage: python scripts/probe_livestock_demo.py"""
import io
import os
import re
import sys

sys.path.insert(0, "scripts")
import win32com.client
import t8_gate as t

SUBS_DIR = r"C:\MyProjects\APKModSrc\Subsystems"
SUBS = [u"АпкСВНГрупповойУчет", u"АпкКРСГрупповойУчет",
        u"АпкСвинокомплексИндивидуальныйУчет"]
OUT = "tmp/livestock_probe.txt"

out = io.open(OUT, "w", encoding="utf-8")


def w(line=u""):
    out.write(line + u"\n")


# --- 1. составы подсистем из XML ---
contents = {}
for sub in SUBS:
    path = os.path.join(SUBS_DIR, sub + ".xml")
    txt = io.open(path, encoding="utf-8").read()
    items = re.findall(r'<xr:Item xsi:type="xr:MDObjectRef">([A-Za-z]+)\.([A-Za-zА-Яа-яЁё0-9]+)</xr:Item>', txt)
    contents[sub] = items

w(u"=== РАЗВЕДКА ЖИВОТНОВОДСТВА (демо-база dev_erpapk_demo) ===")
for sub in SUBS:
    docs = sorted(n for k, n in contents[sub] if k == "Document")
    cats = sorted(n for k, n in contents[sub] if k == "Catalog")
    w(u"")
    w(u"## Подсистема %s: %d документов, %d справочников" % (sub, len(docs), len(cats)))
    w(u"Документы: " + u", ".join(docs))
    w(u"Справочники: " + u", ".join(cats))

# --- 2. COM-проба данных ---
agent = win32com.client.Dispatch("V85.COMConnector").Connect(
    t.conn_str(t.ADMIN, u""))

all_docs = []
for sub in SUBS:
    for k, n in contents[sub]:
        if k == "Document" and (k, n) not in all_docs:
            pass
seen_docs = set()
doc_list = []
for sub in SUBS:
    for k, n in contents[sub]:
        if k == "Document" and n not in seen_docs:
            seen_docs.add(n)
            doc_list.append(n)
# КРС-документы: в АпкКРСГрупповойУчет.xml идут uuid-ссылками (артефакт
# дампа), берём по префиксу из каталога Documents + молочные
for extra in sorted(os.listdir(r"C:\MyProjects\APKModSrc\Documents")):
    if not extra.endswith(".xml"):
        continue
    if (extra.startswith(u"АпкКРС") or extra in
            (u"АпкЖурналНадояМолока.xml", u"АпкВнутреннийРасходМолока.xml")):
        n = extra[:-4]
        if n not in seen_docs:
            seen_docs.add(n)
            doc_list.append(n)

w(u"")
w(u"=== ДАННЫЕ В БАЗЕ (уникальных документов: %d) ===" % len(doc_list))
nonempty_docs = []
for name in doc_list:
    try:
        q = agent.NewObject(u"Запрос")
        q.Text = (u"ВЫБРАТЬ КОЛИЧЕСТВО(*) КАК K ИЗ Документ." + name)
        sel = q.Execute().Choose()
        total = 0
        if sel.Next():
            total = sel.K
        q2 = agent.NewObject(u"Запрос")
        q2.Text = (u"ВЫБРАТЬ ПЕРВЫЕ 3 Документ." + name +
                   u".Ссылка КАК Ref ИЗ Документ." + name +
                   u" УПОРЯДОЧИТЬ ПО Документ." + name + u".Дата УБЫВ")
        sel2 = q2.Execute().Choose()
        samples = []
        while sel2.Next():
            ref = sel2.Ref
            samples.append(u"%s №%s от %s | автор: %s | проведен: %s" % (
                ref.Метаданные().Имя, ref.Номер, ref.Дата, ref.Автор, ref.Проведен))
        w(u"")
        w(u"[%s] всего: %s" % (name, total))
        for s in samples:
            w(u"   " + s)
        if total:
            nonempty_docs.append((name, total))
    except Exception as e:
        w(u"")
        w(u"[%s] ОШИБКА: %s" % (name, e))

w(u"")
w(u"=== СПРАВОЧНИКИ-КАРКАС (животные/фермы/статусы и пр.) ===")
seen_cats = set()
cat_list = []
for sub in SUBS:
    for k, n in contents[sub]:
        if k == "Catalog" and n not in seen_cats:
            seen_cats.add(n)
            cat_list.append(n)
for name in cat_list:
    try:
        q = agent.NewObject(u"Запрос")
        q.Text = (u"ВЫБРАТЬ КОЛИЧЕСТВО(*) КАК K ИЗ Справочник." + name)
        sel = q.Execute().Choose()
        total = 0
        if sel.Next():
            total = sel.K
        w(u"[Справочник.%s] элементов: %s" % (name, total))
    except Exception as e:
        w(u"[Справочник.%s] ОШИБКА: %s" % (name, e))

w(u"")
w(u"=== ИТОГ ===")
w(u"Непустых типов документов: %d из %d" % (len(nonempty_docs), len(doc_list)))
for name, total in sorted(nonempty_docs, key=lambda x: -x[1]):
    w(u"  %s: %s" % (name, total))
out.close()
print("probe done ->", OUT)
