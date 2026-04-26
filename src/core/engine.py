from __future__ import annotations
"""IME 核心狀態機：自動判斷注音詞段並轉換為中文。"""

from dataclasses import replace

from .contracts import CommitAction, CompositionState, InferenceProvider


class ImeCoreEngine:
    # 注音專用鍵（不含 a-z，因 a-z 與英文共用，需搭配規則判斷）。
    _ZHUYIN_MARKER_KEYS = set("125890-;,./3467")

    def __init__(self, inference_provider: InferenceProvider) -> None:
        # 透過注入方式接推理器，保持核心可替換與可測試。
        self._provider = inference_provider
        self._state = CompositionState(
            is_active=True,
            status="AUTO",
            debug_message="就緒：自動判斷注音詞段",
        )

    @property
    def state(self) -> CompositionState:
        return self._state

    def clear(self) -> CompositionState:
        # 主動清空組字緩衝與候選清單。
        self._clear_composition(clear_debug=True)
        return replace(self._state)

    def handle_key(self, key: str) -> CommitAction | None:
        if key == "esc":
            self._state.debug_message = "Esc：清空組字"
            self._clear_composition()
            return None

        if key == "backspace":
            if self._state.buffer:
                self._state.buffer = self._state.buffer[:-1]
                self._refresh_candidates()
                self._state.debug_message = (
                    f"Backspace：buffer='{self._state.buffer}'，候選={len(self._state.candidates)}"
                )
            else:
                self._state.debug_message = "Backspace：buffer 已是空"
            return None

        if key in ("up", "down") and self._state.candidates:
            # 在候選清單中循環移動游標。
            step = -1 if key == "up" else 1
            total = len(self._state.candidates)
            self._state.selected_index = (self._state.selected_index + step) % total
            selected = self._state.candidates[self._state.selected_index].text
            self._state.debug_message = f"{key}：選擇候選 -> {selected}"
            return None

        if key == "space":
            # 空白鍵在此模式下代表一聲，寫入鍵序而非提交。
            self._state.buffer += "1"
            self._refresh_candidates()
            self._state.debug_message = (
                f"輸入 'space(一聲)'：buffer='{self._state.buffer}'，候選={len(self._state.candidates)}"
            )
            return None

        if key == "enter":
            # 僅 Enter 作為提交鍵，避免與一聲（space）衝突。
            if self._should_convert_buffer(self._state.buffer):
                # Enter 常會先在輸入框產生換行，需多刪 1 碼避免殘留前字。
                return self._commit_selected(trigger_consumed=True)
            self._state.debug_message = (
                f"enter：未轉換（buffer='{self._state.buffer}'，候選={len(self._state.candidates)}）"
            )
            self._clear_composition()
            return None

        # 數字鍵在注音鍵盤中同時承擔聲調/韻母，不作候選快捷鍵。

        if self._is_composition_key(key):
            # 累積詞段鍵序，提供模型判斷是否為注音輸入。
            self._state.buffer += key
            self._refresh_candidates()
            self._state.debug_message = (
                f"輸入 '{key}'：buffer='{self._state.buffer}'，候選={len(self._state.candidates)}"
            )
            return None

        # 非組字鍵會中斷目前詞段。
        self._state.debug_message = f"忽略鍵 '{key}'：非組字鍵"
        self._clear_composition()
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
        if trigger_consumed:
            replace_len += 1

        trigger = "space" if trigger_consumed else "enter"
        self._state.debug_message = f"{trigger} 提交：'{text}'，replace_len={replace_len}"
        self._clear_composition()
        return CommitAction(text=text, replace_len=replace_len)

    def _is_composition_key(self, key: str) -> bool:
        if len(key) != 1:
            return False
        return key.isalpha() or key in self._ZHUYIN_MARKER_KEYS

    def _should_convert_buffer(self, buffer: str) -> bool:
        if not buffer:
            return False
        # 包含注音專用鍵時一定轉換；或已有候選時也允許轉換。
        if any(ch in self._ZHUYIN_MARKER_KEYS for ch in buffer):
            return True
        return bool(self._state.candidates)

    def _refresh_candidates(self) -> None:
        # 每次緩衝變動即重新推理候選。
        self._state.candidates = self._provider.infer(self._state.buffer, top_k=9)
        self._state.selected_index = 0

    def _clear_composition(self, clear_debug: bool = False) -> None:
        self._state.buffer = ""
        self._state.candidates = []
        self._state.selected_index = 0
        if clear_debug:
            self._state.debug_message = ""
