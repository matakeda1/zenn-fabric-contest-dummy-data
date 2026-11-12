"""Sales & marketing (B2B office coffee service): campaigns, ad spend, leads, opportunities, stage history, orders."""
from __future__ import annotations

from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

from . import config, people
from .calendar_jp import HOLIDAY_DATES, daterange, fiscal_year
from .io_utils import write_csv

PREFIX = ("カナメ ソラシド ハルカ イロハ ナギサ トキワ シラユリ アカツキ ユズリハ カスミ ワカバ ミドリノ セイラン コハク ルリ ヒスイ "
          "アマネ ツムギ サンゴ ホタル カエデ ツクシ スミレ リンドウ キキョウ ナデシコ アヤメ 東雲 青葉 若葉 桜丘 緑川 朝霧 白鷺 "
          "北斗 南風 早瀬 高嶺 星川 月岡 花園 雪村 水城 黒潮 千歳 八雲 紫苑 銀河 翠嶺 灯台 港北 西陣 浜風 山吹 菖蒲 "
          "ミモザ ルピナス アズサ コトブキ ヒバリ ツグミ カモメ ミズホ ユウナギ アサツユ 白樺 楓林 瑞穂 七海 天城 葵台 "
          "清澄 若竹 椿 柊 蒼天 暁星").split()
SUFFIX = [("精機", "製造業"), ("工業", "製造業"), ("電機", "製造業"), ("食品", "製造業"), ("商事", "卸売・商社"),
          ("物産", "卸売・商社"), ("システムズ", "情報通信"), ("ソリューションズ", "情報通信"), ("テクノロジー", "情報通信"),
          ("ソフトウェア", "情報通信"), ("建設", "建設"), ("設計", "建設"), ("不動産", "不動産"), ("物流", "運輸・物流"),
          ("運輸", "運輸・物流"), ("メディカル", "医療・福祉"), ("クリニック", "医療・福祉"), ("会計事務所", "専門サービス"),
          ("法律事務所", "専門サービス"), ("コンサルティング", "専門サービス"), ("人材サービス", "専門サービス"),
          ("デザイン", "メディア・広告"), ("広告", "メディア・広告"), ("出版", "メディア・広告"), ("保険サービス", "金融・保険"),
          ("ホテル", "宿泊・飲食"), ("ダイニング", "宿泊・飲食"), ("学園", "教育・保育"), ("保育園", "教育・保育")]
BANDS = ["1-9名", "10-49名", "50-99名", "100-299名", "300-999名", "1000名以上"]
BAND_P = [0.12, 0.30, 0.20, 0.20, 0.12, 0.06]
DEPTS = ["総務部", "人事部", "経営企画部", "情報システム部", "営業部", "その他"]
LEVELS = ["担当者", "主任・係長", "課長", "部長", "役員", "経営者"]
STAGES = ["初回訪問", "ヒアリング", "提案", "見積提示", "交渉"]
STAGE_PROB = {"初回訪問": 10, "ヒアリング": 20, "提案": 40, "見積提示": 60, "交渉": 80}
PLANS = {"ライト": 15000, "スタンダード": 32000, "プレミアム": 58000}
COMPETITORS = ["ノースウィンド・コーヒーサービス", "ウッドグローブ・ベンディング", "フォースコーヒー", "自社購入（量販店）"]
BRANCH_OF_REGION = {"北海道": "D200", "東北": "D200", "関東": "D201", "中部": "D211", "近畿": "D210", "中国": "D210",
                    "四国": "D210", "九州": "D212", "九州・沖縄": "D212"}

CONV = {"検索広告": 0.20, "SNS広告": 0.06, "ビジネスSNS広告": 0.14, "展示会": 0.22, "ウェビナー": 0.16,
        "ホワイトペーパー": 0.08, "テレアポ": 0.18, "紹介": 0.45, "自然検索": 0.24, "問い合わせ（CS経由）": 0.35, "不明": 0.15}


def _campaigns():
    C = []

    def add(name, channel, media, start, end, budget, target="全業種", size="10名以上", objective="リード獲得"):
        C.append(dict(campaign_name=name, channel=channel, media=media, start_date=date.fromisoformat(start),
                      end_date=date.fromisoformat(end), budget_jpy=budget, target_industry=target, target_company_size=size,
                      objective=objective))

    qs = [("FY24Q3", "2024-11-01", "2024-12-31"), ("FY24Q4", "2025-01-01", "2025-03-31"), ("FY25Q1", "2025-04-01", "2025-06-30"),
          ("FY25Q2", "2025-07-01", "2025-09-30"), ("FY25Q3", "2025-10-01", "2025-12-31"), ("FY25Q4", "2026-01-01", "2026-03-31"),
          ("FY26Q1", "2026-04-01", "2026-06-30"), ("FY26Q2", "2026-07-01", "2026-09-30"), ("FY26Q3", "2026-10-01", "2026-12-31")]
    for q, a, b in qs:
        days = (date.fromisoformat(b) - date.fromisoformat(a)).days + 1
        add(f"検索広告 Google {q}", "検索広告", "Google 広告", a, b, 22000 * days)
        add(f"検索広告 Yahoo! {q}", "検索広告", "Yahoo! 広告", a, b, 8000 * days)
    for a, b, nm in [("2024-11-05", "2024-12-15", "年末オフィスリフレッシュ"), ("2025-03-01", "2025-04-15", "新年度オフィス"),
                     ("2025-09-01", "2025-10-15", "秋の福利厚生見直し"), ("2026-03-01", "2026-04-15", "新年度オフィス 2026"),
                     ("2026-09-01", "2026-10-15", "秋の福利厚生見直し 2026")]:
        days = (date.fromisoformat(b) - date.fromisoformat(a)).days + 1
        add(f"SNS広告 Meta {nm}", "SNS広告", "Meta 広告", a, b, 15000 * days, size="10-299名", objective="認知・リード獲得")
    for a, b in [("2025-05-12", "2025-06-30"), ("2025-08-01", "2025-09-30"), ("2026-05-11", "2026-06-30")]:
        days = (date.fromisoformat(b) - date.fromisoformat(a)).days + 1
        add(f"ビジネスSNS広告 LinkedIn {a[:7]}", "ビジネスSNS広告", "LinkedIn 広告", a, b, 20000 * days, target="情報通信・専門サービス",
            size="50名以上")
    for nm, a, b, bud in [("オフィス環境EXPO 東京 2025春", "2025-04-16", "2025-04-18", 2600000),
                          ("関西オフィス・総務展 2025秋", "2025-10-08", "2025-10-10", 2100000),
                          ("オフィス環境EXPO 東京 2026春", "2026-04-15", "2026-04-17", 2800000),
                          ("名古屋ビジネスフェア 2026", "2026-07-08", "2026-07-09", 1500000)]:
        add(nm, "展示会", "展示会", a, b, bud, objective="リード獲得・商談化")
    webinars = [("2024-12-11", "社員満足度を上げるオフィスコーヒー活用術"), ("2025-02-19", "出社したくなるオフィスづくり"),
                ("2025-05-21", "福利厚生としてのコーヒー：導入事例紹介"), ("2025-07-16", "総務担当者のためのオフィス飲料コスト最適化"),
                ("2025-09-17", "サステナブルなオフィスコーヒー"), ("2025-11-12", "年末年始の差し入れ・ギフト活用"),
                ("2026-02-18", "新年度に向けたオフィス環境整備"), ("2026-06-17", "コーヒーで変わる会議と雑談"),
                ("2026-09-16", "データで見るオフィスコーヒー導入効果")]
    for d, nm in webinars:
        dd = date.fromisoformat(d)
        add(f"ウェビナー「{nm}」", "ウェビナー", "自社", (dd - timedelta(days=21)).isoformat(), d, 250000)
    for a, b, nm in [("2025-01-15", "2026-10-31", "オフィスコーヒー導入ガイド"), ("2025-06-01", "2026-10-31", "福利厚生アンケートレポート 2025"),
                     ("2026-01-20", "2026-10-31", "飲料コスト比較シート")]:
        add(f"ホワイトペーパー「{nm}」", "ホワイトペーパー", "自社サイト", a, b, 450000)
    for a, b in [("2025-01-15", "2025-03-15"), ("2025-10-01", "2025-11-30"), ("2026-01-15", "2026-03-15")]:
        add(f"テレアポ {a[:7]}", "テレアポ", "外部委託", a, b, 450000 * 2, objective="アポイント獲得")
    add("紹介プログラム", "紹介", "自社", "2024-11-01", "2026-10-31", 0, objective="紹介獲得")
    df = pd.DataFrame(C)
    df.insert(0, "campaign_id", [f"CP{i + 1:03d}" for i in range(len(df))])
    df["utm_campaign"] = [f"cc_{i + 1:03d}" for i in range(len(df))]
    return df


class Marketing:
    def __init__(self, emp, inquiries, seed):
        self.rng = np.random.default_rng(seed)
        self.emp = emp
        self.inq = inquiries
        self.start, self.end = config.MARKETING_START, config.DATA_END

    def companies(self, n=1600):
        r = self.rng
        rows, seen = [], set()
        n = min(n, int(len(PREFIX) * len(SUFFIX) * 0.8))
        prefs = [p[0] for p in config.PREFECTURES]
        pw = np.array([p[1] ** 1.3 for p in config.PREFECTURES])
        pw /= pw.sum()
        region = {p[0]: p[2] for p in config.PREFECTURES}
        while len(rows) < n:
            pre = PREFIX[int(r.integers(len(PREFIX)))]
            suf, ind = SUFFIX[int(r.integers(len(SUFFIX)))]
            core = pre + suf
            if core in seen:
                continue
            seen.add(core)
            if ind == "医療・福祉" and suf == "クリニック":
                form = "医療法人社団"
            elif suf in ("学園",):
                form = "学校法人"
            elif suf == "会計事務所":
                form = "税理士法人"
            elif suf == "法律事務所":
                form = "弁護士法人"
            elif suf == "保育園":
                form = "社会福祉法人"
            else:
                form = str(r.choice(["株式会社", "合同会社", "有限会社"], p=[0.88, 0.07, 0.05]))
            pos = "pre" if (form != "株式会社" or r.random() < 0.6) else "suf"
            name = f"{form}{core}" if pos == "pre" else f"{core}{form}"
            band = str(r.choice(BANDS, p=BAND_P))
            pf = str(r.choice(prefs, p=pw))
            rows.append(dict(account_name=name, core=core, form=form, pos=pos, industry=ind, employee_band=band, prefecture=pf,
                             region=region[pf], appeal=float(r.lognormal(0, 0.35))))
        return pd.DataFrame(rows)

    def raw_name(self, c):
        r = self.rng
        k = r.random()
        core, form = c["core"], c["form"]
        if form != "株式会社" or k < 0.55:
            return c["account_name"]
        if k < 0.68:
            return f"（株）{core}" if c["pos"] == "pre" else f"{core}（株）"
        if k < 0.76:
            return f"(株){core}" if c["pos"] == "pre" else f"{core}(株)"
        if k < 0.84:
            return core
        if k < 0.9:
            return f"株式会社 {core}" if c["pos"] == "pre" else f"{core} 株式会社"
        if k < 0.95:
            return f"{core}".translate(str.maketrans("アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン",
                                                     "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜｦﾝ")) + "株式会社"
        return f"{core} 様"

    def run(self, out_dir):
        r = self.rng
        camps = _campaigns()
        comp = self.companies()
        cw = comp["appeal"].to_numpy() * np.array([{"1-9名": 0.6, "10-49名": 1.0, "50-99名": 1.2, "100-299名": 1.3,
                                                     "300-999名": 1.0, "1000名以上": 0.8}[b] for b in comp["employee_band"]])
        cw /= cw.sum()
        spend, leads = [], []

        def new_lead(t, cid, source, itype):
            ci = int(r.choice(len(comp), p=cw))
            c = comp.iloc[ci]
            leads.append(dict(created_at=t, campaign_id=cid, lead_source=source, comp_idx=ci, company_name=self.raw_name(c),
                              inquiry_type=itype))

        def day_time(d, lo=8, hi=22):
            return datetime(d.year, d.month, d.day, int(r.integers(lo, hi)), int(r.integers(0, 60)), int(r.integers(0, 60)))

        for c in camps.itertuples():
            for d in daterange(max(c.start_date, self.start), min(c.end_date, self.end)):
                wk = d.weekday() >= 5 or d in HOLIDAY_DATES
                if c.channel in ("検索広告", "SNS広告", "ビジネスSNS広告"):
                    media = c.media
                    base = {"Google 広告": (9000, 0.035, 210, 0.020), "Yahoo! 広告": (5200, 0.025, 150, 0.015),
                            "Meta 広告": (42000, 0.009, 90, 0.008), "LinkedIn 広告": (6500, 0.005, 620, 0.025)}[media]
                    yrs = (d - self.start).days / 365
                    imp = int(base[0] * (0.5 if wk else 1.15) * r.lognormal(0, 0.15) * (1.15 if d.month in (2, 3, 9) else 1))
                    clicks = int(r.binomial(imp, base[1]))
                    cpc = base[2] * (1 + 0.12 * yrs) * r.lognormal(0, 0.1)
                    cost = int(min(clicks * cpc, c.budget_jpy / max((c.end_date - c.start_date).days + 1, 1) * 1.3))
                    conv = int(r.binomial(clicks, base[3] * (1.25 if d.month in (2, 3) else 1)))
                    spend.append(dict(date=d, campaign_id=c.campaign_id, media=media, impressions=imp, clicks=clicks,
                                      cost_jpy=cost, platform_conversions=conv))
                    for _ in range(int(r.binomial(conv, 0.85))):
                        src = c.channel
                        cid = c.campaign_id
                        if media == "LinkedIn 広告" and date(2025, 8, 18) <= d <= date(2025, 8, 31):
                            src, cid = "不明", None
                        itype = str(r.choice(["資料請求", "見積依頼", "問い合わせ", "無料トライアル申込"] if d >= date(2025, 10, 1)
                                             else ["資料請求", "見積依頼", "問い合わせ"],
                                             p=[0.5, 0.2, 0.15, 0.15] if d >= date(2025, 10, 1) else [0.6, 0.22, 0.18]))
                        new_lead(day_time(d, 0, 24), cid, src, itype)
                elif c.channel == "展示会":
                    if d == c.start_date:
                        spend.append(dict(date=d, campaign_id=c.campaign_id, media="展示会", impressions=None, clicks=None,
                                          cost_jpy=int(c.budget_jpy), platform_conversions=None))
                    for _ in range(int(r.integers(90, 160))):
                        new_lead(day_time(d, 10, 17), c.campaign_id, "展示会", "名刺交換")
                elif c.channel == "ウェビナー":
                    if d == c.start_date:
                        spend.append(dict(date=d, campaign_id=c.campaign_id, media="自社", impressions=None, clicks=None,
                                          cost_jpy=int(c.budget_jpy), platform_conversions=None))
                    for _ in range(int(r.poisson(4 if d < c.end_date else 0))):
                        new_lead(day_time(d), c.campaign_id, "ウェビナー", "セミナー参加")
                elif c.channel == "ホワイトペーパー":
                    if d == c.start_date:
                        spend.append(dict(date=d, campaign_id=c.campaign_id, media="自社サイト", impressions=None, clicks=None,
                                          cost_jpy=int(c.budget_jpy), platform_conversions=None))
                    for _ in range(int(r.poisson(0.9 if not wk else 0.4))):
                        new_lead(day_time(d, 0, 24), c.campaign_id, "ホワイトペーパー", "資料請求")
                elif c.channel == "テレアポ":
                    if d.day == 1 or d == c.start_date:
                        spend.append(dict(date=d, campaign_id=c.campaign_id, media="外部委託", impressions=None, clicks=None,
                                          cost_jpy=450000, platform_conversions=None))
                    if not wk:
                        for _ in range(int(r.poisson(2.2))):
                            new_lead(day_time(d, 10, 18), c.campaign_id, "テレアポ", "アポイント")
                elif c.channel == "紹介":
                    for _ in range(int(r.poisson(0.12))):
                        new_lead(day_time(d), c.campaign_id, "紹介", "問い合わせ")
        for d in daterange(self.start, self.end):
            for _ in range(int(r.poisson(1.6 if d.weekday() < 5 else 0.6))):
                new_lead(day_time(d, 0, 24), None, "自然検索", str(r.choice(["資料請求", "見積依頼", "問い合わせ"], p=[0.5, 0.25, 0.25])))
        # CS -> sales hand-over
        cs = self.inq[(self.inq["subcategory"] == "法人・大口") | ((self.inq["assigned_team"] == "法人営業部") & self.inq["category"].isna())]
        cs = cs[cs["received_at"] >= pd.Timestamp(self.start)]
        cs_map = []
        for q in cs.itertuples():
            t = q.received_at.to_pydatetime() + timedelta(hours=int(r.integers(2, 48)))
            new_lead(t, None, "問い合わせ（CS経由）", "問い合わせ")
            cs_map.append((len(leads) - 1, q.inquiry_id))
        lead = pd.DataFrame(leads).sort_values("created_at", kind="stable").reset_index()
        cs_lookup = dict(cs_map)
        lead["source_inquiry_id"] = lead["index"].map(cs_lookup)
        lead = lead.drop(columns=["index"])
        lead.insert(0, "lead_id", [f"LD{t:%y%m}-{i + 1:05d}" for i, t in enumerate(lead["created_at"])])
        # enrich, response time, qualification
        isr = self.emp[self.emp["department_id"] == "D202"]
        rows = []
        exh_load = lead[lead["lead_source"] == "展示会"].groupby(lead["created_at"].dt.date).size().to_dict()
        for L in lead.itertuples():
            c = comp.iloc[L.comp_idx]
            t = L.created_at
            d = t.date()
            # first contact by inside sales (business hours)
            delay_h = float(r.lognormal(np.log(3.0), 1.0))
            if L.lead_source == "展示会":
                delay_h = float(r.uniform(20, 140))
            ft = t + timedelta(hours=delay_h)
            while ft.weekday() >= 5 or ft.date() in HOLIDAY_DATES or not (9 <= ft.hour < 19):
                if ft.hour >= 19 or ft.weekday() >= 5 or ft.date() in HOLIDAY_DATES:
                    nd = ft.date() + timedelta(days=1)
                    ft = datetime(nd.year, nd.month, nd.day, 9, int(r.integers(0, 60)))
                else:
                    ft = datetime(ft.year, ft.month, ft.day, 9, int(r.integers(0, 60)))
            if ft > datetime(2026, 10, 31, 23, 59):
                ft = None
            a = people.active_on(isr, d)
            owner = a.iloc[int(r.integers(len(a)))]["employee_id"] if len(a) else None
            resp_h = (ft - t).total_seconds() / 3600 if ft else None
            p = CONV[L.lead_source]
            if resp_h is not None:
                p *= 1.5 if resp_h <= 1 else (1.0 if resp_h <= 24 else (0.75 if resp_h <= 48 else 0.5))
            p *= {"1-9名": 0.4, "10-49名": 0.9, "50-99名": 1.2, "100-299名": 1.25, "300-999名": 1.0, "1000名以上": 0.75}[c["employee_band"]]
            p *= {"見積依頼": 1.8, "資料請求": 0.8, "セミナー参加": 0.75, "名刺交換": 0.7, "無料トライアル申込": 1.6,
                  "問い合わせ": 1.1, "アポイント": 1.2}[L.inquiry_type]
            dq = r.random() < 0.11
            status, reason = None, None
            to_opp = (not dq) and r.random() < min(p, 0.9) and ft is not None
            if dq:
                status = "対象外"
                reason = str(r.choice(["個人のお客様", "競合他社の調査", "重複登録", "連絡が取れない", "サービス対象外地域"],
                                      p=[0.3, 0.1, 0.25, 0.3, 0.05]))
            elif to_opp:
                status = "商談化"
            else:
                age = (config.DATA_END - d).days
                status = "対応中" if age < 14 else str(r.choice(["育成中", "失注（商談前）", "MQL"], p=[0.6, 0.25, 0.15]))
            score = int(np.clip(r.normal(55, 15) + (15 if to_opp else 0) + (10 if L.inquiry_type in ("見積依頼", "無料トライアル申込") else 0)
                                - (20 if dq else 0), 0, 100))
            rows.append(dict(lead_id=L.lead_id, created_at=t, campaign_id=L.campaign_id, lead_source=L.lead_source,
                             company_name=L.company_name, industry=c["industry"] if r.random() > 0.08 else None,
                             employee_band=c["employee_band"], prefecture=c["prefecture"],
                             department=str(r.choice(DEPTS, p=[0.42, 0.18, 0.12, 0.06, 0.08, 0.14])),
                             job_level=str(r.choice(LEVELS, p=[0.38, 0.2, 0.18, 0.12, 0.05, 0.07])),
                             inquiry_type=L.inquiry_type, owner_employee_id=owner, first_contact_at=ft, status=status,
                             disqualify_reason=reason, lead_score=score, source_inquiry_id=L.source_inquiry_id,
                             x_comp=L.comp_idx, x_opp=to_opp))
        ld = pd.DataFrame(rows)
        opps, hist, orders = self.opportunities(ld, comp)
        ld = ld.drop(columns=["x_comp", "x_opp"])
        sp = pd.DataFrame(spend)
        for c in ("impressions", "clicks", "platform_conversions"):
            sp[c] = sp[c].astype("Int64")
        sp.insert(0, "spend_id", [f"SP{i + 1:06d}" for i in range(len(sp))])
        camps_out = camps.copy()
        mk = people.active_on(self.emp, date(2026, 10, 31), ["D105"])
        camps_out["owner_employee_id"] = [mk.iloc[i % len(mk)]["employee_id"] for i in range(len(camps_out))]
        write_csv(camps_out, out_dir / "campaigns.csv")
        write_csv(sp, out_dir / "ad_spend_daily.csv")
        write_csv(ld, out_dir / "leads.csv")
        write_csv(opps, out_dir / "opportunities.csv")
        write_csv(hist, out_dir / "opportunity_stage_history.csv")
        write_csv(orders, out_dir / "orders.csv")
        return dict(campaigns=camps_out, leads=ld, opps=opps, orders=orders, spend=sp)

    def opportunities(self, ld, comp):
        r = self.rng
        reps_all = self.emp[self.emp["department_id"].isin(["D200", "D201", "D210", "D211", "D212"])]
        skill = {e: float(r.lognormal(0, 0.25)) for e in reps_all["employee_id"]}
        ids = list(skill)
        if ids:
            skill[ids[3]] = 1.7
            skill[ids[min(9, len(ids) - 1)]] = 0.55
        O, H, ORD = [], [], []
        k = 0
        for L in ld[ld["x_opp"]].itertuples():
            c = comp.iloc[L.x_comp]
            k += 1
            created = (L.first_contact_at + timedelta(days=float(r.lognormal(np.log(6), 0.6)))).date()
            if created > config.DATA_END:
                continue
            branch = BRANCH_OF_REGION[c["region"]]
            if branch in ("D200", "D201"):
                branch = "D200" if r.random() < 0.5 else "D201"
            reps = people.active_on(reps_all, created, [branch])
            reps = reps[~reps["job_title"].isin(["部長", "支店長", "課長"])] if len(reps) > 2 else reps
            if not len(reps):
                reps = people.active_on(reps_all, created)
            owner = reps.iloc[int(r.integers(len(reps)))]["employee_id"]
            band = c["employee_band"]
            if c["industry"] == "宿泊・飲食":
                plan, fee = "業務用豆卸", int(r.integers(4, 16)) * 10000
            else:
                plan = "ライト" if band in ("1-9名", "10-49名") else ("スタンダード" if band in ("50-99名", "100-299名") else "プレミアム")
                fee = PLANS[plan]
            months = int(r.choice([12, 24, 36], p=[0.5, 0.3, 0.2]))
            init = {"ライト": 30000, "スタンダード": 50000, "プレミアム": 80000, "業務用豆卸": 0}[plan]
            comp_name = str(r.choice(COMPETITORS)) if r.random() < 0.42 else None
            p_win = 0.34 * skill.get(owner, 1.0)
            p_win *= {"紹介": 1.5, "展示会": 1.1, "SNS広告": 0.8, "問い合わせ（CS経由）": 1.3}.get(L.lead_source, 1.0)
            p_win *= 0.72 if comp_name else 1.0
            # stages
            d = created
            hist = []
            outcome = None
            for si, st in enumerate(STAGES):
                dur = int(np.clip(r.lognormal(np.log(9), 0.6), 2, 60))
                hist.append([st, d, None])
                nd = d + timedelta(days=dur)
                if nd > config.DATA_END:
                    break
                hist[-1][2] = nd
                drop_p = [0.12, 0.10, 0.12, 0.10, 0.0][si]
                if st == "見積提示" and nd >= date(2026, 4, 1):
                    fee = int(round(fee * 1.08, -2))
                    drop_p += 0.06
                if r.random() < drop_p:
                    outcome = ("失注", nd)
                    break
                d = nd
            else:
                close = d
                pw = p_win * (1.15 if close.month in (2, 3) else 1.0) * (0.85 if close >= date(2026, 4, 1) else 1.0)
                outcome = ("受注" if r.random() < min(pw * 1.6, 0.95) else "失注", close)
            oid = f"OP{created:%y%m}-{k:04d}"
            if outcome is None:
                stage = hist[-1][0]
                is_won, closed, lost = None, None, None
                exp_close = hist[-1][1] + timedelta(days=int(r.integers(20, 70)))
            else:
                stage, closed = outcome
                is_won = stage == "受注"
                if not is_won:
                    pr = 0.35 if closed >= date(2026, 4, 1) else 0.2
                    lost = str(r.choice(["価格", "競合", "時期尚早", "予算なし", "社内決裁が通らない", "連絡途絶", "要件不一致"],
                                        p=np.array([pr, 0.22 if comp_name else 0.05, 0.14, 0.12, 0.1, 0.1, 0.07]) /
                                        (pr + (0.22 if comp_name else 0.05) + 0.53)))
                else:
                    lost = None
                hist.append([stage, closed, None])
                exp_close = closed
            amount = fee * months + init
            O.append(dict(opportunity_id=oid, lead_id=L.lead_id, account_name=c["account_name"], industry=c["industry"],
                          employee_band=band, prefecture=c["prefecture"], owner_employee_id=owner, branch_department_id=branch,
                          created_date=created, stage=stage, probability_pct=100 if stage == "受注" else (0 if stage == "失注" else STAGE_PROB[stage]),
                          plan=plan, monthly_fee=fee, contract_months=months, initial_fee=init, amount=amount,
                          expected_close_date=exp_close, closed_date=closed, is_won=is_won, lost_reason=lost,
                          competitor=comp_name))
            for st, a, b in hist:
                H.append(dict(opportunity_id=oid, stage=st, entered_date=a, exited_date=b,
                              days_in_stage=(b - a).days if b else None))
            if outcome and outcome[0] == "受注":
                start = closed + timedelta(days=int(r.integers(10, 35)))
                ORD.append(dict(order_id=f"BO{closed:%y%m}-{len(ORD) + 1:04d}", opportunity_id=oid, account_name=c["account_name"],
                                order_date=closed, plan=plan, contract_start_date=start, contract_months=months,
                                monthly_fee=fee, initial_fee=init, total_contract_value=amount, owner_employee_id=owner,
                                branch_department_id=branch, payment_terms=str(r.choice(["月末締め翌月末払い", "20日締め翌月10日払い"], p=[0.8, 0.2]))))
        h = pd.DataFrame(H)
        h.insert(0, "stage_history_id", [f"SH{i + 1:05d}" for i in range(len(h))])
        h["days_in_stage"] = h["days_in_stage"].astype("Int64")
        o = pd.DataFrame(O)
        o["is_won"] = o["is_won"].astype("boolean")
        return o, h, pd.DataFrame(ORD)


def generate(out_dir, emp, inquiries, seed):
    return Marketing(emp, inquiries, seed).run(out_dir)
