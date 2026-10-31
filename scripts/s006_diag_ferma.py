# -*- coding: utf-8 -*-
"""T3 диагностика: справочник ферм - владелец, элементы, представления.
Usage: python scripts/s006_diag_ferma.py"""
import io
import sys

sys.path.insert(0, "scripts")
import win32com.client
import t8_gate as t

out = io.open("tmp/s006/diag-ferma.txt", "w", encoding="utf-8")


def w(s=u""):
    out.write(s + u"\n")


agent = win32com.client.Dispatch("V85.COMConnector").Connect(
    t.conn_str(t.ADMIN, u""))

# какие типы у реквизитов Подразделение/Ферма документа Опорос
q = agent.NewObject(u"Запрос")
q.Text = (u"ВЫБРАТЬ ПЕРВЫЕ 1 Документ.АпкГрупповойОпорос.Ссылка КАК R "
          u"ИЗ Документ.АпкГрупповойОпорос")
s = q.Execute().Choose()
s.Next()
d = s.R
qf = agent.NewObject(u"Запрос")
qf.Text = (u"ВЫБРАТЬ ПЕРВЫЕ 1 "
           u"ПРЕДСТАВЛЕНИЕ(Документ.АпкГрупповойОпорос.Подразделение) КАК P1, "
           u"ПРЕДСТАВЛЕНИЕ(Документ.АпкГрупповойОпорос.Ферма) КАК P2, "
           u"Документ.АпкГрупповойОпорос.Подразделение КАК R1, "
           u"Документ.АпкГрупповойОпорос.Ферма КАК R2 "
           u"ИЗ Документ.АпкГрупповойОпорос")
sf = qf.Execute().Choose()
sf.Next()
w(u"Реквизиты представителя опороса:")
w(u"  Подразделение = [%s] ref=%s" % (sf.P1, sf.R1))
w(u"  Ферма = [%s] ref=%s" % (sf.P2, sf.R2))
d_sub = sf.R1
d_ferm = sf.R2
w(u"")

# элементы справочника АпкФермы
q2 = agent.NewObject(u"Запрос")
q2.Text = (u"ВЫБРАТЬ ПЕРВЫЕ 30 Спр.Ссылка КАК R, ПРЕДСТАВЛЕНИЕ(Спр.Ссылка) "
           u"КАК P, ПРЕДСТАВЛЕНИЕ(Спр.Владелец) КАК Parent "
           u"ИЗ Справочник.АпкФермы КАК Спр УПОРЯДОЧИТЬ ПО Спр.Код")
s2 = q2.Execute().Choose()
w(u"Справочник АпкФермы (первые 30):")
while s2.Next():
    w(u"  %s | parent=%s" % (s2.P, s2.Parent))
w(u"")

q3 = agent.NewObject(u"Запрос")
q3.Text = (u"ВЫБРАТЬ ПЕРВЫЕ 30 Спр.Ссылка КАК R, ПРЕДСТАВЛЕНИЕ(Спр.Ссылка) "
           u"КАК P ИЗ Справочник.АпкФермы КАК Спр "
           u"ГДЕ Спр.Владелец = &Влад")
q3.SetParameter(u"Влад", d_sub)
s3 = q3.Execute().Choose()
w(u"АпкФермы с владельцем=Подразделение представителя:")
n = 0
while s3.Next():
    w(u"  %s" % s3.P)
    n += 1
w(u"  (итого %d)" % n)

out.close()
print("diag done")
