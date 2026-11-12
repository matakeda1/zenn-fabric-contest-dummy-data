# 03_sales_marketing　営業・マーケティング

法人向けオフィスコーヒー事業のキャンペーン → 広告費 → リード → 商談 → 受注。2024-11〜2026-10。

全体の説明はリポジトリ直下の README.md、全列の定義は docs/data_dictionary.md を参照してください。

## ファイル

| ファイル | 行数 | サイズ |
|---|---:|---:|
| `03_sales_marketing/ad_spend_daily.csv` | 1,869 | 0.1 MB |
| `03_sales_marketing/campaigns.csv` | 46 | 0.0 MB |
| `03_sales_marketing/leads.csv` | 10,536 | 2.1 MB |
| `03_sales_marketing/opportunities.csv` | 1,572 | 0.3 MB |
| `03_sales_marketing/opportunity_stage_history.csv` | 7,527 | 0.4 MB |
| `03_sales_marketing/orders.csv` | 441 | 0.1 MB |

### キャンペーン（`campaigns`）

検索広告・SNS 広告・展示会・ウェビナー・ホワイトペーパー・テレアポ・紹介。

- ファイル: `03_sales_marketing/campaigns.csv`
- 行数: 46
- 主キー: `campaign_id`
- 外部キー: owner_employee_id → 04 employees

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `campaign_id` | 文字列 | キャンペーン ID | CP001 |
| `campaign_name` | 文字列 | キャンペーン名 | 検索広告 Google FY24Q3 |
| `channel` | 文字列 | チャネル | 検索広告 |
| `media` | 文字列 | 媒体 | Google 広告 |
| `start_date` | 日付 | 開始日 | 2024-11-01 |
| `end_date` | 日付 | 終了日 | 2024-12-31 |
| `budget_jpy` | 整数 | 予算（円） | 1342000 |
| `target_industry` | 文字列 | ターゲット業種 | 全業種 |
| `target_company_size` | 文字列 | ターゲット企業規模 | 10名以上 |
| `objective` | 文字列 | 目的 | リード獲得 |
| `utm_campaign` | 文字列 | 計測用 UTM パラメータ | cc_001 |
| `owner_employee_id` | 文字列 | 担当者（マーケティング部）の従業員 ID | E10039 |

### 広告費（日次）（`ad_spend_daily`）

デジタル広告は日次の表示回数・クリック・費用・媒体上のコンバージョン。展示会などは実施日に費用を計上。

- ファイル: `03_sales_marketing/ad_spend_daily.csv`
- 行数: 1,869
- 主キー: `spend_id`
- 外部キー: campaign_id → campaigns

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `spend_id` | 文字列 | 広告費 ID | SP000001 |
| `date` | 日付 | 日付 | 2024-11-01 |
| `campaign_id` | 文字列 | キャンペーン ID | CP001 |
| `media` | 文字列 | 媒体 | Google 広告 |
| `impressions` | 整数 | 表示回数 | 8941.0 |
| `clicks` | 整数 | クリック数 | 285.0 |
| `cost_jpy` | 整数 | 費用（円） | 28600 |
| `platform_conversions` | 整数 | 広告媒体が計測したコンバージョン数（CRM のリード数とは一致しない） | 10.0 |

### リード（`leads`）

問い合わせ・資料請求・名刺交換などで獲得した見込み客。会社名は表記ゆれあり（名寄せが必要）。個人名は含まない。

- ファイル: `03_sales_marketing/leads.csv`
- 行数: 10,536
- 主キー: `lead_id`
- 外部キー: campaign_id → campaigns, owner_employee_id → 04 employees, source_inquiry_id → 06 inquiries

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `lead_id` | 文字列 | リード ID | LD2411-00001 |
| `created_at` | 日時 | 獲得日時 | 2024-11-01 00:40:14 |
| `campaign_id` | 文字列 | キャンペーン ID（計測漏れ・自然検索などは空） | CP001 |
| `lead_source` | 文字列 | 獲得経路 | 検索広告 |
| `company_name` | 文字列 | 会社名（入力されたまま。表記ゆれあり） | 有限会社ルピナス電機 |
| `industry` | 文字列 | 業種（未入力あり） | 製造業 |
| `employee_band` | 文字列 | 従業員規模 | 50-99名 |
| `prefecture` | 文字列 | 所在地（都道府県） | 栃木県 |
| `department` | 文字列 | 問い合わせ者の部署 | 営業部 |
| `job_level` | 文字列 | 問い合わせ者の役職 | 経営者 |
| `inquiry_type` | 文字列 | 問い合わせ種別 | 資料請求 |
| `owner_employee_id` | 文字列 | 担当インサイドセールスの従業員 ID | E10113 |
| `first_contact_at` | 日時 | 初回接触日時 | 2024-11-05 09:13:00 |
| `status` | 文字列 | リードのステータス | 育成中 |
| `disqualify_reason` | 文字列 | 対象外の理由 | 重複登録 |
| `lead_score` | 整数 | リードスコア（0〜100） | 30 |
| `source_inquiry_id` | 文字列 | カスタマーサポート経由の場合の問い合わせ ID | INQ20241101-002 |

### 商談（`opportunities`）

リードから商談化した案件。2026-10-31 時点のスナップショット（進行中の案件を含む）。

- ファイル: `03_sales_marketing/opportunities.csv`
- 行数: 1,572
- 主キー: `opportunity_id`
- 外部キー: lead_id → leads, owner_employee_id → 04 employees, branch_department_id → 04 departments

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `opportunity_id` | 文字列 | 商談 ID | OP2411-0001 |
| `lead_id` | 文字列 | リード ID | LD2411-00014 |
| `account_name` | 文字列 | 顧客企業名（正式名称） | 有限会社カモメ建設 |
| `industry` | 文字列 | 業種 | 建設 |
| `employee_band` | 文字列 | 従業員規模 | 1-9名 |
| `prefecture` | 文字列 | 所在地 | 宮城県 |
| `owner_employee_id` | 文字列 | 担当営業の従業員 ID | E10096 |
| `branch_department_id` | 文字列 | 担当部署（営業課・支店） | D200 |
| `created_date` | 日付 | 商談作成日 | 2024-11-09 |
| `stage` | 文字列 | 現在のステージ（初回訪問→ヒアリング→提案→見積提示→交渉→受注 / 失注） | 失注 |
| `probability_pct` | 整数 | 受注確度（%） | 0 |
| `plan` | 文字列 | 提案プラン | ライト |
| `monthly_fee` | 整数 | 月額（円、税抜） | 15000 |
| `contract_months` | 整数 | 契約期間（月） | 12 |
| `initial_fee` | 整数 | 初期費用（円） | 30000 |
| `amount` | 整数 | 契約総額（円） | 210000 |
| `expected_close_date` | 日付 | 受注予定日 | 2024-12-10 |
| `closed_date` | 日付 | 受注・失注日 | 2024-12-10 |
| `is_won` | 真偽 | 受注なら true（進行中は空） | False |
| `lost_reason` | 文字列 | 失注理由 | 要件不一致 |
| `competitor` | 文字列 | 競合（架空） | ノースウィンド・コーヒーサービス |

### 商談ステージ履歴（`opportunity_stage_history`）

商談がどのステージに何日いたか。

- ファイル: `03_sales_marketing/opportunity_stage_history.csv`
- 行数: 7,527
- 主キー: `stage_history_id`
- 外部キー: opportunity_id → opportunities

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `stage_history_id` | 文字列 | ステージ履歴 ID | SH00001 |
| `opportunity_id` | 文字列 | 商談 ID | OP2411-0001 |
| `stage` | 文字列 | ステージ | 初回訪問 |
| `entered_date` | 日付 | ステージに入った日 | 2024-11-09 |
| `exited_date` | 日付 | ステージを出た日（現在のステージは空） | 2024-11-13 |
| `days_in_stage` | 整数 | 滞在日数 | 4.0 |

### 受注（法人契約）（`orders`）

受注した法人契約。

- ファイル: `03_sales_marketing/orders.csv`
- 行数: 441
- 主キー: `order_id`
- 外部キー: opportunity_id → opportunities, owner_employee_id → 04 employees

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `order_id` | 文字列 | 法人受注 ID | BO2502-0001 |
| `opportunity_id` | 文字列 | 商談 ID | OP2411-0002 |
| `account_name` | 文字列 | 顧客企業名 | 株式会社ツグミコンサルティング |
| `order_date` | 日付 | 受注日 | 2025-02-02 |
| `plan` | 文字列 | プラン | プレミアム |
| `contract_start_date` | 日付 | 契約開始日 | 2025-02-27 |
| `contract_months` | 整数 | 契約期間（月） | 12 |
| `monthly_fee` | 整数 | 月額（円、税抜） | 58000 |
| `initial_fee` | 整数 | 初期費用（円） | 80000 |
| `total_contract_value` | 整数 | 契約総額（円） | 776000 |
| `owner_employee_id` | 文字列 | 担当営業の従業員 ID | E10126 |
| `branch_department_id` | 文字列 | 担当部署 | D212 |
| `payment_terms` | 文字列 | 支払条件 | 20日締め翌月10日払い |

