"""HR & attendance: departments, employees, daily attendance, overtime requests, training, resignations."""
from __future__ import annotations

from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

from . import config, people
from .calendar_jp import HOLIDAY_DATES, daterange, is_offday
from .io_utils import fmt_d, fmt_dt, write_csv
from .manufacturing import is_factory_day

COURSES = [
    ("C01", "新入社員研修", "導入研修", "集合", 16, False),
    ("C02", "情報セキュリティ研修", "コンプライアンス", "eラーニング", 1, True),
    ("C03", "コンプライアンス研修", "コンプライアンス", "eラーニング", 1, True),
    ("C04", "ハラスメント防止研修", "コンプライアンス", "eラーニング", 1, True),
    ("C05", "バリスタ基礎研修", "職種別スキル", "集合", 6, False),
    ("C06", "バリスタ上級研修", "職種別スキル", "集合", 8, False),
    ("C07", "食品衛生（HACCP）研修", "安全・衛生", "集合", 3, True),
    ("C08", "焙煎技術研修", "職種別スキル", "集合", 8, False),
    ("C09", "フォークリフト安全講習", "安全・衛生", "集合", 12, False),
    ("C10", "新任管理職研修", "階層別", "集合", 14, False),
    ("C11", "法人営業スキル研修", "職種別スキル", "集合", 8, False),
    ("C12", "データ活用入門（Power BI / Microsoft Fabric）", "DX・データ活用", "eラーニング", 6, False),
    ("C13", "接客マナー研修", "職種別スキル", "集合", 3, False),
    ("C14", "設備保全・予知保全入門", "職種別スキル", "集合", 6, False),
    ("C15", "カスタマー対応力向上研修", "職種別スキル", "集合", 4, False),
    ("C16", "リーダーシップ研修", "階層別", "集合", 12, False),
]

EXIT_COMMENTS = {
    "労働時間・業務量": ["繁忙期の残業が続き、体力的に限界を感じた。", "人員が足りず、希望どおりに休みが取れなかった。",
                   "トラブル対応で休日出勤が重なり、家族との時間が取れなかった。", "業務量が多く、毎月の残業が当たり前になっていた。"],
    "人間関係": ["上司とのコミュニケーションがうまくいかなかった。", "職場の雰囲気になじめなかった。", "困ったときに相談しにくい環境だった。"],
    "キャリアアップ": ["別業界で新しい経験を積みたい。", "より専門性の高い仕事に挑戦したい。", "将来は自分の店を持ちたいので、独立に向けて準備する。"],
    "給与・待遇": ["他社からより良い条件の提示があった。", "昇給の見通しが立たなかった。", "仕事量に対して給与が見合わないと感じた。"],
    "家庭の事情": ["家族の介護のため。", "配偶者の転勤に伴い。", "育児との両立が難しくなった。"],
    "転居": ["引っ越しで通勤が難しくなるため。", "地元に戻ることになったため。"],
    "健康上の理由": ["体調を崩したため、しばらく療養に専念したい。"],
    "仕事内容のミスマッチ": ["入社前に想像していた仕事内容と違った。", "研修の機会が少なく、業務についていけないと感じた。",
                   "最初の数か月で教わる機会がほとんどなく、不安が大きかった。"],
    "学業・就職": ["大学卒業後に就職するため。", "学業に専念するため。", "就職活動に集中するため。"],
    "店舗閉鎖": ["勤務していた店舗の閉店に伴い退職。"],
    "定年退職": ["定年退職。"],
    "その他": ["一身上の都合により。", "詳細は話したくないとのこと。"],
}

HQ_REMOTE = {"D104": 0.5, "D105": 0.4, "D106": 0.4, "D100": 0.3, "D102": 0.3, "D103": 0.3, "D107": 0.3, "D101": 0.15,
             "D108": 0.1, "D109": 0.08, "D110": 0.1, "D200": 0.15, "D201": 0.15, "D202": 0.25, "D210": 0.1, "D211": 0.1,
             "D212": 0.1}
EXHIBITIONS = [date(2025, 4, 16), date(2025, 4, 17), date(2025, 4, 18), date(2025, 10, 8), date(2025, 10, 9),
               date(2025, 10, 10), date(2026, 4, 15), date(2026, 4, 16), date(2026, 4, 17), date(2026, 7, 8), date(2026, 7, 9)]


def _d(x):
    return x if isinstance(x, date) and not pd.isna(x) else None


def _hm(s):
    h, m = s.split(":")
    return int(h) * 60 + int(m)


class HR:
    def __init__(self, depts, emp, mfg, seed):
        self.rng = np.random.default_rng(seed)
        self.depts = depts
        self.emp = emp
        self.mfg = mfg
        self.store = {s["store_id"]: s for s in config.STORES}
        self.site_of = {x.dept_id: x.site_id for x in depts}
        self.fail_days = {}
        for e in mfg.events:
            if e["event_type"] == "故障" and e["downtime"] >= 60:
                d0 = e["date"]
                end = e["end"].date() if hasattr(e["end"], "date") else d0
                for d in daterange(d0, end):
                    self.fail_days.setdefault(d, []).append(e)

    # season / event multipliers for overtime ------------------------------------------------------
    def ot_factor(self, e, d):
        dep = e["department_id"]
        f = 1.0
        m = d.month
        if dep == "D103":
            last = (date(d.year + (m // 12), m % 12 + 1, 1) - timedelta(days=1))
            if (last - d).days <= 3 or d.day <= 6:
                f *= 2.2
            if m in (4, 5):
                f *= 1.6
        if dep == "D102" and m in (3, 4):
            f *= 1.8
        if dep == "D104" and date(2026, 9, 16) <= d <= date(2026, 9, 26):
            f *= 3.2
        if dep in ("D105", "D106") and (m in (11, 12)):
            f *= 1.8
        if dep == "D108" and date(2026, 7, 15) <= d <= date(2026, 8, 10):
            f *= 3.0
        if dep == "D109" and (date(2026, 7, 13) <= d <= date(2026, 8, 7) or date(2026, 9, 16) <= d <= date(2026, 9, 25)
                              or m == 12 or date(2025, 11, 21) <= d <= date(2025, 12, 3)):
            f *= 2.0
        if dep == "D110" and (date(2025, 3, 20) <= d <= date(2025, 4, 25) or date(2025, 11, 1) <= d <= date(2025, 11, 30)
                              or date(2025, 12, 10) <= d <= date(2025, 12, 31)):
            f *= 1.7
        if dep.startswith("D2") and (m == 3 or d in EXHIBITIONS):
            f *= 1.6 if d not in EXHIBITIONS else 2.5
        if dep.startswith("D3"):
            if m == 12:
                f *= 1.9
            if d.month in (7, 8):
                f *= 1.2
            sid = "S" + dep[2:]
            if sid in ("S09", "S16"):
                so = date.fromisoformat(self.store[sid]["open_date"])
                if -25 <= (d - so).days <= 30:
                    f *= 2.4
        if dep in ("D400", "D403") and m in (10, 11, 12):
            f *= 1.6
        if dep == "D402" and date(2026, 7, 17) <= d <= date(2026, 7, 31):
            f *= 2.6
        if dep == "D500":
            if m == 12 and d.day <= 25 or (m == 7 and d.day <= 15):
                f *= 1.9
            if date(2024, 11, 22) <= d <= date(2024, 12, 3) or date(2025, 11, 21) <= d <= date(2025, 12, 2):
                f *= 2.2
            if date(2026, 6, 22) <= d <= date(2026, 6, 25):
                f *= 2.0
        return f

    # ---------------------------------------------------------------------------------------------
    def run(self, out_dir):
        r = self.rng
        emp = self.emp
        att, otr = [], []
        start, end = config.HR_START, config.DATA_END
        part_plan = {}
        for dpt in self.depts:
            part_plan[dpt.dept_id] = sum(n for et, _, _, n in dpt.plan if et == "パート・アルバイト")
        active_part = {}
        for d in daterange(start, end):
            a = people.active_on(emp, d)
            active_part[d] = a[a["employment_type"] == "パート・アルバイト"].groupby("department_id").size().to_dict()
        for e in emp.to_dict(orient="records"):
            hire = e["hire_date"]
            term = _d(e["termination_date"])
            a = max(hire, start)
            b = min(term, end) if term else end
            if a > b:
                continue
            dep = e["department_id"]
            etype = e["employment_type"]
            pt = etype == "パート・アルバイト"
            weekly_days = int(r.choice([3, 4, 5], p=[0.35, 0.4, 0.25])) if pt else 5
            pt_len = int(r.choice([240, 300, 360, 420], p=[0.25, 0.35, 0.3, 0.1]))
            ot_p = e["ot_propensity"]
            leave_target = 0 if pt else float(np.clip(r.normal(10.5, 4), 1, 20))
            if e["job_title"] in ("店長", "副店長") or dep == "D401":
                leave_target *= 0.55
            lv_prob = leave_target / 240
            shift_week = int(r.integers(0, 2))
            for d in daterange(a, b):
                transfer = _d(e.get("transfer_date"))
                if isinstance(transfer, date) and d < transfer:
                    cur_dep = e["prior_department_id"]
                else:
                    cur_dep = dep
                site = self.site_of.get(cur_dep)
                is_store = cur_dep.startswith("D3")
                is_fac = cur_dep.startswith("D4")
                is_dc = cur_dep == "D500"
                wk = d.weekday()
                # --- is this a scheduled workday? ---
                holiday_work = False
                if is_store:
                    s = self.store["S" + cur_dep[2:]]
                    if d < date.fromisoformat(s["open_date"]) - timedelta(days=25):
                        continue
                    if d.month == 1 and d.day == 1:
                        continue
                    # store staff: rotate days off, fewer offs on weekends
                    pwork = (weekly_days / 7) * (1.25 if wk >= 5 else 0.9)
                    if not pt:
                        pwork = 5 / 7 * (1.2 if wk >= 5 else 0.92)
                    if r.random() > pwork:
                        continue
                    o, c = _hm(s["open_time"]), _hm(s["close_time"])
                    if pt:
                        st = int(r.choice([o, o + 120, max(o, c - pt_len)]))
                        sched = (st, st + pt_len)
                        shift = "早番" if st == o else ("遅番" if st + pt_len >= c else "中番")
                    else:
                        k = int(r.integers(0, 3))
                        sched = [(o - 30, o + 510), (c + 30 - 540, c + 30), (o + 120, o + 660)][k]
                        shift = ["早番", "遅番", "中番"][k]
                elif is_fac and dep != "D401" and cur_dep in ("D400",):
                    fd = is_factory_day(d) or d in (date(2026, 6, 20), date(2026, 7, 25))
                    if not fd:
                        continue
                    if pt:
                        if r.random() > weekly_days / 5:
                            continue
                        sched, shift = (_hm("09:00"), _hm("09:00") + pt_len), "日勤"
                    elif wk == 5:
                        if r.random() > 0.55:
                            continue
                        sched, shift = (_hm("06:00"), _hm("14:45")), "早番"
                    else:
                        wkno = (d.isocalendar()[1] + shift_week) % 2
                        sched, shift = ((_hm("06:00"), _hm("14:45")), "早番") if wkno == 0 else ((_hm("13:15"), _hm("22:00")), "遅番")
                elif is_dc:
                    if wk == 6 or (d.month == 1 and d.day <= 3) or (d.month == 12 and d.day == 31):
                        continue
                    if r.random() > (weekly_days / 6 if pt else 5 / 6):
                        continue
                    if pt:
                        sched, shift = (_hm("09:00"), _hm("09:00") + pt_len), "日勤"
                    else:
                        early = r.random() < 0.55
                        sched, shift = ((_hm("07:00"), _hm("16:00")), "早番") if early else ((_hm("13:00"), _hm("22:00")), "遅番")
                else:  # HQ, branches, factory day staff
                    fails = self.fail_days.get(d, [])
                    called = dep == "D401" and any(f["technician"] == e["employee_id"] or r.random() < 0.35 for f in fails)
                    if is_offday(d) and not called:
                        continue
                    if is_offday(d):
                        holiday_work = True
                    if pt:
                        if r.random() > weekly_days / 5:
                            continue
                        st = int(r.choice([_hm("10:00"), _hm("13:00")]))
                        sched, shift = (st, st + pt_len), "日勤"
                    elif is_fac:
                        sched, shift = (_hm("08:00"), _hm("17:00")), "日勤"
                    else:
                        sched, shift = (_hm("09:00"), _hm("18:00")), "日勤"
                # --- leave ---
                if not pt and not holiday_work and r.random() < lv_prob:
                    lt = "年次有給休暇" if r.random() < 0.9 else str(r.choice(["特別休暇", "欠勤"], p=[0.6, 0.4]))
                    att.append(dict(employee_id=e["employee_id"], work_date=d, site_id=site, work_style=None, shift_type=shift,
                                    scheduled_start=sched[0], scheduled_end=sched[1], clock_in=None, clock_out=None,
                                    break_minutes=0, work_minutes=0, overtime_minutes=0, late_night_minutes=0,
                                    holiday_work=False, leave_type=lt, note=None))
                    continue
                sched_min = sched[1] - sched[0]
                brk = 60 if sched_min >= 480 and not shift.endswith("番") or (shift.endswith("番") and sched_min >= 480) else (45 if sched_min > 360 else 0)
                if is_fac and shift in ("早番", "遅番"):
                    brk = 45
                remote = (not is_store and not is_fac and not is_dc and r.random() < HQ_REMOTE.get(cur_dep, 0.0) and not holiday_work)
                cin = sched[0] - int(np.clip(r.normal(8 if not remote else 2, 6), -10, 40))
                if r.random() < 0.015:
                    cin = sched[0] + int(r.integers(3, 40))  # late
                # overtime
                ot = 0
                if not pt or r.random() < 0.1:
                    base = 25 if not pt else 15
                    if is_store:
                        sh = active_part[d].get(cur_dep, 0)
                        plan = part_plan.get(cur_dep, 0) or 1
                        base *= 1 + max(0, plan - sh) / plan * 1.6
                    mean = base * ot_p * self.ot_factor(dict(department_id=cur_dep), d)
                    ot = int(r.exponential(mean)) if r.random() < 0.75 else 0
                    if term and (term - d).days < 120 and e["reason_category"] == "労働時間・業務量":
                        ot = int(ot * 1.6 + r.exponential(40))
                if dep == "D401":
                    fails = self.fail_days.get(d, [])
                    for f in fails:
                        if f["technician"] == e["employee_id"] or r.random() < 0.35:
                            endt = f["end"]
                            if endt.date() == d:
                                ot = max(ot, endt.hour * 60 + endt.minute + 60 - sched[1])
                            else:
                                ot = max(ot, _hm("23:30") - sched[1] + int(r.integers(0, 60)))
                if holiday_work:
                    sched_min = 0
                cout = sched[1] + ot + int(np.clip(r.normal(6, 5), 0, 25))
                if holiday_work:
                    cin = _hm("08:00") + int(r.integers(-20, 40)) if dep == "D401" else _hm("09:00")
                    cout = cin + int(r.integers(180, 600))
                work = cout - cin - brk
                ot_min = max(0, work - (sched_min - brk)) if not holiday_work else work
                ot_min = int(round(ot_min / 1)) if ot_min > 10 else 0
                late = max(0, min(cout, 29 * 60) - 22 * 60) + max(0, 5 * 60 - cin)
                d0 = datetime(d.year, d.month, d.day)
                ci = d0 + timedelta(minutes=int(cin), seconds=int(r.integers(0, 60)))
                co = d0 + timedelta(minutes=int(cout), seconds=int(r.integers(0, 60)))
                note = None
                if r.random() < 0.004:
                    co, note = None, "打刻漏れ（修正申請中）"
                att.append(dict(employee_id=e["employee_id"], work_date=d, site_id=site,
                                work_style="テレワーク" if remote else "出社", shift_type="休日出勤" if holiday_work else shift,
                                scheduled_start=None if holiday_work else sched[0], scheduled_end=None if holiday_work else sched[1],
                                clock_in=ci, clock_out=co, break_minutes=brk, work_minutes=None if co is None else int(work),
                                overtime_minutes=None if co is None else int(ot_min), late_night_minutes=None if co is None else int(late),
                                holiday_work=holiday_work, leave_type=None, note=note))
                # overtime request
                if not pt and co is not None and ot_min >= 30 and r.random() < 0.86:
                    reason, text = self.reason(cur_dep, d, holiday_work)
                    req = int(round(ot_min / 30) * 30)
                    if r.random() < 0.3:
                        req = max(30, req - 30)
                    status = str(r.choice(["承認", "差戻し", "申請中"], p=[0.95, 0.03, 0.02])) if (end - d).days > 3 else "申請中"
                    otr.append(dict(employee_id=e["employee_id"], work_date=d, requested_minutes=req,
                                    approved_minutes=req if status == "承認" else None, reason_category=reason, reason_text=text,
                                    approver_employee_id=e["manager_employee_id"], status=status,
                                    requested_at=d0 + timedelta(minutes=int(sched[1] - int(r.integers(10, 120))))))
            if len(att) % 50 == 0:
                pass
        att = pd.DataFrame(att)
        att = att.sort_values(["work_date", "employee_id"], kind="stable").reset_index(drop=True)
        att.insert(0, "attendance_id", [f"AT{i + 1:07d}" for i in range(len(att))])
        for c in ("scheduled_start", "scheduled_end"):
            att[c] = att[c].map(lambda m: None if m is None or (isinstance(m, float) and np.isnan(m)) else f"{int(m) // 60:02d}:{int(m) % 60:02d}")
        for c in ("work_minutes", "overtime_minutes", "late_night_minutes"):
            att[c] = att[c].astype("Int64")
        otr = pd.DataFrame(otr).sort_values(["work_date", "employee_id"]).reset_index(drop=True)
        otr.insert(0, "request_id", [f"OT{i + 1:06d}" for i in range(len(otr))])
        otr["approved_minutes"] = otr["approved_minutes"].astype("Int64")
        tr = self.training()
        rs = self.resignations()
        self.write(out_dir, att, otr, tr, rs)
        return dict(attendance=att, overtime=otr, training=tr, resignations=rs)

    def reason(self, dep, d, holiday):
        r = self.rng
        if dep == "D401" and d in self.fail_days:
            f = self.fail_days[d][0]
            return "設備トラブル対応", f"{f['equipment_id']} の故障対応・復旧作業のため"
        if dep == "D108" and date(2026, 7, 15) <= d <= date(2026, 8, 10):
            return "品質問題の調査対応", str(r.choice(["焙煎ロットの苦情調査と原因究明のため", "交換対応の手配・お客様への説明資料作成のため"]))
        if dep == "D104" and date(2026, 9, 16) <= d <= date(2026, 9, 26):
            return "システム障害対応", str(r.choice(["アプリ決済不具合の調査・修正版リリース対応のため", "決済エラーの影響範囲調査のため"]))
        if dep == "D109" and date(2026, 7, 13) <= d <= date(2026, 8, 7):
            return "顧客対応", "品質に関するお問い合わせ急増への対応のため"
        if dep == "D109" and date(2026, 9, 16) <= d <= date(2026, 9, 25):
            return "顧客対応", "アプリ決済不具合に関するお問い合わせ対応のため"
        if dep == "D103":
            return "月次決算", str(r.choice(["月次決算処理のため", "決算資料作成のため", "監査対応のため"]))
        if dep.startswith("D2") and d in EXHIBITIONS:
            return "展示会対応", "展示会ブースの設営・来場者対応のため"
        if dep.startswith("D3"):
            sid = "S" + dep[2:]
            if sid in ("S09", "S16") and -25 <= (d - date.fromisoformat(self.store[sid]["open_date"])).days <= 30:
                return "新店オープン準備", "新店舗のオープン準備・スタッフ研修のため"
            if d.month == 12:
                return "繁忙期対応", "年末ギフト需要による繁忙のため"
            return str(r.choice(["欠員補充", "棚卸", "繁忙期対応", "その他"], p=[0.4, 0.15, 0.3, 0.15])), str(
                r.choice(["シフトの欠員を補うため", "月末棚卸のため", "来客が多く締め作業が遅れたため", "発注・在庫確認のため"]))
        if dep == "D500":
            return "繁忙期対応", str(r.choice(["出荷量の増加に対応するため", "ギフト出荷のピーク対応のため", "配送遅延分の出荷のため"]))
        if dep.startswith("D4"):
            return str(r.choice(["生産計画対応", "その他"], p=[0.8, 0.2])), str(r.choice(["ギフト向け増産のため", "段取り替えの遅れを取り戻すため", "品質検査が長引いたため"]))
        return str(r.choice(["資料作成", "会議対応", "その他"], p=[0.5, 0.3, 0.2])), str(
            r.choice(["会議資料の作成のため", "取引先との打ち合わせが長引いたため", "締切対応のため", "翌日の準備のため"]))

    # ---------------------------------------------------------------------------------------------
    def training(self):
        r = self.rng
        emp = self.emp
        rows = []
        start, end = config.HR_START, config.DATA_END

        def add(e, cid, d, mand=False):
            if d > end:
                return
            term = e["termination_date"] if isinstance(e["termination_date"], date) else None
            if term and d > term:
                return
            hrs = next(c for c in COURSES if c[0] == cid)
            comp_p = 0.93 if mand else 0.88
            st = "修了" if r.random() < comp_p else str(r.choice(["未修了", "欠席"]))
            cd = d + timedelta(days=int(r.integers(0, 20))) if hrs[3] == "eラーニング" else d
            if cd > end:
                st, cd = "受講中", None
            score = int(np.clip(r.normal(82, 9), 40, 100)) if hrs[3] == "eラーニング" and st == "修了" else None
            sat = int(np.clip(round(r.normal(4.0, 0.8)), 1, 5)) if st == "修了" and r.random() < 0.7 else None
            rows.append(dict(employee_id=e["employee_id"], course_id=cid, enrolled_date=d, completed_date=cd if st == "修了" else None,
                             status=st, score=score, satisfaction=sat))

        for e in emp.to_dict(orient="records"):
            hire, dep, pt = e["hire_date"], e["department_id"], e["employment_type"] == "パート・アルバイト"
            term = e["termination_date"] if isinstance(e["termination_date"], date) else None
            if term and term < start:
                continue
            new = hire >= start
            if new and not pt:
                add(e, "C01", hire + timedelta(days=int(r.integers(0, 10))))
            if dep.startswith("D3"):
                if new:
                    if not e["onboarding_gap"]:
                        add(e, "C05", hire + timedelta(days=int(r.integers(7, 80))))
                        add(e, "C13", hire + timedelta(days=int(r.integers(14, 90))))
                    elif r.random() < 0.3:
                        add(e, "C05", hire + timedelta(days=int(r.integers(120, 240))))
                if not pt and r.random() < 0.25:
                    add(e, "C06", date(2025, 6, 1) + timedelta(days=int(r.integers(0, 400))))
            for fy in (2024, 2025, 2026):
                ref = date(fy, 6, 1) if fy > 2024 else date(2024, 12, 1)
                if ref < max(hire, start):
                    continue
                add(e, "C02", ref + timedelta(days=int(r.integers(0, 60))), True)
                if not pt:
                    add(e, "C03", ref + timedelta(days=int(r.integers(30, 90))), True)
                    add(e, "C04", ref + timedelta(days=int(r.integers(60, 120))), True)
                if dep.startswith("D3") or dep in ("D400", "D402"):
                    add(e, "C07", date(fy, 9, 1) + timedelta(days=int(r.integers(0, 40))) if fy < 2026 else date(2026, 5, 10)
                        + timedelta(days=int(r.integers(0, 40))), True)
            if dep == "D400" and (new or r.random() < 0.2):
                add(e, "C08", max(hire, start) + timedelta(days=int(r.integers(20, 120))))
            if dep == "D500" and (new or r.random() < 0.15):
                add(e, "C09", max(hire, start) + timedelta(days=int(r.integers(5, 40))))
            if dep.startswith("D2") and not pt and r.random() < 0.6:
                add(e, "C11", date(2025, 5, 20) if r.random() < 0.5 else date(2026, 5, 19))
            if dep == "D109" and r.random() < 0.7:
                add(e, "C15", date(2025, 7, 10) + timedelta(days=int(r.integers(0, 300))))
            if dep == "D401":
                add(e, "C14", date(2026, 8, 20) + timedelta(days=int(r.integers(0, 30))))
            if e["job_title"] in ("課長", "店長", "支店長", "センター長") and r.random() < 0.3:
                add(e, "C10", date(2025, 4, 22) if r.random() < 0.5 else date(2026, 4, 21))
            if e["job_title"] in ("主任", "係長", "副店長") and r.random() < 0.35:
                add(e, "C16", date(2025, 10, 15) if r.random() < 0.5 else date(2026, 6, 10))
            if not pt and dep in ("D100", "D103", "D104", "D105", "D106", "D109", "D110", "D403") and r.random() < 0.35:
                add(e, "C12", date(2025, 11, 1) + timedelta(days=int(r.integers(0, 330))))
        df = pd.DataFrame(rows).sort_values(["enrolled_date", "employee_id"]).reset_index(drop=True)
        df.insert(0, "training_record_id", [f"TR{i + 1:06d}" for i in range(len(df))])
        for c in ("score", "satisfaction"):
            df[c] = df[c].astype("Int64")
        return df

    def resignations(self):
        r = self.rng
        x = self.emp[self.emp["termination_date"].notna()].copy()
        x = x[x["termination_date"] >= config.HR_START]
        rows = []
        for e in x.itertuples():
            pt = e.employment_type == "パート・アルバイト"
            notice = e.termination_date - timedelta(days=int(r.integers(14, 35) if pt else r.integers(30, 75)))
            if e.reason_category == "店舗閉鎖":
                notice = e.termination_date - timedelta(days=60)
            rc = e.reason_category or "その他"
            com = EXIT_COMMENTS.get(rc, EXIT_COMMENTS["その他"])
            comment = com[int(r.integers(len(com)))] if r.random() < 0.85 else None
            rows.append(dict(employee_id=e.employee_id, notice_date=notice, last_working_date=e.termination_date,
                             resignation_type=e.termination_type, reason_category=rc, exit_interview_comment=comment,
                             rehire_eligible=bool(rc not in ("人間関係",) and r.random() < 0.8)))
        df = pd.DataFrame(rows).sort_values("last_working_date").reset_index(drop=True)
        df.insert(0, "resignation_id", [f"RS{i + 1:04d}" for i in range(len(df))])
        return df

    def write(self, out_dir, att, otr, tr, rs):
        write_csv(people.departments_df(self.depts), out_dir / "departments.csv")
        emp = self.emp.copy()
        emp = emp[(emp["termination_date"].isna()) | (emp["termination_date"] >= config.HR_START)]
        cols = ["employee_id", "last_name", "first_name", "gender", "birth_date", "hire_date", "hire_type", "employment_type",
                "department_id", "site_id", "job_title", "grade", "base_salary_monthly", "hourly_wage", "manager_employee_id",
                "status", "termination_date", "commute_minutes"]
        emp = emp[cols].copy()
        for c in ("base_salary_monthly", "hourly_wage"):
            emp[c] = emp[c].astype("Int64")
        write_csv(emp, out_dir / "employees.csv")
        a = att.copy()
        a["clock_in"] = fmt_dt(a["clock_in"])
        a["clock_out"] = fmt_dt(a["clock_out"])
        write_csv(a, out_dir / "attendance.csv")
        o = otr.copy()
        o["requested_at"] = fmt_dt(o["requested_at"])
        write_csv(o, out_dir / "overtime_requests.csv")
        write_csv(pd.DataFrame(COURSES, columns=["course_id", "course_name", "course_category", "delivery_method", "hours",
                                                 "mandatory"]), out_dir / "training_courses.csv")
        write_csv(tr, out_dir / "training_records.csv")
        write_csv(rs, out_dir / "resignations.csv")


def generate(out_dir, depts, emp, mfg, seed):
    return HR(depts, emp, mfg, seed).run(out_dir)
