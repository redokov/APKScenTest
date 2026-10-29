# -*- coding: utf-8 -*-
"""T6: button 'Сгенерировать фичи' in preprocessor form.
Form.xml (CRLF): button id 119/120 + Command id 4.
Module.bsl (LF+BOM): client handler + server wrappers.
Assert-anchors, newline/BOM preserving."""
import io

FORM = "src/АпкПодготовкаСценарныхТестов/Forms/Форма/Ext/Form.xml"
MOD = "src/АпкПодготовкаСценарныхТестов/Forms/Форма/Ext/Form/Module.bsl"

def read(path):
    with io.open(path, "rb") as f:
        raw = f.read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    return raw.decode("utf-8-sig" if bom else "utf-8"), bom

def write(path, text, bom):
    with io.open(path, "wb") as f:
        if bom:
            f.write(b"\xef\xbb\xbf")
        f.write(text.encode("utf-8"))

def patch(path, anchor, insert, before, marker, nl):
    text, bom = read(path)
    anchor = anchor.replace("\n", nl)
    insert = insert.replace("\n", nl)
    n = text.count(anchor)
    assert n == 1, "anchor not unique (%d): %r in %s" % (n, anchor[:50], path)
    new = text.replace(anchor, (insert + anchor) if before else (anchor + insert))
    assert marker in new and new.count(marker) == 1, "marker bad: %s" % marker
    write(path, new, bom)
    print("OK %s (+%d chars)" % (path.encode("ascii", "backslashreplace").decode(), len(new) - len(text)))

CR = "\r\n"

# --- 1. Form.xml: button between Сканировать and ЗапуститьПрогон ---
BTN = ("\t\t\t<Button name=\"СгенерироватьФичи\" id=\"119\">\n"
       "\t\t\t\t<Type>CommandBarButton</Type>\n"
       "\t\t\t\t<CommandName>Form.Command.СгенерироватьФичи</CommandName>\n"
       "\t\t\t\t<ExtendedTooltip name=\"СгенерироватьФичиРасширеннаяПодсказка\" id=\"120\"/>\n"
       "\t\t\t</Button>\n")
patch(FORM, "\t\t\t<Button name=\"ЗапуститьПрогон\" id=\"90\">\n",
      BTN, before=True, marker="<Button name=\"СгенерироватьФичи\"", nl=CR)

# --- 2. Form.xml: command definition ---
CMD = ("\t\t<Command name=\"СгенерироватьФичи\" id=\"4\">\n"
       "\t\t\t<Title>\n\t\t\t\t<v8:item>\n\t\t\t\t\t<v8:lang>ru</v8:lang>\n"
       "\t\t\t\t\t<v8:content>Сгенерировать фичи</v8:content>\n"
       "\t\t\t\t</v8:item>\n\t\t\t</Title>\n"
       "\t\t\t<ToolTip>\n\t\t\t\t<v8:item>\n\t\t\t\t\t<v8:lang>ru</v8:lang>\n"
       "\t\t\t\t\t<v8:content>fixtures.json по scan.json, затем .feature по шаблонам с патчами (features-manifest.json)</v8:content>\n"
       "\t\t\t\t</v8:item>\n\t\t\t</ToolTip>\n"
       "\t\t\t<Action>СгенерироватьФичи</Action>\n"
       "\t\t</Command>\n")
patch(FORM, "\t</Commands>\n</Form>\n", CMD, before=True,
      marker="<Command name=\"СгенерироватьФичи\"", nl=CR)

# --- 3. Module.bsl: client handler after СканироватьДокументы ---
HANDLER = "\n".join([
"&НаКлиенте",
"Процедура СгенерироватьФичи(Команда)",
"",
"\tЕсли ПустаяСтрока(СокрЛП(КаталогПрогона)) Тогда",
"\t\tПоказатьПредупреждение(,",
"\t\t\tНСтр(\"ru = 'Укажите каталог прогона (сначала выполните сканирование)'\"));",
"\t\tВозврат;",
"\tКонецЕсли;",
"",
"\tПопытка",
"\t\tИтогФикстур = Сервер_СформироватьФикстуры(СокрЛП(КаталогПрогона));",
"\t\tИтогФич = Сервер_СгенерироватьФичи(СокрЛП(КаталогПрогона));",
"\tИсключение",
"\t\tПредупреждения = НСтр(\"ru = 'Генерация фич не выполнена:'\") + Символы.ПС",
"\t\t\t+ ПодробноеПредставлениеОшибки(ИнформацияОбОшибке());",
"\t\tВозврат;",
"\tКонецПопытки;",
"",
"\tИтогСканирования = ИтогФикстур + Символы.ПС + ИтогФич;",
"",
"КонецПроцедуры",
"",
])
A_SCAN = ("&НаКлиенте\nПроцедура СканироватьДокументы(Команда)\n"
          "\tСканироватьНаСервере();\nКонецПроцедуры\n")
patch(MOD, A_SCAN, HANDLER, before=False,
      marker="Процедура СгенерироватьФичи(Команда)", nl="\n")

# --- 4. Module.bsl: server wrappers region before ПрогонVAСервер ---
SRV = "\n".join([
"#Область ГенерацияФич",
"",
"&НаСервере",
"Функция Сервер_СформироватьФикстуры(КаталогПрогона)",
"",
"\tОбработка = РеквизитФормыВЗначение(\"Объект\");",
"\tВозврат Обработка.СформироватьФикстуры(КаталогПрогона);",
"",
"КонецФункции",
"",
"&НаСервере",
"Функция Сервер_СгенерироватьФичи(КаталогПрогона)",
"",
"\tОбработка = РеквизитФормыВЗначение(\"Объект\");",
"\tВозврат Обработка.СгенерироватьФичи(КаталогПрогона);",
"",
"КонецФункции",
"",
"#КонецОбласти",
"",
])
patch(MOD, "#Область ПрогонVAСервер\n", SRV, before=True,
      marker="Функция Сервер_СгенерироватьФичи", nl="\n")
print("T6 patch done")
