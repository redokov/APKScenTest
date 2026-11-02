# -*- coding: utf-8 -*-
"""S009 T2: dump ДеревоКОтражению leaves of АРМ выработки for November 2026
(after E2E#4: 5 PBZ НВЦБ-000007 with VI rows + партии)."""
import io
import sys

sys.path.insert(0, 'scripts')
import win32com.client
import t8_gate as t

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
conn = win32com.client.Dispatch('V85.COMConnector').Connect(t.conn_str(t.ADMIN, ''))
out = io.open('tmp/s009/leaf_dump_nov.txt', 'w', encoding='utf-8')

qd = conn.NewObject('Query')
qd.Text = ('ВЫБРАТЬ ДАТАВРЕМЯ(2026, 11, 1) КАК Д1, '
           'ДАТАВРЕМЯ(2026, 11, 30, 23, 59, 59) КАК Д2')
seld = qd.Execute().Choose()
seld.Next()
Per = conn.NewObject('Структура')
Per.Вставить('ДатаНачала', seld.Д1)
Per.Вставить('ДатаОкончания', seld.Д2)
access_orgs = conn.Справочники.Организации.ДоступныеОрганизации(True)
Orgs = conn.NewObject('Массив')
for i in range(access_orgs.Количество()):
    Orgs.Add(access_orgs.Get(i))
St = conn.NewObject('Структура')
St.Вставить('Период', Per)
St.Вставить('Исполнитель', conn.Справочники.ФизическиеЛица.ПустаяСсылка())
St.Вставить('МассивОрганизаций', Orgs)
St.Вставить('ВыводитьТолькоТребующееОтражения', True)
Res = conn.Обработки.АпкАРМПоОтражениюВыработкиСотрудников.ПолучитьСостояниеОтражения(St)


def leaf_rows(rows):
    for i in range(rows.Количество()):
        r = rows.Get(i)
        sub = r.Строки
        if sub.Количество() == 0:
            yield r
        else:
            for x in leaf_rows(sub):
                yield x


S = conn.String
for leaf in leaf_rows(Res.ДеревоСостояния.Строки):
    out.write('leaf:\n')
    for col in ('Организация', 'Подразделение', 'Исполнитель', 'ТипЗатрат', 'ВидРаботы',
                'СтатьяКалькуляции', 'АпкПартияПроизводства', 'Распоряжение',
                'ХарактеристикаРаботы', 'Вытеснено', 'КоличествоКОтражению', 'СуммаКОтражению',
                'КоличествоОтражено', 'СуммаОтражено'):
        try:
            out.write('  %s = %s\n' % (col, S(getattr(leaf, col))))
        except Exception as ex:
            out.write('  %s = ERR:%s\n' % (col, ex))

out.close()
print(io.open('tmp/s009/leaf_dump_nov.txt', encoding='utf-8').read())
