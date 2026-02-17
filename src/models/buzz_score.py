"""Buzzスコアエンティティモジュール."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from src.models.judgment import BuzzLabel


@dataclass
class BuzzScore:
    """話題性スコア（非LLM計算）.

    記事の話題性を5つの要素から定量化したスコア.

    Attributes:
        url: 記事URL
        # 各要素のスコア（0-100）
        recency_score: 鮮度スコア
        consensus_score: 複数ソース出現スコア
        social_proof_score: 外部反応スコア（はてブ数など）
        interest_score: 興味との一致度スコア
        authority_score: 公式補正スコア
        # メタデータ
        source_count: 複数ソース出現回数（Consensus計算の元データ）
        social_proof_count: 外部反応数（はてブ数）
        # 総合スコア
        total_score: 総合Buzzスコア（0-100）
    """

    _HIGH_THRESHOLD: ClassVar[float] = 70.0
    _MID_THRESHOLD: ClassVar[float] = 40.0

    url: str
    # 各要素スコア
    recency_score: float
    consensus_score: float
    social_proof_score: float
    interest_score: float
    authority_score: float
    # メタデータ
    source_count: int
    social_proof_count: int
    # 総合スコア
    total_score: float

    def to_buzz_label(self) -> BuzzLabel:
        """total_scoreからBuzzLabelに変換する.

        閾値:
        - HIGH: total_score >= 70.0
        - MID: total_score >= 40.0
        - LOW: total_score < 40.0

        Returns:
            BuzzLabel
        """
        if self.total_score >= self._HIGH_THRESHOLD:
            return BuzzLabel.HIGH
        if self.total_score >= self._MID_THRESHOLD:
            return BuzzLabel.MID
        return BuzzLabel.LOW
