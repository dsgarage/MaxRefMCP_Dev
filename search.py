"""
Max/MSP リファレンス検索エンジン
MaxMCPの検索ロジック（JavaScript）をPythonに移植。
スコアリング: (名前一致×10) + (タグ一致×5) + (説明一致×3) + (カテゴリ一致×8) + (関連×2)
"""

import json
import re
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent / "data"

_object_db: dict | None = None
_pattern_db: list | None = None
_package_db: list | None = None
_glossary_db: dict | None = None


def _load_json(filename: str) -> Any:
    return json.loads((DATA_DIR / filename).read_text(encoding="utf-8"))


def _get_object_db() -> dict:
    global _object_db
    if _object_db is None:
        _object_db = _load_json("object-db.json")
    return _object_db


def _get_pattern_db() -> list:
    global _pattern_db
    if _pattern_db is None:
        _pattern_db = _load_json("pattern-db.json")
    return _pattern_db


def _get_package_db() -> list:
    global _package_db
    if _package_db is None:
        _package_db = _load_json("package-db.json")
    return _package_db


def _get_glossary_db() -> dict:
    global _glossary_db
    if _glossary_db is None:
        _glossary_db = _load_json("glossary-db.json")
    return _glossary_db


def _text_score(text: str | None, query: str) -> int:
    """テキストマッチのスコアを計算"""
    if not text:
        return 0
    lower = text.lower()
    if lower == query:
        return 10  # 完全一致
    if lower.startswith(query):
        return 7  # 前方一致
    if query in lower:
        return 3  # 部分一致
    return 0


def _array_score(arr: list | None, query: str) -> int:
    """配列内の最大テキストマッチスコア"""
    if not arr or not isinstance(arr, list):
        return 0
    return max((_text_score(item, query) for item in arr if isinstance(item, str)), default=0)


def _tokenize(query: str) -> list[str]:
    """クエリを空白・カンマ・句読点でトークン分割"""
    return [t for t in re.split(r'[\s　,、]+', query.lower()) if t]


def search_objects(
    query: str,
    domain: str | None = None,
    category: str | None = None,
    max_results: int = 10,
) -> dict:
    """オブジェクト検索"""
    db = _get_object_db()
    tokens = _tokenize(query)
    results = []

    for name, obj in db.items():
        if domain and obj.get("domain") != domain:
            continue
        if category and obj.get("category") != category:
            continue

        score = 0
        for token in tokens:
            score += _text_score(name, token) * 10
            score += _text_score(obj.get("category"), token) * 8
            score += _array_score(obj.get("tags"), token) * 5
            score += _array_score(obj.get("tags_ja"), token) * 5
            score += _text_score(obj.get("description"), token) * 3
            score += _text_score(obj.get("description_ja"), token) * 3
            score += _array_score(obj.get("related"), token) * 2

        if score > 0:
            results.append({
                "name": name,
                "score": score,
                "domain": obj.get("domain"),
                "category": obj.get("category"),
                "description": obj.get("description"),
                "description_ja": obj.get("description_ja"),
                "inlets": obj.get("inlets"),
                "outlets": obj.get("outlets"),
                "related": obj.get("related"),
                "rnbo_compatible": obj.get("rnbo_compatible"),
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    limited = results[:max_results]

    return {
        "query": query,
        "domain": domain or "all",
        "category": category or "all",
        "result_count": len(limited),
        "total_matches": len(results),
        "results": limited,
    }


def get_object_detail(name: str) -> dict | None:
    """オブジェクト詳細を取得"""
    db = _get_object_db()
    # 完全一致
    if name in db:
        return {"name": name, **db[name]}
    # 大文字小文字無視
    lower = name.lower()
    for key, obj in db.items():
        if key.lower() == lower:
            return {"name": key, **obj}
    return None


def search_patterns(
    query: str,
    domain: str | None = None,
    max_results: int = 5,
) -> dict:
    """パターン検索（意図ベース）"""
    db = _get_pattern_db()
    tokens = _tokenize(query)
    results = []

    for pattern in db:
        if domain and pattern.get("domain") != domain:
            continue

        score = 0
        for token in tokens:
            score += _text_score(pattern.get("name"), token) * 10
            score += _text_score(pattern.get("name_en"), token) * 10
            score += _text_score(pattern.get("description"), token) * 5
            score += _text_score(pattern.get("description_en"), token) * 5
            score += _array_score(pattern.get("tags"), token) * 8
            score += _array_score(pattern.get("objects"), token) * 3

        if score > 0:
            results.append({**pattern, "score": score})

    results.sort(key=lambda x: x["score"], reverse=True)
    limited = results[:max_results]

    return {
        "query": query,
        "domain": domain or "all",
        "result_count": len(limited),
        "total_matches": len(results),
        "results": limited,
    }


def search_packages(query: str, max_results: int = 5) -> dict:
    """パッケージ検索"""
    db = _get_package_db()
    tokens = _tokenize(query)
    results = []

    for pkg in db:
        score = 0
        for token in tokens:
            score += _text_score(pkg.get("name"), token) * 10
            score += _text_score(pkg.get("id"), token) * 10
            score += _text_score(pkg.get("description"), token) * 5
            score += _text_score(pkg.get("description_en"), token) * 5
            score += _array_score(pkg.get("tags"), token) * 8
            score += _array_score(pkg.get("domain"), token) * 5
            score += _array_score(pkg.get("objects"), token) * 3

        if score > 0:
            results.append({**pkg, "score": score})

    results.sort(key=lambda x: x["score"], reverse=True)
    limited = results[:max_results]

    return {
        "query": query,
        "result_count": len(limited),
        "total_matches": len(results),
        "results": limited,
    }


def lookup_glossary(term: str) -> dict | None:
    """用語集検索（日英対応）"""
    db = _get_glossary_db()
    lower = term.lower()

    # 完全一致（キー）
    if lower in db:
        return {"term": lower, **db[lower]}

    # 日本語名で検索
    for key, entry in db.items():
        if entry.get("ja", "").lower() == lower:
            return {"term": key, **entry}

    # 部分一致
    matches = []
    for key, entry in db.items():
        score = 0
        score += _text_score(key, lower) * 10
        score += _text_score(entry.get("ja"), lower) * 10
        score += _text_score(entry.get("description"), lower) * 3
        score += _text_score(entry.get("description_ja"), lower) * 3
        score += _array_score(entry.get("aliases"), lower) * 5
        if score > 0:
            matches.append({"term": key, "score": score, **entry})

    if matches:
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[0]

    return None
