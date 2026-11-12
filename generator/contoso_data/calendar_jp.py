"""Japanese public holidays (2024-2026) and the shared calendar table."""
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

HOLIDAYS = {
    # 2024
    "2024-01-01": "元日", "2024-01-08": "成人の日", "2024-02-11": "建国記念の日", "2024-02-12": "休日",
    "2024-02-23": "天皇誕生日", "2024-03-20": "春分の日", "2024-04-29": "昭和の日", "2024-05-03": "憲法記念日",
    "2024-05-04": "みどりの日", "2024-05-05": "こどもの日", "2024-05-06": "休日", "2024-07-15": "海の日",
    "2024-08-11": "山の日", "2024-08-12": "休日", "2024-09-16": "敬老の日", "2024-09-22": "秋分の日",
    "2024-09-23": "休日", "2024-10-14": "スポーツの日", "2024-11-03": "文化の日", "2024-11-04": "休日",
    "2024-11-23": "勤労感謝の日",
    # 2025
    "2025-01-01": "元日", "2025-01-13": "成人の日", "2025-02-11": "建国記念の日", "2025-02-23": "天皇誕生日",
    "2025-02-24": "休日", "2025-03-20": "春分の日", "2025-04-29": "昭和の日", "2025-05-03": "憲法記念日",
    "2025-05-04": "みどりの日", "2025-05-05": "こどもの日", "2025-05-06": "休日", "2025-07-21": "海の日",
    "2025-08-11": "山の日", "2025-09-15": "敬老の日", "2025-09-23": "秋分の日", "2025-10-13": "スポーツの日",
    "2025-11-03": "文化の日", "2025-11-23": "勤労感謝の日", "2025-11-24": "休日",
    # 2026
    "2026-01-01": "元日", "2026-01-12": "成人の日", "2026-02-11": "建国記念の日", "2026-02-23": "天皇誕生日",
    "2026-03-20": "春分の日", "2026-04-29": "昭和の日", "2026-05-03": "憲法記念日", "2026-05-04": "みどりの日",
    "2026-05-05": "こどもの日", "2026-05-06": "休日", "2026-07-20": "海の日", "2026-08-11": "山の日",
    "2026-09-21": "敬老の日", "2026-09-22": "休日", "2026-09-23": "秋分の日", "2026-10-12": "スポーツの日",
    "2026-11-03": "文化の日", "2026-11-23": "勤労感謝の日",
}
HOLIDAY_DATES = {date.fromisoformat(k) for k in HOLIDAYS}
WEEKDAY_JA = ["月", "火", "水", "木", "金", "土", "日"]


def is_holiday(d: date) -> bool:
    return d in HOLIDAY_DATES


def is_offday(d: date) -> bool:
    """Weekend, public holiday or company new-year break (12/30-1/3)."""
    return d.weekday() >= 5 or d in HOLIDAY_DATES or (d.month == 12 and d.day >= 30) or (d.month == 1 and d.day <= 3)


def daterange(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def fiscal_year(d: date) -> int:
    return d.year if d.month >= 4 else d.year - 1


def build_calendar(start: date, end: date) -> pd.DataFrame:
    rows = []
    for d in daterange(start, end):
        fy = fiscal_year(d)
        fq = ((d.month - 4) % 12) // 3 + 1
        rows.append(dict(
            date=d.isoformat(), year=d.year, month=d.month, day=d.day, year_month=f"{d.year}-{d.month:02d}",
            weekday_num=d.weekday() + 1, weekday_ja=WEEKDAY_JA[d.weekday()], is_weekend=d.weekday() >= 5,
            is_holiday=d in HOLIDAY_DATES, holiday_name=HOLIDAYS.get(d.isoformat(), ""),
            is_business_day=not is_offday(d), fiscal_year=fy, fiscal_quarter=f"FY{fy}Q{fq}",
            week_start_date=(d - timedelta(days=d.weekday())).isoformat(),
            season={12: "冬", 1: "冬", 2: "冬", 3: "春", 4: "春", 5: "春", 6: "夏", 7: "夏", 8: "夏"}.get(d.month, "秋"),
        ))
    return pd.DataFrame(rows)
