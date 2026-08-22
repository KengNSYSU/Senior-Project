from __future__ import annotations
"""推理模組：本機模型推理。"""

import logging
from typing import List

from .contracts import CandidateItem, InferenceProvider


class LocalModelInferenceProvider(InferenceProvider):
    """直接呼叫本機 PyTorch 模型 (predictor.py) 的推理提供者。"""

    def __init__(self) -> None:
        # 在此匯入 predictor，確保相依性與環境準備就緒。
        import os
        import sys

        # 取得 src 的絕對路徑，並加入 sys.path，
        # 使 predictor.py 內部的直接 import（如 from transformer_main import ...）能正確解析。
        src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)

        from .. import predictor

        self.predictor = predictor
        if not self.predictor.initialize():
            raise RuntimeError("本機模型初始化失敗：找不到模型權重檔！")

    def infer(self, buffer: str, top_k: int = 9) -> List[CandidateItem]:
        if not buffer:
            return []

        try:
            # 呼叫 predictor 取得預測字串 (Greedy Search, 單一結果)
            predicted_text = self.predictor.predict(buffer)
            
            if predicted_text:
                return [
                    CandidateItem(
                        text=predicted_text,
                        final_score=1.0,
                        source="local-pytorch",
                        model_score=1.0,
                        rule_score=0.0,
                    )
                ]
            return []
        except Exception as e:
            logging.error(f"Local model inference error: {e}", exc_info=True)
            return []
