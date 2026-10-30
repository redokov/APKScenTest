# -*- coding: utf-8 -*-
"""Разведка животноводства, шаг 3: справочник Пользователи — у кого есть
привязка к ИБ-пользователю (ИдентификаторПользователяИБ). Особенно Федоров.
Вывод — UTF-8 в tmp/livestock_users.txt.
Usage: python scripts/probe_livestock_users.py"""
import io
import sys

sys.path.insert(0, "scripts")
import win32com.client
import t8_gate as t

agent = win32com.client.Dispatch("V85.COMConnector").Connect(
    t.conn_str(t.ADMIN, u""))
out = io.open("tmp/livestock_users.txt", "w", encoding="utf-8")

q = agent.NewObject(u"Запрос")
q.Text = (u"ВЫБРАТЬ Пользователи.Ссылка КАК Ref, "
          u"Пользователи.Наименование КАК Имя, "
          u"Пользователи.ИдентификаторПользователяИБ КАК UUID "
          u"ИЗ Справочник.Пользователи КАК Пользователи "
          u"УПОРЯДОЧИТЬ ПО Пользователи.Наименование")
sel = q.Execute().Choose()
while sel.Next():
    out.write(u"%s | UUIDИБ: %s\n" % (sel.Имя, sel.UUID))
out.close()
print("users probe done")
