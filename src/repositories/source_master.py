"""収集元マスタリポジトリモジュール."""

import json
from pathlib import Path

import yaml
from pydantic import ValidationError

from src.models.source_config import SourceConfig


class SourceMaster:
    """収集元マスタ.

    設定ファイル（config/sources.yaml または config/sources.json）から収集元設定を読み込む.

    Attributes:
        _sources: 収集元設定のリスト
    """

    def __init__(self, config_path: str | Path) -> None:
        """マスタを初期化する.

        Args:
            config_path: 設定ファイルパス（YAML または JSON）

        Raises:
            FileNotFoundError: 設定ファイルが見つからない場合
            ValidationError: 設定ファイルのバリデーションエラー
            ValueError: ファイル形式の解析エラー
        """
        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"設定ファイルが見つかりません: {config_path}")

        # ファイル拡張子に応じて読み込み方法を選択
        try:
            with open(config_path, encoding="utf-8") as f:
                if config_path.suffix in [".yaml", ".yml"]:
                    data = yaml.safe_load(f)
                elif config_path.suffix == ".json":
                    data = json.load(f)
                else:
                    raise ValueError(f"サポートされていないファイル形式です: {config_path.suffix}")
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise ValueError(f"ファイルの解析に失敗しました: {config_path}") from e

        # sources配列を取得
        if "sources" not in data:
            raise ValueError("設定ファイルに'sources'キーが必要です")

        # 各ソース設定をバリデーション
        self._sources: list[SourceConfig] = []
        for source_data in data["sources"]:
            try:
                source = SourceConfig(**source_data)
                self._sources.append(source)
            except ValidationError as e:
                source_id = source_data.get("source_id")
                raise ValidationError(
                    f"ソース設定のバリデーションエラー (source_id={source_id}): {e}"
                ) from e

    def get_all_sources(self) -> list[SourceConfig]:
        """全収集元設定を取得する.

        Returns:
            収集元設定のリスト
        """
        return self._sources.copy()

    def get_enabled_sources(self) -> list[SourceConfig]:
        """有効な収集元設定を取得する.

        Returns:
            有効な収集元設定のリスト（enabled=Trueのみ）
        """
        return [source for source in self._sources if source.enabled]
