# -*- coding: utf-8 -*-
"""s2_form_dump.py — дамп элементов Form.xml документов АПК (T2/T3/T4).

NS форм = http://v8.1c.ru/8.3/xcf/logform. Печатает дерево элементов
(имя, заголовок, dataPath, skipOnInput, видимость по умолчанию).
Usage: python scripts/s2_form_dump.py [имя-дока...] (по умолчанию три новых).
"""
import io
import sys
import xml.etree.ElementTree as ET

BASE = r"C:\MyProjects\APKModSrc\Documents"
NS = {"lf": "http://v8.1c.ru/8.3/xcf/logform"}

DOCS = {
    "02": "\u0410\u043f\u043a\u041f\u0443\u0442\u0435\u0432\u043e\u0439\u041b\u0438\u0441\u0442\u0410\u0432\u0442\u043e\u0442\u0440\u0430\u043d\u0441\u043f\u043e\u0440\u0442\u0430",
    "04": "\u0410\u043f\u043a\u0417\u0430\u043f\u0440\u0430\u0432\u043e\u0447\u043d\u044b\u0435\u0412\u0435\u0434\u043e\u043c\u043e\u0441\u0442\u0438",
    "05": "\u0410\u043f\u043a\u0420\u0435\u0433\u0438\u0441\u0442\u0440\u0430\u0446\u0438\u044f\u0412\u0437\u0432\u0435\u0448\u0438\u0432\u0430\u043d\u0438\u0439\u041d\u0430\u0422\u043e\u043a\u0443",
}


def text_of(el, tag):
    sub = el.find(f"lf:{tag}", NS)
    if sub is None:
        return ""
    return "".join(sub.itertext()).strip()


def dump(doc, out):
    path = f"{BASE}\\{doc}\\Forms\\\u0424\u043e\u0440\u043c\u0430\u0414\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430\\Ext\\Form.xml"
    root = ET.parse(path).getroot()
    out.write("=" * 70 + "\n")
    out.write("DOC: " + doc + "\n")

    def walk(parent, depth):
        for child in parent:
            tag = child.tag.split("}")[-1]
            if tag in ("Items", "ChildItems", "AutoCommandBar"):
                walk(child, depth)
                continue
            name = child.get("name", "")
            if not name:
                continue
            title = text_of(child, "Title")
            dp = child.get("dataPath", "")
            skip = child.get("skipOnInput", "")
            vis = child.get("visible", "")
            info = f"{tag} [{name}]"
            if title:
                info += f" title={title!r}"
            if dp:
                info += f" dp={dp}"
            if skip == "false":
                info += " skip=false"
            if vis == "false":
                info += " visible=false"
            out.write("  " * depth + info + "\n")
            if tag == "Table":
                # колонки таблицы
                cols = [c for c in child if c.tag.split("}")[-1] == "SearchControl"]
                for sub in child:
                    if sub.tag.split("}")[-1] == "ChildItems":
                        walk(sub, depth + 1)
            else:
                for sub in child:
                    if sub.tag.split("}")[-1] == "ChildItems":
                        walk(sub, depth + 1)

    walk(root, 0)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    docs = sys.argv[1:] or list(DOCS.values())
    with io.open(r"C:\MyProjects\APKScenTest\tmp\s2\form-dump.txt", "w", encoding="utf-8") as out:
        for d in docs:
            dump(d, out)


if __name__ == "__main__":
    main()
