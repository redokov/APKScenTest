# -*- coding: utf-8 -*-
"""s005 T8: RestoreIB via Designer batch (python-subprocess: no MSYS
path mangling, proper UTF-16 cyrillic args). Usage: python scripts/s005_restore_ib.py"""
import subprocess
import sys

CMD = [r"C:\Program Files\1cv8\8.5.4.1683\bin\1cv8.exe", "DESIGNER",
       r"/S", "localhost\dev_erpapk_demo",
       r"/N", u"\u0410\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440 (\u041e\u0440\u043b\u043e\u0432\u0410\u0412)",
       r"/RestoreIB",
       r"C:\MyProjects\APKScenTest\tmp\regress\20261028-062041\pre-update.dt",
       r"/Out", r"C:\MyProjects\APKScenTest\tmp\s005\t8restore\restore.log",
       r"/DumpResult", r"C:\MyProjects\APKScenTest\tmp\s005\t8restore\restore.result"]
p = subprocess.run(CMD, capture_output=True)
print("designer exit:", p.returncode)
sys.exit(p.returncode)
