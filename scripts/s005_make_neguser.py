# -*- coding: utf-8 -*-
"""s005 T5: (re)create the neg IB user via the proven python-t8 recipe
(t8_gate.create_neg_user: IB user + 5 roles + ZOD off + catalog binding
via DataExchange.Load). Headless COM. Usage: python scripts/s005_make_neguser.py"""
import io
import sys

sys.path.insert(0, "scripts")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace")
import win32com.client
import t8_gate as t

agent = win32com.client.Dispatch("V85.COMConnector").Connect(
    t.conn_str(t.ADMIN, ""))
users = agent.ПользователиИнформационнойБазы
h1 = t.create_neg_user(agent, users)
print("OK: neg user created, H1 len=%d" % len(h1))
