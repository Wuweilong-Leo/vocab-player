# -*- coding: utf-8 -*-
"""全局热键 Ctrl+Alt+P"""
import ctypes
import threading
from ctypes import wintypes
from config import WM_HOTKEY, MOD_CONTROL, MOD_ALT, VK_P


class _MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", wintypes.POINT),
    ]


def start_hotkey(callback):
    """注册 Ctrl+Alt+P 全局热键,按下时调用 callback()。
    在守护线程中运行,失败时静默跳过。"""

    def run():
        try:
            user32 = ctypes.windll.user32
            ok = user32.RegisterHotKey(None, 1, MOD_CONTROL | MOD_ALT, VK_P)
            if not ok:
                return
            msg = _MSG()
            while True:
                r = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if r <= 0:
                    break
                if msg.message == WM_HOTKEY:
                    try:
                        callback()
                    except Exception:
                        pass
            user32.UnregisterHotKey(None, 1)
        except Exception:
            pass

    threading.Thread(target=run, daemon=True).start()
