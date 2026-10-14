# -*- coding: utf-8 -*-
"""T8: COM read-only — детерминированный выбор поля и культуры организации «НИВА».

Правило (закреплено t8-finish-12): первое по Коду поле Справочник.АпкПоля организации
«НИВА», у которого в ТЧ ИсторияПоля есть непустая культура (и нет записи, покрывающей
текущую дату в РС.АпкИсторияПолей_ДанныеДляПодбора). Культура — последняя по
НачалоПериодаАктуальности культура из ТЧ ИсторияПоля этого поля (не родитель).

Fix t8-finish-13 (первый запуск t8-finish-12 упал AttributeError <unknown>.Next):
итерируем выборку через Execute().Choose() + Next(), колонки — через свойства-алиасы
(проверенный паттерн com_diag_period.py), АВТОУПОРЯДОЧИВАНИЕ убрано.

Вывод: JSON-сводка в tmp/t8/pick_field_result.json для последующего идемпотентного
создания (scripts/t8_create_objekt.py). Скрипт ТОЛЬКО читает (read-only).
"""
import datetime
import io
import json


def main():
    try:
        import win32com.client
        conn = win32com.client.Dispatch("V85.COMConnector").Connect(
            'Srvr="localhost";Ref="dev_erpapk_demo";Usr="Администратор (ОрловАВ)";Pwd=""')
    except Exception as e:
        print("COM connect FAIL:", e)
        return 1
    try:
        today = datetime.date.today()
        date_lit = "%d, %d, %d" % (today.year, today.month, today.day)
        out = {"today": today.strftime("%d.%m.%Y")}

        def q_sel(text):
            q = conn.NewObject("Query")
            q.Text = text
            return q.Execute().Choose()

        # 1) все поля АпкПоля организации НИВА, по Коду
        sel = q_sel(
            "ВЫБРАТЬ П.Код КАК Code, П.Наименование КАК Name "
            "ИЗ Справочник.АпкПоля КАК П "
            "ГДЕ НЕ П.ПометкаУдаления "
            "И П.Организация.Наименование = \"НИВА\" "
            "УПОРЯДОЧИТЬ ПО П.Код")
        niva = []
        while sel.Next():
            niva.append({"code": str(sel.Code), "name": str(sel.Name)})
        out["niva_fields"] = niva
        print("== АпкПоля НИВА: %d" % len(niva))
        for f in niva:
            print("FIELD: code=%s name=%s" % (f["code"], f["name"]))
        if not niva:
            print("FAIL: нет полей у НИВА")
            return 1

        # 2) по каждому полю (по коду): покрытие текущей даты в ДанныеДляПодбора + культуры ТЧ
        picked = None
        for f in niva:
            sel = q_sel(
                "ВЫБРАТЬ КОЛИЧЕСТВО(*) КАК Cnt "
                "ИЗ РегистрСведений.АпкИсторияПолей_ДанныеДляПодбора КАК Д "
                "ГДЕ Д.Поле.Код = \"%s\" "
                "И Д.Организация.Наименование = \"НИВА\" "
                "И Д.НачалоПериодаАктуальности <= ДАТАВРЕМЯ(%s) "
                "И (Д.КонецПериодаАктуальности = ДАТАВРЕМЯ(1, 1, 1) "
                "ИЛИ Д.КонецПериодаАктуальности > ДАТАВРЕМЯ(%s))" % (f["code"], date_lit, date_lit))
            sel.Next()
            n_actual = int(sel.Cnt)

            sel = q_sel(
                "ВЫБРАТЬ Т.Культура КАК Culture, Т.ГодУрожая КАК God, "
                "Т.НачалоПериодаАктуальности КАК PerBeg, Т.ЭтоРодитель КАК IsParent "
                "ИЗ Справочник.АпкПоля.ИсторияПоля КАК Т "
                "ГДЕ Т.Ссылка.Код = \"%s\" "
                "УПОРЯДОЧИТЬ ПО Т.НачалоПериодаАктуальности" % f["code"])
            hist_rows = []
            while sel.Next():
                hist_rows.append({
                    "culture": conn.String(sel.Culture),
                    "god": str(sel.God),
                    "beg": str(sel.PerBeg),
                    "is_parent": str(sel.IsParent),
                })
            print("FIELD code=%s: актуальных сегодня=%d, ИсторияПоля=%d" % (
                f["code"], n_actual, len(hist_rows)))
            culture = None
            for r in reversed(hist_rows):
                if r["culture"] and r["is_parent"] not in ("Да", "да", "Истина", "True"):
                    culture = r["culture"]
                    break
            if n_actual == 0 and culture:
                picked = {
                    "field_code": f["code"], "field_name": f["name"],
                    "culture": culture, "actual_rows": n_actual,
                    "history_len": len(hist_rows),
                }
                break
        if picked is None:
            print("FAIL: не найдено поле НИВА без актуальной записи и с культурой")
            return 1
        out["picked"] = picked
        print("== PICKED: %s" % json.dumps(picked, ensure_ascii=False))

        # 3) документы изменения истории полей по выбранному полю (могут блокировать ПередЗаписью)
        # (реплика ЕстьДокументыИзмененияИсторииПолей: 11 ТЧ Документ.АпкИзменениеИсторииПолей)
        tch_fields = [
            ("ИзменениеКультуры", "Поле"),
            ("ИзменениеНазначенияКультуры", "Поле"),
            ("РазделениеНаУчасткиСРазнымиКультурами", "Поле"),
            ("ИзменениеПлощадиСева", "Поле"),
            ("ВыбытиеПоля", "Поле"),
            ("ВозвратПоля", "Поле"),
            ("РазделениеПоля", "ПолеИсточник"),
            ("ОбъединениеПолей", "Поле"),
            ("ОбъединениеПолей", "ПолеПриемник"),
            ("ИзменениеПлощадиПоля", "Поле"),
            ("ИзменениеСевооборота", "Поле"),
            ("УстановкаКультурыНаОчереднойГод", "Поле"),
        ]
        docs_parts = []
        for tch, tf in tch_fields:
            docs_parts.append(
                "ВЫБРАТЬ КОЛИЧЕСТВО(*) КАК Cnt "
                "ИЗ Документ.АпкИзменениеИсторииПолей.%s КАК Т "
                "ГДЕ Т.%s.Код = \"%s\" "
                "И НЕ Т.Ссылка.ПометкаУдаления "
                "И Т.Ссылка.Статус = ЗНАЧЕНИЕ(Перечисление.АпкСтатусыИзмененияИсторииПолей.НаСогласовании)"
                % (tch, tf, picked["field_code"].strip()))
        sel = q_sel(" ОБЪЕДИНИТЬ ВСЕ ".join(docs_parts))
        docs_cnt = 0
        while sel.Next():
            docs_cnt += int(sel.Cnt)
        out["docs_izm_hist"] = docs_cnt
        print("== Документ.АпкИзменениеИсторииПолей по полю: %s" % docs_cnt)

        # 4) ожидаемая презентация объекта затрат
        picked["expected_presentation"] = "%s, %s %d г." % (
            picked["field_code"], picked["culture"], today.year)
        picked["cur_year"] = today.year
        picked["cur_month_start"] = "01.%02d.%d" % (today.month, today.year)
        out["result"] = picked
        with io.open("tmp/t8/pick_field_result.json", "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print("== RESULT: %s" % json.dumps(picked, ensure_ascii=False))
        return 0
    finally:
        try:
            conn = None
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
