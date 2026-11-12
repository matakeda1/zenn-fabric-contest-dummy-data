"""Integrity checks for the generated dataset. Writes docs/validation_report.md and exits non-zero on failure.

    python tools/validate.py
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data"
results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(("OK  " if ok else "NG  ") + name + (f"  ({detail})" if detail else ""), flush=True)


def read(rel, **kw):
    p = D / rel
    if p.is_dir():
        return pd.concat([pd.read_csv(f, low_memory=False, **kw) for f in sorted(p.glob("*.csv"))], ignore_index=True)
    return pd.read_csv(p, low_memory=False, **kw)


def pk(df, col, name):
    dup = df[col].duplicated().sum()
    nul = df[col].isna().sum()
    check(f"PK unique: {name}.{col}", dup == 0 and nul == 0, f"rows={len(df):,} dup={dup} null={nul}")


def fk(child, ccol, parent, pcol, name):
    v = child[ccol].dropna()
    bad = (~v.isin(set(parent[pcol]))).sum()
    check(f"FK: {name}", bad == 0, f"checked={len(v):,} orphan={bad}")


def main():
    cal = read("00_common/calendar.csv")
    pk(cal, "date", "calendar")
    st = read("01_retail_ec/stores.csv")
    pr = read("01_retail_ec/products.csv")
    cu = read("01_retail_ec/customers.csv")
    ph = read("01_retail_ec/product_price_history.csv")
    pm = read("01_retail_ec/promotions.csv")
    sb = read("01_retail_ec/subscriptions.csv")
    cl = read("01_retail_ec/store_closures.csv")
    od = read("01_retail_ec/orders")
    ol = read("01_retail_ec/order_lines")
    for df, c, n in [(st, "store_id", "stores"), (pr, "product_id", "products"), (cu, "customer_id", "customers"),
                     (ph, "price_id", "price_history"), (pm, "promotion_id", "promotions"), (sb, "subscription_id", "subscriptions"),
                     (cl, "closure_id", "store_closures"), (od, "order_id", "orders"), (ol, "order_line_id", "order_lines")]:
        pk(df, c, n)
    fk(od, "store_id", st, "store_id", "orders.store_id -> stores")
    fk(od, "customer_id", cu, "customer_id", "orders.customer_id -> customers")
    fk(od, "promotion_code", pm, "promotion_code", "orders.promotion_code -> promotions")
    fk(ol, "order_id", od, "order_id", "order_lines.order_id -> orders")
    fk(ol, "product_id", pr, "product_id", "order_lines.product_id -> products")
    fk(cu, "home_store_id", st, "store_id", "customers.home_store_id -> stores")
    fk(sb, "customer_id", cu, "customer_id", "subscriptions.customer_id -> customers")
    s = ol.groupby("order_id")[["line_subtotal", "tax_amount"]].sum()
    j = od.set_index("order_id")[["subtotal_excl_tax", "tax_total", "shipping_fee", "total_incl_tax"]].join(s)
    bad = ((j["subtotal_excl_tax"] != j["line_subtotal"]) | (j["tax_total"] != j["tax_amount"]) |
           (j["total_incl_tax"] != j["subtotal_excl_tax"] + j["tax_total"] + j["shipping_fee"])).sum()
    check("orders totals = sum(order_lines) + shipping", bad == 0, f"mismatch={bad}")
    dt = pd.to_datetime(od["order_datetime"])
    check("orders period 2024-01-01..2026-10-31", dt.min() >= pd.Timestamp("2024-01-01") and dt.max() < pd.Timestamp("2026-11-01"),
          f"{dt.min()} .. {dt.max()}")
    reg = cu.set_index("customer_id")["registered_date"]
    m = od.dropna(subset=["customer_id"])
    early = (pd.to_datetime(m["order_datetime"]).dt.normalize() < pd.to_datetime(m["customer_id"].map(reg))).sum()
    check("orders after customer registration", early == 0, f"violations={early}")
    # 02
    eq = read("02_manufacturing_iot/equipment.csv")
    fh = read("02_manufacturing_iot/failure_history.csv")
    lots = read("02_manufacturing_iot/production_lots.csv")
    pk(eq, "equipment_id", "equipment")
    pk(fh, "work_order_id", "failure_history")
    pk(lots, "lot_id", "production_lots")
    fk(lots, "product_id", pr, "product_id", "production_lots.product_id -> products")
    sr = read("02_manufacturing_iot/sensor_readings")
    fk(sr, "equipment_id", eq, "equipment_id", "sensor_readings.equipment_id -> equipment")
    t = pd.to_datetime(sr["timestamp"])
    check("sensor period 2026-05-01..2026-10-31", t.min() >= pd.Timestamp("2026-05-01") and t.max() < pd.Timestamp("2026-11-01"),
          f"rows={len(sr):,} dup_rows={sr.duplicated().sum()}")
    # 04
    dep = read("04_hr_attendance/departments.csv")
    emp = read("04_hr_attendance/employees.csv")
    att = read("04_hr_attendance/attendance.csv")
    otr = read("04_hr_attendance/overtime_requests.csv")
    trc = read("04_hr_attendance/training_courses.csv")
    trr = read("04_hr_attendance/training_records.csv")
    rsg = read("04_hr_attendance/resignations.csv")
    for df, c, n in [(dep, "department_id", "departments"), (emp, "employee_id", "employees"), (att, "attendance_id", "attendance"),
                     (otr, "request_id", "overtime_requests"), (trc, "course_id", "training_courses"),
                     (trr, "training_record_id", "training_records"), (rsg, "resignation_id", "resignations")]:
        pk(df, c, n)
    fk(emp, "department_id", dep, "department_id", "employees.department_id -> departments")
    fk(emp, "manager_employee_id", emp, "employee_id", "employees.manager_employee_id -> employees")
    fk(att, "employee_id", emp, "employee_id", "attendance.employee_id -> employees")
    fk(otr, "approver_employee_id", emp, "employee_id", "overtime_requests.approver -> employees")
    fk(trr, "course_id", trc, "course_id", "training_records.course_id -> courses")
    fk(rsg, "employee_id", emp, "employee_id", "resignations.employee_id -> employees")
    fk(fh, "technician_employee_id", emp, "employee_id", "failure_history.technician -> employees")
    fk(lots, "qc_inspector_employee_id", emp, "employee_id", "production_lots.qc_inspector -> employees")
    dup_att = att.duplicated(["employee_id", "work_date"]).sum()
    check("attendance one row per employee-day", dup_att == 0, f"dup={dup_att}")
    # 05
    si = read("05_facility_energy/sites.csv")
    en = read("05_facility_energy/energy_usage_30min")
    hv = read("05_facility_energy/hvac_settings_log.csv")
    pk(si, "site_id", "sites")
    pk(hv, "log_id", "hvac_settings_log")
    fk(en, "site_id", si, "site_id", "energy.site_id -> sites")
    fk(att, "site_id", si, "site_id", "attendance.site_id -> sites")
    fk(dep, "site_id", si, "site_id", "departments.site_id -> sites")
    d2 = en.duplicated(["site_id", "timestamp"]).sum()
    check("energy one row per site-slot", d2 == 0, f"rows={len(en):,} dup={d2}")
    # 03
    cp = read("03_sales_marketing/campaigns.csv")
    sp = read("03_sales_marketing/ad_spend_daily.csv")
    ld = read("03_sales_marketing/leads.csv")
    op = read("03_sales_marketing/opportunities.csv")
    sh = read("03_sales_marketing/opportunity_stage_history.csv")
    bo = read("03_sales_marketing/orders.csv")
    for df, c, n in [(cp, "campaign_id", "campaigns"), (sp, "spend_id", "ad_spend_daily"), (ld, "lead_id", "leads"),
                     (op, "opportunity_id", "opportunities"), (sh, "stage_history_id", "stage_history"), (bo, "order_id", "b2b_orders")]:
        pk(df, c, n)
    fk(sp, "campaign_id", cp, "campaign_id", "ad_spend.campaign_id -> campaigns")
    fk(ld, "campaign_id", cp, "campaign_id", "leads.campaign_id -> campaigns")
    fk(op, "lead_id", ld, "lead_id", "opportunities.lead_id -> leads")
    fk(sh, "opportunity_id", op, "opportunity_id", "stage_history -> opportunities")
    fk(bo, "opportunity_id", op, "opportunity_id", "b2b_orders -> opportunities")
    fk(op, "owner_employee_id", emp, "employee_id", "opportunities.owner -> employees")
    fk(ld, "owner_employee_id", emp, "employee_id", "leads.owner -> employees")
    # 06
    iq = read("06_customer_support/inquiries.csv")
    pk(iq, "inquiry_id", "inquiries")
    fk(iq, "customer_id", cu, "customer_id", "inquiries.customer_id -> customers")
    fk(iq, "order_id", od, "order_id", "inquiries.order_id -> orders")
    fk(iq, "product_id", pr, "product_id", "inquiries.product_id -> products")
    fk(iq, "store_id", st, "store_id", "inquiries.store_id -> stores")
    fk(iq, "assignee_employee_id", emp, "employee_id", "inquiries.assignee -> employees")
    fk(iq, "lot_no", lots, "lot_id", "inquiries.lot_no -> production_lots")
    fk(ld, "source_inquiry_id", iq, "inquiry_id", "leads.source_inquiry_id -> inquiries")
    jl = pd.read_json(D / "06_customer_support/inquiries.jsonl", lines=True)
    check("inquiries.jsonl == inquiries.csv (rows)", len(jl) == len(iq), f"{len(jl)} vs {len(iq)}")
    # 08
    purchases, n_ev, legacy = [], 0, 0
    for f in sorted(glob.glob(str(D / "08_app_logs/events/*.jsonl"))):
        with open(f, encoding="utf-8") as fh_:
            for line in fh_:
                n_ev += 1
                e = json.loads(line)
                if "eventId" in e:
                    legacy += 1
                    if e.get("name") == "purchase":
                        purchases.append(e["orderNo"])
                elif e["event_name"] == "purchase":
                    purchases.append(e["params"]["order_id"])
    pu = pd.Series(purchases).drop_duplicates()
    check("app purchase.order_id -> orders", pu.isin(set(od["order_id"])).all(), f"events={n_ev:,} legacy={legacy:,} purchases={len(pu):,}")
    win = od[(pd.to_datetime(od["order_datetime"]) >= "2026-09-01") & (od["device"] == "アプリ") & (od["order_status"] != "キャンセル")]
    check("every app order in window has a purchase event", win["order_id"].isin(set(pu)).all(), f"app_orders={len(win):,}")
    # 07
    files = list((D / "07_excel_reports").rglob("*.xlsx")) + list((D / "07_excel_reports").rglob("*.csv"))
    check("07 excel/csv files", len(files) >= 100, f"files={len(files)}")
    ok = all(r[1] for r in results)
    lines = ["# 検証レポート", "", "`tools/validate.py` の実行結果です（主キーの一意性、データセット間の外部キー、金額の整合など）。", "",
             "| 結果 | チェック | 詳細 |", "|---|---|---|"]
    lines += [f"| {'✅' if o else '❌'} | {n} | {d} |" for n, o, d in results]
    (ROOT / "docs" / "validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("ALL OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
