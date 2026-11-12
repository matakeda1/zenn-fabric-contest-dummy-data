# 05_facility_energy　施設・エネルギー

全 22 拠点の 30 分ごとの電力・ガス使用量（BEMS の外気温つき）と空調の設定ログ。2024-11〜2026-10。

全体の説明はリポジトリ直下の README.md、全列の定義は docs/data_dictionary.md を参照してください。

## ファイル

| ファイル | 行数 | サイズ |
|---|---:|---:|
| `05_facility_energy/energy_usage_30min/energy_usage_30min_2024.csv` | 58,560 | 2.1 MB |
| `05_facility_energy/energy_usage_30min/energy_usage_30min_2025.csv` | 365,280 | 13.3 MB |
| `05_facility_energy/energy_usage_30min/energy_usage_30min_2026.csv` | 306,432 | 11.1 MB |
| `05_facility_energy/hvac_settings_log.csv` | 30,810 | 2.7 MB |
| `05_facility_energy/sites.csv` | 22 | 0.0 MB |

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

