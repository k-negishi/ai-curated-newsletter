"""URL正規化ユーティリティモジュール."""

from urllib.parse import parse_qs, urlparse, urlunparse


def normalize_url(url: str) -> str:
    """URLを正規化する.

    以下の正規化を行う:
    - クエリパラメータの除去（utm_*等のトラッキングパラメータ）
    - スキームの統一（https）
    - トレーリングスラッシュの除去
    - フラグメント（#以降）の除去

    Args:
        url: 正規化前URL

    Returns:
        正規化されたURL

    Raises:
        ValueError: URLが不正な形式の場合

    Examples:
        >>> normalize_url("http://example.com/path?utm_source=twitter")
        'https://example.com/path'
        >>> normalize_url("https://example.com/path/")
        'https://example.com/path'
    """
    if not url:
        raise ValueError("URLが空です")

    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValueError(f"URLの解析に失敗しました: {url}") from e

    # スキームをhttpsに統一
    scheme = "https"

    # クエリパラメータからトラッキングパラメータを除去
    query_params = parse_qs(parsed.query)
    # utm_*, fbclid, gclid等のトラッキングパラメータを除去
    tracking_params = {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "fbclid",
        "gclid",
        "msclkid",
    }
    filtered_params = {
        k: v
        for k, v in query_params.items()
        if not any(k.startswith(prefix) for prefix in ["utm_"]) and k not in tracking_params
    }

    # クエリ文字列を再構築（空の場合は除去）
    query = ""
    if filtered_params:
        query = "&".join(f"{k}={v[0]}" for k, v in filtered_params.items())

    # パスからトレーリングスラッシュを除去
    path = parsed.path.rstrip("/") if parsed.path != "/" else parsed.path

    # フラグメントを除去
    fragment = ""

    # 正規化されたURLを構築
    return urlunparse((scheme, parsed.netloc, path, parsed.params, query, fragment))
