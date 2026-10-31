# -*- coding: utf-8 -*-
"""T3 диагностика: статусы ЖивотныхГрупповойУчет и склады (имена, владельцы).
Usage: python scripts/s006_diag_status.py"""
import io
import sys

sys.path.insert(0, "scripts")
import win32com.client
import t8_gate as t

agent = win32com.client.Dispatch("V85.COMConnector").Connect(
    t.conn_str(t.ADMIN, u""))
out = io.open("tmp/s006/diag-status.txt", "w", encoding="utf-8")
q = agent.NewObject(u"Запрос")
q.Text = (u"ВЫБРАТЬ ПЕРВЫЕ 60 Спр.Ссылка КАК R, ПРЕДСТАВЛЕНИЕ(Спр.Ссылка) "
          u"КАК P ИЗ Справочник.АпкСтатусыЖивотныхГрупповойУчет КАК Спр "
          u"УПОРЯДОЧИТЬ ПО Спр.Код")
s = q.Execute().Choose()
while s.Next():
    out.write(u"статус [%s]\n" % s.P)
q2 = agent.NewObject(u"Запрос")
q2.Text = (u"ВЫБРАТЬ ПЕРВЫЕ 40 ПРЕДСТАВЛЕНИЕ(Спр.Ссылка) КАК P "
           u"ИЗ Справочник.Склады КАК Спр "
           u"ГДЕ Спр.Наименование ПОДОБНО \"%Агидельская%\" "
           u"ИЛИ Спр.Наименование ПОДОБНО \"%СТФ 1%\"")
s2 = q2.Execute().Choose()
out.write(u"---склады---\n")
while s2.Next():
    out.write(u"склад [%s]\n" % s2.P)
out.close()
print("done")
