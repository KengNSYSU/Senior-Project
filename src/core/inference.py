from __future__ import annotations
"""推理模組：呼叫遠端模型。"""

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import List

from .contracts import CandidateItem, InferenceProvider


@dataclass
class InferenceConfig:
    # 遠端推理端點。
    remote_endpoint: str = ""
    # 呼叫遠端模型超時秒數（偏短，確保互動流暢）。
    timeout_seconds: float = 0.15


class HybridInferenceProvider(InferenceProvider):
    """模型優先的推理提供者。

    遠端回應格式（JSON）：
    {
      "candidates": [{"text": "你", "score": 0.92}, ...]
    }
    """

    def __init__(self, config: InferenceConfig) -> None:
        self._config = config

    def infer(self, buffer: str, top_k: int = 9) -> List[CandidateItem]:
        if not buffer:
            return []

        return self._infer_remote(buffer, top_k)

    def _infer_remote(self, buffer: str, top_k: int) -> List[CandidateItem]:
        if not self._config.remote_endpoint:
            return []

        payload = json.dumps({"buffer": buffer, "top_k": top_k}).encode("utf-8")
        request = urllib.request.Request(
            self._config.remote_endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self._config.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            logging.error(f"Remote inference failed: {e}", exc_info=True)
            return []

        raw_candidates = data.get("candidates", [])
        results: List[CandidateItem] = []
        for item in raw_candidates[:top_k]:
            text = str(item.get("text", "")).strip()
            if not text:
                continue
            model_score = float(item.get("score", 0.0))
            results.append(
                CandidateItem(
                    text=text,
                    final_score=model_score,
                    source="remote-model",
                    model_score=model_score,
                    rule_score=0.0,
                )
            )
        return results


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
        self.predictor.initialize(base_path=src_dir)

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
