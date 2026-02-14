"""判定結果エンティティモジュール."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class InterestLabel(StrEnum):
    """関心度ラベル.

    Attributes:
        ACT_NOW: 今すぐ読むべき
        THINK: 設計判断に役立つ
        FYI: 知っておくとよい
        IGNORE: 関心外
    """

    ACT_NOW = "ACT_NOW"
    THINK = "THINK"
    FYI = "FYI"
    IGNORE = "IGNORE"


class BuzzLabel(StrEnum):
    """話題性ラベル.

    Attributes:
        HIGH: 非常に話題
        MID: 中程度の話題
        LOW: 低い話題性
    """

    HIGH = "HIGH"
    MID = "MID"
    LOW = "LOW"


@dataclass
class JudgmentResult:
    """LLM判定結果.

    LLMによる記事判定の結果を表す.

    Attributes:
        url: 記事URL（キャッシュキー）
        title: 記事タイトル
        description: 記事の概要（最大800文字）
        interest_label: 関心度ラベル
        buzz_label: 話題性ラベル
        confidence: 信頼度（0.0-1.0）
        reason: 判定理由（最大200文字）
        model_id: 使用したLLMモデルID
        judged_at: 判定日時（UTC）
        tags: 記事タグ（例: ["Kotlin", "Claude"]）
        published_at: 記事の公開日時（UTC）
    """

    url: str
    title: str
    description: str
    interest_label: InterestLabel
    buzz_label: BuzzLabel
    confidence: float
    reason: str
    model_id: str
    judged_at: datetime
    published_at: datetime
    tags: list[str] = field(default_factory=list)
