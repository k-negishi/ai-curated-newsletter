"""Buzzスコア計算サービスモジュール."""

from collections import Counter

from src.models.article import Article
from src.models.buzz_score import BuzzScore
from src.models.interest_profile import InterestProfile
from src.models.source_config import AuthorityLevel
from src.repositories.source_master import SourceMaster
from src.services.social_proof.multi_source_social_proof_fetcher import (
    MultiSourceSocialProofFetcher,
)
from src.shared.logging.logger import get_logger
from src.shared.utils.date_utils import now_utc

logger = get_logger(__name__)


class BuzzScorer:
    """Buzzスコア計算サービス（5要素統合版）.

    スコア計算式:
    - recency_score = max(100 - (days_old * 10), 0)
    - consensus_score = min(source_count * 20, 100)
    - social_proof_score = 4指標統合スコア（yamadashy, Hatena, Zenn, Qiita）（0-100）
    - interest_score = InterestProfileとのマッチング度（0-100）
    - authority_score = authority_levelに応じたスコア（0, 50, 80, 100）
    - total_score = (recency × 0.20) + (consensus × 0.15) + (social_proof × 0.35)
                  + (interest × 0.25) + (authority × 0.05)
    """

    # 重み配分（SNS反応を重視）
    WEIGHT_RECENCY = 0.20
    WEIGHT_CONSENSUS = 0.15
    WEIGHT_SOCIAL_PROOF = 0.35
    WEIGHT_INTEREST = 0.25
    WEIGHT_AUTHORITY = 0.05

    def __init__(
        self,
        interest_profile: InterestProfile,
        source_master: SourceMaster,
        social_proof_fetcher: MultiSourceSocialProofFetcher,
    ) -> None:
        """Buzzスコア計算サービスを初期化する.

        Args:
            interest_profile: 興味プロファイル
            source_master: 収集元マスタ
            social_proof_fetcher: MultiSourceSocialProof取得サービス（4指標統合）
        """
        self._interest_profile = interest_profile
        self._source_master = source_master
        self._social_proof_fetcher = social_proof_fetcher

    async def calculate_scores(self, articles: list[Article]) -> dict[str, BuzzScore]:
        """全記事のBuzzスコアを計算する（非同期版）.

        Args:
            articles: 重複排除済み記事のリスト

        Returns:
            スコア辞書（normalized_url -> BuzzScore）
        """
        logger.info("buzz_scoring_start", article_count=len(articles))

        # 前処理: URL出現回数を集計
        url_counts: dict[str, int] = Counter(article.normalized_url for article in articles)

        # SocialProof（4指標統合スコア）を一括取得
        social_proof_scores = await self._social_proof_fetcher.fetch_batch(articles)

        # 各記事のスコアを計算
        scores: dict[str, BuzzScore] = {}

        for article in articles:
            recency_score = self._calculate_recency_score(article)
            consensus_score = self._calculate_consensus_score(article.normalized_url, url_counts)
            social_proof_score = social_proof_scores.get(article.url, 20.0)  # デフォルト20.0
            interest_score = self._calculate_interest_score(article)
            authority_score = self._calculate_authority_score(article.source_name)

            total_score = self._calculate_total_score(
                recency_score,
                consensus_score,
                social_proof_score,
                interest_score,
                authority_score,
            )

            buzz_score = BuzzScore(
                url=article.url,
                recency_score=recency_score,
                consensus_score=consensus_score,
                social_proof_score=social_proof_score,
                interest_score=interest_score,
                authority_score=authority_score,
                source_count=url_counts.get(article.normalized_url, 1),
                social_proof_count=0,  # 4指標統合版では個別カウント不要
                total_score=total_score,
            )

            scores[article.normalized_url] = buzz_score

            logger.debug(
                "buzz_score_calculated",
                url=article.url,
                total_score=total_score,
                recency=recency_score,
                consensus=consensus_score,
                social_proof=social_proof_score,
                interest=interest_score,
                authority=authority_score,
            )

        logger.info("buzz_scoring_complete", score_count=len(scores))

        return scores

    def _calculate_recency_score(self, article: Article) -> float:
        """Recency（鮮度）スコアを計算する.

        Args:
            article: 記事

        Returns:
            スコア（0-100）
        """
        now = now_utc()
        days_old = (now - article.published_at).days
        return max(100.0 - (days_old * 10.0), 0.0)

    def _calculate_consensus_score(self, normalized_url: str, url_counts: dict[str, int]) -> float:
        """Consensus（複数ソース出現）スコアを計算する.

        Args:
            normalized_url: 正規化URL
            url_counts: URL出現回数の辞書

        Returns:
            スコア（0-100）
        """
        source_count = url_counts.get(normalized_url, 1)
        return min(source_count * 20.0, 100.0)

    def _calculate_interest_score(self, article: Article) -> float:
        """Interest（興味との一致度）スコアを計算する（5段階版）.

        Args:
            article: 記事

        Returns:
            スコア（0-100）
        """
        text = f"{article.title} {article.description}".lower()

        # トピックレベルとスコアのマッピング
        topic_levels = [
            (self._interest_profile.max_interest, 100.0),
            (self._interest_profile.high_interest, 85.0),
            (self._interest_profile.medium_interest, 70.0),
            (self._interest_profile.low_interest, 50.0),
            (self._interest_profile.ignore_interest, 0.0),
        ]

        for topics, score in topic_levels:
            for topic in topics:
                if self._match_topic(topic, text):
                    return score

        # いずれにも一致しない場合はデフォルト（低関心相当）
        return 50.0

    def _match_topic(self, topic: str, text: str) -> bool:
        """トピックとテキストのマッチング判定.

        Args:
            topic: トピック文字列（例: "AI/ML（大規模言語モデル、機械学習基盤）"）
            text: 記事タイトル+概要の結合テキスト

        Returns:
            マッチングした場合True
        """
        # トピックからキーワードを抽出（括弧内・カンマ区切り）
        keywords = []

        # 括弧外のメインキーワード
        main = topic.split("（")[0].split("(")[0].strip()
        keywords.append(main.lower())

        # 括弧内のサブキーワード
        if "（" in topic or "(" in topic:
            sub = topic.split("（")[-1].split("(")[-1].split("）")[0].split(")")[0]
            keywords.extend([k.strip().lower() for k in sub.split("、") if k.strip()])
            keywords.extend([k.strip().lower() for k in sub.split(",") if k.strip()])

        # いずれかのキーワードが含まれればマッチ
        return any(keyword in text for keyword in keywords if keyword)

    def _calculate_authority_score(self, source_name: str) -> float:
        """Authority（公式補正）スコアを計算する.

        Args:
            source_name: ソース名

        Returns:
            スコア（0-100）
        """
        # SourceMasterからsource_nameに対応するSourceConfigを取得
        sources = self._source_master.get_all_sources()
        source_config = next((s for s in sources if s.name == source_name), None)

        if source_config is None:
            return 0.0

        # authority_levelに応じたスコア
        authority_level = source_config.authority_level

        if authority_level == AuthorityLevel.OFFICIAL:
            return 100.0
        if authority_level == AuthorityLevel.HIGH:
            return 80.0
        if authority_level == AuthorityLevel.MEDIUM:
            return 50.0
        # LOW or 未設定
        return 0.0

    def _calculate_total_score(
        self,
        recency: float,
        consensus: float,
        social_proof: float,
        interest: float,
        authority: float,
    ) -> float:
        """総合Buzzスコアを計算する（重み付け合算）.

        Args:
            recency: 鮮度スコア
            consensus: Consensusスコア
            social_proof: SocialProofスコア
            interest: Interestスコア
            authority: Authorityスコア

        Returns:
            総合スコア（0-100）
        """
        return (
            (recency * self.WEIGHT_RECENCY)
            + (consensus * self.WEIGHT_CONSENSUS)
            + (social_proof * self.WEIGHT_SOCIAL_PROOF)
            + (interest * self.WEIGHT_INTEREST)
            + (authority * self.WEIGHT_AUTHORITY)
        )
