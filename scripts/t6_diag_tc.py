# -*- coding: utf-8 -*-
"""T6 diag2: launch TestClient manually, watch windows/screenshot."""
import os
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
V8C = r"C:\Program Files\1cv8\8.5.4.1683\bin\1cv8c.exe"
DIAG = r"C:\MyProjects\APKScenTest\tmp\t6\diag"
ADMIN = "Администратор (ОрловАВ)"
BASE = r"localhost\dev_erpapk_demo"


def shot(tag):
    path = os.path.join(DIAG, "tc-%s.png" % tag)
    ps = r"""
Add-Type -AssemblyName System.Windows.Forms,System.Drawing
$b = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($b.Left, $b.Top, 0, 0, $bmp.Size)
$bmp.Save('%s')
$g.Dispose(); $bmp.Dispose()
""" % path.replace("\\", "\\")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                   capture_output=True, timeout=60)
    return path


def wins():
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-Process | Where-Object {$_.MainWindowTitle} | "
         "ForEach-Object { $_.Id.ToString() + ' :: ' + $_.ProcessName + ' :: ' + $_.MainWindowTitle }"],
        capture_output=True, timeout=30)
    return out.stdout.decode("utf-8", errors="replace").strip().splitlines()


def main():
    cmd = [V8C, "/TestClient", "-TCPHost", "localhost", "-TCPPort", "48512",
           "/S", BASE, "/N", ADMIN, "/P", "",
           "/DisableStartupMessages", "/DisableStartupDialogs"]
    print("[tc] launching:", " ".join(cmd))
    p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for t in (10, 25, 40):
        time.sleep(t - (10 if t == 25 else 20 if t == 40 else 0) or 0)
    # simpler loop:
    for i, t in enumerate((10, 15, 20, 30, 45)):
        target = sum((10, 5, 5, 10, 15)[:i + 1])
        time.sleep(target - (sum((10, 5, 5, 10, 15)[:i]) if i else 0))
        alive = p.poll() is None
        print("[t=%ds] alive=%s" % (target, alive))
        for w in wins():
            if "1cv8" in w or "1C" in w or "Предприятие" in w:
                print("   win:", w)
        shot("t%d" % target)
    if p.poll() is None:
        subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"], capture_output=True)
    print("[tc] done rc=%s" % p.poll())


if __name__ == "__main__":
    main()
