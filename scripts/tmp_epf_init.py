# -*- coding: utf-8 -*-
"""tmp_epf_init.py — запуск epf-init/init.ps1 с кириллическими параметрами.

python-скрипт-файл надёжно хранит UTF-8 литералы; subprocess передаёт
аргументы в CreateProcess как UTF-16, минуя ненадёжный bash-транспорт.
"""
import subprocess, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PS = r'C:/MyProjects/PiPack/skills/1c/epf-init/scripts/init.ps1'

NAME = 'АпкПодготовкаСценарныхТестов'
SYNONYM = 'Подготовка сценарных тестов АПК'

args = [
    'powershell.exe', '-NoProfile', '-File', PS,
    '-Name', NAME,
    '-Synonym', SYNONYM,
    '-SrcDir', 'src',
    '-FormatVersion', '2.21',
]
r = subprocess.run(args, capture_output=True)
sys.stdout.write(r.stdout.decode('utf-8', 'replace'))
sys.stdout.write(r.stderr.decode('utf-8', 'replace'))
print('exit:', r.returncode)
