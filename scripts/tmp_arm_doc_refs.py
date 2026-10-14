# -*- coding: utf-8 -*-
"""tmp_arm_doc_refs.py — ссылки на целевые документы в модулях АРМов АПК.

Для каждой обработки DataProcessors/АпкАРМПоОтражению* ищет упоминания имён
5 целевых документов в .bsl/.txt файлах объекта и его форм.
Вывод: АРМ | документ | число вхождений | примеры строк.
"""
import io, sys, os
import xml.etree.ElementTree as ET

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = r'C:/MyProjects/APKModSrc/DataProcessors'

DOCS = [
    'АпкПутевойЛистТракториста',
    'АпкПутевойЛистАвтотранспорта',
    'АпкНарядНаСдельнуюРаботу',
    'АпкЗаправочныеВедомости',
    'АпкРегистрацияВзвешиванийНаТоку',
]

def find_refs(arm_dir):
    """Возвращает {doc: [(file, line), ...]}"""
    refs = {d: [] for d in DOCS}
    for root, dirs, files in os.walk(arm_dir):
        for fn in files:
            if not (fn.endswith('.bsl') or fn.endswith('.txt')):
                continue
            fp = os.path.join(root, fn)
            try:
                with open(fp, encoding='utf-8') as f:
                    for i, line in enumerate(f, 1):
                        for d in DOCS:
                            if d in line:
                                s = line.strip()
                                if len(s) > 120:
                                    s = s[:120] + '...'
                                refs[d].append((os.path.relpath(fp, arm_dir), i, s))
                                break
            except (UnicodeDecodeError, OSError):
                pass
    return refs

def main():
    arms = sorted(n for n in os.listdir(BASE)
                  if n.startswith('АпкАРМПоОтражению') and os.path.isdir(os.path.join(BASE, n)))
    print('АРМов отражения: %d' % len(arms))
    print()
    any_found = False
    for arm in arms:
        refs = find_refs(os.path.join(BASE, arm))
        hits = {d: v for d, v in refs.items() if v}
        if not hits:
            continue
        any_found = True
        print('## %s' % arm)
        for d, v in hits.items():
            print('** %s — %d вхожд.' % (d, len(v)))
            for fp, i, s in v[:3]:
                print('   %s:%d: %s' % (fp, i, s))
            if len(v) > 3:
                print('   ... ещё %d' % (len(v) - 3))
        print()
    if not any_found:
        print('(прямых ссылок на целевые документы не найдено)')

if __name__ == '__main__':
    main()
