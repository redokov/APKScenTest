# T6: fill empty Except blocks in Form/Module.bsl (MissingCodeTryCatchEx)
import glob
p = glob.glob('src/**/Form/Module.bsl', recursive=True)[0]
txt = open(p, 'rb').read().decode('utf-8')

r1_old = ('\u0418\u0441\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u0435\n\t\t'
          '// \u0432\u0435\u0440\u0434\u0438\u043a\u0442 \u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u0435\u043d - \u0441\u0442\u0430\u0442\u0443\u0441 \u043e\u0441\u0442\u0430\u0451\u0442\u0441\u044f \u043e\u0442 \u0437\u0430\u043f\u0443\u0441\u043a\u0430 (timeout/error)\n\u041a\u043e\u043d\u0435\u0446\u041f\u043e\u043f\u044b\u0442\u043a\u0438;')
r1_new = ('\u0418\u0441\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u0435\n\t\t'
          '// \u0432\u0435\u0440\u0434\u0438\u043a\u0432\u0442 \u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u0435\u043d - \u0441\u0442\u0430\u0442\u0443\u0441 \u043e\u0441\u0442\u0430\u0451\u0442\u0441\u044f \u043e\u0442 \u0437\u0430\u043f\u0443\u0441\u043a\u0430 (timeout/error)\n\u041a\u043e\u043d\u0435\u0446\u041f\u043e\u043f\u044b\u0442\u043a\u0438;')

# except block 1: verdict unavailable
e1_old = ('Исключение\n\t\t// вердикт недоступен - статус остаётся от запуска (timeout/error)\n\tКонецПопытки;')
e1_new = ('Исключение\n\t\t// вердикт недоступен - статус остаётся от запуска (timeout/error)\n'
          '\t\tРезультат.error = Результат.error\n'
          '\t\t\t+ ПодробноеПредставлениеОшибки(ИнформацияОбОшибке());\n\tКонецПопытки;')
# except block 2: cleanup failure
e2_old = ('Исключение\n\t\t// артефакты батча необязательны для вердикта\n\tКонецПопытки;')
e2_new = ('Исключение\n\t\t// артефакты батча необязательны для вердикта\n'
          '\t\tРезультат.error = Результат.error\n'
          '\t\t\t+ ПодробноеПредставлениеОшибки(ИнформацияОбОшибке());\n\tКонецПопытки;')

assert txt.count(e1_old) == 1, 'e1 pattern'
txt = txt.replace(e1_old, e1_new)
assert txt.count(e2_old) == 1, 'e2 pattern'
txt = txt.replace(e2_old, e2_new)
open(p, 'wb').write(txt.encode('utf-8'))
print('patched OK')
