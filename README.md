# Max/MSP Reference MCP Server

Max/MSP・Max4Live の日本語対応リファレンス MCP サーバー。
Claude Desktop から自然言語でオブジェクト、パターン、パッケージ、用語を検索できます。

## ツール一覧

| ツール | 説明 |
|--------|------|
| `search_object` | オブジェクト検索（名前・タグ・日本語キーワード） |
| `get_object` | オブジェクト詳細（インレット/アウトレット等） |
| `search_pattern` | パッチパターン検索（やりたいことを自然言語で） |
| `search_package` | パッケージ・ライブラリ検索 |
| `glossary` | 用語集検索（日英対応） |

## ローカル起動

```bash
pip install -r requirements.txt
python core.py
# → http://localhost:8000/mcp
```

## Claude Desktop で使う

`claude_desktop_config.json` に追加:

```json
{
  "mcpServers": {
    "max-ref": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

## Railway デプロイ

### 初回セットアップ

1. [railway.app](https://railway.app) でアカウント作成（GitHub連携推奨）
2. Railway CLI インストール: `npm i -g @railway/cli && railway login`
3. このリポジトリを GitHub に push
4. Railway Dashboard → New Project → Deploy from GitHub repo
5. デプロイ完了後、Settings → Networking → Generate Domain で URL 取得

### デプロイ後の設定

`claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "max-ref": {
      "url": "https://<your-app>.up.railway.app/mcp"
    }
  }
}
```

## データソース

- **object-db.json** — 128 オブジェクト（MSP/Max/Jitter）
- **pattern-db.json** — 17 パッチパターン
- **package-db.json** — 14 パッケージ
- **glossary-db.json** — 35 用語（日英対応）

## ライセンス

MIT
