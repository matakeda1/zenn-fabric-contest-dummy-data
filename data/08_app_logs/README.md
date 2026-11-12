# 08_app_logs　アプリ操作ログ（半構造・JSON）

公式アプリのイベントログ（JSON Lines、1 日 1 ファイル）。2026-09〜10。

全体の説明はリポジトリ直下の README.md、全列の定義は docs/data_dictionary.md を参照してください。

## ファイル

| ファイル | 行数 | サイズ |
|---|---:|---:|
| `08_app_logs/app_releases.csv` | 12 | 0.0 MB |
| `08_app_logs/events/`（61 ファイル） | 133,648 | 82.7 MB |

### アプリのリリース履歴（`app_releases`）

iOS / Android のバージョンとリリース日・内容。

- ファイル: `08_app_logs/app_releases.csv`
- 行数: 12
- 主キー: `platform + app_version`

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `platform` | 文字列 | iOS / Android | iOS |
| `app_version` | 文字列 | バージョン | 4.9.3 |
| `release_date` | 日付 | リリース日 | 2025-03-10 |
| `release_note` | 文字列 | リリース内容 | 旧アーキテクチャ最終版（サポート継続中） |

### イベントの JSON 構造

1 行 = 1 イベントの JSON Lines です（`events/app_events_YYYY-MM-DD.jsonl`、受信日ごと）。新しいアプリ（v5 系）と旧アプリ（4.9.3）でスキーマが異なります。

**v5 系（`schema_version: "5"`、ネストあり）**

| パス | 説明 |
|---|---|
| `event_id` | イベント ID（再送により同じ ID の重複行あり） |
| `event_name` | `app_open` `screen_view` `search` `view_item_list` `view_item` `add_to_cart` `remove_from_cart` `view_cart` `begin_checkout` `add_payment_info` `purchase` `error` `coupon_display` `store_search` `push_open` `app_background` |
| `event_timestamp` | 端末での発生時刻（ISO 8601、+09:00。一部の端末は誤って `Z` 表記） |
| `received_at` | サーバー受信時刻（オフライン時はまとめて遅れて届く） |
| `user.anonymous_id` | 端末ごとの匿名 ID |
| `user.member_id_hash` | ログイン会員のハッシュ ID（customer_id とは直接結合できない） |
| `user.is_logged_in` | ログイン状態 |
| `session.session_id` / `session_seq` / `traffic_source` | セッション ID、通算セッション番号、流入元（organic / push / deeplink / ad） |
| `screen.name` / `screen.previous` | 画面名と直前の画面 |
| `device.platform` / `os_version` / `model` / `app_version` / `locale` | 端末情報 |
| `geo.prefecture` | 都道府県（会員登録情報ベース。未ログインは空） |
| `params` | イベント固有の値。`view_item` などは商品（`product_id` ほか）、`search` は `search_term`、`error` は `error_code` / `error_message`、`purchase` は `order_id`・`value`・`items`（配列） |

**旧アプリ 4.9.3（フラットな旧スキーマ）**: `eventId` `name` `ts`（UNIX エポックミリ秒）`uid` `memberHash` `sid` `screenName` `os` `appVer` `itemId` `price` `qty` `orderNo` `amount` `items`（"P001x1,P096x1" 形式の文字列）`keyword` `err` `coupon` `store`

`purchase` イベントの `order_id`（旧スキーマは `orderNo`）は 01_retail_ec の `orders.order_id` と一致し、閲覧から購入までを受注データとつなげて分析できます。
