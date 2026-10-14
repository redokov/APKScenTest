# -*- coding: utf-8 -*-
"""T7: добавить в Form.xml кнопку «Сформировать отчёт» (D-011), поле
ИтогОтчета и ТЧ ОтчетСценарии (+атрибуты +команда). Idempotent.
Файл: UTF-8 noBOM, CRLF (как был).
"""
import sys

PATH = r"c:\MyProjects\APKScenTest\src\АпкПодготовкаСценарныхТестов\Forms\Форма\Ext\Form.xml"

BUTTON = (
    '\t\t\t<Button name="СформироватьОтчет" id="92">\r\n'
    '\t\t\t\t<Type>CommandBarButton</Type>\r\n'
    '\t\t\t\t<CommandName>Form.Command.СформироватьОтчет</CommandName>\r\n'
    '\t\t\t\t<ExtendedTooltip name="СформироватьОтчетРасширеннаяПодсказка" id="93"/>\r\n'
    '\t\t\t</Button>\r\n'
)

ITEMS = (
    '\t\t<InputField name="ИтогОтчета" id="94">\r\n'
    '\t\t\t<DataPath>ИтогОтчета</DataPath>\r\n'
    '\t\t\t<ReadOnly>true</ReadOnly>\r\n'
    '\t\t\t<MultiLine>true</MultiLine>\r\n'
    '\t\t\t<Height>2</Height>\r\n'
    '\t\t\t<ContextMenu name="ИтогОтчетаКонтекстноеМеню" id="95"/>\r\n'
    '\t\t\t<ExtendedTooltip name="ИтогОтчетаРасширеннаяПодсказка" id="96"/>\r\n'
    '\t\t</InputField>\r\n'
    '\t\t<Table name="ОтчетСценарии" id="97">\r\n'
    '\t\t\t<Representation>List</Representation>\r\n'
    '\t\t\t<CommandBarLocation>None</CommandBarLocation>\r\n'
    '\t\t\t<ReadOnly>true</ReadOnly>\r\n'
    '\t\t\t<SkipOnInput>false</SkipOnInput>\r\n'
    '\t\t\t<AutoInsertNewRow>true</AutoInsertNewRow>\r\n'
    '\t\t\t<EnableStartDrag>true</EnableStartDrag>\r\n'
    '\t\t\t<EnableDrag>true</EnableDrag>\r\n'
    '\t\t\t<FileDragMode>AsFile</FileDragMode>\r\n'
    '\t\t\t<DataPath>ОтчетСценарии</DataPath>\r\n'
    '\t\t\t<SearchStringLocation>None</SearchStringLocation>\r\n'
    '\t\t\t<ViewStatusLocation>None</ViewStatusLocation>\r\n'
    '\t\t\t<SearchControlLocation>None</SearchControlLocation>\r\n'
    '\t\t\t<RowFilter xsi:nil="true"/>\r\n'
    '\t\t\t<ContextMenu name="ОтчетСценарииКонтекстноеМеню" id="98"/>\r\n'
    '\t\t\t<AutoCommandBar name="ОтчетСценарииКоманднаяПанель" id="99"/>\r\n'
    '\t\t\t<ExtendedTooltip name="ОтчетСценарииРасширеннаяПодсказка" id="100"/>\r\n'
    '\t\t\t<ChildItems>\r\n'
    '\t\t\t\t<InputField name="ОтчетСценарииСценарий" id="101">\r\n'
    '\t\t\t\t\t<DataPath>ОтчетСценарии.Сценарий</DataPath>\r\n'
    '\t\t\t\t\t<EditMode>EnterOnInput</EditMode>\r\n'
    '\t\t\t\t\t<ContextMenu name="ОтчетСценарииСценарийКонтекстноеМеню" id="102"/>\r\n'
    '\t\t\t\t\t<ExtendedTooltip name="ОтчетСценарииСценарийРасширеннаяПодсказка" id="103"/>\r\n'
    '\t\t\t\t</InputField>\r\n'
    '\t\t\t\t<InputField name="ОтчетСценарииПользователь" id="104">\r\n'
    '\t\t\t\t\t<DataPath>ОтчетСценарии.Пользователь</DataPath>\r\n'
    '\t\t\t\t\t<EditMode>EnterOnInput</EditMode>\r\n'
    '\t\t\t\t\t<ContextMenu name="ОтчетСценарииПользовательКонтекстноеМеню" id="105"/>\r\n'
    '\t\t\t\t\t<ExtendedTooltip name="ОтчетСценарииПользовательРасширеннаяПодсказка" id="106"/>\r\n'
    '\t\t\t\t</InputField>\r\n'
    '\t\t\t\t<InputField name="ОтчетСценарииСтатус" id="107">\r\n'
    '\t\t\t\t\t<DataPath>ОтчетСценарии.Статус</DataPath>\r\n'
    '\t\t\t\t\t<EditMode>EnterOnInput</EditMode>\r\n'
    '\t\t\t\t\t<ContextMenu name="ОтчетСценарииСтатусКонтекстноеМеню" id="108"/>\r\n'
    '\t\t\t\t\t<ExtendedTooltip name="ОтчетСценарииСтатусРасширеннаяПодсказка" id="109"/>\r\n'
    '\t\t\t\t</InputField>\r\n'
    '\t\t\t\t<InputField name="ОтчетСценарииДлительностьМс" id="110">\r\n'
    '\t\t\t\t\t<DataPath>ОтчетСценарии.ДлительностьМс</DataPath>\r\n'
    '\t\t\t\t\t<EditMode>EnterOnInput</EditMode>\r\n'
    '\t\t\t\t\t<ContextMenu name="ОтчетСценарииДлительностьМсКонтекстноеМеню" id="111"/>\r\n'
    '\t\t\t\t\t<ExtendedTooltip name="ОтчетСценарииДлительностьМсРасширеннаяПодсказка" id="112"/>\r\n'
    '\t\t\t\t</InputField>\r\n'
    '\t\t\t\t<InputField name="ОтчетСценарииСтатусБатча" id="113">\r\n'
    '\t\t\t\t\t<DataPath>ОтчетСценарии.СтатусБатча</DataPath>\r\n'
    '\t\t\t\t\t<EditMode>EnterOnInput</EditMode>\r\n'
    '\t\t\t\t\t<ContextMenu name="ОтчетСценарииСтатусБатчаКонтекстноеМеню" id="114"/>\r\n'
    '\t\t\t\t\t<ExtendedTooltip name="ОтчетСценарииСтатусБатчаРасширеннаяПодсказка" id="115"/>\r\n'
    '\t\t\t\t</InputField>\r\n'
    '\t\t\t\t<InputField name="ОтчетСценарииКодВозврата" id="116">\r\n'
    '\t\t\t\t\t<DataPath>ОтчетСценарии.КодВозврата</DataPath>\r\n'
    '\t\t\t\t\t<EditMode>EnterOnInput</EditMode>\r\n'
    '\t\t\t\t\t<ContextMenu name="ОтчетСценарииКодВозвратаКонтекстноеМеню" id="117"/>\r\n'
    '\t\t\t\t\t<ExtendedTooltip name="ОтчетСценарииКодВозвратаРасширеннаяПодсказка" id="118"/>\r\n'
    '\t\t\t\t</InputField>\r\n'
    '\t\t\t</ChildItems>\r\n'
    '\t\t</Table>\r\n'
)


def column(name, title, ident):
    return (
        '\t\t\t\t<Column name="%s" id="%d">\r\n'
        '\t\t\t\t\t<Title>\r\n'
        '\t\t\t\t\t\t<v8:item>\r\n'
        '\t\t\t\t\t\t\t<v8:lang>ru</v8:lang>\r\n'
        '\t\t\t\t\t\t\t<v8:content>%s</v8:content>\r\n'
        '\t\t\t\t\t\t</v8:item>\r\n'
        '\t\t\t\t\t</Title>\r\n'
        '\t\t\t\t\t<Type>\r\n'
        '\t\t\t\t\t\t<v8:Type>%s</v8:Type>\r\n'
        '\t\t\t\t\t</Type>\r\n'
        '\t\t\t\t</Column>\r\n' % (name, ident, title, "xs:string")
    )


ATTRS = (
    '\t\t<Attribute name="ИтогОтчета" id="11">\r\n'
    '\t\t\t<Title>\r\n'
    '\t\t\t\t<v8:item>\r\n'
    '\t\t\t\t\t<v8:lang>ru</v8:lang>\r\n'
    '\t\t\t\t\t<v8:content>Итог отчёта</v8:content>\r\n'
    '\t\t\t\t</v8:item>\r\n'
    '\t\t\t</Title>\r\n'
    '\t\t\t<Type>\r\n'
    '\t\t\t\t<v8:Type>xs:string</v8:Type>\r\n'
    '\t\t\t\t<v8:StringQualifiers>\r\n'
    '\t\t\t\t\t<v8:Length>0</v8:Length>\r\n'
    '\t\t\t\t\t<v8:AllowedLength>Variable</v8:AllowedLength>\r\n'
    '\t\t\t\t</v8:StringQualifiers>\r\n'
    '\t\t\t</Type>\r\n'
    '\t\t</Attribute>\r\n'
    '\t\t<Attribute name="ОтчетСценарии" id="12">\r\n'
    '\t\t\t<Title>\r\n'
    '\t\t\t\t<v8:item>\r\n'
    '\t\t\t\t\t<v8:lang>ru</v8:lang>\r\n'
    '\t\t\t\t\t<v8:content>Сценарии отчёта</v8:content>\r\n'
    '\t\t\t\t</v8:item>\r\n'
    '\t\t\t</Title>\r\n'
    '\t\t\t<Type>\r\n'
    '\t\t\t\t<v8:Type>v8:ValueTable</v8:Type>\r\n'
    '\t\t\t</Type>\r\n'
    '\t\t\t<Columns>\r\n'
    + column("Сценарий", "Сценарий", 1)
    + column("Пользователь", "Пользователь", 2)
    + column("Статус", "Статус", 3)
    + '\t\t\t\t<Column name="ДлительностьМс" id="4">\r\n'
    '\t\t\t\t\t<Title>\r\n'
    '\t\t\t\t\t\t<v8:item>\r\n'
    '\t\t\t\t\t\t\t<v8:lang>ru</v8:lang>\r\n'
    '\t\t\t\t\t\t\t<v8:content>Длительность, мс</v8:content>\r\n'
    '\t\t\t\t\t\t</v8:item>\r\n'
    '\t\t\t\t\t</Title>\r\n'
    '\t\t\t\t\t<Type>\r\n'
    '\t\t\t\t\t\t<v8:Type>xs:decimal</v8:Type>\r\n'
    '\t\t\t\t\t\t<v8:NumberQualifiers>\r\n'
    '\t\t\t\t\t\t\t<v8:Digits>15</v8:Digits>\r\n'
    '\t\t\t\t\t\t\t<v8:FractionDigits>0</v8:FractionDigits>\r\n'
    '\t\t\t\t\t\t\t<v8:AllowedSign>Any</v8:AllowedSign>\r\n'
    '\t\t\t\t\t\t</v8:NumberQualifiers>\r\n'
    '\t\t\t\t\t</Type>\r\n'
    '\t\t\t\t</Column>\r\n'
    + column("СтатусБатча", "Статус батча", 5)
    + column("КодВозврата", "Код возврата", 6)
    + '\t\t\t</Columns>\r\n'
    '\t\t</Attribute>\r\n'
)

COMMAND = (
    '\t\t<Command name="СформироватьОтчет" id="3">\r\n'
    '\t\t\t<Title>\r\n'
    '\t\t\t\t<v8:item>\r\n'
    '\t\t\t\t\t<v8:lang>ru</v8:lang>\r\n'
    '\t\t\t\t\t<v8:content>Сформировать отчёт</v8:content>\r\n'
    '\t\t\t\t</v8:item>\r\n'
    '\t\t\t</Title>\r\n'
    '\t\t\t<ToolTip>\r\n'
    '\t\t\t\t<v8:item>\r\n'
    '\t\t\t\t\t<v8:lang>ru</v8:lang>\r\n'
    '\t\t\t\t\t<v8:content>Сводка прогона: batches.json + allure + fixtures -> summary.json и summary.md</v8:content>\r\n'
    '\t\t\t\t</v8:item>\r\n'
    '\t\t\t</ToolTip>\r\n'
    '\t\t\t<Action>СформироватьОтчет</Action>\r\n'
    '\t\t</Command>\r\n'
)


def main():
    with open(PATH, encoding="utf-8", newline="") as f:
        text = f.read()
    if 'Command name="СформироватьОтчет"' in text:
        print("[SKIP] already patched")
        return

    # 1. кнопка в командную панель после кнопки ЗапуститьПрогон
    btn_anchor = '\t\t\t\t<ExtendedTooltip name="ЗапуститьПрогонРасширеннаяПодсказка" id="91"/>\r\n\t\t\t</Button>\r\n'
    assert text.count(btn_anchor) == 1
    text = text.replace(btn_anchor, btn_anchor + BUTTON)

    # 2. элементы после поля ИтогПрогона (конец ChildItems верхнего уровня)
    item_anchor = '\t\t\t<ExtendedTooltip name="ИтогПрогонаРасширеннаяПодсказка" id="86"/>\r\n\t\t</InputField>\r\n\t</ChildItems>\r\n'
    assert text.count(item_anchor) == 1
    text = text.replace(item_anchor,
                        '\t\t\t<ExtendedTooltip name="ИтогПрогонаРасширеннаяПодсказка" id="86"/>\r\n\t\t</InputField>\r\n'
                        + ITEMS + '\t</ChildItems>\r\n')

    # 3. атрибуты перед </Attributes>
    attr_anchor = '\t</Attributes>\r\n'
    assert text.count(attr_anchor) == 1
    text = text.replace(attr_anchor, ATTRS + attr_anchor)

    # 4. команда перед </Commands>
    cmd_anchor = '\t</Commands>\r\n'
    assert text.count(cmd_anchor) == 1
    text = text.replace(cmd_anchor, COMMAND + cmd_anchor)

    with open(PATH, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    print("[OK] Form.xml patched, lines:", text.count("\r\n"))


if __name__ == "__main__":
    sys.exit(main())
