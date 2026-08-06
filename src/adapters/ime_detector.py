from __future__ import annotations
"""偵測 Windows 前景視窗的系統輸入法狀態。

使用 ImmGetDefaultIMEWnd + SendMessage(WM_IME_CONTROL) 的方式，
相容使用 TSF 的現代應用程式（如 VSCode、UWP 等）。
"""

import ctypes

# WM_IME_CONTROL 訊息常數。
_WM_IME_CONTROL = 0x0283
# IMC_GETCONVERSIONMODE 子命令。
_IMC_GETCONVERSIONMODE = 0x0001
# IME_CMODE_NATIVE: 設定時為原生（中文）模式。
_IME_CMODE_NATIVE = 0x0001


def is_english_input() -> bool | None:
    """判斷前景視窗目前是否為英文輸入模式。

    回傳 True 表示英文，False 表示中文，
    None 表示無法判斷。
    """
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    imm32 = ctypes.WinDLL("imm32", use_last_error=True)

    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None

    ime_hwnd = imm32.ImmGetDefaultIMEWnd(hwnd)
    if not ime_hwnd:
        return None

    conv_mode = user32.SendMessageW(ime_hwnd, _WM_IME_CONTROL, _IMC_GETCONVERSIONMODE, 0)
    return not bool(conv_mode & _IME_CMODE_NATIVE)
