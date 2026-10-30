# -*- coding: utf-8 -*-
"""Разведка животноводства, шаг 4: у Федорова (и Орлова/Соколова для
контроля) — есть ли привязка к живому ИБ-пользователю и под каким именем.
Вывод — UTF-8 в tmp/livestock_userbind.txt.
Usage: python scripts/probe_livestock_userbind.py"""
import io
import sys

sys.path.insert(0, "scripts")
import win32com.client
import t8_gate as t

agent = win32com.client.Dispatch("V85.COMConnector").Connect(
    t.conn_str(t.ADMIN, u""))
out = io.open("tmp/livestock_userbind.txt", "w", encoding="utf-8")

TARGETS = [u"Орлов Александр Владимирович", u"Соколов Максим Игоревич",
           u"Федоров Борис Михайлович"]

q = agent.NewObject(u"Запрос")
q.Text = (u"ВЫБРАТЬ Пользователи.Ссылка КАК Ref, "
          u"Пользователи.Наименование КАК Имя, "
          u"Пользователи.ИдентификаторПользователяИБ КАК U "
          u"ИЗ Справочник.Пользователи КАК Пользователи")
sel = q.Execute().Choose()
cat_bind = {}
while sel.Next():
    name = sel.Имя
    if name in TARGETS:
        try:
            u = str(sel.U)  # UUID -> string
        except Exception:
            u = u"??"
        cat_bind[name] = u
        out.write(u"Справочник '%s' -> UUIDИБ: %s\n" % (name, u))

# живые ИБ-пользователи: имя + UUID
users = agent.ПользователиИнформационнойБазы
ib = {}
for u in users.ПолучитьПользователей():
    ib[str(u.Имя)] = str(u.УникальныйИдентификатор)
out.write(u"\nЖивых ИБ-пользователей: %d\n" % len(ib))
for n in sorted(ib):
    out.write(u"ИБ: %s | %s\n" % (n, ib[n]))

out.write(u"\n=== СВЕРКА ===\n")
for name in TARGETS:
    uuid = cat_bind.get(name, u"—")
    match = [n for n, u2 in ib.items() if u2 == uuid]
    out.write(u"%s: UUID=%s -> ИБ-пользователь: %s\n" % (
        name, uuid, match[0] if match else u"НЕТ ПРИВЯЗКИ"))
out.close()
print("bind probe done")
