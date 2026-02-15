"""LLM判定エラー例外モジュール."""


class LlmError(Exception):
    """LLM判定エラー.

    LLMによる記事判定中に発生するエラーの基底クラス.
    """


class LlmJsonParseError(LlmError):
    """LLM出力のJSON解析エラー.

    LLMの出力がJSON形式でない、または期待される形式と異なる場合に発生する.
    リトライ対象のエラー（最大2回）.
    """


class LlmTimeoutError(LlmError):
    """LLMタイムアウトエラー.

    LLMのレスポンスがタイムアウト時間内に返ってこない場合に発生する.
    """
