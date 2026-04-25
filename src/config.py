from __future__ import annotations
"""應用設定載入：集中管理詞典與模型端點來源。"""

import os
from dataclasses import dataclass


@dataclass
class AppConfig:
    # 本地詞典（JSON）路徑。
    lexicon_path: str
    # 遠端模型推理端點（可留空）。
    remote_model_endpoint: str


def load_config() -> AppConfig:
    # 以專案根目錄推導預設資源路徑。
    project_root = os.path.dirname(os.path.dirname(__file__))

    default_lexicon = os.path.join(project_root, "data", "lexicon.json")

    return AppConfig(
        # 環境變數可覆寫預設詞典路徑。
        lexicon_path=os.getenv("SP_IME_LEXICON", default_lexicon),
        # 環境變數可指定遠端推理 API。
        remote_model_endpoint=os.getenv("SP_IME_MODEL_ENDPOINT", ""),
    )
