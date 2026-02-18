"""MultiSourceSocialProofFetcherモジュール."""

import asyncio
from urllib.parse import urlparse

from src.models.article import Article
from src.services.social_proof.hatena_count_fetcher import HatenaCountFetcher
from src.services.social_proof.qiita_rank_fetcher import QiitaRankFetcher
from src.services.social_proof.yamadashy_signal_fetcher import YamadashySignalFetcher
from src.services.social_proof.zenn_like_fetcher import ZennLikeFetcher
from src.shared.logging.logger import get_logger

logger = get_logger(__name__)


class MultiSourceSocialProofFetcher:
    """複数情報源からSocialProofスコアを統合取得するサービス.

    4つの情報源（yamadashy, Hatena, Zenn, Qiita）からスコアを取得し、
    URLドメインに基づく適用重み正規化で統合スコアを算出する。

    ドメイン別の適用指標:
    - zenn.dev  → Y + H + Z（Qは除外）→ 適用重み合計 0.85
    - qiita.com → Y + H + Q（Zは除外）→ 適用重み合計 0.65
    - その他    → Y + H（Z, Qは除外）→ 適用重み合計 0.50

    統合計算式: S = 適用指標の加重合計 / 適用重み合計

    Attributes:
        _yamadashy_fetcher: yamadashy掲載シグナル取得
        _hatena_fetcher: Hatenaブックマーク数取得
        _zenn_fetcher: Zenn like数取得
        _qiita_fetcher: Qiita順位取得
    """

    # 各指標の重み
    WEIGHT_YAMADASHY = 0.05
    WEIGHT_HATENA = 0.45
    WEIGHT_ZENN = 0.35
    WEIGHT_QIITA = 0.15

    # デフォルトスコア（全欠損時）
    DEFAULT_SCORE = 20.0

    def __init__(
        self,
        yamadashy_fetcher: YamadashySignalFetcher | None = None,
        hatena_fetcher: HatenaCountFetcher | None = None,
        zenn_fetcher: ZennLikeFetcher | None = None,
        qiita_fetcher: QiitaRankFetcher | None = None,
    ) -> None:
        """MultiSourceSocialProofFetcherを初期化する.

        Args:
            yamadashy_fetcher: yamadashy掲載シグナル取得（デフォルト: 新規作成）
            hatena_fetcher: Hatenaブックマーク数取得（デフォルト: 新規作成）
            zenn_fetcher: Zenn like数取得（デフォルト: 新規作成）
            qiita_fetcher: Qiita順位取得（デフォルト: 新規作成）
        """
        self._yamadashy_fetcher = (
            yamadashy_fetcher if yamadashy_fetcher is not None else YamadashySignalFetcher()
        )
        self._hatena_fetcher = (
            hatena_fetcher if hatena_fetcher is not None else HatenaCountFetcher()
        )
        self._zenn_fetcher = zenn_fetcher if zenn_fetcher is not None else ZennLikeFetcher()
        self._qiita_fetcher = qiita_fetcher if qiita_fetcher is not None else QiitaRankFetcher()

    async def fetch_batch(self, articles: list[Article]) -> dict[str, float]:
        """複数記事のSocialProofスコアを一括取得する.

        Args:
            articles: 記事リスト

        Returns:
            URLをキーとするSocialProofスコア（0-100）の辞書
        """
        if not articles:
            return {}

        logger.debug("multi_source_social_proof_fetch_start", article_count=len(articles))

        urls = [article.url for article in articles]

        # 4つの情報源を並列で取得
        yamadashy_task = self._yamadashy_fetcher.fetch_signals(urls)
        hatena_task = self._hatena_fetcher.fetch_batch(urls)
        zenn_task = self._zenn_fetcher.fetch_batch(urls)
        qiita_task = self._qiita_fetcher.fetch_batch(urls)

        results = await asyncio.gather(
            yamadashy_task,
            hatena_task,
            zenn_task,
            qiita_task,
            return_exceptions=True,
        )

        # 結果を展開
        yamadashy_signals = results[0] if not isinstance(results[0], BaseException) else {}
        hatena_scores = results[1] if not isinstance(results[1], BaseException) else {}
        zenn_scores = results[2] if not isinstance(results[2], BaseException) else {}
        qiita_scores = results[3] if not isinstance(results[3], BaseException) else {}

        # 統合スコアを計算
        integrated_scores = self._calculate_integrated_scores(
            urls,
            yamadashy_signals,
            hatena_scores,
            zenn_scores,
            qiita_scores,
        )

        logger.info(
            "multi_source_social_proof_fetch_complete",
            article_count=len(articles),
            success_count=len(integrated_scores),
        )

        return integrated_scores

    def _calculate_integrated_scores(
        self,
        urls: list[str],
        yamadashy_signals: dict[str, int],
        hatena_scores: dict[str, float],
        zenn_scores: dict[str, float],
        qiita_scores: dict[str, float],
    ) -> dict[str, float]:
        """4指標をURLドメインに基づく適用重み正規化で統合する.

        URLのドメインに応じて適用可能な指標のみを使い、
        適用重みの合計で正規化することで、ドメイン間のスコアを公平に比較する。

        Args:
            urls: 記事URLリスト
            yamadashy_signals: yamadashy掲載シグナル（100 or 0）
            hatena_scores: Hatenaスコア（0-100）
            zenn_scores: Zennスコア（0-100）
            qiita_scores: Qiitaスコア（0-100）

        Returns:
            URLをキーとする統合スコア（0-100）の辞書
        """
        integrated_scores = {}

        for url in urls:
            # 各指標を取得（デフォルト0）
            y = yamadashy_signals.get(url, 0)
            h = hatena_scores.get(url, 0.0)
            z = zenn_scores.get(url, 0.0)
            q = qiita_scores.get(url, 0.0)

            # ドメイン判定
            netloc = urlparse(url).netloc

            # Y と H は全ドメイン共通で適用
            weighted_sum = self.WEIGHT_YAMADASHY * y + self.WEIGHT_HATENA * h
            applicable_weight = self.WEIGHT_YAMADASHY + self.WEIGHT_HATENA

            # ドメイン固有の指標を追加
            if "zenn.dev" in netloc:
                weighted_sum += self.WEIGHT_ZENN * z
                applicable_weight += self.WEIGHT_ZENN
            elif "qiita.com" in netloc:
                weighted_sum += self.WEIGHT_QIITA * q
                applicable_weight += self.WEIGHT_QIITA

            # 統合スコア計算（適用重みで正規化）
            score = weighted_sum / applicable_weight

            integrated_scores[url] = score

            logger.debug(
                "social_proof_score_calculated",
                url=url,
                y=y,
                h=h,
                z=z,
                q=q,
                applicable_weight=applicable_weight,
                score=score,
            )

        return integrated_scores
