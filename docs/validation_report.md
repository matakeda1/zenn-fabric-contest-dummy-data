# 検証レポート

`tools/validate.py` の実行結果です（主キーの一意性、データセット間の外部キー、金額の整合など）。

| 結果 | チェック | 詳細 |
|---|---|---|
| ✅ | PK unique: calendar.date | rows=1,096 dup=0 null=0 |
| ✅ | PK unique: stores.store_id | rows=17 dup=0 null=0 |
| ✅ | PK unique: products.product_id | rows=77 dup=0 null=0 |
| ✅ | PK unique: customers.customer_id | rows=32,459 dup=0 null=0 |
| ✅ | PK unique: price_history.price_id | rows=160 dup=0 null=0 |
| ✅ | PK unique: promotions.promotion_id | rows=20 dup=0 null=0 |
| ✅ | PK unique: subscriptions.subscription_id | rows=3,210 dup=0 null=0 |
| ✅ | PK unique: store_closures.closure_id | rows=141 dup=0 null=0 |
| ✅ | PK unique: orders.order_id | rows=494,189 dup=0 null=0 |
| ✅ | PK unique: order_lines.order_line_id | rows=788,448 dup=0 null=0 |
| ✅ | FK: orders.store_id -> stores | checked=494,189 orphan=0 |
| ✅ | FK: orders.customer_id -> customers | checked=270,093 orphan=0 |
| ✅ | FK: orders.promotion_code -> promotions | checked=26,142 orphan=0 |
| ✅ | FK: order_lines.order_id -> orders | checked=788,448 orphan=0 |
| ✅ | FK: order_lines.product_id -> products | checked=788,448 orphan=0 |
| ✅ | FK: customers.home_store_id -> stores | checked=16,903 orphan=0 |
| ✅ | FK: subscriptions.customer_id -> customers | checked=3,210 orphan=0 |
| ✅ | orders totals = sum(order_lines) + shipping | mismatch=0 |
| ✅ | orders period 2024-01-01..2026-10-31 | 2024-01-01 00:01:13 .. 2026-10-31 23:36:06 |
| ✅ | orders after customer registration | violations=0 |
| ✅ | PK unique: equipment.equipment_id | rows=8 dup=0 null=0 |
| ✅ | PK unique: failure_history.work_order_id | rows=83 dup=0 null=0 |
| ✅ | PK unique: production_lots.lot_id | rows=13,077 dup=0 null=0 |
| ✅ | FK: production_lots.product_id -> products | checked=13,077 orphan=0 |
| ✅ | FK: sensor_readings.equipment_id -> equipment | checked=2,118,080 orphan=0 |
| ✅ | sensor period 2026-05-01..2026-10-31 | rows=2,118,080 dup_rows=160 |
| ✅ | PK unique: departments.department_id | rows=38 dup=0 null=0 |
| ✅ | PK unique: employees.employee_id | rows=628 dup=0 null=0 |
| ✅ | PK unique: attendance.attendance_id | rows=194,821 dup=0 null=0 |
| ✅ | PK unique: overtime_requests.request_id | rows=49,852 dup=0 null=0 |
| ✅ | PK unique: training_courses.course_id | rows=16 dup=0 null=0 |
| ✅ | PK unique: training_records.training_record_id | rows=3,986 dup=0 null=0 |
| ✅ | PK unique: resignations.resignation_id | rows=201 dup=0 null=0 |
| ✅ | FK: employees.department_id -> departments | checked=628 orphan=0 |
| ✅ | FK: employees.manager_employee_id -> employees | checked=614 orphan=0 |
| ✅ | FK: attendance.employee_id -> employees | checked=194,821 orphan=0 |
| ✅ | FK: overtime_requests.approver -> employees | checked=47,340 orphan=0 |
| ✅ | FK: training_records.course_id -> courses | checked=3,986 orphan=0 |
| ✅ | FK: resignations.employee_id -> employees | checked=201 orphan=0 |
| ✅ | FK: failure_history.technician -> employees | checked=83 orphan=0 |
| ✅ | FK: production_lots.qc_inspector -> employees | checked=13,077 orphan=0 |
| ✅ | attendance one row per employee-day | dup=0 |
| ✅ | PK unique: sites.site_id | rows=22 dup=0 null=0 |
| ✅ | PK unique: hvac_settings_log.log_id | rows=30,810 dup=0 null=0 |
| ✅ | FK: energy.site_id -> sites | checked=730,272 orphan=0 |
| ✅ | FK: attendance.site_id -> sites | checked=194,821 orphan=0 |
| ✅ | FK: departments.site_id -> sites | checked=38 orphan=0 |
| ✅ | energy one row per site-slot | rows=730,272 dup=0 |
| ✅ | PK unique: campaigns.campaign_id | rows=46 dup=0 null=0 |
| ✅ | PK unique: ad_spend_daily.spend_id | rows=1,869 dup=0 null=0 |
| ✅ | PK unique: leads.lead_id | rows=10,536 dup=0 null=0 |
| ✅ | PK unique: opportunities.opportunity_id | rows=1,572 dup=0 null=0 |
| ✅ | PK unique: stage_history.stage_history_id | rows=7,527 dup=0 null=0 |
| ✅ | PK unique: b2b_orders.order_id | rows=441 dup=0 null=0 |
| ✅ | FK: ad_spend.campaign_id -> campaigns | checked=1,869 orphan=0 |
| ✅ | FK: leads.campaign_id -> campaigns | checked=9,495 orphan=0 |
| ✅ | FK: opportunities.lead_id -> leads | checked=1,572 orphan=0 |
| ✅ | FK: stage_history -> opportunities | checked=7,527 orphan=0 |
| ✅ | FK: b2b_orders -> opportunities | checked=441 orphan=0 |
| ✅ | FK: opportunities.owner -> employees | checked=1,572 orphan=0 |
| ✅ | FK: leads.owner -> employees | checked=10,536 orphan=0 |
| ✅ | PK unique: inquiries.inquiry_id | rows=9,378 dup=0 null=0 |
| ✅ | FK: inquiries.customer_id -> customers | checked=7,799 orphan=0 |
| ✅ | FK: inquiries.order_id -> orders | checked=3,959 orphan=0 |
| ✅ | FK: inquiries.product_id -> products | checked=8,156 orphan=0 |
| ✅ | FK: inquiries.store_id -> stores | checked=204 orphan=0 |
| ✅ | FK: inquiries.assignee -> employees | checked=9,378 orphan=0 |
| ✅ | FK: inquiries.lot_no -> production_lots | checked=56 orphan=0 |
| ✅ | FK: leads.source_inquiry_id -> inquiries | checked=92 orphan=0 |
| ✅ | inquiries.jsonl == inquiries.csv (rows) | 9378 vs 9378 |
| ✅ | app purchase.order_id -> orders | events=133,648 legacy=8,051 purchases=2,245 |
| ✅ | every app order in window has a purchase event | app_orders=2,245 |
| ✅ | 07 excel/csv files | files=253 |
