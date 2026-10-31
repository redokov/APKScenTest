# -*- coding: utf-8 -*-
"""T3: глубокий UIA-дамп (БЕЗ фильтра Custom/Pane) - чтобы видеть строки
таблиц/выпадающих списков 1С (они ControlType.Custom/DataItem).
Usage: python scripts/s006_uia_deep.py <out.txt>"""
import sys

DEEP_PS = r"""
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
    $line = ('  ' + $e.Current.ControlType.ProgrammaticName + ' | ' + $e.Current.Name + ' | cls=' + $e.Current.ClassName)
    try {
      $v = $e.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
      $line = $line + ' | VAL=' + $v.Current.Value
    } catch {}
    [void]$sb.AppendLine($line)
  }
}
[System.IO.File]::WriteAllText($out, $sb.ToString(), [System.Text.Encoding]::UTF8)
Write-Output ('chars: ' + $sb.Length)
"""

if __name__ == "__main__":
    import subprocess
    out = sys.argv[1] if len(sys.argv) > 1 else "tmp/s006/deep-tree.txt"
    r = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         DEEP_PS % out.replace("\\", "\\\\")],
        capture_output=True, timeout=240)
    print(r.stdout.decode("utf-8", "replace") +
          r.stderr.decode("utf-8", "replace"))
