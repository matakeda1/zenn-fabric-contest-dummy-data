"""Product catalog, price history and promotions (Contoso Coffee)."""
from __future__ import annotations

from datetime import date

import pandas as pd

# category, subcategory, temp(hot/iced/any/none), channel(store/ec/both), tax(food/goods), lot line
# price = list price (税抜) as of 2024-01. season = (start "MM-DD", end "MM-DD") inclusive, may wrap the year.
P = []


def add(pid, name, cat, sub, size, price, cost_rate, channel, temp="none", tax="food", line=None,
        launch="2012-01-01", end=None, season=None, store_w=1.0, ec_w=1.0, report_cat=None):
    P.append(dict(product_id=pid, product_name=name, category=cat, subcategory=sub, size=size,
                  list_price=price, cost_rate=cost_rate, channel=channel, temp_type=temp, tax_class=tax,
                  production_line=line, launch_date=launch, end_date=end, season=season,
                  store_w=store_w, ec_w=ec_w, report_category=report_cat or cat))


# --- コーヒー豆 ---------------------------------------------------------------
add("P001", "ハウスブレンド 200g", "コーヒー豆", "ブレンド", "200g", 1300, 0.40, "both", line="RST", store_w=3.0, ec_w=3.2)
add("P002", "ハウスブレンド 500g", "コーヒー豆", "ブレンド", "500g", 2900, 0.40, "both", line="RST", store_w=1.0, ec_w=2.2)
add("P003", "モーニングブレンド 200g", "コーヒー豆", "ブレンド", "200g", 1250, 0.40, "both", line="RST", store_w=1.6, ec_w=1.5)
add("P004", "ディープロースト 200g", "コーヒー豆", "ブレンド", "200g", 1350, 0.40, "both", line="RST", store_w=1.8, ec_w=1.9)
add("P005", "ディープロースト 500g", "コーヒー豆", "ブレンド", "500g", 3000, 0.40, "both", line="RST", store_w=0.5, ec_w=1.2)
add("P006", "カフェインレスブレンド 200g", "コーヒー豆", "ブレンド", "200g", 1450, 0.42, "both", line="RST",
    launch="2025-10-01", store_w=1.2, ec_w=1.8)
add("P007", "エチオピア イルガチェフェ 200g", "コーヒー豆", "シングルオリジン", "200g", 1600, 0.42, "both", line="RST", store_w=1.1, ec_w=1.3)
add("P008", "ケニア ニエリ 200g", "コーヒー豆", "シングルオリジン", "200g", 1700, 0.42, "both", line="RST", store_w=0.7, ec_w=0.9)
add("P009", "グアテマラ アンティグア 200g", "コーヒー豆", "シングルオリジン", "200g", 1450, 0.42, "both", line="RST", store_w=0.9, ec_w=1.0)
add("P010", "コロンビア ウィラ 200g", "コーヒー豆", "シングルオリジン", "200g", 1400, 0.42, "both", line="RST", store_w=0.9, ec_w=1.0)
add("P011", "ブラジル セラード 200g", "コーヒー豆", "シングルオリジン", "200g", 1250, 0.42, "both", line="RST", store_w=1.0, ec_w=1.0)
add("P012", "インドネシア マンデリン 200g", "コーヒー豆", "シングルオリジン", "200g", 1500, 0.42, "both", line="RST", store_w=0.9, ec_w=1.0)
add("P013", "コスタリカ タラス 200g", "コーヒー豆", "シングルオリジン", "200g", 1550, 0.42, "both", line="RST", store_w=0.6, ec_w=0.7)
add("P014", "イエメン モカ・マタリ 200g", "コーヒー豆", "シングルオリジン", "200g", 2200, 0.45, "both", line="RST",
    end="2025-06-30", store_w=0.5, ec_w=0.7)
add("P015", "パナマ ゲイシャ 100g", "コーヒー豆", "シングルオリジン", "100g", 3800, 0.50, "both", line="RST",
    season=("11-01", "01-31"), store_w=0.4, ec_w=0.9)
add("P016", "春のブレンド 200g", "コーヒー豆", "季節のブレンド", "200g", 1400, 0.40, "both", line="RST",
    season=("03-01", "05-31"), store_w=1.2, ec_w=1.0)
add("P017", "アイスブレンド 200g", "コーヒー豆", "季節のブレンド", "200g", 1400, 0.40, "both", line="RST",
    season=("06-01", "08-31"), store_w=1.3, ec_w=1.1)
add("P018", "秋のブレンド 200g", "コーヒー豆", "季節のブレンド", "200g", 1400, 0.40, "both", line="RST",
    season=("09-01", "11-30"), store_w=1.2, ec_w=1.0)
add("P019", "ホリデーブレンド 200g", "コーヒー豆", "季節のブレンド", "200g", 1500, 0.40, "both", line="RST",
    season=("12-01", "02-28"), store_w=1.4, ec_w=1.3)
# --- ドリップバッグ -------------------------------------------------------------
add("P020", "ドリップバッグ ハウスブレンド 5袋", "ドリップバッグ", "ドリップバッグ", "5袋", 700, 0.38, "both", line="PKG", store_w=2.0, ec_w=1.0)
add("P021", "ドリップバッグ ハウスブレンド 10袋", "ドリップバッグ", "ドリップバッグ", "10袋", 1300, 0.38, "both", line="PKG", store_w=1.2, ec_w=2.0)
add("P022", "ドリップバッグ ハウスブレンド 30袋", "ドリップバッグ", "ドリップバッグ", "30袋", 3600, 0.38, "ec", line="PKG", ec_w=1.6)
add("P023", "ドリップバッグ 飲み比べセット 10袋", "ドリップバッグ", "ドリップバッグ", "10袋", 1500, 0.40, "both", line="PKG", store_w=1.0, ec_w=1.5)
add("P024", "ドリップバッグ 深煎り 10袋", "ドリップバッグ", "ドリップバッグ", "10袋", 1350, 0.38, "both", line="PKG", store_w=0.6, ec_w=1.0)
add("P025", "ドリップバッグ カフェインレス 10袋", "ドリップバッグ", "ドリップバッグ", "10袋", 1450, 0.40, "both", line="PKG",
    launch="2025-10-01", store_w=0.6, ec_w=1.2)
# --- ドリンク（店舗のみ） -----------------------------------------------------------
add("P030", "ブレンドコーヒー", "ドリンク", "コーヒー", "Regular", 420, 0.22, "store", temp="hot", store_w=9.0)
add("P031", "アイスコーヒー", "ドリンク", "コーヒー", "Regular", 450, 0.22, "store", temp="iced", store_w=8.0)
add("P032", "カフェラテ", "ドリンク", "エスプレッソ", "Regular", 520, 0.25, "store", temp="hot", store_w=7.0)
add("P033", "アイスカフェラテ", "ドリンク", "エスプレッソ", "Regular", 550, 0.25, "store", temp="iced", store_w=6.5)
add("P034", "カプチーノ", "ドリンク", "エスプレッソ", "Regular", 520, 0.25, "store", temp="hot", store_w=2.5)
add("P035", "エスプレッソ", "ドリンク", "エスプレッソ", "Single", 380, 0.20, "store", temp="hot", store_w=1.0)
add("P036", "カフェモカ", "ドリンク", "エスプレッソ", "Regular", 580, 0.27, "store", temp="any", store_w=1.8)
add("P037", "コールドブリュー", "ドリンク", "コーヒー", "Regular", 580, 0.24, "store", temp="iced",
    launch="2025-05-15", store_w=3.5)
add("P038", "抹茶ラテ", "ドリンク", "ティー", "Regular", 560, 0.28, "store", temp="any", store_w=2.6)
add("P039", "ほうじ茶ラテ", "ドリンク", "ティー", "Regular", 540, 0.27, "store", temp="any", store_w=1.8)
add("P040", "チャイラテ", "ドリンク", "ティー", "Regular", 540, 0.27, "store", temp="any", store_w=1.3)
add("P041", "ココア", "ドリンク", "その他", "Regular", 500, 0.27, "store", temp="hot", store_w=1.2)
add("P042", "コーヒーフラッペ", "ドリンク", "フラッペ", "Regular", 620, 0.30, "store", temp="iced",
    season=("06-01", "09-30"), store_w=3.0)
add("P043", "桜ラテ", "ドリンク", "季節限定", "Regular", 600, 0.30, "store", temp="any",
    season=("03-01", "04-15"), store_w=3.0)
add("P044", "パンプキンスパイスラテ", "ドリンク", "季節限定", "Regular", 620, 0.30, "store", temp="any",
    season=("09-15", "11-30"), store_w=2.6)
add("P045", "ジンジャーラテ", "ドリンク", "季節限定", "Regular", 580, 0.29, "store", temp="hot",
    season=("12-01", "02-28"), store_w=2.4)
add("P046", "オーツミルクラテ", "ドリンク", "エスプレッソ", "Regular", 600, 0.28, "store", temp="any",
    launch="2024-09-01", store_w=2.0)
# --- 焼き菓子・スイーツ ---------------------------------------------------------------
add("P050", "クッキー（プレーン）", "焼き菓子", "クッキー", "1枚", 260, 0.33, "store", line="OVN", store_w=2.4)
add("P051", "チョコチップクッキー", "焼き菓子", "クッキー", "1枚", 280, 0.34, "store", line="OVN", store_w=2.2)
add("P052", "フィナンシェ", "焼き菓子", "焼き菓子", "1個", 300, 0.34, "both", line="OVN", store_w=2.0, ec_w=0.5)
add("P053", "マドレーヌ", "焼き菓子", "焼き菓子", "1個", 280, 0.34, "both", line="OVN", store_w=1.6, ec_w=0.4)
add("P054", "スコーン", "焼き菓子", "スコーン", "1個", 350, 0.32, "store", line="OVN", store_w=1.8)
add("P055", "バナナブレッド", "焼き菓子", "ケーキ", "1切れ", 380, 0.33, "store", line="OVN", store_w=1.3)
add("P056", "チーズケーキ", "焼き菓子", "ケーキ", "1個", 480, 0.36, "store", line="OVN", store_w=1.8)
add("P057", "ガトーショコラ", "焼き菓子", "ケーキ", "1個", 520, 0.37, "store", line="OVN", store_w=1.4)
add("P058", "季節のタルト", "焼き菓子", "ケーキ", "1個", 560, 0.38, "store", store_w=1.2)
add("P059", "焼き菓子アソート 8個入", "焼き菓子", "ギフト菓子", "8個", 2400, 0.40, "both", line="OVN", store_w=0.8, ec_w=1.6)
add("P060", "バウムクーヘン", "焼き菓子", "ギフト菓子", "1本", 1800, 0.40, "both", store_w=0.5, ec_w=1.0)
# --- ボトル飲料 -------------------------------------------------------------------
add("P070", "ボトルコーヒー 無糖 500ml", "ボトル飲料", "RTD", "500ml", 300, 0.55, "both", store_w=1.2, ec_w=0.5)
add("P071", "ボトルコーヒー 微糖 500ml", "ボトル飲料", "RTD", "500ml", 300, 0.55, "both", store_w=0.9, ec_w=0.3)
add("P072", "カフェオレ ボトル 500ml", "ボトル飲料", "RTD", "500ml", 320, 0.55, "store", store_w=0.9)
add("P073", "アイスコーヒーリキッド 1L", "ボトル飲料", "RTD", "1L", 980, 0.50, "both", store_w=0.7, ec_w=1.6)
add("P074", "コールドブリュー ボトル 500ml", "ボトル飲料", "RTD", "500ml", 420, 0.52, "both",
    launch="2025-05-15", store_w=0.9, ec_w=0.7)
# --- ギフト ---------------------------------------------------------------------
add("P080", "コーヒーギフト 豆3種セット", "ギフト", "ギフトセット", "200g×3", 4500, 0.45, "both", line="RST", store_w=0.5, ec_w=1.6)
add("P081", "ドリップバッグギフト 20袋", "ギフト", "ギフトセット", "20袋", 3300, 0.43, "both", line="PKG", store_w=0.6, ec_w=1.8)
add("P082", "コーヒー＆焼き菓子ギフト", "ギフト", "ギフトセット", "1箱", 5000, 0.45, "both", store_w=0.4, ec_w=1.5)
add("P083", "バレンタインギフト", "ギフト", "季節ギフト", "1箱", 3800, 0.45, "both", season=("01-15", "02-14"), store_w=1.0, ec_w=2.5)
add("P084", "ホワイトデーギフト", "ギフト", "季節ギフト", "1箱", 3000, 0.45, "both", season=("02-20", "03-14"), store_w=0.8, ec_w=1.8)
add("P085", "お中元ギフト アイスコーヒーリキッド3本", "ギフト", "季節ギフト", "1L×3", 3600, 0.48, "both",
    season=("06-10", "08-15"), store_w=0.6, ec_w=3.0)
add("P086", "お歳暮ギフト プレミアムセット", "ギフト", "季節ギフト", "1箱", 6000, 0.46, "both",
    season=("11-15", "12-25"), store_w=0.6, ec_w=3.0)
# --- 器具・グッズ（標準税率） ------------------------------------------------------------
add("P090", "ドリッパー（陶器）", "器具・グッズ", "抽出器具", "1個", 2200, 0.50, "both", tax="goods", store_w=0.5, ec_w=0.8)
add("P091", "ペーパーフィルター 100枚", "器具・グッズ", "消耗品", "100枚", 440, 0.50, "both", tax="goods", store_w=1.0, ec_w=1.0)
add("P092", "コーヒーミル（手挽き）", "器具・グッズ", "抽出器具", "1台", 5800, 0.50, "both", tax="goods", store_w=0.2, ec_w=0.5)
add("P093", "電動コーヒーミル", "器具・グッズ", "抽出器具", "1台", 12800, 0.55, "ec", tax="goods", ec_w=0.4)
add("P094", "ドリップケトル", "器具・グッズ", "抽出器具", "1台", 6600, 0.52, "both", tax="goods", store_w=0.15, ec_w=0.4)
add("P095", "マグカップ（ロゴ）", "器具・グッズ", "グッズ", "1個", 1800, 0.45, "both", tax="goods", store_w=0.5, ec_w=0.5)
add("P096", "ステンレスタンブラー", "器具・グッズ", "グッズ", "1個", 3300, 0.45, "both", tax="goods", store_w=0.5, ec_w=0.6)
add("P097", "コーヒーキャニスター", "器具・グッズ", "グッズ", "1個", 2500, 0.48, "both", tax="goods", store_w=0.2, ec_w=0.4)
# --- 定期便（EC のみ） -----------------------------------------------------------------
add("P100", "定期便 ハウスブレンド 500g", "定期便", "定期便", "500g/月", 2700, 0.40, "sub", line="RST", launch="2024-06-01")
add("P101", "定期便 シングルオリジン 2種", "定期便", "定期便", "200g×2/月", 3000, 0.42, "sub", line="RST", launch="2024-06-01")
add("P102", "定期便 ドリップバッグ 30袋", "定期便", "定期便", "30袋/月", 3300, 0.40, "sub", line="PKG", launch="2024-06-01")
add("P103", "定期便 カフェインレス 500g", "定期便", "定期便", "500g/月", 3000, 0.42, "sub", line="RST", launch="2025-10-01")

PRICE_REVISIONS = [date(2025, 4, 1), date(2026, 4, 1)]


def _round(x, unit):
    return int(round(x / unit) * unit)


def revised_price(p: dict, rev: date, current: int) -> int:
    cat = p["category"]
    if rev == date(2025, 4, 1):
        if cat == "コーヒー豆":
            return _round(current * 1.10, 50)
        if cat == "ドリップバッグ":
            return _round(current * 1.08, 10)
        if cat == "ドリンク":
            return current + (40 if current >= 500 else 30)
        if cat == "ボトル飲料":
            return current + 20
        if cat == "ギフト":
            return _round(current * 1.05, 100)
        if cat == "定期便":
            return _round(current * 1.10, 100)
        return current
    if rev == date(2026, 4, 1):
        if cat == "焼き菓子":
            return current + (30 if current >= 400 else 20) if current < 1000 else _round(current * 1.06, 100)
        if cat == "コーヒー豆":
            return _round(current * 1.04, 50)
        return current
    return current


def catalog() -> pd.DataFrame:
    df = pd.DataFrame(P)
    return df


def price_history() -> pd.DataFrame:
    rows = []
    for p in P:
        start = max(date.fromisoformat(p["launch_date"]), date(2024, 1, 1))
        price = p["list_price"]
        valid_from = start
        for rev in PRICE_REVISIONS:
            if rev <= valid_from:
                continue
            newp = revised_price(p, rev, price)
            if newp != price:
                rows.append(dict(product_id=p["product_id"], valid_from=valid_from, valid_to=rev, unit_price=price))
                valid_from, price = rev, newp
        rows.append(dict(product_id=p["product_id"], valid_from=valid_from, valid_to=None, unit_price=price))
    df = pd.DataFrame(rows)
    df.insert(0, "price_id", [f"PR{i + 1:04d}" for i in range(len(df))])
    return df


def in_season(season, d: date) -> bool:
    if not season:
        return True
    s, e = season
    md = d.strftime("%m-%d")
    if s <= e:
        return s <= md <= e
    return md >= s or md <= e


def available(p: dict, d: date) -> bool:
    if d < date.fromisoformat(p["launch_date"]):
        return False
    if p["end_date"] and d > date.fromisoformat(p["end_date"]):
        return False
    return in_season(p["season"], d)


def promotions() -> pd.DataFrame:
    rows = []

    def add_promo(name, channel, start, end, target, dtype, value, code=None, note="", pcode=None):
        rows.append(dict(promotion_code=pcode or code, promotion_name=name, channel=channel, start_date=start, end_date=end,
                         target_category=target, discount_type=dtype, discount_value=value,
                         coupon_code=code, note=note))

    for y in (2024, 2025, 2026):
        add_promo(f"新春セール {y}", "オンラインストア", f"{y}-01-01", f"{y}-01-05", "全商品", "割引率", 10, f"NY{y}")
        add_promo(f"周年祭 {y}", "全チャネル", f"{y}-03-01", f"{y}-03-10", "コーヒー豆,ドリップバッグ", "割引率", 10, f"ANNIV{y}",
                  "創業記念。店舗・オンラインとも対象（オンラインはクーポンコード入力）", pcode=f"ANNIV{y}")
        add_promo(f"アイスコーヒーフェア {y}", "全チャネル", f"{y}-07-01", f"{y}-08-31", "ボトル飲料,ギフト", "フェア", 0, None,
                  "アイスコーヒーリキッド・お中元ギフトを特集（値引きなし）", pcode=f"ICEFAIR{y}")
        add_promo(f"コーヒーの日キャンペーン {y}", "全チャネル", f"{y}-10-01", f"{y}-10-07",
                  "コーヒー豆", "割引率", 20, f"COFFEEDAY{y}", "10/1 コーヒーの日。店舗は 10/1 のみ、オンラインは 10/7 まで")
    add_promo("ブラックフライデー 2024", "オンラインストア", "2024-11-22", "2024-12-01", "全商品", "割引率", 15, "BF2024")
    add_promo("ブラックフライデー 2025", "オンラインストア", "2025-11-21", "2025-11-30", "全商品", "割引率", 15, "BF2025")
    for y in (2024, 2025, 2026):
        add_promo(f"バレンタインフェア {y}", "全チャネル", f"{y}-01-20", f"{y}-02-14", "ギフト,焼き菓子", "フェア", 0, pcode=f"VDAY{y}")
    add_promo("アプリ会員クーポン（ドリンク50円引）", "店舗", "2024-01-01", None, "ドリンク", "値引額", 50, "APP50",
              "アプリ提示で利用。1会計1回")
    add_promo("定期便スタートキャンペーン", "オンラインストア", "2024-06-01", "2024-07-31", "定期便", "割引率", 20, "SUB20",
              "初回のみ 20% OFF")
    add_promo("心斎橋店 閉店セール", "店舗", "2025-12-15", "2025-12-28", "コーヒー豆,ドリップバッグ,器具・グッズ", "割引率", 20, None,
              "心斎橋店のみ", pcode="CLOSING-S12")
    df = pd.DataFrame(rows)
    df.insert(0, "promotion_id", [f"PM{i + 1:03d}" for i in range(len(df))])
    return df
