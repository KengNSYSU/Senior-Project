from __future__ import annotations
"""推理模組：優先呼叫遠端模型，失敗時退回本地詞典評分。"""

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Dict, List

from .contracts import CandidateItem, InferenceProvider


@dataclass
class InferenceConfig:
    # 本地詞典路徑。
    lexicon_path: str
    # 遠端推理端點，留空代表僅使用本地 fallback。
    remote_endpoint: str = ""
    # 呼叫遠端模型超時秒數（偏短，確保互動流暢）。
    timeout_seconds: float = 0.15


class HybridInferenceProvider(InferenceProvider):
    """模型優先的推理提供者，含本地詞典退回策略。

    遠端回應格式（JSON）：
    {
      "candidates": [{"text": "你", "score": 0.92}, ...]
    }
    """

    def __init__(self, config: InferenceConfig) -> None:
        self._config = config
        self._lexicon = self._load_lexicon(config.lexicon_path)

    def infer(self, buffer: str, top_k: int = 9) -> List[CandidateItem]:
        # 先嘗試遠端模型，若失敗再回退本地詞典。
        if not buffer:
            return []

        remote = self._infer_remote(buffer, top_k)
        if remote:
            return remote

        return self._infer_local(buffer, top_k)

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
        except (urllib.error.URLError, TimeoutError, ValueError):
            # 網路/格式異常時直接回退本地推理。
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

    def _infer_local(self, buffer: str, top_k: int) -> List[CandidateItem]:
        # 先精準命中，再退為前綴命中。
        matches = self._lexicon.get(buffer, [])

        if not matches:
            prefix_matches: List[str] = []
            for key, values in self._lexicon.items():
                if key.startswith(buffer):
                    prefix_matches.extend(values)
            matches = prefix_matches

        deduped: List[str] = []
        seen = set()
        for text in matches:
            if text not in seen:
                deduped.append(text)
                seen.add(text)

        results: List[CandidateItem] = []
        for idx, text in enumerate(deduped[:top_k]):
            # 規則分數隨順位遞減，並與簡化模型分數融合。
            rule_score = 1.0 / (idx + 1)
            model_score = self._pseudo_model_score(buffer, text)
            final_score = (0.7 * model_score) + (0.3 * rule_score)
            results.append(
                CandidateItem(
                    text=text,
                    final_score=final_score,
                    source="local-fallback",
                    model_score=model_score,
                    rule_score=rule_score,
                )
            )

        return sorted(results, key=lambda x: x.final_score, reverse=True)

    @staticmethod
    def _pseudo_model_score(buffer: str, text: str) -> float:
        # 本地佔位評分：後續可替換為真實模型推理路徑。
        return min(1.0, (len(buffer) * 0.15) + (len(text) * 0.1))

    @staticmethod
    def _load_lexicon(path: str) -> Dict[str, List[str]]:
        # 讀取並清洗詞典，確保輸出型別固定為 Dict[str, List[str]]。
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, dict):
            return {}

        cleaned: Dict[str, List[str]] = {}
        for key, value in data.items():
            if isinstance(value, list):
                normalized_key = str(key).strip().lower()
                if not normalized_key:
                    continue
                normalized_values = [str(item).strip() for item in value if str(item).strip()]
                if normalized_values:
                    cleaned[normalized_key] = normalized_values
        return cleaned
