from __future__ import annotations
"""C 方案浮層視窗：顯示輸入狀態、組字緩衝與候選清單。"""

import queue
import tkinter as tk
from dataclasses import replace

from src.core.contracts import CompositionState


class OverlayWindow:
    def __init__(self) -> None:
        # 建立簡易置頂視窗，作為驗證版候選 UI。
        self._root = tk.Tk()
        self._root.title("Senior Project IME")
        self._root.attributes("-topmost", True)
        self._root.geometry("460x160+100+100")

        self._state_queue: queue.Queue[CompositionState] = queue.Queue()

        self._status_label = tk.Label(self._root, text="Mode: EN", font=("Segoe UI", 11, "bold"))
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

    def run(self) -> None:
        self._root.mainloop()

    def _drain_queue(self) -> None:
        # 批次取出待渲染狀態，降低 UI 閃爍。
        while True:
            try:
                state = self._state_queue.get_nowait()
            except queue.Empty:
                break
            self._render(state)
        self._root.after(33, self._drain_queue)

    def _render(self, state: CompositionState) -> None:
        # 以最新狀態更新標籤與候選列表。
        self._status_label.config(text=f"Mode: {state.status}")
        self._buffer_label.config(text=f"Buffer: {state.buffer}")
        self._debug_label.config(text=f"Debug: {state.debug_message}")

        self._candidate_box.delete(0, tk.END)
        for idx, item in enumerate(state.candidates, start=1):
            cursor = ">" if (idx - 1) == state.selected_index else " "
            line = f"{cursor} {idx}. {item.text} | score={item.final_score:.3f} | src={item.source}"
            self._candidate_box.insert(tk.END, line)
