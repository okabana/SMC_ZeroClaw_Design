# SMC_ZeroClaw_Design

## 1. 目的

ZeroClaw を、bitFlyer 向け SMC トレード環境における **補助・監視・通知エージェント** として利用する。
ZeroClaw 自体は **注文執行の主体にはしない**。
注文執行は別の deterministic な売買ボット本体が担当し、ZeroClaw は以下を担当する。

* 市場状況の要約
* SMC 観点のシナリオ整理
* Discord 通知
* 日次 / 週次レビュー
* リスク監視
* トレード判断の補助

---

## 2. 基本方針

### 2.1 ZeroClaw の役割

ZeroClaw は以下の役割に限定する。

* Discord 上の会話インターフェース
* PostgreSQL に保存された分析結果の要約
* シグナルや異常状態の通知
* トレードレビュー生成
* 手動判断支援

### 2.2 ZeroClaw にやらせないこと

以下は ZeroClaw に直接やらせない。

* 成行 / 指値注文の直接発行
* ポジションサイズの最終決定
* SL / TP の最終決定
* 曖昧な自然言語のみを入力とした注文執行
* API エラー時の自律リトライ注文

### 2.3 設計思想

売買ロジックは必ず deterministic にする。
LLM は以下に限定する。

* 解釈
* 要約
* 優先順位付け
* 説明
* 通知文生成
* レビュー

---

## 3. 想定アーキテクチャ

```text
[Market Data / Exchange API]
          |
          v
 [Trading Engine / SMC Analyzer]
          |
          +--> [PostgreSQL]
          |
          +--> [Signal / Event Publisher]
                         |
                         v
                    [ZeroClaw]
                         |
                         v
                     [Discord]
```

### 3.1 構成要素

* **Trading Engine**

  * 市場データ取得
  * SMC 判定
  * 売買判断
  * 注文執行
  * リスク制御
* **PostgreSQL**

  * 約定履歴
  * 分析結果
  * シグナル履歴
  * 通知履歴
  * レビュー対象データ
* **ZeroClaw**

  * Discord 応答
  * DB 読み出し結果の要約
  * アラート文面生成
  * トレードレビュー
* **Discord**

  * 人間の確認
  * 指示
  * レポート受信
  * 手動承認

---

## 4. SMC で扱う主要概念

ZeroClaw は以下の概念を理解し、それを説明・要約できる必要がある。

* Market Structure
* HH / HL / LH / LL
* BOS
* CHoCH
* Liquidity
* Equal Highs / Equal Lows
* Buy-side liquidity / Sell-side liquidity
* Liquidity Sweep
* Order Block
* Breaker
* Fair Value Gap
* Mitigation
* Premium / Discount
* Session bias
* Displacement
* MSS

---

## 5. 役割分担

## 5.1 Trading Engine

責務:

* OHLCV / ticker / order book / execution 取得
* 上位足 / 下位足構造判定
* BOS / CHoCH 判定
* FVG / OB / liquidity sweep 判定
* エントリー条件判定
* SL / TP 算出
* 注文執行
* 約定後の状態更新
* PostgreSQL への保存

## 5.2 ZeroClaw

責務:

* 状況説明
* トレード候補の自然言語化
* 監視通知
* 日報 / 週報
* ルール逸脱レビュー
* Discord からの問い合わせ応答

---

## 6. ZeroClaw の具体的ユースケース

### 6.1 現在の構造確認

例:

* BTC/JPY の上位足バイアスは？
* 15分足の直近 BOS はどちらか？
* CHoCH は発生したか？
* premium / discount のどこか？

### 6.2 エントリー候補整理

例:

* 現在の候補シナリオを優先順で出す
* ロング条件は何が揃っているか
* 未充足条件は何か
* 無理なエントリーかどうか

### 6.3 イベント通知

例:

* 重要 OB への再接触
* liquidity sweep 発生
* FVG 埋め完了
* 上位足バイアス転換
* 連敗上限到達
* DD 閾値超過

### 6.4 レビュー

例:

* 今日のトレードを総括して
* ルール逸脱があったか
* 損失トレードの共通点は何か
* どの条件がノイズだったか

---

## 7. Discord での想定コマンド / 問い合わせ

自然言語ベースでよいが、運用しやすくするため代表コマンドを決める。

### 7.1 状況確認系

* `@bot BTC/JPY の上位足バイアス`
* `@bot 15分足の構造を要約`
* `@bot 直近の BOS と CHoCH`
* `@bot いまの主要 liquidity を整理`

### 7.2 エントリー補助系

* `@bot 今のエントリー候補`
* `@bot ロング条件の充足率`
* `@bot この価格帯は discount か`
* `@bot FVG と OB の優先順位`

### 7.3 運用監視系

* `@bot 今日の損益`
* `@bot 連敗回数`
* `@bot 現在のDD`
* `@bot 最新の異常通知`

### 7.4 レビュー系

* `@bot 今日のトレードレビュー`
* `@bot 直近3トレードの反省点`
* `@bot ルール逸脱一覧`
* `@bot 勝ちパターンと負けパターン`

---

## 8. PostgreSQL の想定テーブル

最低限、以下があるとよい。

### 8.1 約定履歴

`multi_asset_executions`

想定カラム:

* id
* side
* price
* size
* exec_date
* product_code

### 8.2 市場構造スナップショット

`market_structure_snapshots`

想定カラム:

* id
* product_code
* timeframe
* captured_at
* bias
* last_bos
* last_choch
* swing_high
* swing_low
* premium_discount_state
* note_json

### 8.3 liquidity / zone

`smc_zones`

想定カラム:

* id
* product_code
* timeframe
* zone_type
* price_from
* price_to
* created_at
* is_active
* strength_score
* meta_json

### 8.4 シグナル履歴

`trade_signals`

想定カラム:

* id
* product_code
* timeframe
* signal_type
* direction
* score
* detected_at
* status
* reason_json

### 8.5 レビュー履歴

`trade_reviews`

想定カラム:

* id
* review_date
* product_code
* period_type
* summary
* good_points
* bad_points
* violations
* improvement_actions
* created_at

### 8.6 通知履歴

`notifications`

想定カラム:

* id
* channel
* category
* message
* sent_at
* related_signal_id
* severity

---

## 9. ZeroClaw に渡す入力データ方針

ZeroClaw に生データを丸投げしない。
以下のような **構造化済み JSON** を渡す前提にする。

例:

```json
{
  "product_code": "BTC_JPY",
  "timeframe": "15m",
  "bias": "bullish",
  "last_bos": "up",
  "last_choch": null,
  "liquidity": {
    "buy_side": [11250000, 11280000],
    "sell_side": [11190000]
  },
  "zones": [
    {
      "type": "bullish_ob",
      "from": 11212000,
      "to": 11218000,
      "strength": 0.83
    },
    {
      "type": "fvg",
      "from": 11221000,
      "to": 11226000,
      "strength": 0.76
    }
  ],
  "entry_conditions": {
    "htf_bias_aligned": true,
    "liquidity_swept": true,
    "choch_confirmed": false,
    "displacement_confirmed": true,
    "fvg_reentry": false
  }
}
```

ZeroClaw はこの JSON を元に、日本語で説明・要約・優先順位付けを行う。

---

## 10. ZeroClaw 用 system prompt 方針

以下の性格を持たせる。

### 10.1 基本ロール

* あなたは SMC に基づいて市場構造を解釈するトレード支援 AI
* あなたは注文執行者ではない
* あなたは判断補助、監視、レビュー、説明を担当する

### 10.2 行動原則

* 不明確なときは断定しない
* シグナルの強さと前提条件を分けて説明する
* エントリー推奨時は、必ず未充足条件も示す
* リスク管理を最優先する
* 感情的な表現を避ける
* 事実と推測を明確に分ける

### 10.3 出力ルール

* まず結論
* 次に根拠
* 次に未充足条件
* 最後に監視ポイント
* 数値がある場合は必ず明示
* わからない場合は「データ不足」と明示

---

## 11. 推奨出力フォーマット

### 11.1 市場要約

```text
結論:
15分足は bullish 維持。ただし直近高値手前で buy-side liquidity を意識。

根拠:
- 上位足バイアスは上
- 直近 BOS は上方向
- sell-side liquidity sweep 後の反発を確認
- bullish OB が有効

未充足条件:
- 1分足 CHoCH 未確認
- FVG 再侵入待ち

監視ポイント:
11218000 再接触
11226000 の流動性反応
```

### 11.2 エントリー候補

```text
候補:
ロング監視優先

理由:
- 上位足 bullish
- sell-side liquidity sweep 済み
- bullish OB 内に滞在
- displacement は確認済み

不足:
- 下位足 CHoCH 未確定
- FVG リテスト未発生

注意:
現時点では先走りエントリーに注意
```

### 11.3 レビュー

```text
総評:
構造認識は良かったが、エントリータイミングが早かった。

良かった点:
- 上位足バイアスに逆らっていない
- liquidity の位置認識は妥当

問題点:
- CHoCH 未確定で進入
- RR の悪い位置でエントリー

改善:
- 下位足確認を必須化
- FVG 再侵入待ちを厳守
```

---

## 12. 通知カテゴリ設計

通知はカテゴリを分ける。

* `structure_update`
* `entry_candidate`
* `entry_blocked`
* `risk_warning`
* `drawdown_alert`
* `execution_result`
* `daily_review`
* `weekly_review`
* `system_error`

重大度:

* info
* warning
* critical

---

## 13. リスク管理の扱い

ZeroClaw は以下を監視し、閾値超過時に通知する。

* 日次最大損失
* 週次最大損失
* 連敗回数
* 同一時間帯の過剰取引
* 指定回数以上の早すぎる損切
* API エラー連続発生
* DB 保存失敗
* 約定と戦略状態の不整合

ZeroClaw は「止めるべき」と判断しても、停止命令自体は deterministic なボット本体側が受け持つのが望ましい。

---

## 14. 開発フェーズ

### フェーズ1: 読み取り専用

* PostgreSQL の最新状態を読んで Discord で返答
* 約定履歴の要約
* 手動レビュー

### フェーズ2: 通知

* 条件一致時の Discord 通知
* DD / 連敗 / 異常監視
* 日報 / 週報

### フェーズ3: 半自動承認

* ZeroClaw が候補を説明
* 人間が承認
* 売買ボット本体が注文

### フェーズ4: 自動化補助強化

* 複数シナリオ比較
* 時間帯別統計コメント
* ルール逸脱分析の高度化

---

## 15. 初期実装で優先すべき機能

優先順位は以下。

1. PostgreSQL から最新分析結果を読む
2. Discord で「上位足バイアス」「直近 BOS / CHoCH」「候補シナリオ」を返す
3. DD / 連敗 / 異常通知
4. 日次レビュー
5. 直近3トレードの改善提案

---

## 16. Codex に依頼する実装タスク例

### タスク1

PostgreSQL の `market_structure_snapshots` から最新データを取得し、ZeroClaw から読める JSON として返す API / スクリプトを実装する。

### タスク2

`trade_signals` の最新候補を Discord 向けテキストに変換するヘルパーを実装する。

### タスク3

`multi_asset_executions` を元に日次レビュー用の集計を行う SQL を作成する。

### タスク4

ZeroClaw から呼び出す補助コマンドとして、以下を実装する。

* latest_bias
* latest_signal
* daily_review
* risk_status
* zone_summary

### タスク5

Discord 通知テンプレートをカテゴリ別に実装する。

---

## 17. 最終結論

ZeroClaw は SMC トレーダーの **思考整理・監視・通知・レビュー担当** として使うのが最適。
売買そのものは別の deterministic な bot に任せる。
この構成により、以下を両立できる。

* 安全性
* 再現性
* 説明性
* 運用しやすさ
* 将来的な拡張性

