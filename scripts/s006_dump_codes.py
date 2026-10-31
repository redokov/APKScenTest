# -*- coding: utf-8 -*-
"""T3: коды (и представления «Имя (Код)») элементов СтруктураПредприятия
и АпкФермы, нужных для probe/фикстур СВН и КРС.
Usage: python scripts/s006_dump_codes.py"""
import io
import sys

sys.path.insert(0, "scripts")
import win32com.client
import t8_gate as t

agent = win32com.client.Dispatch("V85.COMConnector").Connect(
    t.conn_str(t.ADMIN, u""))
out = io.open("tmp/s006/codes.txt", "w", encoding="utf-8")

STRUCT = [u"СТФ Агидельская", u"СТФ №1", u"Мелихово МТФ", u"Грибановка МТФ",
          u"СТФ №3", u"Дирекция"]
FERMY = [u"СТФ Агидельская", u"СТФ 1", u"СТФ Стерлитамакская",
         u"Мелихово МТФ", u"Грибановка МТФ", u"СТФ 3"]
SKLADY = [u"Склад Агидельская", u"Склад СТФ 1", u"Склад Мелихово"]


def dump_cat(catalog, names, label, with_owner=False, code_field=u"Код"):
    q = agent.NewObject(u"Запрос")
    like = u" ИЛИ ".join(
        u"Спр.Наименование = \"%s\"" % n for n in names)
    own = (u", ПРЕДСТАВЛЕНИЕ(Спр.Владелец) КАК Own " if with_owner else u"")
    code = ((u"Спр." + code_field + u" КАК C") if code_field
            else u"0 КАК C")
    q.Text = (u"ВЫБРАТЬ Спр.Ссылка КАК R, Спр.Наименование КАК N, " +
              code + own +
              u" ИЗ Справочник." + catalog + u" КАК Спр ГДЕ " + like)
    s = q.Execute().Choose()
    out.write(u"### %s\n" % label)
    while s.Next():
        if with_owner:
            out.write(u"  [%s] код=%s | владелец=[%s]\n" % (s.N, s.C, s.Own))
        else:
            out.write(u"  [%s] код=%s\n" % (s.N, s.C))


dump_cat(u"СтруктураПредприятия", STRUCT, u"СтруктураПредприятия")
dump_cat(u"АпкФермы", FERMY, u"АпкФермы", with_owner=True)
dump_cat(u"Склады", SKLADY, u"Склады", code_field=None)
out.close()
print("done")
