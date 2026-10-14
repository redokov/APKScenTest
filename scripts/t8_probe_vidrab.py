# -*- coding: utf-8 -*-
# t8 COM read-only probe: does "Внесение удобрений" вид работ have АпкОсновноеНаправлениеЗатрат?
import win32com.client, sys

agent = win32com.client.Dispatch('V85.COMConnector').Connect(
    "Srvr='localhost';Ref='dev_erpapk_demo';Usr='Администратор (ОрловАВ)';")
q = ('ВЫБРАТЬ ПЕРВЫЕ 20 Пер.Ссылка КАК Ссылка ИЗ Перечисление.АпкТипыЗатрат КАК Пер')
res = agent.NewObject('Query')
res.Text = q
sel = res.Execute().Choose()
out = []
while sel.Next():
    out.append(agent.String(sel.Ссылка))
sys.stdout.buffer.write(('\n'.join(out) or 'EMPTY').encode('utf-8'))
