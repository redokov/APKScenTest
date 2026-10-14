# -*- coding: utf-8 -*-
"""tmp_enum_values.py — значения перечислений АПК из XML-исходников (для design-разведки).

Usage: python scripts/tmp_enum_values.py <EnumName> [...] > out.md
Names passed as \\u-escaped ASCII to survive the tool transport.
"""
import sys, io, os, codecs
import xml.etree.ElementTree as ET

NS = {'m': 'http://v8.1c.ru/8.3/MDClasses'}
BASE = r'C:/MyProjects/APKModSrc/Enums'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def ru_synonym(el):
    if el is None:
        return ''
    for child in el:
        tag = child.tag.split('}')[-1]
        if tag == 'value':
            return (child.text or '').strip()
    return (el.text or '').strip()

def dump(name):
    p = os.path.join(BASE, name + '.xml')
    if not os.path.exists(p):
        print('MISSING: ' + name.encode('unicode_escape').decode())
        return
    root = ET.parse(p).getroot()
    enum_el = root.find('m:Enum', NS)
    print('## ' + name)
    co = enum_el.find('m:ChildObjects', NS) if enum_el is not None else None
    if co is None:
        print('(нет значений)')
        return
    print('| Значение | Синоним |')
    print('|---|---|')
    for c in co:
        tag = c.tag.split('}')[-1]
        if tag == 'EnumValue':
            nm = c.findtext('m:Properties/m:Name', namespaces=NS)
            syn = ru_synonym(c.find('m:Properties/m:Synonym', NS))
            print('| %s | %s |' % (nm, syn))
    print()

if __name__ == '__main__':
    for a in sys.argv[1:]:
        if '\\u' in a:
            a = codecs.decode(a, 'unicode_escape')
        dump(a)
