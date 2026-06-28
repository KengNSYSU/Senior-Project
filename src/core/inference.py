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
        from .. import predictor

        # 取得 src 的絕對路徑
        # __file__ -> .../src/core/inference.py
        # os.path.dirname -> .../src/core
        # os.path.dirname -> .../src
        src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.predictor = predictor
        # 將路徑作為參數傳入，而不是改變工作目錄
        if not self.predictor.initialize(base_path=src_dir):
            raise RuntimeError("本機模型初始化失敗：找不到模型權重檔 transcoder_v1.pth！")

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
