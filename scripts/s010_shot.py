# -*- coding: utf-8 -*-
"""s010: скриншот окна 1С по hwnd (PrintWindow PW_RENDERFULLCONTENT=2)."""
import ctypes
import ctypes.wintypes as w
import sys

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32


class BMIH(ctypes.Structure):
    _fields_ = [('biSize', w.DWORD), ('biWidth', w.LONG), ('biHeight', w.LONG),
                ('biPlanes', w.WORD), ('biBitCount', w.WORD),
                ('biCompression', w.DWORD), ('biSizeImage', w.DWORD),
                ('biXPelsPerMeter', w.LONG), ('biYPelsPerMeter', w.LONG),
                ('biClrUsed', w.DWORD), ('biClrImportant', w.DWORD)]


class BMI(ctypes.Structure):
    _fields_ = [('bmiHeader', BMIH), ('bmiColors', w.DWORD * 3)]


def shot(hwnd, path):
    rc = w.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rc))
    ww = max(1, rc.right - rc.left)
    hh = max(1, rc.bottom - rc.top)
    hdc = user32.GetWindowDC(hwnd)
    mem = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, ww, hh)
    gdi32.SelectObject(mem, bmp)
    user32.PrintWindow(hwnd, mem, 2)
    row = ((ww * 24 + 31) // 32) * 4
    buf = ctypes.create_string_buffer(row * hh)
    bmi = BMI()
    bmi.bmiHeader.biSize = ctypes.sizeof(BMIH)
    bmi.bmiHeader.biWidth = ww
    bmi.bmiHeader.biHeight = -hh
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 24
    gdi32.GetDIBits(mem, bmp, 0, hh, buf, ctypes.byref(bmi), 0)
    from PIL import Image
    im = Image.frombytes('RGB', (ww, hh), buf.raw[:row * hh])
    im.save(path)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mem)
    user32.ReleaseDC(hwnd, hdc)
    return ww, hh


if __name__ == '__main__':
    hwnd = int(sys.argv[1], 0)
    path = sys.argv[2]
    print(shot(hwnd, path))
