# 06_customer_support　カスタマーサポート（非構造・半構造）

問い合わせ本文（日本語の自由記述）と受付日時・チャネル・関連商品・対応状況。2024-01〜2026-10。

全体の説明はリポジトリ直下の README.md、全列の定義は docs/data_dictionary.md を参照してください。

## ファイル

| ファイル | 行数 | サイズ |
|---|---:|---:|
| `06_customer_support/inquiries.csv` | 9,378 | 4.2 MB |
| `06_customer_support/inquiries.jsonl` | 9,378 | 7.3 MB |

### 問い合わせ（`inquiries`）

約 9,400 件。本文は日本語の自由記述（メール・Web フォーム・電話メモ・チャット・アプリ・SNS・店頭）。本文に改行を含むため CSV は複数行のセルあり（同じ内容の JSON Lines 版 inquiries.jsonl も同梱）。

- ファイル: `06_customer_support/inquiries.csv`
- 行数: 9,378
- 主キー: `inquiry_id`
- 外部キー: customer_id → 01 customers, order_id → 01 orders, product_id → 01 products, store_id → 01 stores, assignee_employee_id → 04 employees, lot_no → 02 production_lots

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `inquiry_id` | 文字列 | 問い合わせ ID | INQ20240101-001 |
| `received_at` | 日時 | 受付日時 | 2024-01-01 10:44:27 |
| `channel` | 文字列 | チャネル（電話 / メール / Webフォーム / チャット / アプリ内 / SNS / 店頭） | 電話 |
| `customer_id` | 文字列 | 顧客 ID（特定できた場合） | C006480 |
| `order_id` | 文字列 | 関連する受注 ID | EC240104-00008 |
| `product_id` | 文字列 | 関連する商品 ID | P059 |
| `store_id` | 文字列 | 関連する店舗 ID | S14 |
| `category` | 文字列 | 大分類（担当者が付与。未分類あり） | 法人・大口 |
| `subcategory` | 文字列 | 小分類（未分類あり） | 法人・大口 |
| `subject` | 文字列 | 件名 | 記念品として焼き菓子アソートを30個。法人割引・請求書払いの |
| `body` | 文字列 | 本文（自由記述） | 【入電 10:44】 お客様より、記念品として焼き菓子アソートを30個。法人割引… |
| `status` | 文字列 | 対応状況 | 完了 |
| `priority` | 文字列 | 優先度 | 中 |
| `assigned_team` | 文字列 | 担当チーム | 法人営業部 |
| `assignee_employee_id` | 文字列 | 担当者の従業員 ID | E10112 |
| `first_response_at` | 日時 | 初回回答日時 | 2024-01-01 10:46:27 |
| `closed_at` | 日時 | 完了日時 | 2024-01-02 22:04:50 |
| `csat_score` | 整数 | 顧客満足度アンケート（1〜5、回答者のみ） | 5.0 |
| `lot_no` | 文字列 | ロット番号（担当者が入力できた場合） | L260710-R2-06 |

