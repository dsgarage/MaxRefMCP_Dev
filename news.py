"""
Cycling '74 公式ニュース取得モジュール
公式サイト（Next.js）の __NEXT_DATA__ からデータを抽出。
"""

import re
import urllib.request
import urllib.error
import json
from html.parser import HTMLParser
from datetime import datetime


# --- HTML ヘルパー ---

class SimpleTextExtractor(HTMLParser):
    """HTMLからプレーンテキストを抽出"""

    def __init__(self):
        super().__init__()
        self.text_parts: list[str] = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "nav", "header", "footer"):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav", "header", "footer"):
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            stripped = data.strip()
            if stripped:
                self.text_parts.append(stripped)

    def get_text(self) -> str:
        return "\n".join(self.text_parts)


def _strip_html(html_str) -> str:
    """HTMLタグを除去してプレーンテキストを返す"""
    if not html_str:
        return ""
    if not isinstance(html_str, str):
        return str(html_str)
    extractor = SimpleTextExtractor()
    extractor.feed(html_str)
    return extractor.get_text()


def _extract_rich_text(content) -> str:
    """Cycling '74 のリッチテキストJSON（TipTap/ProseMirror形式）からプレーンテキストを抽出"""
    if isinstance(content, str):
        return _strip_html(content)
    if not isinstance(content, dict):
        return ""

    texts = []

    def walk(node):
        if isinstance(node, dict):
            if node.get("type") == "text":
                texts.append(node.get("text", ""))
            for child in node.get("content", []):
                walk(child)
            # 段落・見出しの後に改行
            if node.get("type") in ("paragraph", "heading", "bulletList", "orderedList", "listItem"):
                texts.append("\n")
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(content)
    return re.sub(r'\n{3,}', '\n\n', "".join(texts)).strip()


# --- フェッチ関数 ---

def _fetch_url(url: str, timeout: int = 10) -> str | None:
    """URLからHTMLを取得"""
    headers = {
        "User-Agent": "MaxRefMCP/3.1 (news-fetcher)",
        "Accept": "text/html,application/xhtml+xml",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError):
        return None


def _extract_next_data(html: str) -> dict | None:
    """Next.js の __NEXT_DATA__ JSON を抽出"""
    match = re.search(
        r'<script\s+id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL
    )
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


def fetch_official_news(max_results: int = 5) -> dict:
    """Cycling '74 公式サイトから最新記事を取得"""
    html = _fetch_url("https://cycling74.com/articles")
    if not html:
        return {
            "error": "cycling74.com への接続に失敗しました。",
            "source": "https://cycling74.com/articles",
        }

    next_data = _extract_next_data(html)
    if not next_data:
        return {
            "error": "ページデータの解析に失敗しました。",
            "source": "https://cycling74.com/articles",
        }

    post_data = (
        next_data.get("props", {}).get("pageProps", {}).get("postData", {})
    )
    results = post_data.get("results", [])

    articles = []
    for r in results[:max_results]:
        slug = r.get("name", "")
        authors = r.get("authors", [])
        author_name = authors[0].get("name", "") if authors else ""
        raw_excerpt = r.get("excerpt", "")
        if isinstance(raw_excerpt, dict):
            excerpt = raw_excerpt.get("text", "")
        else:
            excerpt = _strip_html(raw_excerpt)

        article = {
            "title": r.get("title", ""),
            "url": f"https://cycling74.com/articles/{slug}",
            "date": r.get("created_at", ""),
            "author": author_name,
        }
        if excerpt:
            article["excerpt"] = excerpt[:200]
        tags = r.get("tags") or r.get("admin_tags") or []
        if tags:
            article["tags"] = tags

        articles.append(article)

    return {
        "source": "https://cycling74.com/articles",
        "total_articles": post_data.get("total", 0),
        "article_count": len(articles),
        "articles": articles,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
    }


def fetch_rnbo_news(max_results: int = 5) -> dict:
    """RNBO 関連の最新情報を取得（製品ページ + Move ページ）"""
    results = {}

    # RNBO メインページ
    html = _fetch_url("https://cycling74.com/products/rnbo")
    if html:
        next_data = _extract_next_data(html)
        if next_data:
            page_props = next_data.get("props", {}).get("pageProps", {})
            results["rnbo_page"] = _extract_text_sections(html, max_results)

    # RNBO Move ページ
    html_move = _fetch_url("https://cycling74.com/products/rnbo/move")
    if html_move:
        results["move_page"] = _extract_text_sections(html_move, max_results)

    if not results:
        return {
            "error": "RNBO ページへの接続に失敗しました。",
            "source": "https://cycling74.com/products/rnbo",
        }

    return {
        "source": "https://cycling74.com/products/rnbo",
        **results,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
    }


def _extract_text_sections(html: str, max_sections: int = 5) -> list[dict]:
    """HTMLからキーセクションのテキストを抽出"""
    extractor = SimpleTextExtractor()
    extractor.feed(html)
    lines = extractor.text_parts

    sections = []
    seen = set()
    for i, line in enumerate(lines):
        if len(line) < 15:
            continue
        context = " ".join(lines[max(0, i - 1):min(len(lines), i + 3)]).strip()
        if len(context) > 30 and context not in seen:
            seen.add(context)
            sections.append({"text": context[:400]})

    return sections[:max_sections]


def fetch_article_detail(url: str) -> dict:
    """個別記事の詳細を取得"""
    if "cycling74.com" not in url:
        return {"error": "cycling74.com の記事URLのみ対応しています。"}

    html = _fetch_url(url)
    if not html:
        return {"error": f"記事の取得に失敗しました: {url}"}

    # Next.js データから取得を試行
    next_data = _extract_next_data(html)
    if next_data:
        page_props = next_data.get("props", {}).get("pageProps", {})
        post = page_props.get("post") or page_props.get("postData", {})

        if isinstance(post, dict) and post.get("title"):
            raw_content = post.get("content", "")
            content_text = _extract_rich_text(raw_content)
            authors = post.get("authors", [])
            author_name = authors[0].get("name", "") if authors else ""

            result = {
                "url": url,
                "title": post.get("title", ""),
                "author": author_name,
                "date": post.get("created_at", ""),
                "content": content_text[:3000],
                "fetched_at": datetime.utcnow().isoformat() + "Z",
            }
            tags = post.get("tags") or post.get("admin_tags") or []
            if tags:
                result["tags"] = tags
            return result

    # フォールバック: HTMLからテキスト抽出
    extractor = SimpleTextExtractor()
    extractor.feed(html)
    text = extractor.get_text()

    title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
    title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip() if title_match else ""

    content_lines = [l for l in text.split("\n") if len(l) > 30]
    content = "\n".join(content_lines[:30])

    return {
        "url": url,
        "title": title,
        "content": content[:3000],
        "fetched_at": datetime.utcnow().isoformat() + "Z",
    }
