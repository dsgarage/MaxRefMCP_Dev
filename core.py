"""
Max/MSP リファレンス MCP サーバー
FastMCPを使用した Max/MSP・Max4Live リファレンスサーバー。
初学者向けに日本語対応の自然言語検索を提供。
"""

import os
from fastmcp import FastMCP

from search import (
    search_objects,
    get_object_detail,
    search_patterns,
    search_packages,
    lookup_glossary,
)

mcp = FastMCP(
    "Max/MSP Reference",
    instructions=(
        "Max/MSP・Max4Live の日本語対応リファレンスサーバーです。"
        "オブジェクト、パッチパターン、パッケージ、用語を検索できます。"
        "初学者にもわかりやすい日本語の説明を提供します。"
    ),
)


@mcp.tool()
def search_object(
    query: str,
    domain: str | None = None,
    category: str | None = None,
    max_results: int = 10,
) -> dict:
    """Max/MSPオブジェクトを検索します。名前、タグ、日本語キーワードで検索可能。

    Args:
        query: 検索キーワード（例: "cycle~", "オシレーター", "filter"）
        domain: ドメインフィルター（"max", "msp", "jitter"）
        category: カテゴリフィルター（"oscillator", "filter", "math" など）
        max_results: 最大結果数（デフォルト10）
    """
    return search_objects(query, domain=domain, category=category, max_results=max_results)


@mcp.tool()
def get_object(name: str) -> dict:
    """Max/MSPオブジェクトの詳細情報を取得します。インレット、アウトレット、関連オブジェクト等。

    Args:
        name: オブジェクト名（例: "cycle~", "metro", "jit.gl.gridshape"）
    """
    result = get_object_detail(name)
    if result is None:
        return {"error": f"オブジェクト '{name}' が見つかりません。search_object で検索してみてください。"}
    return result


@mcp.tool()
def search_pattern(
    query: str,
    domain: str | None = None,
    max_results: int = 5,
) -> dict:
    """Max/MSPのパッチパターン（テンプレート）を検索します。やりたいことを自然言語で入力。

    Args:
        query: やりたいこと（例: "シンセサイザーを作りたい", "delay effect", "ビデオ再生"）
        domain: ドメインフィルター（"max", "msp", "jitter"）
        max_results: 最大結果数（デフォルト5）
    """
    return search_patterns(query, domain=domain, max_results=max_results)


@mcp.tool()
def search_package(query: str, max_results: int = 5) -> dict:
    """Max/MSPのパッケージ・ライブラリを検索します。

    Args:
        query: 検索キーワード（例: "spatial audio", "コンピュータビジョン", "BEAP"）
        max_results: 最大結果数（デフォルト5）
    """
    return search_packages(query, max_results=max_results)


@mcp.tool()
def glossary(term: str) -> dict:
    """Max/MSP関連の用語を検索します。日英対応。

    Args:
        term: 調べたい用語（例: "signal", "シグナル", "bang", "パッチコード"）
    """
    result = lookup_glossary(term)
    if result is None:
        return {"error": f"用語 '{term}' が見つかりません。別の表現で検索してみてください。"}
    return result


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port, path="/mcp")
