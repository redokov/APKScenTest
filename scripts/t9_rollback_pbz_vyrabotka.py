# -*- coding: utf-8 -*-
# Rollback для scripts/t9_upd_pbz_vyrabotka.py:
#  1) удаляет добавленную строку ВыходныеИзделия (Номенклатура="Услуги машино-тракторного парка",
#     НомерГруппыЗатрат=1) из PБЗ НВЦБ-000002 (окт 2026);
#  2) помечает на удаление созданную ПартияПроизводства (Документ=PБЗ, Код="1");
#  3) гарантирует непроведённое состояние PБЗ.
import io, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import win32com.client
conn = win32com.client.Dispatch("V85.COMConnector").Connect(
    "Srvr='localhost';Ref='dev_erpapk_demo';Usr='Администратор (ОрловАВ)'")
out = io.open('tmp/t9/arm-vyusotr-final/rollback.log', 'w', encoding='utf-8')
S = conn.String

q = conn.NewObject("Query")
q.Text = ("ВЫБРАТЬ Д.Ссылка КАК R ИЗ Документ.ПроизводствоБезЗаказа КАК Д "
          "ГДЕ Д.Номер = \"НВЦБ-000002\" И Д.Дата >= ДАТАВРЕМЯ(2026,10,1)")
sel = q.Execute().Choose()
pbz = None
while sel.Next():
    pbz = sel.R
if pbz is None:
    out.write("PБЗ НЕ НАЙДЕН\n")
    sys.exit(1)

# 1) удалить строку ВыходныеИзделия
obj = pbz.ПолучитьОбъект()
rows = obj.ВыходныеИзделия
idx_del = []
i = 0
while i < rows.Количество():
    r = rows.Get(i)
    if S(r.Номенклатура) == "Услуги машино-тракторного парка" and r.НомерГруппыЗатрат == 1:
        idx_del.append(i)
    i += 1
for i in reversed(idx_del):
    rows.Delete(i)
    out.write("ВыходныеИзделия row %s deleted\n" % i)
if obj.Проведен:
    obj.Записать(conn.РежимЗаписиДокумента.ОтменаПроведения)
else:
    obj.Записать(conn.РежимЗаписиДокумента.Запись)
out.write("PBZ updated,Проведен=%s\n" % S(obj.Проведен))

# 2) пометить партию на удаление
q2 = conn.NewObject("Query")
q2.Text = ("ВЫБРАТЬ П.Ссылка КАК R ИЗ Справочник.ПартииПроизводства КАК П "
           "ГДЕ П.Документ = &D И НЕ П.ПометкаУдаления")
q2.УстановитьПараметр("D", pbz)
sel = q2.Execute().Choose()
n = 0
while sel.Next():
    pobj = sel.R.ПолучитьОбъект()
    pobj.ПометкаУдаления = True
    pobj.Записать()
    n += 1
out.write("parties marked: %s\n" % n)
out.write("OK: rollback завершён\n")
out.close()
print("done")
