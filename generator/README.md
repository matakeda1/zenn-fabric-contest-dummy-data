# generator — ダミーデータの生成コード

`python generate.py` で `data/` のすべてのファイルを作り直します（約 10 分）。乱数シードは固定なので、同じコードからは同じデータができます。

```bash
pip install -r requirements.txt
python generate.py --out ../data --organizer-out ../_organizer_only/expected_outputs [--seed 2026]
```

## 構成

| ファイル | 役割 |
|---|---|
| `generate.py` | 全体の実行（依存関係の順に各モジュールを呼び出し、`data/MANIFEST.csv` を作成） |
| `contoso_data/config.py` | 期間、会社名、店舗・拠点、気象庁の観測所、都道府県、アプリ不具合の設定 |
| `contoso_data/weather.py` | 気象庁の日別データの取得・キャッシュ、日最高・最低気温からの時間別気温の推定 |
| `contoso_data/calendar_jp.py` | 祝日（2024〜2026）とカレンダー |
| `contoso_data/products.py` | 商品マスタ・価格改定・販促 |
| `contoso_data/people.py` | 部署・従業員（入社・退職・異動のタイムライン） |
| `contoso_data/manufacturing.py` | 02 設備・1 分ごとのセンサー値・故障履歴・製造ロット |
| `contoso_data/retail.py` | 01 会員・店舗の会計・オンライン注文・定期便・配送・返品 |
| `contoso_data/app_logs.py` | 08 アプリのイベントログ（01 のアプリ注文から購入セッションを作成） |
| `contoso_data/support.py` / `support_text.py` | 06 問い合わせ（他データの出来事から作成）と本文のテンプレート |
| `contoso_data/marketing.py` | 03 キャンペーン・広告費・リード・商談・受注 |
| `contoso_data/hr.py` | 04 勤怠・残業申請・研修・退職 |
| `contoso_data/energy.py` | 05 拠点・30 分ごとの電力・ガス・空調ログ |
| `contoso_data/excel_reports.py` | 07 店舗ごとに書式が違う日報・発注書と正解データ |

生成の順序：気象・組織 → 製造 → 小売 → アプリログ → 問い合わせ → 営業 → 人事 → エネルギー → 帳票。
後のデータは前のデータの出来事（注文・故障・不具合など）を参照して作られるため、データ同士の整合が取れています。

## 気象データ

`reference/jma_daily_weather.csv` は、気象庁「過去の気象データ検索」の日別値（14 地点、2024-01〜2026-10）を取得して加工したものです。
キャッシュがない場合は初回実行時に気象庁のサイトから取得します（`python -m contoso_data.weather` で再取得）。

出典：気象庁ホームページ（https://www.data.jma.go.jp/stats/etrn/index.php）の過去の気象データを加工して作成
