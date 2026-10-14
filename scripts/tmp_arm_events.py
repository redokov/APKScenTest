# -*- coding: utf-8 -*-
"""tmp_arm_events.py — карта подписок АРМов отражения АПК.

Для каждой обработки DataProcessors/АпкАРМПоОтражению* собирает:
- все значения ИмяСобытия = "..." (события подписки);
- все токены Документ.<Имя> и Регистр*.<Имя> из текстов модулей (таблицы данных).
"""
import io, sys, os, re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = r'C:/MyProjects/APKModSrc/DataProcessors'

RE_EVENT = re.compile(r'ИмяСобытия\s*=\s*"([^"]+)"')
RE_TABLE = re.compile(r'(Документ|РегистрНакопления|РегистрСведений|РегистрБухгалтерии)\.([A-Za-zА-Яа-яЁё_0-9]+)')

def collect(arm_dir):
    events, tables = set(), set()
    for root, dirs, files in os.walk(arm_dir):
        for fn in files:
            if not (fn.endswith('.bsl') or fn.endswith('.txt')):
                continue
            fp = os.path.join(root, fn)
            try:
                text = open(fp, encoding='utf-8').read()
            except (UnicodeDecodeError, OSError):
                continue
            for m in RE_EVENT.finditer(text):
                events.add(m.group(1))
            for m in RE_TABLE.finditer(text):
                tables.add('%s.%s' % (m.group(1), m.group(2)))
    return sorted(events), sorted(tables)

def main():
    arms = sorted(n for n in os.listdir(BASE)
                  if n.startswith('АпкАРМПоОтражению') and os.path.isdir(os.path.join(BASE, n)))
    for arm in arms:
        events, tables = collect(os.path.join(BASE, arm))
        print('## %s' % arm)
        print('События: %s' % (', '.join(events) if events else '—'))
        apk_tables = [t for t in tables if '.Апк' in t or 'Заправк' in t or 'Путев' in t or 'Наряд' in t]
        if apk_tables:
            print('Отраслевые таблицы: %s' % ', '.join(apk_tables))
        print()

if __name__ == '__main__':
    main()
