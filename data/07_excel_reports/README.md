# 07_excel_reports　Excel 帳票（非構造）

8 店舗から提出された書式バラバラの日報（2026-10）と発注書（2026-09〜10）。

全体の説明はリポジトリ直下の README.md、全列の定義は docs/data_dictionary.md を参照してください。

## ファイル

| ファイル | 行数 | サイズ |
|---|---:|---:|
| `07_excel_reports/daily_reports/S01_sapporo/`（31 ファイル） | - | 0.2 MB |
| `07_excel_reports/daily_reports/S03_shibuya/` | - | 0.0 MB |
| `07_excel_reports/daily_reports/S04_shinjuku/` | - | 0.0 MB |
| `07_excel_reports/daily_reports/S08_nagoya/`（31 ファイル） | - | 0.2 MB |
| `07_excel_reports/daily_reports/S10_kyoto/`（30 ファイル） | - | 0.2 MB |
| `07_excel_reports/daily_reports/S11_umeda/`（5 ファイル） | - | 0.0 MB |
| `07_excel_reports/daily_reports/S15_fukuoka/`（30 ファイル） | - | 0.2 MB |
| `07_excel_reports/daily_reports/S16_naha/` | 31 | 0.0 MB |
| `07_excel_reports/master/report_stores.csv` | 8 | 0.0 MB |
| `07_excel_reports/master/supply_items.csv` | 26 | 0.0 MB |
| `07_excel_reports/purchase_orders/S01_sapporo/`（17 ファイル） | - | 0.1 MB |
| `07_excel_reports/purchase_orders/S03_shibuya/`（17 ファイル） | - | 0.1 MB |
| `07_excel_reports/purchase_orders/S04_shinjuku/`（2 ファイル） | - | 0.0 MB |
| `07_excel_reports/purchase_orders/S08_nagoya/`（17 ファイル） | - | 0.1 MB |
| `07_excel_reports/purchase_orders/S10_kyoto/`（17 ファイル） | - | 0.1 MB |
| `07_excel_reports/purchase_orders/S11_umeda/`（17 ファイル） | - | 0.1 MB |
| `07_excel_reports/purchase_orders/S15_fukuoka/`（17 ファイル） | - | 0.1 MB |
| `07_excel_reports/purchase_orders/S16_naha/`（17 ファイル） | - | 0.1 MB |

### 本部の品目マスタ（`supply_items`）

発注書の品名を名寄せするための正式な品目一覧（07_excel_reports/master/）。

- ファイル: `07_excel_reports/master/supply_items.csv`
- 行数: 26
- 主キー: `item_code`

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `item_code` | 文字列 | 品目コード | SP001 |
| `item_name` | 文字列 | 正式品名 | コーヒー豆 ハウスブレンド（業務用） |
| `spec` | 文字列 | 規格 | 1kg |
| `unit` | 文字列 | 単位 | 袋 |
| `case_quantity` | 整数 | 1 ケースあたりの入数 | 10 |
| `unit_price` | 整数 | 単価（円） | 2400 |

### 帳票を提出している店舗（`report_stores`）

日報・発注書を提出している 8 店舗（01 の store_id と共通）。

- ファイル: `07_excel_reports/master/report_stores.csv`
- 行数: 8
- 主キー: `store_id`
- 外部キー: store_id → 01 stores

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `store_id` | 文字列 | 店舗 ID | S01 |
| `store_name` | 文字列 | 店舗名 | 札幌大通店 |

### 帳票の書式（店舗ごとに異なります）

| 店舗 | 日報の書式 | 発注書の書式 |
|---|---|---|
| S01 札幌大通店 | 1 日 1 ファイル・縦型フォーム（結合セル、特記事項欄） | 旧様式（品名は自由記述、数量は「2ケース」など単位つき文字列。ファイル名に年なし） |
| S03 渋谷店 | 月 1 ブック・日別シート（シート名の不統一あり）、時間帯×売上区分の表、結合見出し | 本部様式 v2（品目コードの記入漏れあり） |
| S04 新宿店 | 月 1 ファイルの横持ち表（日付が列）、和暦（令和 8 年）、予算比は文字列 | 月 1 ブック・発注日ごとのシート、左右 2 ブロックの表 |
| S08 名古屋栄店 | 1 日 1 ファイル・英語見出し、**金額は千円単位**、天気は記号（☀☁☂） | 本部様式 v2 |
| S10 京都四条店 | 1 日 1 ファイル、**金額は税抜**、「円」「人」つき文字列・全角数字、和暦（R8.10.1）、外国人客数あり。1 日分が未提出 | 旧様式 |
| S11 梅田店 | 週報（7 日分を縦に積んだブロック、日付セルを縦に結合） | 本部様式 v2 |
| S15 福岡天神店 | 1 日 1 ファイル、承認欄つきで表は 10 行目から。2 日分が未提出、1 日分は「(修正版)」ファイルあり | 本部様式 v2 |
| S16 那覇国際通り店 | **CSV（Shift_JIS）** の月次ファイル、金額はカンマつき文字列 | 英語見出しのシート、半角カナ・全角数字の混在 |

品名の表記ゆれ（例：「牛乳」「ミルク」「ﾐﾙｸ」、「オーツミルク」「オートミルク」「Oat milk」）は、`master/supply_items.csv` の正式品名へ名寄せしてください。
日報の売上は POS（01_retail_ec の orders）と突き合わせられます。手入力による転記ミスも少し含まれます。
