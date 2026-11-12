"""Generate the full dummy dataset.

Usage:
    python generate.py --out ../data --organizer-out ../_organizer_only
"""
from __future__ import annotations

import argparse
import shutil
import time
from pathlib import Path

import pandas as pd

from contoso_data import (app_logs, calendar_jp, config, energy, excel_reports, hr, manufacturing, marketing, people,
                          retail, support, weather)
from contoso_data.io_utils import write_csv

DIRS = {
    "common": "00_common",
    "retail": "01_retail_ec",
    "mfg": "02_manufacturing_iot",
    "mkt": "03_sales_marketing",
    "hr": "04_hr_attendance",
    "energy": "05_facility_energy",
    "support": "06_customer_support",
    "excel": "07_excel_reports",
    "app": "08_app_logs",
}


def manifest(out: Path) -> pd.DataFrame:
    rows = []
    for p in sorted(out.rglob("*")):
        if not p.is_file() or p.name == "MANIFEST.csv":
            continue
        n = None
        if p.suffix in (".csv", ".jsonl"):
            enc = "cp932" if p.name.startswith("naha_daily") else "utf-8"
            if p.suffix == ".csv":
                try:
                    n = len(pd.read_csv(p, encoding=enc, low_memory=False))
                except Exception:
                    n = None
            else:
                with open(p, encoding="utf-8") as fh:
                    n = sum(1 for _ in fh)
        rows.append(dict(path=p.relative_to(out).as_posix(), size_bytes=p.stat().st_size, rows=n))
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="../data")
    ap.add_argument("--organizer-out", default="../_organizer_only/expected_outputs")
    ap.add_argument("--seed", type=int, default=config.BASE_SEED)
    a = ap.parse_args()
    out = Path(a.out).resolve()
    org = Path(a.organizer_out).resolve()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    s = a.seed
    t0 = time.time()

    def step(name):
        print(f"[{time.time() - t0:6.0f}s] {name}", flush=True)

    step("weather (JMA cache) / calendar / organization")
    wx = weather.load()
    write_csv(calendar_jp.build_calendar(config.RETAIL_START, pd.Timestamp("2026-12-31").date()), out / DIRS["common"] / "calendar.csv")
    depts, emp = people.build(s + 1)
    step("02 manufacturing / IoT")
    mfg = manufacturing.generate(out / DIRS["mfg"], wx, emp, s + 2)
    step("01 retail / EC")
    rr = retail.generate(out / DIRS["retail"], wx, mfg, s + 3)
    step("08 app logs")
    app_logs.generate(out / DIRS["app"], rr, s + 8)
    step("06 customer support")
    inq = support.generate(out / DIRS["support"], rr, mfg, emp, wx, s + 6)
    step("03 sales / marketing")
    marketing.generate(out / DIRS["mkt"], emp, inq, s + 4)
    step("04 HR / attendance")
    h = hr.generate(out / DIRS["hr"], depts, emp, mfg, s + 5)
    step("05 facility / energy")
    energy.generate(out / DIRS["energy"], wx, rr, h, mfg, s + 7)
    step("07 Excel reports")
    excel_reports.generate(out / DIRS["excel"], org, rr, emp, inq, wx, s + 9)
    step("manifest")
    m = manifest(out)
    write_csv(m, out / "MANIFEST.csv")
    print(m.groupby(m["path"].str.split("/").str[0]).agg(files=("path", "count"), mb=("size_bytes", lambda x: round(x.sum() / 1e6, 1)),
                                                         rows=("rows", "sum")).to_string())
    step(f"done -> {out}")


if __name__ == "__main__":
    main()
