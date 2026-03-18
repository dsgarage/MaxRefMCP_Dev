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


# --- 設計相談ツール ---


def compare_objects_detail(objects: list[str]) -> dict:
    """複数オブジェクトを比較"""
    if len(objects) < 2:
        return {"error": "比較には2つ以上のオブジェクト名が必要です。"}
    if len(objects) > 5:
        return {"error": "比較は最大5つまでです。"}

    db = _get_object_db()
    found = []
    not_found = []

    for name in objects:
        detail = get_object_detail(name)
        if detail:
            found.append(detail)
        else:
            not_found.append(name)

    if len(found) < 2:
        return {
            "error": "比較に必要な2つ以上のオブジェクトが見つかりません。",
            "not_found": not_found,
        }

    # 比較軸を構築
    comparison = {
        "objects": [],
        "shared_traits": [],
        "differences": [],
    }

    domains = set()
    categories = set()
    rnbo_flags = set()

    for obj in found:
        entry = {
            "name": obj["name"],
            "domain": obj.get("domain"),
            "category": obj.get("category"),
            "description_ja": obj.get("description_ja"),
            "inlet_count": len(obj.get("inlets") or []),
            "outlet_count": len(obj.get("outlets") or []),
            "inlets": obj.get("inlets"),
            "outlets": obj.get("outlets"),
            "rnbo_compatible": obj.get("rnbo_compatible"),
            "related": obj.get("related"),
            "tags_ja": obj.get("tags_ja"),
        }
        comparison["objects"].append(entry)
        domains.add(obj.get("domain"))
        categories.add(obj.get("category"))
        rnbo_flags.add(obj.get("rnbo_compatible"))

    # 共通点
    if len(domains) == 1:
        comparison["shared_traits"].append(f"同じドメイン: {domains.pop()}")
    if len(categories) == 1:
        comparison["shared_traits"].append(f"同じカテゴリ: {categories.pop()}")
    if len(rnbo_flags) == 1:
        val = rnbo_flags.pop()
        comparison["shared_traits"].append(f"RNBO互換性: {'対応' if val else '非対応'}")

    # 相互参照チェック
    names_set = {obj["name"] for obj in found}
    for obj in found:
        related = set(obj.get("related") or [])
        cross_refs = related & names_set - {obj["name"]}
        if cross_refs:
            comparison["shared_traits"].append(
                f"{obj['name']} は {', '.join(cross_refs)} を関連オブジェクトとして参照"
            )

    # 差異
    if len(domains) > 1:
        comparison["differences"].append({
            "aspect": "ドメイン",
            "values": {obj["name"]: obj.get("domain") for obj in found},
        })
    if len(categories) > 1:
        comparison["differences"].append({
            "aspect": "カテゴリ",
            "values": {obj["name"]: obj.get("category") for obj in found},
        })

    inlet_counts = {obj["name"]: len(obj.get("inlets") or []) for obj in found}
    if len(set(inlet_counts.values())) > 1:
        comparison["differences"].append({
            "aspect": "インレット数",
            "values": inlet_counts,
        })

    outlet_counts = {obj["name"]: len(obj.get("outlets") or []) for obj in found}
    if len(set(outlet_counts.values())) > 1:
        comparison["differences"].append({
            "aspect": "アウトレット数",
            "values": outlet_counts,
        })

    if len(rnbo_flags) > 1:
        comparison["differences"].append({
            "aspect": "RNBO互換性",
            "values": {obj["name"]: obj.get("rnbo_compatible") for obj in found},
        })

    result = {
        "comparison": comparison,
        "object_count": len(found),
    }
    if not_found:
        result["not_found"] = not_found

    return result


def suggest_approaches(
    goal: str,
    constraints: list[str] | None = None,
) -> dict:
    """目標に対する実装アプローチを提案"""
    # パターン検索で関連テンプレートを取得
    pattern_results = search_patterns(goal, max_results=5)
    matched_patterns = pattern_results.get("results", [])

    # ゴールからオブジェクト検索も行い、関連オブジェクトを収集
    object_results = search_objects(goal, max_results=10)
    matched_objects = object_results.get("results", [])

    # 制約条件の処理
    constraint_notes = []
    filtered_patterns = matched_patterns
    if constraints:
        for c in constraints:
            cl = c.lower()
            if "rnbo" in cl:
                constraint_notes.append("RNBO互換オブジェクトのみ使用")
                # RNBO非互換オブジェクトを除外
                matched_objects = [
                    o for o in matched_objects if o.get("rnbo_compatible") is not False
                ]
            elif "cpu" in cl or "負荷" in cl or "軽量" in cl:
                constraint_notes.append("CPU負荷を抑える構成を優先")
            elif "live" in cl or "ableton" in cl or "m4l" in cl:
                constraint_notes.append("Max for Live環境での動作を考慮")

    # アプローチ構築
    approaches = []
    for pattern in filtered_patterns:
        approach = {
            "name": pattern.get("name") or pattern.get("name_en"),
            "description": pattern.get("description") or pattern.get("description_en"),
            "objects": pattern.get("objects", []),
            "skill": pattern.get("skill"),
            "relevance_score": pattern.get("score", 0),
        }
        approaches.append(approach)

    # パターンにマッチしなくても、関連オブジェクトから自由構成を提案
    if matched_objects and len(approaches) < 3:
        obj_names = [o["name"] for o in matched_objects[:5]]
        categories = list({o.get("category") for o in matched_objects[:5] if o.get("category")})
        approaches.append({
            "name": "カスタム構成",
            "description": f"関連オブジェクト（{', '.join(obj_names[:3])}等）を組み合わせた構成",
            "objects": obj_names,
            "categories_involved": categories,
            "skill": None,
            "relevance_score": 0,
        })

    return {
        "goal": goal,
        "constraints": constraints or [],
        "constraint_notes": constraint_notes,
        "approach_count": len(approaches),
        "approaches": approaches,
        "related_objects": [
            {"name": o["name"], "category": o.get("category"), "description_ja": o.get("description_ja")}
            for o in matched_objects[:8]
        ],
    }


def explain_connection_detail(source: str, destination: str) -> dict:
    """2オブジェクト間の接続を解説"""
    src = get_object_detail(source)
    dst = get_object_detail(destination)

    if not src:
        return {"error": f"接続元オブジェクト '{source}' が見つかりません。"}
    if not dst:
        return {"error": f"接続先オブジェクト '{destination}' が見つかりません。"}

    src_outlets = src.get("outlets") or []
    dst_inlets = dst.get("inlets") or []

    # 型互換性の判定
    connections = []
    warnings = []

    for oi, outlet in enumerate(src_outlets):
        out_type = outlet.get("type", "unknown")
        for ii, inlet in enumerate(dst_inlets):
            in_type = inlet.get("type", "unknown")

            compatible = _check_type_compatibility(out_type, in_type)
            if compatible["status"] != "incompatible":
                connections.append({
                    "source_outlet": oi,
                    "source_outlet_type": out_type,
                    "source_outlet_desc": outlet.get("description", ""),
                    "dest_inlet": ii,
                    "dest_inlet_type": in_type,
                    "dest_inlet_desc": inlet.get("description", ""),
                    "compatibility": compatible["status"],
                    "note": compatible.get("note", ""),
                })

    # signal → message の警告
    src_is_signal = any(o.get("type") == "signal" for o in src_outlets)
    dst_is_message = all(i.get("type") in ("message", "int", "float", "list") for i in dst_inlets) if dst_inlets else False
    if src_is_signal and dst_is_message:
        warnings.append(
            f"{src['name']} はシグナル出力ですが {dst['name']} はメッセージ入力です。"
            "snapshot~ 等でシグナルをメッセージに変換する必要があります。"
        )

    # 推奨接続の選定
    recommended = None
    if connections:
        # signal-signal の接続を優先、次に最初のインレット
        signal_conns = [c for c in connections if c["compatibility"] == "perfect"]
        recommended = signal_conns[0] if signal_conns else connections[0]

    # 相互参照チェック
    is_related = dst["name"] in (src.get("related") or []) or src["name"] in (dst.get("related") or [])

    return {
        "source": {
            "name": src["name"],
            "domain": src.get("domain"),
            "outlet_count": len(src_outlets),
        },
        "destination": {
            "name": dst["name"],
            "domain": dst.get("domain"),
            "inlet_count": len(dst_inlets),
        },
        "is_related": is_related,
        "possible_connections": connections,
        "recommended": recommended,
        "warnings": warnings,
    }


def _check_type_compatibility(out_type: str, in_type: str) -> dict:
    """出力タイプと入力タイプの互換性を判定"""
    out_t = out_type.lower()
    in_t = in_type.lower()

    # 完全一致
    if out_t == in_t:
        return {"status": "perfect"}

    # signal 同士
    if "signal" in out_t and "signal" in in_t:
        return {"status": "perfect"}

    # message 系は相互互換
    message_types = {"message", "int", "float", "list", "bang", "symbol"}
    if out_t in message_types and in_t in message_types:
        return {"status": "compatible", "note": "メッセージ型の自動変換が行われます"}

    # signal → message は変換が必要
    if "signal" in out_t and in_t in message_types:
        return {"status": "needs_conversion", "note": "snapshot~ でシグナル→メッセージ変換が必要"}

    # message → signal は変換が必要
    if out_t in message_types and "signal" in in_t:
        return {"status": "compatible", "note": "メッセージ値がシグナルレートに変換されます（sig~ 相当）"}

    # 不明な型は接続可能として扱う
    return {"status": "compatible", "note": "型の互換性を確認してください"}


def check_rnbo_compatibility(objects: list[str]) -> dict:
    """RNBOの互換性をチェック"""
    if not objects:
        return {"error": "チェックするオブジェクト名を指定してください。"}

    db = _get_object_db()
    results = {
        "compatible": [],
        "incompatible": [],
        "unknown": [],
        "alternatives": {},
    }

    for name in objects:
        detail = get_object_detail(name)
        if not detail:
            results["unknown"].append({
                "name": name,
                "reason": "データベースに登録されていません",
            })
            continue

        rnbo = detail.get("rnbo_compatible")
        if rnbo is True:
            results["compatible"].append(name)
        elif rnbo is False:
            results["incompatible"].append(name)
            # 同カテゴリのRNBO互換オブジェクトを代替として提案
            category = detail.get("category")
            if category:
                alts = []
                for key, obj in db.items():
                    if (
                        obj.get("category") == category
                        and obj.get("rnbo_compatible") is True
                        and key != detail["name"]
                    ):
                        alts.append(key)
                if alts:
                    results["alternatives"][name] = alts[:3]
        else:
            results["unknown"].append({
                "name": name,
                "reason": "RNBO互換性の情報がありません",
            })

    total = len(objects)
    compatible_count = len(results["compatible"])
    results["summary"] = {
        "total": total,
        "compatible": compatible_count,
        "incompatible": len(results["incompatible"]),
        "unknown": len(results["unknown"]),
        "all_compatible": compatible_count == total,
    }

    return results
