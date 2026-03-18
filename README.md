# MaxRefMCP — Max/MSP リファレンス・設計相談 MCP サーバー

Max/MSP・Max4Live の日本語対応リファレンス・設計相談 MCP サーバー。
Claude Code / Claude Desktop から自然言語でオブジェクト仕様の調査、パッチ設計の壁打ち、学習支援が受けられます。

```
Claude Code → MaxRefMCP（調べる・学ぶ・設計する）
           → MaxMCP（作る・操る・制御する）  ← 姉妹プロジェクト
```

---

## ツール一覧

### リファレンス検索（5ツール）

| ツール | 説明 |
|--------|------|
| `maxref.search_object` | オブジェクト検索（名前・タグ・日本語キーワード） |
| `maxref.get_object` | オブジェクト詳細（インレット/アウトレット・仕様書） |
| `maxref.search_pattern` | パッチパターン検索（やりたいことを自然言語で） |
| `maxref.search_package` | パッケージ・ライブラリ検索 |
| `maxref.glossary` | 用語集検索（日英対応） |

### 設計相談（4ツール）

| ツール | 説明 |
|--------|------|
| `maxref.compare_objects` | オブジェクト比較（用途・構成・RNBO互換性を並べて解説） |
| `maxref.suggest_approach` | 実装アプローチ提案（やりたいことから複数案を壁打ち） |
| `maxref.explain_connection` | 接続方法解説（型互換性・推奨接続の判定） |
| `maxref.rnbo_compatibility` | RNBO互換チェック（非対応時は代替提案） |

### フィードバック（2ツール）

| ツール | 説明 |
|--------|------|
| `maxref.report_bug` | バグ報告 → GitHub Issue を自動作成（MaxMCP / MaxRefMCP に自動振り分け） |
| `maxref.request_feature` | 機能追加リクエスト → GitHub Issue を自動作成（自動振り分け） |

> フィードバックツールの利用には環境変数 `GITHUB_TOKEN` の設定が必要です。
> 未設定の場合は手動作成用の URL が返されます。

---

## MaxMCP との使い分け

| | MaxRefMCP（本サーバー） | [MaxMCP](https://github.com/dsgarage/MaxMCP) |
|---|---|---|
| **一言で** | 頭を使う | 手を動かす |
| **役割** | リファレンス・設計相談・学習 | パッチ構築・操作・制御 |
| **接続** | スタンドアロン | Max 9 にWebSocket接続 |
| **発話例** | 「cycle~ と phasor~ の違いは？」 | 「減算シンセを作って」 |

**ワークフロー**: MaxRefMCP で設計を相談 → MaxMCP で実装

---

## セットアップ

### ローカル起動

```bash
pip install -r requirements.txt
python core.py
# → http://localhost:8000/mcp
```

### Claude Code / Claude Desktop で使う

`.mcp.json` または `claude_desktop_config.json` に追加:

```json
{
  "mcpServers": {
    "max-ref": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### Railway デプロイ

1. [railway.app](https://railway.app) でアカウント作成（GitHub連携推奨）
2. Railway CLI インストール: `npm i -g @railway/cli && railway login`
3. このリポジトリを GitHub に push
4. Railway Dashboard → New Project → Deploy from GitHub repo
5. デプロイ完了後、Settings → Networking → Generate Domain で URL 取得

```json
{
  "mcpServers": {
    "max-ref": {
      "url": "https://<your-app>.up.railway.app/mcp"
    }
  }
}
```

---

## テスト

```bash
python -m pytest test_search.py -v
```

---

## データソース

- **object-db.json** — 128 オブジェクト（MSP/Max/Jitter）
- **pattern-db.json** — 17 パッチパターン
- **package-db.json** — 14 パッケージ
- **glossary-db.json** — 36 用語（日英対応）

## ライセンス

MIT
