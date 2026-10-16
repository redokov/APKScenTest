# -*- coding: utf-8 -*-
# Rollback правки #4: удаляет настройку РС АпкПараметрыОтраженияЗатратРастениеводства
# для вида работы "Загрузка удобрений" (создана scripts/s2_add_nastr_udobren.py).
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import win32com.client
conn = win32com.client.Dispatch("V85.COMConnector").Connect(
    "Srvr='localhost';Ref='dev_erpapk_demo';Usr='Администратор (ОрловАВ)'")

SPRAV = conn.Справочники
VIDY = SPRAV.ВидыРаботСотрудников
dst = getattr(VIDY, "НайтиПоНаименованию")("Загрузка удобрений", True)
if getattr(dst, "Пустая")():
    print("NOT FOUND"); sys.exit(1)

q = conn.NewObject("Query")
q.Text = ("ВЫБРАТЬ ПараметрыОтраженияЗатрат.Период КАК П "
          "ИЗ РегистрСведений.АпкПараметрыОтраженияЗатратРастениеводства КАК ПараметрыОтраженияЗатрат "
          "ГДЕ ПараметрыОтраженияЗатрат.ОбъектНастройки = &Настр "
          "УПОРЯДОЧИТЬ ПО ПараметрыОтраженияЗатрат.Период УБЫВ")
q.УстановитьПараметр("Настр", dst)
sel = q.Execute().Choose()
if not sel.Next():
    print("NO RECORDS"); sys.exit(0)

deleted = 0
while True:
    per = sel.П
    RS = conn.РегистрыСведений.АпкПараметрыОтраженияЗатратРастениеводства
    Nab = RS.СоздатьНаборЗаписей()
    Otb = getattr(Nab, "Отбор")
    Otb.Период.Установить(per)
    Otb.ОбъектНастройки.Установить(dst)
    Otb.Организация.Установить(SPRAV.Организации.ПустаяСсылка())
    Nab.Записать()
    deleted += 1
    if not sel.Next():
        break
print("OK: удалено записей:", deleted)
