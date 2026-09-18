from __future__ import annotations
"""C 方案輸入擷取器：監聽全域鍵盤，轉成核心可處理事件。"""

import time
from typing import Callable

from pynput import keyboard


class InputCaptureAdapter:
    def __init__(self, on_key: Callable[[str], None], is_composing: Callable[[], bool] | None = None) -> None:
        # on_key: 單鍵事件。
        self._on_key = on_key
        self._is_composing = is_composing
        self._listener: keyboard.Listener | None = None
        self._capture_paused = False
        self._suppress_until = 0.0
        self._suppressing_enter = False

    def start(self) -> None:
        # 啟動背景監聽執行緒。
        # 在 Windows 上利用 win32_event_filter 攔截 Enter 鍵，避免它在目標視窗中觸發換行或送出
        import sys
        if sys.platform == "win32":
            self._listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release,
                win32_event_filter=self._win32_event_filter
            )
        else:
            self._listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        self._listener.start()

    def stop(self) -> None:
        # 停止背景監聽執行緒。
        if self._listener is not None:
            self._listener.stop()

    def _win32_event_filter(self, msg: int, data: any) -> bool:
        try:
            # VK_RETURN (Enter 鍵) 的虛擬鍵碼為 0x0D
            if data.vkCode == 0x0D:
                # 0x0100: WM_KEYDOWN, 0x0104: WM_SYSKEYDOWN
                if msg in (0x0100, 0x0104):
                    composing = self._is_composing() if self._is_composing else False
                    if not self._capture_paused and composing:
                        self._suppressing_enter = True
                        self._on_key("enter")
                        
                        if self._listener is not None:
                            self._listener.suppress_event()
                            
                # 0x0101: WM_KEYUP, 0x0105: WM_SYSKEYUP
                elif msg in (0x0101, 0x0105):
                    if self._suppressing_enter:
                        self._suppressing_enter = False
                        if self._listener is not None:
                            self._listener.suppress_event()
        except Exception as e:
            # SuppressException 必須重新向上拋出，pynput 才能接收並在作業系統層級攔截該按鍵事件
            if e.__class__.__name__ == 'SuppressException':
                raise
            import traceback
            traceback.print_exc()
        return True

    def set_paused(self, paused: bool) -> None:
        # 提交文字時暫停擷取，避免自觸發回圈。
        self._capture_paused = paused
        if not paused:
            # 避免提交回灌的尾端事件在恢復後被擷取。
            self._suppress_until = time.monotonic() + 0.05

    def _on_press(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        if self._capture_paused:
            return
        if time.monotonic() < self._suppress_until:
            return

        normalized = self._normalize_key(key)
        if not normalized:
            return

        self._on_key(normalized)

    def _on_release(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        # 目前不需追蹤組合鍵狀態，保留介面以符合 listener callback。
        _ = key

    @staticmethod
    def _normalize_key(key: keyboard.Key | keyboard.KeyCode) -> str:
        # 將 pynput key 物件轉成核心約定字串。
        if isinstance(key, keyboard.KeyCode):
            if key.char:
                return key.char
            return ""

        key_map = {
            keyboard.Key.backspace: "backspace",
            keyboard.Key.space: "space",
            keyboard.Key.enter: "enter",
            keyboard.Key.esc: "esc",
            keyboard.Key.up: "up",
            keyboard.Key.down: "down",
        }
        return key_map.get(key, "")
