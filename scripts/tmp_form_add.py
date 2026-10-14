# -*- coding: utf-8 -*-
"""tmp_form_add.py — добавление формы Форма к EPF (form-add.ps1, кириллица через файл)."""
import subprocess, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PS = r'C:/MyProjects/PiPack/skills/1c/form-add/scripts/form-add.ps1'
OBJ = 'src/АпкПодготовкаСценарныхТестов.xml'

args = [
    'powershell.exe', '-NoProfile', '-File', PS,
    '-ObjectPath', OBJ,
    '-FormName', 'Форма',
    '-Purpose', 'Object',
    '-SetDefault',
]
r = subprocess.run(args, capture_output=True)
sys.stdout.write(r.stdout.decode('utf-8', 'replace'))
sys.stdout.write(r.stderr.decode('utf-8', 'replace'))
print('exit:', r.returncode)
