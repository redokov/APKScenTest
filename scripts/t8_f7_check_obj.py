# -*- coding: utf-8 -*-
"""T8 probe6b предпроверка (COM read-only): Код/Наименование объекта затрат
"115, Пшеница озимая 2015 г." и его период действия в РС АпкИсторияПолей_ДанныеДляПодбора."""
import json


def main():
    conn = None
    try:
        import win32com.client
        conn = win32com.client.Dispatch("V85.COMConnector").Connect(
            'Srvr="localhost";Ref="dev_erpapk_demo";Usr="Администратор (ОрловАВ)";Pwd=""')
    except Exception as e:
        print("COM connect FAIL:", e)
        return 1
    try:
        q = conn.NewObject("Запрос")
        q.Text = ("ВЫБРАТЬ Спр.Ссылка, Спр.Код, Спр.Наименование, Спр.АпкВид ИЗ Справочник.СтруктураПредприятия КАК Спр "
                  "ГДЕ Спр.Код = \"115\" ИЛИ Спр.Наименование ПОДОБНО \"%Пшеница озимая 2015%\"")
        sel = q.Execute()
        refs = []
        while sel.Next():
            refs.append((sel.Ссылка, sel.Код, sel.Наименование, sel.АпкВид))
        for r in refs:
            print("OBJ:", r[1], "|", r[2], "| вид:", r[3])
        if not refs:
            print("not found")
            return 1
        ref = refs[0][0]
        q2 = conn.NewObject("Запрос")
        q2.Text = ("ВЫБРАТЬ Ист.НачалоПериодаАктуальности, Ист.КонецПериодаАктуальности, Ист.ГодУрожая "
                    "ИЗ РегистрСведений.АпкИсторияПолей_ДанныеДляПодбора КАК Ист "
                    "ГДЕ Ист.ОбъектЗатрат = &Реф")
        q2.SetParameter("Реф", ref)
        sel2 = q2.Execute()
        n = 0
        while sel2.Next():
            n += 1
            print("PERIOD:", sel2.НачалоПериодаАктуальности, "-", sel2.КонецПериодаАктуальности, "ГодУрожая:", sel2.ГодУрожая)
        print("periods:", n)
    finally:
        try:
            conn = None
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
