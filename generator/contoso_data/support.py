"""Customer-support inquiries (semi-structured text) derived from events in the other datasets."""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

from . import config, people
from .calendar_jp import daterange
from .io_utils import write_csv
from .support_text import ALIASES, CLOSE, EMOJI, GREET, OP_REPLY, PHONE_ACTION, SNS_TAGS, T

CHANNELS = ["電話", "メール", "Webフォーム", "チャット", "アプリ内", "SNS", "店頭"]
MIX_2024 = np.array([0.33, 0.25, 0.22, 0.08, 0.07, 0.03, 0.02])
MIX_2026 = np.array([0.22, 0.17, 0.20, 0.22, 0.13, 0.03, 0.03])
HOUR_P = np.array([1, .5, .3, .2, .2, .3, .6, 1, 1.4, 1.6, 1.6, 1.5, 1.6, 1.5, 1.4, 1.4, 1.3, 1.3, 1.3, 1.5, 1.8, 1.9, 1.7, 1.3])
HOUR_P = HOUR_P / HOUR_P.sum()
TEAM_DEPT = {"EC運営（物流）": "D106", "品質保証部": "D108", "カスタマーサポート": "D109", "情報システム": "D104",
             "店舗運営部": "D110", "法人営業部": "D202"}
REASON_PHRASE = {"値上げのため": "値上げで負担が大きくなった", "飲みきれず在庫が余る": "飲みきれずに豆が余ってしまう",
                 "他社サービスへ乗り換え": "他のサービスを試してみたい", "味に飽きた": "味に少し飽きてしまった",
                 "生活環境の変化": "引っ越しで生活環境が変わる", "経済的な理由": "家計を見直している",
                 "店舗で購入するため": "近くの店舗で買えるようになった", "その他": "しばらくコーヒーを控える"}


class Support:
    def __init__(self, retail, mfg, emp, wx, seed):
        self.rng = np.random.default_rng(seed)
        self.rr, self.mfg, self.emp = retail, mfg, emp
        self.seeds = []
        st = pd.DataFrame(config.STORES)
        self.store_name = dict(zip(st["store_id"], st["store_name"]))
        lines = retail.lines
        self.first_product = lines.groupby("order_id")["product_id"].first().to_dict()

    # ------------------------------------------------------------------------------------------
    def seed(self, t, cat, sub, tidx=None, **kw):
        self.seeds.append(dict(received_at=t, category=cat, subcategory=sub, tidx=tidx, **kw))

    def biz_time(self, d: date, channel=None):
        r = self.rng
        if channel in ("電話", "チャット"):
            h = int(r.integers(10, 18))
        else:
            h = int(r.choice(24, p=HOUR_P))
        return datetime(d.year, d.month, d.day, h) + timedelta(seconds=int(r.integers(0, 3600)))

    # ------------------------------------------------------------------------------------------
    def collect(self):
        r = self.rng
        h = self.rr.orders
        ec = h[h["channel"] != "店舗"].copy()
        prom = pd.to_datetime(ec["promised_delivery_date"])
        dlv = pd.to_datetime(ec["delivered_date"])
        late = ec[(dlv > prom) & (r.random(len(ec)) < 0.18)]
        drip = {"P020", "P021", "P022", "P023", "P024", "P025", "P081", "P102"}
        for o in late.itertuples():
            pd_ = o.promised_delivery_date
            d = pd_ + timedelta(days=int(r.integers(0, 3)))
            pid = self.first_product.get(o.order_id)
            od = o.order_datetime.date()
            outage = date(2026, 6, 18) <= od <= date(2026, 6, 23) and pid in drip
            self.seed(self.biz_time(min(d, config.DATA_END)), "配送・お届け", "配送遅延", 3 if outage else None,
                      customer_id=o.customer_id, order_id=o.order_id, product_id=pid, odate=od,
                      days=max(1, (min(d, config.DATA_END) - pd_).days))
        for o in h[(h["order_status"] == "キャンセル") & (r.random(len(h)) < 0.3)].itertuples():
            t = o.order_datetime.to_pydatetime() + timedelta(minutes=int(r.integers(5, 1440)))
            self.seed(t, "注文・決済", "キャンセル・変更", None, customer_id=o.customer_id, order_id=o.order_id,
                      product_id=self.first_product.get(o.order_id), odate=o.order_datetime.date())
        lot_orders = set(self.rr.lot_issues["order_id"]) if len(self.rr.lot_issues) else set()
        for o in h[(h["order_status"] == "返品") & ~h["order_id"].isin(lot_orders)].itertuples():
            if r.random() < 0.85 and isinstance(o.returned_date, date):
                d = o.returned_date - timedelta(days=int(r.integers(0, 3)))
                self.seed(self.biz_time(d), "返品・交換", "返品・交換", None, customer_id=o.customer_id, order_id=o.order_id,
                          product_id=self.first_product.get(o.order_id), odate=o.order_datetime.date())
        for li in self.rr.lot_issues.itertuples():
            ch = str(r.choice(["メール", "Webフォーム", "電話", "チャット", "店頭" if li.channel == "店舗" else "アプリ内"],
                              p=[0.3, 0.25, 0.25, 0.1, 0.1]))
            self.seed(self.biz_time(li.complaint_date, ch), "商品品質", "味・香り", int(r.integers(0, 3)),
                      customer_id=li.customer_id, order_id=li.order_id, product_id=li.product_id,
                      store_id=li.store_id if li.channel == "店舗" else None, lot_id=li.lot_id, channel=ch,
                      odate=None)
        f = self.rr.failed_app_checkouts
        if len(f):
            cust = self.rr.customers.set_index("customer_id")
            for x in f.itertuples():
                if r.random() > 0.42:
                    continue
                t = pd.Timestamp(x.attempted_at).to_pydatetime() + timedelta(minutes=int(r.integers(10, 600)))
                ch = str(r.choice(["アプリ内", "チャット", "メール", "電話"], p=[0.45, 0.3, 0.15, 0.1]))
                k = r.random() < 0.6
                self.seed(t, "注文・決済" if k else "アプリ・会員", "決済エラー" if k else "アプリ不具合", 0 if k else 2,
                          customer_id=x.customer_id, channel=ch, appver="5.4.0",
                          os=f"Android {r.choice(['14', '15', '16'])}", model=str(r.choice(["Pixel 9", "Galaxy S25", "AQUOS sense9", "Xperia 10 VI", "arrows We2"])))
        for s in self.rr.subscriptions.itertuples():
            if s.status == "解約" and isinstance(s.cancel_date, date) and r.random() < 0.35:
                d = s.cancel_date - timedelta(days=int(r.integers(0, 3)))
                self.seed(self.biz_time(max(d, s.start_date)), "定期便", "解約", None, customer_id=s.customer_id, product_id=s.product_id,
                          reason=REASON_PHRASE.get(s.cancel_reason, "しばらく休みたい"))
            for _ in range(int(s.skip_count)):
                if r.random() < 0.15:
                    end = s.cancel_date if isinstance(s.cancel_date, date) else config.DATA_END
                    span = max((end - s.start_date).days, 1)
                    d = s.start_date + timedelta(days=int(r.integers(0, span)))
                    self.seed(self.biz_time(d), "定期便", "スキップ・周期変更", None, customer_id=s.customer_id, product_id=s.product_id)
        for c in self.rr.closures.itertuples():
            if c.closure_type in ("臨時休業", "短縮営業") and c.reason.startswith("大雨") and r.random() < 0.5:
                d = c.date
                t = datetime(d.year, d.month, d.day, int(r.integers(7, 11)), int(r.integers(0, 60)))
                self.seed(t, "店舗", "営業時間・混雑", 0, store_id=c.store_id, channel=str(r.choice(["電話", "SNS"], p=[0.6, 0.4])))
        cust = self.rr.customers
        active_ids = cust["customer_id"].to_numpy()
        reg_i = cust["reg_i"].to_numpy()
        end_i = cust["end_i"].to_numpy()
        home = cust["home_store_id"].to_numpy()
        pids_all = list(self.rr.product_df["product_id"])
        bean_like = [p for p in pids_all if p in ALIASES]
        cats_base = [("商品のお問い合わせ", None, 0.33), ("アプリ・会員", None, 0.15), ("注文・決済", "クーポン・ポイント", 0.08),
                     ("注文・決済", "領収書", 0.04), ("ご意見・ご要望", None, 0.10), ("配送・お届け", "お届け日時の変更", 0.05),
                     ("配送・お届け", "破損・汚損", 0.03), ("配送・お届け", "誤配送・内容違い", 0.02), ("商品品質", "味・香り", 0.025),
                     ("商品品質", "異物混入", 0.006), ("商品品質", "賞味期限", 0.01), ("商品品質", "パッケージ不良", 0.02),
                     ("法人・大口", "法人・大口", 0.03), ("その他", "営業メール・スパム", 0.04), ("その他", "その他", 0.025),
                     ("定期便", "商品変更", 0.015)]
        cw = np.array([c[2] for c in cats_base])
        cw /= cw.sum()
        stores_open = [s for s in config.STORES]
        from .products import P as PRODUCTS, available
        pmeta = {p["product_id"]: p for p in PRODUCTS}
        _avail_cache = {}

        def avail_on(d):
            if d not in _avail_cache:
                _avail_cache[d] = {p for p, m in pmeta.items() if available(m, d)}
            return _avail_cache[d]

        beans = [p for p in pmeta if pmeta[p]["category"] == "コーヒー豆"]
        drips = [p for p in pmeta if pmeta[p]["category"] == "ドリップバッグ"]
        sweets_ec = ["P052", "P053", "P059", "P060"]
        gifts = [p for p in pmeta if pmeta[p]["category"] == "ギフト"] + ["P059", "P060"]
        ec_items = [p for p in pmeta if pmeta[p]["channel"] in ("ec", "both")]
        POOLS = {"ギフト・のし": gifts, "保存方法・淹れ方": beans + drips, "在庫・再入荷": ec_items,
                 "味・香り": beans + drips, "異物混入": beans + sweets_ec + ["P050", "P051", "P054"],
                 "賞味期限": beans + drips + sweets_ec + gifts, "パッケージ不良": drips + beans,
                 "お届け日時の変更": ec_items, "破損・汚損": ec_items, "誤配送・内容違い": ec_items,
                 "ご要望": beans, "法人・大口": gifts + drips, "商品変更": ["P100", "P101", "P102", "P103"],
                 "アレルギー・原材料": ["P050", "P051", "P052", "P053", "P054", "P056", "P057", "P059", "P060"],
                 "お褒め": beans + drips + ["P030", "P032", "P037", "P038", "P046", "P052", "P054", "P056"],
                 "カフェイン": ["P006", "P025", "P001"], "クーポン・ポイント": ec_items, "領収書": ec_items}
        for d in daterange(config.SUPPORT_START, config.DATA_END):
            di = (d - config.RETAIL_START).days
            yrs = di / 365.25
            lam = 3.4 * (1 + 0.25 * yrs) * (0.7 if d.weekday() >= 5 else 1.0)
            if date(2025, 3, 15) <= d <= date(2025, 5, 31):
                self._n_price = int(r.poisson(1.2))
                for _ in range(self._n_price):
                    self.seed(self.biz_time(d), "ご意見・ご要望", "ご要望", 2, customer_id=self._cust(active_ids, reg_i, end_i, di))
            for _ in range(int(r.poisson(lam))):
                k = int(r.choice(len(cats_base), p=cw))
                cat, sub, _w = cats_base[k]
                if sub is None:
                    subs = [s for (c, s) in T if c == cat]
                    sub = subs[int(r.integers(len(subs)))]
                cid = self._cust(active_ids, reg_i, end_i, di) if r.random() < 0.72 and cat != "その他" else None
                pool = POOLS.get(sub, bean_like)
                pool = [p for p in pool if p in avail_on(d)] or [p for p in bean_like if p in avail_on(d)]
                pid = pool[int(r.integers(len(pool)))]
                if sub in ("在庫・再入荷",) and d >= date(2025, 7, 1) and r.random() < 0.3:
                    pid = "P014"
                if sub == "お褒め" and d >= date(2025, 5, 15) and r.random() < 0.3:
                    pid = str(r.choice(["P037", "P074"])) if d.month in (5, 6, 7, 8, 9) else "P006"
                tid = None
                if sub == "お褒め" and pid in ("P037", "P074", "P006"):
                    tid = 1
                elif sub == "お褒め":
                    tid = 0
                if sub == "アプリ不具合":
                    tid = int(r.integers(0, 2))
                if sub == "味・香り":
                    tid = int(r.integers(3, 5))
                if sub == "ご要望":
                    tid = int(r.integers(0, 2))
                self.seed(self.biz_time(d), cat, sub, tid, customer_id=cid, product_id=pid,
                          store_id=None, appver=str(r.choice(["5.3.2", "5.3.0", "5.4.1", "5.5.0"])),
                          os=str(r.choice(["iOS 26.5", "iOS 18.7", "Android 15", "Android 16"])),
                          model=str(r.choice(["iPhone 16", "iPhone 15", "Pixel 9", "Galaxy A55"])), qty=int(r.integers(3, 9)))
            # store-related
            for s in stores_open:
                so = date.fromisoformat(s["open_date"])
                sc = date.fromisoformat(s["close_date"]) if s["close_date"] else None
                if d < so or (sc and d > sc):
                    continue
                p = 0.009
                cold = s["store_id"] == "S07" and date(2026, 6, 1) <= d <= date(2026, 9, 30)
                if cold:
                    p += 0.05
                if r.random() < p:
                    if cold and r.random() < 0.8:
                        sub, tid = "設備・環境", 1
                    else:
                        sub = str(r.choice(["接客", "設備・環境", "忘れ物"], p=[0.6, 0.25, 0.15]))
                        tid = None
                        if sub == "設備・環境":
                            tid = int(r.choice([0, 1, 2], p=[0.35, 0.25, 0.4]))
                    loc = np.where(home == s["store_id"])[0]
                    cid = active_ids[loc[int(r.integers(len(loc)))]] if len(loc) and r.random() < 0.5 else None
                    self.seed(self.biz_time(d), "店舗", sub, tid, store_id=s["store_id"], customer_id=cid)

    def _cust(self, ids, reg_i, end_i, di):
        for _ in range(20):
            k = int(self.rng.integers(len(ids)))
            if reg_i[k] <= di <= end_i[k] + 60:
                return ids[k]
        return None

    # ------------------------------------------------------------------------------------------
    def channel_for(self, s):
        r = self.rng
        if s.get("channel"):
            return s["channel"]
        t = s["received_at"]
        a = min(max((t.date() - date(2024, 1, 1)).days / (date(2026, 10, 31) - date(2024, 1, 1)).days, 0), 1)
        mix = MIX_2024 * (1 - a) + MIX_2026 * a
        if t.date() < date(2024, 4, 1):
            mix[3] = 0
        if s["category"] == "店舗":
            mix = np.array([0.35, 0.15, 0.2, 0.05, 0.05, 0.05, 0.15])
        elif s["category"] == "その他":
            mix = np.array([0.0, 0.5, 0.5, 0, 0, 0, 0])
        elif s["category"] == "法人・大口":
            mix = np.array([0.4, 0.3, 0.3, 0, 0, 0, 0])
        else:
            mix[6] = 0
        return CHANNELS[int(r.choice(len(CHANNELS), p=mix / mix.sum()))]

    def fmt_date(self, od, recv):
        r = self.rng
        if od is None:
            return "先日"
        k = int(r.integers(0, 5))
        if k == 0:
            return f"{od.month}/{od.day}"
        if k == 1:
            return f"{od.month}月{od.day}日"
        if k == 2:
            n = (recv.date() - od).days
            return f"{n}日前" if n > 0 else "今日"
        if k == 3:
            return od.strftime("%Y/%m/%d")
        return "先週" if (recv.date() - od).days >= 5 else f"{od.month}/{od.day}"

    def lot_variant(self, lot):
        if not lot:
            return "（ロット番号不明）"
        r = self.rng
        k = int(r.integers(0, 5))
        if k == 0:
            return lot
        if k == 1:
            return lot.replace("-", "")
        if k == 2:
            return "ロットNo." + lot
        if k == 3:
            return lot[1:7] + "-" + lot.split("-")[1]
        return lot.lower()

    def render(self, s, ch):
        r = self.rng
        tpl = T[(s["category"], s["subcategory"])]
        items = tpl["items"]
        i = s["tidx"] if s.get("tidx") is not None and s["tidx"] < len(items) else int(r.integers(len(items)))
        it = items[i]
        recv = s["received_at"]
        pid = s.get("product_id")
        store = s.get("store_id")
        sname = self.store_name.get(store, "近くの店舗")
        if store and r.random() < 0.35:
            sname = sname.replace("店", "のお店") if r.random() < 0.5 else sname + "さん"
        oid = s.get("order_id") or "（不明）"
        if s.get("order_id") and r.random() < 0.25:
            oid = "分かりません"
        ctx = dict(product=(ALIASES.get(pid) or ["コーヒー"])[int(r.integers(len(ALIASES.get(pid) or ["x"])))] if pid else "商品",
                   order_id=oid, odate=self.fmt_date(s.get("odate"), recv), days=s.get("days", int(r.integers(1, 5))),
                   lot=self.lot_variant(s.get("lot_id")), store=sname, appver=s.get("appver", "5.3.2"),
                   os=s.get("os", "iOS 26.5"), model=s.get("model", "iPhone 16"), reason=s.get("reason", "しばらく休みたい"),
                   qty=s.get("qty", int(r.integers(2, 6))))
        body = it["body"].format(**ctx)
        summary = it["summary"].format(**ctx)
        short = it["short"].format(**ctx)
        subject = it["subject"].format(**ctx)
        cat = s["category"]
        if ch == "メール":
            g = GREET[int(r.integers(len(GREET)))]
            c = CLOSE[int(r.integers(len(CLOSE)))]
            text = "\n\n".join(x for x in (g, body, c) if x)
            if s.get("customer_id") and r.random() < 0.3:
                text += f"\n\n会員番号：{s['customer_id']}"
        elif ch == "Webフォーム":
            kind = {"配送・お届け": "ご注文・配送について", "注文・決済": "ご注文・お支払いについて", "商品品質": "商品について",
                    "商品のお問い合わせ": "商品について", "定期便": "定期便について", "アプリ・会員": "アプリ・会員について",
                    "店舗": "店舗について", "返品・交換": "返品・交換について", "法人・大口": "法人のお客様",
                    }.get(cat, "その他")
            text = f"【お問い合わせ種別】{kind}\n【ご注文番号】{s.get('order_id') or ''}\n【お問い合わせ内容】\n{body}"
        elif ch == "電話":
            act = PHONE_ACTION.get(cat, PHONE_ACTION["default"])
            text = f"【入電 {recv:%H:%M}】\nお客様より、{summary}とのこと。\n→ {act[int(r.integers(len(act)))]}"
            if s.get("lot_id") and r.random() < 0.7:
                text += f"\n※ロット番号：{s['lot_id']}（お客様読み上げ）"
            subject = summary[:30]
        elif ch == "チャット":
            op = OP_REPLY.get(cat, OP_REPLY["default"])
            text = f"お客様: {short}{EMOJI[int(r.integers(len(EMOJI)))]}\nオペレーター: {op[0]}"
            if s.get("lot_id"):
                text += f"\nお客様: 袋には {self.lot_variant(s['lot_id'])} と書いてあります"
            elif s.get("order_id") and r.random() < 0.6:
                text += f"\nお客様: 注文番号は {s['order_id']} です"
            text += f"\nオペレーター: {op[-1]}"
            subject = short[:30]
        elif ch == "アプリ内":
            text = body.split("\n機種")[0] + f"\n---\nアプリ: {ctx['appver']} / {ctx['os']} / {ctx['model']}"
        elif ch == "SNS":
            text = f"@contoso_coffee {short}{EMOJI[int(r.integers(len(EMOJI)))]} {SNS_TAGS[int(r.integers(len(SNS_TAGS)))]}".strip()
            subject = "SNS 投稿"
        else:  # 店頭
            text = f"【店頭】{self.store_name.get(store, '店舗')}にて、お客様より{summary}とのお申し出。\n→ 店長が対応し、本部へ報告。"
            subject = summary[:30]
        if r.random() < 0.08:
            text = text.translate(str.maketrans("0123456789", "０１２３４５６７８９"))
        return subject, text, tpl

    # ------------------------------------------------------------------------------------------
    def build(self, out_dir):
        r = self.rng
        self.collect()
        seeds = sorted(self.seeds, key=lambda s: s["received_at"])
        seeds = [s for s in seeds if config.SUPPORT_START <= s["received_at"].date() <= config.DATA_END]
        vol = pd.Series([s["received_at"].date() for s in seeds]).value_counts()
        med = vol.median()
        rows = []
        seq = {}
        emp = self.emp
        for s in seeds:
            t = s["received_at"]
            ch = self.channel_for(s)
            if ch in ("電話", "チャット", "店頭") and not (10 <= t.hour < 18):
                nd = t.date() + timedelta(days=1 if t.hour >= 18 else 0)
                t = datetime(nd.year, nd.month, nd.day, 10) + timedelta(seconds=int(r.integers(0, 8 * 3600)))
                s["received_at"] = t
            subject, body, tpl = self.render(s, ch)
            d = t.date()
            seq[d] = seq.get(d, 0) + 1
            load = vol.get(d, med) / med
            if ch == "電話":
                fr = t + timedelta(seconds=int(r.integers(20, 300)))
            elif ch == "チャット":
                fr = t + timedelta(seconds=int(r.integers(30, 600) * max(1, load)))
            elif ch == "店頭":
                fr = t
            else:
                hrs = float(r.lognormal(np.log(3.5), 0.8)) * max(1.0, load ** 1.3)
                fr = t + timedelta(hours=hrs)
                if fr.hour >= 19 or fr.hour < 9:
                    nd = fr.date() + timedelta(days=1 if fr.hour >= 19 else 0)
                    fr = datetime(nd.year, nd.month, nd.day, 9) + timedelta(minutes=int(r.integers(0, 180)))
            cat, sub = s["category"], s["subcategory"]
            res_days = {"配送・お届け": (1, 3), "商品品質": (3, 14), "注文・決済": (0.1, 2), "定期便": (0.05, 1),
                        "アプリ・会員": (0.3, 5), "店舗": (0.5, 3), "商品のお問い合わせ": (0.05, 1), "返品・交換": (2, 7),
                        "法人・大口": (1, 3), "ご意見・ご要望": (0.05, 2), "その他": (0.01, 1)}[cat]
            res = float(r.uniform(*res_days))
            if sub == "決済エラー" and date(2026, 9, 16) <= d <= date(2026, 9, 22):
                res = max(res, (datetime(2026, 9, 22, 18) - t).total_seconds() / 86400)
            closed = fr + timedelta(days=res)
            team = tpl["team"]
            escal = cat == "商品品質" and (s.get("lot_id") or sub in ("異物混入",)) or (sub == "決済エラー" and d >= date(2026, 9, 16) and d <= date(2026, 9, 25))
            dept = TEAM_DEPT["カスタマーサポート"] if ch != "店頭" else None
            if escal or team in ("品質保証部", "情報システム", "法人営業部"):
                dept = TEAM_DEPT[team] if team in TEAM_DEPT else TEAM_DEPT["情報システム"]
            if ch == "店頭":
                dept = None
            assignee = None
            if dept:
                a = people.active_on(emp, d, [dept])
                if len(a):
                    assignee = a.iloc[int(r.integers(len(a)))]["employee_id"]
            elif s.get("store_id"):
                a = people.active_on(emp, d, ["D3" + s["store_id"][1:]])
                a = a[a["job_title"].isin(["店長", "副店長"])]
                if len(a):
                    assignee = a.iloc[0]["employee_id"]
            status = "完了"
            if closed.date() > config.DATA_END:
                status = str(r.choice(["対応中", "回答待ち", "エスカレーション" if escal else "対応中"]))
                closed_v = None
            else:
                closed_v = closed
            if fr.date() > config.DATA_END:
                fr_v, status = None, "未対応"
            else:
                fr_v = fr
            if sub == "営業メール・スパム":
                status, assignee = "対応不要", assignee
            csat = None
            if status == "完了" and sub != "営業メール・スパム" and r.random() < 0.3:
                base = 4.3 - 0.35 * min(res, 7) / 2 - (0.8 if cat == "商品品質" else 0) - (0.5 if sub == "決済エラー" else 0) \
                       + (0.4 if sub == "お褒め" else 0) - (0.3 if load > 2 else 0)
                csat = int(np.clip(round(base + r.normal(0, 0.8)), 1, 5))
            pri = "高" if escal else tpl["priority"]
            rows.append(dict(inquiry_id=f"INQ{d:%Y%m%d}-{seq[d]:03d}", received_at=t, channel=ch,
                             customer_id=s.get("customer_id"), order_id=s.get("order_id"), product_id=s.get("product_id")
                             if cat not in ("店舗", "その他", "アプリ・会員") else None, store_id=s.get("store_id"),
                             category=cat, subcategory=sub, subject=subject, body=body, status=status, priority=pri,
                             assigned_team=team, assignee_employee_id=assignee, first_response_at=fr_v, closed_at=closed_v,
                             csat_score=csat, lot_no=s.get("lot_id") if s.get("lot_id") and r.random() < 0.55 else None))
        df = pd.DataFrame(rows)
        df = df.sort_values("received_at", kind="stable").reset_index(drop=True)
        dkey = pd.to_datetime(df["received_at"]).dt.strftime("%Y%m%d")
        df["inquiry_id"] = "INQ" + dkey + "-" + (df.groupby(dkey).cumcount() + 1).astype(str).str.zfill(3)
        # label noise: some tickets were never categorised by agents
        unl = (r.random(len(df)) < 0.12) | ((df["status"] != "完了") & (r.random(len(df)) < 0.6))
        df.loc[unl, ["category", "subcategory"]] = None
        df["received_at"] = pd.to_datetime(df["received_at"])
        for c in ("first_response_at", "closed_at"):
            df[c] = pd.to_datetime(df[c])
        df["csat_score"] = df["csat_score"].astype("Int64")
        out = df.copy()
        for c in ("received_at", "first_response_at", "closed_at"):
            out[c] = out[c].dt.strftime("%Y-%m-%d %H:%M:%S")
        write_csv(out, out_dir / "inquiries.csv")
        with open(out_dir / "inquiries.jsonl", "w", encoding="utf-8", newline="\n") as fh:
            for rec in out.to_dict(orient="records"):
                rec = {k: (None if (isinstance(v, float) and np.isnan(v)) or v is pd.NA else v) for k, v in rec.items()}
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return df


def generate(out_dir, retail, mfg, emp, wx, seed):
    return Support(retail, mfg, emp, wx, seed).build(out_dir)
