from __future__ import annotations
"""C 方案輸入擷取器：監聽全域鍵盤，轉成核心可處理事件。"""

import time
from typing import Callable

from pynput import keyboard


class InputCaptureAdapter:
    def __init__(self, on_key: Callable[[str], None]) -> None:
        # on_key: 單鍵事件。
        self._on_key = on_key
        self._listener: keyboard.Listener | None = None
        self._capture_paused = False
        self._suppress_until = 0.0

    def start(self) -> None:
        # 啟動背景監聽執行緒。
        self._listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        self._listener.start()

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
