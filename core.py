"""
Max/MSP Reference MCP Server
Max/MSP & Max4Live reference server powered by FastMCP.
Provides bilingual (Japanese/English) object search, design consultation, and learning support.
"""

import os
from pathlib import Path
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
from github_issues import create_bug_report, create_feature_request
from analytics import track, get_summary, get_recent_calls
from news import fetch_official_news, fetch_rnbo_news, fetch_article_detail

mcp = FastMCP(
    "Max/MSP Reference",
    instructions=(
        "Max/MSP & Max4Live bilingual (JA/EN) reference and design consultation server. "
        "Provides object specs, patch design brainstorming, and learning support. "
        "For actual patch building/manipulation, use MaxMCP (max.* tools).\n"
        "Max/MSP・Max4Live の日英バイリンガル対応リファレンス・設計相談サーバーです。"
        "オブジェクト仕様の調査、パッチ設計の壁打ち、学習支援を提供します。"
        "パッチの実際の構築・操作にはMaxMCP（max.*ツール）を使用してください。"
    ),
)


# --- Reference Search / リファレンス検索 ---


@mcp.tool(name="maxref.search_object")
@track("maxref.search_object")
def search_object(
    query: str,
    domain: str | None = None,
    category: str | None = None,
    max_results: int = 10,
) -> dict:
    """Search Max/MSP object references by name or keyword. Returns inlet/outlet specs, related objects, and usage info. Use before building patches for research and learning. For placing objects in a patch, use MaxMCP's max.object.create.
    Max/MSPオブジェクトのリファレンスを検索。インレット/アウトレット仕様、関連オブジェクト、使い方を調べたいときに使用。

    Args:
        query: Search keyword / 検索キーワード (e.g. "cycle~", "oscillator", "filter")
        domain: Domain filter / ドメインフィルター ("max", "msp", "jitter")
        category: Category filter / カテゴリフィルター ("oscillator", "filter", "math", etc.)
        max_results: Maximum number of results / 最大結果数 (default: 10)
    """
    return search_objects(query, domain=domain, category=category, max_results=max_results)


@mcp.tool(name="maxref.get_object")
@track("maxref.get_object")
def get_object(name: str) -> dict:
    """Get detailed reference for a Max/MSP object. Returns complete specs including inlet/outlet types, related objects, and usage examples.
    Max/MSPオブジェクトの詳細リファレンスを取得。インレット/アウトレットの型・意味、関連オブジェクト、使用例を含む完全な仕様書。

    Args:
        name: Object name / オブジェクト名 (e.g. "cycle~", "metro", "jit.gl.gridshape")
    """
    result = get_object_detail(name)
    if result is None:
        return {"error": f"Object '{name}' not found. Try searching with maxref.search_object. / オブジェクト '{name}' が見つかりません。maxref.search_object で検索してみてください。"}
    return result


@mcp.tool(name="maxref.search_pattern")
@track("maxref.search_pattern")
def search_pattern(
    query: str,
    domain: str | None = None,
    max_results: int = 5,
) -> dict:
    """Search Max/MSP patch design patterns by intent. Returns object combinations and connection templates. Use during design phase for brainstorming. For actual patch building, use MaxMCP Skills (/max-synth, etc.).
    やりたいことからMax/MSPパッチの設計パターンを検索。使用オブジェクトと接続構成のテンプレートを返す。

    Args:
        query: What you want to do / やりたいこと (e.g. "build a synthesizer", "delay effect", "video playback")
        domain: Domain filter / ドメインフィルター ("max", "msp", "jitter")
        max_results: Maximum number of results / 最大結果数 (default: 5)
    """
    return search_patterns(query, domain=domain, max_results=max_results)


@mcp.tool(name="maxref.search_package")
@track("maxref.search_package")
def search_package(query: str, max_results: int = 5) -> dict:
    """Search Max/MSP external packages and libraries. Provides feature comparison, version compatibility, and selection info.
    Max/MSPの外部パッケージ・ライブラリのリファレンスを検索。機能比較、対応バージョンなど選定に必要な情報を提供。

    Args:
        query: Search keyword / 検索キーワード (e.g. "spatial audio", "computer vision", "BEAP")
        max_results: Maximum number of results / 最大結果数 (default: 5)
    """
    return search_packages(query, max_results=max_results)


@mcp.tool(name="maxref.glossary")
@track("maxref.glossary")
def glossary(term: str) -> dict:
    """Japanese-English glossary for Max/MSP terminology. Explains DSP, signal flow, and Max-specific concepts in beginner-friendly language.
    Max/MSP関連用語の日英対応辞書。DSP、シグナルフロー、Max固有の概念を初学者にもわかりやすく解説。

    Args:
        term: Term to look up / 調べたい用語 (e.g. "signal", "bang", "patch cord")
    """
    result = lookup_glossary(term)
    if result is None:
        return {"error": f"Term '{term}' not found. Try a different expression. / 用語 '{term}' が見つかりません。別の表現で検索してみてください。"}
    return result


# --- Design Consultation / 設計相談 ---


@mcp.tool(name="maxref.compare_objects")
@track("maxref.compare_objects")
def compare_objects(objects: list[str]) -> dict:
    """Compare 2-5 Max/MSP objects side by side. Shows differences in usage, inlet/outlet configuration, domain, and RNBO compatibility. Use for object selection during design.
    2つ以上のMax/MSPオブジェクトを比較。用途の違い、インレット/アウトレット構成、ドメイン、RNBO互換性などを並べて解説。

    Args:
        objects: List of object names to compare (2-5) / 比較するオブジェクト名のリスト（2〜5個。例: ["cycle~", "phasor~"]）
    """
    return compare_objects_detail(objects)


@mcp.tool(name="maxref.suggest_approach")
@track("maxref.suggest_approach")
def suggest_approach(
    goal: str,
    constraints: list[str] | None = None,
) -> dict:
    """Suggest multiple implementation approaches for a goal, with pros and cons for each. Use as a design brainstorming partner.
    やりたいことに対して複数の実装アプローチを提案し、それぞれのメリット・デメリットを解説。設計の壁打ち相手として使用。

    Args:
        goal: What you want to achieve / 実現したいこと (e.g. "build a polyphonic synth", "audio-reactive visuals")
        constraints: List of constraints / 制約条件のリスト (e.g. ["RNBO compatible", "low CPU", "Max for Live"])
    """
    return suggest_approaches(goal, constraints=constraints)


@mcp.tool(name="maxref.explain_connection")
@track("maxref.explain_connection")
def explain_connection(source: str, destination: str) -> dict:
    """Explain connection method and signal flow between two objects. Shows which outlet connects to which inlet and checks type compatibility.
    2つのオブジェクト間の接続方法と信号フローを解説。どのアウトレットからどのインレットに接続すべきか、型の互換性を確認。

    Args:
        source: Source object name / 接続元オブジェクト名 (e.g. "cycle~")
        destination: Destination object name / 接続先オブジェクト名 (e.g. "ezdac~")
    """
    return explain_connection_detail(source, destination)


@mcp.tool(name="maxref.rnbo_compatibility")
@track("maxref.rnbo_compatibility")
def rnbo_compatibility(objects: list[str]) -> dict:
    """Check if objects are RNBO compatible. Suggests alternatives for incompatible objects. Use before RNBO export.
    指定オブジェクトがRNBOに対応しているか確認。非対応の場合は代替オブジェクトを提案。RNBOエクスポート前の事前チェックに使用。

    Args:
        objects: List of object names to check / チェックするオブジェクト名のリスト (e.g. ["cycle~", "groove~", "js"])
    """
    return check_rnbo_compatibility(objects)


# --- Feedback / フィードバック ---


@mcp.tool(name="maxref.report_bug")
@track("maxref.report_bug")
def report_bug(
    title: str,
    description: str,
    steps_to_reproduce: str | None = None,
    expected: str | None = None,
    actual: str | None = None,
    target_repo: str | None = None,
) -> dict:
    """Report a bug and auto-create a GitHub Issue. Automatically routes to the appropriate repo: patch building/control bugs go to MaxMCP, reference/search bugs go to MaxRefMCP.
    MaxMCP / MaxRefMCP のバグを報告してGitHub Issueを自動作成。内容に基づいて適切なリポジトリに自動振り分け。

    Args:
        title: Bug summary / バグの概要
        description: Detailed description / バグの詳細説明
        steps_to_reproduce: Steps to reproduce (optional) / 再現手順（任意）
        expected: Expected behavior (optional) / 期待される動作（任意）
        actual: Actual behavior (optional) / 実際の動作（任意）
        target_repo: Explicit target ("maxmcp" or "maxrefmcp", auto-detected if omitted) / 振り分け先（省略時は自動判定）
    """
    return create_bug_report(
        title=title,
        description=description,
        steps_to_reproduce=steps_to_reproduce,
        expected=expected,
        actual=actual,
        target_repo=target_repo,
    )


@mcp.tool(name="maxref.request_feature")
@track("maxref.request_feature")
def request_feature(
    title: str,
    description: str,
    use_case: str | None = None,
    target_repo: str | None = None,
) -> dict:
    """Request a new feature and auto-create a GitHub Issue. Automatically routes to the appropriate repo based on content.
    MaxMCP / MaxRefMCP への機能追加リクエストをGitHub Issueとして自動作成。内容に基づいて適切なリポジトリに自動振り分け。

    Args:
        title: Feature summary / 機能の概要
        description: Detailed description / 機能の詳細説明
        use_case: Use case (optional) / ユースケース・利用場面（任意）
        target_repo: Explicit target ("maxmcp" or "maxrefmcp", auto-detected if omitted) / 振り分け先（省略時は自動判定）
    """
    return create_feature_request(
        title=title,
        description=description,
        use_case=use_case,
        target_repo=target_repo,
    )


# --- Official News / 公式ニュース ---


@mcp.tool(name="maxref.official_news")
@track("maxref.official_news")
def official_news(max_results: int = 5) -> dict:
    """Fetch latest articles and news from the official Cycling '74 website. Check new features, updates, and community info.
    Cycling '74 公式サイトから最新の記事・ニュースを取得。新機能、アップデート、コミュニティ情報を確認できる。

    Args:
        max_results: Number of articles to fetch / 取得する記事数 (default: 5)
    """
    return fetch_official_news(max_results=max_results)


@mcp.tool(name="maxref.rnbo_news")
@track("maxref.rnbo_news")
def rnbo_news(max_results: int = 5) -> dict:
    """Fetch latest RNBO-related information. Check Move Takeover, export targets, new features, and latest developments.
    RNBO 関連の最新情報を取得。Move Takeover、エクスポートターゲット、新機能などの最新動向を確認。

    Args:
        max_results: Number of sections to fetch / 取得するセクション数 (default: 5)
    """
    return fetch_rnbo_news(max_results=max_results)


@mcp.tool(name="maxref.read_article")
@track("maxref.read_article")
def read_article(url: str) -> dict:
    """Read and fetch content from a Cycling '74 article. Use with URLs obtained from maxref.official_news.
    Cycling '74 公式サイトの記事を読み込み、内容を取得する。maxref.official_news で取得した記事URLを指定して詳細を確認。

    Args:
        url: Article URL from cycling74.com / cycling74.com の記事URL
    """
    return fetch_article_detail(url)


# --- Analytics / アナリティクス ---


@mcp.tool(name="maxref.analytics")
def analytics(days: int = 30) -> dict:
    """Get MaxRefMCP API usage summary. Shows per-tool call counts, response times, popular queries, and daily trends.
    MaxRefMCP の API 利用状況サマリーを取得。ツール別呼び出し数、応答時間、人気検索クエリ、日別推移などを返す。

    Args:
        days: Aggregation period in days / 集計期間・日数 (default: 30)
    """
    return get_summary(days)


# --- Dashboard HTTP Routes ---

from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route

DASHBOARD_HTML = (Path(__file__).parent / "dashboard.html").read_text(encoding="utf-8")


async def _dashboard_view(request: Request) -> HTMLResponse:
    return HTMLResponse(DASHBOARD_HTML)


async def _analytics_summary(request: Request) -> JSONResponse:
    days = int(request.query_params.get("days", 30))
    return JSONResponse(get_summary(days))


async def _analytics_recent(request: Request) -> JSONResponse:
    limit = int(request.query_params.get("limit", 50))
    return JSONResponse(get_recent_calls(limit))


mcp._additional_http_routes.extend([
    Route("/", _dashboard_view),
    Route("/analytics/summary", _analytics_summary),
    Route("/analytics/recent", _analytics_recent),
])


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port, path="/mcp")
