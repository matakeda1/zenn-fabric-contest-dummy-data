"""Facility & energy: sites, 30-minute electricity / gas usage with BEMS outdoor temperature, HVAC settings log."""
from __future__ import annotations

from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

from . import config, weather
from .calendar_jp import HOLIDAY_DATES, daterange, is_offday
from .io_utils import write_csv
from .manufacturing import is_factory_day


def _hm(s):
    h, m = s.split(":")
    return int(h) * 60 + int(m)


class Energy:
    def __init__(self, wx, retail, hr, mfg, seed):
        self.rng = np.random.default_rng(seed)
        self.wx = wx
        self.rr = retail
        self.hr = hr
        self.mfg = mfg
        self.start, self.end = config.ENERGY_START, config.DATA_END
        self.idx = pd.date_range(pd.Timestamp(self.start), pd.Timestamp(self.end) + pd.Timedelta(days=1), freq="30min",
                                 inclusive="left").as_unit("ns")
        self.n = len(self.idx)
        self.dates = self.idx.date
        self.minute = (self.idx.hour * 60 + self.idx.minute).to_numpy()
        self.closures = {(r.store_id, r.date): r.closure_type for r in retail.closures.itertuples()}
        st = retail.orders[retail.orders["channel"] == "店舗"]
        st = st[st["order_datetime"] >= pd.Timestamp(self.start)]
        self.receipts = st.groupby(["store_id", st["order_datetime"].dt.floor("30min")]).size()
        att = hr["attendance"]
        onsite = att[(att["work_style"] == "出社") & att["clock_in"].notna()]
        self.hq_onsite = onsite[onsite["site_id"] == "H01"].groupby("work_date").size().to_dict()
        self.logs = []

    def sites(self):
        rows = []
        for s in config.STORES:
            rows.append(dict(site_id=s["store_id"], site_name=s["store_name"], site_type="店舗", prefecture=s["prefecture"],
                             city=s["city"], latitude=s["lat"], longitude=s["lon"], floor_area_m2=s["floor_m2"],
                             building_type="路面店" if s["area_type"] in ("住宅地", "観光地") else "商業ビル テナント",
                             electricity_contract="低圧", contract_kw=int(20 + s["floor_m2"] * 0.25),
                             gas_supply="都市ガス" if s["gas"] else "なし", open_date=s["open_date"], close_date=s["close_date"],
                             hvac_zones="客席", station=s["station"]))
        for s in config.OTHER_SITES:
            rows.append(dict(site_id=s["site_id"], site_name=s["site_name"], site_type=s["site_type"], prefecture=s["prefecture"],
                             city=s["city"], latitude=s["lat"], longitude=s["lon"], floor_area_m2=s["floor_m2"],
                             building_type=s["building_type"], electricity_contract=s["electricity_contract"],
                             contract_kw=s["contract_kw"], gas_supply="都市ガス" if s["gas"] else "なし", open_date=s["open_date"],
                             close_date=None,
                             hvac_zones={"工場": "包装室", "物流センター": "冷蔵エリア", "本社": "執務室,会議室", "支店": "執務室"}[s["site_type"]],
                             station=s["station"]))
        df = pd.DataFrame(rows)
        df["jma_station_name"] = df["station"].map(lambda k: config.STATIONS[k]["name"])
        df["jma_prec_no"] = df["station"].map(lambda k: config.STATIONS[k]["prec_no"])
        df["jma_block_no"] = df["station"].map(lambda k: config.STATIONS[k]["block_no"])
        return df

    # ---------------------------------------------------------------------------------------------
    def log(self, site, zone, t, etype, mode, sp, fan, by, note=None):
        self.logs.append(dict(site_id=site, zone=zone, event_time=t, event_type=etype, mode=mode, setpoint_c=sp,
                              fan_speed=fan, changed_by=by, note=note))

    def hvac_timeline(self, site, zone, temp_daily, on_windows, cool_sp, heat_sp, night_bug=None, overrides=()):
        """Returns arrays (on, mode, setpoint) per slot and writes the event log."""
        r = self.rng
        n = self.n
        on = np.zeros(n, dtype=bool)
        mode = np.zeros(n, dtype=np.int8)  # 0 off/fan, 1 cool, 2 heat
        sp = np.full(n, np.nan)
        cur_mode = None
        cur_sp = None
        days = sorted(set(self.dates))
        for d in days:
            win = on_windows(d)
            tmean = temp_daily.get(d, 18.0)
            m = 1 if tmean >= 21.5 and d.month in (5, 6, 7, 8, 9, 10) else (2 if tmean <= 15.5 else 0)
            spv = cool_sp(d) if m == 1 else (heat_sp(d) if m == 2 else None)
            for ov in overrides:
                if ov[0] <= d <= ov[1] and m == ov[2]:
                    spv = ov[3]
            if win is None:
                continue
            a, b = win
            t_on = datetime(d.year, d.month, d.day) + timedelta(minutes=a)
            t_off = datetime(d.year, d.month, d.day) + timedelta(minutes=b)
            mode_name = {0: "送風", 1: "冷房", 2: "暖房"}[m]
            if m != cur_mode:
                self.log(site, zone, t_on - timedelta(minutes=1), "モード変更", mode_name, spv, "自動", "BEMS 自動制御",
                         "季節切替")
                cur_mode = m
            if spv != cur_sp and spv is not None:
                by = "スケジュール"
                note = None
                for ov in overrides:
                    if ov[0] <= d <= ov[1] and m == ov[2]:
                        by, note = ov[4], ov[5]
                self.log(site, zone, t_on - timedelta(minutes=1), "設定変更", mode_name, spv, "自動", by, note)
                cur_sp = spv
            self.log(site, zone, t_on, "運転開始", mode_name, spv, "自動", "スケジュール")
            bug = night_bug and night_bug[0] <= d <= night_bug[1]
            if not bug:
                self.log(site, zone, t_off, "運転停止", "停止", None, None, "スケジュール")
            i0 = int((t_on - datetime.combine(self.start, datetime.min.time())).total_seconds() // 1800)
            i1 = int((t_off - datetime.combine(self.start, datetime.min.time())).total_seconds() // 1800)
            if bug:
                nd = d + timedelta(days=1)
                i1 = int((datetime(nd.year, nd.month, nd.day) + timedelta(minutes=a) - datetime.combine(self.start, datetime.min.time())).total_seconds() // 1800)
            i0, i1 = max(i0, 0), min(i1, n)
            on[i0:i1] = True
            mode[i0:i1] = m
            sp[i0:i1] = spv if spv is not None else np.nan
            # occasional manual tweak by staff on hot / cold days
            if m == 1 and r.random() < 0.06 and site.startswith("S"):
                tt = t_on + timedelta(hours=int(r.integers(3, 7)))
                self.log(site, zone, tt, "設定変更", "冷房", spv - 2, "強", "手動（店舗）", "暑いとのお客様の声")
                j0 = int((tt - datetime.combine(self.start, datetime.min.time())).total_seconds() // 1800)
                sp[j0:i1] = spv - 2
                self.log(site, zone, t_off - timedelta(minutes=2), "設定変更", "冷房", spv, "自動", "BEMS 自動制御", "設定値の自動復帰")
        return on, mode, sp

    # ---------------------------------------------------------------------------------------------
    def run(self, out_dir):
        r = self.rng
        sites = self.sites()
        frames = []
        f30 = self.mfg.factory_30min.set_index("slot")
        for s in sites.itertuples():
            sid = s.site_id
            st_daily = weather.daily(self.wx, s.station)
            tser = weather.subdaily_temperature(st_daily, 30, r, self.start, self.end, noise=0.4).to_numpy()
            tdaily = {k.date(): v for k, v in st_daily["temp_mean_c"].items()}
            opened = date.fromisoformat(s.open_date)
            closed = date.fromisoformat(s.close_date) if isinstance(s.close_date, str) else None
            valid = np.array([(d >= opened - timedelta(days=7)) and (closed is None or d <= closed) for d in self.dates])
            area = s.floor_area_m2
            minute = self.minute
            elec = np.zeros(self.n)
            gas = np.zeros(self.n) if s.gas_supply != "なし" else None
            if s.site_type == "店舗":
                store = next(x for x in config.STORES if x["store_id"] == sid)
                o, c = _hm(store["open_time"]), _hm(store["close_time"])

                def win(d, sid=sid, o=o, c=c, opened=opened, closed=closed):
                    if d < opened or (closed and d > closed):
                        return None
                    ct = self.closures.get((sid, d))
                    if ct in ("年始休業", "改装休業", "臨時休業"):
                        return None
                    if ct == "短縮営業":
                        return (o - 30, min(c, 17 * 60))
                    return (o - 30, c + 15)

                overrides = []
                if sid == "S07":
                    overrides.append((date(2026, 6, 1), date(2026, 9, 30), 1, 22.0, "手動（店舗）", "店長判断で設定温度を変更"))
                night = (date(2026, 6, 10), date(2026, 7, 3)) if sid == "S10" else None
                on, mode, sp = self.hvac_timeline(sid, "客席", tdaily, win, lambda d: 26.0, lambda d: 21.0, night, overrides)
                open_mask = np.array([win(d) is not None for d in self.dates])
                in_hours = np.zeros(self.n, dtype=bool)
                for i, d in enumerate(self.dates):
                    w = win(d)
                    if w and w[0] <= minute[i] < w[1]:
                        in_hours[i] = True
                rc = np.zeros(self.n)
                if sid in self.receipts.index.get_level_values(0):
                    ser = self.receipts.loc[sid]
                    pos = self.idx.get_indexer(pd.DatetimeIndex(ser.index).as_unit("ns"))
                    ok = pos >= 0
                    rc[pos[ok]] = ser.to_numpy()[ok]
                base = 1.0 + 0.007 * area
                elec = base + np.where(in_hours, 2.2 + 0.018 * area + 0.16 * rc, 0)
                if sid == "S03":
                    pass
                gas_on = s.gas_supply != "なし"
                if gas_on:
                    gas = np.where(in_hours, 0.25 + 0.03 * rc, 0.02)
            elif s.site_type in ("本社", "支店"):
                def win(d):
                    if is_offday(d):
                        return None
                    return (_hm("08:30"), _hm("19:30") if s.site_type == "本社" else _hm("19:00"))

                cool = (lambda d: 25.0 if d < date(2025, 7, 1) else 27.0) if sid == "H01" else (lambda d: 26.0)
                heat = (lambda d: 22.0 if d < date(2025, 11, 1) else 20.0) if sid == "H01" else (lambda d: 21.0)
                on, mode, sp = self.hvac_timeline(sid, "執務室", tdaily, win, cool, heat)
                if sid == "H01":
                    self.hvac_timeline(sid, "会議室", tdaily, win, cool, heat)
                    self.logs.append(dict(site_id="H01", zone="執務室", event_time=datetime(2025, 7, 1, 8, 0), event_type="設定変更",
                                          mode="冷房", setpoint_c=27.0, fan_speed="自動", changed_by="手動（本社）",
                                          note="省エネ方針により冷房設定温度を 25℃→27℃ に変更"))
                in_hours = np.array([(win(d) is not None) and (win(d)[0] <= m_ < win(d)[1]) for d, m_ in zip(self.dates, minute)])
                if sid == "H01":
                    occ = np.array([self.hq_onsite.get(d, 0) for d in self.dates], dtype=float)
                    elec = 9.0 + np.where(in_hours, 4.0 + 0.11 * occ, 0)
                else:
                    elec = 0.5 + np.where(in_hours, 1.6 + 0.002 * area, 0)
            elif s.site_type == "工場":
                def win(d):
                    return (_hm("06:00"), _hm("22:00")) if is_factory_day(d) else None

                on, mode, sp = self.hvac_timeline(sid, "包装室", tdaily, win, lambda d: 24.0, lambda d: 20.0)
                prod = np.array([is_factory_day(d) for d in self.dates]) & (minute >= 6 * 60) & (minute < 22 * 60)
                elec = 22.0 + np.where(prod, 48.0 + r.normal(0, 3, self.n), 0)
                gas = 1.2 + np.where(prod & (minute < 21 * 60 + 30), 24.0 + r.normal(0, 2, self.n), 0)
                # inside the sensor window use the machine-level simulation
                pos = self.idx.get_indexer(pd.DatetimeIndex(f30.index).as_unit("ns"))
                ok = pos >= 0
                elec[pos[ok]] = 22.0 + f30["elec_kwh"].to_numpy()[ok]
                gas[pos[ok]] = 1.2 + f30["gas_m3"].to_numpy()[ok]
            else:  # DC
                def win(d):
                    return None if d.weekday() == 6 or (d.month == 1 and d.day <= 3) else (_hm("07:00"), _hm("22:00"))

                on, mode, sp = self.hvac_timeline(sid, "冷蔵エリア", tdaily, win, lambda d: 18.0, lambda d: 16.0)
                ops = np.array([win(d) is not None for d in self.dates]) & (minute >= 7 * 60) & (minute < 22 * 60)
                peak = np.array([1.3 if (d.month == 12 and d.day <= 25) or (d.month == 7 and d.day <= 15) else 1.0 for d in self.dates])
                elec = 7.0 + 0.22 * np.clip(tser - 15, 0, None) + np.where(ops, 16.0 * peak, 0) + np.where(
                    (minute >= 22 * 60) | (minute < 5 * 60), 4.0, 0)
            # HVAC energy (all sites): standby/fan while running + cooling/heating load.
            # Lower cooling setpoints cost disproportionately more (larger fan speed, longer compressor runs).
            sp_eff = np.nan_to_num(sp, nan=24.0)
            cool_load = np.where(on & (mode == 1), np.clip(tser - (sp_eff - 6), 0, None), 0)
            heat_load = np.where(on & (mode == 2), np.clip((sp_eff + 2) - tser, 0, None), 0)
            sp_factor = np.where(mode == 1, 1 + 0.08 * np.clip(26 - sp_eff, 0, None), 1.0)
            base_on = np.where(on, 0.55, 0)
            k = area / 100.0
            hv = k * (base_on + 0.30 * cool_load * sp_factor + 0.17 * heat_load)
            if s.site_type == "工場":
                hv = hv * 0.35
            elif s.site_type == "物流センター":
                hv = hv * 0.25
            elif s.site_type in ("本社", "支店"):
                hv = hv * 0.35
            elec = elec + hv
            elec = elec * r.lognormal(0, 0.04, self.n)
            # pre-open / post-close
            elec = np.where(valid, elec, np.nan)
            if gas is not None:
                gas = np.where(valid, gas * r.lognormal(0, 0.05, self.n), np.nan)
            temp_sensor = tser + 0.6 + r.normal(0, 0.2, self.n)
            # data quality: meter replacement, communication loss, sensor faults
            if sid == "S03":
                m = (self.idx >= "2025-09-09 10:00") & (self.idx < "2025-09-09 14:00")
                elec = np.where(m, 0.0, elec)
                if gas is not None:
                    gas = np.where(m, 0.0, gas)
            if sid == "D01":
                m = (self.idx >= "2026-03-12 02:00") & (self.idx < "2026-03-12 08:00")
                elec = np.where(m, np.nan, elec)
            lost = r.random(self.n) < 0.0006
            elec = np.where(lost, np.nan, elec)
            if sid == "S14":
                m = (self.idx >= "2026-01-20") & (self.idx < "2026-02-03")
                temp_sensor = np.where(m, np.nan, temp_sensor)
            if sid == "H01":
                m = (self.idx >= "2025-08-01") & (self.idx < "2025-08-15")
                temp_sensor = np.where(m, temp_sensor + 6.5, temp_sensor)  # sensor placed in the sun
            df = pd.DataFrame(dict(site_id=sid, timestamp=self.idx, electricity_kwh=np.round(elec, 2),
                                   gas_m3=np.round(gas, 3) if gas is not None else np.nan,
                                   outdoor_temp_c=np.round(temp_sensor, 1)))
            df = df[valid]
            frames.append(df)
            print(f"    energy {sid}", flush=True)
        e = pd.concat(frames, ignore_index=True).sort_values(["timestamp", "site_id"], kind="stable")
        e["year"] = e["timestamp"].dt.year
        for y, g in e.groupby("year"):
            g = g.drop(columns=["year"]).copy()
            g["timestamp"] = g["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
            write_csv(g, out_dir / "energy_usage_30min" / f"energy_usage_30min_{y}.csv")
        lg = pd.DataFrame(self.logs).sort_values(["event_time", "site_id"], kind="stable").reset_index(drop=True)
        lg = lg[(lg["event_time"] >= pd.Timestamp(self.start)) & (lg["event_time"] < pd.Timestamp(self.end) + pd.Timedelta(days=1))]
        lg.insert(0, "log_id", [f"HV{i + 1:06d}" for i in range(len(lg))])
        lg["event_time"] = pd.to_datetime(lg["event_time"]).dt.strftime("%Y-%m-%d %H:%M:%S")
        write_csv(lg, out_dir / "hvac_settings_log.csv")
        write_csv(sites.drop(columns=["station"]), out_dir / "sites.csv")
        return dict(rows=len(e), logs=len(lg))


def generate(out_dir, wx, retail, hr, mfg, seed):
    return Energy(wx, retail, hr, mfg, seed).run(out_dir)
