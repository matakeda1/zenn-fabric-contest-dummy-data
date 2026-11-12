"""Messy branch forms: daily reports (日報) and purchase orders (発注書) with store-specific layouts.

Every store uses its own layout on purpose (merged cells, cross-tab, weekly blocks, 千円 units, 税抜 amounts,
full-width digits, Japanese era dates, Shift_JIS CSV, missing / duplicated submissions, notation variants).
"""
from __future__ import annotations

import math
from datetime import date, timedelta

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from . import config, people, weather
from .calendar_jp import HOLIDAY_DATES, daterange
from .io_utils import write_csv

REPORT_STORES = ["S01", "S03", "S04", "S08", "S10", "S11", "S15", "S16"]
WD = "月火水木金土日"
THIN = Side(style="thin", color="999999")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
HEAD = PatternFill("solid", fgColor="DDEBF7")
ZEN = str.maketrans("0123456789,", "０１２３４５６７８９，")

SUPPLY = [
    ("SP001", "コーヒー豆 ハウスブレンド（業務用）", "1kg", "袋", 10, 2400, ["ハウスブレンド 1kg", "豆（ハウス）", "ハウスブレンド業務用", "HB 1kg", "ﾊｳｽﾌﾞﾚﾝﾄﾞ"]),
    ("SP002", "コーヒー豆 エスプレッソブレンド（業務用）", "1kg", "袋", 10, 2600, ["エスプレッソ豆", "エスプレッソブレンド", "ESP豆 1kg", "エスプレッソ用"]),
    ("SP003", "コーヒー豆 カフェインレス（業務用）", "500g", "袋", 10, 1700, ["カフェインレス豆", "デカフェ豆", "カフェインレス 500g"]),
    ("SP004", "牛乳", "1L", "本", 12, 230, ["牛乳", "牛乳 1L", "ミルク", "牛乳(1000ml)", "ﾐﾙｸ"]),
    ("SP005", "オーツミルク", "1L", "本", 6, 380, ["オーツミルク", "オーツ", "Oat milk", "オートミルク"]),
    ("SP006", "ホットカップ M", "240ml", "個", 1000, 12, ["ホットカップM", "HOTカップ(M)", "紙コップ M ホット", "ホットカップＭ", "ﾎｯﾄｶｯﾌﾟM"]),
    ("SP007", "ホットカップ L", "360ml", "個", 1000, 14, ["ホットカップL", "HOTカップ(L)", "ホットカップＬ"]),
    ("SP008", "アイスカップ M", "360ml", "個", 1000, 15, ["アイスカップM", "ICEカップ(M)", "プラカップM", "アイスカップＭ"]),
    ("SP009", "アイスカップ L", "480ml", "個", 1000, 17, ["アイスカップL", "ICEカップ(L)", "プラカップL"]),
    ("SP010", "ホット用リッド", "M/L共通", "個", 1000, 5, ["ホット用フタ", "リッド(ホット)", "ホットリッド"]),
    ("SP011", "アイス用リッド", "M/L共通", "個", 1000, 6, ["アイス用フタ", "リッド(アイス)", "アイスリッド", "ドームリッド"]),
    ("SP012", "紙ストロー", "6mm", "本", 2000, 3, ["ストロー", "紙ストロー", "ｽﾄﾛｰ"]),
    ("SP013", "カップスリーブ", "M/L共通", "枚", 1000, 4, ["スリーブ", "カップスリーブ", "ホルダー"]),
    ("SP014", "ガムシロップ", "11g", "個", 500, 4, ["ガムシロ", "ガムシロップ", "シロップ(ガム)"]),
    ("SP015", "コーヒーフレッシュ", "4.5ml", "個", 500, 4, ["フレッシュ", "コーヒーフレッシュ", "ミルクポーション"]),
    ("SP016", "抹茶パウダー", "500g", "袋", 10, 2200, ["抹茶パウダー", "抹茶", "抹茶粉"]),
    ("SP017", "ほうじ茶パウダー", "500g", "袋", 10, 1900, ["ほうじ茶パウダー", "ほうじ茶"]),
    ("SP018", "チャイシロップ", "1L", "本", 6, 1500, ["チャイシロップ", "チャイ"]),
    ("SP019", "チョコレートソース", "1kg", "本", 6, 1300, ["チョコソース", "チョコレートソース"]),
    ("SP020", "パンプキンスパイスシロップ（季節限定）", "750ml", "本", 6, 1600, ["パンプキンシロップ", "パンプキンスパイス", "PSLシロップ"]),
    ("SP021", "クッキー（個包装）", "1枚", "個", 50, 90, ["クッキー", "クッキー個包装", "ｸｯｷｰ"]),
    ("SP022", "フィナンシェ（個包装）", "1個", "個", 40, 105, ["フィナンシェ", "フィナンシエ"]),
    ("SP023", "スコーン（冷凍）", "1個", "個", 30, 120, ["スコーン", "スコーン冷凍"]),
    ("SP024", "紙袋 S", "-", "枚", 500, 8, ["紙袋S", "手提げ袋(小)", "ショッパーS"]),
    ("SP025", "紙袋 M", "-", "枚", 500, 11, ["紙袋M", "手提げ袋(中)", "ショッパーM"]),
    ("SP026", "ペーパーナプキン", "-", "枚", 5000, 1, ["ナプキン", "紙ナプキン", "ペーパーナプキン"]),
]


def cat4(c):
    return {"ドリンク": "ドリンク", "コーヒー豆": "豆・ドリップ", "ドリップバッグ": "豆・ドリップ", "焼き菓子": "焼き菓子"}.get(c, "物販・その他")


def weather_word(text, precip, style, rng):
    w = weather.weather_category(text, precip, 0)
    if style == "symbol":
        return {"晴": "☀", "曇": "☁", "雨": "☂", "雪": "☃"}[w]
    if style == "hira":
        return {"晴": "はれ", "曇": "くもり", "雨": "あめ", "雪": "ゆき"}[w] if rng.random() < 0.7 else {"晴": "晴れ", "曇": "曇り", "雨": "雨", "雪": "雪"}[w]
    if style == "kanji1":
        return w
    base = {"晴": "晴れ", "曇": "曇り", "雨": "雨", "雪": "雪"}[w]
    if rng.random() < 0.2 and w in ("晴", "曇"):
        return base + "時々" + ("曇り" if w == "晴" else "晴れ")
    return base


class Forms:
    def __init__(self, retail, emp, inq, wx, seed):
        self.rng = np.random.default_rng(seed)
        self.rr, self.emp, self.inq = retail, emp, inq
        self.wxd = {k: weather.daily(wx, k) for k in config.STATIONS}
        self.store = {s["store_id"]: s for s in config.STORES}
        h = retail.orders
        st = h[(h["channel"] == "店舗") & (h["order_datetime"] >= "2025-09-01")].copy()
        lines = retail.lines.merge(st[["order_id", "store_id", "order_datetime", "eat_in"]], on="order_id")
        cat = retail.product_df.set_index("product_id")["category"]
        lines["cat4"] = lines["product_id"].map(cat).map(cat4)
        lines["date"] = lines["order_datetime"].dt.date
        lines["hour"] = lines["order_datetime"].dt.hour
        self.lines = lines
        st["date"] = st["order_datetime"].dt.date
        self.daily = st.groupby(["store_id", "date"]).agg(sales=("total_incl_tax", "sum"), sales_ex=("subtotal_excl_tax", "sum"),
                                                          customers=("order_id", "count")).reset_index()
        self.bycat = lines.groupby(["store_id", "date", "cat4"])["line_total"].sum().unstack(fill_value=0)
        self.bycat_ex = lines.groupby(["store_id", "date", "cat4"])["line_subtotal"].sum().unstack(fill_value=0)
        self.records = []

    # ---------------------------------------------------------------------------------------------
    def day_values(self, sid, d):
        r = self.rng
        row = self.daily[(self.daily["store_id"] == sid) & (self.daily["date"] == d)]
        sales = int(row["sales"].iloc[0]) if len(row) else 0
        sales_ex = int(row["sales_ex"].iloc[0]) if len(row) else 0
        cust = int(row["customers"].iloc[0]) if len(row) else 0
        cats = {}
        cats_ex = {}
        for c in ("ドリンク", "豆・ドリップ", "焼き菓子", "物販・その他"):
            cats[c] = int(self.bycat.loc[(sid, d), c]) if (sid, d) in self.bycat.index and c in self.bycat.columns else 0
            cats_ex[c] = int(self.bycat_ex.loc[(sid, d), c]) if (sid, d) in self.bycat_ex.index and c in self.bycat_ex.columns else 0
        py = d.replace(year=d.year - 1) - timedelta(days=(d.replace(year=d.year - 1).weekday() - d.weekday()) % 7 - 0)
        prev = self.daily[(self.daily["store_id"] == sid) & (self.daily["date"] == py)]
        w = self.wxd[self.store[sid]["station"]].loc[pd.Timestamp(d)]
        staff = people.active_on(self.emp, d, ["D3" + sid[1:]])
        writer = staff.iloc[int(r.integers(len(staff)))] if len(staff) else None
        mgr = staff[staff["job_title"] == "店長"]
        mgr = mgr.iloc[0] if len(mgr) else None
        n_staff = int(np.clip(round(len(staff) * r.uniform(0.45, 0.65)), 3, 12)) if len(staff) else 4
        waste_sweets = int(r.poisson(3 + (4 if w["precip_mm"] >= 10 else 0)))
        waste_drink = int(r.poisson(1.2))
        comment = self.comment(sid, d, w, cust)
        v = dict(store_id=sid, date=d, sales=sales, sales_ex=sales_ex, customers=cust, cats=cats, cats_ex=cats_ex,
                 prev_sales=int(prev["sales"].iloc[0]) if len(prev) else None, weather_text=str(w["weather_day"]),
                 precip=float(w["precip_mm"]), tmax=float(w["temp_max_c"]),
                 writer=f"{writer['last_name']}" if writer is not None else "",
                 writer_full=f"{writer['last_name']} {writer['first_name']}" if writer is not None else "",
                 manager=f"{mgr['last_name']}" if mgr is not None else "", n_staff=n_staff,
                 staff_hours=round(n_staff * r.uniform(5.5, 7.5), 1), waste_sweets=waste_sweets, waste_drink=waste_drink,
                 comment=comment, error=None)
        # manual transcription errors (vs POS)
        if r.random() < 0.035 and sales > 0:
            kind = int(r.integers(0, 3))
            s = str(sales)
            if kind == 0 and len(s) >= 4:
                i = int(r.integers(0, len(s) - 1))
                s2 = s[:i] + s[i + 1] + s[i] + s[i + 2:]
                v["sales"], v["error"] = int(s2), "桁の入れ替わり"
            elif kind == 1:
                v["sales"], v["error"] = sales + int(r.choice([-10000, -1000, 1000, 10000])), "金額の入力ミス"
            else:
                v["customers"], v["error"] = cust + int(r.choice([-3, -2, -1, 1, 2, 3])), "客数の入力ミス"
        return v

    def comment(self, sid, d, w, cust):
        r = self.rng
        parts = []
        if w["precip_mm"] >= 30:
            parts.append(str(r.choice(["大雨のため客足が鈍かった。", "雨が強く、夕方以降はほとんど来店なし。", "雨で客数減。テイクアウト中心。"])))
        elif w["precip_mm"] >= 5:
            parts.append(str(r.choice(["雨のため客数やや少なめ。", "午後から雨。", "雨で客足鈍い。"])))
        if w["temp_max_c"] >= 28:
            parts.append(str(r.choice(["暑さでアイスドリンクがよく出た。", "アイスコーヒー・コールドブリューが好調。", "暑い一日。フラッペ完売。"])))
        if d.month == 10 and d.day == 1:
            parts.append("コーヒーの日キャンペーンで豆の購入が多かった。")
        if d in HOLIDAY_DATES or d.weekday() >= 5:
            parts.append(str(r.choice(["週末で混雑。", "家族連れが多かった。", "観光客多め。", ""])))
        q = self.inq[(self.inq["store_id"] == sid) & (self.inq["received_at"].dt.date == d)]
        if len(q):
            parts.append("お客様からご意見あり（本部へ報告済み）。")
        if r.random() < 0.06:
            parts.append(str(r.choice(["エスプレッソマシンの抽出が不安定。メーカーに連絡済み。", "製氷機の調子が悪い。",
                                       "レジの釣銭機エラーが1回発生。", "スタッフ1名欠勤のためシフト調整。", "近隣でイベントがあり混雑。",
                                       "パンプキンスパイスラテの問い合わせ多数。", "スコーン品切れ（15時）。"])))
        return "".join(p for p in parts if p)

    # ---------------------------------------------------------------------------------------------
    def _title(self, ws, rng_, text, size=14):
        ws.merge_cells(rng_)
        c = ws[rng_.split(":")[0]]
        c.value = text
        c.font = Font(bold=True, size=size)
        c.alignment = Alignment(horizontal="center", vertical="center")

    def _box(self, ws, cells):
        for row in ws[cells]:
            for c in row:
                c.border = BOX

    def record(self, v, fmt, path, **extra):
        rec = dict(store_id=v["store_id"], report_date=v["date"], source_file=str(path.relative_to(self.base)).replace("\\", "/"),
                   layout=fmt, weather_reported=extra.get("weather"), amount_basis=extra.get("basis", "税込"),
                   sales_reported_yen=extra.get("sales_yen", v["sales"]), customers_reported=v["customers"],
                   drink_yen=v["cats"]["ドリンク"], beans_drip_yen=v["cats"]["豆・ドリップ"], sweets_yen=v["cats"]["焼き菓子"],
                   others_yen=v["cats"]["物販・その他"], reported_by=v["writer_full"], comment=v["comment"],
                   pos_sales_incl_tax=extra.get("pos_sales"), pos_customers=extra.get("pos_customers"),
                   transcription_error=v["error"], is_superseded=extra.get("superseded", False))
        self.records.append(rec)

    # ---------------------------------------------------------------------------------------------
    def fmt_S01(self, v, out):
        wb = Workbook()
        ws = wb.active
        ws.title = "日報"
        self._title(ws, "A1:F1", "札幌大通店　営業日報")
        d = v["date"]
        wword = weather_word(v["weather_text"], v["precip"], "kanji", self.rng)
        ws["A3"], ws["B3"], ws["C3"], ws["D3"], ws["E3"], ws["F3"] = "日付", d, "曜日", WD[d.weekday()], "天気", wword
        ws["B3"].number_format = "yyyy/m/d"
        ws["A4"], ws["B4"], ws["C4"], ws["D4"] = "記入者", v["writer_full"], "店長確認", "済" if self.rng.random() < 0.8 else ""
        self._title(ws, "A6:D6", "売上実績（税込）", 11)
        ws["A7"], ws["B7"], ws["C7"], ws["D7"] = "区分", "売上金額", "構成比", "前年同曜日"
        tot = v["sales"]
        for i, c in enumerate(["ドリンク", "豆・ドリップ", "焼き菓子", "物販・その他"]):
            ws.cell(8 + i, 1, {"豆・ドリップ": "コーヒー豆・ドリップ", "物販・その他": "物販・その他"}.get(c, c))
            ws.cell(8 + i, 2, v["cats"][c]).number_format = "#,##0"
            ws.cell(8 + i, 3, round(v["cats"][c] / tot, 3) if tot else 0).number_format = "0.0%"
        ws["A12"], ws["B12"] = "合計", tot
        ws["B12"].number_format = "#,##0"
        ws["D12"] = v["prev_sales"] if v["prev_sales"] else "-"
        ws["A14"], ws["B14"], ws["C14"], ws["D14"] = "客数", v["customers"], "客単価", round(tot / v["customers"]) if v["customers"] else 0
        ws["A15"], ws["B15"], ws["C15"], ws["D15"] = "スタッフ", f"{v['n_staff']}人", "総労働時間", v["staff_hours"]
        ws.merge_cells("A17:A18")
        ws["A17"] = "廃棄"
        ws["A17"].alignment = Alignment(vertical="center")
        ws["B17"], ws["C17"] = "焼き菓子", f"{v['waste_sweets']}個"
        ws["B18"], ws["C18"] = "ドリンク", f"{v['waste_drink']}杯"
        ws["A20"] = "特記事項"
        ws.merge_cells("A21:F24")
        ws["A21"] = v["comment"] or "特になし"
        ws["A21"].alignment = Alignment(wrap_text=True, vertical="top")
        self._box(ws, "A7:D12")
        ws.column_dimensions["A"].width = 18
        ws.column_dimensions["B"].width = 14
        p = out / f"日報_札幌大通店_{d:%Y%m%d}.xlsx"
        wb.save(p)
        self.record(v, "A: 1日1ファイル・縦型フォーム", p, weather=wword, pos_sales=v["sales_pos"], pos_customers=v["cust_pos"])

    def fmt_S03(self, vs, out):
        wb = Workbook()
        wb.remove(wb.active)
        for v in vs:
            d = v["date"]
            name = f"{d.month}月{d.day}日" if d.day != 12 else f"{d.month}.{d.day}"
            ws = wb.create_sheet(name)
            ws["A1"] = "渋谷店 日報"
            ws["A1"].font = Font(bold=True, size=14)
            wsym = weather_word(v["weather_text"], v["precip"], "symbol", self.rng)
            ws["A2"] = f"日付：{d.year}年{d.month}月{d.day}日（{WD[d.weekday()]}）　天気：{wsym} {weather_word(v['weather_text'], v['precip'], 'kanji1', self.rng)}　記入：{v['writer']}"
            ws.merge_cells("A4:A5")
            ws["A4"] = "時間帯"
            ws.merge_cells("B4:E4")
            ws["B4"] = "売上（税込）"
            ws.merge_cells("F4:F5")
            ws["F4"] = "客数"
            for i, h in enumerate(["店内", "テイクアウト", "物販", "計"]):
                ws.cell(5, 2 + i, h)
            for c in ("A4", "B4", "F4"):
                ws[c].alignment = Alignment(horizontal="center", vertical="center")
                ws[c].fill = HEAD
            L = self.lines[(self.lines["store_id"] == "S03") & (self.lines["date"] == d)]
            O = L.drop_duplicates("order_id")
            bands = [("〜11時", 0, 11), ("11〜14時", 11, 14), ("14〜17時", 14, 17), ("17時〜", 17, 24)]
            tot = [0, 0, 0, 0, 0]
            for i, (lab, a, b) in enumerate(bands):
                x = L[(L["hour"] >= a) & (L["hour"] < b)]
                eat = int(x[(x["eat_in"] == "店内") & x["cat4"].isin(["ドリンク", "焼き菓子"])]["line_total"].sum())
                take = int(x[(x["eat_in"] != "店内") & x["cat4"].isin(["ドリンク", "焼き菓子"])]["line_total"].sum())
                goods = int(x[~x["cat4"].isin(["ドリンク", "焼き菓子"])]["line_total"].sum())
                cust = int(((O["hour"] >= a) & (O["hour"] < b)).sum())
                vals = [eat, take, goods, eat + take + goods, cust]
                ws.cell(6 + i, 1, lab)
                for j, val in enumerate(vals):
                    ws.cell(6 + i, 2 + j, val).number_format = "#,##0"
                    tot[j] += val
            ws.cell(10, 1, "合計")
            for j, val in enumerate(tot):
                ws.cell(10, 2 + j, val).number_format = "#,##0"
            if v["error"] == "桁の入れ替わり" or v["error"] == "金額の入力ミス":
                ws.cell(10, 5, v["sales"])
            if v["error"] == "客数の入力ミス":
                ws.cell(10, 6, v["customers"])
            self._box(ws, "A4:F10")
            ws["A12"] = "コメント"
            ws.merge_cells("B12:F14")
            ws["B12"] = v["comment"] or ""
            ws["B12"].alignment = Alignment(wrap_text=True, vertical="top")
            ws.column_dimensions["A"].width = 12
            self.record(v, "B: 月次ブック・日別シート（時間帯×売上区分）", out / "【渋谷店】日報_2026年10月.xlsx",
                        weather=wsym, pos_sales=v["sales_pos"], pos_customers=v["cust_pos"])
        wb.save(out / "【渋谷店】日報_2026年10月.xlsx")

    def fmt_S04(self, vs, out):
        wb = Workbook()
        ws = wb.active
        ws.title = "10月"
        ws["A1"] = "令和8年10月 新宿店 売上日報"
        ws["A1"].font = Font(bold=True, size=14)
        heads = ["項目"] + [str(v["date"].day) for v in vs] + ["月計"]
        for j, h in enumerate(heads):
            c = ws.cell(3, 1 + j, h)
            c.fill = HEAD
        items = ["曜日", "天気", "売上（円）", "客数", "客単価", "ドリンク", "豆・ドリップ", "菓子", "その他", "予算", "予算比"]
        budget_month = sum(v["sales_pos"] for v in vs) * self.rng.uniform(0.97, 1.05)
        wsum = [1.1 if v["date"].weekday() >= 5 else 0.96 for v in vs]
        for i, it in enumerate(items):
            ws.cell(4 + i, 1, it)
        tot = dict(s=0, c=0, d=0, b=0, k=0, o=0, bu=0)
        for j, v in enumerate(vs):
            col = 2 + j
            bud = int(round(budget_month * wsum[j] / sum(wsum), -3))
            vals = [WD[v["date"].weekday()], weather_word(v["weather_text"], v["precip"], "kanji1", self.rng), v["sales"],
                    v["customers"], round(v["sales"] / v["customers"]) if v["customers"] else 0, v["cats"]["ドリンク"],
                    v["cats"]["豆・ドリップ"], v["cats"]["焼き菓子"], v["cats"]["物販・その他"], bud,
                    f"{v['sales'] / bud * 100:.1f}%" if bud else "-"]
            for i, val in enumerate(vals):
                c = ws.cell(4 + i, col, val)
                if isinstance(val, int):
                    c.number_format = "#,##0"
            tot["s"] += v["sales"]
            tot["c"] += v["customers"]
            tot["bu"] += bud
            self.record(v, "C: 月次・横持ち（日付が列）", out / "新宿店 売上日報 R8.10.xlsx", weather=vals[1],
                        pos_sales=v["sales_pos"], pos_customers=v["cust_pos"])
        mc = 2 + len(vs)
        ws.cell(6, mc, tot["s"]).number_format = "#,##0"
        ws.cell(7, mc, tot["c"]).number_format = "#,##0"
        ws.cell(13, mc, tot["bu"]).number_format = "#,##0"
        ws.cell(16, 1, "備考")
        for j, v in enumerate(vs):
            if v["comment"]:
                ws.cell(16, 2 + j, v["comment"]).alignment = Alignment(wrap_text=True, vertical="top")
        ws.column_dimensions["A"].width = 12
        self._box(ws, f"A3:{ws.cell(14, mc).coordinate}")
        wb.save(out / "新宿店 売上日報 R8.10.xlsx")

    def fmt_S08(self, v, out):
        wb = Workbook()
        ws = wb.active
        ws.title = "report"
        d = v["date"]
        k = lambda x: round(x / 1000, 1)  # noqa: E731
        rows = [("Date", d.strftime("%Y-%m-%d")), ("Store", "名古屋栄店 (S08)"),
                ("Weather", weather_word(v["weather_text"], v["precip"], "symbol", self.rng)), ("Max temp", f"{v['tmax']:.0f}℃"),
                ("Sales (千円)", k(v["sales"])), ("Customers", v["customers"]), ("Drink (千円)", k(v["cats"]["ドリンク"])),
                ("Beans/Drip (千円)", k(v["cats"]["豆・ドリップ"])), ("Sweets (千円)", k(v["cats"]["焼き菓子"])),
                ("Others (千円)", k(v["cats"]["物販・その他"])), ("Staff", v["n_staff"]), ("Writer", v["writer"]), ("Memo", v["comment"])]
        for i, (a, b) in enumerate(rows):
            ws.cell(1 + i, 1, a).font = Font(bold=True)
            ws.cell(1 + i, 2, b)
        ws.column_dimensions["A"].width = 18
        ws.column_dimensions["B"].width = 40
        p = out / f"daily_report_S08_{d:%Y-%m-%d}.xlsx"
        wb.save(p)
        self.record(v, "D: 1日1ファイル・英語見出し・千円単位", p, weather=rows[2][1], sales_yen=int(round(k(v["sales"]) * 1000)),
                    pos_sales=v["sales_pos"], pos_customers=v["cust_pos"])

    def fmt_S10(self, v, out):
        wb = Workbook()
        ws = wb.active
        ws.title = "Sheet1"
        d = v["date"]
        self._title(ws, "A1:E1", "京都四条店　日報")
        ws["A2"] = "※金額はすべて税抜"
        ws["A2"].font = Font(color="C00000", size=9)
        ws["A3"], ws["B3"] = "日付", f"R8.{d.month}.{d.day}"
        wword = weather_word(v["weather_text"], v["precip"], "hira", self.rng)
        ws["C3"], ws["D3"] = "天気", wword
        sales_ex = v["sales_ex"] if v["error"] is None else int(round(v["sales"] / 1.085))
        zen = self.rng.random() < 0.35
        fmt = lambda x: (f"{x:,}円".translate(ZEN) if zen else f"{x:,}円")  # noqa: E731
        ws["A5"], ws["B5"] = "売上", fmt(sales_ex)
        ws["A6"], ws["B6"] = "客数", f"{v['customers']}人"
        inbound = int(v["customers"] * self.rng.uniform(0.18, 0.42))
        ws["C6"], ws["D6"] = "うち外国人客", f"{inbound}人"
        ws["A8"] = "内訳"
        for i, c in enumerate(["ドリンク", "豆・ドリップ", "焼き菓子", "物販・その他"]):
            ws.cell(9 + i, 1, c)
            ws.cell(9 + i, 2, fmt(v["cats_ex"][c]))
        ws["A14"] = "所感"
        ws.merge_cells("A15:E18")
        ws["A15"] = v["comment"] or "特になし"
        ws["A15"].alignment = Alignment(wrap_text=True, vertical="top")
        ws["D20"] = f"記入者：{v['writer']}"
        p = out / f"【京都四条店】日報 {d.month}.{d.day}.xlsx"
        wb.save(p)
        self.record(v, "E: 税抜・全角数字・和暦", p, weather=wword, basis="税抜", sales_yen=sales_ex,
                    pos_sales=v["sales_pos"], pos_customers=v["cust_pos"])

    def fmt_S11(self, vs, out):
        weeks = [vs[i:i + 7] for i in range(0, len(vs), 7)]
        for wk in weeks:
            wb = Workbook()
            ws = wb.active
            ws.title = "週報"
            a, b = wk[0]["date"], wk[-1]["date"]
            ws["A1"] = f"梅田店　週報（{a.month}/{a.day}〜{b.month}/{b.day}）"
            ws["A1"].font = Font(bold=True, size=13)
            row = 3
            items = [("売上", "sales"), ("客数", "customers"), ("ドリンク", "ドリンク"), ("豆・ドリップ", "豆・ドリップ"),
                     ("焼き菓子", "焼き菓子"), ("天気", "w")]
            for v in wk:
                d = v["date"]
                ws.merge_cells(start_row=row, start_column=1, end_row=row + len(items) - 1, end_column=1)
                c = ws.cell(row, 1, f"{d.month}/{d.day}\n({WD[d.weekday()]})")
                c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
                c.fill = HEAD
                wword = weather_word(v["weather_text"], v["precip"], "kanji", self.rng)
                for i, (lab, key) in enumerate(items):
                    ws.cell(row + i, 2, lab)
                    if key in ("sales", "customers"):
                        val = v[key]
                    elif key == "w":
                        val = wword
                    else:
                        val = v["cats"][key]
                    ws.cell(row + i, 3, val)
                    if isinstance(val, int):
                        ws.cell(row + i, 3).number_format = "#,##0"
                if v["comment"]:
                    ws.merge_cells(start_row=row, start_column=4, end_row=row + len(items) - 1, end_column=6)
                    ws.cell(row, 4, v["comment"]).alignment = Alignment(wrap_text=True, vertical="top")
                self._box(ws, f"A{row}:C{row + len(items) - 1}")
                row += len(items) + 1
                self.record(v, "F: 週報・日付縦結合ブロック", out / f"梅田店_週報_{a:%m%d}-{b:%m%d}.xlsx", weather=wword,
                            pos_sales=v["sales_pos"], pos_customers=v["cust_pos"])
            ws.cell(row, 1, "週計").font = Font(bold=True)
            ws.cell(row, 3, sum(v["sales"] for v in wk)).number_format = "#,##0"
            ws.column_dimensions["A"].width = 10
            ws.column_dimensions["D"].width = 40
            wb.save(out / f"梅田店_週報_{a:%m%d}-{b:%m%d}.xlsx")

    def fmt_S15(self, v, out, suffix="", superseded=False):
        wb = Workbook()
        ws = wb.active
        ws.title = "日報"
        d = v["date"]
        ws.merge_cells("A1:B3")
        ws["A1"] = "Contoso Coffee"
        ws["A1"].font = Font(bold=True, color="6B4226", size=16)
        ws["A1"].alignment = Alignment(vertical="center")
        for i, lab in enumerate(["店長", "SV", "本部"]):
            col = 6 + i
            ws.cell(1, col, lab).alignment = Alignment(horizontal="center")
            ws.merge_cells(start_row=2, start_column=col, end_row=3, end_column=col)
            ws.cell(2, col, v["manager"] if i == 0 and self.rng.random() < 0.85 else "")
            self._box(ws, f"{ws.cell(1, col).coordinate}:{ws.cell(3, col).coordinate}")
        ws["A5"] = f"福岡天神店　日報　{d.year}年{d.month}月{d.day}日（{WD[d.weekday()]}）"
        ws["A5"].font = Font(bold=True, size=12)
        wword = weather_word(v["weather_text"], v["precip"], "kanji", self.rng)
        hdr = ["天気", "売上（税込）", "客数", "客単価", "ドリンク", "豆・ドリップ", "焼き菓子", "物販その他"]
        for j, h in enumerate(hdr):
            c = ws.cell(10, 1 + j, h)
            c.fill = HEAD
        vals = [wword, v["sales"], v["customers"], round(v["sales"] / v["customers"]) if v["customers"] else 0,
                v["cats"]["ドリンク"], v["cats"]["豆・ドリップ"], v["cats"]["焼き菓子"], v["cats"]["物販・その他"]]
        for j, val in enumerate(vals):
            c = ws.cell(11, 1 + j, val)
            if isinstance(val, int):
                c.number_format = "#,##0"
        self._box(ws, "A10:H11")
        ws["A13"] = "連絡事項"
        ws.merge_cells("A14:H17")
        ws["A14"] = v["comment"] or ""
        ws["A14"].alignment = Alignment(wrap_text=True, vertical="top")
        ws["A19"] = f"記入者：{v['writer_full']}"
        p = out / f"福岡天神店_日報_{d:%Y%m%d}{suffix}.xlsx"
        wb.save(p)
        self.record(v, "G: 承認欄付き・表が10行目から", p, weather=wword, pos_sales=v["sales_pos"], pos_customers=v["cust_pos"],
                    superseded=superseded)

    def fmt_S16(self, vs, out):
        rows = []
        for v in vs:
            d = v["date"]
            w = weather_word(v["weather_text"], v["precip"], "kanji1", self.rng)
            rows.append([f"{d.year}/{d.month}/{d.day}", w, f"{v['sales']:,}", v["customers"], f"{v['cats']['ドリンク']:,}",
                         f"{v['cats']['豆・ドリップ']:,}", f"{v['cats']['焼き菓子']:,}", f"{v['cats']['物販・その他']:,}",
                         (v["comment"] or "").replace("〜", "-")])
            self.record(v, "H: CSV（Shift_JIS）", out / "naha_daily_202610.csv", weather=w, pos_sales=v["sales_pos"],
                        pos_customers=v["cust_pos"])
        df = pd.DataFrame(rows, columns=["日付", "天気", "売上", "客数", "ドリンク", "豆", "菓子", "その他", "メモ"])
        df.to_csv(out / "naha_daily_202610.csv", index=False, encoding="cp932", errors="replace")

    # ---------------------------------------------------------------------------------------------
    def daily_reports(self, base):
        r = self.rng
        self.base = base
        out_root = base / "daily_reports"
        days = list(daterange(config.EXCEL_DAILY_START, config.DATA_END))
        for sid in REPORT_STORES:
            folder = {"S01": "S01_sapporo", "S03": "S03_shibuya", "S04": "S04_shinjuku", "S08": "S08_nagoya", "S10": "S10_kyoto",
                      "S11": "S11_umeda", "S15": "S15_fukuoka", "S16": "S16_naha"}[sid]
            out = out_root / folder
            out.mkdir(parents=True, exist_ok=True)
            vs = []
            for d in days:
                v = self.day_values(sid, d)
                v["sales_pos"] = int(self.daily[(self.daily["store_id"] == sid) & (self.daily["date"] == d)]["sales"].sum())
                v["cust_pos"] = int(self.daily[(self.daily["store_id"] == sid) & (self.daily["date"] == d)]["customers"].sum())
                vs.append(v)
            if sid == "S01":
                for v in vs:
                    self.fmt_S01(v, out)
            elif sid == "S03":
                self.fmt_S03(vs, out)
            elif sid == "S04":
                self.fmt_S04(vs, out)
            elif sid == "S08":
                for v in vs:
                    self.fmt_S08(v, out)
            elif sid == "S10":
                for v in vs:
                    if v["date"] == date(2026, 10, 19):
                        continue  # not submitted
                    self.fmt_S10(v, out)
            elif sid == "S11":
                self.fmt_S11(vs, out)
            elif sid == "S15":
                for v in vs:
                    if v["date"] in (date(2026, 10, 18), date(2026, 10, 25)):
                        continue  # not submitted
                    if v["date"] == date(2026, 10, 10):
                        bad = dict(v)
                        bad["sales"] = v["sales"] + 10000
                        bad["error"] = "金額の入力ミス（修正版で訂正）"
                        self.fmt_S15(bad, out, superseded=True)
                        v = dict(v)
                        v["error"] = None
                        v["sales"] = v["sales_pos"]
                        self.fmt_S15(v, out, suffix="(修正版)")
                        continue
                    self.fmt_S15(v, out)
            elif sid == "S16":
                self.fmt_S16(vs, out)
            print(f"    daily reports {sid}", flush=True)

    # ---------------------------------------------------------------------------------------------
    def purchase_orders(self, base):
        r = self.rng
        out_root = base / "purchase_orders"
        L = self.lines
        po_recs = []
        for sid in REPORT_STORES:
            folder = {"S01": "S01_sapporo", "S03": "S03_shibuya", "S04": "S04_shinjuku", "S08": "S08_nagoya", "S10": "S10_kyoto",
                      "S11": "S11_umeda", "S15": "S15_fukuoka", "S16": "S16_naha"}[sid]
            out = out_root / folder
            out.mkdir(parents=True, exist_ok=True)
            staff = people.active_on(self.emp, date(2026, 10, 1), ["D3" + sid[1:]])
            order_days = [d for d in daterange(config.EXCEL_PO_START, config.DATA_END) if d.weekday() in (0, 3)]
            month_book = {}
            seq = 0
            for d in order_days:
                seq += 1
                win = L[(L["store_id"] == sid) & (L["date"] >= d - timedelta(days=4)) & (L["date"] < d)]
                pidq = win.groupby("product_id")["quantity"].sum()
                hot = int(pidq.reindex(["P030", "P032", "P034", "P035", "P036", "P038", "P039", "P040", "P041", "P044", "P045", "P046"]).fillna(0).sum())
                ice = int(pidq.reindex(["P031", "P033", "P037", "P042"]).fillna(0).sum())
                latte = int(pidq.reindex(["P032", "P033", "P036", "P038", "P039", "P040", "P044", "P045"]).fillna(0).sum())
                need = {"SP001": hot * 0.012, "SP002": latte * 0.018 + 1, "SP004": latte * 0.22, "SP005": int(pidq.get("P046", 0)) * 0.25 + 1,
                        "SP006": hot * 0.75, "SP008": ice * 0.8, "SP010": hot * 0.8, "SP011": ice * 0.8, "SP012": ice,
                        "SP014": ice * 0.4, "SP021": int(pidq.reindex(["P050", "P051"]).fillna(0).sum()) * 0.9,
                        "SP022": int(pidq.get("P052", 0)) * 0.9, "SP023": int(pidq.get("P054", 0)) * 0.9,
                        "SP016": int(pidq.get("P038", 0)) * 0.02, "SP020": int(pidq.get("P044", 0)) * 0.03,
                        "SP024": len(win["order_id"].unique()) * 0.25, "SP026": len(win["order_id"].unique()) * 1.2}
                items = []
                for code, name, spec, unit, case, price, variants in SUPPLY:
                    q = need.get(code, 0)
                    if code in ("SP007", "SP009", "SP013", "SP015", "SP017", "SP018", "SP019", "SP025", "SP003") and r.random() < 0.25:
                        q = case * 0.6
                    if q <= 0:
                        continue
                    if unit in ("個", "枚", "本") and case >= 100:
                        cases = max(1, math.ceil(q / case))
                        qty, u = cases, "ケース"
                    elif unit == "本" and code in ("SP004", "SP005"):
                        qty, u = max(1, math.ceil(q / case)), "ケース"
                    else:
                        qty, u = max(1, math.ceil(q)), unit
                    items.append(dict(code=code, name=name, spec=spec, unit_master=unit, case=case, qty=qty, unit=u,
                                      variant=variants[int(r.integers(len(variants)))]))
                if not items:
                    continue
                writer = staff.iloc[int(r.integers(len(staff)))] if len(staff) else None
                po_no = {"S01": f"S01-{d:%m%d}", "S03": f"PO-S03-{d:%Y%m%d}", "S04": f"新宿-{seq:03d}", "S08": f"PO-S08-{d:%Y%m%d}",
                         "S10": f"京{d:%m%d}", "S11": f"PO-S11-{d:%Y%m%d}", "S15": f"PO-S15-{d:%Y%m%d}", "S16": f"NAHA{seq:03d}"}[sid]
                deliver = d + timedelta(days=2 if sid not in ("S01", "S16") else 3)
                for it in items:
                    po_recs.append(dict(store_id=sid, po_number=po_no, order_date=d, requested_delivery_date=deliver,
                                        item_code=it["code"], item_name_written=it["variant"] if sid in ("S01", "S10", "S16", "S04") else it["name"],
                                        quantity_written=it["qty"], unit_written=it["unit"],
                                        quantity_in_master_unit=it["qty"] * (it["case"] if it["unit"] == "ケース" else 1),
                                        master_unit=it["unit_master"], ordered_by=f"{writer['last_name']} {writer['first_name']}" if writer is not None else ""))
                if sid in ("S03", "S08", "S11", "S15"):
                    self.po_v2(out, sid, d, po_no, deliver, items, writer)
                elif sid in ("S01", "S10"):
                    self.po_v1(out, sid, d, po_no, deliver, items, writer)
                elif sid == "S04":
                    month_book.setdefault(d.month, []).append((d, po_no, deliver, items, writer))
                else:
                    self.po_naha(out, d, po_no, deliver, items, writer)
            for m, lst in month_book.items():
                self.po_shinjuku(out, m, lst)
            print(f"    purchase orders {sid}", flush=True)
        return pd.DataFrame(po_recs)

    def po_v2(self, out, sid, d, po_no, deliver, items, writer):
        wb = Workbook()
        ws = wb.active
        ws.title = "発注書"
        self._title(ws, "A1:G1", "発　注　書", 16)
        ws["F2"] = "様式 HQ-PO v2"
        ws["F2"].font = Font(size=8, color="808080")
        meta = [("発注書番号", po_no), ("発注日", d), ("店舗", f"{self.store[sid]['store_name']}（{sid}）"),
                ("発注者", f"{writer['last_name']} {writer['first_name']}" if writer is not None else ""), ("納品希望日", deliver)]
        for i, (a, b) in enumerate(meta):
            ws.cell(3 + i, 1, a).fill = HEAD
            ws.merge_cells(start_row=3 + i, start_column=2, end_row=3 + i, end_column=4)
            c = ws.cell(3 + i, 2, b)
            if isinstance(b, date):
                c.number_format = "yyyy/mm/dd"
        hdr = ["No", "品目コード", "品名", "規格", "数量", "単位", "備考"]
        for j, h in enumerate(hdr):
            ws.cell(9, 1 + j, h).fill = HEAD
        for i, it in enumerate(items):
            code = it["code"] if self.rng.random() > 0.12 else ""
            vals = [i + 1, code, it["name"], it["spec"], it["qty"], it["unit"], "至急" if self.rng.random() < 0.04 else ""]
            for j, val in enumerate(vals):
                ws.cell(10 + i, 1 + j, val)
        self._box(ws, f"A9:G{9 + len(items)}")
        ws.column_dimensions["C"].width = 36
        wb.save(out / f"発注書_{sid}_{d:%Y%m%d}.xlsx")

    def po_v1(self, out, sid, d, po_no, deliver, items, writer):
        wb = Workbook()
        ws = wb.active
        ws.title = "Sheet1"
        ws["A1"] = f"{self.store[sid]['store_name']}　発注表"
        ws["A1"].font = Font(bold=True, size=13)
        ws["A2"] = f"発注日 {d.month}/{d.day}　納品希望 {deliver.month}/{deliver.day}　担当 {writer['last_name'] if writer is not None else ''}"
        ws["A4"], ws["B4"], ws["C4"] = "品名", "数量", "メモ"
        for c in ("A4", "B4", "C4"):
            ws[c].fill = HEAD
        for i, it in enumerate(items):
            u = {"ケース": str(self.rng.choice(["ケース", "cs", "c/s", "箱"])), "袋": "袋", "本": "本", "個": "個", "枚": "枚"}.get(it["unit"], it["unit"])
            q = f"{it['qty']}{u}"
            if self.rng.random() < 0.15:
                q = q.translate(ZEN)
            ws.cell(5 + i, 1, it["variant"])
            ws.cell(5 + i, 2, q)
        ws.column_dimensions["A"].width = 28
        wb.save(out / f"{sid}_発注_{d:%m%d}.xlsx")

    def po_shinjuku(self, out, month, lst):
        wb = Workbook()
        wb.remove(wb.active)
        for d, po_no, deliver, items, writer in lst:
            ws = wb.create_sheet(f"{d:%m%d}")
            ws["A1"] = f"新宿店 発注（{po_no}）"
            ws["A2"], ws["B2"] = "発注日", d
            ws["B2"].number_format = "m月d日"
            ws["A3"], ws["B3"] = "納品日", deliver
            ws["B3"].number_format = "m月d日"
            ws.merge_cells("A5:B5")
            ws["A5"] = "ドリンク資材"
            ws.merge_cells("C5:D5")
            ws["C5"] = "食材・その他"
            left = [it for it in items if it["code"] in ("SP006", "SP007", "SP008", "SP009", "SP010", "SP011", "SP012", "SP013", "SP024", "SP025", "SP026")]
            right = [it for it in items if it not in left]
            for i, it in enumerate(left):
                ws.cell(6 + i, 1, it["variant"])
                ws.cell(6 + i, 2, f"{it['qty']}{'cs' if it['unit'] == 'ケース' else it['unit']}")
            for i, it in enumerate(right):
                ws.cell(6 + i, 3, it["variant"])
                ws.cell(6 + i, 4, it["qty"])
                ws.cell(6 + i, 5, it["unit"])
            ws.column_dimensions["A"].width = 22
            ws.column_dimensions["C"].width = 26
        wb.save(out / f"新宿店_発注_2026年{month}月.xlsx")

    def po_naha(self, out, d, po_no, deliver, items, writer):
        wb = Workbook()
        ws = wb.active
        ws.title = "order"
        ws["A1"] = "那覇国際通り店 Order Sheet"
        ws["A2"] = f"No. {po_no} / {d:%Y.%m.%d} / 納品 {deliver:%m/%d}"
        ws["A4"], ws["B4"], ws["C4"] = "Item", "Qty", "Unit"
        for i, it in enumerate(items):
            ws.cell(5 + i, 1, it["variant"])
            ws.cell(5 + i, 2, it["qty"] if self.rng.random() > 0.2 else str(it["qty"]).translate(ZEN))
            ws.cell(5 + i, 3, "cs" if it["unit"] == "ケース" else it["unit"])
        wb.save(out / f"naha_order_{d:%Y%m%d}.xlsx")

    # ---------------------------------------------------------------------------------------------
    def run(self, base, organizer_dir):
        self.daily_reports(base)
        po = self.purchase_orders(base)
        master = pd.DataFrame([dict(item_code=c, item_name=n, spec=s, unit=u, case_quantity=q, unit_price=p)
                               for c, n, s, u, q, p, _ in SUPPLY])
        write_csv(master, base / "master" / "supply_items.csv")
        st = pd.DataFrame([dict(store_id=s, store_name=self.store[s]["store_name"]) for s in REPORT_STORES])
        write_csv(st, base / "master" / "report_stores.csv")
        dr = pd.DataFrame(self.records)
        organizer_dir.mkdir(parents=True, exist_ok=True)
        write_csv(dr, organizer_dir / "daily_reports_expected.csv")
        write_csv(po, organizer_dir / "purchase_orders_expected.csv")
        n_files = sum(1 for _ in base.rglob("*") if _.is_file())
        return dict(daily_records=len(dr), po_lines=len(po), files=n_files)


def generate(base, organizer_dir, retail, emp, inq, wx, seed):
    return Forms(retail, emp, inq, wx, seed).run(base, organizer_dir)
