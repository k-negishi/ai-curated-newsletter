"""Formatterサービスのユニットテスト."""

from datetime import datetime, timezone

from src.models.judgment import BuzzLabel, InterestLabel, JudgmentResult
from src.services.formatter import Formatter


def _judgment(
    *,
    title: str,
    url: str,
    interest_label: InterestLabel,
    tags: list[str],
) -> JudgmentResult:
    return JudgmentResult(
        url=url,
        title=title,
        description="概要テキスト",
        interest_label=interest_label,
        buzz_label=BuzzLabel.HIGH,
        confidence=0.9,
        summary="理由",
        model_id="test-model",
        judged_at=datetime(2026, 2, 13, 12, 0, 0, tzinfo=timezone.utc),
        published_at=datetime(2026, 2, 13, 10, 0, 0, tzinfo=timezone.utc),
        tags=tags,
    )


def test_format_uses_short_separator_and_jst_without_timezone_suffix() -> None:
    formatter = Formatter()
    body = formatter.format(
        selected_articles=[
            _judgment(
                title="Article One",
                url="https://example.com/one",
                interest_label=InterestLabel.ACT_NOW,
                tags=["Kotlin", "Claude"],
            )
        ],
        collected_count=10,
        judged_count=5,
        executed_at=datetime(2026, 2, 13, 15, 0, 0, tzinfo=timezone.utc),
    )

    assert "=" * 80 not in body
    assert "-" * 80 not in body
    assert "実行日時: 2026-02-14 00:00:00" in body
    assert "UTC" not in body
    assert "JST" not in body


def test_format_uses_global_sequence_across_sections_and_adds_tags() -> None:
    formatter = Formatter()
    body = formatter.format(
        selected_articles=[
            _judgment(
                title="Act",
                url="https://example.com/act",
                interest_label=InterestLabel.ACT_NOW,
                tags=["Kotlin"],
            ),
            _judgment(
                title="Think",
                url="https://example.com/think",
                interest_label=InterestLabel.THINK,
                tags=["Claude", "Python"],
            ),
            _judgment(
                title="FYI",
                url="https://example.com/fyi",
                interest_label=InterestLabel.FYI,
                tags=[],
            ),
        ],
        collected_count=10,
        judged_count=5,
        executed_at=datetime(2026, 2, 13, 0, 0, 0, tzinfo=timezone.utc),
    )

    assert "[1] Act" in body
    assert "[2] Think" in body
    assert "[3] FYI" in body
    assert "Tag: Kotlin" in body
    assert "Tag: Claude, Python" in body
    assert "Tag: -" in body


def test_format_html_links_only_url_field() -> None:
    formatter = Formatter()
    html = formatter.format_html(
        selected_articles=[
            _judgment(
                title="Claude.io deep dive",
                url="https://example.com/claude",
                interest_label=InterestLabel.ACT_NOW,
                tags=["Claude"],
            )
        ],
        collected_count=1,
        judged_count=1,
        executed_at=datetime(2026, 2, 13, 0, 0, 0, tzinfo=timezone.utc),
    )

    assert '<a href="https://example.com/claude"' in html
    assert "Claude.io deep dive" in html
    assert "<a href=\"Claude.io\"" not in html


def test_format_published_date_formats_to_yyyy_mm_dd() -> None:
    """公開日をYYYY-MM-DD形式でフォーマットすることを検証."""
    formatter = Formatter()
    published_at = datetime(2026, 2, 13, 10, 0, 0, tzinfo=timezone.utc)

    result = formatter._format_published_date(published_at)

    assert result == "2026-02-13"  # JSTに変換: 2026-02-13 19:00:00 JST


def test_format_article_includes_tag_and_published_date() -> None:
    """プレーンテキスト版でTagと公開日がタイトルの下に表示されることを検証."""
    formatter = Formatter()
    body = formatter.format(
        selected_articles=[
            _judgment(
                title="Test Article",
                url="https://example.com/test",
                interest_label=InterestLabel.ACT_NOW,
                tags=["Python", "Testing"],
            )
        ],
        collected_count=10,
        judged_count=5,
        executed_at=datetime(2026, 2, 13, 0, 0, 0, tzinfo=timezone.utc),
    )

    # タイトルの後にTagと公開日が表示される
    assert "[1] Test Article" in body
    assert "Tag: Python, Testing" in body
    assert "公開日: 2026-02-13" in body
    # Tag がタイトルの下（URLより前）に来ることを確認
    title_pos = body.find("[1] Test Article")
    tag_pos = body.find("Tag: Python, Testing")
    url_pos = body.find("URL: https://example.com/test")
    assert title_pos < tag_pos < url_pos


def test_format_html_uses_one_line_format_with_br() -> None:
    """HTML版で1行形式（<br/>のみ）でTag と公開日が表示されることを検証."""
    formatter = Formatter()
    html = formatter.format_html(
        selected_articles=[
            _judgment(
                title="Test Article",
                url="https://example.com/test",
                interest_label=InterestLabel.ACT_NOW,
                tags=["Python", "Testing"],
            )
        ],
        collected_count=10,
        judged_count=5,
        executed_at=datetime(2026, 2, 13, 0, 0, 0, tzinfo=timezone.utc),
    )

    # <p> タグが使われていないことを確認（記事部分）
    assert "<p>[1] Test Article</p>" not in html
    assert "<p>URL:" not in html
    # <br/> タグで改行されていることを確認
    assert "<br/>" in html
    # Tag と公開日が含まれていることを確認
    assert "Tag: Python, Testing" in html
    assert "公開日: 2026-02-13" in html


def test_format_html_does_not_use_ol_li_tags() -> None:
    """HTML版で<ol>と<li>タグが使われないことを検証."""
    formatter = Formatter()
    html = formatter.format_html(
        selected_articles=[
            _judgment(
                title="First Article",
                url="https://example.com/first",
                interest_label=InterestLabel.ACT_NOW,
                tags=["Python"],
            ),
            _judgment(
                title="Second Article",
                url="https://example.com/second",
                interest_label=InterestLabel.ACT_NOW,
                tags=["Testing"],
            ),
        ],
        collected_count=10,
        judged_count=5,
        executed_at=datetime(2026, 2, 13, 0, 0, 0, tzinfo=timezone.utc),
    )

    # <ol> と <li> タグが使われていないことを確認
    assert "<ol>" not in html
    assert "</ol>" not in html
    assert "<li>" not in html
    assert "</li>" not in html
    # 記事間に空白行（<br/><br/>）があることを確認
    assert "<br/><br/>" in html


def test_format_html_section_has_space_after_subtitle() -> None:
    """HTML版でセクションタイトル・サブタイトルの後にスペースがあることを検証."""
    formatter = Formatter()
    html = formatter.format_html(
        selected_articles=[
            _judgment(
                title="Test Article",
                url="https://example.com/test",
                interest_label=InterestLabel.ACT_NOW,
                tags=["Python"],
            )
        ],
        collected_count=10,
        judged_count=5,
        executed_at=datetime(2026, 2, 13, 0, 0, 0, tzinfo=timezone.utc),
    )

    # サブタイトルの後に <br/> があることを確認
    assert "<p>今すぐ読むべき重要な記事</p><br/>" in html


def test_format_think_section_subtitle_includes_broader_context() -> None:
    """THINKセクションのサブタイトルが設計だけでなく幅広い技術判断を含むことを検証."""
    formatter = Formatter()

    # プレーンテキスト版
    body = formatter.format(
        selected_articles=[
            _judgment(
                title="Test Article",
                url="https://example.com/test",
                interest_label=InterestLabel.THINK,
                tags=["Python"],
            )
        ],
        collected_count=10,
        judged_count=5,
        executed_at=datetime(2026, 2, 13, 0, 0, 0, tzinfo=timezone.utc),
    )

    # サブタイトルが「技術判断に役立つ記事」であることを確認
    assert "技術判断に役立つ記事" in body

    # HTML版
    html = formatter.format_html(
        selected_articles=[
            _judgment(
                title="Test Article",
                url="https://example.com/test",
                interest_label=InterestLabel.THINK,
                tags=["Python"],
            )
        ],
        collected_count=10,
        judged_count=5,
        executed_at=datetime(2026, 2, 13, 0, 0, 0, tzinfo=timezone.utc),
    )

    # HTML版でもサブタイトルが「技術判断に役立つ記事」であることを確認
    assert "技術判断に役立つ記事" in html


def test_format_uses_new_separator_characters() -> None:
    """区切り線が新しい文字（─）になっていることを検証（Gmail署名誤判定対策）."""
    formatter = Formatter()
    body = formatter.format(
        selected_articles=[
            _judgment(
                title="Test Article",
                url="https://example.com/test",
                interest_label=InterestLabel.ACT_NOW,
                tags=["Python"],
            )
        ],
        collected_count=10,
        judged_count=5,
        executed_at=datetime(2026, 2, 13, 0, 0, 0, tzinfo=timezone.utc),
    )

    # 旧区切り線（= や - の繰り返し）が使われていないことを確認
    assert "=" * 40 not in body
    assert "-" * 40 not in body
    # 新区切り線（─）が使われていることを確認
    assert "─" * 40 in body


def test_format_html_uses_new_separator_characters() -> None:
    """HTML版でも区切り線が新しい文字（─）になっていることを検証."""
    formatter = Formatter()
    html = formatter.format_html(
        selected_articles=[
            _judgment(
                title="Test Article",
                url="https://example.com/test",
                interest_label=InterestLabel.ACT_NOW,
                tags=["Python"],
            )
        ],
        collected_count=10,
        judged_count=5,
        executed_at=datetime(2026, 2, 13, 0, 0, 0, tzinfo=timezone.utc),
    )

    # HTML版でも新区切り線（─）が使われていることを確認（<hr/>の代わり）
    # または <hr/> が残っている場合はそのままでもOK（後で設計判断）
    # とりあえず旧区切り線がないことを確認
    assert "=" * 40 not in html
    assert "-" * 40 not in html


def test_format_includes_variable_content_in_footer() -> None:
    """メール末尾に可変コンテンツ（生成日時）が含まれていることを検証."""
    formatter = Formatter()
    executed_at = datetime(2026, 2, 15, 10, 30, 0, tzinfo=timezone.utc)
    body = formatter.format(
        selected_articles=[
            _judgment(
                title="Test Article",
                url="https://example.com/test",
                interest_label=InterestLabel.ACT_NOW,
                tags=["Python"],
            )
        ],
        collected_count=10,
        judged_count=5,
        executed_at=executed_at,
    )

    # 生成日時がフッターに含まれていることを確認
    # JST変換: 2026-02-15 10:30:00 UTC -> 2026-02-15 19:30:00 JST
    assert "生成日時: 2026-02-15 19:30:00" in body
    # "Generated with Claude Code" の前に生成日時があることを確認
    generated_pos = body.find("Generated with Claude Code")
    timestamp_pos = body.find("生成日時: 2026-02-15 19:30:00")
    assert timestamp_pos < generated_pos


def test_format_html_includes_variable_content_in_footer() -> None:
    """HTML版でもメール末尾に可変コンテンツ（生成日時）が含まれていることを検証."""
    formatter = Formatter()
    executed_at = datetime(2026, 2, 15, 10, 30, 0, tzinfo=timezone.utc)
    html = formatter.format_html(
        selected_articles=[
            _judgment(
                title="Test Article",
                url="https://example.com/test",
                interest_label=InterestLabel.ACT_NOW,
                tags=["Python"],
            )
        ],
        collected_count=10,
        judged_count=5,
        executed_at=executed_at,
    )

    # 生成日時がフッターに含まれていることを確認
    assert "生成日時: 2026-02-15 19:30:00" in html
    # "Generated with Claude Code" の前に生成日時があることを確認
    generated_pos = html.find("Generated with Claude Code")
    timestamp_pos = html.find("生成日時: 2026-02-15 19:30:00")
    assert timestamp_pos < generated_pos
