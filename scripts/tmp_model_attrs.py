# -*- coding: utf-8 -*-
"""tmp_model_attrs.py — реквизиты каталогов моделей ТС (для design-разведки)."""
import io, sys, os
import xml.etree.ElementTree as ET

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
NS = {'m': 'http://v8.1c.ru/8.3/MDClasses'}
BASE = r'C:/MyProjects/APKModSrc/Catalogs'

NAMES = [
    'АпкМоделиАвтотранспорта',
    'АпкМоделиСХТехники',
]

for nm in NAMES:
    p = os.path.join(BASE, nm + '.xml')
    if not os.path.exists(p):
        print('MISSING flat-form:', nm)
        continue
    obj = ET.parse(p).getroot().find('m:Catalog', NS)
    co = obj.find('m:ChildObjects', NS)
    print('##', nm)
    for c in co:
        if c.tag.split('}')[-1] == 'Attribute':
            a = c.findtext('m:Properties/m:Name', namespaces=NS)
            tp = c.find('m:Properties/m:Type', NS)
            types = ', '.join((t.text or '').strip().split(':')[-1] for t in tp) if tp is not None else ''
            print('| %s | %s |' % (a, types))
    print()
