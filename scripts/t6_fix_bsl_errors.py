# T6: fix bsl-ls errors in ObjectModule.bsl and Form/Module.bsl.
# Byte-exact replacements (UTF-8 files, LF endings). Prints byte-diff proof.
import glob

obj = glob.glob('src/**/Ext/ObjectModule.bsl', recursive=True)[0]
mod = glob.glob('src/**/Form/Module.bsl', recursive=True)[0]

EMDASH = '\u2014'  # em-dash -> ASCII hyphen (InvalidCharacterInFile)
DQ = '\u0022'      # double quote


def patch(path, repl, label):
    data = open(path, 'rb').read()
    txt = data.decode('utf-8')
    applied = []
    for old, new in repl:
        n = txt.count(old)
        if n == 0:
            applied.append(f'  MISS: {old[:60]!r}')
            continue
        txt = txt.replace(old, new)
        applied.append(f'  x{n}: {old[:60]!r}')
    out = txt.encode('utf-8')
    open(path, 'wb').write(out)
    print(label)
    for a in applied:
        print(a)


# --- ObjectModule.bsl ---
q4 = DQ * 4          # """" - one quote char inside BSL string
obj_repl = [
    # ЗначениеИзСтрокиПодключения: search arg "\"\"" -> one-quote string
    ('(' + DQ + '\\' + DQ + DQ + ', ' + DQ + DQ + ')', '(' + q4 + ', ' + DQ + DQ + ')'),
    # Кавычки(): "\"" + ... + "\"" -> """" + ... + """"
    ('' + DQ + '\\' + DQ + DQ + ' + ' , q4 + ' + '),
    ('+ ' + DQ + '\\' + DQ + DQ + ';', '+ ' + q4 + ';'),
    # БазаИзСтрокиПодключения: "\\" (two backslashes) -> "\" (single)
    ('+ ' + DQ + '\\' + '\\' + DQ + ' + ', '+ ' + DQ + '\\' + DQ + ' + '),
    # em-dash -> hyphen in comments
    (EMDASH, '-'),
    # empty Except in ПодменитьПароль (ЗОД read)
    ('Исключение\n\t\t// свойство ЗОД недоступно (нет права/версия) - восстанавливать нечего\n\tКонецПопытки;',
     'Исключение\n\t\t// свойство ЗОД недоступно (нет права/версия) - восстанавливать нечего\n\t\tСнимок.ЗОД = Неопределено;\n\tКонецПопытки;'),
    # empty Except in НайтиПользователяИБПоИмени
    ('Исключение\n\t\t// метод может отсутствовать в сборке платформы - обход ниже\n\tКонецПопытки;',
     'Исключение\n\t\t// метод может отсутствовать в сборке платформы - обход ниже\n\t\tПользователь = Неопределено;\n\tКонецПопытки;'),
]
patch(obj, obj_repl, '=== ObjectModule.bsl ===')

# --- Form/Module.bsl ---
mod_repl = [
    # КомандаЗапускаБатча: Возврат "\"" + Команда + "\"";
    ('Возврат ' + DQ + '\\' + DQ + DQ + ' + Команда + ' + DQ + '\\' + DQ + DQ + ';',
     'Возврат ' + q4 + ' + Команда + ' + q4 + ';'),
    # КавычкиКлиент: Возврат "\"" + Строка(Значение) + "\"";
    ('Возврат ' + DQ + '\\' + DQ + DQ + ' + Строка(Значение) + ' + DQ + '\\' + DQ + DQ + ';',
     'Возврат ' + q4 + ' + Строка(Значение) + ' + q4 + ';'),
    # ТекущаяДата -> ТекущаяДатаСеанса
    ('ТекущаяДата()', 'ТекущаяДатаСеанса()'),
    # ping 127.0.0.1 -> localhost (UsingHardcodeNetworkAddress)
    ('127.0.0.1', 'localhost'),
    # WScript.Shell COM: accepted Windows-only deviation (TD-003)
    ('\tШелл = Новый COMОбъект(' + DQ + 'WScript.Shell' + DQ + ');',
     '\t// BSLLS:UsingObjectNotAvailableUnix-off\n\tШелл = Новый COMОбъект(' + DQ + 'WScript.Shell' + DQ + ');'),
]
patch(mod, mod_repl, '=== Form/Module.bsl ===')
