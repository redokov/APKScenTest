# -*- coding: utf-8 -*-
"""s005 live run: shared UIA helpers for 1C 8.5 thin/thick client windows.

Patterns proven in t8_gate.py: V8Window* class names, security modal
'1С:Предприятие' with 'Продолжить' button, InvokePattern for buttons.
New here: field read/set via ValuePattern, window dump, question dialog
Да/Нет click, file dialog driving."""
import os, subprocess, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V8 = r"C:\Program Files\1cv8\8.5.4.1683\bin\1cv8.exe"
CONN = r"localhost\dev_erpapk_demo"
ADMIN = "Администратор (ОрловАВ)"
TMP = os.path.join(ROOT, "tmp", "s005")


def log(msg):
    print(msg, flush=True)


def ps(script, timeout=120):
    r = subprocess.run(["powershell", "-NoProfile", "-Command", script],
                       capture_output=True, timeout=timeout)
    return r.stdout.decode("utf-8", "replace") + r.stderr.decode("utf-8", "replace")


def launch(epf, client_log):
    os.makedirs(TMP, exist_ok=True)
    fp = open(client_log, "wb")
    proc = subprocess.Popen(
        [V8, "/S", CONN, "/RunModeManagedApplication", "/N", ADMIN,
         "/DisableStartupDialogs", "/Execute", epf],
        stdout=fp, stderr=subprocess.STDOUT)
    return proc, fp


def watchdog_start(duration_sec, log_name):
    """Dismiss the security modal '1С:Предприятие' [Продолжить]."""
    wd_ps = r"""
$ErrorActionPreference = 'Continue'
Add-Type -AssemblyName UIAutomationClient
$deadline = (Get-Date).AddSeconds(%d)
$log = '%s'
while ((Get-Date) -lt $deadline) {
  Start-Sleep -Milliseconds 1000
  try {
    $root = [System.Windows.Automation.AutomationElement]::RootElement
    $wins = $root.FindAll([System.Windows.Automation.TreeScope]::Children, [System.Windows.Automation.Condition]::TrueCondition)
    foreach ($w in $wins) {
      if ($w.Current.ClassName -notlike 'V8Window*') { continue }
      if ($w.Current.Name -ne '1С:Предприятие') { continue }
      $btncond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.AutomationControlType]::Button)
      $btns = $w.FindAll([System.Windows.Automation.TreeScope]::Descendants, $btncond)
      foreach ($b in $btns) {
        if ($b.Name -eq 'Продолжить') {
          try {
            $b.GetPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
            Add-Content -Path $log -Value ('dismissed security modal') -Encoding UTF8
          } catch {}
        }
      }
    }
  } catch {}
}
""" % (duration_sec, os.path.join(TMP, log_name).replace("\\", "\\\\"))
    return subprocess.Popen(["powershell", "-NoProfile", "-Command", wd_ps],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


DUMP_PS = r"""
$ErrorActionPreference = 'Continue'
Add-Type -AssemblyName UIAutomationClient
$out = '%s'
$root = [System.Windows.Automation.AutomationElement]::RootElement
$wins = $root.FindAll([System.Windows.Automation.TreeScope]::Children, [System.Windows.Automation.Condition]::TrueCondition)
$sb = New-Object System.Text.StringBuilder
foreach ($w in $wins) {
  if ($w.Current.ClassName -notlike 'V8Window*') { continue }
  [void]$sb.AppendLine(('WIN: ' + $w.Current.Name + ' | ' + $w.Current.ClassName))
  $els = $w.FindAll([System.Windows.Automation.TreeScope]::Descendants, [System.Windows.Automation.Condition]::TrueCondition)
  foreach ($e in $els) {
    $ct = $e.Current.ControlType.ProgrammaticName
    if ($ct -like '*Pane*' -or $ct -like '*Custom*') { continue }
    $line = ('  ' + $ct + ' | ' + $e.Current.Name)
    try {
      $v = $e.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
      $line = $line + ' | VAL=' + $v.Current.Value
    } catch {}
    [void]$sb.AppendLine($line)
  }
}
[System.IO.File]::WriteAllText($out, $sb.ToString(), [System.Text.Encoding]::UTF8)
Write-Output ('lines: ' + $sb.Length)
"""


def dump(path):
    """Dump all V8Window* UIA trees (control types, names, values)."""
    return ps(DUMP_PS % path.replace("\\", "\\\\"), timeout=180)


CLICK_PS = r"""
$ErrorActionPreference = 'Continue'
Add-Type -AssemblyName UIAutomationClient
$winTitle = '%s'
$ctlType = '%s'
$name = '%s'
$root = [System.Windows.Automation.AutomationElement]::RootElement
$wins = $root.FindAll([System.Windows.Automation.TreeScope]::Children, [System.Windows.Automation.Condition]::TrueCondition)
$found = 0
foreach ($w in $wins) {
  if ($w.Current.ClassName -notlike 'V8Window*') { continue }
  if ($winTitle -ne '*' -and $w.Current.Name -ne $winTitle) { continue }
  $cond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::$ctlType)
  $els = $w.FindAll([System.Windows.Automation.TreeScope]::Descendants, $cond)
  foreach ($e in $els) {
    if ($e.Current.Name -notlike $name) { continue }
    $found = $found + 1
    if ($ctlType -eq 'Button') {
      $e.GetPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
    } else {
      try { $e.SetFocus() } catch {}
    }
    break
  }
  if ($found -gt 0) { break }
}
Write-Output ('clicked: ' + $found)
"""


def click(win_title, name_pattern, ctl="Button"):
    return ps(CLICK_PS % (win_title, ctl, name_pattern))


GETVAL_PS = r"""
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
    out = ps(GETVAL_PS % (win_title, name))
    for line in out.splitlines():
        if line.startswith("VAL: "):
            return line[5:]
    return None
