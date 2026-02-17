"""Buzzスコアエンティティモジュール."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from src.models.judgment import BuzzLabel


@dataclass
class BuzzScore:
    """話題性スコア（非LLM計算）.

    記事の話題性を4つの要素から定量化したスコア.

    Attributes:
        url: 記事URL
        recency_score: 鮮度スコア
        social_proof_score: 外部反応スコア（はてブ数など）
        interest_score: 興味との一致度スコア
        authority_score: 公式補正スコア
        social_proof_count: 外部反応数（はてブ数）
        total_score: 総合Buzzスコア（0-100）
    """

    _HIGH_THRESHOLD: ClassVar[float] = 70.0
    _MID_THRESHOLD: ClassVar[float] = 40.0
    # BuzzScorerの重み定数（interest成分の除外に使用）
    _WEIGHT_INTEREST: ClassVar[float] = 0.35
    # external_buzz正規化の分母（interest以外の重みの合計）
    _MAX_EXTERNAL_BUZZ_RAW: ClassVar[float] = 1.0 - _WEIGHT_INTEREST

    url: str
    # 各要素スコア
    recency_score: float
    social_proof_score: float
    interest_score: float
    authority_score: float
    # メタデータ
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

    @property
    def external_buzz(self) -> float:
        """interest成分を除外した外部話題性スコア（0-100正規化）.

        total_scoreからinterest_scoreの寄与分を除去し、
        残りのスコアを0-100スケールに正規化する。

        Returns:
            外部話題性スコア（0.0-100.0）
        """
        raw = self.total_score - self.interest_score * self._WEIGHT_INTEREST
        return min(max(raw, 0.0) / self._MAX_EXTERNAL_BUZZ_RAW, 100.0)
