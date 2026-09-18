from __future__ import annotations
"""C 方案提交器：把選字結果送回前景應用。"""

from contextlib import contextmanager
from typing import Callable, Iterator

from pynput.keyboard import Controller, Key


class OutputCommitAdapter:
    def __init__(self, pause_capture: Callable[[bool], None]) -> None:
        # 透過 pause_capture 與輸入擷取器協調，避免鍵盤回灌。
        self._keyboard = Controller()
        self._pause_capture = pause_capture

    @contextmanager
    def _paused_capture(self) -> Iterator[None]:
        # 提交期間暫停擷取，提交後恢復。
        self._pause_capture(True)
        try:
            yield
        finally:
            self._pause_capture(False)

    def commit_text(self, text: str, replace_len: int = 0) -> None:
        # replace_len 代表先刪除組字長度，再輸入最終候選。
        if not text and replace_len <= 0:
            return

        import time

        with self._paused_capture():
            # 動態偵測並等待實體 Enter 鍵 (VK_RETURN = 0x0D) 完全被放開，以防與後續模擬的 Backspace 衝突
            try:
                import ctypes
                user32 = ctypes.windll.user32
                # GetAsyncKeyState 回傳值最高位元 (0x8000) 為 1 代表按鍵目前仍被按下
                while user32.GetAsyncKeyState(0x0D) & 0x8000:
                    time.sleep(0.01)
            except Exception:
                time.sleep(0.05)

            # 額外多等一小段時間讓作業系統的事件佇列與 UI 徹底就緒
            time.sleep(0.02)

            for _ in range(max(0, replace_len)):
                self._keyboard.press(Key.backspace)
                self._keyboard.release(Key.backspace)
                time.sleep(0.02)  # 20ms 延遲以確保目標視窗能正確處理每一個 Backspace

            if text:
                self._keyboard.type(text)
