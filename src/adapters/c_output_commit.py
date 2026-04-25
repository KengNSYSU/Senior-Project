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

        with self._paused_capture():
            for _ in range(max(0, replace_len)):
                self._keyboard.press(Key.backspace)
                self._keyboard.release(Key.backspace)

            if text:
                self._keyboard.type(text)
