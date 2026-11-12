# データ辞書（全テーブル・全列）

> このファイルは `tools/build_docs.py` で生成しています。列の型はデータから推定しています。

## 00_common　共通マスタ

全データセットで共通に使えるカレンダー（祝日・会計年度つき）。

### カレンダー（`calendar`）

日付ディメンション。祝日・会社の会計年度（4 月始まり）つき。2026-12-31 まで。

- ファイル: `00_common/calendar.csv`
- 行数: 1,096
- 主キー: `date`

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `date` | 日付 | 日付 | 2024-01-01 |
| `year` | 整数 | 年 | 2024 |
| `month` | 整数 | 月 | 1 |
| `day` | 整数 | 日 | 1 |
| `year_month` | 文字列 | 年月（YYYY-MM） | 2024-01 |
| `weekday_num` | 整数 | 曜日番号（月=1〜日=7） | 1 |
| `weekday_ja` | 文字列 | 曜日（日本語） | 月 |
| `is_weekend` | 真偽 | 土日フラグ | False |
| `is_holiday` | 真偽 | 祝日・振替休日フラグ | True |
| `holiday_name` | 文字列 | 祝日名 | 元日 |
| `is_business_day` | 真偽 | 本社の営業日フラグ（土日祝・年末年始 12/30〜1/3 を除く） | False |
| `fiscal_year` | 整数 | 会計年度（4 月始まり。例：2025-04〜2026-03 は 2025） | 2023 |
| `fiscal_quarter` | 文字列 | 会計四半期（例：FY2025Q1） | FY2023Q4 |
| `week_start_date` | 日付 | 週の開始日（月曜） | 2024-01-01 |
| `season` | 文字列 | 季節（春夏秋冬） | 冬 |

## 01_retail_ec　小売・EC

直営店の POS とオンラインストア（Web・アプリ・定期便）の受注データ。2024-01〜2026-10。

### 店舗（`stores`）

直営 16 店舗（閉店 1・新規出店 2 を含む）とオンラインストア（W01）。最寄りの気象庁観測所つき。

- ファイル: `01_retail_ec/stores.csv`
- 行数: 17
- 主キー: `store_id`

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `store_id` | 文字列 | 店舗 ID（S01〜S16、オンラインは W01）。05 の site_id と共通 | S01 |
| `store_name` | 文字列 | 店舗名 | 札幌大通店 |
| `store_type` | 文字列 | 直営店 / EC | 直営店 |
| `area_type` | 文字列 | 立地（オフィス街・駅前・繁華街・商業地・商業施設・住宅地・観光地） | 商業地 |
| `prefecture` | 文字列 | 都道府県 | 北海道 |
| `city` | 文字列 | 市区町村 | 札幌市中央区 |
| `latitude` | 小数 | 緯度（概略） | 43.0606 |
| `longitude` | 小数 | 経度（概略） | 141.3544 |
| `open_date` | 日付 | 開店日 | 2016-04-01 |
| `close_date` | 日付 | 閉店日（営業中は空） | 2025-12-28 |
| `open_time` | 文字列 | 開店時刻 | 09:00 |
| `close_time` | 文字列 | 閉店時刻 | 20:00 |
| `seat_count` | 整数 | 客席数 | 24 |
| `floor_area_m2` | 整数 | 床面積（㎡） | 120 |
| `jma_station_name` | 文字列 | 最寄りの気象庁観測所名（気象データ結合用） | 札幌 |
| `jma_prec_no` | 整数 | 気象庁「過去の気象データ検索」の府県番号（prec_no） | 14.0 |
| `jma_block_no` | 整数 | 気象庁「過去の気象データ検索」の地点番号（block_no） | 47412.0 |

### 商品（`products`）

コーヒー豆・ドリップバッグ・店内ドリンク・焼き菓子・ボトル飲料・ギフト・器具・定期便の 77 商品。

- ファイル: `01_retail_ec/products.csv`
- 行数: 77
- 主キー: `product_id`

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `product_id` | 文字列 | 商品 ID | P001 |
| `product_name` | 文字列 | 商品名 | ハウスブレンド 200g |
| `category` | 文字列 | カテゴリ | コーヒー豆 |
| `subcategory` | 文字列 | サブカテゴリ | ブレンド |
| `size` | 文字列 | 規格・容量 | 200g |
| `sales_channel` | 文字列 | 販売チャネル（店舗のみ / オンラインのみ / 店舗・オンライン / 定期便） | 店舗・オンライン |
| `serving_temp` | 文字列 | ドリンクの提供温度（ホット / アイス / 両方） | ホット |
| `launch_price` | 整数 | 発売時（または 2024-01 時点）の税抜単価（円） | 1300 |
| `current_price` | 整数 | 2026-10 時点の税抜単価（円） | 1500 |
| `unit_cost` | 整数 | 原価（円、概算） | 600 |
| `tax_category` | 文字列 | 消費税区分（軽減税率対象 / 標準税率） | 軽減税率対象（飲食料品） |
| `launch_date` | 日付 | 発売日 | 2012-01-01 |
| `end_date` | 日付 | 販売終了日 | 2025-06-30 |
| `sales_season` | 文字列 | 販売時期（MM-DD〜MM-DD、季節限定のみ） | 11-01〜01-31 |
| `lot_managed` | 真偽 | 自社工場で製造しロット管理している商品か（02 の production_lots と結合可） | True |

### 商品価格履歴（`product_price_history`）

税抜単価の改定履歴（2025-04-01・2026-04-01 に価格改定）。

- ファイル: `01_retail_ec/product_price_history.csv`
- 行数: 160
- 主キー: `price_id`
- 外部キー: product_id → products

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `price_id` | 文字列 | 価格履歴 ID | PR0001 |
| `product_id` | 文字列 | 商品 ID | P001 |
| `valid_from` | 日付 | 適用開始日 | 2024-01-01 |
| `valid_to` | 日付 | 適用終了日（この日の前日まで有効。現行価格は空） | 2025-04-01 |
| `unit_price` | 整数 | 税抜単価（円） | 1300 |

### 販促（`promotions`）

セール・キャンペーン・クーポンの一覧。

- ファイル: `01_retail_ec/promotions.csv`
- 行数: 20
- 主キー: `promotion_id`

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `promotion_id` | 文字列 | 販促 ID | PM001 |
| `promotion_code` | 文字列 | 販促コード（orders.promotion_code と結合） | NY2024 |
| `promotion_name` | 文字列 | 販促名 | 新春セール 2024 |
| `channel` | 文字列 | 対象チャネル | オンラインストア |
| `start_date` | 日付 | 開始日 | 2024-01-01 |
| `end_date` | 日付 | 終了日 | 2024-01-05 |
| `target_category` | 文字列 | 対象カテゴリ（カンマ区切り） | 全商品 |
| `discount_type` | 文字列 | 割引種別（割引率 / 値引額 / フェア） | 割引率 |
| `discount_value` | 整数 | 割引値（% または円） | 10 |
| `coupon_code` | 文字列 | お客様が入力・提示するクーポンコード | NY2024 |
| `note` | 文字列 | 備考 | 創業記念。店舗・オンラインとも対象（オンラインはクーポンコード入力） |

### 顧客（会員）（`customers`）

会員 約 3.2 万人。氏名・連絡先は含まない（匿名化済み）。

- ファイル: `01_retail_ec/customers.csv`
- 行数: 32,459
- 主キー: `customer_id`
- 外部キー: home_store_id → stores

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `customer_id` | 文字列 | 顧客 ID | C000001 |
| `registered_date` | 日付 | 会員登録日 | 2016-01-15 |
| `registration_channel` | 文字列 | 登録経路（店舗 / オンラインストア / アプリ） | 店舗 |
| `gender` | 文字列 | 性別（女性 / 男性 / その他・無回答） | 女性 |
| `birth_year` | 整数 | 生まれ年 | 1979 |
| `prefecture` | 文字列 | 居住都道府県 | 大阪府 |
| `home_store_id` | 文字列 | よく利用する店舗（店舗登録の会員など） | S11 |
| `app_user` | 真偽 | 公式アプリ利用者か | True |
| `mail_opt_in` | 真偽 | メール配信の許諾 | True |
| `member_rank` | 文字列 | 会員ランク（直近 12 か月の購入額で判定） | レギュラー |
| `status` | 文字列 | 有効 / 退会 | 有効 |
| `withdrawn_date` | 日付 | 退会日 | 2016-08-06 |

### 定期便契約（`subscriptions`）

2024-06 開始の定期便（毎月お届け）の契約。解約理由つき。

- ファイル: `01_retail_ec/subscriptions.csv`
- 行数: 3,210
- 主キー: `subscription_id`
- 外部キー: customer_id → customers, product_id → products

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `subscription_id` | 文字列 | 定期便契約 ID | SUB00001 |
| `customer_id` | 文字列 | 顧客 ID | C014757 |
| `product_id` | 文字列 | 定期便商品 ID | P100 |
| `start_date` | 日付 | 開始日 | 2024-06-02 |
| `billing_day` | 整数 | 毎月のお届け（決済）日 | 2 |
| `status` | 文字列 | 継続中 / 解約 | 継続中 |
| `cancel_date` | 日付 | 解約日 | 2025-02-27 |
| `cancel_reason` | 文字列 | 解約理由（選択式） | 飲みきれず在庫が余る |
| `skip_count` | 整数 | スキップした回数 | 4 |

### 店舗の休業・短縮営業（`store_closures`）

年始休業・改装休業、大雨・大雪による臨時休業や短縮営業の記録。

- ファイル: `01_retail_ec/store_closures.csv`
- 行数: 141
- 主キー: `closure_id`
- 外部キー: store_id → stores

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `closure_id` | 文字列 | 休業記録 ID | CL0001 |
| `store_id` | 文字列 | 店舗 ID | S01 |
| `date` | 日付 | 日付 | 2024-01-01 |
| `closure_type` | 文字列 | 年始休業 / 改装休業 / 臨時休業 / 短縮営業 | 年始休業 |
| `reason` | 文字列 | 理由 | 元日休業 |

### 受注（ヘッダ）（`orders`）

店舗の会計（レシート）・オンライン注文・定期便の 1 件 = 1 行。年ごとに分割（orders/ フォルダ）。

- ファイル: `01_retail_ec/orders/（3 ファイル）`
- 行数: 494,189
- 主キー: `order_id`
- 外部キー: store_id → stores, customer_id → customers, promotion_code → promotions

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `order_id` | 文字列 | 受注 ID（店舗：S03-240105-0042、オンライン：EC240105-00012、定期便：SB240105-00003） | EC240101-00001 |
| `order_datetime` | 日時 | 受注日時（店舗は会計時刻） | 2024-01-01 00:01:13 |
| `channel` | 文字列 | 店舗 / オンラインストア / 定期便 | オンラインストア |
| `store_id` | 文字列 | 店舗 ID（オンライン・定期便は W01） | W01 |
| `customer_id` | 文字列 | 顧客 ID（店舗で会員カード・アプリ提示なしの場合は空） | C010327 |
| `device` | 文字列 | 店頭 / Web / アプリ / 定期便 | Web |
| `eat_in` | 文字列 | 店内 / 持ち帰り（店舗のみ。店内飲食の飲食料品は 10%） | 店内 |
| `payment_method` | 文字列 | 支払方法 | コンビニ後払い |
| `item_count` | 整数 | 点数（数量の合計） | 2 |
| `subtotal_excl_tax` | 整数 | 税抜小計（値引後） | 2600 |
| `discount_total` | 整数 | 値引額の合計 | 0 |
| `tax_total` | 整数 | 消費税額 | 208 |
| `shipping_fee` | 整数 | 送料（税込。店舗は 0） | 550 |
| `total_incl_tax` | 整数 | 税込合計（小計 + 消費税 + 送料） | 3358 |
| `coupon_code` | 文字列 | 利用されたクーポンコード | NY2024 |
| `promotion_code` | 文字列 | 適用された販促コード | NY2024 |
| `order_status` | 文字列 | 完了 / キャンセル / 返品 / 出荷済み / 受付済み | 完了 |
| `shipping_prefecture` | 文字列 | お届け先都道府県（オンライン・定期便） | 秋田県 |
| `shipped_date` | 日付 | 出荷日 | 2024-01-04 |
| `promised_delivery_date` | 日付 | お届け予定日（注文時点） | 2024-01-05 |
| `delivered_date` | 日付 | お届け日（実績） | 2024-01-05 |
| `returned_date` | 日付 | 返品受付日 | 2024-01-18 |

### 受注明細（`order_lines`）

受注 1 件に含まれる商品ごとの明細。年ごとに分割（order_lines/ フォルダ）。

- ファイル: `01_retail_ec/order_lines/（3 ファイル）`
- 行数: 788,448
- 主キー: `order_line_id`
- 外部キー: order_id → orders, product_id → products

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `order_line_id` | 文字列 | 受注明細 ID（order_id + 行番号） | S01-240102-0001-01 |
| `order_id` | 文字列 | 受注 ID | S01-240102-0001 |
| `line_no` | 整数 | 行番号 | 1 |
| `product_id` | 文字列 | 商品 ID | P030 |
| `quantity` | 整数 | 数量 | 2 |
| `unit_price` | 整数 | 税抜単価（円、販売時点の価格） | 420 |
| `discount_amount` | 整数 | 値引額（円） | 0 |
| `line_subtotal` | 整数 | 税抜金額（単価×数量−値引） | 840 |
| `tax_rate` | 小数 | 消費税率（0.08 / 0.10） | 0.1 |
| `tax_amount` | 整数 | 消費税額（明細ごとに切り捨て） | 84 |
| `line_total` | 整数 | 税込金額 | 924 |

## 02_manufacturing_iot　製造・IoT

熊谷工場の設備マスタ、1 分ごとのセンサー値（2026-05〜10）、故障・保全履歴（2025-01〜）、製造ロット。

### 設備（`equipment`）

熊谷工場の主要設備 8 台。

- ファイル: `02_manufacturing_iot/equipment.csv`
- 行数: 8
- 主キー: `equipment_id`
- 外部キー: site_id → 05 sites

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `equipment_id` | 文字列 | 設備 ID | RST-01 |
| `equipment_name` | 文字列 | 設備名 | 焙煎機 1号機 |
| `equipment_type` | 文字列 | 設備種別（sensor_definitions と結合） | 焙煎機 |
| `line` | 文字列 | ライン | 焙煎ライン |
| `site_id` | 文字列 | 拠点 ID（F01＝熊谷工場） | F01 |
| `manufacturer` | 文字列 | メーカー（架空） | ファブリカム工機 |
| `model` | 文字列 | 型式 | FR-120 |
| `install_date` | 日付 | 設置日 | 2018-04-10 |
| `rated_power_kw` | 小数 | 定格出力（kW） | 15.0 |
| `fuel` | 文字列 | 動力・燃料 | 都市ガス |
| `criticality` | 文字列 | 重要度（A/B） | A |
| `pm_interval_days` | 整数 | 予防保全の周期（日） | 90 |

### センサー定義（`sensor_definitions`）

設備種別ごとに sensor_readings の各列が何を測っているか・正常範囲・警報条件。

- ファイル: `02_manufacturing_iot/sensor_definitions.csv`
- 行数: 28
- 主キー: `equipment_type + column_name`

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `equipment_type` | 文字列 | 設備種別 | 焙煎機 |
| `column_name` | 文字列 | sensor_readings の列名 | temperature_c |
| `measurement` | 文字列 | 測定項目 | 排気温度 |
| `unit` | 文字列 | 単位 | ℃ |
| `normal_min` | 小数 | 正常範囲の下限 | 165.0 |
| `normal_max` | 小数 | 正常範囲の上限 | 235.0 |
| `alarm_rule` | 文字列 | 警報条件 | 245 以上 |
| `note` | 文字列 | 備考 |  |

### センサー値（1 分ごと）（`sensor_readings`）

8 設備 × 1 分間隔（2026-05-01〜2026-10-31）。月ごとに分割。通信断による欠損、センサー故障による固定値・異常値、再送による重複行を含む（実データと同様）。

- ファイル: `02_manufacturing_iot/sensor_readings/（6 ファイル）`
- 行数: 2,118,080
- 主キー: `（なし）timestamp + equipment_id が実質キー（重複あり）`
- 外部キー: equipment_id → equipment

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `timestamp` | 日時 | 計測時刻（JST、分単位） | 2026-05-01 00:00:00 |
| `equipment_id` | 文字列 | 設備 ID | CHL-01 |
| `status` | 文字列 | 運転状態（RUN 稼働 / IDLE 待機・チョコ停 / STOP 停止 / FAULT 故障停止 / MAINT 保全） | STOP |
| `temperature_c` | 小数 | 温度（設備種別により意味が異なる → sensor_definitions） | 15.0 |
| `vibration_mm_s` | 小数 | 振動（速度 RMS、mm/s） | 0.05 |
| `current_a` | 小数 | 電流（A） | 0.0 |
| `pressure_kpa` | 小数 | 圧力（kPa、設備によっては空） | 971.0 |
| `speed_rpm` | 小数 | 回転数・速度（設備によっては空） | 0.0 |

### 故障・保全履歴（`failure_history`）

保全管理システム（CMMS）の作業記録。2025-01〜2026-10。故障・予防保全。

- ファイル: `02_manufacturing_iot/failure_history.csv`
- 行数: 83
- 主キー: `work_order_id`
- 外部キー: equipment_id → equipment, technician_employee_id → 04 employees

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `work_order_id` | 文字列 | 作業指示番号 | WO-2025-0001 |
| `equipment_id` | 文字列 | 設備 ID | CHL-01 |
| `event_type` | 文字列 | 故障 / 予防保全 | 予防保全 |
| `occurred_at` | 日時 | 発生（停止）日時 | 2025-01-11 09:00:00 |
| `recovered_at` | 日時 | 復旧日時 | 2025-01-11 11:51:00 |
| `downtime_minutes` | 整数 | 停止時間（分） | 171 |
| `detected_by` | 文字列 | 検知方法 | 定期点検 |
| `failure_mode` | 文字列 | 故障モード | 定期整備 |
| `symptom` | 文字列 | 症状（自由記述） | 計画停止による定期整備。 |
| `root_cause` | 文字列 | 原因（自由記述） | - |
| `action_taken` | 文字列 | 処置（自由記述） | 点検・清掃・消耗品交換を実施。 |
| `parts_replaced` | 文字列 | 交換部品 | 消耗品一式 |
| `repair_cost_jpy` | 整数 | 修理費（円） | 54000 |
| `production_impact` | 文字列 | 生産への影響（自由記述） | ドリップバッグ包装（PKG-02）が約 25 時間停止。ドリップバッグ商品の出荷… |
| `technician_employee_id` | 文字列 | 担当した保全担当者の従業員 ID | E10374 |

### 製造ロット（`production_lots`）

工場で製造したコーヒー豆・ドリップバッグ・焼き菓子のロット。2024-01〜2026-10。

- ファイル: `02_manufacturing_iot/production_lots.csv`
- 行数: 13,077
- 主キー: `lot_id`
- 外部キー: product_id → 01 products, equipment_id → equipment, qc_inspector_employee_id → 04 employees

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `lot_id` | 文字列 | ロット番号（L + 製造日 YYMMDD - ライン - 連番）。商品の袋に印字され、問い合わせ本文に登場する | L240105-R2-01 |
| `product_id` | 文字列 | 商品 ID | P001 |
| `production_date` | 日付 | 製造日 | 2024-01-05 |
| `equipment_id` | 文字列 | 製造した設備（焙煎機など） | RST-02 |
| `shift` | 文字列 | 早番 / 遅番 | 早番 |
| `produced_qty` | 整数 | 製造数 | 195 |
| `defect_qty` | 整数 | 不良数 | 0 |
| `qc_result` | 文字列 | 品質検査の判定 | 合格 |
| `roast_color_agtron` | 小数 | 焙煎度の測定値（Agtron 値。小さいほど深煎り。未測定は空） | 53.6 |
| `roast_spec_min` | 整数 | 焙煎度の規格下限 | 51.0 |
| `roast_spec_max` | 整数 | 焙煎度の規格上限 | 59.0 |
| `moisture_pct` | 小数 | 水分値（%） | 1.98 |
| `best_before_date` | 日付 | 賞味期限 | 2025-01-04 |
| `hold_status` | 文字列 | 出荷可 / 廃棄 / 回収・交換対象 | 出荷可 |
| `qc_inspector_employee_id` | 文字列 | 検査担当者の従業員 ID | E10379 |

## 03_sales_marketing　営業・マーケティング

法人向けオフィスコーヒー事業のキャンペーン → 広告費 → リード → 商談 → 受注。2024-11〜2026-10。

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

## 04_hr_attendance　人事・勤怠

部署・従業員・日次勤怠・残業申請・研修受講・退職者。2024-11〜2026-10。

### 部署（`departments`）

本社部門・法人営業・店舗・工場・物流センターの部署。

- ファイル: `04_hr_attendance/departments.csv`
- 行数: 38
- 主キー: `department_id`
- 外部キー: site_id → 05 sites

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `department_id` | 文字列 | 部署 ID | D100 |
| `department_name` | 文字列 | 部署名 | 経営企画部 |
| `division` | 文字列 | 本部 | 本社部門 |
| `site_id` | 文字列 | 勤務地の拠点 ID | H01 |
| `parent_department_id` | 文字列 | 上位部署 ID | D200 |
| `established_date` | 日付 | 設置日（新店など） | 2016-04-01 |
| `abolished_date` | 日付 | 廃止日（閉店した店舗） | 2025-12-28 |

### 従業員（`employees`）

2024-11 以降に在籍した従業員（退職者を含む）。氏名は架空。

- ファイル: `04_hr_attendance/employees.csv`
- 行数: 628
- 主キー: `employee_id`
- 外部キー: department_id → departments, manager_employee_id → employees

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `employee_id` | 文字列 | 従業員 ID | E10001 |
| `last_name` | 文字列 | 姓（架空） | 松尾 |
| `first_name` | 文字列 | 名（架空） | 明美 |
| `gender` | 文字列 | 性別 | 女性 |
| `birth_date` | 日付 | 生年月日 | 1973-05-05 |
| `hire_date` | 日付 | 入社日 | 2024-09-19 |
| `hire_type` | 文字列 | 新卒 / 中途 / パート採用 | 新卒 |
| `employment_type` | 文字列 | 正社員 / 契約社員 / パート・アルバイト | 正社員 |
| `department_id` | 文字列 | 所属部署 ID（現在または退職時） | D100 |
| `site_id` | 文字列 | 勤務地の拠点 ID | H01 |
| `job_title` | 文字列 | 役職 | 部長 |
| `grade` | 文字列 | 等級（G1〜G7、パートは P） | G6 |
| `base_salary_monthly` | 整数 | 月額基本給（円、正社員・契約社員） | 500000.0 |
| `hourly_wage` | 整数 | 時給（円、パート・アルバイト） | 1310.0 |
| `manager_employee_id` | 文字列 | 上長の従業員 ID | E10001 |
| `status` | 文字列 | 在籍 / 退職 | 在籍 |
| `termination_date` | 日付 | 退職日 | 2026-06-15 |
| `commute_minutes` | 整数 | 通勤時間（分） | 20 |

### 勤怠（日次）（`attendance`）

出勤日・休暇取得日の 1 人 1 日 1 行。打刻漏れを含む。

- ファイル: `04_hr_attendance/attendance.csv`
- 行数: 194,821
- 主キー: `attendance_id`
- 外部キー: employee_id → employees, site_id → 05 sites

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `attendance_id` | 文字列 | 勤怠 ID | AT0000001 |
| `employee_id` | 文字列 | 従業員 ID | E10001 |
| `work_date` | 日付 | 勤務日 | 2024-11-01 |
| `site_id` | 文字列 | 勤務した拠点 | H01 |
| `work_style` | 文字列 | 出社 / テレワーク | 出社 |
| `shift_type` | 文字列 | 日勤 / 早番 / 中番 / 遅番 / 休日出勤 | 日勤 |
| `scheduled_start` | 文字列 | 所定の始業時刻 | 09:00 |
| `scheduled_end` | 文字列 | 所定の終業時刻 | 18:00 |
| `clock_in` | 日時 | 出勤打刻 | 2024-11-01 08:55:55 |
| `clock_out` | 日時 | 退勤打刻（打刻漏れは空） | 2024-11-01 18:02:51 |
| `break_minutes` | 整数 | 休憩（分） | 60 |
| `work_minutes` | 整数 | 実労働時間（分） | 487.0 |
| `overtime_minutes` | 整数 | 所定外労働（分） | 0.0 |
| `late_night_minutes` | 整数 | 深夜労働（22〜5 時、分） | 0.0 |
| `holiday_work` | 真偽 | 休日出勤か | False |
| `leave_type` | 文字列 | 休暇の種類（年次有給休暇 / 特別休暇 / 欠勤） | 年次有給休暇 |
| `note` | 文字列 | 備考 | 打刻漏れ（修正申請中） |

### 残業申請（`overtime_requests`）

正社員・契約社員の残業申請（申請理由は自由記述つき）。申請のない残業もある。

- ファイル: `04_hr_attendance/overtime_requests.csv`
- 行数: 49,852
- 主キー: `request_id`
- 外部キー: employee_id → employees, approver_employee_id → employees

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `request_id` | 文字列 | 申請 ID | OT000001 |
| `employee_id` | 文字列 | 従業員 ID | E10003 |
| `work_date` | 日付 | 対象日 | 2024-11-01 |
| `requested_minutes` | 整数 | 申請時間（分） | 90 |
| `approved_minutes` | 整数 | 承認時間（分） | 90.0 |
| `reason_category` | 文字列 | 理由区分 | 資料作成 |
| `reason_text` | 文字列 | 理由（自由記述） | 締切対応のため |
| `approver_employee_id` | 文字列 | 承認者の従業員 ID | E10001 |
| `status` | 文字列 | 承認 / 差戻し / 申請中 | 承認 |
| `requested_at` | 日時 | 申請日時 | 2024-11-01 16:32:00 |

### 研修コース（`training_courses`）

必須研修（コンプライアンス・衛生）と職種別・階層別の研修。

- ファイル: `04_hr_attendance/training_courses.csv`
- 行数: 16
- 主キー: `course_id`

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `course_id` | 文字列 | コース ID | C01 |
| `course_name` | 文字列 | コース名 | 新入社員研修 |
| `course_category` | 文字列 | 区分 | 導入研修 |
| `delivery_method` | 文字列 | 集合 / eラーニング | 集合 |
| `hours` | 整数 | 時間 | 16 |
| `mandatory` | 真偽 | 必須研修か | False |

### 研修受講（`training_records`）

研修の受講・修了記録。

- ファイル: `04_hr_attendance/training_records.csv`
- 行数: 3,986
- 主キー: `training_record_id`
- 外部キー: employee_id → employees, course_id → training_courses

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `training_record_id` | 文字列 | 受講記録 ID | TR000001 |
| `employee_id` | 文字列 | 従業員 ID | E10162 |
| `course_id` | 文字列 | コース ID | C07 |
| `enrolled_date` | 日付 | 受講（申込）日 | 2024-09-01 |
| `completed_date` | 日付 | 修了日 | 2024-09-01 |
| `status` | 文字列 | 修了 / 未修了 / 欠席 / 受講中 | 修了 |
| `score` | 整数 | テストの点数（eラーニング） | 83.0 |
| `satisfaction` | 整数 | 満足度（1〜5） | 2.0 |

### 退職者（`resignations`）

2024-11〜2026-10 の退職者。退職面談のコメント（自由記述）つき。

- ファイル: `04_hr_attendance/resignations.csv`
- 行数: 201
- 主キー: `resignation_id`
- 外部キー: employee_id → employees

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `resignation_id` | 文字列 | 退職 ID | RS0001 |
| `employee_id` | 文字列 | 従業員 ID | E10050 |
| `notice_date` | 日付 | 退職の申し出日 | 2024-10-02 |
| `last_working_date` | 日付 | 最終出社日（退職日） | 2024-11-06 |
| `resignation_type` | 文字列 | 自己都合 / 会社都合 / 定年 / 契約満了 | 自己都合 |
| `reason_category` | 文字列 | 退職理由の区分 | キャリアアップ |
| `exit_interview_comment` | 文字列 | 退職面談のコメント（自由記述） | 最初の数か月で教わる機会がほとんどなく、不安が大きかった。 |
| `rehire_eligible` | 真偽 | 再雇用の可否 | True |

## 05_facility_energy　施設・エネルギー

全 22 拠点の 30 分ごとの電力・ガス使用量（BEMS の外気温つき）と空調の設定ログ。2024-11〜2026-10。

### 拠点（`sites`）

店舗 16・工場・物流センター・本社・支店 3 の 22 拠点。最寄りの気象庁観測所つき。

- ファイル: `05_facility_energy/sites.csv`
- 行数: 22
- 主キー: `site_id`

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `site_id` | 文字列 | 拠点 ID（店舗は 01 の store_id と共通） | S01 |
| `site_name` | 文字列 | 拠点名 | 札幌大通店 |
| `site_type` | 文字列 | 店舗 / 工場 / 物流センター / 本社 / 支店 | 店舗 |
| `prefecture` | 文字列 | 都道府県 | 北海道 |
| `city` | 文字列 | 市区町村 | 札幌市中央区 |
| `latitude` | 小数 | 緯度（概略） | 43.0606 |
| `longitude` | 小数 | 経度（概略） | 141.3544 |
| `floor_area_m2` | 整数 | 延床面積（㎡） | 120 |
| `building_type` | 文字列 | 建物の種類 | 商業ビル テナント |
| `electricity_contract` | 文字列 | 電力契約（高圧 / 低圧） | 低圧 |
| `contract_kw` | 整数 | 契約電力（kW） | 50 |
| `gas_supply` | 文字列 | ガス供給（都市ガス / なし） | 都市ガス |
| `open_date` | 日付 | 開設日 | 2016-04-01 |
| `close_date` | 日付 | 閉鎖日 | 2025-12-28 |
| `hvac_zones` | 文字列 | 空調ゾーン | 客席 |
| `jma_station_name` | 文字列 | 最寄りの気象庁観測所名 | 札幌 |
| `jma_prec_no` | 整数 | 気象庁の府県番号（prec_no） | 14 |
| `jma_block_no` | 整数 | 気象庁の地点番号（block_no） | 47412 |

### 電力・ガス使用量（30 分ごと）（`energy_usage_30min`）

拠点ごとの 30 分値（2024-11-01〜2026-10-31）。年ごとに分割。通信断による欠損、メーター交換時の 0 値、外気温センサーの故障・日射の影響を含む。

- ファイル: `05_facility_energy/energy_usage_30min/（3 ファイル）`
- 行数: 730,272
- 主キー: `site_id + timestamp`
- 外部キー: site_id → sites

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `site_id` | 文字列 | 拠点 ID | B01 |
| `timestamp` | 日時 | 30 分コマの開始時刻（JST） | 2024-11-01 00:00:00 |
| `electricity_kwh` | 小数 | 電力使用量（kWh / 30 分） | 0.46 |
| `gas_m3` | 小数 | ガス使用量（m³ / 30 分。ガス契約のない拠点は空） | 1.199 |
| `outdoor_temp_c` | 小数 | BEMS の外気温センサー値（℃） | 19.4 |

### 空調の設定ログ（`hvac_settings_log`）

BEMS が記録した空調の運転開始・停止、モード・設定温度の変更。

- ファイル: `05_facility_energy/hvac_settings_log.csv`
- 行数: 30,810
- 主キー: `log_id`
- 外部キー: site_id → sites

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `log_id` | 文字列 | ログ ID | HV000001 |
| `site_id` | 文字列 | 拠点 ID | F01 |
| `zone` | 文字列 | 空調ゾーン | 包装室 |
| `event_time` | 日時 | 日時 | 2024-11-01 05:59:00 |
| `event_type` | 文字列 | 運転開始 / 運転停止 / 設定変更 / モード変更 | モード変更 |
| `mode` | 文字列 | 冷房 / 暖房 / 送風 / 停止 | 送風 |
| `setpoint_c` | 小数 | 設定温度（℃） | 21.0 |
| `fan_speed` | 文字列 | 風量 | 自動 |
| `changed_by` | 文字列 | 変更者（スケジュール / 手動 / BEMS 自動制御） | BEMS 自動制御 |
| `note` | 文字列 | 備考 | 季節切替 |

## 06_customer_support　カスタマーサポート（非構造・半構造）

問い合わせ本文（日本語の自由記述）と受付日時・チャネル・関連商品・対応状況。2024-01〜2026-10。

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

## 07_excel_reports　Excel 帳票（非構造）

8 店舗から提出された書式バラバラの日報（2026-10）と発注書（2026-09〜10）。

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

## 08_app_logs　アプリ操作ログ（半構造・JSON）

公式アプリのイベントログ（JSON Lines、1 日 1 ファイル）。2026-09〜10。

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
