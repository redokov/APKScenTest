# -*- coding: utf-8 -*-
# T8: COM read-only probe — почему МоточасовПриВыезде невидим для МТЗ-82.
# Читает: константы (АпкУчетМоточасов, АпкРежимУчетаГСМ_СХТехники),
# реквизиты ТС (АпкМодель, АпкРежимУчетаГСМ) и флаги модели СХ-техники.
# Никаких записей — только чтение. Результат -> tmp/t8/visibility-probe.txt (UTF-8).
import io
import sys

import uuid

import win32com.client

def new_uuid(s):
    return agent.NewObject("УникальныйИдентификатор", s)

sys.stdout.reconfigure(encoding="utf-8")

CONN = "Srvr='localhost';Ref='dev_erpapk_demo';Usr='Администратор (ОрловАВ)';Pwd='';"
TS_UUID = "a5ee1259-928f-11e5-893f-00261877087b"  # МТЗ-82, Гос.№36ВА33-79
OUT = r"c:/MyProjects/APKScenTest/tmp/t8/visibility-probe.txt"

out = io.StringIO()


def w(*a):
    out.write(" ".join(str(x) for x in a) + "\n")


agent = win32com.client.Dispatch("V85.COMConnector").Connect(CONN)

w("const АпкУчетМоточасов =", agent.Константы.АпкУчетМоточасов.Получить())
w("const АпкРежимУчетаГСМ_СХТехники =", agent.Константы.АпкРежимУчетаГСМ_СХТехники.Получить())
w("const АпкУчетУЭГ =", agent.Константы.АпкУчетУЭГ.Получить())
w("const АпкВестиУчетЗаданийМеханизатору =", agent.Константы.АпкВестиУчетЗаданийМеханизатору.Получить())

ts = agent.Справочники.ТранспортныеСредства.ПолучитьСсылку(new_uuid(TS_UUID))
w("ТС представление =", ts)
ts_obj = ts.ПолучитьОбъект() if False else None
# read attrs via query-less way: XMLGetString is heavy; use ПолучитьРеквизиты? not exists.
# Use object attributes through Ссылка properties:
w("ТС АпкРежимУчетаГСМ =", ts.АпкРежимУчетаГСМ)
model = ts.АпкМодель
w("ТС АпкМодель =", model)
if model:
    for flag in ("ОтображатьМоточасы", "ОтображатьОборудование",
                 "ОтображатьКилометры", "ОтображатьГектары",
                 "ОтображатьТонны", "ОтображатьВремяНачалаОкончания",
                 "ОтображатьУЭГА", "ОтображатьДопОбъемРабот",
                 "ОтображатьКоличествоОборудованияВАгрегате"):
        try:
            w("  model.%s = %s" % (flag, getattr(model, flag)))
        except Exception as e:
            w("  model.%s = ERR %s" % (flag, str(e)[:100]))

# заодно: исходный документ НВ00-000001 (ref 14f60fc2-92b1-11e5-893f-00261877087b)
doc_ref = agent.Документы.АпкПутевойЛистТракториста.ПолучитьСсылку(
    new_uuid("14f60fc2-92b1-11e5-893f-00261877087b"))
w("src doc =", doc_ref)
try:
    w("src doc МоточасовПриВыезде =", doc_ref.МоточасовПриВыезде)
    w("src doc Техника =", doc_ref.Техника)
    w("src doc Проведен =", doc_ref.Проведен)
except Exception as e:
    w("src doc read ERR", str(e)[:200])

open(OUT, "w", encoding="utf-8").write(out.getvalue())
print("written", OUT)
