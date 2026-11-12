"""Retail / EC: stores, products, customers, orders (header + lines), subscriptions, closures."""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

from . import config, products as prodmod, weather
from .calendar_jp import HOLIDAY_DATES, daterange
from .io_utils import fmt_d, fmt_dt, write_csv

AGE_GROUPS = ["10代", "20代", "30代", "40代", "50代", "60代", "70代以上"]
AGE_P = np.array([0.02, 0.18, 0.24, 0.22, 0.18, 0.11, 0.05])

HOUR_PROFILE = {
    "オフィス街": {7: 0.9, 8: 1.6, 9: 1.2, 10: 0.7, 11: 0.8, 12: 1.3, 13: 1.2, 14: 0.8, 15: 1.0, 16: 0.7, 17: 0.6, 18: 0.5, 19: 0.3},
    "駅前": {7: 1.0, 8: 1.4, 9: 1.0, 10: 0.8, 11: 0.9, 12: 1.1, 13: 1.0, 14: 0.9, 15: 1.0, 16: 0.9, 17: 1.0, 18: 1.0, 19: 0.8, 20: 0.5},
    "繁華街": {8: 0.4, 9: 0.6, 10: 0.8, 11: 1.0, 12: 1.2, 13: 1.3, 14: 1.3, 15: 1.4, 16: 1.2, 17: 1.0, 18: 0.9, 19: 0.7, 20: 0.5},
    "住宅地": {9: 0.8, 10: 1.2, 11: 1.1, 12: 0.9, 13: 0.9, 14: 1.1, 15: 1.2, 16: 1.0, 17: 0.8, 18: 0.5},
    "観光地": {8: 0.5, 9: 0.8, 10: 1.2, 11: 1.3, 12: 1.2, 13: 1.3, 14: 1.4, 15: 1.3, 16: 1.1, 17: 0.8, 18: 0.6, 19: 0.4, 20: 0.3},
}
HOUR_PROFILE["商業地"] = HOUR_PROFILE["繁華街"]
HOUR_PROFILE["商業施設"] = HOUR_PROFILE["繁華街"]

DOW = {  # Mon..Sun, holiday
    "オフィス街": [1.05, 1.08, 1.08, 1.08, 1.10, 0.55, 0.45, 0.50],
    "駅前": [1.00, 1.00, 1.00, 1.00, 1.05, 1.05, 0.90, 0.95],
    "繁華街": [0.88, 0.88, 0.88, 0.90, 0.97, 1.30, 1.25, 1.25],
    "商業地": [0.90, 0.90, 0.90, 0.92, 0.98, 1.25, 1.20, 1.20],
    "商業施設": [0.85, 0.85, 0.85, 0.88, 0.95, 1.35, 1.30, 1.30],
    "住宅地": [0.92, 0.92, 0.92, 0.92, 0.95, 1.20, 1.15, 1.15],
    "観光地": [0.85, 0.85, 0.85, 0.88, 0.95, 1.35, 1.25, 1.40],
}
MONTH = [0.92, 0.95, 1.02, 1.00, 1.03, 0.95, 1.00, 1.02, 0.97, 1.00, 1.02, 1.12]
EC_HOUR = np.array([0.9, 0.6, 0.35, 0.2, 0.15, 0.2, 0.35, 0.6, 0.8, 0.9, 1.0, 1.0, 1.25, 1.1, 0.95, 0.95, 0.95, 1.0,
                    1.05, 1.2, 1.4, 1.5, 1.4, 1.15])
STORE_PAY = ["現金", "クレジットカード", "交通系IC", "電子マネー", "QRコード決済"]
EC_PAY = ["クレジットカード", "ID決済", "コンビニ後払い", "代金引換", "キャリア決済"]
REGION_STATION = {"北海道": "sapporo", "東北": "sendai", "関東": "tokyo", "中部": "nagoya", "近畿": "osaka",
                  "中国": "hiroshima", "四国": "hiroshima", "九州": "fukuoka", "九州・沖縄": "naha"}
TRANSIT = {"北海道": 2, "東北": 1, "関東": 1, "中部": 1, "近畿": 2, "中国": 2, "四国": 2, "九州": 2, "九州・沖縄": 3}


@dataclass
class RetailResult:
    stores: pd.DataFrame
    customers: pd.DataFrame
    orders: pd.DataFrame
    lines: pd.DataFrame
    subscriptions: pd.DataFrame
    closures: pd.DataFrame
    failed_app_checkouts: pd.DataFrame
    lot_issues: pd.DataFrame
    product_df: pd.DataFrame


def _qty(rng, cats):
    q = np.ones(len(cats), dtype=np.int64)
    u = rng.random(len(cats))
    tables = {"ドリンク": [0.88, 0.98], "焼き菓子": [0.70, 0.92, 0.98], "ギフト": [0.80, 0.92, 0.97],
              "器具・グッズ": [0.95]}
    for c, cut in tables.items():
        m = cats == c
        q[m] = 1 + np.searchsorted(np.array(cut), u[m])
    m = np.isin(cats, ["コーヒー豆", "ドリップバッグ", "ボトル飲料"])
    q[m] = 1 + np.searchsorted(np.array([0.85, 0.97]), u[m])
    return q


class Retail:
    def __init__(self, wx: pd.DataFrame, mfg, seed: int):
        self.rng = np.random.default_rng(seed)
        self.wx = wx
        self.mfg = mfg
        self.days = list(daterange(config.RETAIL_START, config.DATA_END))
        self.didx = {d: i for i, d in enumerate(self.days)}
        cat = prodmod.catalog()
        self.pdf = cat
        self.pids = cat["product_id"].to_numpy()
        self.pcat = cat["category"].to_numpy()
        self.psub = cat["subcategory"].to_numpy()
        self.ptemp = cat["temp_type"].to_numpy()
        self.ptax = cat["tax_class"].to_numpy()
        self.pchan = cat["channel"].to_numpy()
        self.pw_store = np.where(np.isin(self.pchan, ["store", "both"]), cat["store_w"].to_numpy(), 0.0)
        self.pw_ec = np.where(np.isin(self.pchan, ["ec", "both"]), cat["ec_w"].to_numpy(), 0.0)
        self.pindex = {p: i for i, p in enumerate(self.pids)}
        self.avail = np.array([[prodmod.available(p, d) for p in prodmod.P] for d in self.days])
        # price matrix: period 0 (<2025-04), 1 (<2026-04), 2
        ph = prodmod.price_history()
        self.price_hist = ph
        self.price = np.zeros((len(self.pids), 3), dtype=np.int64)
        bounds = [date(2024, 1, 1), date(2025, 4, 1), date(2026, 4, 1)]
        by_p = {}
        for r in ph.itertuples():
            by_p.setdefault(r.product_id, []).append((r.valid_from, r.valid_to if isinstance(r.valid_to, date) else None,
                                                      int(r.unit_price)))
        for i, pid in enumerate(self.pids):
            rows = sorted(by_p[pid])
            for k, b in enumerate(bounds):
                val = [u for f, t, u in rows if f <= b and (t is None or t > b)]
                self.price[i, k] = val[0] if val else rows[0][2]
        self.wxd = {k: weather.daily(wx, k) for k in config.STATIONS}
        self.wcache = {}
        for k, dfw in self.wxd.items():
            for ts_, row in zip(dfw.index, dfw[["precip_mm", "gust_max_ms", "temp_max_c", "snowfall_cm"]].itertuples(index=False)):
                self.wcache[(k, ts_.date())] = row._asdict()
        self.size500 = np.char.endswith(cat["size"].to_numpy().astype(str), "500g")

    # ------------------------------------------------------------------------------------------
    def period(self, d: date) -> int:
        return 0 if d < date(2025, 4, 1) else (1 if d < date(2026, 4, 1) else 2)

    def w(self, station, d):
        return self.wcache[(station, min(d, config.DATA_END))]

    # ------------------------------------------------------------------------------------------
    def customers(self):
        rng = self.rng
        rows = []
        pref_names = [p[0] for p in config.PREFECTURES]
        pref_w = np.array([p[1] * p[3] for p in config.PREFECTURES], dtype=float)
        pref_w /= pref_w.sum()
        region_of = {p[0]: p[2] for p in config.PREFECTURES}

        def reg_dates(n, a: date, b: date, skew=1.0):
            span = (b - a).days
            u = rng.random(n) ** (1 / skew)
            return [a + timedelta(days=int(x * span)) for x in u]

        def mk(channel, reg, store=None):
            age_i = int(rng.choice(len(AGE_GROUPS), p=AGE_P))
            if channel == "アプリ":
                age_i = int(np.clip(age_i - (1 if rng.random() < 0.35 else 0), 0, 6))
            reg_age = [17, 25, 35, 45, 55, 65, 74][age_i] + int(rng.integers(-3, 5))
            byear = reg.year - reg_age
            g = rng.choice(["女性", "男性", "その他・無回答"], p=[0.58, 0.38, 0.04])
            if store is not None:
                pref = store["prefecture"] if rng.random() < 0.9 else str(rng.choice(pref_names, p=pref_w))
            else:
                pref = str(rng.choice(pref_names, p=pref_w))
            one = rng.random() < {"店舗": 0.30, "オンラインストア": 0.35, "アプリ": 0.25}[channel]
            life = int(rng.integers(0, 21)) if one else int(rng.exponential({"店舗": 900, "オンラインストア": 700, "アプリ": 800}[channel]))
            act_end = reg + timedelta(days=life)
            sw = ew = 0.0
            if channel == "店舗":
                sw = rng.gamma(0.7, 1.0)
                if rng.random() < 0.18:
                    ew = rng.gamma(0.6, 0.6)
            elif channel == "オンラインストア":
                ew = rng.gamma(0.8, 1.0)
            else:
                ew = rng.gamma(0.8, 1.1)
                if store is not None:
                    sw = rng.gamma(0.7, 0.8)
            app = channel == "アプリ" or rng.random() < (0.38 if channel == "店舗" else 0.33)
            app_since = reg if channel == "アプリ" else (max(reg, date(2021, 4, 1)) + timedelta(days=int(rng.integers(0, 700))) if app else None)
            older = (reg.year - byear) >= 50
            plat = ("Android" if rng.random() < (0.5 if older else 0.4) else "iOS") if app else None
            rows.append(dict(registered_date=reg, registration_channel=channel, gender=g, birth_year=byear,
                             prefecture=pref, region=region_of[pref], home_store_id=store["store_id"] if store else None,
                             app_user=app, app_since=app_since, platform=plat, mail_opt_in=bool(rng.random() < 0.62),
                             act_end=act_end, store_w=sw, ec_w=ew,
                             age_band=1 if reg.year - byear < 35 else (3 if reg.year - byear >= 55 else 2)))

        for s in config.STORES:
            so = date.fromisoformat(s["open_date"])
            sc = date.fromisoformat(s["close_date"]) if s["close_date"] else config.DATA_END
            if so < date(2024, 1, 1):
                for reg in reg_dates(int(s["base"] * 18), max(so, date(2016, 1, 1)), date(2023, 12, 31), skew=1.6):
                    mk("店舗", reg, s)
            a = max(so, date(2024, 1, 1))
            n_new = int(s["base"] * 0.018 * (min(sc, config.DATA_END) - a).days * (1.6 if so >= date(2025, 1, 1) else 1))
            for reg in reg_dates(max(n_new, 0), a, min(sc, config.DATA_END), skew=1.1):
                mk("店舗", reg, s)
        for reg in reg_dates(5000, date(2016, 1, 15), date(2023, 12, 31), skew=1.8):
            mk("オンラインストア", reg)
        for reg in reg_dates(7600, date(2024, 1, 1), config.DATA_END, skew=1.25):
            mk("オンラインストア", reg)
        stores_open = lambda d: [s for s in config.STORES if date.fromisoformat(s["open_date"]) <= d and  # noqa: E731
                                 (not s["close_date"] or date.fromisoformat(s["close_date"]) >= d)]
        for reg in reg_dates(2000, date(2021, 4, 1), date(2023, 12, 31), skew=1.5) + \
                reg_dates(4600, date(2024, 1, 1), config.DATA_END, skew=1.35):
            st = None
            if rng.random() < 0.55:
                cands = stores_open(reg)
                st = cands[int(rng.integers(len(cands)))]
            mk("アプリ", reg, st)
        df = pd.DataFrame(rows).sort_values("registered_date", kind="stable").reset_index(drop=True)
        df.insert(0, "customer_id", [f"C{i + 1:06d}" for i in range(len(df))])
        wd = []
        for r in df.itertuples():
            if rng.random() < 0.06:
                w = r.act_end + timedelta(days=int(rng.integers(30, 300)))
                wd.append(w if w <= config.DATA_END else None)
            else:
                wd.append(None)
        df["withdrawn_date"] = wd
        df["reg_i"] = [(r - config.RETAIL_START).days for r in df["registered_date"]]
        df["end_i"] = [((min(a, w) if isinstance(w, date) else a) - config.RETAIL_START).days
                       for a, w in zip(df["act_end"], df["withdrawn_date"])]
        df["app_i"] = [((a - config.RETAIL_START).days if isinstance(a, date) else 10 ** 6) for a in df["app_since"]]
        self.cust = df
        return df

    # ------------------------------------------------------------------------------------------
    def closures(self):
        rows = []
        for s in config.STORES:
            for d in self.days:
                so = date.fromisoformat(s["open_date"])
                sc = date.fromisoformat(s["close_date"]) if s["close_date"] else None
                if d < so or (sc and d > sc):
                    continue
                w = self.w(s["station"], d)
                if d.month == 1 and d.day == 1:
                    rows.append((s["store_id"], d, "年始休業", "元日休業"))
                elif s["store_id"] == "S03" and date(2025, 2, 3) <= d <= date(2025, 2, 16):
                    rows.append((s["store_id"], d, "改装休業", "店内改装工事"))
                elif w["precip_mm"] >= 150 or (w["precip_mm"] >= 100 and w["gust_max_ms"] >= 22):
                    rows.append((s["store_id"], d, "臨時休業", "大雨・暴風のため臨時休業"))
                elif w["precip_mm"] >= 100:
                    rows.append((s["store_id"], d, "短縮営業", "大雨のため 16 時で閉店"))
                elif w["snowfall_cm"] >= 25:
                    rows.append((s["store_id"], d, "短縮営業", "大雪のため短縮営業"))
                elif d.month == 12 and d.day == 31:
                    rows.append((s["store_id"], d, "短縮営業", "大晦日のため 17 時で閉店"))
        df = pd.DataFrame(rows, columns=["store_id", "date", "closure_type", "reason"])
        df.insert(0, "closure_id", [f"CL{i + 1:04d}" for i in range(len(df))])
        self.closure_map = {(r.store_id, r.date): r.closure_type for r in df.itertuples()}
        return df

    # ------------------------------------------------------------------------------------------
    def _store_lambda(self, s, d):
        area = s["area_type"]
        so = date.fromisoformat(s["open_date"])
        w = self.w(s["station"], d)
        hol = d in HOLIDAY_DATES
        lam = s["base"] * DOW[area][7 if hol else d.weekday()] * MONTH[d.month - 1]
        yrs = (d - date(2024, 1, 1)).days / 365.25
        lam *= 1 + 0.03 * yrs
        if area == "観光地":
            lam *= 1 + 0.10 * yrs
            if s["store_id"] == "S10" and (d.month == 11 or (d.month == 4 and d.day <= 15)):
                lam *= 1.25
        if s["store_id"] == "S01" and d.month == 2 and 4 <= d.day <= 11:
            lam *= 1.2
        if s["store_id"] == "S16" and d.month in (7, 8):
            lam *= 1.15
        if s["store_id"] == "S03" and d > date(2025, 2, 16):
            lam *= 1.10
        if (d - so).days < 14:
            lam *= 1.45
        elif (d - so).days < 75:
            lam *= 1.15
        if s["store_id"] == "S12" and date(2025, 12, 15) <= d <= date(2025, 12, 28):
            lam *= 1.35
        # weather
        p, tmax, snow = w["precip_mm"], w["temp_max_c"], w["snowfall_cm"]
        f = 1 - 0.011 * min(p, 30)
        if p >= 50:
            f *= 0.85
        if snow >= 5:
            f *= 0.8
        if snow >= 15:
            f *= 0.75
        if tmax >= 35:
            f *= 0.93
        if 18 <= tmax <= 26 and p < 1:
            f *= 1.04
        if tmax <= 5:
            f *= 0.95
        lam *= f
        # events
        md = (d.month, d.day)
        if md in ((1, 2), (1, 3)):
            lam *= 1.2 if area == "観光地" else 0.8
        if md in ((12, 24), (12, 25)):
            lam *= 1.12
        if md in ((2, 13), (2, 14)):
            lam *= 1.1
        if md == (10, 1):
            lam *= 1.25
        if d.month == 3 and d.day <= 10:
            lam *= 1.06
        if d.month == 8 and 13 <= d.day <= 16:
            lam *= 0.6 if area == "オフィス街" else (1.25 if area == "観光地" else 1.0)
        if date(2025, 4, 1) <= d <= date(2025, 6, 30):
            lam *= 0.96
        ct = self.closure_map.get((s["store_id"], d))
        if ct in ("年始休業", "改装休業", "臨時休業"):
            return 0.0, w
        if ct == "短縮営業":
            lam *= 0.5
        return lam, w

    def _store_weights(self, s, d, w, part, eps=0.0):
        di = self.didx[d]
        wt = self.pw_store * self.avail[di]
        tmax = w["temp_max_c"]
        iced = min(0.95, max(0.03, 0.10 + 0.78 / (1 + math.exp(-(tmax - 23) / 3.2)) + eps))
        wt = np.where(self.ptemp == "iced", wt * iced * 2, wt)
        wt = np.where(self.ptemp == "hot", wt * (1 - iced) * 2, wt)
        boost = 1 + max(0.0, tmax - 28) / 6
        wt = np.where(np.isin(self.pids, ["P037", "P042", "P031"]), wt * boost, wt)
        cat = self.pcat
        if part == 0:
            wt = np.where(cat == "ドリンク", wt * 1.35, wt * 0.8)
            wt = np.where(self.ptemp == "hot", wt * 1.15, wt)
            wt = np.where(self.pids == "P054", wt * 1.6, wt)
        elif part == 2:
            wt = np.where(cat == "焼き菓子", wt * 1.5, wt)
        elif part == 3:
            wt = np.where(np.isin(cat, ["コーヒー豆", "ドリップバッグ", "ギフト"]), wt * 1.4, wt)
            wt = np.where(cat == "ドリンク", wt * 0.85, wt)
        md = (d.month, d.day)
        if md == (10, 1):
            wt = np.where(cat == "コーヒー豆", wt * 2.5, wt)
        if d.month == 3 and d.day <= 10:
            wt = np.where(np.isin(cat, ["コーヒー豆", "ドリップバッグ"]), wt * 1.4, wt)
        if d.month == 12 or (d.month == 2 and d.day <= 14) or (d.month == 7):
            wt = np.where(cat == "ギフト", wt * 1.8, wt)
        if d.month in (1, 2) and d <= date(d.year, 2, 14):
            wt = np.where(self.pids == "P057", wt * 1.8, wt)
        if date(2025, 4, 1) <= d <= date(2025, 6, 30):
            wt = np.where(cat == "コーヒー豆", wt * 0.85, wt)
        if date(2026, 6, 19) <= d <= date(2026, 6, 26):
            wt = np.where(cat == "ドリップバッグ", wt * 0.2, wt)
        if s["store_id"] == "S12" and date(2025, 12, 15) <= d <= date(2025, 12, 28):
            wt = np.where(np.isin(cat, ["コーヒー豆", "ドリップバッグ", "器具・グッズ"]), wt * 1.6, wt)
        return wt / wt.sum()

    def _minute_dist(self, s, weekend):
        prof = HOUR_PROFILE["繁華街" if weekend and s["area_type"] == "オフィス街" else s["area_type"]]
        o = int(s["open_time"][:2]) * 60 + int(s["open_time"][3:])
        c = int(s["close_time"][:2]) * 60 + int(s["close_time"][3:])
        if weekend and s["area_type"] == "オフィス街":
            o, c = 9 * 60, 18 * 60
        wmin = np.zeros(1440)
        for m in range(o, c - 5):
            wmin[m] = prof.get(m // 60, 0.25)
        return np.cumsum(wmin) / wmin.sum()

    # ------------------------------------------------------------------------------------------
    def store_orders(self):
        rng = self.rng
        cust = self.cust
        H, L = [], []
        member_idx = {}
        for s in config.STORES:
            m = (cust["home_store_id"] == s["store_id"]).to_numpy() & (cust["store_w"].to_numpy() > 0)
            member_idx[s["store_id"]] = np.where(m)[0]
        reg_i = cust["reg_i"].to_numpy()
        end_i = cust["end_i"].to_numpy()
        app_i = cust["app_i"].to_numpy()
        sw = cust["store_w"].to_numpy()
        cust_ids = cust["customer_id"].to_numpy()
        app_flag = cust["app_user"].to_numpy()
        for s in config.STORES:
            so = date.fromisoformat(s["open_date"])
            sc = date.fromisoformat(s["close_date"]) if s["close_date"] else None
            mins = {False: self._minute_dist(s, False), True: self._minute_dist(s, True)}
            midx = member_idx[s["store_id"]]
            eatin_p = 0.0 if s["seats"] == 0 else (0.30 if s["area_type"] == "オフィス街" else (0.45 if s["area_type"] == "観光地" else 0.36))
            lines_mu = 0.5 if s["area_type"] in ("オフィス街", "駅前") else (0.8 if s["area_type"] == "観光地" else 0.65)
            for d in self.days:
                if d < so or (sc and d > sc):
                    continue
                lam, w = self._store_lambda(s, d)
                if lam <= 0:
                    continue
                n = int(rng.poisson(lam * rng.lognormal(0, 0.10)))
                if n == 0:
                    continue
                di = self.didx[d]
                weekend = d.weekday() >= 5 or d in HOLIDAY_DATES
                mm = np.searchsorted(mins[weekend], rng.random(n))
                mm.sort()
                secs = rng.integers(0, 60, n)
                part = np.where(mm < 11 * 60, 0, np.where(mm < 14 * 60, 1, np.where(mm < 17 * 60, 2, 3)))
                # members
                yrs = (d - date(2024, 1, 1)).days / 365.25
                is_mem = rng.random(n) < (0.36 + 0.04 * yrs)
                act = midx[(reg_i[midx] <= di) & (end_i[midx] >= di)]
                cid = np.full(n, None, dtype=object)
                if len(act) and is_mem.any():
                    p = sw[act] / sw[act].sum()
                    pick = act[rng.choice(len(act), size=int(is_mem.sum()), p=p)]
                    cid[is_mem] = cust_ids[pick]
                    is_app = np.zeros(n, dtype=bool)
                    is_app[is_mem] = app_flag[pick] & (app_i[pick] <= di)
                else:
                    is_mem[:] = False
                    is_app = np.zeros(n, dtype=bool)
                eat = rng.random(n) < eatin_p
                # payment
                k = min(2, d.year - 2024)
                pay_p = np.array([[0.34, 0.27, 0.13, 0.06, 0.20], [0.29, 0.29, 0.13, 0.06, 0.23], [0.24, 0.31, 0.13, 0.06, 0.26]][k])
                if s["area_type"] == "観光地":
                    pay_p = pay_p + np.array([-0.04, 0.08, 0, 0, -0.04])
                pay = rng.choice(5, size=n, p=pay_p / pay_p.sum())
                nl = np.minimum(1 + rng.poisson(lines_mu, n), 7)
                o_idx = np.repeat(np.arange(n), nl)
                o_part = part[o_idx]
                eps = float(rng.normal(0, 0.07))
                prod = np.empty(len(o_idx), dtype=np.int64)
                for pt in range(4):
                    sel = o_part == pt
                    if sel.any():
                        cw = np.cumsum(self._store_weights(s, d, w, pt, eps))
                        prod[sel] = np.minimum(np.searchsorted(cw, rng.random(int(sel.sum()))), len(cw) - 1)
                # merge duplicates within order
                key = o_idx * 1000 + prod
                uk, inv = np.unique(key, return_inverse=True)
                q = _qty(rng, self.pcat[prod])
                qty = np.bincount(inv, weights=q).astype(np.int64)
                o_idx = uk // 1000
                prod = uk % 1000
                cat = self.pcat[prod]
                unit = self.price[prod, self.period(d)]
                disc = np.zeros(len(prod), dtype=np.int64)
                promo = np.full(n, None, dtype=object)
                coupon = np.full(n, None, dtype=object)
                if (d.month, d.day) == (10, 1):
                    m = cat == "コーヒー豆"
                    disc[m] = (unit[m] * qty[m] * 0.2).astype(np.int64)
                    promo[np.unique(o_idx[m])] = f"COFFEEDAY{d.year}"
                if d.month == 3 and d.day <= 10:
                    m = np.isin(cat, ["コーヒー豆", "ドリップバッグ"])
                    disc[m] = (unit[m] * qty[m] * 0.1).astype(np.int64)
                    promo[np.unique(o_idx[m])] = f"ANNIV{d.year}"
                if s["store_id"] == "S12" and date(2025, 12, 15) <= d <= date(2025, 12, 28):
                    m = np.isin(cat, ["コーヒー豆", "ドリップバッグ", "器具・グッズ"])
                    disc[m] = (unit[m] * qty[m] * 0.2).astype(np.int64)
                    promo[np.unique(o_idx[m])] = "CLOSING-S12"
                # app coupon: one drink line per receipt
                use_cp = is_app & (rng.random(n) < 0.35)
                drink_lines = np.where((cat == "ドリンク") & use_cp[o_idx] & (disc == 0))[0]
                if len(drink_lines):
                    first = drink_lines[np.unique(o_idx[drink_lines], return_index=True)[1]]
                    disc[first] = 50
                    coupon[o_idx[first]] = "APP50"
                    promo = np.where(pd.isna(promo) & (coupon == "APP50"), "APP50", promo)
                sub = unit * qty - disc
                food_eat = np.isin(cat, ["ドリンク", "焼き菓子"]) & eat[o_idx]
                rate = np.where((self.ptax[prod] == "goods") | food_eat, 0.10, 0.08)
                tax = np.floor(sub * rate).astype(np.int64)
                ymd = d.strftime("%y%m%d")
                oids = np.array([f"{s['store_id']}-{ymd}-{i + 1:04d}" for i in range(n)], dtype=object)
                ts = [datetime(d.year, d.month, d.day, int(m_ // 60), int(m_ % 60), int(sc_)) for m_, sc_ in zip(mm, secs)]
                H.append(pd.DataFrame(dict(order_id=oids, order_datetime=ts, channel="店舗", store_id=s["store_id"],
                                           customer_id=cid, device="店頭", eat_in=np.where(eat, "店内", "持ち帰り"),
                                           payment_method=np.array(STORE_PAY, dtype=object)[pay], coupon_code=coupon,
                                           promotion_code=promo)))
                L.append(pd.DataFrame(dict(order_id=oids[o_idx], product_idx=prod, quantity=qty, unit_price=unit,
                                           discount_amount=disc, line_subtotal=sub, tax_rate=rate, tax_amount=tax)))
            print(f"    store {s['store_id']} done", flush=True)
        return pd.concat(H, ignore_index=True), pd.concat(L, ignore_index=True)

    # ------------------------------------------------------------------------------------------
    def _ec_weights(self, d, band):
        di = self.didx[d]
        wt = self.pw_ec * self.avail[di]
        cat = self.pcat
        md = (d.month, d.day)
        gift_peak = (d.month == 6 and d.day >= 15) or d.month == 7 or (d.month == 11 and d.day >= 20) or (d.month == 12 and d.day <= 25)
        if gift_peak:
            wt = np.where(np.isin(self.pids, ["P080", "P081", "P082"]), wt * 2.5, wt)
        if d.month == 2 and d.day <= 14:
            wt = np.where(np.isin(self.pids, ["P080", "P081", "P082"]), wt * 1.5, wt)
            wt = np.where(self.pids == "P083", wt * (1 + d.day / 5), wt)
        tmax = self.w("tokyo", d)["temp_max_c"]
        wt = np.where(np.isin(self.pids, ["P073", "P074", "P017", "P085"]), wt * (1 + max(0.0, tmax - 25) / 5), wt)
        if md >= (10, 1) and md <= (10, 7):
            wt = np.where(cat == "コーヒー豆", wt * 2.0, wt)
        if date(2026, 6, 18) <= d <= date(2026, 6, 23):
            wt = np.where(cat == "ドリップバッグ", wt * 0.5, wt)
        if band == 1:
            wt = np.where(np.isin(cat, ["ドリップバッグ", "焼き菓子", "器具・グッズ"]), wt * 1.3, wt)
            wt = np.where(self.size500, wt * 0.7, wt)
        elif band == 3:
            wt = np.where(cat == "コーヒー豆", wt * 1.25, wt)
            wt = np.where(self.size500, wt * 1.4, wt)
        return np.cumsum(wt / wt.sum())

    def _ec_lambda(self, d):
        yrs = (d - date(2024, 1, 1)).days / 365.25
        lam = 50 * (1 + 0.22 * yrs)
        lam *= [1.08, 1.0, 0.98, 0.97, 0.95, 0.98, 1.06][d.weekday()]
        lam *= [1.05, 1.15, 1.0, 0.95, 1.05, 1.08, 1.2, 0.95, 0.95, 1.0, 1.1, 1.45][d.month - 1]
        md = (d.month, d.day)
        if d.month == 1 and d.day <= 5:
            lam *= 1.8 if d.day <= 2 else 1.4
        bf = {2024: date(2024, 11, 22), 2025: date(2025, 11, 21)}.get(d.year)
        if bf and bf <= d <= bf + timedelta(days=9):
            lam *= 2.4 if (d - bf).days < 2 else 1.7
        if md == (10, 1):
            lam *= 2.2
        elif (10, 2) <= md <= (10, 7):
            lam *= 1.4
        if d.month == 3 and d.day <= 10:
            lam *= 1.3
        if (d.month == 1 and d.day >= 20) or (d.month == 2 and d.day <= 10):
            lam *= 1.2
        if d.day == 25:
            lam *= 1.06
        w = self.w("tokyo", d)
        if w["precip_mm"] >= 10:
            lam *= 1.07
        prev = self.w("tokyo", d - timedelta(days=1)) if d > config.RETAIL_START else w
        if prev["precip_mm"] >= 100:
            lam *= 1.1
        return lam

    def _promo_ec(self, d):
        md = (d.month, d.day)
        if d.month == 1 and d.day <= 5:
            return f"NY{d.year}", None, 0.10
        bf = {2024: date(2024, 11, 22), 2025: date(2025, 11, 21)}.get(d.year)
        if bf and bf <= d <= bf + timedelta(days=9):
            return f"BF{d.year}", None, 0.15
        if (10, 1) <= md <= (10, 7):
            return f"COFFEEDAY{d.year}", ["コーヒー豆"], 0.20
        if d.month == 3 and d.day <= 10:
            return f"ANNIV{d.year}", ["コーヒー豆", "ドリップバッグ"], 0.10
        return None, None, 0

    def ec_orders(self):
        rng = self.rng
        cust = self.cust
        ecm = np.where(cust["ec_w"].to_numpy() > 0)[0]
        reg_i = cust["reg_i"].to_numpy()
        end_i = cust["end_i"].to_numpy()
        app_i = cust["app_i"].to_numpy()
        ew = cust["ec_w"].to_numpy()
        band = cust["age_band"].to_numpy()
        plat = cust["platform"].to_numpy()
        cust_ids = cust["customer_id"].to_numpy()
        prefs = cust["prefecture"].to_numpy()
        hour_cdf = np.cumsum(EC_HOUR / EC_HOUR.sum())
        H, L, failed = [], [], []
        for d in self.days:
            di = self.didx[d]
            n = int(rng.poisson(self._ec_lambda(d) * rng.lognormal(0, 0.08)))
            act = ecm[(reg_i[ecm] <= di) & (end_i[ecm] >= di)]
            if n == 0 or len(act) == 0:
                continue
            pick = act[rng.choice(len(act), size=n, p=ew[act] / ew[act].sum())]
            hrs = np.searchsorted(hour_cdf, rng.random(n))
            secs = rng.integers(0, 3600, n)
            order = np.argsort(hrs * 3600 + secs, kind="stable")
            pick, hrs, secs = pick[order], hrs[order], secs[order]
            is_app = (app_i[pick] <= di) & (rng.random(n) < 0.85)
            device = np.where(is_app, "アプリ", "Web")
            ts = np.array([datetime(d.year, d.month, d.day) + timedelta(seconds=int(h * 3600 + s_)) for h, s_ in zip(hrs, secs)])
            # Android 5.4.0 checkout bug: some app orders fail
            keep = np.ones(n, dtype=bool)
            adopt = config.ANDROID_540_ADOPTION.get(d, 0.0)
            if adopt:
                cand = is_app & (plat[pick] == "Android")
                fail = cand & (rng.random(n) < adopt * config.APP_BUG_FAIL_RATE)
                retry_web = fail & (rng.random(n) < 0.35)
                for i in np.where(fail)[0]:
                    failed.append(dict(customer_id=cust_ids[pick[i]], attempted_at=ts[i], retried_on_web=bool(retry_web[i]),
                                       platform="Android", app_version="5.4.0"))
                device = np.where(retry_web, "Web", device)
                ts = np.where(retry_web, ts + np.array([timedelta(minutes=int(x)) for x in rng.integers(5, 90, n)]), ts)
                keep = ~fail | retry_web
            pick, device, ts = pick[keep], device[keep], ts[keep]
            n = len(pick)
            if n == 0:
                continue
            order = np.argsort(ts, kind="stable")
            pick, device, ts = pick[order], device[order], ts[order]
            code, cats_on, rate_off = self._promo_ec(d)
            use_code = rng.random(n) < (0.8 if code else 0)
            nl = np.minimum(1 + rng.poisson(0.9, n), 8)
            o_idx = np.repeat(np.arange(n), nl)
            prod = np.empty(len(o_idx), dtype=np.int64)
            ob = band[pick][o_idx]
            for b in (1, 2, 3):
                sel = ob == b
                if sel.any():
                    cw = self._ec_weights(d, b)
                    prod[sel] = np.minimum(np.searchsorted(cw, rng.random(int(sel.sum()))), len(cw) - 1)
            key = o_idx * 1000 + prod
            uk, inv = np.unique(key, return_inverse=True)
            q = _qty(rng, self.pcat[prod])
            gift = self.pcat[prod] == "ギフト"
            q = np.where(gift & (rng.random(len(q)) < 0.25), q + rng.integers(1, 4, len(q)), q)
            qty = np.bincount(inv, weights=q).astype(np.int64)
            o_idx, prod = uk // 1000, uk % 1000
            cat = self.pcat[prod]
            unit = self.price[prod, self.period(d)]
            disc = np.zeros(len(prod), dtype=np.int64)
            if code:
                elig = use_code[o_idx] & (np.isin(cat, cats_on) if cats_on else True)
                disc = np.where(elig, (unit * qty * rate_off).astype(np.int64), 0)
            sub = unit * qty - disc
            rate = np.where(self.ptax[prod] == "goods", 0.10, 0.08)
            tax = np.floor(sub * rate).astype(np.int64)
            ymd = d.strftime("%y%m%d")
            oids = np.array([f"EC{ymd}-{i + 1:05d}" for i in range(n)], dtype=object)
            pay_p = np.array([0.58, 0.18, 0.11, 0.06, 0.07])
            pay = rng.choice(5, size=n, p=pay_p)
            pay = np.where((device == "アプリ") & (rng.random(n) < 0.15), 4, pay)
            used = np.zeros(n, dtype=bool)
            if code:
                used[np.unique(o_idx[disc > 0])] = True
            H.append(pd.DataFrame(dict(order_id=oids, order_datetime=ts, channel="オンラインストア", store_id="W01",
                                       customer_id=cust_ids[pick], device=device, eat_in=None,
                                       payment_method=np.array(EC_PAY, dtype=object)[pay],
                                       coupon_code=np.where(used, code, None), promotion_code=np.where(used, code, None),
                                       shipping_prefecture=prefs[pick])))
            L.append(pd.DataFrame(dict(order_id=oids[o_idx], product_idx=prod, quantity=qty, unit_price=unit,
                                       discount_amount=disc, line_subtotal=sub, tax_rate=rate, tax_amount=tax)))
        h = pd.concat(H, ignore_index=True)
        # gifts shipped elsewhere
        pref_names = [p[0] for p in config.PREFECTURES]
        pref_w = np.array([p[1] for p in config.PREFECTURES], dtype=float)
        mv = rng.random(len(h)) < 0.06
        h.loc[mv, "shipping_prefecture"] = rng.choice(pref_names, size=int(mv.sum()), p=pref_w / pref_w.sum())
        return h, pd.concat(L, ignore_index=True), pd.DataFrame(failed)

    # ------------------------------------------------------------------------------------------
    def subscriptions(self):
        rng = self.rng
        cust = self.cust
        ecm = np.where(cust["ec_w"].to_numpy() > 0)[0]
        reg_i = cust["reg_i"].to_numpy()
        end_i = cust["end_i"].to_numpy()
        cust_ids = cust["customer_id"].to_numpy()
        prefs = cust["prefecture"].to_numpy()
        subs = []
        taken = set()
        d = date(2024, 6, 1)
        while d <= config.DATA_END:
            yrs = (d - date(2024, 6, 1)).days / 365.25
            lam = 22 * (1 + 0.35 * yrs)
            if d <= date(2024, 7, 31):
                lam *= 2.5
            if date(2025, 10, 1) <= d <= date(2025, 11, 15):
                lam *= 1.4
            if date(2025, 4, 1) <= d <= date(2025, 5, 31):
                lam *= 0.6
            di = self.didx[d]
            act = ecm[(reg_i[ecm] <= di) & (end_i[ecm] >= di + 30)]
            for _ in range(int(rng.poisson(lam))):
                c = int(act[int(rng.integers(len(act)))])
                if c in taken:
                    continue
                taken.add(c)
                start = d + timedelta(days=int(rng.integers(0, 7)))
                if start > config.DATA_END:
                    continue
                opts = ["P100", "P101", "P102"] + (["P103"] if start >= date(2025, 10, 1) else [])
                pw = np.array([0.55, 0.2, 0.2] + ([0.15] if len(opts) == 4 else []))
                plan = str(rng.choice(opts, p=pw / pw.sum()))
                subs.append(dict(customer_idx=c, product_id=plan, start_date=start, billing_day=min(start.day, 28)))
            d += timedelta(days=7)
        rows_h, rows_l, sub_rows = [], [], []
        seq_by_day = {}
        for k, sb in enumerate(subs):
            c = sb["customer_idx"]
            pid = sb["product_id"]
            pi = self.pindex[pid]
            m_date = sb["start_date"]
            status, cancel, reason, skips = "継続中", None, None, 0
            first = True
            while m_date <= config.DATA_END:
                hz = 0.045
                if date(2025, 4, 1) <= m_date <= date(2025, 5, 31):
                    hz = 0.11
                if (m_date - sb["start_date"]).days > 0 and rng.random() < hz:
                    status, cancel = "解約", m_date - timedelta(days=int(rng.integers(3, 20)))
                    if date(2025, 3, 15) <= cancel <= date(2025, 6, 15) and rng.random() < 0.55:
                        reason = "値上げのため"
                    else:
                        reason = str(rng.choice(["飲みきれず在庫が余る", "他社サービスへ乗り換え", "味に飽きた", "生活環境の変化",
                                                 "経済的な理由", "店舗で購入するため", "その他"],
                                                p=[0.28, 0.12, 0.14, 0.14, 0.12, 0.08, 0.12]))
                    break
                if not first and rng.random() < 0.07:
                    skips += 1
                else:
                    seq_by_day[m_date] = seq_by_day.get(m_date, 0) + 1
                    oid = f"SB{m_date:%y%m%d}-{seq_by_day[m_date]:05d}"
                    ts = datetime(m_date.year, m_date.month, m_date.day, 6, 0) + timedelta(minutes=int(rng.integers(0, 60)))
                    unit = int(self.price[pi, self.period(m_date)])
                    disc = int(unit * 0.2) if first and m_date <= date(2024, 7, 31) else 0
                    sub_amt = unit - disc
                    tax = int(math.floor(sub_amt * 0.08))
                    rows_h.append(dict(order_id=oid, order_datetime=ts, channel="定期便", store_id="W01",
                                       customer_id=cust_ids[c], device="定期便", eat_in=None, payment_method="クレジットカード",
                                       coupon_code="SUB20" if disc else None, promotion_code="SUB20" if disc else None,
                                       shipping_prefecture=prefs[c]))
                    rows_l.append(dict(order_id=oid, product_idx=pi, quantity=1, unit_price=unit, discount_amount=disc,
                                       line_subtotal=sub_amt, tax_rate=0.08, tax_amount=tax))
                first = False
                y, mo = m_date.year + (m_date.month // 12), m_date.month % 12 + 1
                m_date = date(y, mo, sb["billing_day"])
            sub_rows.append(dict(subscription_id=f"SUB{k + 1:05d}", customer_id=cust_ids[c], product_id=pid,
                                 start_date=sb["start_date"], billing_day=sb["billing_day"], status=status,
                                 cancel_date=cancel, cancel_reason=reason, skip_count=skips))
        return pd.DataFrame(rows_h), pd.DataFrame(rows_l), pd.DataFrame(sub_rows)

    # ------------------------------------------------------------------------------------------
    def fulfil(self, h: pd.DataFrame, lines: pd.DataFrame):
        """Shipping fee, ship/delivery dates, delays, cancellations and returns for EC & subscription orders."""
        rng = self.rng
        region_of = {p[0]: p[2] for p in config.PREFECTURES}
        ec = h["channel"] != "店舗"
        agg = lines.groupby("order_id").agg(sub=("line_subtotal", "sum"), tax=("tax_amount", "sum"))
        h = h.join(agg, on="order_id")
        drip_ids = {self.pindex[p] for p in ("P020", "P021", "P022", "P023", "P024", "P025", "P081", "P102")}
        has_drip = set(lines.loc[lines["product_idx"].isin(drip_ids), "order_id"])
        ship, prom, deliv, status, ret, fee = [], [], [], [], [], []
        for r in h.itertuples():
            if r.channel == "店舗":
                ship.append(None), prom.append(None), deliv.append(None), status.append("完了"), ret.append(None), fee.append(0)
                continue
            d = r.order_datetime.date()
            incl = r.sub + r.tax
            if r.channel == "定期便":
                f = 0
            else:
                thr = 3000 if d < date(2025, 7, 1) else 4000
                base_fee = 550 if d < date(2025, 4, 1) else 600
                f = 0 if incl >= thr else base_fee
            fee.append(f)
            sd = d + timedelta(days=0 if r.order_datetime.hour < 13 else 1)
            while sd.weekday() == 6 or (sd.month == 1 and sd.day <= 3):
                sd += timedelta(days=1)
            reg = region_of.get(r.shipping_prefecture, "関東")
            transit = TRANSIT[reg]
            promised = sd + timedelta(days=transit)
            delay = 0
            bf = {2024: date(2024, 11, 22), 2025: date(2025, 11, 21)}.get(d.year)
            if bf and bf <= d <= bf + timedelta(days=4):
                delay += int(rng.integers(1, 3))
            if (d.month == 12 and 15 <= d.day <= 25) or (d.month == 7 and d.day <= 15):
                delay += int(rng.random() < 0.5)
            dc = self.w("chiba", sd)
            if dc["precip_mm"] >= 80 or dc["gust_max_ms"] >= 22:
                delay += int(rng.integers(1, 3))
            if r.order_id in has_drip and date(2026, 6, 18) <= d <= date(2026, 6, 23):
                sd2 = date(2026, 6, 22) + timedelta(days=int(rng.integers(0, 3)))
                delay += max(0, (sd2 - sd).days)
            sd = sd + timedelta(days=delay)
            dw = self.w(REGION_STATION[reg], min(sd + timedelta(days=transit), config.DATA_END))
            extra = 1 if (dw["precip_mm"] >= 80 or dw["gust_max_ms"] >= 20) else 0
            dd = sd + timedelta(days=transit + extra + int(rng.random() < 0.05))
            cancel_p = 0.022 + (0.15 if (r.order_id in has_drip and date(2026, 6, 18) <= d <= date(2026, 6, 23)) else 0)
            if r.channel != "定期便" and rng.random() < cancel_p:
                ship.append(None), prom.append(promised), deliv.append(None), status.append("キャンセル"), ret.append(None)
                continue
            ship.append(sd if sd <= config.DATA_END else None)
            prom.append(promised)
            deliv.append(dd if dd <= config.DATA_END else None)
            if rng.random() < 0.005 and dd + timedelta(days=5) <= config.DATA_END:
                status.append("返品")
                ret.append(dd + timedelta(days=int(rng.integers(2, 10))))
            else:
                status.append("完了" if dd <= config.DATA_END else "出荷済み" if sd <= config.DATA_END else "受付済み")
                ret.append(None)
        h["shipped_date"] = ship
        h["promised_delivery_date"] = prom
        h["delivered_date"] = deliv
        h["order_status"] = status
        h["returned_date"] = ret
        h["shipping_fee"] = fee
        return h.drop(columns=["sub", "tax"])

    def lot_issues(self, h: pd.DataFrame, lines: pd.DataFrame):
        """Orders that received over-roasted lots (RST-02 drift) -> complaints & returns."""
        rng = self.rng
        aff = self.mfg.affected_lots
        aff_by_p = {p: g.sort_values("production_date") for p, g in aff.groupby("product_id")}
        base_map = {"P100": "P002"}
        pidx = {self.pindex[p]: p for p in list(aff_by_p) + ["P100"]}
        cand = lines[lines["product_idx"].isin(pidx.keys())].merge(
            h[["order_id", "order_datetime", "channel", "customer_id", "store_id", "order_status", "delivered_date"]], on="order_id")
        cand = cand[(cand["order_datetime"] >= "2026-07-10") & (cand["order_datetime"] < "2026-08-16")]
        rows = []
        for r in cand.itertuples():
            pid = pidx[r.product_idx]
            base = base_map.get(pid, pid)
            g = aff_by_p.get(base)
            if g is None:
                continue
            od = r.order_datetime.date()
            recent = g[(g["production_date"] <= od - timedelta(days=2)) & (g["production_date"] >= od - timedelta(days=21))]
            if recent.empty or rng.random() > 0.5:
                continue
            p_c = 0.06 if r.channel != "店舗" else 0.035
            if pid in ("P007", "P011"):
                p_c *= 0.6
            if rng.random() > p_c:
                continue
            lot = recent.sample(1, random_state=int(rng.integers(1 << 30))).iloc[0]["lot_id"]
            base_d = r.delivered_date if isinstance(r.delivered_date, date) else od
            cdate = base_d + timedelta(days=int(rng.integers(1, 12)))
            returned = r.channel != "店舗" and r.order_status == "完了" and rng.random() < 0.55
            rows.append(dict(order_id=r.order_id, product_id=pid, customer_id=r.customer_id, store_id=r.store_id,
                             channel=r.channel, lot_id=lot, complaint_date=min(cdate, config.DATA_END), returned=returned))
        df = pd.DataFrame(rows)
        if len(df):
            ret = df[df["returned"]].drop_duplicates("order_id")
            m = h["order_id"].isin(ret["order_id"])
            rd = dict(zip(ret["order_id"], ret["complaint_date"]))
            h.loc[m, "order_status"] = "返品"
            h.loc[m, "returned_date"] = h.loc[m, "order_id"].map(rd)
        return df, h

    # ------------------------------------------------------------------------------------------
    def run(self, out_dir):
        print("  customers...", flush=True)
        self.customers()
        closures = self.closures()
        print("  store orders...", flush=True)
        sh, sl = self.store_orders()
        print("  ec orders...", flush=True)
        eh, el, failed = self.ec_orders()
        print("  subscriptions...", flush=True)
        bh, bl, subs = self.subscriptions()
        h = pd.concat([sh, eh, bh], ignore_index=True)
        h["order_datetime"] = pd.to_datetime(h["order_datetime"])
        lines = pd.concat([sl, el, bl], ignore_index=True)
        h = h.sort_values(["order_datetime", "order_id"], kind="stable").reset_index(drop=True)
        print("  fulfilment...", flush=True)
        h = self.fulfil(h, lines)
        lot_iss, h = self.lot_issues(h, lines)
        # line ids / totals
        lines["line_no"] = lines.groupby("order_id").cumcount() + 1
        lines["order_line_id"] = lines["order_id"] + "-" + lines["line_no"].astype(str).str.zfill(2)
        lines["product_id"] = self.pids[lines["product_idx"].to_numpy()]
        lines["line_total"] = lines["line_subtotal"] + lines["tax_amount"]
        agg = lines.groupby("order_id").agg(item_count=("quantity", "sum"), subtotal_excl_tax=("line_subtotal", "sum"),
                                            discount_total=("discount_amount", "sum"), tax_total=("tax_amount", "sum"))
        h = h.join(agg, on="order_id")
        h["total_incl_tax"] = h["subtotal_excl_tax"] + h["tax_total"] + h["shipping_fee"]
        self.write(out_dir, h, lines, subs, closures)
        cust = self.cust
        return RetailResult(self.stores_df, cust, h, lines, subs, closures, failed, lot_iss, self.products_out)

    def write(self, out_dir, h, lines, subs, closures):
        stores = pd.DataFrame(config.STORES + [config.EC_STORE])
        stores["store_type"] = np.where(stores["store_id"] == "W01", "EC", "直営店")
        stores["jma_station_name"] = stores["station"].map(lambda k: config.STATIONS[k]["name"])
        stores["jma_prec_no"] = stores["station"].map(lambda k: config.STATIONS[k]["prec_no"])
        stores["jma_block_no"] = stores["station"].map(lambda k: config.STATIONS[k]["block_no"])
        stores = stores.rename(columns={"seats": "seat_count", "floor_m2": "floor_area_m2", "lat": "latitude",
                                        "lon": "longitude"})
        stores.loc[stores["store_id"] == "W01", ["jma_station_name", "jma_prec_no", "jma_block_no"]] = None
        stores["jma_prec_no"] = stores["jma_prec_no"].astype("Int64")
        stores["jma_block_no"] = stores["jma_block_no"].astype("Int64")
        cols = ["store_id", "store_name", "store_type", "area_type", "prefecture", "city", "latitude", "longitude",
                "open_date", "close_date", "open_time", "close_time", "seat_count", "floor_area_m2",
                "jma_station_name", "jma_prec_no", "jma_block_no"]
        self.stores_df = stores[cols]
        write_csv(self.stores_df, out_dir / "stores.csv")
        pdf = self.pdf.copy()
        cur = self.price[:, 2]
        pdf["current_price"] = cur
        pdf["season"] = pdf["season"].map(lambda s: f"{s[0]}〜{s[1]}" if s else None)
        pdf["sales_channel"] = pdf["channel"].map({"store": "店舗のみ", "ec": "オンラインのみ", "both": "店舗・オンライン",
                                                   "sub": "定期便（オンライン）"})
        pdf["tax_category"] = pdf["tax_class"].map({"food": "軽減税率対象（飲食料品）", "goods": "標準税率"})
        pdf["unit_cost"] = (pdf["current_price"] * pdf["cost_rate"]).round(-1).astype(int)
        pdf["lot_managed"] = pdf["production_line"].notna()
        pdf = pdf.rename(columns={"list_price": "launch_price", "season": "sales_season", "temp_type": "serving_temp"})
        pdf["serving_temp"] = pdf["serving_temp"].map({"hot": "ホット", "iced": "アイス", "any": "ホット/アイス", "none": None})
        self.products_out = pdf[["product_id", "product_name", "category", "subcategory", "size", "sales_channel",
                                 "serving_temp", "launch_price", "current_price", "unit_cost", "tax_category",
                                 "launch_date", "end_date", "sales_season", "lot_managed"]]
        write_csv(self.products_out, out_dir / "products.csv")
        ph = self.price_hist.copy()
        write_csv(ph, out_dir / "product_price_history.csv")
        write_csv(prodmod.promotions(), out_dir / "promotions.csv")
        c = self.cust
        # member rank from last 12 months spend
        last12 = h[(h["order_datetime"] >= "2025-11-01") & h["customer_id"].notna() & (h["order_status"] != "キャンセル")]
        spend = last12.groupby("customer_id")["total_incl_tax"].sum()
        sp = c["customer_id"].map(spend).fillna(0)
        c["member_rank"] = np.select([sp >= 100000, sp >= 40000, sp >= 15000], ["プラチナ", "ゴールド", "シルバー"], "レギュラー")
        c["status"] = np.where(c["withdrawn_date"].notna(), "退会", "有効")
        cout = c[["customer_id", "registered_date", "registration_channel", "gender", "birth_year", "prefecture",
                  "home_store_id", "app_user", "mail_opt_in", "member_rank", "status", "withdrawn_date"]]
        write_csv(cout, out_dir / "customers.csv")
        sub = subs.copy()
        write_csv(sub, out_dir / "subscriptions.csv")
        write_csv(closures, out_dir / "store_closures.csv")
        hcols = ["order_id", "order_datetime", "channel", "store_id", "customer_id", "device", "eat_in",
                 "payment_method", "item_count", "subtotal_excl_tax", "discount_total", "tax_total", "shipping_fee",
                 "total_incl_tax", "coupon_code", "promotion_code", "order_status", "shipping_prefecture", "shipped_date",
                 "promised_delivery_date", "delivered_date", "returned_date"]
        lcols = ["order_line_id", "order_id", "line_no", "product_id", "quantity", "unit_price", "discount_amount",
                 "line_subtotal", "tax_rate", "tax_amount", "line_total"]
        hh = h[hcols].copy()
        hh["year"] = hh["order_datetime"].dt.year
        ll = lines[lcols].copy()
        yr_of = dict(zip(hh["order_id"], hh["year"]))
        ll["year"] = ll["order_id"].map(yr_of)
        for y in sorted(hh["year"].unique()):
            write_csv(hh[hh["year"] == y].drop(columns=["year"]), out_dir / "orders" / f"orders_{y}.csv")
            write_csv(ll[ll["year"] == y].drop(columns=["year"]), out_dir / "order_lines" / f"order_lines_{y}.csv")


def generate(out_dir, wx, mfg, seed) -> RetailResult:
    return Retail(wx, mfg, seed).run(out_dir)
