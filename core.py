"""
Max/MSP リファレンス MCP サーバー
FastMCPを使用した Max/MSP・Max4Live リファレンスサーバー。
初学者向けに日本語対応の自然言語検索・設計相談を提供。
"""

import os
from fastmcp import FastMCP

from search import (
    search_objects,
    get_object_detail,
    search_patterns,
    search_packages,
    lookup_glossary,
    compare_objects_detail,
    suggest_approaches,
    explain_connection_detail,
    check_rnbo_compatibility,
)

mcp = FastMCP(
    "Max/MSP Reference",
    instructions=(
        "Max/MSP・Max4Live の日本語対応リファレンス・設計相談サーバーです。"
        "オブジェクト仕様の調査、パッチ設計の壁打ち、学習支援を提供します。"
        "パッチの実際の構築・操作にはMaxMCP（max.*ツール）を使用してください。"
    ),
)


@mcp.tool(name="maxref.search_object")
def search_object(
    query: str,
    domain: str | None = None,
    category: str | None = None,
    max_results: int = 10,
) -> dict:
    """Max/MSPオブジェクトのリファレンスを検索。インレット/アウトレット仕様、関連オブジェクト、使い方を調べたいときに使用。パッチを作る前の調査・学習向け。パッチ構築時のオブジェクト配置にはMaxMCPのmax.object.createを使用してください。

    Args:
        query: 検索キーワード（例: "cycle~", "オシレーター", "filter"）
        domain: ドメインフィルター（"max", "msp", "jitter"）
        category: カテゴリフィルター（"oscillator", "filter", "math" など）
        max_results: 最大結果数（デフォルト10）
    """
    return search_objects(query, domain=domain, category=category, max_results=max_results)


@mcp.tool(name="maxref.get_object")
def get_object(name: str) -> dict:
    """Max/MSPオブジェクトの詳細リファレンスを取得。インレット/アウトレットの型・意味、関連オブジェクト、使用例を含む完全な仕様書。設計判断の根拠として参照。

    Args:
        name: オブジェクト名（例: "cycle~", "metro", "jit.gl.gridshape"）
    """
    result = get_object_detail(name)
    if result is None:
        return {"error": f"オブジェクト '{name}' が見つかりません。maxref.search_object で検索してみてください。"}
    return result


@mcp.tool(name="maxref.search_pattern")
def search_pattern(
    query: str,
    domain: str | None = None,
    max_results: int = 5,
) -> dict:
    """やりたいことからMax/MSPパッチの設計パターンを検索。使用オブジェクトと接続構成のテンプレートを返す。設計フェーズでの構成検討・壁打ちに使用。実際のパッチ構築にはMaxMCPのSkills（/max-synth等）を使用してください。

    Args:
        query: やりたいこと（例: "シンセサイザーを作りたい", "delay effect", "ビデオ再生"）
        domain: ドメインフィルター（"max", "msp", "jitter"）
        max_results: 最大結果数（デフォルト5）
    """
    return search_patterns(query, domain=domain, max_results=max_results)


@mcp.tool(name="maxref.search_package")
def search_package(query: str, max_results: int = 5) -> dict:
    """Max/MSPの外部パッケージ・ライブラリのリファレンスを検索。機能比較、対応バージョンなど選定に必要な情報を提供。

    Args:
        query: 検索キーワード（例: "spatial audio", "コンピュータビジョン", "BEAP"）
        max_results: 最大結果数（デフォルト5）
    """
    return search_packages(query, max_results=max_results)


@mcp.tool(name="maxref.glossary")
def glossary(term: str) -> dict:
    """Max/MSP関連用語の日英対応辞書。DSP、シグナルフロー、Max固有の概念を初学者にもわかりやすく解説。

    Args:
        term: 調べたい用語（例: "signal", "シグナル", "bang", "パッチコード"）
    """
    result = lookup_glossary(term)
    if result is None:
        return {"error": f"用語 '{term}' が見つかりません。別の表現で検索してみてください。"}
    return result


@mcp.tool(name="maxref.compare_objects")
def compare_objects(objects: list[str]) -> dict:
    """2つ以上のMax/MSPオブジェクトを比較。用途の違い、インレット/アウトレット構成、ドメイン、RNBO互換性などを並べて解説。設計時のオブジェクト選定に使用。

    Args:
        objects: 比較するオブジェクト名のリスト（2〜5個。例: ["cycle~", "phasor~"] や ["groove~", "play~", "wave~"]）
    """
    return compare_objects_detail(objects)


@mcp.tool(name="maxref.suggest_approach")
def suggest_approach(
    goal: str,
    constraints: list[str] | None = None,
) -> dict:
    """やりたいことに対して複数の実装アプローチを提案し、それぞれのメリット・デメリットを解説。設計の壁打ち相手として使用。

    Args:
        goal: 実現したいこと（例: "音声入力に反応する映像を作りたい", "ポリフォニックシンセを作りたい"）
        constraints: 制約条件のリスト（例: ["RNBO互換", "CPU負荷を抑えたい", "Max for Live用"]）
    """
    return suggest_approaches(goal, constraints=constraints)


@mcp.tool(name="maxref.explain_connection")
def explain_connection(source: str, destination: str) -> dict:
    """2つのオブジェクト間の接続方法と信号フローを解説。どのアウトレットからどのインレットに接続すべきか、型の互換性を確認。

    Args:
        source: 接続元オブジェクト名（例: "cycle~"）
        destination: 接続先オブジェクト名（例: "ezdac~"）
    """
    return explain_connection_detail(source, destination)


@mcp.tool(name="maxref.rnbo_compatibility")
def rnbo_compatibility(objects: list[str]) -> dict:
    """指定オブジェクトがRNBOに対応しているか確認。非対応の場合は代替オブジェクトを提案。RNBOエクスポート前の事前チェックに使用。

    Args:
        objects: チェックするオブジェクト名のリスト（例: ["cycle~", "groove~", "js"]）
    """
    return check_rnbo_compatibility(objects)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port, path="/mcp")
