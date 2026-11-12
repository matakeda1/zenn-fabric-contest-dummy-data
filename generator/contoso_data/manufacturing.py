"""Manufacturing / IoT: equipment, 1-minute sensor readings, CMMS failure history, production lots."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

from . import config, people, weather
from .calendar_jp import HOLIDAY_DATES, daterange
from .io_utils import fmt_d, fmt_dt, write_csv

EQUIPMENT = [
    dict(equipment_id="RST-01", equipment_name="焙煎機 1号機", equipment_type="焙煎機", line="焙煎ライン",
         manufacturer="ファブリカム工機", model="FR-120", install_date="2018-04-10", rated_power_kw=15.0,
         fuel="都市ガス", criticality="A", pm_interval_days=90),
    dict(equipment_id="RST-02", equipment_name="焙煎機 2号機", equipment_type="焙煎機", line="焙煎ライン",
         manufacturer="ファブリカム工機", model="FR-120S", install_date="2021-09-01", rated_power_kw=15.0,
         fuel="都市ガス", criticality="A", pm_interval_days=90),
    dict(equipment_id="GRD-01", equipment_name="業務用グラインダー", equipment_type="グラインダー", line="粉砕ライン",
         manufacturer="リットウェア精機", model="LG-750", install_date="2019-03-15", rated_power_kw=22.0,
         fuel="電力", criticality="A", pm_interval_days=180),
    dict(equipment_id="PKG-01", equipment_name="充填包装機（豆）", equipment_type="包装機", line="包装ライン",
         manufacturer="ノースウィンド包装機械", model="NP-300", install_date="2017-07-20", rated_power_kw=7.5,
         fuel="電力・圧縮空気", criticality="B", pm_interval_days=60),
    dict(equipment_id="PKG-02", equipment_name="ドリップバッグ包装機", equipment_type="包装機", line="包装ライン",
         manufacturer="ノースウィンド包装機械", model="ND-60", install_date="2022-02-01", rated_power_kw=5.5,
         fuel="電力・圧縮空気", criticality="B", pm_interval_days=60),
    dict(equipment_id="OVN-01", equipment_name="トンネルオーブン", equipment_type="オーブン", line="製菓ライン",
         manufacturer="テイルスピン製作所", model="TS-1800", install_date="2020-11-05", rated_power_kw=12.0,
         fuel="都市ガス", criticality="A", pm_interval_days=120),
    dict(equipment_id="CMP-01", equipment_name="エアコンプレッサー", equipment_type="コンプレッサー", line="ユーティリティ",
         manufacturer="ウッドグローブ機工", model="WC-55", install_date="2016-05-30", rated_power_kw=55.0,
         fuel="電力", criticality="A", pm_interval_days=60),
    dict(equipment_id="CHL-01", equipment_name="チラー（冷却水）", equipment_type="チラー", line="ユーティリティ",
         manufacturer="ウッドグローブ機工", model="WR-40", install_date="2019-08-20", rated_power_kw=40.0,
         fuel="電力", criticality="B", pm_interval_days=180),
]

SENSOR_DEFS = [
    # equipment_type, column, meaning, unit, normal_min, normal_max, alarm
    ("焙煎機", "temperature_c", "排気温度", "℃", 165, 235, "245 以上"),
    ("焙煎機", "vibration_mm_s", "ドラム振動（速度RMS）", "mm/s", 0.8, 2.5, "4.5 以上"),
    ("焙煎機", "current_a", "ドラムモーター電流", "A", 6.5, 10.5, "12 以上"),
    ("焙煎機", "pressure_kpa", "ガス供給圧", "kPa", 1.9, 2.3, "1.6 以下"),
    ("焙煎機", "speed_rpm", "ドラム回転数", "rpm", 55, 61, "50 以下"),
    ("グラインダー", "temperature_c", "軸受温度", "℃", 30, 60, "70 以上"),
    ("グラインダー", "vibration_mm_s", "軸受振動（速度RMS）", "mm/s", 1.0, 2.8, "4.5 で注意 / 7.1 で危険"),
    ("グラインダー", "current_a", "モーター電流", "A", 25, 40, "45 以上"),
    ("グラインダー", "speed_rpm", "回転数", "rpm", 1440, 1490, "1400 以下"),
    ("包装機", "temperature_c", "シール温度", "℃", 158, 172, "155 以下"),
    ("包装機", "vibration_mm_s", "本体振動", "mm/s", 0.8, 3.0, "5.0 以上"),
    ("包装機", "current_a", "主モーター電流", "A", 3.5, 8.0, "9.5 以上"),
    ("包装機", "pressure_kpa", "供給エア圧", "kPa", 520, 650, "450 以下"),
    ("包装機", "speed_rpm", "包装サイクル数（回/分）", "回/分", 30, 70, "-"),
    ("オーブン", "temperature_c", "炉内温度", "℃", 178, 195, "170 以下 / 205 以上"),
    ("オーブン", "vibration_mm_s", "コンベア振動", "mm/s", 0.4, 2.0, "3.5 以上"),
    ("オーブン", "current_a", "コンベアモーター電流", "A", 3.0, 6.0, "7.5 以上"),
    ("オーブン", "pressure_kpa", "ガス供給圧", "kPa", 2.1, 2.6, "1.8 以下"),
    ("オーブン", "speed_rpm", "コンベア速度（m/分）", "m/分", 9.0, 11.0, "-"),
    ("コンプレッサー", "temperature_c", "吐出温度", "℃", 70, 98, "105 で警報 / 110 でトリップ"),
    ("コンプレッサー", "vibration_mm_s", "本体振動", "mm/s", 1.2, 3.5, "6.0 以上"),
    ("コンプレッサー", "current_a", "モーター電流（負荷/無負荷）", "A", 30, 95, "105 以上"),
    ("コンプレッサー", "pressure_kpa", "吐出圧力", "kPa", 650, 750, "600 以下"),
    ("コンプレッサー", "speed_rpm", "モーター回転数", "rpm", 2940, 2985, "-"),
    ("チラー", "temperature_c", "冷水出口温度", "℃", 6.5, 8.0, "10.0 以上"),
    ("チラー", "vibration_mm_s", "圧縮機振動", "mm/s", 1.0, 3.0, "5.0 以上"),
    ("チラー", "current_a", "圧縮機電流", "A", 25, 75, "85 以上"),
    ("チラー", "pressure_kpa", "高圧側冷媒圧力", "kPa", 1250, 2200, "1000 以下で低圧トリップ"),
]

# Factory calendar exceptions (2024-2026)
FACTORY_OFF = set()
for y in (2024, 2025, 2026):
    for md in ("04-29", "05-03", "05-04", "05-05", "05-06", "08-13", "08-14", "08-15", "08-16",
               "12-29", "12-30", "12-31", "01-01", "01-02", "01-03", "01-04"):
        FACTORY_OFF.add(date.fromisoformat(f"{y}-{md}"))
FACTORY_OFF |= {date(2026, 5, 2), date(2026, 9, 21), date(2026, 9, 22), date(2026, 9, 23)}
EXTRA_SATURDAYS = {date(2026, 6, 20): ["GRD-01", "PKG-02", "CMP-01"], date(2026, 7, 25): ["RST-01", "CMP-01", "CHL-01"]}


def is_factory_day(d: date) -> bool:
    if d in FACTORY_OFF:
        return False
    if d.weekday() == 6:
        return False
    if d.weekday() == 5:
        return d.month in (10, 11, 12)  # gift season Saturday shifts
    return True


@dataclass
class MfgResult:
    equipment: pd.DataFrame
    failures: pd.DataFrame
    lots: pd.DataFrame
    affected_lots: pd.DataFrame
    factory_30min: pd.DataFrame
    events: list
    drip_outage: tuple
    compressor_trip_day: date


def _blocks(day_windows, n_days, base_mod):
    """Build state array from per-day windows: list[(day_idx, start_min, end_min, state)]."""
    st = np.zeros(n_days * 1440, dtype=np.int8)
    for di, s, e, v in day_windows:
        st[di * 1440 + s: di * 1440 + e] = v
    return st


def _hm(s: str) -> int:
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def _lag(target, alpha_up, alpha_down, x0):
    out = np.empty_like(target)
    x = x0
    for i in range(len(target)):
        t = target[i]
        a = alpha_up if t > x else alpha_down
        x = x + (t - x) * a
        out[i] = x
    return out


def _block_pos(mask):
    """Minutes since start of each contiguous True block (0 for False)."""
    idx = np.arange(len(mask))
    starts = np.where(mask & ~np.concatenate([[False], mask[:-1]]), idx, 0)
    starts = np.maximum.accumulate(starts)
    return np.where(mask, idx - starts, 0)


def generate(out_dir, wx: pd.DataFrame, emp: pd.DataFrame, seed: int) -> MfgResult:
    rng = np.random.default_rng(seed)
    start, end = config.MFG_SENSOR_START, config.DATA_END
    days = list(daterange(start, end))
    nd = len(days)
    N = nd * 1440
    ts = pd.date_range(pd.Timestamp(start), periods=N, freq="1min")
    mod = np.tile(np.arange(1440), nd)
    day_idx = np.repeat(np.arange(nd), 1440)

    kum = weather.daily(wx, "kumagaya")
    amb = weather.subdaily_temperature(kum, 1, rng, start, end, noise=0.5).to_numpy()

    # Hottest production day in August -> compressor trip
    aug = kum.loc["2026-08-01":"2026-08-31"]
    aug = aug[[is_factory_day(d.date()) for d in aug.index]]
    trip_day = aug["temp_max_c"].idxmax().date()

    def windows(eq):
        w = []
        for di, d in enumerate(days):
            sat = d.weekday() == 5
            prod = is_factory_day(d)
            extra = EXTRA_SATURDAYS.get(d, [])
            if eq.startswith("RST"):
                if prod and not sat:
                    w += [(di, _hm("06:00"), _hm("06:30"), 1), (di, _hm("06:30"), _hm("12:00"), 2),
                          (di, _hm("12:00"), _hm("12:40"), 1), (di, _hm("12:40"), _hm("18:00"), 2),
                          (di, _hm("18:00"), _hm("18:30"), 1), (di, _hm("18:30"), _hm("21:30"), 2),
                          (di, _hm("21:30"), _hm("22:00"), 1)]
                elif (prod and sat) or eq in extra:
                    w += [(di, _hm("06:00"), _hm("06:30"), 1), (di, _hm("06:30"), _hm("14:30"), 2),
                          (di, _hm("14:30"), _hm("14:45"), 1)]
            elif eq == "GRD-01":
                if prod and not sat:
                    w += [(di, _hm("07:00"), _hm("11:30"), 2), (di, _hm("13:30"), _hm("17:30"), 2)]
                elif (prod and sat) or eq in extra:
                    w += [(di, _hm("07:00"), _hm("14:00"), 2)]
            elif eq.startswith("PKG"):
                if prod and not sat:
                    w += [(di, _hm("07:00"), _hm("12:00"), 2), (di, _hm("12:00"), _hm("12:40"), 1),
                          (di, _hm("12:40"), _hm("18:00"), 2), (di, _hm("18:00"), _hm("18:30"), 1),
                          (di, _hm("18:30"), _hm("21:00"), 2)]
                elif (prod and sat) or eq in extra:
                    w += [(di, _hm("07:00"), _hm("14:30"), 2)]
            elif eq == "OVN-01":
                if prod and not sat:
                    w += [(di, _hm("05:30"), _hm("06:15"), 1), (di, _hm("06:15"), _hm("12:00"), 2),
                          (di, _hm("12:00"), _hm("12:40"), 1), (di, _hm("12:40"), _hm("17:00"), 2),
                          (di, _hm("17:00"), _hm("17:20"), 1)]
                elif prod and sat:
                    w += [(di, _hm("05:30"), _hm("06:15"), 1), (di, _hm("06:15"), _hm("13:30"), 2)]
            elif eq == "CMP-01":
                if prod and not sat:
                    w += [(di, _hm("05:45"), _hm("22:15"), 2)]
                elif (prod and sat) or eq in extra:
                    w += [(di, _hm("05:45"), _hm("15:00"), 2)]
            elif eq == "CHL-01":
                if prod and not sat:
                    w += [(di, _hm("06:00"), _hm("22:00"), 2)]
                elif (prod and sat) or eq in extra:
                    w += [(di, _hm("06:00"), _hm("15:00"), 2)]
        return w

    def tidx(s: str) -> int:
        t = datetime.fromisoformat(s)
        return int((t - datetime.combine(start, datetime.min.time())).total_seconds() // 60)

    STOP, IDLE, RUN, FAULT, MAINT = 0, 1, 2, 3, 4
    states = {e["equipment_id"]: _blocks(windows(e["equipment_id"]), nd, mod) for e in EQUIPMENT}

    # ---- incidents inside the sensor window ---------------------------------------------------------
    grd_fail, grd_back = tidx("2026-06-18 10:42"), tidx("2026-06-19 12:40")
    rst_drift0, rst_fail, rst_back = tidx("2026-07-08 06:00"), tidx("2026-07-21 15:30"), tidx("2026-07-21 19:30")
    cmp_trip = tidx(f"{trip_day} 14:20")
    cmp_back = tidx(f"{trip_day} 16:25")
    pkg_fail, pkg_back = tidx("2026-09-24 14:10"), tidx("2026-09-24 17:05")
    chl_leak0, chl_fail, chl_back = tidx("2026-09-01 00:00"), tidx("2026-09-28 07:40"), tidx("2026-09-29 01:40")
    ovn_fail, ovn_back = tidx("2026-10-05 08:12"), tidx("2026-10-05 13:20")

    states["GRD-01"][grd_fail:grd_back] = FAULT
    pk2_stop0, pk2_stop1 = tidx("2026-06-18 12:45"), tidx("2026-06-19 14:00")
    s = states["PKG-02"][pk2_stop0:pk2_stop1]
    s[s > 0] = STOP
    states["RST-02"][rst_fail:rst_back] = MAINT
    states["CMP-01"][cmp_trip:cmp_back] = FAULT
    for eq in ("PKG-01", "PKG-02"):
        s = states[eq][cmp_trip + 4: cmp_back + 10]
        s[s > 0] = STOP
    states["PKG-01"][pkg_fail:pkg_back] = FAULT
    states["CHL-01"][chl_fail:chl_back] = FAULT
    s = states["OVN-01"][tidx("2026-09-28 08:00"): tidx("2026-09-28 17:20")]
    s[s > 0] = STOP
    states["OVN-01"][ovn_fail:ovn_back] = FAULT
    maint = [("RST-01", "2026-06-13 08:00", "2026-06-13 12:00"), ("CMP-01", "2026-07-11 09:00", "2026-07-11 11:00"),
             ("CHL-01", "2026-05-16 09:00", "2026-05-16 13:00"), ("OVN-01", "2026-08-22 09:00", "2026-08-22 14:00"),
             ("GRD-01", "2026-09-12 09:00", "2026-09-12 11:00"), ("PKG-02", "2026-08-17 06:00", "2026-08-17 09:00")]
    for eq, a, b in maint:
        states[eq][tidx(a):tidx(b)] = MAINT

    # micro stops (チョコ停) on packers
    for eq in ("PKG-01", "PKG-02"):
        st = states[eq]
        for di, d in enumerate(days):
            base_n = 3.5
            if eq == "PKG-01" and date(2026, 9, 1) <= d < date(2026, 9, 24):
                base_n += 1 + 9 * ((d - date(2026, 9, 1)).days / 23)
            for _ in range(rng.poisson(base_n)):
                m = di * 1440 + int(rng.integers(_hm("07:30"), _hm("20:30")))
                ln = int(rng.integers(2, 9))
                seg = st[m:m + ln]
                if (seg == RUN).all():
                    st[m:m + ln] = IDLE

    # ---- signals ---------------------------------------------------------------------------------
    frames = []
    factory_load = {}
    indoor = amb + 3.0
    for e in EQUIPMENT:
        eq = e["equipment_id"]
        st = states[eq]
        run = st == RUN
        idle = st == IDLE
        on = run | idle
        n = lambda sd: rng.normal(0, sd, N)  # noqa: E731
        temp = np.full(N, np.nan)
        vib = np.full(N, np.nan)
        cur = np.full(N, np.nan)
        prs = np.full(N, np.nan)
        spd = np.full(N, np.nan)
        if eq.startswith("RST"):
            pos = _block_pos(run)
            ph = pos % 20
            prof = np.where(ph < 14, 168 + 60 * (ph / 14) ** 0.8, np.where(ph < 16, 172, 172 + 3.5 * (ph - 16)))
            target = np.where(run, prof, np.where(idle, 188, indoor))
            if eq == "RST-02":
                target = target + np.where(run, 2.5, 0)
                drift = (np.arange(N) >= rst_drift0) & (np.arange(N) < rst_fail)
                prog = np.clip((np.arange(N) - rst_drift0) / max(rst_fail - rst_drift0, 1), 0, 1)
                target = target + np.where(drift & run, (5 + 11 * prog) * np.where(ph < 14, ph / 14, 0.4), 0)
            temp = _lag(target, 0.45, 0.012, indoor[0]) + n(0.9)
            if eq == "RST-02":
                drift = (np.arange(N) >= rst_drift0) & (np.arange(N) < rst_fail)
                temp = temp + np.where(drift & run, n(1.6), 0)
            vib = np.where(run, 1.45 + n(0.18), np.where(idle, 1.15 + n(0.12), 0.05 + np.abs(n(0.02))))
            cur = np.where(run, 8.6 + n(0.3), np.where(idle, 7.8 + n(0.25), 0.0))
            prs = 2.08 + n(0.035) - np.where(run & (ph == 0), 0.12, 0)
            spd = np.where(on, 58 + n(0.4), 0.0)
            gas_m3_min = np.where(run, np.where(ph < 14, 0.42, 0.08), np.where(idle, 0.18, 0.0))
            factory_load[eq] = dict(elec_kw=np.where(on, 13.0, 0.3), gas_m3=gas_m3_min)
        elif eq == "GRD-01":
            t = np.arange(N)
            wear0 = tidx("2026-06-01 00:00")
            wear = np.clip((t - wear0) / (grd_fail - wear0), 0, 1)
            wear = np.where(t < grd_fail, wear, 0)
            vib_h = 1.75 + n(0.22)
            vib = np.where(run, vib_h * (1 + 3.6 * wear ** 2.2) + np.where(wear > 0.6, np.abs(n(0.6)) * wear, 0),
                           0.06 + np.abs(n(0.02)))
            after = t >= grd_back
            vib = np.where(run & after, 1.55 + n(0.18), vib)
            target = np.where(run, indoor + 17 + 14 * wear ** 2, indoor)
            temp = _lag(target, 0.03, 0.01, indoor[0]) + n(0.3)
            cur = np.where(run, 32 + 1.5 * wear + n(1.6), 0.0)
            spd = np.where(run, 1468 + n(2.5) - 6 * wear, 0.0)
            factory_load[eq] = dict(elec_kw=np.where(run, 19.0, 0.2), gas_m3=np.zeros(N))
        elif eq.startswith("PKG"):
            setp = 165.0
            target = np.where(run, setp, np.where(idle, setp - 4, indoor))
            if eq == "PKG-01":
                t = np.arange(N)
                deg = (t >= tidx("2026-09-01 00:00")) & (t < pkg_fail)
                prog = np.clip((t - tidx("2026-09-01 00:00")) / (pkg_fail - tidx("2026-09-01 00:00")), 0, 1)
                dips = deg & (rng.random(N) < 0.004 + 0.02 * prog)
                dip_mask = np.convolve(dips.astype(int), np.ones(6, dtype=int), mode="same") > 0
                target = target - np.where(dip_mask & on, 9 + 6 * rng.random(N), 0)
            temp = _lag(target, 0.25, 0.02, indoor[0]) + n(0.8)
            vib = np.where(run, 1.9 + n(0.25), np.where(idle, 0.9 + n(0.1), 0.05 + np.abs(n(0.02))))
            cur = np.where(run, (6.2 if eq == "PKG-01" else 4.8) + n(0.3), np.where(idle, 2.1 + n(0.1), 0.0))
            spd = np.where(run, (38 if eq == "PKG-01" else 62) + n(1.8), 0.0)
            # compressed-air supply pressure follows the compressor (drops when CMP-01 stops or trips)
            air = np.where(states["CMP-01"] == RUN, 592.0, 0.0)
            prs = np.clip(_lag(air, 0.5, 0.12, 0.0) + np.where(air > 0, n(6), np.abs(n(1.0))), 0, None)
            factory_load[eq] = dict(elec_kw=np.where(run, e["rated_power_kw"] * 0.8, np.where(idle, 1.5, 0.15)),
                                    gas_m3=np.zeros(N))
        elif eq == "OVN-01":
            target = np.where(run, 186, np.where(idle, 186, indoor))
            target = np.where(st == FAULT, indoor, target)
            temp = _lag(target, 0.06, 0.008, indoor[0]) + n(1.0)
            vib = np.where(on, 1.0 + n(0.15), 0.05 + np.abs(n(0.02)))
            cur = np.where(on, 4.6 + n(0.2), 0.0)
            prs = np.where(on, 2.32 + n(0.04), 2.40 + n(0.02))
            spd = np.where(run, 10.0 + n(0.15), 0.0)
            factory_load[eq] = dict(elec_kw=np.where(on, 10.0, 0.3), gas_m3=np.where(run, 0.30, np.where(idle, 0.45, 0)))
        elif eq == "CMP-01":
            on_c = run
            cyc = _block_pos(on_c) % 26
            loading = on_c & (cyc < 11)
            prs_t = np.where(on_c, np.where(cyc < 11, 660 + 8 * cyc, 748 - 4.5 * (cyc - 11)), 0)
            prs = np.where(on_c, prs_t + n(3), np.nan)
            # pressure decays to ~0 when stopped
            prs = np.where(on_c, prs, 0.0)
            prs = _lag(prs, 0.6, 0.08, 0.0) + np.where(on_c, 0, np.abs(n(1.0)))
            heat = 6.0 * loading
            t_idx = np.arange(N)
            t0 = tidx(f"{trip_day} 11:30")
            trip_mask = (t_idx >= t0) & (t_idx < cmp_trip)
            need = max(0.0, 117.0 - (79 + 0.62 * (amb[cmp_trip] - 25) + 6.0))
            hot = np.where(trip_mask, need * np.clip((t_idx - t0) / (cmp_trip - t0), 0, 1) ** 1.5, 0)
            target = np.where(on_c, 79 + 0.62 * (amb - 25) + heat + hot, indoor)
            temp = _lag(target, 0.12, 0.02, indoor[0]) + n(0.6)
            cur = np.where(on_c, np.where(loading, 84 + n(2.5), 36 + n(1.5)), 0.0)
            vib = np.where(on_c, 2.2 + n(0.25), 0.06 + np.abs(n(0.02)))
            spd = np.where(on_c, np.where(loading, 2968 + n(4), 2981 + n(2)), 0.0)
            factory_load[eq] = dict(elec_kw=np.where(on_c, np.where(loading, 55.0, 22.0), 0.0), gas_m3=np.zeros(N))
            states[eq] = st
        elif eq == "CHL-01":
            t = np.arange(N)
            leak = np.clip((t - chl_leak0) / (chl_fail - chl_leak0), 0, 1) * ((t >= chl_leak0) & (t < chl_fail))
            target = np.where(run, 7.0 + 3.4 * leak ** 1.5, indoor - 2)
            temp = _lag(target, 0.05, 0.03, 15.0) + n(0.15)
            cur = np.where(run, 24 + 1.55 * np.clip(amb - 12, 0, None) * (1 + 0.18 * leak) + n(1.5), 0.0)
            prs = np.where(run, (1180 + 30 * amb) * (1 - 0.24 * leak) + n(15), 820 + 12 * amb + n(5))
            vib = np.where(run, 1.7 + n(0.2), 0.05 + np.abs(n(0.02)))
            factory_load[eq] = dict(elec_kw=np.where(run, 0.75 * cur, 0.4), gas_m3=np.zeros(N))
        status = np.array(["STOP", "IDLE", "RUN", "FAULT", "MAINT"])[st]
        df = pd.DataFrame(dict(timestamp=ts, equipment_id=eq, status=status, temperature_c=np.round(temp, 1),
                               vibration_mm_s=np.round(np.clip(vib, 0, None), 2), current_a=np.round(np.clip(cur, 0, None), 1),
                               pressure_kpa=np.round(prs, 2 if eq.startswith("RST") or eq == "OVN-01" else 0) if not np.isnan(prs).all() else np.nan,
                               speed_rpm=np.round(np.clip(spd, 0, None), 1) if not np.isnan(spd).all() else np.nan))
        frames.append(df)

    sensors = pd.concat(frames, ignore_index=True)
    # ---- data quality issues ---------------------------------------------------------------------------
    gaps = [("2026-06-03 02:10", "2026-06-03 04:40"), ("2026-08-27 13:05", "2026-08-27 13:50"),
            ("2026-10-19 21:40", "2026-10-19 22:05")]
    drop = np.zeros(len(sensors), dtype=bool)
    for a, b in gaps:
        drop |= (sensors["timestamp"] >= a) & (sensors["timestamp"] < b)
    m = (sensors["equipment_id"] == "OVN-01") & (sensors["timestamp"] >= "2026-07-14 10:00") & (sensors["timestamp"] < "2026-07-14 10:20")
    sensors.loc[m, ["temperature_c", "vibration_mm_s", "current_a", "pressure_kpa", "speed_rpm"]] = np.nan
    m = (sensors["equipment_id"] == "RST-01") & (sensors["timestamp"] >= "2026-08-20 09:00") & (sensors["timestamp"] < "2026-08-20 12:00")
    sensors.loc[m, "temperature_c"] = 203.4
    spike_idx = rng.choice(np.where(sensors["status"].to_numpy() == "RUN")[0], 30, replace=False)
    for k, i in enumerate(spike_idx):
        col = ["temperature_c", "vibration_mm_s", "current_a"][k % 3]
        val = {"temperature_c": 999.9, "vibration_mm_s": float(rng.uniform(30, 80)), "current_a": -1.0}[col]
        sensors.iat[i, sensors.columns.get_loc(col)] = val
    sensors = sensors[~drop]
    dup = sensors.sample(160, random_state=int(rng.integers(1 << 30)))
    sensors = pd.concat([sensors, dup]).sort_values(["timestamp", "equipment_id"], kind="stable").reset_index(drop=True)

    sdir = out_dir / "sensor_readings"
    sensors["ym"] = sensors["timestamp"].dt.strftime("%Y-%m")
    for ym, g in sensors.groupby("ym"):
        g = g.drop(columns=["ym"]).copy()
        g["timestamp"] = g["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
        write_csv(g, sdir / f"sensor_readings_{ym}.csv")

    # factory load per 30 min (for the energy dataset)
    slot = ts.floor("30min")
    elec = sum(v["elec_kw"] for v in factory_load.values()) / 60.0  # kWh per minute
    gas = sum(v["gas_m3"] for v in factory_load.values())
    f30 = pd.DataFrame({"slot": slot, "elec_kwh": elec, "gas_m3": gas}).groupby("slot").sum().reset_index()

    # ---- CMMS failure history -------------------------------------------------------------------------
    techs = emp[emp["department_id"] == "D401"]

    def tech_on(d):
        a = people.active_on(techs, d)
        return a.sample(1, random_state=int(rng.integers(1 << 30)))["employee_id"].iloc[0] if len(a) else None

    def at(s):
        return datetime.fromisoformat(s)

    rec = []

    def add(eq, etype, occ, rec_end, detected, mode, symptom, cause, action, parts, cost, impact=""):
        rec.append(dict(equipment_id=eq, event_type=etype, occurred_at=occ, recovered_at=rec_end,
                        downtime_minutes=int((rec_end - occ).total_seconds() // 60), detected_by=detected,
                        failure_mode=mode, symptom=symptom, root_cause=cause, action_taken=action,
                        parts_replaced=parts, repair_cost_jpy=cost, production_impact=impact,
                        technician_employee_id=tech_on(occ.date())))

    add("GRD-01", "故障", at("2026-06-18 10:42"), at("2026-06-19 12:40"), "オペレーター", "軸受焼付き",
        "運転中に異音と焦げ臭いにおいが発生し、過負荷で停止した。",
        "主軸受の潤滑不足による摩耗の進行。振動値は 6 月上旬から上昇していたが、アラーム閾値が未設定だった。",
        "主軸受とシールを交換し、グリス給脂周期を 3 か月から 1 か月に短縮した。振動アラーム（4.5 mm/s）を設定。",
        "主軸受×2、オイルシール×2", 486000, "ドリップバッグ包装（PKG-02）が約 25 時間停止。ドリップバッグ商品の出荷が遅延。")
    add("RST-02", "故障", at("2026-07-21 15:30"), at("2026-07-21 19:30"), "品質検査（苦情調査）", "温度制御異常",
        "顧客から「焦げ臭い」「苦すぎる」との苦情が続き、品質保証部の調査で焙煎度が規格より深いロットを確認。",
        "排気温度センサー（熱電対）の劣化により実温度より低く表示され、制御が過加熱側にずれていた。7/8 頃から発生。",
        "熱電対を交換し温度校正を実施。7/8〜7/21 に 2 号機で焙煎したロットを出荷停止・交換対象とした。",
        "熱電対（K型）×1", 128000, "対象ロットの自主交換対応。7/25（土）に 1 号機で代替生産。")
    add("CMP-01", "故障", datetime.combine(trip_day, datetime.min.time()) + timedelta(hours=14, minutes=20),
        datetime.combine(trip_day, datetime.min.time()) + timedelta(hours=16, minutes=25), "センサー監視", "過熱停止",
        "吐出温度が 110℃ を超えトリップ。工場内のエア供給が停止した。",
        "猛暑による吸込空気温度の上昇と、アフタークーラーのフィン汚れによる冷却能力低下。",
        "アフタークーラーを清掃し、コンプレッサー室に換気扇を増設。",
        "なし（清掃）", 95000, "包装機 2 台が約 2 時間停止。")
    add("PKG-01", "故障", at("2026-09-24 14:10"), at("2026-09-24 17:05"), "オペレーター", "シール不良",
        "シール温度が不安定になり、袋の接着不良とチョコ停が増加。最終的にヒーター断線で停止。",
        "シールヒーター素線の経年劣化（9 月初旬から温度低下が断続的に発生）。",
        "シールヒーターと温度調節器を交換。", "シールヒーター×2、温度調節器×1", 214000, "豆の袋詰めが約 3 時間停止。")
    add("CHL-01", "故障", at("2026-09-28 07:40"), at("2026-09-29 01:40"), "センサー監視", "冷媒漏れ",
        "低圧トリップで停止。冷水出口温度が 9 月初旬から徐々に上昇していた。",
        "配管ろう付け部のピンホールによる冷媒漏れ。",
        "漏れ箇所を補修し冷媒を補充。", "冷媒 R410A 8kg", 352000, "製菓ラインの冷却工程が使えず、9/28 の製菓ラインを終日停止。")
    add("OVN-01", "故障", at("2026-10-05 08:12"), at("2026-10-05 13:20"), "オペレーター", "着火不良",
        "バーナーが失火し、炉内温度が低下。再着火できず停止。", "イグナイター電極の摩耗。",
        "イグナイターを交換。", "イグナイター×1", 76000, "焼き菓子の生産を約 5 時間停止。")
    for eq, a, b in maint:
        add(eq, "予防保全", at(a), at(b), "定期点検", "定期整備", "計画停止による定期整備。", "-",
            "点検・清掃・消耗品交換を実施。", "消耗品一式", int(rng.integers(30, 160)) * 1000)

    # earlier history (2025-01 .. 2026-04)
    modes = {
        "焙煎機": [("バーナー着火不良", "着火ミスが続き停止", "点火プラグの摩耗", "点火プラグ交換"),
                ("排気ファン異常", "排気ファンから異音", "ファンベルトの緩み", "ベルト調整・交換"),
                ("温度制御異常", "排気温度が安定しない", "熱電対の接触不良", "端子の締め直し")],
        "グラインダー": [("刃の摩耗", "粒度が粗くなった", "グラインド刃の摩耗", "刃の交換"),
                    ("軸受摩耗", "振動・異音", "軸受の摩耗", "軸受交換")],
        "包装機": [("シール不良", "接着不良が多発", "シールバーの汚れ", "清掃・調整"),
                ("フィルム搬送異常", "フィルムが蛇行", "ガイドローラーの摩耗", "ローラー交換"),
                ("計量異常", "充填量のばらつき", "ロードセルのずれ", "校正")],
        "オーブン": [("着火不良", "失火", "イグナイター不良", "イグナイター交換"),
                 ("コンベア停止", "コンベアが停止", "チェーンの伸び", "チェーン調整")],
        "コンプレッサー": [("過熱停止", "吐出温度高でトリップ", "クーラー汚れ", "清掃"),
                    ("圧力低下", "吐出圧が上がらない", "吸込フィルター目詰まり", "フィルター交換")],
        "チラー": [("高圧カット", "高圧異常で停止", "凝縮器の汚れ", "凝縮器洗浄")],
    }
    rate = {"焙煎機": 3.0, "グラインダー": 2.0, "包装機": 4.0, "オーブン": 2.0, "コンプレッサー": 2.0, "チラー": 1.5}
    for e in EQUIPMENT:
        d = config.MFG_HISTORY_START
        while d < config.MFG_SENSOR_START:
            hz = rate[e["equipment_type"]] / 365
            if e["equipment_type"] in ("コンプレッサー", "チラー") and d.month in (7, 8):
                hz *= 3
            if rng.random() < hz and is_factory_day(d) and d.weekday() < 5:
                mode, sym, cause, act = modes[e["equipment_type"]][int(rng.integers(len(modes[e["equipment_type"]])))]
                occ = datetime.combine(d, datetime.min.time()) + timedelta(minutes=int(rng.integers(_hm("06:30"), _hm("20:30"))))
                dt = int(np.clip(rng.lognormal(np.log(150), 0.8), 20, 1800))
                add(e["equipment_id"], "故障", occ, occ + timedelta(minutes=dt),
                    str(rng.choice(["オペレーター", "センサー監視", "定期点検"], p=[0.6, 0.25, 0.15])), mode, sym + "。",
                    cause + "。", act + "。", "-" if "清掃" in act or "調整" in act else "交換部品あり",
                    int(np.clip(rng.lognormal(np.log(80000), 0.7), 10000, 900000)) // 1000 * 1000)
            d += timedelta(days=1)
        d = config.MFG_HISTORY_START + timedelta(days=int(rng.integers(5, 30)))
        while d < config.MFG_SENSOR_START:
            sat = d + timedelta(days=(5 - d.weekday()) % 7)
            occ = datetime.combine(sat, datetime.min.time()) + timedelta(hours=9)
            add(e["equipment_id"], "予防保全", occ, occ + timedelta(minutes=int(rng.integers(90, 300))), "定期点検",
                "定期整備", "計画停止による定期整備。", "-", "点検・清掃・消耗品交換を実施。", "消耗品一式",
                int(rng.integers(30, 160)) * 1000)
            d += timedelta(days=e["pm_interval_days"])
    fail = pd.DataFrame(rec).sort_values("occurred_at").reset_index(drop=True)
    fail.insert(0, "work_order_id", [f"WO-{t.year}-{i + 1:04d}" for i, t in enumerate(fail["occurred_at"])])

    # ---- production lots ---------------------------------------------------------------------------------
    lots, affected = _lots(rng, emp)

    events = [dict(date=r.occurred_at.date(), end=r.recovered_at, equipment_id=r.equipment_id, event_type=r.event_type,
                   technician=r.technician_employee_id, downtime=r.downtime_minutes) for r in fail.itertuples()]

    eqdf = pd.DataFrame(EQUIPMENT)
    eqdf.insert(4, "site_id", "F01")
    write_csv(eqdf, out_dir / "equipment.csv")
    sd = pd.DataFrame(SENSOR_DEFS, columns=["equipment_type", "column_name", "measurement", "unit", "normal_min",
                                             "normal_max", "alarm_rule"])
    sd["note"] = ""
    write_csv(sd, out_dir / "sensor_definitions.csv")
    f_out = fail.copy()
    f_out["occurred_at"] = fmt_dt(f_out["occurred_at"])
    f_out["recovered_at"] = fmt_dt(f_out["recovered_at"])
    write_csv(f_out, out_dir / "failure_history.csv")
    l_out = lots.copy()
    for c in ("production_date", "best_before_date"):
        l_out[c] = fmt_d(l_out[c])
    write_csv(l_out, out_dir / "production_lots.csv")
    return MfgResult(eqdf, fail, lots, affected, f30, events, (datetime(2026, 6, 18, 10, 42), datetime(2026, 6, 19, 14, 0)),
                     trip_day)


AGTRON = {"P001": 55, "P002": 55, "P003": 60, "P004": 40, "P005": 40, "P006": 52, "P007": 68, "P008": 64, "P009": 58,
          "P010": 60, "P011": 56, "P012": 45, "P013": 62, "P014": 58, "P015": 70, "P016": 62, "P017": 42, "P018": 54,
          "P019": 48}


def _lots(rng, emp):
    from .products import P, available

    prod = {p["product_id"]: p for p in P}
    beans = [p for p in AGTRON]
    drips = ["P020", "P021", "P022", "P023", "P024", "P025"]
    sweets = ["P050", "P051", "P052", "P053", "P054", "P055", "P056", "P057", "P059"]
    freq = {"P001": 1.0, "P002": 1.0, "P003": 0.6, "P004": 1.0, "P005": 0.4, "P006": 0.6, "P015": 0.2,
            "P020": 1.0, "P021": 1.0, "P022": 0.4, "P023": 0.4, "P024": 0.4, "P025": 0.4,
            "P050": 1.0, "P051": 1.0, "P052": 1.0, "P053": 1.0, "P054": 0.6, "P055": 0.4, "P056": 0.6, "P057": 0.4,
            "P059": 0.4}
    qa = emp[emp["department_id"] == "D402"]
    rows = []
    for d in daterange(config.LOTS_START, config.DATA_END):
        if not is_factory_day(d) and d not in EXTRA_SATURDAYS:
            continue
        if d in EXTRA_SATURDAYS and d == date(2026, 6, 20):
            todays = [("P020", "PKG-02"), ("P021", "PKG-02"), ("P022", "PKG-02")]
        elif d in EXTRA_SATURDAYS:
            todays = [("P001", "RST-01"), ("P002", "RST-01"), ("P004", "RST-01")]
        else:
            todays = []
            rr = 0
            for pid in beans:
                if available(prod[pid], d) and rng.random() < freq.get(pid, 0.35 if prod[pid]["subcategory"] == "シングルオリジン" else 0.9):
                    eq = "RST-02" if (pid in ("P001", "P002", "P004", "P017") and rng.random() < 0.55) else ("RST-01" if rr % 2 == 0 else "RST-02")
                    rr += 1
                    todays.append((pid, eq))
            if not (date(2026, 6, 18) <= d <= date(2026, 6, 19)):
                todays += [(pid, "PKG-02") for pid in drips if available(prod[pid], d) and rng.random() < freq[pid]]
            if d != date(2026, 9, 28):
                todays += [(pid, "OVN-01") for pid in sweets if available(prod[pid], d)
                           and rng.random() < freq[pid] * (1.6 if pid == "P057" and d.month in (1, 2) else 1)]
            if d.month in (6, 7, 11, 12, 1, 2) and d.weekday() == 2:
                todays += [("P080", "PKG-01"), ("P081", "PKG-02")]
        seq = {}
        aq = people.active_on(qa, d)
        for pid, eq in todays:
            seq[eq] = seq.get(eq, 0) + 1
            code = {"RST-01": "R1", "RST-02": "R2", "PKG-02": "D", "OVN-01": "O", "PKG-01": "P"}[eq]
            p = prod[pid]
            if p["category"] in ("コーヒー豆",):
                qty = int(rng.integers(150, 420) if p["size"] == "200g" else rng.integers(60, 160))
            elif p["category"] in ("ドリップバッグ", "ギフト"):
                qty = int(rng.integers(200, 700))
            else:
                qty = int(rng.integers(180, 620))
            agt = mo = smin = smax = None
            drift = eq == "RST-02" and date(2026, 7, 8) <= d <= date(2026, 7, 21)
            if pid in AGTRON:
                smin, smax = AGTRON[pid] - 4, AGTRON[pid] + 4
                if rng.random() < 0.6 or drift and rng.random() < 0.4:
                    agt = round(AGTRON[pid] + rng.normal(0, 1.6) - (rng.uniform(7, 11) if drift else 0), 1)
                mo = round(rng.normal(1.1, 0.12) if drift else rng.normal(1.85, 0.25), 2)
            defect = int(rng.binomial(qty, 0.004 if not drift else 0.006))
            qc = "合格"
            if agt is not None and (agt < smin - 3 or agt > smax + 3) and not drift:
                qc = "条件付き合格"
            if rng.random() < 0.003:
                qc = "不合格"
            hold = "出荷可" if qc != "不合格" else "廃棄"
            if drift:
                hold = "回収・交換対象"
            shelf = 365 if p["category"] in ("コーヒー豆", "ドリップバッグ", "ギフト") else (45 if pid != "P056" else 10)
            insp = aq.sample(1, random_state=int(rng.integers(1 << 30)))["employee_id"].iloc[0] if len(aq) else None
            rows.append(dict(lot_id=f"L{d:%y%m%d}-{code}-{seq[eq]:02d}", product_id=pid, production_date=d, equipment_id=eq,
                             shift="早番" if seq[eq] <= 4 else "遅番", produced_qty=qty, defect_qty=defect, qc_result=qc,
                             roast_color_agtron=agt, roast_spec_min=smin, roast_spec_max=smax, moisture_pct=mo,
                             best_before_date=d + timedelta(days=shelf), hold_status=hold, qc_inspector_employee_id=insp))
    lots = pd.DataFrame(rows)
    for c in ("roast_spec_min", "roast_spec_max"):
        lots[c] = lots[c].astype("Int64")
    affected = lots[lots["hold_status"] == "回収・交換対象"].copy()
    return lots, affected
