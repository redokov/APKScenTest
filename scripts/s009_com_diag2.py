# -*- coding: utf-8 -*-
"""S009 T2 diag2: ПартииПроизводства для ноябрьского ПБЗ + содержимое
ВыходныхИзделий; наличие Выработки без фильтра даты."""
import sys
import io

sys.path.insert(0, 'scripts')
import win32com.client
import t8_gate as t

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
conn = win32com.client.Dispatch("V85.COMConnector").Connect(t.conn_str(t.ADMIN, ""))

out = io.open('tmp/s009/com_diag2.txt', 'w', encoding='utf-8')


def q_all(txt):
    qq = conn.NewObject("Query")
    qq.Text = txt
    sel = qq.Execute().Choose()
    rows = []
    while sel.Next():
        rows.append(sel)
    return rows


# ПБЗ ноября + содержимое ВыходныхИзделий
rows = q_all(
    "ВЫБРАТЬ РАЗЛИЧНЫЕ Док.Ссылка КАК Реф, Док.Номер КАК Номер "
    "ИЗ Документ.ПроизводствоБезЗаказа КАК Док "
    "ГДЕ Док.Дата МЕЖДУ ДАТАВРЕМЯ(2026, 11, 1) И ДАТАВРЕМЯ(2026, 11, 30, 23, 59, 59)")
out.write("PBZ distinct November: %d\n" % len(rows))
pbz_refs = []
for r in rows:
    out.write("  %s\n" % r.Номер)
    pbz_refs.append(r.Реф)
    vi = r.Реф.ВыходныеИзделия
    for i in range(vi.Count()):
        row = vi.Get(i)
        out.write("    VI: nomen=%s qty=%s gruppa=%s\n" % (
            row.Номенклатура, row.Количество, row.НомерГруппыЗатрат))

# ПартииПроизводства с документом = ноябрьский ПБЗ
for ref in pbz_refs:
    qq = conn.NewObject("Query")
    qq.Text = ("ВЫБРАТЬ Партия.Ссылка КАК Реф, Партия.Код КАК Код "
               "ИЗ Справочник.ПартииПроизводства КАК Партия "
               "ГДЕ Партия.Документ = &Док")
    qq.УстановитьПараметр("Док", ref)
    sel = qq.Execute().Choose()
    n = 0
    while sel.Next():
        n += 1
        out.write("  Partiya for PBZ: code=%s\n" % sel.Код)
    out.write("  Partiya count for %s: %d\n" % (ref.Номер, n))

out.close()
print(io.open('tmp/s009/com_diag2.txt', encoding='utf-8').read())
