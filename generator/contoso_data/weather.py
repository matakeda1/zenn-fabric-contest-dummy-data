"""JMA daily weather: fetch (once), cache, and helpers to derive sub-daily temperature.

Source: 気象庁「過去の気象データ検索」(https://www.data.jma.go.jp/stats/etrn/index.php)
The cache is committed so that the generator runs offline and deterministically.
"""
from __future__ import annotations

import io
import re
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from . import config

CACHE = Path(__file__).resolve().parent.parent / "reference" / "jma_daily_weather.csv"
URL = "https://www.data.jma.go.jp/stats/etrn/view/daily_s1.php?prec_no={p}&block_no={b}&year={y}&month={m}&day=&view="

COLS = [
    "day", "pressure_local_hpa", "pressure_sea_hpa", "precip_mm", "precip_max_1h_mm", "precip_max_10m_mm",
    "temp_mean_c", "temp_max_c", "temp_min_c", "humidity_mean_pct", "humidity_min_pct", "wind_mean_ms",
    "wind_max_ms", "wind_max_dir", "gust_max_ms", "gust_max_dir", "sunshine_h", "snowfall_cm",
    "snow_depth_cm", "weather_day", "weather_night",
]
NUMERIC = [c for c in COLS if c not in ("day", "wind_max_dir", "gust_max_dir", "weather_day", "weather_night")]


def _num(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return np.nan
    s = str(v).strip()
    if s in ("--", "－－"):
        return 0.0
    s = re.sub(r"[\)\]#\s]", "", s)
    try:
        return float(s)
    except ValueError:
        return np.nan


def _months(start: date, end: date):
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        yield y, m
        m += 1
        if m == 13:
            y, m = y + 1, 1


def fetch(start: date = date(2024, 1, 1), end: date = config.DATA_END, sleep: float = 0.6) -> pd.DataFrame:
    import requests

    frames = []
    sess = requests.Session()
    sess.headers["User-Agent"] = "Mozilla/5.0 (dummy-data generator for a Zenn contest; contact via GitHub)"
    for key, st in config.STATIONS.items():
        for y, m in _months(start, end):
            url = URL.format(p=st["prec_no"], b=st["block_no"], y=y, m=m)
            for attempt in range(4):
                try:
                    r = sess.get(url, timeout=30)
                    r.raise_for_status()
                    break
                except Exception:
                    if attempt == 3:
                        raise
                    time.sleep(3 * (attempt + 1))
            r.encoding = "utf-8"
            if st["name"] not in r.text:
                raise RuntimeError(f"station name {st['name']} not found in {url}")
            t = pd.read_html(io.StringIO(r.text), attrs={"id": "tablefix1"})[0]
            t.columns = COLS
            t = t[pd.to_numeric(t["day"], errors="coerce").notna()].copy()
            t["date"] = [date(y, m, int(d)).isoformat() for d in t["day"]]
            for c in NUMERIC:
                t[c] = t[c].map(_num)
            t["station"] = key
            t["station_name"] = st["name"]
            frames.append(t.drop(columns=["day"]))
            time.sleep(sleep)
        print(f"  fetched {key}", flush=True)
    df = pd.concat(frames, ignore_index=True)
    cols = ["station", "station_name", "date"] + [c for c in COLS if c != "day"]
    return df[cols]


def load() -> pd.DataFrame:
    if not CACHE.exists():
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        print("Fetching JMA daily weather (first run only)...")
        df = fetch()
        df.to_csv(CACHE, index=False, lineterminator="\n")
    df = pd.read_csv(CACHE)
    df["date"] = pd.to_datetime(df["date"])
    # Fill rare gaps so downstream models never see NaN temperatures.
    df = df.sort_values(["station", "date"]).reset_index(drop=True)
    for c in ["temp_mean_c", "temp_max_c", "temp_min_c", "humidity_mean_pct"]:
        df[c] = df.groupby("station")[c].transform(lambda s: s.interpolate(limit_direction="both"))
    for c in ["precip_mm", "snowfall_cm", "snow_depth_cm", "gust_max_ms", "sunshine_h"]:
        df[c] = df[c].fillna(0.0)
    df["weather_day"] = df["weather_day"].fillna("")
    return df


def daily(df: pd.DataFrame, station: str) -> pd.DataFrame:
    return df[df["station"] == station].set_index("date").sort_index()


def subdaily_temperature(day_df: pd.DataFrame, freq_minutes: int, rng: np.random.Generator,
                         start: date, end: date, noise: float = 0.35) -> pd.Series:
    """Diurnal temperature curve from daily min/max (min ~05:00, max ~14:00) with AR(1) noise."""
    idx = pd.date_range(pd.Timestamp(start), pd.Timestamp(end) + pd.Timedelta(days=1), freq=f"{freq_minutes}min",
                        inclusive="left")
    d = day_df.loc[pd.Timestamp(start) - pd.Timedelta(days=1): pd.Timestamp(end) + pd.Timedelta(days=1)]
    anchors_t, anchors_v = [], []
    for ts, row in d.iterrows():
        anchors_t.append(ts + pd.Timedelta(hours=5))
        anchors_v.append(row["temp_min_c"])
        anchors_t.append(ts + pd.Timedelta(hours=14, minutes=30))
        anchors_v.append(row["temp_max_c"])
    at = np.array([a.value for a in anchors_t], dtype="int64")  # Timestamp.value is always ns
    av = np.array(anchors_v, dtype=float)
    x = idx.as_unit("ns").asi8
    pos = np.searchsorted(at, x, side="right") - 1
    pos = np.clip(pos, 0, len(at) - 2)
    t0, t1 = at[pos], at[pos + 1]
    v0, v1 = av[pos], av[pos + 1]
    frac = (x - t0) / (t1 - t0)
    curve = v0 + (v1 - v0) * (1 - np.cos(np.pi * frac)) / 2
    eps = rng.normal(0, noise, len(x))
    ar = np.empty_like(eps)
    acc = 0.0
    phi = 0.97 if freq_minutes <= 5 else 0.85
    for i, e in enumerate(eps):
        acc = phi * acc + e * np.sqrt(1 - phi ** 2)
        ar[i] = acc
    return pd.Series(curve + ar, index=idx)


def weather_category(text: str, precip: float, snowfall: float) -> str:
    """Rough category from JMA 天気概況 text."""
    t = text or ""
    if snowfall >= 1 or ("雪" in t[:2]):
        return "雪"
    if precip >= 10 or t.startswith("雨") or t.startswith("大雨"):
        return "雨"
    if t.startswith("晴") or t.startswith("快晴"):
        return "晴"
    if t.startswith("曇") or t.startswith("薄曇"):
        return "曇"
    if precip >= 1:
        return "雨"
    return "曇" if not t else ("晴" if "晴" in t else "曇")


if __name__ == "__main__":
    out = fetch()
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(CACHE, index=False, lineterminator="\n")
    print(out.shape, "->", CACHE)
