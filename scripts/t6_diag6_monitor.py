# -*- coding: utf-8 -*-
"""T6 diag6: passive monitor for the production gate cycle.

Run alongside `python scripts/t6_gate.py b`. Every SCAN seconds captures:
- top-level window titles (win32gui)
- UIA tree dump of V8Window* windows (names of controls/buttons)
- full-desktop screenshot (if SCAN is running in an interactive session)
- CIM snapshot of 1cv8/1cv8c/cmd/conhost processes with command lines

Everything lands in tmp/t6/diag6/. Passive only: no clicks, no kills.
Stops when tmp/t6/diag6/stop exists or duration exceeded.
"""
import io
import json
import os
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"C:\MyProjects\APKScenTest"
DIAG = os.path.join(ROOT, "tmp", "t6", "diag6")
DURATION = int(os.environ.get("DIAG6_DURATION", "1200"))
SCAN = 15

os.makedirs(DIAG, exist_ok=True)
STOP = os.path.join(DIAG, "stop")

UIA_PS = r"""
Add-Type -AssemblyName UIAutomationClient
$root = [System.Windows.Automation.AutomationElement]::RootElement
$cond = [System.Windows.Automation.Condition]::TrueCondition
$wins = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $cond)
foreach ($w in $wins) {
  $cn = $w.Current.ClassName
  $nm = $w.Current.Name
  if ($cn -notlike 'V8Window*' -and $nm -notlike '*1*' -and $nm -notlike '*Предприятие*') { }
  if ($cn -notlike 'V8Window*') { continue }
  '=== V8WIN: ' + $nm
  $btncond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Button)
  $btns = $w.FindAll([System.Windows.Automation.TreeScope]::Descendants, $btncond)
  foreach ($b in $btns) { '  BUTTON: ' + $b.Current.Name }
  $txtcond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Text)
  $txts = $w.FindAll([System.Windows.Automation.TreeScope]::Descendants, $txtcond)
  $i = 0
  foreach ($t in $txts) { $i++; if ($i -gt 15) { break }; '  TEXT: ' + $t.Current.Name }
}
"""


def window_titles():
    titles = []

    def cb(hwnd, _):
        import win32gui
        if win32gui.IsWindowVisible(hwnd):
            t = win32gui.GetWindowText(hwnd)
            if t:
                titles.append(t[:100])
    try:
        import win32gui
        win32gui.EnumWindows(cb, None)
    except Exception as e:
        titles.append("enumfail: %s" % str(e)[:80])
    return titles


def uia_dump():
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", UIA_PS],
                             capture_output=True, timeout=120)
        return out.stdout.decode("utf-8", errors="replace")
    except Exception as e:
        return "uiafail: %s" % str(e)[:120]


def proc_snapshot():
    try:
        ps = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(1cv8|1cv8c)\\.exe$' } | "
             "Select-Object ProcessId,ParentProcessId,Name,CommandLine | ConvertTo-Json -Compress"],
            capture_output=True, timeout=90)
        raw = ps.stdout.decode("utf-8", errors="replace")
        try:
            rows = json.loads(raw)
        except Exception:
            rows = raw
        lines = []
        if isinstance(rows, dict):
            rows = [rows]
        if isinstance(rows, list):
            for r in rows:
                if isinstance(r, dict):
                    lines.append("pid=%s ppid=%s %s :: %s" % (
                        r.get("ProcessId"), r.get("ParentProcessId"), r.get("Name"),
                        (r.get("CommandLine") or "")[:180]))
        return "\n".join(lines)
    except Exception as e:
        return "procfail: %s" % str(e)[:120]


def screenshot(tag):
    try:
        import win32gui
        import win32ui
        import win32con
        hwin = win32gui.GetDesktopWindow()
        import win32api
        width = win32api.GetSystemMetrics(0)
        height = win32api.GetSystemMetrics(1)
        hdc = win32gui.GetWindowDC(hwin)
        try:
            import ctypes
            import ctypes.wintypes
            from PIL import Image
            mfcdc = win32ui.CreateDCFromHandle(hdc)
            save = win32ui.CreateBitmap()
            save.CreateCompatibleBitmap(mfcdc, width, height)
            mfc = save.CreateCompatibleDC(mfcdc)
            mfc.BitBlt((0, 0), (width, height), mfcdc, (0, 0), win32con.SRCCOPY)
            path = os.path.join(DIAG, "shot-%s.png" % tag)
            save.SaveBitmapFile(mfc, path)
            win32gui.DeleteObject(save.GetHandle())
            mfc.DeleteDC()
            win32gui.DeleteDC(mfcdc)
            return path
        finally:
            win32gui.ReleaseDC(hwin, hdc)
    except Exception as e:
        return "shotfail: %s" % str(e)[:120]


def main():
    print("[diag6] monitoring %ds, scan=%ds" % (DURATION, SCAN), flush=True)
    t0 = time.time()
    while time.time() - t0 < DURATION:
        if os.path.exists(STOP):
            print("[diag6] stop-file", flush=True)
            break
        dt = int(time.time() - t0)
        rec = io.open(os.path.join(DIAG, "monitor.log"), "a", encoding="utf-8")
        try:
            rec.write("=== t=%ds (%s) ===\n" % (dt, time.strftime("%H:%M:%S")))
            rec.write("--- wins: %s\n" % " | ".join(window_titles())[:600])
            rec.write("--- procs:\n%s\n" % proc_snapshot())
            rec.write("--- uia:\n%s\n" % uia_dump())
        finally:
            rec.close()
        shot = screenshot("%04d" % dt)
        print("[diag6] t=%ds shot=%s" % (dt, shot), flush=True)
        time.sleep(SCAN)
    print("[diag6] done", flush=True)


if __name__ == "__main__":
    main()
