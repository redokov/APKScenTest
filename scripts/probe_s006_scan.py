# -*- coding: utf-8 -*-
"""T2 спеки 006: скан-гейт — валидация coverage-map записей животноводства
против живых данных dev_erpapk_demo. Для каждого из 14 типов: топ-3
документа, все fieldList.header поля + ТЧ-колонки у топ-представителя;
заполненность (значение/пусто/НЕТ ПОЛЯ). Авторы по типам.
Вывод — UTF-8 в tmp/s006/scan-plan.txt.
Usage: python scripts/probe_s006_scan.py"""
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

out = io.open("tmp/s006/scan-plan.txt", "w", encoding="utf-8")


def w(s=u""):
    out.write(s + u"\n")


agent = win32com.client.Dispatch("V85.COMConnector").Connect(
    t.conn_str(t.ADMIN, u""))

w(u"=== T2 СКАН-ГЕЙТ спеки 006: coverage-map vs живые данные ===")
gate_fail = 0
for name in LIVE:
    entry = docs.get(name)
    if not entry:
        w(u"\n[%s] НЕТ ЗАПИСИ В COVERAGE-MAP — ФЕЙЛ ГЕЙТА" % name)
        gate_fail += 1
        continue
    fl = entry["fieldList"]
    header = fl.get("header", [])
    tabular = fl.get("tabular", {})
    tpl = entry.get("template")
    try:
        q = agent.NewObject(u"Запрос")
        q.Text = (u"ВЫБРАТЬ ПЕРВЫЕ 1 Документ." + name +
                  u".Ссылка КАК Ref ИЗ Документ." + name +
                  u" УПОРЯДОЧИТЬ ПО Документ." + name + u".Дата УБЫВ")
        sel = q.Execute().Choose()
        if not sel.Next():
            w(u"\n[%s] НЕТ ДАННЫХ — ФЕЙЛ ГЕЙТА" % name)
            gate_fail += 1
            continue
        ref = sel.Ref
        w(u"")
        w(u"## %s (шаблон %s) — представитель: %s" % (name, tpl, ref))
        # авторы
        qa = agent.NewObject(u"Запрос")
        qa.Text = (u"ВЫБРАТЬ РАЗЛИЧНЫЕ ПРЕДСТАВЛЕНИЕ(Документ." + name +
                   u".Автор) КАК A, КОЛИЧЕСТВО(РАЗЛИЧНЫЕ Документ." + name +
                   u".Ссылка) КАК N ИЗ Документ." + name +
                   u" СГРУППИРОВАТЬ ПО ПРЕДСТАВЛЕНИЕ(Документ." + name + u".Автор)")
        sa = qa.Execute().Choose()
        authors = []
        while sa.Next():
            authors.append(u"%s (%s)" % (sa.A, sa.N))
        w(u"Авторы: " + u"; ".join(authors))
        obj = ref.ПолучитьОбъект()
        # шапка
        for f in header:
            try:
                v = getattr(obj, f)
                vs = u"" if v is None else u"%s" % v
                mark = u"OK" if vs else u"ПУСТО"
                w(u"  header.%s = %s [%s]" % (f, (vs[:60] or u"—"), mark))
            except Exception:
                w(u"  header.%s — НЕТ ПОЛЯ [ФЕЙЛ]" % f)
                gate_fail += 1
        # ТЧ
        for ts, cols in tabular.items():
            try:
                rows = getattr(obj, ts)
                cnt = rows.Количество()
                w(u"  ТЧ %s: строк %d" % (ts, cnt))
                if cnt:
                    row0 = rows.Получить(0)
                    for c in cols:
                        try:
                            v = getattr(row0, c)
                            vs = u"" if v is None else u"%s" % v
                            w(u"    %s = %s [%s]" % (c, (vs[:60] or u"—"),
                                                     u"OK" if vs else u"ПУСТО"))
                        except Exception:
                            w(u"    %s — НЕТ ПОЛЯ [ФЕЙЛ]" % c)
                            gate_fail += 1
                else:
                    w(u"    (пустая ТЧ у представителя — колонки не проверены)")
            except Exception:
                w(u"  ТЧ %s — НЕТ ТАБЛИЧНОЙ ЧАСТИ [ФЕЙЛ]" % ts)
                gate_fail += 1
    except Exception as e:
        w(u"\n[%s] ОШИБКА СКАНА: %s [ФЕЙЛ ГЕЙТА]" % (name, e))
        gate_fail += 1

w(u"")
w(u"=== ИТОГ ГЕЙТА: фейлов %d (0 = PASS) ===" % gate_fail)
out.close()
print("scan gate done, fails:", gate_fail)
