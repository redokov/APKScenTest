param([int]$hwnd)
Add-Type '
using System;
using System.Text;
using System.Runtime.InteropServices;
public class C {
  [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr h, EnumProc cb, IntPtr l);
  public delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern int GetWindowTextW(IntPtr h, [MarshalAs(UnmanagedType.LPWStr)] StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern int GetClassNameW(IntPtr h, [MarshalAs(UnmanagedType.LPWStr)] StringBuilder s, int n);
}
'
$kids = New-Object System.Collections.ArrayList
$cb = {
  param($h, $l)
  $t = New-Object System.Text.StringBuilder 256
  [C]::GetWindowTextW($h, $t, 256) | Out-Null
  $c = New-Object System.Text.StringBuilder 256
  [C]::GetClassNameW($h, $c, 256) | Out-Null
  [void]$kids.Add(("h=$h class=" + $c.ToString() + " text=" + $t.ToString()))
  return $true
}
[C]::EnumChildWindows([IntPtr]$hwnd, $cb, [IntPtr]::Zero) | Out-Null
$kids | ForEach-Object { [Console]::WriteLine($_) }
