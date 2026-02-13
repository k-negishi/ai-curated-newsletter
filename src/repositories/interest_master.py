"""関心マスタリポジトリモジュール."""

from pathlib import Path

import yaml

from src.models.interest_profile import InterestProfile, JudgmentCriterion
from src.shared.logging.logger import get_logger

logger = get_logger(__name__)


class InterestMaster:
    """関心マスタ.

    config/interests.yamlから関心プロファイルを読み込む.

    Attributes:
        _config_path: 設定ファイルパス
        _profile: 読み込んだプロファイル（キャッシュ）
    """

    def __init__(self, config_path: str | Path) -> None:
        """関心マスタを初期化する.

        Args:
            config_path: 設定ファイルパス（config/interests.yaml）
        """
        self._config_path = Path(config_path)
        self._profile: InterestProfile | None = None

    def get_profile(self) -> InterestProfile:
        """関心プロファイルを取得する.

        Returns:
            関心プロファイル

        Raises:
            FileNotFoundError: 設定ファイルが見つからない場合
            ValueError: YAML解析に失敗した場合
        """
        if self._profile is not None:
            return self._profile

        logger.info("interest_profile_load_start", config_path=str(self._config_path))

        if not self._config_path.exists():
            raise FileNotFoundError(f"Interest config file not found: {self._config_path}")

        try:
            with open(self._config_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            logger.error("interest_config_parse_error", path=str(self._config_path), error=str(e))
            raise ValueError(f"Failed to parse interests.yaml: {e}") from e

        # 必須フィールドのバリデーション
        if "profile" not in data:
            raise ValueError("Missing 'profile' key in interests.yaml")
        if "criteria" not in data:
            raise ValueError("Missing 'criteria' key in interests.yaml")

        # YAMLからInterestProfileを生成
        profile_data = data.get("profile", {})
        criteria_data = data.get("criteria", {})

        # 判定基準の辞書を作成
        criteria = {}
        for key, value in criteria_data.items():
            criteria[key] = JudgmentCriterion(
                label=value.get("label", ""),
                description=value.get("description", ""),
                examples=value.get("examples", []),
            )

        self._profile = InterestProfile(
            summary=profile_data.get("summary", ""),
            high_interest=profile_data.get("high_interest", []),
            medium_interest=profile_data.get("medium_interest", []),
            low_priority=profile_data.get("low_priority", []),
            criteria=criteria,
        )

        logger.info(
            "interest_profile_loaded",
            high_interest_count=len(self._profile.high_interest),
            medium_interest_count=len(self._profile.medium_interest),
            low_priority_count=len(self._profile.low_priority),
        )

        return self._profile
