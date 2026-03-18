"""
GitHub Issue 作成モジュール
MaxMCP / MaxRefMCP への Issue を自動振り分けして作成する。
"""

import json
import os
import re
import urllib.request
import urllib.error

REPOS = {
    "maxmcp": "dsgarage/MaxMCP-dev",
    "maxrefmcp": "dsgarage/MaxRefMCP",
}

# MaxMCP に振り分けるキーワード（パッチ構築・操作・制御系）
_MAXMCP_KEYWORDS = [
    "パッチ", "patcher", "オブジェクト配置", "接続", "connect",
    "websocket", "ws-bridge", "node.script", "クライアント", "client",
    "dsp", "audio.toggle", "ezdac", "lock", "unlock",
    "layout", "align", "distribute", "cleanup",
    "ableton", "live", "m4l", "max for live",
    "rnbo export", "rnbo.export",
    "max.object", "max.patcher", "max.audio", "max.log",
    "max.setup", "max.client", "max.ableton", "max.rnbo",
    "skill", "スキル", "/max-synth", "/max-fx", "/max-sampler",
    "patcher-api", "v8",
]

# MaxRefMCP に振り分けるキーワード（リファレンス・設計相談系）
_MAXREFMCP_KEYWORDS = [
    "リファレンス", "reference", "検索", "search",
    "用語", "glossary", "辞書",
    "比較", "compare", "壁打ち", "設計相談", "suggest",
    "接続解説", "explain_connection", "型互換",
    "rnbo互換", "rnbo_compatibility", "互換チェック",
    "object-db", "pattern-db", "package-db", "glossary-db",
    "maxref.", "データベース", "db",
    "railway", "デプロイ", "deploy",
    "fastmcp",
]


def _classify_repo(title: str, description: str) -> str:
    """タイトルと説明からリポジトリを判定"""
    text = f"{title} {description}".lower()

    maxmcp_score = 0
    maxrefmcp_score = 0

    for kw in _MAXMCP_KEYWORDS:
        if kw.lower() in text:
            maxmcp_score += 1

    for kw in _MAXREFMCP_KEYWORDS:
        if kw.lower() in text:
            maxrefmcp_score += 1

    if maxmcp_score > maxrefmcp_score:
        return "maxmcp"
    elif maxrefmcp_score > maxmcp_score:
        return "maxrefmcp"
    else:
        # スコア同点またはどちらにもマッチしない場合、
        # max. プレフィックスのツール名があればMaxMCP
        if re.search(r'\bmax\.(object|patcher|audio|log|setup|client|ableton|rnbo)\b', text):
            return "maxmcp"
        # maxref. プレフィックスがあればMaxRefMCP
        if "maxref." in text:
            return "maxrefmcp"
        # デフォルトはMaxMCP（実装系の方が Issue が多い想定）
        return "maxmcp"


def _get_github_token() -> str | None:
    return os.environ.get("GITHUB_TOKEN")


def _create_github_issue(repo: str, title: str, body: str, labels: list[str]) -> dict:
    """GitHub API で Issue を作成"""
    token = _get_github_token()
    if not token:
        return {
            "error": "GITHUB_TOKEN 環境変数が設定されていません。GitHub Issue の作成にはトークンが必要です。",
            "fallback": {
                "repo": repo,
                "title": title,
                "body": body,
                "labels": labels,
                "manual_url": f"https://github.com/{repo}/issues/new",
            },
        }

    url = f"https://api.github.com/repos/{repo}/issues"
    payload = json.dumps({
        "title": title,
        "body": body,
        "labels": labels,
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {
                "success": True,
                "issue_number": data["number"],
                "url": data["html_url"],
                "repo": repo,
                "title": data["title"],
            }
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        return {
            "error": f"GitHub API エラー: {e.code} {e.reason}",
            "detail": error_body,
            "repo": repo,
        }


def create_bug_report(
    title: str,
    description: str,
    steps_to_reproduce: str | None = None,
    expected: str | None = None,
    actual: str | None = None,
    target_repo: str | None = None,
) -> dict:
    """バグレポートを作成して適切なリポジトリに Issue を発行"""
    # リポジトリ振り分け
    if target_repo and target_repo.lower() in REPOS:
        repo_key = target_repo.lower()
    else:
        repo_key = _classify_repo(title, description)

    repo = REPOS[repo_key]

    # Issue 本文を構築
    body_parts = [
        "## バグ報告\n",
        f"### 概要\n{description}\n",
    ]
    if steps_to_reproduce:
        body_parts.append(f"### 再現手順\n{steps_to_reproduce}\n")
    if expected:
        body_parts.append(f"### 期待される動作\n{expected}\n")
    if actual:
        body_parts.append(f"### 実際の動作\n{actual}\n")

    body_parts.append(f"\n---\n*自動振り分け先: {repo_key} (`{repo}`)*")

    body = "\n".join(body_parts)
    labels = ["bug"]

    return _create_github_issue(repo, f"[Bug] {title}", body, labels)


def create_feature_request(
    title: str,
    description: str,
    use_case: str | None = None,
    target_repo: str | None = None,
) -> dict:
    """機能追加リクエストを作成して適切なリポジトリに Issue を発行"""
    # リポジトリ振り分け
    if target_repo and target_repo.lower() in REPOS:
        repo_key = target_repo.lower()
    else:
        repo_key = _classify_repo(title, description)

    repo = REPOS[repo_key]

    # Issue 本文を構築
    body_parts = [
        "## 機能リクエスト\n",
        f"### 概要\n{description}\n",
    ]
    if use_case:
        body_parts.append(f"### ユースケース\n{use_case}\n")

    body_parts.append(f"\n---\n*自動振り分け先: {repo_key} (`{repo}`)*")

    body = "\n".join(body_parts)
    labels = ["enhancement"]

    return _create_github_issue(repo, f"[Feature] {title}", body, labels)
