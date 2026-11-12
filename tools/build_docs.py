"""Build docs/data_dictionary.md and data/<dataset>/README.md from the generated data + column descriptions.

Fails if a CSV column has no description (keeps docs in sync with the generator).
    python tools/build_docs.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

DATASETS = {
    "00_common": ("共通マスタ", "全データセットで共通に使えるカレンダー（祝日・会計年度つき）。"),
    "01_retail_ec": ("小売・EC", "直営店の POS とオンラインストア（Web・アプリ・定期便）の受注データ。2024-01〜2026-10。"),
    "02_manufacturing_iot": ("製造・IoT", "熊谷工場の設備マスタ、1 分ごとのセンサー値（2026-05〜10）、故障・保全履歴（2025-01〜）、製造ロット。"),
    "03_sales_marketing": ("営業・マーケティング", "法人向けオフィスコーヒー事業のキャンペーン → 広告費 → リード → 商談 → 受注。2024-11〜2026-10。"),
    "04_hr_attendance": ("人事・勤怠", "部署・従業員・日次勤怠・残業申請・研修受講・退職者。2024-11〜2026-10。"),
    "05_facility_energy": ("施設・エネルギー", "全 22 拠点の 30 分ごとの電力・ガス使用量（BEMS の外気温つき）と空調の設定ログ。2024-11〜2026-10。"),
    "06_customer_support": ("カスタマーサポート（非構造・半構造）", "問い合わせ本文（日本語の自由記述）と受付日時・チャネル・関連商品・対応状況。2024-01〜2026-10。"),
    "07_excel_reports": ("Excel 帳票（非構造）", "8 店舗から提出された書式バラバラの日報（2026-10）と発注書（2026-09〜10）。"),
    "08_app_logs": ("アプリ操作ログ（半構造・JSON）", "公式アプリのイベントログ（JSON Lines、1 日 1 ファイル）。2026-09〜10。"),
}

T = {}


def t(folder, name, title, desc, pk, fk, cols):
    T[(folder, name)] = dict(title=title, desc=desc, pk=pk, fk=fk, cols=cols)


t("00_common", "calendar", "カレンダー", "日付ディメンション。祝日・会社の会計年度（4 月始まり）つき。2026-12-31 まで。", "date", "", {
    "date": "日付", "year": "年", "month": "月", "day": "日", "year_month": "年月（YYYY-MM）", "weekday_num": "曜日番号（月=1〜日=7）",
    "weekday_ja": "曜日（日本語）", "is_weekend": "土日フラグ", "is_holiday": "祝日・振替休日フラグ", "holiday_name": "祝日名",
    "is_business_day": "本社の営業日フラグ（土日祝・年末年始 12/30〜1/3 を除く）", "fiscal_year": "会計年度（4 月始まり。例：2025-04〜2026-03 は 2025）",
    "fiscal_quarter": "会計四半期（例：FY2025Q1）", "week_start_date": "週の開始日（月曜）", "season": "季節（春夏秋冬）"})

t("01_retail_ec", "stores", "店舗", "直営 16 店舗（閉店 1・新規出店 2 を含む）とオンラインストア（W01）。最寄りの気象庁観測所つき。", "store_id", "", {
    "store_id": "店舗 ID（S01〜S16、オンラインは W01）。05 の site_id と共通", "store_name": "店舗名", "store_type": "直営店 / EC",
    "area_type": "立地（オフィス街・駅前・繁華街・商業地・商業施設・住宅地・観光地）", "prefecture": "都道府県", "city": "市区町村",
    "latitude": "緯度（概略）", "longitude": "経度（概略）", "open_date": "開店日", "close_date": "閉店日（営業中は空）",
    "open_time": "開店時刻", "close_time": "閉店時刻", "seat_count": "客席数", "floor_area_m2": "床面積（㎡）",
    "jma_station_name": "最寄りの気象庁観測所名（気象データ結合用）", "jma_prec_no": "気象庁「過去の気象データ検索」の府県番号（prec_no）",
    "jma_block_no": "気象庁「過去の気象データ検索」の地点番号（block_no）"})
t("01_retail_ec", "products", "商品", "コーヒー豆・ドリップバッグ・店内ドリンク・焼き菓子・ボトル飲料・ギフト・器具・定期便の 77 商品。", "product_id", "", {
    "product_id": "商品 ID", "product_name": "商品名", "category": "カテゴリ", "subcategory": "サブカテゴリ", "size": "規格・容量",
    "sales_channel": "販売チャネル（店舗のみ / オンラインのみ / 店舗・オンライン / 定期便）", "serving_temp": "ドリンクの提供温度（ホット / アイス / 両方）",
    "launch_price": "発売時（または 2024-01 時点）の税抜単価（円）", "current_price": "2026-10 時点の税抜単価（円）", "unit_cost": "原価（円、概算）",
    "tax_category": "消費税区分（軽減税率対象 / 標準税率）", "launch_date": "発売日", "end_date": "販売終了日", "sales_season": "販売時期（MM-DD〜MM-DD、季節限定のみ）",
    "lot_managed": "自社工場で製造しロット管理している商品か（02 の production_lots と結合可）"})
t("01_retail_ec", "product_price_history", "商品価格履歴", "税抜単価の改定履歴（2025-04-01・2026-04-01 に価格改定）。", "price_id", "product_id → products", {
    "price_id": "価格履歴 ID", "product_id": "商品 ID", "valid_from": "適用開始日", "valid_to": "適用終了日（この日の前日まで有効。現行価格は空）",
    "unit_price": "税抜単価（円）"})
t("01_retail_ec", "promotions", "販促", "セール・キャンペーン・クーポンの一覧。", "promotion_id", "", {
    "promotion_id": "販促 ID", "promotion_code": "販促コード（orders.promotion_code と結合）", "promotion_name": "販促名", "channel": "対象チャネル",
    "start_date": "開始日", "end_date": "終了日", "target_category": "対象カテゴリ（カンマ区切り）", "discount_type": "割引種別（割引率 / 値引額 / フェア）",
    "discount_value": "割引値（% または円）", "coupon_code": "お客様が入力・提示するクーポンコード", "note": "備考"})
t("01_retail_ec", "customers", "顧客（会員）", "会員 約 3.2 万人。氏名・連絡先は含まない（匿名化済み）。", "customer_id", "home_store_id → stores", {
    "customer_id": "顧客 ID", "registered_date": "会員登録日", "registration_channel": "登録経路（店舗 / オンラインストア / アプリ）",
    "gender": "性別（女性 / 男性 / その他・無回答）", "birth_year": "生まれ年", "prefecture": "居住都道府県",
    "home_store_id": "よく利用する店舗（店舗登録の会員など）", "app_user": "公式アプリ利用者か", "mail_opt_in": "メール配信の許諾",
    "member_rank": "会員ランク（直近 12 か月の購入額で判定）", "status": "有効 / 退会", "withdrawn_date": "退会日"})
t("01_retail_ec", "subscriptions", "定期便契約", "2024-06 開始の定期便（毎月お届け）の契約。解約理由つき。", "subscription_id",
  "customer_id → customers, product_id → products", {
      "subscription_id": "定期便契約 ID", "customer_id": "顧客 ID", "product_id": "定期便商品 ID", "start_date": "開始日",
      "billing_day": "毎月のお届け（決済）日", "status": "継続中 / 解約", "cancel_date": "解約日", "cancel_reason": "解約理由（選択式）",
      "skip_count": "スキップした回数"})
t("01_retail_ec", "store_closures", "店舗の休業・短縮営業", "年始休業・改装休業、大雨・大雪による臨時休業や短縮営業の記録。", "closure_id", "store_id → stores", {
    "closure_id": "休業記録 ID", "store_id": "店舗 ID", "date": "日付", "closure_type": "年始休業 / 改装休業 / 臨時休業 / 短縮営業", "reason": "理由"})
t("01_retail_ec", "orders", "受注（ヘッダ）", "店舗の会計（レシート）・オンライン注文・定期便の 1 件 = 1 行。年ごとに分割（orders/ フォルダ）。",
  "order_id", "store_id → stores, customer_id → customers, promotion_code → promotions", {
      "order_id": "受注 ID（店舗：S03-240105-0042、オンライン：EC240105-00012、定期便：SB240105-00003）",
      "order_datetime": "受注日時（店舗は会計時刻）", "channel": "店舗 / オンラインストア / 定期便", "store_id": "店舗 ID（オンライン・定期便は W01）",
      "customer_id": "顧客 ID（店舗で会員カード・アプリ提示なしの場合は空）", "device": "店頭 / Web / アプリ / 定期便",
      "eat_in": "店内 / 持ち帰り（店舗のみ。店内飲食の飲食料品は 10%）", "payment_method": "支払方法", "item_count": "点数（数量の合計）",
      "subtotal_excl_tax": "税抜小計（値引後）", "discount_total": "値引額の合計", "tax_total": "消費税額", "shipping_fee": "送料（税込。店舗は 0）",
      "total_incl_tax": "税込合計（小計 + 消費税 + 送料）", "coupon_code": "利用されたクーポンコード", "promotion_code": "適用された販促コード",
      "order_status": "完了 / キャンセル / 返品 / 出荷済み / 受付済み", "shipping_prefecture": "お届け先都道府県（オンライン・定期便）",
      "shipped_date": "出荷日", "promised_delivery_date": "お届け予定日（注文時点）", "delivered_date": "お届け日（実績）", "returned_date": "返品受付日"})
t("01_retail_ec", "order_lines", "受注明細", "受注 1 件に含まれる商品ごとの明細。年ごとに分割（order_lines/ フォルダ）。", "order_line_id",
  "order_id → orders, product_id → products", {
      "order_line_id": "受注明細 ID（order_id + 行番号）", "order_id": "受注 ID", "line_no": "行番号", "product_id": "商品 ID", "quantity": "数量",
      "unit_price": "税抜単価（円、販売時点の価格）", "discount_amount": "値引額（円）", "line_subtotal": "税抜金額（単価×数量−値引）",
      "tax_rate": "消費税率（0.08 / 0.10）", "tax_amount": "消費税額（明細ごとに切り捨て）", "line_total": "税込金額"})

t("02_manufacturing_iot", "equipment", "設備", "熊谷工場の主要設備 8 台。", "equipment_id", "site_id → 05 sites", {
    "equipment_id": "設備 ID", "equipment_name": "設備名", "equipment_type": "設備種別（sensor_definitions と結合）", "line": "ライン", "site_id": "拠点 ID（F01＝熊谷工場）",
    "manufacturer": "メーカー（架空）", "model": "型式", "install_date": "設置日", "rated_power_kw": "定格出力（kW）", "fuel": "動力・燃料",
    "criticality": "重要度（A/B）", "pm_interval_days": "予防保全の周期（日）"})
t("02_manufacturing_iot", "sensor_definitions", "センサー定義", "設備種別ごとに sensor_readings の各列が何を測っているか・正常範囲・警報条件。",
  "equipment_type + column_name", "", {
      "equipment_type": "設備種別", "column_name": "sensor_readings の列名", "measurement": "測定項目", "unit": "単位", "normal_min": "正常範囲の下限",
      "normal_max": "正常範囲の上限", "alarm_rule": "警報条件", "note": "備考"})
t("02_manufacturing_iot", "sensor_readings", "センサー値（1 分ごと）", "8 設備 × 1 分間隔（2026-05-01〜2026-10-31）。月ごとに分割。"
  "通信断による欠損、センサー故障による固定値・異常値、再送による重複行を含む（実データと同様）。", "（なし）timestamp + equipment_id が実質キー（重複あり）",
  "equipment_id → equipment", {
      "timestamp": "計測時刻（JST、分単位）", "equipment_id": "設備 ID", "status": "運転状態（RUN 稼働 / IDLE 待機・チョコ停 / STOP 停止 / FAULT 故障停止 / MAINT 保全）",
      "temperature_c": "温度（設備種別により意味が異なる → sensor_definitions）", "vibration_mm_s": "振動（速度 RMS、mm/s）", "current_a": "電流（A）",
      "pressure_kpa": "圧力（kPa、設備によっては空）", "speed_rpm": "回転数・速度（設備によっては空）"})
t("02_manufacturing_iot", "failure_history", "故障・保全履歴", "保全管理システム（CMMS）の作業記録。2025-01〜2026-10。故障・予防保全。", "work_order_id",
  "equipment_id → equipment, technician_employee_id → 04 employees", {
      "work_order_id": "作業指示番号", "equipment_id": "設備 ID", "event_type": "故障 / 予防保全", "occurred_at": "発生（停止）日時",
      "recovered_at": "復旧日時", "downtime_minutes": "停止時間（分）", "detected_by": "検知方法", "failure_mode": "故障モード",
      "symptom": "症状（自由記述）", "root_cause": "原因（自由記述）", "action_taken": "処置（自由記述）", "parts_replaced": "交換部品",
      "repair_cost_jpy": "修理費（円）", "production_impact": "生産への影響（自由記述）", "technician_employee_id": "担当した保全担当者の従業員 ID"})
t("02_manufacturing_iot", "production_lots", "製造ロット", "工場で製造したコーヒー豆・ドリップバッグ・焼き菓子のロット。2024-01〜2026-10。", "lot_id",
  "product_id → 01 products, equipment_id → equipment, qc_inspector_employee_id → 04 employees", {
      "lot_id": "ロット番号（L + 製造日 YYMMDD - ライン - 連番）。商品の袋に印字され、問い合わせ本文に登場する", "product_id": "商品 ID", "production_date": "製造日",
      "equipment_id": "製造した設備（焙煎機など）", "shift": "早番 / 遅番", "produced_qty": "製造数", "defect_qty": "不良数",
      "qc_result": "品質検査の判定", "roast_color_agtron": "焙煎度の測定値（Agtron 値。小さいほど深煎り。未測定は空）",
      "roast_spec_min": "焙煎度の規格下限", "roast_spec_max": "焙煎度の規格上限", "moisture_pct": "水分値（%）", "best_before_date": "賞味期限",
      "hold_status": "出荷可 / 廃棄 / 回収・交換対象", "qc_inspector_employee_id": "検査担当者の従業員 ID"})

t("03_sales_marketing", "campaigns", "キャンペーン", "検索広告・SNS 広告・展示会・ウェビナー・ホワイトペーパー・テレアポ・紹介。", "campaign_id",
  "owner_employee_id → 04 employees", {
      "campaign_id": "キャンペーン ID", "campaign_name": "キャンペーン名", "channel": "チャネル", "media": "媒体", "start_date": "開始日", "end_date": "終了日",
      "budget_jpy": "予算（円）", "target_industry": "ターゲット業種", "target_company_size": "ターゲット企業規模", "objective": "目的",
      "utm_campaign": "計測用 UTM パラメータ", "owner_employee_id": "担当者（マーケティング部）の従業員 ID"})
t("03_sales_marketing", "ad_spend_daily", "広告費（日次）", "デジタル広告は日次の表示回数・クリック・費用・媒体上のコンバージョン。展示会などは実施日に費用を計上。",
  "spend_id", "campaign_id → campaigns", {
      "spend_id": "広告費 ID", "date": "日付", "campaign_id": "キャンペーン ID", "media": "媒体", "impressions": "表示回数", "clicks": "クリック数",
      "cost_jpy": "費用（円）", "platform_conversions": "広告媒体が計測したコンバージョン数（CRM のリード数とは一致しない）"})
t("03_sales_marketing", "leads", "リード", "問い合わせ・資料請求・名刺交換などで獲得した見込み客。会社名は表記ゆれあり（名寄せが必要）。個人名は含まない。",
  "lead_id", "campaign_id → campaigns, owner_employee_id → 04 employees, source_inquiry_id → 06 inquiries", {
      "lead_id": "リード ID", "created_at": "獲得日時", "campaign_id": "キャンペーン ID（計測漏れ・自然検索などは空）", "lead_source": "獲得経路",
      "company_name": "会社名（入力されたまま。表記ゆれあり）", "industry": "業種（未入力あり）", "employee_band": "従業員規模", "prefecture": "所在地（都道府県）",
      "department": "問い合わせ者の部署", "job_level": "問い合わせ者の役職", "inquiry_type": "問い合わせ種別", "owner_employee_id": "担当インサイドセールスの従業員 ID",
      "first_contact_at": "初回接触日時", "status": "リードのステータス", "disqualify_reason": "対象外の理由", "lead_score": "リードスコア（0〜100）",
      "source_inquiry_id": "カスタマーサポート経由の場合の問い合わせ ID"})
t("03_sales_marketing", "opportunities", "商談", "リードから商談化した案件。2026-10-31 時点のスナップショット（進行中の案件を含む）。", "opportunity_id",
  "lead_id → leads, owner_employee_id → 04 employees, branch_department_id → 04 departments", {
      "opportunity_id": "商談 ID", "lead_id": "リード ID", "account_name": "顧客企業名（正式名称）", "industry": "業種", "employee_band": "従業員規模",
      "prefecture": "所在地", "owner_employee_id": "担当営業の従業員 ID", "branch_department_id": "担当部署（営業課・支店）", "created_date": "商談作成日",
      "stage": "現在のステージ（初回訪問→ヒアリング→提案→見積提示→交渉→受注 / 失注）", "probability_pct": "受注確度（%）", "plan": "提案プラン",
      "monthly_fee": "月額（円、税抜）", "contract_months": "契約期間（月）", "initial_fee": "初期費用（円）", "amount": "契約総額（円）",
      "expected_close_date": "受注予定日", "closed_date": "受注・失注日", "is_won": "受注なら true（進行中は空）", "lost_reason": "失注理由",
      "competitor": "競合（架空）"})
t("03_sales_marketing", "opportunity_stage_history", "商談ステージ履歴", "商談がどのステージに何日いたか。", "stage_history_id",
  "opportunity_id → opportunities", {
      "stage_history_id": "ステージ履歴 ID", "opportunity_id": "商談 ID", "stage": "ステージ", "entered_date": "ステージに入った日",
      "exited_date": "ステージを出た日（現在のステージは空）", "days_in_stage": "滞在日数"})
t("03_sales_marketing", "orders", "受注（法人契約）", "受注した法人契約。", "order_id", "opportunity_id → opportunities, owner_employee_id → 04 employees", {
    "order_id": "法人受注 ID", "opportunity_id": "商談 ID", "account_name": "顧客企業名", "order_date": "受注日", "plan": "プラン",
    "contract_start_date": "契約開始日", "contract_months": "契約期間（月）", "monthly_fee": "月額（円、税抜）", "initial_fee": "初期費用（円）",
    "total_contract_value": "契約総額（円）", "owner_employee_id": "担当営業の従業員 ID", "branch_department_id": "担当部署", "payment_terms": "支払条件"})

t("04_hr_attendance", "departments", "部署", "本社部門・法人営業・店舗・工場・物流センターの部署。", "department_id", "site_id → 05 sites", {
    "department_id": "部署 ID", "department_name": "部署名", "division": "本部", "site_id": "勤務地の拠点 ID", "parent_department_id": "上位部署 ID",
    "established_date": "設置日（新店など）", "abolished_date": "廃止日（閉店した店舗）"})
t("04_hr_attendance", "employees", "従業員", "2024-11 以降に在籍した従業員（退職者を含む）。氏名は架空。", "employee_id",
  "department_id → departments, manager_employee_id → employees", {
      "employee_id": "従業員 ID", "last_name": "姓（架空）", "first_name": "名（架空）", "gender": "性別", "birth_date": "生年月日", "hire_date": "入社日",
      "hire_type": "新卒 / 中途 / パート採用", "employment_type": "正社員 / 契約社員 / パート・アルバイト", "department_id": "所属部署 ID（現在または退職時）",
      "site_id": "勤務地の拠点 ID", "job_title": "役職", "grade": "等級（G1〜G7、パートは P）", "base_salary_monthly": "月額基本給（円、正社員・契約社員）",
      "hourly_wage": "時給（円、パート・アルバイト）", "manager_employee_id": "上長の従業員 ID", "status": "在籍 / 退職", "termination_date": "退職日",
      "commute_minutes": "通勤時間（分）"})
t("04_hr_attendance", "attendance", "勤怠（日次）", "出勤日・休暇取得日の 1 人 1 日 1 行。打刻漏れを含む。", "attendance_id",
  "employee_id → employees, site_id → 05 sites", {
      "attendance_id": "勤怠 ID", "employee_id": "従業員 ID", "work_date": "勤務日", "site_id": "勤務した拠点", "work_style": "出社 / テレワーク",
      "shift_type": "日勤 / 早番 / 中番 / 遅番 / 休日出勤", "scheduled_start": "所定の始業時刻", "scheduled_end": "所定の終業時刻",
      "clock_in": "出勤打刻", "clock_out": "退勤打刻（打刻漏れは空）", "break_minutes": "休憩（分）", "work_minutes": "実労働時間（分）",
      "overtime_minutes": "所定外労働（分）", "late_night_minutes": "深夜労働（22〜5 時、分）", "holiday_work": "休日出勤か",
      "leave_type": "休暇の種類（年次有給休暇 / 特別休暇 / 欠勤）", "note": "備考"})
t("04_hr_attendance", "overtime_requests", "残業申請", "正社員・契約社員の残業申請（申請理由は自由記述つき）。申請のない残業もある。", "request_id",
  "employee_id → employees, approver_employee_id → employees", {
      "request_id": "申請 ID", "employee_id": "従業員 ID", "work_date": "対象日", "requested_minutes": "申請時間（分）", "approved_minutes": "承認時間（分）",
      "reason_category": "理由区分", "reason_text": "理由（自由記述）", "approver_employee_id": "承認者の従業員 ID", "status": "承認 / 差戻し / 申請中",
      "requested_at": "申請日時"})
t("04_hr_attendance", "training_courses", "研修コース", "必須研修（コンプライアンス・衛生）と職種別・階層別の研修。", "course_id", "", {
    "course_id": "コース ID", "course_name": "コース名", "course_category": "区分", "delivery_method": "集合 / eラーニング", "hours": "時間", "mandatory": "必須研修か"})
t("04_hr_attendance", "training_records", "研修受講", "研修の受講・修了記録。", "training_record_id", "employee_id → employees, course_id → training_courses", {
    "training_record_id": "受講記録 ID", "employee_id": "従業員 ID", "course_id": "コース ID", "enrolled_date": "受講（申込）日", "completed_date": "修了日",
    "status": "修了 / 未修了 / 欠席 / 受講中", "score": "テストの点数（eラーニング）", "satisfaction": "満足度（1〜5）"})
t("04_hr_attendance", "resignations", "退職者", "2024-11〜2026-10 の退職者。退職面談のコメント（自由記述）つき。", "resignation_id", "employee_id → employees", {
    "resignation_id": "退職 ID", "employee_id": "従業員 ID", "notice_date": "退職の申し出日", "last_working_date": "最終出社日（退職日）",
    "resignation_type": "自己都合 / 会社都合 / 定年 / 契約満了", "reason_category": "退職理由の区分", "exit_interview_comment": "退職面談のコメント（自由記述）",
    "rehire_eligible": "再雇用の可否"})

t("05_facility_energy", "sites", "拠点", "店舗 16・工場・物流センター・本社・支店 3 の 22 拠点。最寄りの気象庁観測所つき。", "site_id", "", {
    "site_id": "拠点 ID（店舗は 01 の store_id と共通）", "site_name": "拠点名", "site_type": "店舗 / 工場 / 物流センター / 本社 / 支店",
    "prefecture": "都道府県", "city": "市区町村", "latitude": "緯度（概略）", "longitude": "経度（概略）", "floor_area_m2": "延床面積（㎡）",
    "building_type": "建物の種類", "electricity_contract": "電力契約（高圧 / 低圧）", "contract_kw": "契約電力（kW）", "gas_supply": "ガス供給（都市ガス / なし）",
    "open_date": "開設日", "close_date": "閉鎖日", "hvac_zones": "空調ゾーン", "jma_station_name": "最寄りの気象庁観測所名",
    "jma_prec_no": "気象庁の府県番号（prec_no）", "jma_block_no": "気象庁の地点番号（block_no）"})
t("05_facility_energy", "energy_usage_30min", "電力・ガス使用量（30 分ごと）", "拠点ごとの 30 分値（2024-11-01〜2026-10-31）。年ごとに分割。"
  "通信断による欠損、メーター交換時の 0 値、外気温センサーの故障・日射の影響を含む。", "site_id + timestamp", "site_id → sites", {
      "site_id": "拠点 ID", "timestamp": "30 分コマの開始時刻（JST）", "electricity_kwh": "電力使用量（kWh / 30 分）",
      "gas_m3": "ガス使用量（m³ / 30 分。ガス契約のない拠点は空）", "outdoor_temp_c": "BEMS の外気温センサー値（℃）"})
t("05_facility_energy", "hvac_settings_log", "空調の設定ログ", "BEMS が記録した空調の運転開始・停止、モード・設定温度の変更。", "log_id", "site_id → sites", {
    "log_id": "ログ ID", "site_id": "拠点 ID", "zone": "空調ゾーン", "event_time": "日時", "event_type": "運転開始 / 運転停止 / 設定変更 / モード変更",
    "mode": "冷房 / 暖房 / 送風 / 停止", "setpoint_c": "設定温度（℃）", "fan_speed": "風量", "changed_by": "変更者（スケジュール / 手動 / BEMS 自動制御）",
    "note": "備考"})

t("06_customer_support", "inquiries", "問い合わせ", "約 9,400 件。本文は日本語の自由記述（メール・Web フォーム・電話メモ・チャット・アプリ・SNS・店頭）。"
  "本文に改行を含むため CSV は複数行のセルあり（同じ内容の JSON Lines 版 inquiries.jsonl も同梱）。", "inquiry_id",
  "customer_id → 01 customers, order_id → 01 orders, product_id → 01 products, store_id → 01 stores, assignee_employee_id → 04 employees, lot_no → 02 production_lots", {
      "inquiry_id": "問い合わせ ID", "received_at": "受付日時", "channel": "チャネル（電話 / メール / Webフォーム / チャット / アプリ内 / SNS / 店頭）",
      "customer_id": "顧客 ID（特定できた場合）", "order_id": "関連する受注 ID", "product_id": "関連する商品 ID", "store_id": "関連する店舗 ID",
      "category": "大分類（担当者が付与。未分類あり）", "subcategory": "小分類（未分類あり）", "subject": "件名", "body": "本文（自由記述）",
      "status": "対応状況", "priority": "優先度", "assigned_team": "担当チーム", "assignee_employee_id": "担当者の従業員 ID",
      "first_response_at": "初回回答日時", "closed_at": "完了日時", "csat_score": "顧客満足度アンケート（1〜5、回答者のみ）",
      "lot_no": "ロット番号（担当者が入力できた場合）"})

t("07_excel_reports", "supply_items", "本部の品目マスタ", "発注書の品名を名寄せするための正式な品目一覧（07_excel_reports/master/）。", "item_code", "", {
    "item_code": "品目コード", "item_name": "正式品名", "spec": "規格", "unit": "単位", "case_quantity": "1 ケースあたりの入数", "unit_price": "単価（円）"})
t("07_excel_reports", "report_stores", "帳票を提出している店舗", "日報・発注書を提出している 8 店舗（01 の store_id と共通）。", "store_id", "store_id → 01 stores", {
    "store_id": "店舗 ID", "store_name": "店舗名"})
t("08_app_logs", "app_releases", "アプリのリリース履歴", "iOS / Android のバージョンとリリース日・内容。", "platform + app_version", "", {
    "platform": "iOS / Android", "app_version": "バージョン", "release_date": "リリース日", "release_note": "リリース内容"})

TYPE_JA = {"int64": "整数", "Int64": "整数", "float64": "小数", "bool": "真偽", "boolean": "真偽", "object": "文字列", "str": "文字列",
           "string": "文字列"}


def infer_type(s: pd.Series, col: str) -> str:
    v = s.dropna()
    if v.empty:
        return "文字列"
    dt = str(s.dtype)
    if dt.startswith("int") or dt == "Int64":
        return "整数"
    if dt.startswith("float"):
        return "整数" if (v % 1 == 0).all() and not col.endswith(("_c", "_kwh", "_m3", "_a", "_kpa", "_mm_s", "_rpm", "_pct", "rate")) else "小数"
    if dt.startswith("bool"):
        return "真偽"
    x = v.astype(str)
    if x.str.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}").all():
        return "日時"
    if x.str.fullmatch(r"\d{4}-\d{2}-\d{2}").all():
        return "日付"
    if x.isin(["True", "False"]).all():
        return "真偽"
    return "文字列"


def table_files(folder: str, name: str):
    base = DATA / folder
    for cand in (base / f"{name}.csv", base / "master" / f"{name}.csv"):
        if cand.exists():
            return [cand]
    sub = base / name
    if sub.is_dir():
        return sorted(sub.glob("*.csv"))
    return []


def main():
    man = pd.read_csv(DATA / "MANIFEST.csv")
    rows_of = dict(zip(man["path"], man["rows"]))
    missing = []
    doc = ["# データ辞書（全テーブル・全列）", "",
           "> このファイルは `tools/build_docs.py` で生成しています。列の型はデータから推定しています。", ""]
    per_folder = {}
    for (folder, name), meta in T.items():
        files = table_files(folder, name)
        if not files:
            missing.append(f"{folder}/{name}: file not found")
            continue
        sample = pd.read_csv(files[0], nrows=20000, low_memory=False)
        undocumented = [c for c in sample.columns if c not in meta["cols"]]
        extra = [c for c in meta["cols"] if c not in sample.columns]
        if undocumented or extra:
            missing.append(f"{folder}/{name}: undocumented={undocumented} stale={extra}")
        nrows = sum(int(rows_of.get(f.relative_to(DATA).as_posix(), 0) or 0) for f in files)
        rel = [f.relative_to(DATA).as_posix() for f in files]
        loc = rel[0] if len(rel) == 1 else f"{Path(rel[0]).parent.as_posix()}/（{len(rel)} ファイル）"
        sec = [f"### {meta['title']}（`{name}`）", "", meta["desc"], "",
               f"- ファイル: `{loc}`", f"- 行数: {nrows:,}", f"- 主キー: `{meta['pk']}`"]
        if meta["fk"]:
            sec.append(f"- 外部キー: {meta['fk']}")
        sec += ["", "| 列名 | 型 | 説明 | 例 |", "|---|---|---|---|"]
        for c in sample.columns:
            ex = sample[c].dropna()
            exv = str(ex.iloc[0]).replace("\n", " ").replace("|", "／") if len(ex) else ""
            if len(exv) > 40:
                exv = exv[:40] + "…"
            sec.append(f"| `{c}` | {infer_type(sample[c], c)} | {meta['cols'].get(c, '（未記載）')} | {exv} |")
        sec.append("")
        per_folder.setdefault(folder, []).append("\n".join(sec))
    if missing:
        print("\n".join(missing))
        sys.exit(1)
    for folder, (title, desc) in DATASETS.items():
        doc += [f"## {folder}　{title}", "", desc, ""] + per_folder.get(folder, [])
        if folder == "07_excel_reports":
            doc += [EXCEL_NOTE, ""]
        if folder == "08_app_logs":
            doc += [APP_NOTE, ""]
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "data_dictionary.md").write_text("\n".join(doc), encoding="utf-8", newline="\n")
    for folder, (title, desc) in DATASETS.items():
        body = [f"# {folder}　{title}", "", desc, "", "全体の説明はリポジトリ直下の README.md、全列の定義は docs/data_dictionary.md を参照してください。", ""]
        files = man[man["path"].str.startswith(folder + "/")]
        body += ["## ファイル", "", "| ファイル | 行数 | サイズ |", "|---|---:|---:|"]
        grouped = {}
        for r in files.itertuples():
            p = Path(r.path)
            key = p.parent.as_posix() + "/" if len(files) > 12 and p.parent.name not in (folder, "master") else r.path
            g = grouped.setdefault(key, [0, None, 0])
            g[0] += 1
            if pd.notna(r.rows):
                g[1] = (g[1] or 0) + int(r.rows)
            g[2] += int(r.size_bytes)
        for k, (n, rws, sz) in grouped.items():
            label = f"`{k}`" + (f"（{n} ファイル）" if n > 1 else "")
            body.append(f"| {label} | {'-' if rws is None else f'{rws:,}'} | {sz / 1e6:.1f} MB |")
        body.append("")
        body += per_folder.get(folder, [])
        if folder == "07_excel_reports":
            body += [EXCEL_NOTE]
        if folder == "08_app_logs":
            body += [APP_NOTE]
        (DATA / folder / "README.md").write_text("\n".join(body) + "\n", encoding="utf-8", newline="\n")
    print("docs written")


EXCEL_NOTE = """### 帳票の書式（店舗ごとに異なります）

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
日報の売上は POS（01_retail_ec の orders）と突き合わせられます。手入力による転記ミスも少し含まれます。"""

APP_NOTE = """### イベントの JSON 構造

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

`purchase` イベントの `order_id`（旧スキーマは `orderNo`）は 01_retail_ec の `orders.order_id` と一致し、閲覧から購入までを受注データとつなげて分析できます。"""

if __name__ == "__main__":
    main()
