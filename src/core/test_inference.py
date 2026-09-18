from __future__ import annotations
"""測試推理模組：僅用於驗證逐字輸入與結果顯示。"""

from typing import List

from .contracts import CandidateItem, InferenceProvider


class SimpleTestInferenceProvider(InferenceProvider):
    """簡易測試推理提供者：驗證逐字輸入能送到模型並顯示結果。"""

    _TARGET_INPUT = "ji3lovesu3"
    _TARGET_OUTPUT = "我love你"

    def infer(self, buffer: str, top_k: int = 9) -> List[CandidateItem]:
        # 空緩衝不回傳候選。
        if not buffer:
            return []

        # 只有一個功能：完整輸入時回傳指定結果；否則回傳目前 buffer。
        if buffer == self._TARGET_INPUT:
            result = self._TARGET_OUTPUT
        else:
            result = buffer

        return [
            CandidateItem(
                text=result,
                final_score=1.0,
                source="test-hardcoded",
                model_score=1.0,
                rule_score=1.0,
            )
        ]
