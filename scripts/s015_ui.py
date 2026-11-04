# -*- coding: utf-8 -*-
"""s015: UIA helpers for user-docs screenshots (preprocessor + runner forms).

Reuses proven PS patterns from s005_uia_lib (dump/click/get_value).
Adds: set_value (ValuePattern + Enter commit), window enumeration,
window screenshot via s010_shot, graceful WM_CLOSE, file-dialog driving.
All output -> tmp/s015/.
"""
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s005_uia_lib as uia  # noqa: E402
from s010_shot import shot  # noqa: E402


def ps(script, timeout=120):
    """UTF-8-safe powershell wrapper (s005_uia_lib.ps decodes cp866 as utf-8)."""
    pre = "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8;"
    r = subprocess.run(["powershell", "-NoProfile", "-Command", pre + script],
                       capture_output=True, timeout=timeout)
    return r.stdout.decode("utf-8", "replace") + r.stderr.decode("utf-8", "replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S015 = os.path.join(ROOT, "tmp", "s015")
V8 = r"C:\Program Files\1cv8\8.5.4.1683\bin\1cv8.exe"
V8C = r"C:\Program Files\1cv8\8.5.4.1683\bin\1cv8c.exe"
CONN = r"localhost\dev_erpapk_demo"
ADMIN = "Администратор (ОрловАВ)"

os.makedirs(S015, exist_ok=True)


def log(msg):
    ts = time.strftime("%H:%M:%S")
    print("[%s] %s" % (ts, msg), flush=True)
    with open(os.path.join(S015, "ui.log"), "a", encoding="utf-8") as f:
        f.write("[%s] %s\n" % (ts, msg))


def launch(epf, name):
    """Launch 1C thin client with /Execute epf (detached, log in tmp/s015)."""
    client_log = os.path.join(S015, name + ".log")
    fp = open(client_log, "wb")
    proc = subprocess.Popen(
        [V8, "/S", CONN, "/RunModeManagedApplication", "/N", ADMIN,
         "/DisableStartupDialogs", "/Execute", epf],
        stdout=fp, stderr=subprocess.STDOUT)
    uia.watchdog_start(600, "wd_" + name + ".log")  # dismiss [Продолжить]
    return proc, client_log


LISTWIN_PS = r"""
$ErrorActionPreference = 'Continue'
Add-Type -AssemblyName UIAutomationClient
$root = [System.Windows.Automation.AutomationElement]::RootElement
$wins = $root.FindAll([System.Windows.Automation.TreeScope]::Children, [System.Windows.Automation.Condition]::TrueCondition)
foreach ($w in $wins) {
  if ($w.Current.ClassName -notlike 'V8Window*' -and $w.Current.ClassName -ne '#32770') { continue }
  Write-Output ($w.Current.Name + ' | ' + $w.Current.ClassName + ' | ' + $w.Current.NativeWindowHandle)
}
"""


def list_windows():
    out = ps(LISTWIN_PS, timeout=60)
    wins = []
    for line in out.splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) == 3 and parts[2].isdigit():
            wins.append({"title": parts[0], "class": parts[1], "hwnd": int(parts[2])})
    return wins


def find_window(title_contains, retries=20, delay=3):
    for _ in range(retries):
        for w in list_windows():
            if title_contains in w["title"]:
                return w
        time.sleep(delay)
    return None


SETVAL_PS = r"""
$ErrorActionPreference = 'Continue'
Add-Type -AssemblyName UIAutomationClient
$winTitle = '%s'
$name = '%s'
$val = '%s'
$root = [System.Windows.Automation.AutomationElement]::RootElement
$wins = $root.FindAll([System.Windows.Automation.TreeScope]::Children, [System.Windows.Automation.Condition]::TrueCondition)
foreach ($w in $wins) {
  if ($w.Current.ClassName -notlike 'V8Window*') { continue }
  if ($winTitle -ne '*' -and $w.Current.Name -ne $winTitle) { continue }
  $els = $w.FindAll([System.Windows.Automation.TreeScope]::Descendants, [System.Windows.Automation.Condition]::TrueCondition)
  foreach ($e in $els) {
    if ($e.Current.Name -ne $name) { continue }
    try {
      $v = $e.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
      $v.SetValue($val)
      Write-Output 'SET: ok'
      exit
    } catch {}
  }
}
Write-Output 'SET: notfound'
"""


CLICK2_PS = r"""
$ErrorActionPreference = 'Continue'
Add-Type -AssemblyName UIAutomationClient
$winTitle = '%s'
$name = '%s'
$root = [System.Windows.Automation.AutomationElement]::RootElement
$wins = $root.FindAll([System.Windows.Automation.TreeScope]::Children, [System.Windows.Automation.Condition]::TrueCondition)
$found = 0
foreach ($w in $wins) {
  if ($w.Current.ClassName -notlike 'V8Window*') { continue }
  if ($winTitle -ne '*' -and $w.Current.Name -ne $winTitle) { continue }
  $els = $w.FindAll([System.Windows.Automation.TreeScope]::Descendants, [System.Windows.Automation.Condition]::TrueCondition)
  foreach ($e in $els) {
    if ($e.Current.Name -ne $name) { continue }
    $found = $found + 1
    $inv = $e.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
    $inv.Invoke()
    break
  }
  if ($found -gt 0) { break }
}
Write-Output ('clicked: ' + $found)
"""


def click(win_title, name):
    out = ps(CLICK2_PS % (win_title, name), timeout=60)
    return 'clicked: 1' in out


GETVAL2_PS = r"""
$ErrorActionPreference = 'Continue'
Add-Type -AssemblyName UIAutomationClient
$winTitle = '%s'
$name = '%s'
$root = [System.Windows.Automation.AutomationElement]::RootElement
$wins = $root.FindAll([System.Windows.Automation.TreeScope]::Children, [System.Windows.Automation.Condition]::TrueCondition)
foreach ($w in $wins) {
  if ($w.Current.ClassName -notlike 'V8Window*') { continue }
  if ($winTitle -ne '*' -and $w.Current.Name -ne $winTitle) { continue }
  $els = $w.FindAll([System.Windows.Automation.TreeScope]::Descendants, [System.Windows.Automation.Condition]::TrueCondition)
  foreach ($e in $els) {
    if ($e.Current.Name -ne $name) { continue }
    try {
      $v = $e.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
      Write-Output ('VAL: ' + $v.Current.Value)
      exit
    } catch {}
  }
}
Write-Output 'VAL: '
"""


def get_value(win_title, name):
    out = ps(GETVAL2_PS % (win_title, name), timeout=60)
    for line in out.splitlines():
        if line.startswith("VAL: "):
            return line[5:]
    return None


def set_value(win_title, name, val):
    out = ps(SETVAL_PS % (win_title, name, val.replace("'", "''")), timeout=60)
    ok = "SET: ok" in out
    if ok:  # commit edit: refocus window and press Enter via SendKeys
        commit = ps(r"""
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
""", timeout=30)
        log("set_value(%s)=%s commit=%s" % (name, ok, commit.strip()[:40]))
    return ok


RECT_PS = r"""
$ErrorActionPreference = 'Continue'
Add-Type -AssemblyName UIAutomationClient
$winTitle = '%s'
$name = '%s'
$root = [System.Windows.Automation.AutomationElement]::RootElement
$wins = $root.FindAll([System.Windows.Automation.TreeScope]::Children, [System.Windows.Automation.Condition]::TrueCondition)
foreach ($w in $wins) {
  if ($w.Current.ClassName -notlike 'V8Window*') { continue }
  if ($winTitle -ne '*' -and $w.Current.Name -ne $winTitle) { continue }
  $els = $w.FindAll([System.Windows.Automation.TreeScope]::Descendants, [System.Windows.Automation.Condition]::TrueCondition)
  foreach ($e in $els) {
    if ($e.Current.Name -ne $name) { continue }
    $r = $e.Current.BoundingRectangle
    Write-Output ('RECT: ' + $r.X + ',' + $r.Y + ',' + $r.Width + ',' + $r.Height)
    exit
  }
}
Write-Output 'RECT: '
"""


def get_rect(win_title, name):
    out = ps(RECT_PS % (win_title, name), timeout=60)
    for line in out.splitlines():
        if line.startswith("RECT: "):
            parts = line[6:].split(",")
            if len(parts) == 4:
                try:
                    x, y, w_, h_ = (float(p) for p in parts)
                    return x, y, w_, h_
                except ValueError:
                    return None
    return None


def click_real(win_title, name, dy=0.0):
    """Real mouse click at element center via SendInput."""
    rect = get_rect(win_title, name)
    if not rect or not rect[2]:
        return False
    x = int(rect[0] + rect[2] / 2)
    y = int(rect[1] + rect[3] / 2 + dy)
    import ctypes
    user32 = ctypes.windll.user32
    user32.SetCursorPos(x, y)
    time.sleep(0.15)
    user32.mouse_event(0x0002, 0, 0, 0, 0)  # LEFTDOWN
    time.sleep(0.05)
    user32.mouse_event(0x0004, 0, 0, 0, 0)  # LEFTUP
    log("click_real(%s) at %d,%d" % (name, x, y))
    return True


def click_at(x, y):
    import ctypes
    user32 = ctypes.windll.user32
    user32.SetCursorPos(x, y)
    time.sleep(0.15)
    user32.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.05)
    user32.mouse_event(0x0004, 0, 0, 0, 0)
    log("click_at %d,%d" % (x, y))


def screenshot(hwnd, png_name):
    path = os.path.join(S015, png_name)
    shot(hwnd, path)
    return path


def close_graceful(hwnd, wait_sec=60):
    """WM_CLOSE to the window, wait for process exit by window disappearance."""
    import ctypes
    ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE
    for _ in range(wait_sec // 2):
        time.sleep(2)
        for w in list_windows():
            if w["hwnd"] == hwnd:
                break
        else:
            return True
    return False


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for w in list_windows():
        print(w)
