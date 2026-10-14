# -*- coding: utf-8 -*-
"""T6: add run-attributes/fields/button/command to Form.xml (Cyrillic-safe)."""
import io

P = r"c:\MyProjects\APKScenTest\src\АпкПодготовкаСценарныхТестов\Forms\Форма\Ext\Form.xml"

t = io.open(P, encoding="utf-8").read()

# 1. Fields after the last </Table>
old_tail = "<TABTABTABTAB></InputField>\n<TABTABTAB></ChildItems>\n<TABTAB></Table>\n<TAB></ChildItems>\n<TAB><Attributes>"
new_tail = (
    "<TABTABTABTAB></InputField>\n<TABTAB></ChildItems>\n<TABTAB></Table>\n"
    "<TABTAB><InputField name=\"КаталогПрогона\" id=\"81\">\n"
    "<TABTABTAB><DataPath>КаталогПрогона</DataPath>\n"
    "<TABTABTAB><ContextMenu name=\"КаталогПрогонаКонтекстноеМеню\" id=\"82\"/>\n"
    "<TABTABTAB><ExtendedTooltip name=\"КаталогПрогонаРасширеннаяПодсказка\" id=\"83\"/>\n"
    "<TABTAB></InputField>\n"
    "<TABTAB><InputField name=\"ИтогПрогона\" id=\"84\">\n"
    "<TABTABTAB><DataPath>ИтогПрогона</DataPath>\n"
    "<TABTABTAB><ReadOnly>true</ReadOnly>\n"
    "<TABTABTAB><MultiLine>true</MultiLine>\n"
    "<TABTABTAB><Height>3</Height>\n"
    "<TABTABTAB><ContextMenu name=\"ИтогПрогонаКонтекстноеМеню\" id=\"85\"/>\n"
    "<TABTABTAB><ExtendedTooltip name=\"ИтогПрогонаРасширеннаяПодсказка\" id=\"86\"/>\n"
    "<TABTAB></InputField>\n"
    "<TAB></ChildItems>\n<TAB><Attributes>"
)

def S(text):
    return text.replace("<TABTABTABTAB>", "\t\t\t\t").replace(
        "<TABTABTAB>", "\t\t\t").replace("<TABTAB>", "\t\t").replace("<TAB>", "\t")

old_tail = S(old_tail)
new_tail = S(new_tail)

assert t.count(old_tail) == 1, "tail not found: %d" % t.count(old_tail)
t = t.replace(old_tail, new_tail)

# 2. Button in command bar
old_btn = S(
    "<TABTABTABTAB><ExtendedTooltip name=\"СканироватьДокументыРасширеннаяПодсказка\" id=\"2\"/>\n"
    "<TABTABTAB></Button>"
)
new_btn = S(
    "<TABTABTABTAB><ExtendedTooltip name=\"СканироватьДокументыРасширеннаяПодсказка\" id=\"2\"/>\n"
    "<TABTABTAB></Button>\n"
    "<TABTABTAB><Button name=\"ЗапуститьПрогон\" id=\"90\">\n"
    "<TABTABTABTAB><Type>CommandBarButton</Type>\n"
    "<TABTABTABTAB><CommandName>Form.Command.ЗапуститьПрогон</CommandName>\n"
    "<TABTABTABTAB><ExtendedTooltip name=\"ЗапуститьПрогонРасширеннаяПодсказка\" id=\"91\"/>\n"
    "<TABTABTAB></Button>"
)
assert t.count(old_btn) == 1, "button anchor not found"
t = t.replace(old_btn, new_btn)

# 3. Command definition
old_cmd = S(
    "<TABTABTAB><Action>СканироватьДокументы</Action>\n<TABTAB></Command>\n<TAB></Commands>"
)
new_cmd = S(
    "<TABTABTAB><Action>СканироватьДокументы</Action>\n<TABTAB></Command>\n"
    "<TABTAB><Command name=\"ЗапуститьПрогон\" id=\"2\">\n"
    "<TABTABTAB><Title>\n<TABTABTABTAB><v8:item>\n<TABTABTABTABTAB><v8:lang>ru</v8:lang>\n"
    "<TABTABTABTABTAB><v8:content>Запустить прогон (подменяет пароли)</v8:content>\n"
    "<TABTABTABTAB></v8:item>\n<TABTABTAB></Title>\n"
    "<TABTABTAB><ToolTip>\n<TABTABTABTAB><v8:item>\n<TABTABTABTABTAB><v8:lang>ru</v8:lang>\n"
    "<TABTABTABTABTAB><v8:content>Цикл батчей VA: подмена пароля, батч, восстановление. "
    "Вердикт — только ReturnStatus-файл</v8:content>\n<TABTABTABTAB></v8:item>\n<TABTABTAB></ToolTip>\n"
    "<TABTABTAB><Action>ЗапуститьПрогон</Action>\n<TABTAB></Command>\n<TAB></Commands>"
)
assert t.count(old_cmd) == 1, "cmd anchor not found"
t = t.replace(old_cmd, new_cmd)

# 4. Attributes
old_attr = S("<TAB></Attributes>\n<TAB><Commands>")
new_attr = S(
    "<TABTAB><Attribute name=\"КаталогПрогона\" id=\"9\">\n"
    "<TABTABTAB><Title>\n<TABTABTABTAB><v8:item>\n<TABTABTABTABTAB><v8:lang>ru</v8:lang>\n"
    "<TABTABTABTABTAB><v8:content>Каталог прогона (fixtures.json + features/)</v8:content>\n"
    "<TABTABTABTAB></v8:item>\n<TABTABTAB></Title>\n"
    "<TABTABTAB><Type>\n<TABTABTABTAB><v8:Type>xs:string</v8:Type>\n"
    "<TABTABTABTAB><v8:StringQualifiers>\n<TABTABTABTABTAB><v8:Length>0</v8:Length>\n"
    "<TABTABTABTABTAB><v8:AllowedLength>Variable</v8:AllowedLength>\n"
    "<TABTABTABTAB></v8:StringQualifiers>\n<TABTABTAB></Type>\n<TABTAB></Attribute>\n"
    "<TABTAB><Attribute name=\"ИтогПрогона\" id=\"10\">\n"
    "<TABTABTAB><Title>\n<TABTABTABTAB><v8:item>\n<TABTABTABTABTAB><v8:lang>ru</v8:lang>\n"
    "<TABTABTABTABTAB><v8:content>Итог прогона</v8:content>\n"
    "<TABTABTABTAB></v8:item>\n<TABTABTAB></Title>\n"
    "<TABTABTAB><Type>\n<TABTABTABTAB><v8:Type>xs:string</v8:Type>\n"
    "<TABTABTABTAB><v8:StringQualifiers>\n<TABTABTABTABTAB><v8:Length>0</v8:Length>\n"
    "<TABTABTABTABTAB><v8:AllowedLength>Variable</v8:AllowedLength>\n"
    "<TABTABTABTAB></v8:StringQualifiers>\n<TABTABTAB></Type>\n<TABTAB></Attribute>\n"
    "<TAB></Attributes>\n<TAB><Commands>"
)
assert t.count(old_attr) == 1, "attr anchor not found"
t = t.replace(old_attr, new_attr)

io.open(P, "w", encoding="utf-8").write(t)
print("OK: Form.xml updated")
