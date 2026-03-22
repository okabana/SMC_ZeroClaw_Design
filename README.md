# SMC_ZeroClaw_Design

ZeroClaw を bitFlyer 向け SMC トレード環境の **補助・監視・通知エージェント** として使うための Phase 1 実装スキャフォールドです。

## 今回追加したもの

- PostgreSQL の分析テーブルを読む `zeroclaw` CLI
- `latest_bias` / `latest_signal` / `daily_review` / `risk_status` / `zone_summary` の 5 コマンド
- Discord へ流し込みやすい日本語テキストフォーマッタ
- フォーマッタと日付処理のユニットテスト

## ディレクトリ構成

```text
.
├── pyproject.toml
├── README.md
├── src/
│   └── zeroclaw/
│       ├── cli.py
│       ├── db.py
│       ├── formatters.py
│       └── models.py
└── tests/
    └── test_formatters.py
```

## 想定ユースケース

このスキャフォールドは以下の用途を想定しています。

1. PostgreSQL の `market_structure_snapshots` から最新状態を読む
2. `trade_signals` を Discord 向けテキストに整形する
3. `multi_asset_executions` から日次レビューを作る
4. `notifications` と約定状況から簡易リスク状態を確認する
5. `smc_zones` のアクティブ zone を要約する

## インストール

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[postgres,test]
```

## SQL スキーマ

初期テーブルをまとめて作成する SQL を `sql/001_create_core_tables.sql` に追加しています。

```bash
psql 'postgresql://user:pass@localhost:5432/app' -f sql/001_create_core_tables.sql
```

この SQL では以下を作成します。

- `multi_asset_executions`
- `market_structure_snapshots`
- `smc_zones`
- `trade_signals`
- `trade_reviews`
- `notifications`

## CLI 実行例

```bash
zeroclaw latest_bias --dsn 'postgresql://user:pass@localhost:5432/app' --product-code BTC_JPY --timeframe 15m
zeroclaw latest_signal --dsn 'postgresql://user:pass@localhost:5432/app' --product-code BTC_JPY --timeframe 15m
zeroclaw daily_review --dsn 'postgresql://user:pass@localhost:5432/app' --product-code BTC_JPY --review-date 2026-03-22
zeroclaw risk_status --dsn 'postgresql://user:pass@localhost:5432/app' --product-code BTC_JPY
zeroclaw zone_summary --dsn 'postgresql://user:pass@localhost:5432/app' --product-code BTC_JPY --timeframe 15m
```

## 実装メモ

- DB 接続は `psycopg` を optional dependency にしています。
- LLM に生データを渡さず、構造化済みデータから日本語要約を作る方針です。
- 注文執行ロジックは含めていません。
- 勝敗や損益の集計ロジックは、実運用の約定スキーマに合わせて調整してください。

## 次にやるとよいこと

- 実際のスキーマに合わせて SQL を精密化する
- Discord Bot から CLI / Python API を呼び出す
- 日報 / 週報テンプレートを追加する
- 連敗判定や DD 閾値判定を bot 本体の deterministic ルールに接続する
