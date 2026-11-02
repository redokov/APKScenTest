# -*- coding: utf-8 -*-
"""S010 T3: COM-проверка контур-фильтра препроцессора (dist EPF).

Ревизия s009: превью-таблица раннера показывает ВСЕ строки манифеста
с колонкой Включён (ПланПрогона не фильтрует строки, только считает
флаг ТестМанифестаВключен). Фильтрация происходит в батч-генерации
(ГруппыФайловМанифеста <- ПодготовитьПрогон). Проверяем через COM:
1) ПланПрогона без фильтра: 32 строки, все Включён=Истина;
2) ПланПрогона с фильтром Контуры{КРС=Ложь}: 32 строки, но
   Включён=Ложь ровно у КРС-шаблонов (ожидаем 11 -> включено 21);
3) то же с Отключены (точечное отключение) для контроля ключа.
Никаких записей в базу, ПланПрогона не пишет файлы."""
import sys
import io
import os

sys.path.insert(0, 'scripts')
import win32com.client
import t8_gate as t

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
os.makedirs('tmp/s010', exist_ok=True)
out = io.open('tmp/s010/com_filter_probe.txt', 'w', encoding='utf-8')
RUN_DIR = 'C:/MyProjects/APKScenTest/tests/run-20261102-034905'
EPF = 'C:/MyProjects/APKScenTest/dist/АпкПодготовкаСценарныхТестов.epf'

conn = win32com.client.Dispatch("V85.COMConnector").Connect(t.conn_str(t.ADMIN, ""))
vp = getattr(conn, 'ВнешниеОбработки')
obj = vp.Создать(EPF, False)

def plan(filter_ref):
    if filter_ref is None:
        return obj.ПланПрогона(RUN_DIR)
    return obj.ПланПрогона(RUN_DIR, filter_ref)

# --- 1: без фильтра
rows = plan(None)
total = 0
enabled = 0
excluded_no_filter = []
for r in rows:
    total += 1
    if r.Включён:
        enabled += 1
    else:
        excluded_no_filter.append(r.Шаблон)
out.write('без фильтра: всего=%d включено=%d исключено=%s\n' % (total, enabled, excluded_no_filter))

# --- 2: фильтр Контуры{КРС=Ложь}
contours = conn.NewObject('Структура')
contures_ins = contours  # alias
contures_ins.Вставить('Растениеводство', True)
contures_ins.Вставить('Свиноводство', True)
contures_ins.Вставить('КРС', False)
flt = conn.NewObject('Структура')
flt.Вставить('Контуры', contours)
flt.Вставить('Отключены', conn.NewObject('Массив'))
rows = plan(flt)
total = 0
enabled = 0
excluded = []
by_contour = {}
for r in rows:
    total += 1
    c = str(r.Контур)
    by_contour.setdefault(c, [0, 0])
    by_contour[c][0] += 1
    if r.Включён:
        enabled += 1
        by_contour[c][1] += 1
    else:
        excluded.append('%s/%s' % (r.Контур, r.Шаблон))
out.write('фильтр КРС=Ложь: всего=%d включено=%d\n' % (total, enabled))
for c in sorted(by_contour):
    out.write('  контур %-16s всего=%d включено=%d\n' % (c, by_contour[c][0], by_contour[c][1]))
out.write('исключённые шаблоны: %s\n' % ', '.join(excluded))

# --- 3: точечное отключение: один КРС-шаблон в Отключены
arr = conn.NewObject('Массив')
key = str(excluded[0].split('/')[1]) + '--' + ''  # user пустой в ключе не нужен
# ключ: Шаблон + "--" + Пользователь; пользователя берём из первой исключённой записи нельзя - возьмём из плана
rows = plan(None)
first_user = None
first_tmpl = None
for r in rows:
    first_user = str(r.Пользователь)
    first_tmpl = str(r.Шаблон)
    break
arr.Добавить(first_tmpl + '--' + first_user)
flt2 = conn.NewObject('Структура')
flt2.Вставить('Контуры', contours)
flt2.Вставить('Отключены', arr)
rows = plan(flt2)
total = 0
enabled2 = 0
excluded2 = []
for r in rows:
    total += 1
    if r.Включён:
        enabled2 += 1
    else:
        excluded2.append('%s/%s/%s' % (r.Контур, r.Шаблон, r.Пользователь))
out.write('фильтр КРС=Ложь + точечно %s--%s: всего=%d включено=%d\n' % (first_tmpl, first_user, total, enabled2))
out.write('исключённые: %s\n' % ', '.join(excluded2))

out.close()
print(io.open('tmp/s010/com_filter_probe.txt', encoding='utf-8').read())
