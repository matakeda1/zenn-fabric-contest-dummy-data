# 02_manufacturing_iot　製造・IoT

熊谷工場の設備マスタ、1 分ごとのセンサー値（2026-05〜10）、故障・保全履歴（2025-01〜）、製造ロット。

全体の説明はリポジトリ直下の README.md、全列の定義は docs/data_dictionary.md を参照してください。

## ファイル

| ファイル | 行数 | サイズ |
|---|---:|---:|
| `02_manufacturing_iot/equipment.csv` | 8 | 0.0 MB |
| `02_manufacturing_iot/failure_history.csv` | 83 | 0.0 MB |
| `02_manufacturing_iot/production_lots.csv` | 13,077 | 1.2 MB |
| `02_manufacturing_iot/sensor_definitions.csv` | 28 | 0.0 MB |
| `02_manufacturing_iot/sensor_readings/sensor_readings_2026-05.csv` | 357,148 | 19.5 MB |
| `02_manufacturing_iot/sensor_readings/sensor_readings_2026-06.csv` | 344,430 | 18.9 MB |
| `02_manufacturing_iot/sensor_readings/sensor_readings_2026-07.csv` | 357,145 | 19.6 MB |
| `02_manufacturing_iot/sensor_readings/sensor_readings_2026-08.csv` | 356,790 | 19.5 MB |
| `02_manufacturing_iot/sensor_readings/sensor_readings_2026-09.csv` | 345,621 | 18.9 MB |
| `02_manufacturing_iot/sensor_readings/sensor_readings_2026-10.csv` | 356,946 | 19.6 MB |

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

