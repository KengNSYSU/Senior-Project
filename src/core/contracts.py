from __future__ import annotations
"""核心資料契約：定義輸入法核心與各 Adapter 的共享介面。"""

from dataclasses import dataclass, field
from typing import List, Protocol


@dataclass
class CandidateItem:
    # 候選文字內容。
    text: str
    # 最終排序分數（可由模型分數與規則分數融合）。
    final_score: float
    # 候選來源標記（例如 remote-model / local-fallback）。
    source: str
    # 模型分數，便於分析與除錯。
    model_score: float = 0.0
    # 規則分數，便於分析與除錯。
    rule_score: float = 0.0


@dataclass
class CompositionState:
    # 是否處於輸入法啟用狀態。
    is_active: bool = False
    # 目前組字緩衝內容（尚未提交）。
    buffer: str = ""
    # 目前候選清單。
    candidates: List[CandidateItem] = field(default_factory=list)
    # 目前選中的候選索引。
    selected_index: int = 0
    # 目前模式顯示字串（例如 AUTO）。
    status: str = "EN"
    # 偵錯訊息（最近一次決策原因）。
    debug_message: str = ""


@dataclass
class CommitAction:
    # 要提交到前景應用的最終文字。
    text: str
    # 提交前需刪除的原始組字長度。
    replace_len: int


class InferenceProvider(Protocol):
    def infer(self, buffer: str, top_k: int = 9) -> List[CandidateItem]:
        ...


class OverlayPresenter(Protocol):
    def render(self, state: CompositionState) -> None:
        ...


class OutputCommitter(Protocol):
    def commit_text(self, text: str, replace_len: int = 0) -> None:
        ...
