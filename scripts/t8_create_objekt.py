# -*- coding: utf-8 -*-
"""T8: идемпотентное создание записи АпкПоля.ИсторияПоля (текущий период).

ЕДИНСТВЕННОЕ разрешённое изменение данных (решение пользователя 2026-10-14):
если у поля 115 организации НИВА нет покрывающего текущую дату объекта затрат,
добавляем строку ТЧ ИсторияПоля: культура «Пшеница озимая», ГодУрожая=<тек.год>,
Период [нач. тек. месяца .. 31.12.2099], Подразделение «Отделение №2».
ПередЗаписью сам создаст объект затрат СтруктураПредприятия
«115, Пшеница озимая <год> г.» и перепишет РС.АпкИсторияПолей(+_ДанныеДляПодбора).

Идемпотентность: перед записью проверяем наличие покрывающей записи
в РС.АпкИсторияПолей_ДанныеДляПодбора (поле+организация+дата) и строки ТЧ.
"""
import datetime
import io
import json
import uuid

POLE_CODE = "00-0000001"
POLE_NAME = "115"
CULTURE_NAME = "Пшеница озимая"
PODR_NAME = "Отделение №2"
END_YEAR = 2099


def main():
    try:
        import win32com.client
        import pywintypes
    except Exception as e:
        print("import FAIL:", e)
        return 1
    agent = None
    try:
        agent = win32com.client.Dispatch("V85.COMConnector").Connect(
            'Srvr="localhost";Ref="dev_erpapk_demo";Usr="Администратор (ОрловАВ)";Pwd=""')
    except Exception as e:
        print("COM connect FAIL:", e)
        return 1

    def q_sel(text):
        q = agent.NewObject("Query")
        q.Text = text
        return q.Execute().Choose()

    def d1c(y, m, d):
        return pywintypes.Time(datetime.datetime(y, m, d, 0, 0, 0))

    today = datetime.date.today()
    ms = datetime.date(today.year, today.month, 1)
    cur_year = today.year
    out = {"today": today.strftime("%d.%m.%Y"), "period_beg": ms.strftime("%d.%m.%Y"),
           "period_end": "31.12.%d" % END_YEAR, "cur_year": cur_year}
    expected = "%s, %s %d г." % (POLE_NAME, CULTURE_NAME, cur_year)
    out["expected_presentation"] = expected

    try:
        # --- 0) проверка блокирующих документов изменения истории полей уже сделана
        #     в t8_pick_field.py (docs=0); повторять не требуется.

        # --- 1) идемпотентность: покрывающая запись в ДанныеДляПодбора?
        sel = q_sel(
            "ВЫБРАТЬ Д.ОбъектЗатрат.Наименование КАК Name "
            "ИЗ РегистрСведений.АпкИсторияПолей_ДанныеДляПодбора КАК Д "
            "ГДЕ Д.Поле.Код = \"%s\" "
            "И Д.Организация.Наименование = \"НИВА\" "
            "И Д.НачалоПериодаАктуальности <= ДАТАВРЕМЯ(%d, %d, %d) "
            "И Д.КонецПериодаАктуальности > ДАТАВРЕМЯ(%d, %d, %d)"
            % (POLE_CODE, today.year, today.month, today.day,
               today.year, today.month, today.day))
        existing = []
        while sel.Next():
            existing.append(str(sel.Name))
        if existing:
            out["status"] = "already-exists"
            out["existing"] = existing
            print("SKIP: уже есть покрывающие записи: %s" % existing)
            _dump(out)
            return 0

        # --- 2) ссылки: поле, культура, подразделение
        sel = q_sel(
            "ВЫБРАТЬ П.Ссылка КАК Ref ИЗ Справочник.АпкПоля КАК П ГДЕ П.Код = \"%s\"" % POLE_CODE)
        if not sel.Next():
            print("FAIL: поле не найдено")
            return 1
        pole_ref = sel.Ref

        sel = q_sel(
            "ВЫБРАТЬ К.Ссылка КАК Ref ИЗ Справочник.АпкКультуры КАК К "
            "ГДЕ К.Наименование = \"%s\"" % CULTURE_NAME)
        if not sel.Next():
            print("FAIL: культура не найдена")
            return 1
        culture_ref = sel.Ref

        sel = q_sel(
            "ВЫБРАТЬ ПЕРВЫЕ 1 Т.Подразделение КАК Ref "
            "ИЗ Справочник.АпкПоля.ИсторияПоля КАК Т "
            "ГДЕ Т.Ссылка.Код = \"%s\" "
            "И Т.Подразделение <> ЗНАЧЕНИЕ(Справочник.СтруктураПредприятия.ПустаяСсылка)"
            % POLE_CODE)
        if not sel.Next():
            print("FAIL: подразделение в ТЧ не найдено")
            return 1
        podr_ref = sel.Ref

        # --- 3) объект справочника АпкПоля
        pole_obj = pole_ref.ПолучитьОбъект()
        hist = pole_obj.ИсторияПоля

        # двойная защита: нет ли уже такой строки ТЧ (культура+год+подразделение)
        dup = None
        n_hist = hist.Количество()
        for i in range(n_hist):
            r = hist.Получить(i)
            if (str(r.Культура) == CULTURE_NAME) and int(r.ГодУрожая) == cur_year:
                dup = i
                break
        if dup is not None:
            out["status"] = "tc-row-exists"
            print("SKIP: строка ТЧ уже есть (индекс %d)" % dup)
            _dump(out)
            return 0

        # --- 4) добавить строку и записать
        row = hist.Добавить()
        row.КлючСвязи = str(uuid.uuid4())
        row.Культура = culture_ref
        row.ГодУрожая = cur_year
        row.НачалоПериодаАктуальности = d1c(ms.year, ms.month, ms.day)
        row.КонецПериодаАктуальности = d1c(END_YEAR, 12, 31)
        row.Подразделение = podr_ref
        row.ЭтоРодитель = False
        row.ЭтоВетвь = False
        row.НеИспользуется = False
        row.НеИспользуетсяНачинаяСГода = False
        pole_obj.Записать()
        print("WRITE: строка добавлена, объект записан")

        # --- 5) верификация: покрывающая запись появилась, имя объекта ожидаемо
        sel = q_sel(
            "ВЫБРАТЬ Д.ОбъектЗатрат.Наименование КАК Name "
            "ИЗ РегистрСведений.АпкИсторияПолей_ДанныеДляПодбора КАК Д "
            "ГДЕ Д.Поле.Код = \"%s\" "
            "И Д.Организация.Наименование = \"НИВА\" "
            "И Д.НачалоПериодаАктуальности <= ДАТАВРЕМЯ(%d, %d, %d) "
            "И Д.КонецПериодаАктуальности > ДАТАВРЕМЯ(%d, %d, %d)"
            % (POLE_CODE, today.year, today.month, today.day,
               today.year, today.month, today.day))
        found = []
        while sel.Next():
            found.append(str(sel.Name))
        out["found_after_write"] = found
        print("AFTER: покрывающие записи: %s" % found)
        if expected not in found:
            out["status"] = "FAIL"
            print("FAIL: ожидаемого объекта %s нет в списке" % expected)
            _dump(out)
            return 1
        out["status"] = "created"
        _dump(out)
        return 0
    finally:
        try:
            agent = None
        except Exception:
            pass


def _dump(out):
    with io.open("tmp/t8/create_objekt_result.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    raise SystemExit(main())
