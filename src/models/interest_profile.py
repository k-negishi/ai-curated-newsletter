"""関心プロファイルエンティティモジュール."""

from dataclasses import dataclass


@dataclass
class JudgmentCriterion:
    """判定基準の定義.

    Attributes:
        label: 判定ラベル（ACT_NOW/THINK/FYI/IGNORE）
        description: 判定基準の説明
        examples: 該当する記事の例
    """

    label: str
    description: str
    examples: list[str]


@dataclass
class InterestProfile:
    """関心プロファイル（5段階版）.

    Attributes:
        summary: プロファイルの概要
        max_interest: 最高関心を持つトピックのリスト
        high_interest: 高い関心を持つトピックのリスト
        medium_interest: 中程度の関心を持つトピックのリスト
        low_interest: 低関心のトピックのリスト
        ignore_interest: 関心外のトピックのリスト
        criteria: 判定基準の辞書（キー: act_now/think/fyi/ignore）
    """

    summary: str
    max_interest: list[str]
    high_interest: list[str]
    medium_interest: list[str]
    low_interest: list[str]
    ignore_interest: list[str]
    criteria: dict[str, JudgmentCriterion]

    def format_for_prompt(self) -> str:
        """プロンプト用に関心プロファイルを整形する（5段階対応版）.

        Returns:
            プロンプトに埋め込むための文字列
        """
        lines = [self.summary.strip(), ""]

        if self.max_interest:
            lines.append("**最高関心を持つトピック**:")
            for topic in self.max_interest:
                lines.append(f"- {topic}")
            lines.append("")

        if self.high_interest:
            lines.append("**強い関心を持つトピック**:")
            for topic in self.high_interest:
                lines.append(f"- {topic}")
            lines.append("")

        if self.medium_interest:
            lines.append("**中程度の関心を持つトピック**:")
            for topic in self.medium_interest:
                lines.append(f"- {topic}")
            lines.append("")

        if self.low_interest:
            lines.append("**低関心のトピック**:")
            for topic in self.low_interest:
                lines.append(f"- {topic}")
            lines.append("")

        if self.ignore_interest:
            lines.append("**関心外のトピック**:")
            for topic in self.ignore_interest:
                lines.append(f"- {topic}")
            lines.append("")

        return "\n".join(lines).strip()

    def format_criteria_for_prompt(self) -> str:
        """判定基準をプロンプト用に整形する.

        Returns:
            プロンプトに埋め込むための判定基準文字列
        """
        lines = []
        for key in ["act_now", "think", "fyi", "ignore"]:
            if key in self.criteria:
                criterion = self.criteria[key]
                lines.append(f"- **{criterion.label}**: {criterion.description}")
                if criterion.examples:
                    lines.append("  - 該当例:")
                    for example in criterion.examples:
                        lines.append(f"    - {example}")

        return "\n".join(lines)
