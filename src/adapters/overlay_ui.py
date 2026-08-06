from __future__ import annotations
"""C 方案浮層視窗：顯示輸入狀態、組字緩衝與候選清單。"""

import queue
import threading
import tkinter as tk
from dataclasses import replace
from typing import Callable

from src.core.contracts import CompositionState


class OverlayWindow:
    def __init__(self, on_ime_changed: Callable[[bool], None] | None = None) -> None:
        # 建立簡易置頂視窗，作為驗證版候選 UI。
        self._root = tk.Tk()
        self._root.title("Senior Project IME")
        self._root.attributes("-topmost", True)
        self._root.geometry("460x160+100+100")

        self._closed = threading.Event()
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)

        # IME 狀態偵測：每 10 次 drain（~330ms）檢查一次。
        self._on_ime_changed = on_ime_changed
        self._ime_poll_counter = 0
        self._last_is_english: bool | None = None

        self._state_queue: queue.Queue[CompositionState] = queue.Queue()

        self._status_label = tk.Label(self._root, text="Mode: AUTO", font=("Segoe UI", 11, "bold"))
        self._status_label.pack(anchor="w", padx=10, pady=(8, 4))

        self._buffer_label = tk.Label(self._root, text="Buffer: ", font=("Consolas", 11))
        self._buffer_label.pack(anchor="w", padx=10)

        self._debug_label = tk.Label(self._root, text="Debug: ", font=("Consolas", 10))
        self._debug_label.pack(anchor="w", padx=10, pady=(2, 2))

        self._candidate_box = tk.Listbox(self._root, height=6, width=64)
        self._candidate_box.pack(anchor="w", padx=10, pady=(4, 8))

        self._root.after(33, self._drain_queue)

    def enqueue_state(self, state: CompositionState) -> None:
        # 由其他執行緒推入狀態，由 UI 執行緒統一渲染。
        self._state_queue.put(replace(state))

    @property
    def is_closed(self) -> bool:
        """視窗是否已關閉，供外部查詢以進行資源清理。"""
        return self._closed.is_set()

    def run(self) -> None:
        self._root.mainloop()

    def _on_close(self) -> None:
        # 標記已關閉，停止 polling 後再銷毀視窗。
        self._closed.set()
        self._root.destroy()

    def _drain_queue(self) -> None:
        # 若視窗已關閉，不再排程以避免操作已銷毀的 widget。
        if self._closed.is_set():
            return
        # 每 10 次 drain（~330ms）檢查一次系統輸入法狀態。
        self._ime_poll_counter += 1
        if self._ime_poll_counter >= 10:
            self._ime_poll_counter = 0
            self._check_ime_state()
        # 批次取出待渲染狀態，降低 UI 閃爍。
        while True:
            try:
                state = self._state_queue.get_nowait()
            except queue.Empty:
                break
            self._render(state)
        self._root.after(33, self._drain_queue)

    def _check_ime_state(self) -> None:
        """偵測系統輸入法狀態，若有變化則通知 app 並更新標籤。"""
        import ctypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        imm32 = ctypes.WinDLL("imm32", use_last_error=True)

        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return

        # 取得前景視窗對應的預設 IME 視窗（相容 TSF 應用程式）。
        ime_hwnd = imm32.ImmGetDefaultIMEWnd(hwnd)
        if not ime_hwnd:
            return

        # WM_IME_CONTROL = 0x0283, IMC_GETCONVERSIONMODE = 0x0001
        conv_mode = user32.SendMessageW(ime_hwnd, 0x0283, 0x0001, 0)
        # IME_CMODE_NATIVE (0x0001): 設定時為中文模式，未設定時為英文模式。
        is_english = not bool(conv_mode & 0x0001)

        if is_english == self._last_is_english:
            return
        self._last_is_english = is_english
        if is_english:
            self._status_label.config(text="Mode: AUTO")
        else:
            self._status_label.config(text="Mode: ⚠ 非英文輸入法（已暫停）")
        if self._on_ime_changed:
            self._on_ime_changed(is_english)

    def _render(self, state: CompositionState) -> None:
        # 以最新狀態更新標籤與候選列表。
        # 僅在英文模式下以 engine 狀態更新標籤，避免覆蓋 IME 警示。
        if self._last_is_english is not False:
            self._status_label.config(text=f"Mode: {state.status}")
        self._buffer_label.config(text=f"Buffer: {state.buffer}")
        self._debug_label.config(text=f"Debug: {state.debug_message}")

        self._candidate_box.delete(0, tk.END)
        for idx, item in enumerate(state.candidates, start=1):
            cursor = ">" if (idx - 1) == state.selected_index else " "
            line = f"{cursor} {idx}. {item.text} | score={item.final_score:.3f} | src={item.source}"
            self._candidate_box.insert(tk.END, line)
