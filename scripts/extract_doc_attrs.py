# -*- coding: utf-8 -*-
"""extract_doc_attrs.py — реквизиты и табличные части документов АПК из XML-исходников.

Usage: python scripts/extract_doc_attrs.py <DocumentName> [...] > out.md
Source dir fixed: C:/MyProjects/APKModSrc/Documents (APK module XML dump).
Names passed as \\u-escaped ASCII to survive the tool transport.
"""
import sys, io, os
import xml.etree.ElementTree as ET

NS = {'m': 'http://v8.1c.ru/8.3/MDClasses'}
BASE = r'C:/MyProjects/APKModSrc/Documents'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def one_type(tel):
    parts = []
    if tel is None:
        return ''
    for ts in tel:
        v = (ts.text or '').strip()
        if v:
            v = v.split(':')[-1]
            if v.startswith('CatalogRef.'):
                v = 'Справочник.' + v.split('.', 1)[1]
            elif v.startswith('DocumentRef.'):
                v = 'Документ.' + v.split('.', 1)[1]
            parts.append(v)
    return ', '.join(parts)

def dump(name):
    p = os.path.join(BASE, name + '.xml')
    if not os.path.exists(p):
        print('MISSING: ' + name.encode('unicode_escape').decode())
        return
    obj = ET.parse(p).getroot().find('m:Document', NS)
    print('## ' + name)
    print()
    co = obj.find('m:ChildObjects', NS)
    if co is None:
        print('(нет ChildObjects)')
        return
    attrs, tabs = [], []
    for c in co:
        tag = c.tag.split('}')[1]
        if tag == 'Attribute':
            nm = c.findtext('m:Properties/m:Name', namespaces=NS)
            tp = one_type(c.find('m:Properties/m:Type', NS))
            attrs.append((nm, tp))
        elif tag == 'TabularSection':
            nm = c.findtext('m:Properties/m:Name', namespaces=NS)
            cols = []
            for cc in c.findall('m:ChildObjects/m:Attribute', NS):
                cn = cc.findtext('m:Properties/m:Name', namespaces=NS)
                ct = one_type(cc.find('m:Properties/m:Type', NS))
                cols.append((cn, ct))
            tabs.append((nm, cols))
    if attrs:
        print('| Реквизит | Тип |')
        print('|---|---|')
        for nm, tp in attrs:
            print('| %s | %s |' % (nm, tp))
        print()
    for nm, cols in tabs:
        print('Табличная часть **%s**' % nm)
        print()
        if cols:
            print('| Колонка | Тип |')
            print('|---|---|')
            for cn, ct in cols:
                print('| %s | %s |' % (cn, ct))
            print()

if __name__ == '__main__':
    import codecs
    for a in sys.argv[1:]:
        if '\\u' in a:
            a = codecs.decode(a, 'unicode_escape')
        dump(a)
