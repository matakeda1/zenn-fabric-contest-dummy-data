"""Mobile app event logs (JSON Lines) linked to EC app orders, store coupon use and the 5.4.0 checkout bug."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

from . import config
from .calendar_jp import daterange
from .io_utils import write_csv

SALT = "contoso-zenn-2026"
JST = "+09:00"
RELEASES = [
    ("iOS", "4.9.3", date(2025, 3, 10), "旧アーキテクチャ最終版（サポート継続中）"),
    ("Android", "4.9.3", date(2025, 3, 10), "旧アーキテクチャ最終版（サポート継続中）"),
    ("iOS", "5.3.0", date(2026, 7, 28), "店舗検索の改善"),
    ("Android", "5.3.0", date(2026, 7, 28), "店舗検索の改善"),
    ("iOS", "5.3.2", date(2026, 8, 25), "軽微な不具合修正"),
    ("Android", "5.3.2", date(2026, 8, 25), "軽微な不具合修正"),
    ("iOS", "5.4.0", date(2026, 9, 16), "決済 SDK を更新、カート画面をリニューアル"),
    ("Android", "5.4.0", date(2026, 9, 16), "決済 SDK を更新、カート画面をリニューアル（段階的リリース）"),
    ("iOS", "5.4.1", date(2026, 9, 22), "不具合修正"),
    ("Android", "5.4.1", date(2026, 9, 22), "Android 版で決済が完了しない場合がある不具合を修正"),
    ("iOS", "5.5.0", date(2026, 10, 20), "モバイルオーダー（店舗受け取り）のβ提供開始"),
    ("Android", "5.5.0", date(2026, 10, 20), "モバイルオーダー（店舗受け取り）のβ提供開始"),
]
IOS_MODELS = ["iPhone 17", "iPhone 17 Pro", "iPhone 16", "iPhone 16 Pro", "iPhone 15", "iPhone 14", "iPhone 13", "iPhone SE (3rd)"]
AND_MODELS = ["Pixel 10", "Pixel 9", "Pixel 8a", "Galaxy S25", "Galaxy A55", "Xperia 10 VI", "AQUOS sense9", "arrows We2",
              "OPPO Reno13 A", "moto g64"]
SEARCH_TERMS = ["ハウスブレンド", "はうすぶれんど", "ドリップバッグ", "どりっぷばっぐ", "ドリップパック", "カフェインレス", "デカフェ",
                "decaf", "ギフト", "お歳暮", "深煎り", "浅煎り", "エチオピア", "ゲイシャ", "マンデリン", "コールドブリュー", "水出し",
                "アイスコーヒー", "マグカップ", "ミル", "定期便", "焼き菓子", "フィナンシェ", "セット", "秋のブレンド", "ホリデー"]


@dataclass
class AppResult:
    events: int
    sessions: int


def _h(s: str, n=16) -> str:
    return hashlib.sha256((SALT + s).encode()).hexdigest()[:n]


class AppLogs:
    def __init__(self, retail, seed):
        self.rng = np.random.default_rng(seed)
        self.rr = retail
        self.start, self.end = config.APP_LOG_START, config.DATA_END
        cust = retail.customers
        self.cust = cust.set_index("customer_id")
        pdf = retail.product_df.set_index("product_id")
        self.pname = pdf["product_name"].to_dict()
        self.pcat = pdf["category"].to_dict()
        self.ec_products = [p for p, r in pdf.iterrows() if r["sales_channel"] in ("オンラインのみ", "店舗・オンライン")]
        lines = retail.lines
        self.lines_by_order = {k: g for k, g in lines.groupby("order_id")}
        self.device_cache = {}
        self.out = []
        self.n_sessions = 0

    # ---------------------------------------------------------------------------------------------
    def device_of(self, key: str, platform: str | None = None, legacy: bool | None = None):
        if key in self.device_cache:
            return self.device_cache[key]
        r = np.random.default_rng(int(_h(key, 8), 16))
        platform = platform if isinstance(platform, str) else None
        plat = platform or ("iOS" if r.random() < 0.58 else "Android")
        if legacy is None:
            legacy = r.random() < 0.06
        if plat == "iOS":
            model = IOS_MODELS[int(r.integers(len(IOS_MODELS)))]
            osv = str(r.choice(["26.4", "26.5", "26.6", "18.7"], p=[0.3, 0.35, 0.25, 0.1]))
        else:
            model = AND_MODELS[int(r.integers(len(AND_MODELS)))]
            osv = str(r.choice(["16", "15", "14", "13"], p=[0.35, 0.35, 0.2, 0.1]))
        dev = dict(platform=plat, os_version=osv, model=model, legacy=legacy, lag=float(r.exponential(3.5)),
                   ios27=r.random() < 0.55)
        self.device_cache[key] = dev
        return dev

    def version(self, dev, t: datetime, forced=None):
        if forced:
            return forced
        if dev["legacy"]:
            return "4.9.3"
        d = t.date()
        avail = [v for p, v, rd, _ in RELEASES if p == dev["platform"] and not v.startswith("4") and
                 rd + timedelta(days=dev["lag"]) <= d]
        v = avail[-1] if avail else "5.3.0"
        if dev["platform"] == "Android" and v in ("5.4.0", "5.4.1"):
            adopt = config.ANDROID_540_ADOPTION.get(d)
            if d < config.APP_BUG_FIX:
                v = "5.4.0"
            elif adopt is not None and self.rng.random() < adopt:
                v = "5.4.0"
        return v

    def osv(self, dev, t):
        if dev["platform"] == "iOS" and dev["ios27"] and t.date() >= date(2026, 9, 15) + timedelta(days=dev["lag"] * 3):
            return "27.0" if t.date() < date(2026, 10, 25) else "27.1"
        return dev["os_version"]

    def uuid(self):
        b = self.rng.integers(0, 256, 16, dtype=np.uint8).tobytes()
        h = b.hex()
        return f"{h[:8]}-{h[8:12]}-4{h[13:16]}-a{h[17:20]}-{h[20:32]}"

    # ---------------------------------------------------------------------------------------------
    def emit(self, sess, name, t, screen, prev, params=None):
        dev = sess["dev"]
        ver = sess["ver"]
        t = t + timedelta(milliseconds=int(self.rng.integers(0, 1000)))
        recv = t + timedelta(milliseconds=int(self.rng.lognormal(6.5, 1.0)))
        if self.rng.random() < 0.01:
            recv += timedelta(minutes=int(self.rng.integers(5, 240)))  # offline buffering
        if dev["legacy"]:
            ev = {"eventId": self.uuid(), "name": name, "ts": int((t - datetime(1970, 1, 1, 9)).total_seconds() * 1000),
                  "uid": sess["anon"], "memberHash": sess["member"], "sid": sess["sid"], "screenName": screen,
                  "os": f"{dev['platform']} {self.osv(dev, t)}", "appVer": ver}
            p = params or {}
            if "product_id" in p:
                ev["itemId"] = p["product_id"]
                ev["price"] = p.get("price")
                ev["qty"] = p.get("quantity", 1)
            if "order_id" in p:
                ev["orderNo"] = p["order_id"]
                ev["amount"] = p["value"]
                ev["items"] = ",".join(f"{i['product_id']}x{i['quantity']}" for i in p["items"])
            if "search_term" in p:
                ev["keyword"] = p["search_term"]
            if "error_code" in p:
                ev["err"] = p["error_code"]
            if "coupon_code" in p:
                ev["coupon"] = p["coupon_code"]
            if "store_id" in p:
                ev["store"] = p["store_id"]
            self.out.append((recv, ev))
            return
        ms = f"{t.microsecond // 1000:03d}"
        ts = t.strftime("%Y-%m-%dT%H:%M:%S.") + ms + JST
        if sess["tzbug"]:
            ts = t.strftime("%Y-%m-%dT%H:%M:%S.") + ms + "Z"
        ev = {
            "event_id": self.uuid(),
            "event_name": name,
            "event_timestamp": ts,
            "received_at": recv.strftime("%Y-%m-%dT%H:%M:%S.") + f"{recv.microsecond // 1000:03d}" + JST,
            "schema_version": "5",
            "user": {"anonymous_id": sess["anon"], "member_id_hash": sess["member"], "is_logged_in": sess["member"] is not None},
            "session": {"session_id": sess["sid"], "session_seq": sess["seq"], "traffic_source": sess["src"]},
            "screen": {"name": screen, "previous": prev},
            "device": {"platform": dev["platform"], "os_version": self.osv(dev, t), "model": dev["model"], "app_version": ver,
                       "locale": "ja-JP"},
            "geo": {"prefecture": sess["pref"]},
            "params": params or {},
        }
        self.out.append((recv, ev))
        if self.rng.random() < 0.012:  # duplicate delivery (retry)
            self.out.append((recv + timedelta(seconds=int(self.rng.integers(1, 30))), ev))

    def new_session(self, key, member_cid, t, src="organic", platform=None, forced_ver=None, pref=None):
        dev = self.device_of(key, platform)
        self.n_sessions += 1
        return dict(dev=dev, ver=self.version(dev, t, forced_ver), anon="a_" + _h("anon" + key, 16),
                    member=("m_" + _h("member" + member_cid, 20)) if member_cid else None, sid="s_" + _h(f"s{self.n_sessions}{t}", 14),
                    seq=int(self.rng.integers(1, 120)), src=src, pref=pref, tzbug=(dev["platform"] == "Android" and dev["model"] == "moto g64"))

    def step(self, t, lo=3, hi=40):
        return t + timedelta(seconds=int(self.rng.integers(lo, hi)))

    def item_params(self, pid, qty=1, price=None):
        return {"product_id": pid, "product_name": self.pname[pid], "category": self.pcat[pid],
                "price": int(price) if price is not None else None, "quantity": int(qty)}

    # ---------------------------------------------------------------------------------------------
    def purchase_session(self, order, items):
        rng = self.rng
        cid = order.customer_id
        c = self.cust.loc[cid]
        end_t = order.order_datetime.to_pydatetime()
        n_view = len(items) + int(rng.integers(0, 4))
        t = end_t - timedelta(seconds=int(rng.integers(90, 240)) * (n_view + 2))
        src = "push" if (end_t.date() in (date(2026, 9, 1), date(2026, 10, 1)) and rng.random() < 0.4) else str(
            rng.choice(["organic", "deeplink", "ad"], p=[0.8, 0.12, 0.08]))
        s = self.new_session(cid, cid, t, src, platform=c["platform"], pref=c["prefecture"])
        if src == "push":
            self.emit(s, "push_open", t, "home", None, {"campaign": f"push_{end_t:%m%d}"})
        self.emit(s, "app_open", t, "home", None)
        t = self.step(t)
        self.emit(s, "screen_view", t, "home", None)
        prev = "home"
        if rng.random() < 0.45:
            t = self.step(t)
            term = SEARCH_TERMS[int(rng.integers(len(SEARCH_TERMS)))]
            self.emit(s, "search", t, "search_results", prev, {"search_term": term, "result_count": int(rng.integers(0, 25))})
            prev = "search_results"
        extra = [self.ec_products[int(rng.integers(len(self.ec_products)))] for _ in range(n_view - len(items))]
        for pid in extra:
            t = self.step(t, 10, 90)
            self.emit(s, "view_item", t, "product_detail", prev, self.item_params(pid))
        for it in items.itertuples():
            t = self.step(t, 10, 120)
            self.emit(s, "view_item", t, "product_detail", prev, self.item_params(it.product_id, 1, it.unit_price))
            t = self.step(t, 3, 30)
            self.emit(s, "add_to_cart", t, "product_detail", prev, self.item_params(it.product_id, it.quantity, it.unit_price))
            prev = "product_detail"
        t = self.step(t)
        self.emit(s, "view_cart", t, "cart", prev, {"cart_value": int(items["line_total"].sum())})
        t = self.step(t)
        self.emit(s, "begin_checkout", t, "checkout", "cart", {"cart_value": int(items["line_total"].sum())})
        t = min(self.step(t, 10, 60), end_t - timedelta(seconds=5))
        self.emit(s, "add_payment_info", t, "payment", "checkout", {"payment_method": order.payment_method})
        self.emit(s, "purchase", end_t, "order_complete", "payment", {
            "order_id": order.order_id, "value": int(order.total_incl_tax), "currency": "JPY",
            "shipping_fee": int(order.shipping_fee), "coupon_code": order.coupon_code if isinstance(order.coupon_code, str) else None,
            "payment_method": order.payment_method,
            "items": [{"product_id": it.product_id, "quantity": int(it.quantity), "price": int(it.unit_price)} for it in items.itertuples()]})
        if rng.random() < 0.6:
            self.emit(s, "app_background", self.step(end_t, 5, 120), "order_complete", None)

    def failed_session(self, f):
        rng = self.rng
        cid = f.customer_id
        c = self.cust.loc[cid]
        t0 = f.attempted_at.to_pydatetime() if hasattr(f.attempted_at, "to_pydatetime") else f.attempted_at
        t = t0 - timedelta(minutes=int(rng.integers(3, 9)))
        s = self.new_session(cid, cid, t, "organic", platform="Android", forced_ver="5.4.0", pref=c["prefecture"])
        self.emit(s, "app_open", t, "home", None)
        pids = [self.ec_products[int(rng.integers(len(self.ec_products)))] for _ in range(int(rng.integers(1, 4)))]
        prev = "home"
        for pid in pids:
            t = self.step(t, 10, 80)
            self.emit(s, "view_item", t, "product_detail", prev, self.item_params(pid))
            t = self.step(t, 3, 20)
            self.emit(s, "add_to_cart", t, "product_detail", prev, self.item_params(pid))
            prev = "product_detail"
        t = self.step(t)
        self.emit(s, "begin_checkout", t, "checkout", "cart")
        for k in range(int(rng.integers(1, 4))):
            t = self.step(t, 10, 50)
            self.emit(s, "add_payment_info", t, "payment", "checkout", {"payment_method": "クレジットカード"})
            t = t + timedelta(seconds=30)
            self.emit(s, "error", t, "payment", "checkout",
                      {"error_code": "PAYMENT_SDK_TIMEOUT", "error_message": "決済処理がタイムアウトしました。時間をおいて再度お試しください。",
                       "retry_count": k})
        self.emit(s, "app_background", self.step(t), "payment", None)

    def browse_session(self, t, cid, pref, kind, src="organic"):
        rng = self.rng
        key = cid if cid else f"guest{int(rng.integers(0, 60000))}"
        plat = self.cust.loc[cid]["platform"] if cid else None
        s = self.new_session(key, cid if (cid and rng.random() < 0.93) else None, t, src, platform=plat, pref=pref)
        if src == "push":
            self.emit(s, "push_open", t, "home", None, {"campaign": f"push_{t:%m%d}"})
        self.emit(s, "app_open", t, "home", None)
        t = self.step(t)
        self.emit(s, "screen_view", t, "home", None)
        prev = "home"
        if kind == "bounce":
            pass
        elif kind in ("browse", "cart"):
            if rng.random() < 0.5:
                t = self.step(t)
                self.emit(s, "search", t, "search_results", prev,
                          {"search_term": SEARCH_TERMS[int(rng.integers(len(SEARCH_TERMS)))], "result_count": int(rng.integers(0, 25))})
                prev = "search_results"
            else:
                t = self.step(t)
                cat = str(rng.choice(["コーヒー豆", "ドリップバッグ", "ギフト", "焼き菓子", "器具・グッズ"]))
                self.emit(s, "view_item_list", t, "category", prev, {"item_list_name": cat})
                prev = "category"
            for _ in range(int(rng.integers(1, 6))):
                pid = self.ec_products[int(rng.integers(len(self.ec_products)))]
                t = self.step(t, 8, 100)
                self.emit(s, "view_item", t, "product_detail", prev, self.item_params(pid))
                if kind == "cart" and rng.random() < 0.6:
                    t = self.step(t, 3, 25)
                    self.emit(s, "add_to_cart", t, "product_detail", prev, self.item_params(pid))
            if kind == "cart":
                t = self.step(t)
                self.emit(s, "view_cart", t, "cart", "product_detail")
                if rng.random() < 0.3:
                    t = self.step(t)
                    self.emit(s, "remove_from_cart", t, "cart", "cart")
                if rng.random() < 0.35:
                    t = self.step(t)
                    self.emit(s, "begin_checkout", t, "checkout", "cart")
        elif kind == "store":
            t = self.step(t)
            self.emit(s, "store_search", t, "store_list", prev, {"query": pref or "現在地"})
            t = self.step(t)
            st = str(rng.choice([x["store_id"] for x in config.STORES if x["close_date"] is None]))
            self.emit(s, "screen_view", t, "store_detail", "store_list", {"store_id": st})
        elif kind == "mypage":
            t = self.step(t)
            self.emit(s, "screen_view", t, str(rng.choice(["mypage", "order_history", "point", "settings"])), prev)
        if rng.random() < 0.7:
            self.emit(s, "app_background", self.step(t, 5, 200), prev, None)

    def coupon_session(self, order):
        rng = self.rng
        cid = order.customer_id
        c = self.cust.loc[cid]
        t = order.order_datetime.to_pydatetime() - timedelta(seconds=int(rng.integers(40, 240)))
        s = self.new_session(cid, cid, t, "organic", platform=c["platform"], pref=c["prefecture"])
        self.emit(s, "app_open", t, "home", None)
        t = self.step(t, 2, 10)
        self.emit(s, "screen_view", t, "coupon", "home")
        t = self.step(t, 2, 20)
        self.emit(s, "coupon_display", t, "coupon", "home", {"coupon_code": "APP50", "store_id": order.store_id})

    # ---------------------------------------------------------------------------------------------
    def run(self, out_dir):
        rng = self.rng
        h = self.rr.orders
        win = (h["order_datetime"] >= pd.Timestamp(self.start)) & (h["order_datetime"] < pd.Timestamp(self.end) + pd.Timedelta(days=1))
        app_orders = h[win & (h["device"] == "アプリ") & (h["order_status"] != "キャンセル")]
        for o in app_orders.itertuples():
            self.purchase_session(o, self.lines_by_order[o.order_id])
        cp = h[win & (h["coupon_code"] == "APP50")]
        for o in cp.itertuples():
            if isinstance(self.cust.loc[o.customer_id]["platform"], str):
                self.coupon_session(o)
        f = self.rr.failed_app_checkouts
        if len(f):
            f = f.assign(attempted_at=pd.to_datetime(f["attempted_at"]))
            f = f[(f["attempted_at"] >= pd.Timestamp(self.start))]
            for r in f.itertuples():
                self.failed_session(r)
                if (not bool(r.retried_on_web)) and rng.random() < 0.45:
                    r2 = r._replace(attempted_at=r.attempted_at + pd.Timedelta(hours=int(rng.integers(1, 30))))
                    self.failed_session(r2)
        cust = self.rr.customers
        app_users = cust[cust["app_user"] & cust["platform"].notna()]
        daily_purchase = app_orders.groupby(app_orders["order_datetime"].dt.date).size()
        hours = np.array([0.6, 0.35, 0.2, 0.1, 0.1, 0.2, 0.5, 1.0, 1.2, 1.0, 0.9, 0.9, 1.4, 1.2, 0.9, 0.9, 1.0, 1.1, 1.3,
                          1.5, 1.8, 1.9, 1.6, 1.1])
        hours = np.cumsum(hours / hours.sum())
        app_i = cust.set_index("customer_id")["app_i"]
        for d in daterange(self.start, self.end):
            di = (d - config.RETAIL_START).days
            pool = app_users[(app_users["reg_i"] <= di) & (app_users["app_i"] <= di)]
            n = int(daily_purchase.get(d, 30) * rng.uniform(7, 9))
            pushes = {date(2026, 9, 1): 9, date(2026, 10, 1): 8, date(2026, 10, 20): 12}
            for k in range(n):
                hr = int(np.searchsorted(hours, rng.random()))
                t = datetime(d.year, d.month, d.day, hr) + timedelta(seconds=int(rng.integers(0, 3600)))
                src = "organic"
                if d in pushes and rng.random() < 0.3:
                    t = datetime(d.year, d.month, d.day, pushes[d]) + timedelta(seconds=int(rng.exponential(1500)))
                    src = "push"
                if rng.random() < 0.22:
                    cid, pref = None, None
                else:
                    r = pool.iloc[int(rng.integers(len(pool)))]
                    cid, pref = r["customer_id"], r["prefecture"]
                kind = str(rng.choice(["bounce", "browse", "cart", "store", "mypage"], p=[0.28, 0.42, 0.14, 0.08, 0.08]))
                self.browse_session(t, cid, pref, kind, src)
        # write per day (by received date)
        self.out.sort(key=lambda x: x[0])
        ev_dir = out_dir / "events"
        ev_dir.mkdir(parents=True, exist_ok=True)
        files = {}
        for recv, ev in self.out:
            k = min(max(recv.date(), self.start), self.end)
            files.setdefault(k, []).append(json.dumps(ev, ensure_ascii=False, separators=(",", ":")))
        for k, rows in files.items():
            with open(ev_dir / f"app_events_{k:%Y-%m-%d}.jsonl", "w", encoding="utf-8", newline="\n") as fh:
                fh.write("\n".join(rows) + "\n")
        rel = pd.DataFrame(RELEASES, columns=["platform", "app_version", "release_date", "release_note"])
        write_csv(rel, out_dir / "app_releases.csv")
        return AppResult(len(self.out), self.n_sessions)


def generate(out_dir, retail, seed) -> AppResult:
    return AppLogs(retail, seed).run(out_dir)
