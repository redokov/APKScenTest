# Click the (single) button inside a modal window identified by HWND.
# Usage: python scripts/s009_click_modal.py <hwnd>
import sys
import subprocess

PS = r"""
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
$target = [IntPtr]::new(%s)
$root = [System.Windows.Automation.AutomationElement]::RootElement
$wins = $root.FindAll([System.Windows.Automation.TreeScope]::Children, [System.Windows.Automation.Condition]::TrueCondition)
$modal = $null
foreach ($w in $wins) {
  if ($w.Current.NativeWindowHandle -eq $target) { $modal = $w; break }
}
if (-not $modal) { Write-Output 'MODAL_NOT_FOUND'; exit 1 }
$btnCond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Button)
$btns = $modal.FindAll([System.Windows.Automation.TreeScope]::Descendants, $btnCond)
Write-Output ('BUTTONS=' + $btns.Count)
if ($btns.Count -lt 1) { exit 2 }
$b = $btns[0]
Write-Output ('CLICK: ' + $b.Current.Name)
$inv = $b.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
$inv.Invoke()
Start-Sleep -Seconds 2
Write-Output 'CLICKED'
"""

if __name__ == "__main__":
    hwnd = sys.argv[1]
    r = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", PS % int(hwnd)],
        capture_output=True, text=True, timeout=120)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(r.stdout)
    print(r.stderr[:500])
