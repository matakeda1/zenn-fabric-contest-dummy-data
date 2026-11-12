"""Shared constants: periods, company profile, weather stations, stores and sites."""
from __future__ import annotations

from datetime import date

COMPANY_NAME_JA = "コントソ珈琲株式会社"
COMPANY_NAME_EN = "Contoso Coffee Co., Ltd."
BRAND = "Contoso Coffee"

BASE_SEED = 2026

DATA_END = date(2026, 10, 31)
RETAIL_START = date(2024, 1, 1)
SUPPORT_START = date(2024, 1, 1)
LOTS_START = date(2024, 1, 1)
MFG_SENSOR_START = date(2026, 5, 1)
MFG_HISTORY_START = date(2025, 1, 1)
MARKETING_START = date(2024, 11, 1)
HR_START = date(2024, 11, 1)
ENERGY_START = date(2024, 11, 1)
EXCEL_DAILY_START = date(2026, 10, 1)
EXCEL_PO_START = date(2026, 9, 1)
APP_LOG_START = date(2026, 9, 1)

# Android app 5.4.0 checkout bug (staged rollout) and hotfix 5.4.1
APP_BUG_RELEASE = date(2026, 9, 16)
APP_BUG_FIX = date(2026, 9, 22)
ANDROID_540_ADOPTION = {  # share of Android app users on 5.4.0 that day
    date(2026, 9, 16): 0.15, date(2026, 9, 17): 0.35, date(2026, 9, 18): 0.55, date(2026, 9, 19): 0.70,
    date(2026, 9, 20): 0.78, date(2026, 9, 21): 0.82, date(2026, 9, 22): 0.55, date(2026, 9, 23): 0.25,
    date(2026, 9, 24): 0.10, date(2026, 9, 25): 0.04,
}
APP_BUG_FAIL_RATE = 0.62  # share of payment attempts that fail on 5.4.0

# JMA "main" observation stations (daily_s1 pages).
STATIONS = {
    "sapporo": {"name": "札幌", "prec_no": 14, "block_no": 47412},
    "sendai": {"name": "仙台", "prec_no": 34, "block_no": 47590},
    "tokyo": {"name": "東京", "prec_no": 44, "block_no": 47662},
    "yokohama": {"name": "横浜", "prec_no": 46, "block_no": 47670},
    "kumagaya": {"name": "熊谷", "prec_no": 43, "block_no": 47626},
    "chiba": {"name": "千葉", "prec_no": 45, "block_no": 47682},
    "kanazawa": {"name": "金沢", "prec_no": 56, "block_no": 47605},
    "nagoya": {"name": "名古屋", "prec_no": 51, "block_no": 47636},
    "kyoto": {"name": "京都", "prec_no": 61, "block_no": 47759},
    "osaka": {"name": "大阪", "prec_no": 62, "block_no": 47772},
    "kobe": {"name": "神戸", "prec_no": 63, "block_no": 47770},
    "hiroshima": {"name": "広島", "prec_no": 67, "block_no": 47765},
    "fukuoka": {"name": "福岡", "prec_no": 82, "block_no": 47807},
    "naha": {"name": "那覇", "prec_no": 91, "block_no": 47936},
}

# Physical stores. base = average receipts/day before weather & seasonal effects.
# area_type drives weekday/hour profiles.
STORES = [
    dict(store_id="S01", store_name="札幌大通店", prefecture="北海道", city="札幌市中央区", station="sapporo",
         area_type="商業地", open_date="2016-04-01", close_date=None, seats=24, floor_m2=120, base=22,
         open_time="09:00", close_time="20:00", lat=43.0606, lon=141.3544, gas=True),
    dict(store_id="S02", store_name="仙台一番町店", prefecture="宮城県", city="仙台市青葉区", station="sendai",
         area_type="商業地", open_date="2017-10-01", close_date=None, seats=20, floor_m2=105, base=19,
         open_time="09:00", close_time="20:00", lat=38.2600, lon=140.8730, gas=False),
    dict(store_id="S03", store_name="渋谷店", prefecture="東京都", city="渋谷区", station="tokyo",
         area_type="繁華街", open_date="2012-03-01", close_date=None, seats=30, floor_m2=150, base=33,
         open_time="08:00", close_time="21:00", lat=35.6595, lon=139.7005, gas=True),
    dict(store_id="S04", store_name="新宿店", prefecture="東京都", city="新宿区", station="tokyo",
         area_type="駅前", open_date="2014-06-01", close_date=None, seats=18, floor_m2=95, base=34,
         open_time="07:30", close_time="21:00", lat=35.6909, lon=139.7003, gas=False),
    dict(store_id="S05", store_name="丸の内店", prefecture="東京都", city="千代田区", station="tokyo",
         area_type="オフィス街", open_date="2015-09-01", close_date=None, seats=26, floor_m2=130, base=30,
         open_time="07:30", close_time="20:00", lat=35.6812, lon=139.7671, gas=False),
    dict(store_id="S06", store_name="吉祥寺店", prefecture="東京都", city="武蔵野市", station="tokyo",
         area_type="住宅地", open_date="2019-04-01", close_date=None, seats=16, floor_m2=85, base=17,
         open_time="09:00", close_time="19:00", lat=35.7030, lon=139.5797, gas=False),
    dict(store_id="S07", store_name="横浜みなとみらい店", prefecture="神奈川県", city="横浜市西区", station="yokohama",
         area_type="商業施設", open_date="2018-03-01", close_date=None, seats=28, floor_m2=140, base=26,
         open_time="10:00", close_time="20:00", lat=35.4570, lon=139.6320, gas=False),
    dict(store_id="S08", store_name="名古屋栄店", prefecture="愛知県", city="名古屋市中区", station="nagoya",
         area_type="商業地", open_date="2016-11-01", close_date=None, seats=24, floor_m2=125, base=24,
         open_time="09:00", close_time="20:00", lat=35.1709, lon=136.9084, gas=True),
    dict(store_id="S09", store_name="金沢香林坊店", prefecture="石川県", city="金沢市", station="kanazawa",
         area_type="観光地", open_date="2025-04-18", close_date=None, seats=18, floor_m2=90, base=16,
         open_time="09:00", close_time="19:00", lat=36.5613, lon=136.6537, gas=False),
    dict(store_id="S10", store_name="京都四条店", prefecture="京都府", city="京都市下京区", station="kyoto",
         area_type="観光地", open_date="2015-04-01", close_date=None, seats=22, floor_m2=110, base=29,
         open_time="08:00", close_time="20:00", lat=35.0038, lon=135.7687, gas=True),
    dict(store_id="S11", store_name="梅田店", prefecture="大阪府", city="大阪市北区", station="osaka",
         area_type="駅前", open_date="2013-10-01", close_date=None, seats=30, floor_m2=155, base=33,
         open_time="07:30", close_time="21:00", lat=34.7025, lon=135.4959, gas=False),
    dict(store_id="S12", store_name="心斎橋店", prefecture="大阪府", city="大阪市中央区", station="osaka",
         area_type="繁華街", open_date="2017-07-01", close_date="2025-12-28", seats=20, floor_m2=100, base=20,
         open_time="10:00", close_time="21:00", lat=34.6751, lon=135.5010, gas=False),
    dict(store_id="S13", store_name="神戸三宮店", prefecture="兵庫県", city="神戸市中央区", station="kobe",
         area_type="商業地", open_date="2016-03-01", close_date=None, seats=22, floor_m2=110, base=22,
         open_time="09:00", close_time="20:00", lat=34.6946, lon=135.1953, gas=False),
    dict(store_id="S14", store_name="広島紙屋町店", prefecture="広島県", city="広島市中区", station="hiroshima",
         area_type="商業地", open_date="2018-09-01", close_date=None, seats=18, floor_m2=90, base=17,
         open_time="09:00", close_time="20:00", lat=34.3955, lon=132.4560, gas=False),
    dict(store_id="S15", store_name="福岡天神店", prefecture="福岡県", city="福岡市中央区", station="fukuoka",
         area_type="繁華街", open_date="2014-11-01", close_date=None, seats=28, floor_m2=140, base=28,
         open_time="08:00", close_time="21:00", lat=33.5911, lon=130.3990, gas=True),
    dict(store_id="S16", store_name="那覇国際通り店", prefecture="沖縄県", city="那覇市", station="naha",
         area_type="観光地", open_date="2025-11-21", close_date=None, seats=16, floor_m2=80, base=16,
         open_time="10:00", close_time="21:00", lat=26.2155, lon=127.6870, gas=False),
]

EC_STORE = dict(store_id="W01", store_name="オンラインストア", prefecture="東京都", city="渋谷区", station="tokyo",
                area_type="EC", open_date="2016-01-15", close_date=None, seats=0, floor_m2=0, base=0,
                open_time="00:00", close_time="23:59", lat=None, lon=None, gas=False)

OTHER_SITES = [
    dict(site_id="F01", site_name="熊谷工場", site_type="工場", prefecture="埼玉県", city="熊谷市", station="kumagaya",
         floor_m2=5200, open_date="2010-04-01", lat=36.1473, lon=139.3886, gas=True,
         building_type="自社工場", electricity_contract="高圧（業務用）", contract_kw=900),
    dict(site_id="D01", site_name="千葉物流センター", site_type="物流センター", prefecture="千葉県", city="千葉市美浜区",
         station="chiba", floor_m2=3400, open_date="2015-02-01", lat=35.6420, lon=140.0500, gas=False,
         building_type="賃借倉庫", electricity_contract="高圧（業務用）", contract_kw=420),
    dict(site_id="H01", site_name="本社", site_type="本社", prefecture="東京都", city="渋谷区", station="tokyo",
         floor_m2=2100, open_date="2012-03-01", lat=35.6580, lon=139.7016, gas=False,
         building_type="オフィスビル（賃借）", electricity_contract="高圧（業務用）", contract_kw=350),
    dict(site_id="B01", site_name="大阪支店", site_type="支店", prefecture="大阪府", city="大阪市北区", station="osaka",
         floor_m2=320, open_date="2016-04-01", lat=34.7055, lon=135.4983, gas=False,
         building_type="オフィスビル（賃借）", electricity_contract="低圧", contract_kw=45),
    dict(site_id="B02", site_name="名古屋支店", site_type="支店", prefecture="愛知県", city="名古屋市中村区", station="nagoya",
         floor_m2=240, open_date="2018-04-01", lat=35.1709, lon=136.8816, gas=False,
         building_type="オフィスビル（賃借）", electricity_contract="低圧", contract_kw=35),
    dict(site_id="B03", site_name="福岡支店", site_type="支店", prefecture="福岡県", city="福岡市博多区", station="fukuoka",
         floor_m2=210, open_date="2019-04-01", lat=33.5902, lon=130.4207, gas=False,
         building_type="オフィスビル（賃借）", electricity_contract="低圧", contract_kw=30),
]

PREFECTURES = [
    # (name, population in 10k, region, coffee affinity)
    ("北海道", 509, "北海道", 0.95), ("青森県", 118, "東北", 0.8), ("岩手県", 116, "東北", 0.8),
    ("宮城県", 226, "東北", 0.95), ("秋田県", 92, "東北", 0.8), ("山形県", 104, "東北", 0.8),
    ("福島県", 177, "東北", 0.85), ("茨城県", 282, "関東", 0.95), ("栃木県", 190, "関東", 0.9),
    ("群馬県", 190, "関東", 0.9), ("埼玉県", 733, "関東", 1.05), ("千葉県", 627, "関東", 1.05),
    ("東京都", 1404, "関東", 1.25), ("神奈川県", 922, "関東", 1.15), ("新潟県", 213, "中部", 0.85),
    ("富山県", 101, "中部", 0.9), ("石川県", 111, "中部", 1.0), ("福井県", 75, "中部", 0.9),
    ("山梨県", 80, "中部", 0.9), ("長野県", 202, "中部", 0.95), ("岐阜県", 194, "中部", 0.95),
    ("静岡県", 355, "中部", 0.95), ("愛知県", 748, "中部", 1.1), ("三重県", 174, "近畿", 0.9),
    ("滋賀県", 141, "近畿", 1.0), ("京都府", 254, "近畿", 1.3), ("大阪府", 876, "近畿", 1.1),
    ("兵庫県", 537, "近畿", 1.2), ("奈良県", 131, "近畿", 1.05), ("和歌山県", 90, "近畿", 0.85),
    ("鳥取県", 54, "中国", 0.85), ("島根県", 65, "中国", 0.8), ("岡山県", 185, "中国", 0.95),
    ("広島県", 276, "中国", 1.0), ("山口県", 131, "中国", 0.85), ("徳島県", 70, "四国", 0.85),
    ("香川県", 93, "四国", 0.9), ("愛媛県", 131, "四国", 0.85), ("高知県", 67, "四国", 0.8),
    ("福岡県", 510, "九州", 1.05), ("佐賀県", 80, "九州", 0.85), ("長崎県", 128, "九州", 0.85),
    ("熊本県", 172, "九州", 0.9), ("大分県", 111, "九州", 0.85), ("宮崎県", 106, "九州", 0.85),
    ("鹿児島県", 157, "九州", 0.85), ("沖縄県", 147, "九州・沖縄", 0.9),
]
