from __future__ import annotations
"""應用設定載入：集中管理詞典與模型端點來源。"""

import os
from dataclasses import dataclass


@dataclass
class AppConfig:
    # 遠端模型推理端點（可留空）。
    remote_model_endpoint: str


def load_config() -> AppConfig:
    return AppConfig(
        # 環境變數可指定遠端推理 API。
        remote_model_endpoint=os.getenv("SP_IME_MODEL_ENDPOINT", ""),
    )
