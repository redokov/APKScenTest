# -*- coding: utf-8 -*-
"""S009 T2 diag: all PBZ + Vyrabotka docs regardless of date; session date."""
import sys
import io

sys.path.insert(0, 'scripts')
import win32com.client
import t8_gate as t

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
conn = win32com.client.Dispatch("V85.COMConnector").Connect(t.conn_str(t.ADMIN, ""))

out = io.open('tmp/s009/com_diag.txt', 'w', encoding='utf-8')


def q_all(txt):
    qq = conn.NewObject("Query")
    qq.Text = txt
    sel = qq.Execute().Choose()
    rows = []
    while sel.Next():
        rows.append(sel)
    return rows


out.write("SessionDate: %s\n" % conn.ПолучитьТекущуюДатуСеанса() if hasattr(conn, "ПолучитьТекущуюДатуСеанса") else "")

rows = q_all(
    "ВЫБРАТЬ ПЕРВЫЕ 30 Док.Ссылка КАК Реф, Док.Номер КАК Номер, Док.Дата КАК Дата, "
    "Док.Проведен КАК Проведен ИЗ Документ.ПроизводствоБезЗаказа КАК Док "
    "УПОРЯДОЧИТЬ ПО Док.Дата УБЫВ")
out.write("PBZ all (top30): %d\n" % len(rows))
for r in rows:
    vi = r.Реф.ВыходныеИзделия
    out.write("  %s %s posted=%s VI=%d\n" % (r.Номер, str(r.Дата)[:10], r.Проведен, vi.Count()))

rows = q_all(
    "ВЫБРАТЬ ПЕРВЫЕ 30 Док.Номер КАК Номер, Док.Дата КАК Дата, Док.Проведен КАК Проведен "
    "ИЗ Документ.ВыработкаСотрудников КАК Док УПОРЯДОЧИТЬ ПО Док.Дата УБЫВ")
out.write("Vyrabotka all (top30): %d\n" % len(rows))
for r in rows:
    out.write("  %s %s posted=%s\n" % (r.Номер, str(r.Дата)[:10], r.Проведен))

out.close()
print(io.open('tmp/s009/com_diag.txt', encoding='utf-8').read())
