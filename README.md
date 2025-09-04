# ISSL Translation Slack Bot

Slack bot for translation services at ISSL (Institute of Space and Astronautical Science)

## 機能

- `:english-japanese-translation:` リアクションに反応して自動翻訳
- 英語→日本語、日本語→英語の双方向翻訳
- スレッド内およびメインメッセージでの動作
- DMやプライベートチャンネルでも利用可能
- 翻訳処理中は `:eyes:` リアクションで状態表示

## Slack Bot の設定

### 1. Slack アプリの作成

1. [Slack API](https://api.slack.com/apps) にアクセス
2. "Create New App" → "From scratch" を選択
3. アプリ名: `ISSL Translation Bot`
4. ワークスペースを選択

### 2. 必要な権限（OAuth Scopes）

**Bot Token Scopes** に以下を追加:
- `channels:history` - パブリックチャンネルのメッセージ履歴読取
- `channels:read` - パブリックチャンネル情報読取
- `groups:history` - プライベートチャンネルのメッセージ履歴読取
- `groups:read` - プライベートチャンネル情報読取
- `im:history` - DMのメッセージ履歴読取
- `im:read` - DM情報読取
- `mpim:history` - グループDMのメッセージ履歴読取
- `mpim:read` - グループDM情報読取
- `chat:write` - メッセージ送信
- `chat:write.public` - パブリックチャンネルへのメッセージ送信
- `reactions:read` - リアクション読取
- `reactions:write` - リアクション追加/削除

### 3. Socket Mode の有効化

1. "Socket Mode" を有効化
2. App Token を生成（名前: `socket-token`、スコープ: `connections:write`）

### 4. Event Subscriptions の設定

1. "Event Subscriptions" を有効化
2. Request URL は空欄のままでOK（Socket Mode有効時は不要）
3. "Subscribe to bot events" に以下を追加:
   - `reaction_added` - リアクション追加イベント

### 5. ボットをワークスペースに追加

1. "Install to Workspace" ボタンをクリック
2. 権限を確認して承認
3. 招待不要でワークスペース全体で利用可能

## 必要な情報

Slack から取得する必要がある情報:

- **Bot User OAuth Token**: `xoxb-` で始まるトークン（OAuth & Permissions ページ）
- **App Token**: `xapp-` で始まるトークン（Basic Information ページ）
- **OpenAI API Key**: [OpenAI Platform](https://platform.openai.com/api-keys) で生成

## インストールと設定

### 1. 環境変数の設定

`.env.example` を `.env` にコピーして編集:

```bash
cp .env.example .env
```

`.env` ファイル:
```
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_APP_TOKEN=xapp-your-app-token-here
OPENAI_API_KEY=sk-your-openai-api-key-here
TRANSLATION_EMOJI=english-japanese-translation
PROCESSING_EMOJI=eyes
```

### 2. Docker で実行（推奨）

```bash
# ビルドと起動
docker compose up -d

# ログ確認
docker compose logs -f

# 停止
docker compose down
```

### 3. ローカル開発（uv使用）

```bash
# 依存関係インストール
uv pip install -e .

# 直接実行
uv run python -m issl_translation_bot.main
```

## 使用方法

1. 翻訳したいメッセージに `:english-japanese-translation:` リアクションを付ける
2. ボットが `:eyes:` リアクションを追加（処理中表示）
3. 翻訳結果がスレッドに投稿される
4. 処理完了後、`:eyes:` リアクションが自動削除される

## 開発コマンド

```bash
# コードフォーマット
uv run black .
uv run isort .

# リンター
uv run flake8 .

# 型チェック
uv run mypy .
```

## トラブルシューティング

### ボットが反応しない場合

1. 必要な権限が設定されているか確認
2. ワークスペースにボットがインストールされているか確認
3. Socket Mode が有効化されているか確認
4. ログを確認: `docker compose logs -f`

### 翻訳エラーが発生する場合

1. OpenAI API キーが正しく設定されているか確認
2. API クォータが残っているか確認
3. ネットワーク接続を確認