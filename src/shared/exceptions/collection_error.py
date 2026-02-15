"""収集エラー例外モジュール."""


class CollectionError(Exception):
    """収集エラー（全ソース失敗時）.

    全ての収集元からの記事取得に失敗した場合に発生する.
    """


class SourceCollectionError(CollectionError):
    """単一ソース収集エラー.

    特定の収集元からの記事取得に失敗した場合に発生する.
    このエラーは個別にハンドリングされ、他のソースの収集は継続される.
    """
