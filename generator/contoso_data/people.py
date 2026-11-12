"""Organization master: departments and employees (with hire / attrition timeline)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

import numpy as np
import pandas as pd

from . import config

SURNAMES = ("佐藤 鈴木 高橋 田中 伊藤 渡辺 山本 中村 小林 加藤 吉田 山田 佐々木 山口 松本 井上 木村 林 斎藤 清水 "
            "山崎 森 池田 橋本 阿部 石川 山下 中島 石井 小川 前田 岡田 長谷川 藤田 後藤 近藤 村上 遠藤 青木 坂本 "
            "福田 太田 西村 藤井 金子 岡本 藤原 中野 三浦 原田 中川 松田 竹内 小野 田村 中山 和田 石田 森田 上田 "
            "原 内田 柴田 酒井 宮崎 横山 高木 安藤 宮本 大野 小島 工藤 谷口 今井 高田 丸山 増田 杉山 村田 大塚 "
            "平野 藤本 久保 松井 千葉 岩崎 桜井 木下 野口 松尾 菊地 野村 新井 渡部 東 浅野 秋山 星野").split()
MALE = ("翔太 大輔 拓也 健太 直樹 和也 達也 翔 亮 誠 大樹 悠斗 陽翔 蓮 湊 大和 優斗 颯太 拓海 健一 浩二 隆 学 修 "
        "剛 聡 雄一 康介 智也 圭 洋平 慎也 俊介 一輝 涼介 海斗 陸 悠真 樹 航 光 匠 賢治 正人 大地").split()
FEMALE = ("陽菜 結衣 美咲 さくら 葵 凛 結菜 芽依 七海 莉子 愛 彩 舞 真由美 恵 由美 智子 裕子 久美子 明美 直美 麻衣 "
          "千尋 瞳 綾香 菜々子 優花 美穂 沙織 理恵 香織 奈央 美月 杏 楓 花 心春 紗希 遥 茜 さやか 早紀 琴音").split()

GRADE_SALARY = {"G1": 220000, "G2": 245000, "G3": 280000, "G4": 330000, "G5": 400000, "G6": 480000, "G7": 580000}


@dataclass
class Dept:
    dept_id: str
    dept_name: str
    division: str
    site_id: str
    parent: str | None
    plan: list = field(default_factory=list)  # (employment_type, job_title, grade, count)
    open_date: date = date(2010, 4, 1)
    close_date: date | None = None


def _departments() -> list[Dept]:
    D = []
    seishain = "正社員"
    hq = [
        ("D100", "経営企画部", 6), ("D101", "総務部", 7), ("D102", "人事部", 7), ("D103", "経理財務部", 8),
        ("D104", "情報システム部", 9), ("D105", "マーケティング部", 9), ("D106", "EC事業部", 10),
        ("D107", "商品開発部", 7), ("D108", "品質保証部", 6), ("D110", "店舗運営部", 6),
    ]
    for did, name, n in hq:
        plan = [(seishain, "部長", "G6", 1), (seishain, "課長", "G5", 1), (seishain, "主任", "G3", 2),
                (seishain, "一般", "G2", n - 4)]
        D.append(Dept(did, name, "本社部門", "H01", None, plan))
    D.append(Dept("D109", "カスタマーサポート部", "本社部門", "H01", None,
                  [(seishain, "部長", "G6", 1), (seishain, "課長", "G5", 1), (seishain, "主任", "G3", 2),
                   (seishain, "一般", "G2", 4), ("契約社員", "一般", "G1", 6), ("パート・アルバイト", "一般", "P", 5)]))
    D.append(Dept("D200", "法人営業部 第一営業課", "法人営業本部", "H01", None,
                  [(seishain, "課長", "G5", 1), (seishain, "主任", "G3", 2), (seishain, "一般", "G2", 5)]))
    D.append(Dept("D201", "法人営業部 第二営業課", "法人営業本部", "H01", "D200",
                  [(seishain, "課長", "G5", 1), (seishain, "主任", "G3", 1), (seishain, "一般", "G2", 5)]))
    D.append(Dept("D202", "法人営業部 インサイドセールス課", "法人営業本部", "H01", "D200",
                  [(seishain, "課長", "G4", 1), (seishain, "一般", "G2", 2), ("契約社員", "一般", "G1", 2)]))
    D.append(Dept("D210", "大阪支店", "法人営業本部", "B01", "D200",
                  [(seishain, "支店長", "G5", 1), (seishain, "主任", "G3", 1), (seishain, "一般", "G2", 3),
                   ("契約社員", "営業事務", "G1", 1)]))
    D.append(Dept("D211", "名古屋支店", "法人営業本部", "B02", "D200",
                  [(seishain, "支店長", "G5", 1), (seishain, "一般", "G2", 2), ("契約社員", "営業事務", "G1", 1)]))
    D.append(Dept("D212", "福岡支店", "法人営業本部", "B03", "D200",
                  [(seishain, "支店長", "G4", 1), (seishain, "一般", "G2", 2)]))
    for s in config.STORES:
        n_part = 8 if s["base"] >= 28 else (7 if s["base"] >= 20 else 6)
        n_sei = 2 if s["base"] >= 26 else 1
        plan = [(seishain, "店長", "G4", 1), (seishain, "副店長", "G3", 1), (seishain, "一般", "G2", n_sei),
                ("パート・アルバイト", "一般", "P", n_part)]
        if s["base"] >= 30:
            plan.append(("契約社員", "一般", "G1", 1))
        D.append(Dept("D3" + s["store_id"][1:], s["store_name"], "店舗事業本部", s["store_id"], "D110", plan,
                      open_date=date.fromisoformat(s["open_date"]),
                      close_date=date.fromisoformat(s["close_date"]) if s["close_date"] else None))
    D.append(Dept("D400", "熊谷工場 製造課", "生産本部", "F01", None,
                  [(seishain, "工場長", "G6", 1), (seishain, "課長", "G5", 1), (seishain, "係長", "G4", 3),
                   (seishain, "主任", "G3", 5), (seishain, "一般", "G2", 24), ("契約社員", "一般", "G1", 14),
                   ("パート・アルバイト", "一般", "P", 20)]))
    D.append(Dept("D401", "熊谷工場 設備保全課", "生産本部", "F01", "D400",
                  [(seishain, "課長", "G5", 1), (seishain, "主任", "G3", 2), (seishain, "一般", "G2", 7)]))
    D.append(Dept("D402", "熊谷工場 品質管理課", "生産本部", "F01", "D400",
                  [(seishain, "課長", "G5", 1), (seishain, "主任", "G3", 2), (seishain, "一般", "G2", 4),
                   ("契約社員", "一般", "G1", 2)]))
    D.append(Dept("D403", "熊谷工場 生産管理課", "生産本部", "F01", "D400",
                  [(seishain, "課長", "G5", 1), (seishain, "主任", "G3", 1), (seishain, "一般", "G2", 6)]))
    D.append(Dept("D500", "千葉物流センター 物流課", "生産本部", "D01", None,
                  [(seishain, "センター長", "G5", 1), (seishain, "主任", "G3", 3), (seishain, "一般", "G2", 6),
                   ("契約社員", "一般", "G1", 8), ("パート・アルバイト", "一般", "P", 14)]))
    return D


ANNUAL_ATTRITION = {"正社員": 0.065, "契約社員": 0.13, "パート・アルバイト": 0.26}


class PeopleBuilder:
    def __init__(self, rng: np.random.Generator):
        self.rng = rng
        self.depts = _departments()
        self.rows: list[dict] = []
        self.seq = 10000
        self.used_names: set = set()

    def _name(self, gender: str):
        r = self.rng
        for _ in range(50):
            ln = SURNAMES[int(r.integers(len(SURNAMES)))]
            fn = (MALE if gender == "男性" else FEMALE)[int(r.integers(len(MALE if gender == "男性" else FEMALE)))]
            if (ln, fn) not in self.used_names:
                self.used_names.add((ln, fn))
                return ln, fn
        return ln, fn

    def _new(self, dept: Dept, etype: str, title: str, grade: str, hire: date, hire_type: str, age: int | None = None,
             age_ref: date | None = None):
        r = self.rng
        self.seq += 1
        site = dept.site_id
        if dept.division == "生産本部" and etype != "正社員":
            female_p = 0.55
        elif dept.division == "店舗事業本部":
            female_p = 0.68 if etype == "パート・アルバイト" else 0.5
        elif dept.dept_id in ("D401",):
            female_p = 0.08
        else:
            female_p = 0.45
        if title in ("部長", "工場長", "センター長", "支店長"):
            female_p *= 0.45
        gender = "女性" if r.random() < female_p else "男性"
        if age is None:
            if etype == "パート・アルバイト":
                age = int(np.clip(r.choice([r.normal(21, 2), r.normal(45, 9)], p=[0.45, 0.55]), 18, 68))
            elif title in ("部長", "工場長"):
                age = int(r.integers(46, 57))
            elif title in ("課長", "支店長", "センター長", "店長"):
                age = int(r.integers(35, 52))
            elif title in ("係長", "主任", "副店長"):
                age = int(r.integers(29, 45))
            else:
                age = int(np.clip(r.normal(31, 7), 22, 57))
        ref = age_ref or hire
        bd = ref - timedelta(days=int(age * 365.25 + r.integers(0, 365)))
        min_hire = bd + timedelta(days=int(18.3 * 365.25))
        if hire < min_hire:
            hire = min_hire
        ln, fn = self._name(gender)
        salary = None
        wage = None
        if etype == "パート・アルバイト":
            area = site
            wage = 1250 if area in ("S03", "S04", "S05", "S06", "H01") else (1180 if area in ("S07", "S11", "S12", "S13", "S08", "S10")
                                                                       else 1080)
            wage = int(round((wage + r.integers(0, 16) * 10) / 10) * 10)
        else:
            salary = int(round(GRADE_SALARY[grade] * r.uniform(0.95, 1.08) / 1000) * 1000)
        ot = float(r.lognormal(0, 0.45))
        if dept.dept_id in ("D401", "D500", "D109", "D103") and etype != "パート・アルバイト":
            ot *= 1.35
        if title in ("店長", "副店長"):
            ot *= 1.5
        row = dict(employee_id=f"E{self.seq}", last_name=ln, first_name=fn, gender=gender, birth_date=bd,
                   hire_date=hire, hire_type=hire_type, employment_type=etype, department_id=dept.dept_id,
                   site_id=site, job_title=title, grade=grade, base_salary_monthly=salary, hourly_wage=wage,
                   termination_date=None, termination_type=None, reason_category=None, ot_propensity=ot,
                   onboarding_gap=False, prior_department_id=None, transfer_date=None,
                   commute_minutes=int(np.clip(r.gamma(4, 9), 5, 110)))
        self.rows.append(row)
        return row

    def _tenure_hire(self, dept: Dept, etype: str, ref: date) -> date:
        r = self.rng
        mean_y = {"正社員": 7.5, "契約社員": 3.0, "パート・アルバイト": 2.0}[etype]
        years = r.exponential(mean_y)
        hire = ref - timedelta(days=int(years * 365) + 1)
        floor = max(dept.open_date - timedelta(days=45), date(2010, 4, 1))
        if hire < floor:
            hire = floor + timedelta(days=int(r.integers(0, 60)))
        if hire >= ref:
            hire = ref - timedelta(days=int(r.integers(10, 200)))
        return hire

    def build(self):
        r = self.rng
        start, end = config.HR_START, config.DATA_END
        # Initial roster
        for dept in self.depts:
            for etype, title, grade, n in dept.plan:
                for _ in range(n):
                    if dept.open_date > start:
                        hire = dept.open_date - timedelta(days=int(r.integers(20, 50)))
                        self._new(dept, etype, title, grade, hire, "中途" if etype != "パート・アルバイト" else "パート採用")
                    else:
                        hire = self._tenure_hire(dept, etype, start)
                        ht = "パート採用" if etype == "パート・アルバイト" else ("新卒" if r.random() < 0.45 else "中途")
                        self._new(dept, etype, title, grade, hire, ht, age_ref=start)
        # New graduates
        for y in (2025, 2026):
            targets = ["D303", "D304", "D311", "D315", "D400", "D400", "D400", "D106", "D104", "D109", "D200"]
            for did in targets:
                dept = next(d for d in self.depts if d.dept_id == did)
                self._new(dept, "正社員", "一般", "G1", date(y, 4, 1), "新卒", age=22)
        # Attrition / replacement simulation (process list as it grows)
        dept_map = {d.dept_id: d for d in self.depts}
        i = 0
        while i < len(self.rows):
            e = self.rows[i]
            i += 1
            dept = dept_map[e["department_id"]]
            hire = e["hire_date"]
            begin = max(hire, start)
            if hire > end:
                continue
            # Store closure: part-timers leave, 正社員/契約 transfer to 梅田店
            if dept.close_date and dept.close_date <= end:
                if e["employment_type"] == "パート・アルバイト" or r.random() < 0.25:
                    e["termination_date"] = dept.close_date
                    e["termination_type"] = "会社都合"
                    e["reason_category"] = "店舗閉鎖"
                    continue
                e["prior_department_id"] = e["department_id"]
                e["transfer_date"] = dept.close_date + timedelta(days=1)
                e["department_id"] = "D311"
                e["site_id"] = "S11"
                if e["job_title"] == "店長":
                    e["job_title"] = "副店長"
                dept = dept_map["D311"]
            age_at_start = (begin - e["birth_date"]).days / 365.25
            base = ANNUAL_ATTRITION[e["employment_type"]]
            mult = 1.0
            if age_at_start < 30:
                mult *= 1.3
            if e["department_id"] == "D304":
                mult *= 2.3
            high_ot = e["ot_propensity"] > 1.55 and e["employment_type"] != "パート・アルバイト"
            if high_ot:
                mult *= 2.2
            if e["employment_type"] == "正社員" and e["job_title"] in ("部長", "工場長"):
                mult *= 0.5
            if hire >= start and r.random() < 0.3:
                e["onboarding_gap"] = True
                mult *= 1.6
            d = begin
            term = None
            while d <= end:
                tenure_y = (d - hire).days / 365.25
                m = mult * (1.6 if tenure_y < 1 else 1.0)
                if (d - e["birth_date"]).days / 365.25 >= 60 and e["employment_type"] == "正社員":
                    term = d
                    e["termination_type"] = "定年"
                    e["reason_category"] = "定年退職"
                    break
                if r.random() < base / 12 * m:
                    term = d + timedelta(days=int(r.integers(0, 28)))
                    break
                d += timedelta(days=30)
            if term and term <= end:
                e["termination_date"] = term
                if e["termination_type"] is None:
                    e["termination_type"] = "自己都合" if not (e["employment_type"] == "契約社員" and r.random() < 0.35) else "契約満了"
                    e["reason_category"] = self._reason(e, high_ot)
                # Replacement hire
                rep_date = term + timedelta(days=int(r.integers(14, 75)))
                if rep_date <= end and not (dept.close_date and rep_date > dept.close_date):
                    title = e["job_title"]
                    grade = e["grade"]
                    if title in ("部長", "課長", "店長", "支店長", "センター長", "工場長", "係長"):
                        grade = grade
                    ht = "パート採用" if e["employment_type"] == "パート・アルバイト" else "中途"
                    self._new(dept, e["employment_type"], title, grade, rep_date, ht)
        df = pd.DataFrame(self.rows)
        # Managers: department head = highest title active at end (or latest)
        rank = {"部長": 1, "工場長": 1, "センター長": 2, "支店長": 2, "課長": 3, "店長": 3, "係長": 4, "副店長": 4,
                "主任": 5, "営業事務": 8, "一般": 9}
        df["title_rank"] = df["job_title"].map(rank).fillna(9)
        heads = {}
        for did, g in df.groupby("department_id"):
            g = g.sort_values(["title_rank", "hire_date"])
            active = g[g["termination_date"].isna()]
            heads[did] = (active if len(active) else g).iloc[0]["employee_id"]
        parent = {d.dept_id: d.parent for d in self.depts}
        div_head = {"店舗事業本部": heads.get("D110"), "生産本部": heads.get("D400"), "法人営業本部": heads.get("D200")}

        def mgr(row):
            h = heads[row["department_id"]]
            if row["employee_id"] != h:
                return h
            p = parent.get(row["department_id"])
            if p:
                return heads.get(p)
            return None

        df["manager_employee_id"] = df.apply(mgr, axis=1)
        df["status"] = np.where(df["termination_date"].isna(), "在籍", "退職")
        return df.drop(columns=["title_rank"])

    def _reason(self, e, high_ot):
        r = self.rng
        if high_ot and r.random() < 0.6:
            return "労働時間・業務量"
        if e["department_id"] == "D304" and r.random() < 0.55:
            return "人間関係"
        age = (e["termination_date"] - e["birth_date"]).days / 365.25
        if e["employment_type"] == "パート・アルバイト" and age < 24 and r.random() < 0.5:
            return "学業・就職"
        opts = ["キャリアアップ", "給与・待遇", "家庭の事情", "転居", "健康上の理由", "人間関係", "仕事内容のミスマッチ", "その他"]
        w = np.array([0.24, 0.16, 0.14, 0.09, 0.07, 0.1, 0.12, 0.08])
        if age >= 40:
            w[0] *= 0.5
            w[2] *= 1.6
        return opts[int(r.choice(len(opts), p=w / w.sum()))]


def departments_df(depts: list[Dept]) -> pd.DataFrame:
    return pd.DataFrame([dict(department_id=d.dept_id, department_name=d.dept_name, division=d.division,
                              site_id=d.site_id, parent_department_id=d.parent,
                              established_date=d.open_date if d.open_date > date(2010, 4, 1) else None,
                              abolished_date=d.close_date) for d in depts])


def build(seed: int):
    rng = np.random.default_rng(seed)
    pb = PeopleBuilder(rng)
    emp = pb.build()
    return pb.depts, emp


def active_on(emp: pd.DataFrame, d: date, dept_ids=None) -> pd.DataFrame:
    m = (emp["hire_date"] <= d) & (emp["termination_date"].isna() | (emp["termination_date"] >= d))
    if dept_ids is not None:
        m &= emp["department_id"].isin(dept_ids) | emp["prior_department_id"].isin(dept_ids)
    return emp[m]
