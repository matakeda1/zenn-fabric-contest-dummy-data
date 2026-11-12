# 01_retail_ec　小売・EC

直営店の POS とオンラインストア（Web・アプリ・定期便）の受注データ。2024-01〜2026-10。

全体の説明はリポジトリ直下の README.md、全列の定義は docs/data_dictionary.md を参照してください。

## ファイル

| ファイル | 行数 | サイズ |
|---|---:|---:|
| `01_retail_ec/customers.csv` | 32,459 | 3.0 MB |
| `01_retail_ec/order_lines/`（3 ファイル） | 788,448 | 53.0 MB |
| `01_retail_ec/orders/`（3 ファイル） | 494,189 | 64.3 MB |
| `01_retail_ec/product_price_history.csv` | 160 | 0.0 MB |
| `01_retail_ec/products.csv` | 77 | 0.0 MB |
| `01_retail_ec/promotions.csv` | 20 | 0.0 MB |
| `01_retail_ec/store_closures.csv` | 141 | 0.0 MB |
| `01_retail_ec/stores.csv` | 17 | 0.0 MB |
| `01_retail_ec/subscriptions.csv` | 3,210 | 0.2 MB |

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

