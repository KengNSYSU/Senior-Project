from __future__ import annotations
"""IME 核心狀態機：自動判斷注音詞段並轉換為中文。"""

import threading
from typing import Callable

from .contracts import CommitAction, CompositionState, InferenceProvider, CandidateItem
from .worker import InferenceWorker


class ImeCoreEngine:
    def __init__(self, inference_provider: InferenceProvider, on_state_changed: Callable[[], None] | None = None) -> None:
        # 透過注入方式接推理器，保持核心可替換與可測試。
        self._provider = inference_provider
        self._on_state_changed = on_state_changed
        self._lock = threading.RLock()
        
        # 初始化非同步推理工作器
        self._worker = InferenceWorker(self._provider, self._on_inference_complete)
        
        self._state = CompositionState(
            status="AUTO",
            debug_message="就緒：自動判斷注音詞段",
        )

    @property
    def state(self) -> CompositionState:
        with self._lock:
            return self._state

    def handle_key(self, key: str) -> CommitAction | None:
        """根據按鍵類型分派給對應的處理方法。"""
        if key == "esc":
            return self._handle_escape()
        if key == "backspace":
            return self._handle_backspace()
        if key in ("up", "down"):
            return self._handle_navigation(key)
        if key == "enter":
            return self._handle_commit()
        if key == "space" or self._is_composition_key(key):
            return self._handle_composition(key)

        # 忽略所有其他按鍵
        return self._handle_ignored_key(key)

    def _handle_escape(self) -> None:
        self._state.debug_message = "Esc：清空組字"
        self._clear_composition()
        if self._on_state_changed:
            self._on_state_changed()
        return None

    def _handle_backspace(self) -> None:
        if self._state.buffer:
            self._state.buffer = self._state.buffer[:-1]
            self._refresh_candidates()
            self._state.debug_message = (
                f"Backspace：buffer='{self._state.buffer}'，候選={len(self._state.candidates)}"
            )
        else:
            self._state.debug_message = "Backspace：buffer 已是空"
        if self._on_state_changed:
            self._on_state_changed()
        return None

    def _handle_navigation(self, key: str) -> None:
        if not self._state.candidates:
            return None
        # 在候選清單中循環移動游標。
        step = -1 if key == "up" else 1
        total = len(self._state.candidates)
        self._state.selected_index = (self._state.selected_index + step) % total
        selected = self._state.candidates[self._state.selected_index].text
        self._state.debug_message = f"{key}：選擇候選 -> {selected}"
        if self._on_state_changed:
            self._on_state_changed()
        return None

    def _handle_commit(self) -> CommitAction | None:
        # 僅 Enter 作為提交鍵，避免與一聲（space）衝突。
        # 在提交前，等待當前最新的背景推理任務完成 (最長等待 0.8s)
        self._worker.wait_for_completion(timeout=0.8)

        if self._state.candidates:
            # Enter 作為提交鍵，不預設多刪 1 碼以免刪除正常字元。
            return self._commit_selected(trigger_consumed=True)

        if self._state.buffer:
            self._state.debug_message = "enter：沒有候選，清空 buffer"
        else:
            self._state.debug_message = "enter：buffer 已是空"
        self._clear_composition()
        if self._on_state_changed:
            self._on_state_changed()
        return None

    def _handle_composition(self, key: str) -> None:
        # 空白鍵在此模式下代表一聲，寫入空格符號而非提交。
        # 其他可印出字元則為組字鍵。
        char = " " if key == "space" else key
        self._state.buffer += char
        self._refresh_candidates()
        self._state.debug_message = (
            f"輸入 '{key}'：buffer='{self._state.buffer}'，候選={len(self._state.candidates)}"
        )
        if self._on_state_changed:
            self._on_state_changed()
        return None

    def _handle_ignored_key(self, key: str) -> None:
        # 非組字鍵會中斷目前詞段。
        self._state.debug_message = f"忽略鍵 '{key}'：非組字鍵"
        self._clear_composition()
        if self._on_state_changed:
            self._on_state_changed()
        return None

    def _commit_selected(self, trigger_consumed: bool) -> CommitAction | None:
        # 若無候選則回退提交原始緩衝。
        if not self._state.buffer:
            self._state.debug_message = "提交失敗：buffer 為空"
            return None

        text = self._state.buffer
        if self._state.candidates:
            text = self._state.candidates[self._state.selected_index].text

        replace_len = len(self._state.buffer)

        trigger = "enter" if trigger_consumed else "space"
        self._state.debug_message = f"{trigger} 提交：'{text}'，replace_len={replace_len}"
        self._clear_composition()
        return CommitAction(text=text, replace_len=replace_len)

    def _is_composition_key(self, key: str) -> bool:
        if len(key) != 1:
            return False
        # 將所有可印出字元視為組字鍵（字母、數字、標點等）。
        return key.isprintable()

    def _refresh_candidates(self) -> None:
        buffer = self._state.buffer
        if not buffer:
            self._state.candidates = []
            self._state.selected_index = 0
            # 確保 worker 同步標記為完成狀態
            with self._lock:
                self._worker._event.set()
            return

        # 異步提交給背景工作器，不阻塞鍵盤執行緒
        self._worker.submit(buffer)

    def _on_inference_complete(self, buffer: str, candidates: list[CandidateItem]) -> None:
        """非同步推理完成的回調函數。"""
        with self._lock:
            # 只有當前 buffer 依然與完成推理的 buffer 一致時才更新候選清單
            if self._state.buffer == buffer:
                self._state.candidates = candidates
                self._state.selected_index = 0
                self._state.debug_message = (
                    f"非同步推理完成：buffer='{buffer}'，候選={len(candidates)}"
                )
                if self._on_state_changed:
                    self._on_state_changed()

    def _clear_composition(self, clear_debug: bool = False) -> None:
        self._state.buffer = ""
        self._state.candidates = []
        self._state.selected_index = 0
        # 清空時將 worker 狀態重設為 Idle
        with self._lock:
            self._worker._event.set()
        if clear_debug:
            self._state.debug_message = ""

