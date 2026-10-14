# -*- coding: utf-8 -*-
# T6 diag: list infobase sessions via COM (read-only)
import win32com.client

agent = win32com.client.Dispatch("V85.COMConnector").Connect(
    "Srvr='localhost';Ref='dev_erpapk_demo';Usr='Администратор (ОрловАВ)';Pwd='';")
try:
    sessions = agent.ПолучитьСеансыИнформационнойБазы()
    print("total sessions:", sessions.Количество())
    for i in range(sessions.Количество()):
        s = sessions.Получить(i)
        try:
            print("%s | %s | %s | started=%s" % (
                s.ИмяПользователя or "(none)", s.ИмяКомпьютера,
                s.ИмяПриложения, s.НачалоСеанса))
        except Exception as e:
            print("session row err:", str(e)[:100])
except Exception as e:
    print("sessions via COM fail:", str(e)[:200])
