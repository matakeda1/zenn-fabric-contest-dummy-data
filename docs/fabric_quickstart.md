# Microsoft Fabric（試用版）での取り込み手順

Fabric の試用版（トライアル）容量で、このダミーデータを使い始めるまでの手順をまとめます。
試用版では Data Factory・Data Engineering（ノートブック／Spark）・Real-Time Intelligence・Power BI など Fabric の全ワークロードを使えます。
**Copilot、データ エージェント、AI 関数などの AI 機能は試用版では使えない**点に注意してください（[Fabric 試用版](https://learn.microsoft.com/ja-jp/fabric/fundamentals/fabric-trial)）。

## 1. ワークスペースとレイクハウスを作る

1. 試用版の容量を割り当てたワークスペースを作成します。
2. ワークスペースで **新しい項目 → レイクハウス** を作成します（例：`contoso_lh`）。

## 2. ファイルをアップロードする

1. ZIP を展開し、`data` フォルダーの中身を用意します。
2. レイクハウスのエクスプローラーで **Files** の「…」→ **アップロード → フォルダーのアップロード** を選び、`01_retail_ec` などのフォルダーを丸ごとアップロードします。
   - フォルダーを丸ごとアップロードするときは「フォルダーのアップロード」を使います（「ファイルのアップロード」ではフォルダーを選べません）。
   - OneLake ファイル エクスプローラー（Windows アプリ）を使うと、エクスプローラーからドラッグ＆ドロップでコピーできます。

## 3. CSV をテーブルにする（ノーコード）

Files 上の CSV ファイル、またはフォルダーを右クリックして **テーブルに読み込む（Load to Tables）** を選びます（[Load to Delta Lake tables](https://learn.microsoft.com/ja-jp/fabric/data-engineering/load-to-tables)）。

- テーブル名は英小文字・数字・アンダースコアのみ使えます（例：`orders`）。
- **年や月で分割したテーブルはフォルダーごと 1 テーブルにできます。** 次のフォルダーは「フォルダーを新しいテーブルに読み込む」でそのまま 1 つのテーブルになります。
  - `01_retail_ec/orders/` → `orders`
  - `01_retail_ec/order_lines/` → `order_lines`
  - `02_manufacturing_iot/sensor_readings/` → `sensor_readings`
  - `05_facility_energy/energy_usage_30min/` → `energy_usage_30min`
- `06_customer_support/inquiries.csv` は本文に改行を含むため、ノーコードの読み込みでは行が崩れることがあります。ノートブックで `inquiries.jsonl` を読むのが確実です（下記）。

## 4. ノートブックで読み込む（PySpark）

レイクハウスを既定のレイクハウスとして追加したノートブックで実行します。

```python
from pyspark.sql import functions as F

# 年ごとに分割された CSV をまとめて読む
orders = (spark.read.option("header", True).option("inferSchema", True)
          .csv("Files/01_retail_ec/orders/"))
orders.write.mode("overwrite").saveAsTable("orders")

# 問い合わせ（本文に改行あり）は JSON Lines 版が扱いやすい
inq = spark.read.json("Files/06_customer_support/inquiries.jsonl")
inq.write.mode("overwrite").saveAsTable("inquiries")

# CSV 版を読む場合は multiLine を指定
inq_csv = (spark.read.option("header", True).option("multiLine", True).option("escape", '"')
           .csv("Files/06_customer_support/inquiries.csv"))
```

### アプリの操作ログ（JSON、スキーマが 2 種類）

```python
raw = spark.read.json("Files/08_app_logs/events/")

# 新しいアプリ（v5 系、ネストあり）
v5 = (raw.where(F.col("schema_version") == "5")
      .select("event_id", "event_name",
              F.to_timestamp("event_timestamp").alias("event_ts"),
              F.col("user.anonymous_id").alias("anonymous_id"),
              F.col("session.session_id").alias("session_id"),
              F.col("device.platform").alias("platform"),
              F.col("device.app_version").alias("app_version"),
              F.col("params.product_id").alias("product_id"),
              F.col("params.order_id").alias("order_id")))

# 旧アプリ（4.9.3、フラット・UNIX エポックミリ秒）
legacy = (raw.where(F.col("eventId").isNotNull())
          .select(F.col("eventId").alias("event_id"), F.col("name").alias("event_name"),
                  (F.col("ts") / 1000).cast("timestamp").alias("event_ts"),
                  F.col("uid").alias("anonymous_id"), F.col("sid").alias("session_id"),
                  F.col("itemId").alias("product_id"), F.col("orderNo").alias("order_id")))

# 購入イベントの商品明細（配列）を展開
items = (raw.where(F.col("event_name") == "purchase")
         .select(F.col("params.order_id").alias("order_id"), F.explode("params.items").alias("it"))
         .select("order_id", "it.product_id", "it.quantity", "it.price"))
```

重複イベント（同じ `event_id`）や、タイムゾーン表記の誤り（`Z`）が含まれます。`dropDuplicates(["event_id"])` などで整えてから分析してください。

### Excel 帳票をまとめる（pandas）

```python
import glob, pandas as pd

# 既定のレイクハウスは /lakehouse/default/ にマウントされます
base = "/lakehouse/default/Files/07_excel_reports/daily_reports"
for path in sorted(glob.glob(f"{base}/S01_sapporo/*.xlsx")):
    df = pd.read_excel(path, header=None)   # 書式ごとにセル位置を指定して値を取り出す
    ...

# 那覇店は Shift_JIS の CSV
naha = pd.read_csv(f"{base}/S16_naha/naha_daily_202610.csv", encoding="cp932", thousands=",")
```

`openpyxl` が見つからない場合はノートブックの先頭で `%pip install openpyxl` を実行してください。
店舗ごとの書式の違いは `data/07_excel_reports/README.md` を参照してください。

## 5. リアルタイム処理（Real-Time Intelligence）

### イベントハウスにセンサー値を取り込む

1. ワークスペースで **イベントハウス** を作成します（KQL データベースが自動で作られます）。
2. KQL データベースの **データの取得** から、`sensor_readings_2026-06.csv` などを取り込みます（ローカル ファイルまたは OneLake）。

### ストリーミングで流す（任意）

`tools/replay_sensor_to_eventstream.py` で、1 分値を「いま発生しているデータ」のようにイベントストリームのカスタム エンドポイントへ送れます。

```bash
pip install pandas azure-eventhub
# イベントストリームのカスタム エンドポイント（Event Hub）の接続文字列
export EVENTSTREAM_CONNECTION_STRING="Endpoint=sb://...;EntityPath=..."
python tools/replay_sensor_to_eventstream.py \
  --file data/02_manufacturing_iot/sensor_readings/sensor_readings_2026-06.csv \
  --start "2026-06-10 06:00" --speed 60 --retime
```

`--dry-run` を付けると送信せずに内容を表示します（Azure のリソースなしで確認できます）。

### KQL の例（異常検知）

```kusto
sensor_readings
| where equipment_id == "GRD-01" and status == "RUN"
| make-series vib = avg(vibration_mm_s) default = real(null) on timestamp step 1h
| extend vib = series_fill_linear(vib)
| extend (anomalies, score, baseline) = series_decompose_anomalies(vib, 2.5)
| render anomalychart with (anomalycolumns = anomalies)
```

## 6. Power BI でレポートを作る

レイクハウスのテーブルからセマンティック モデルを作成し（Direct Lake）、リレーションシップを設定してレポートを作ります。
主なリレーションシップは README の ER 図と `docs/data_dictionary.md` の「外部キー」を参照してください。

## 7. 自作の画面から Fabric のデータを読む

| 方法 | ポイント |
|---|---|
| SQL 分析エンドポイント／ウェアハウス | SQL 接続文字列（TDS、TCP 1433）で接続します。認証は Microsoft Entra ID（ユーザーまたはサービス プリンシパル）のみで、SQL 認証には対応していません（[接続](https://learn.microsoft.com/ja-jp/fabric/data-warehouse/connectivity)）。 |
| API for GraphQL | レイクハウス（SQL 分析エンドポイント経由）やウェアハウスを公開できます。**公開するテーブル・ビューには主キーが必要**です（[API for GraphQL](https://learn.microsoft.com/ja-jp/fabric/data-engineering/api-graphql-overview)）。SQL 分析エンドポイント経由のデータは読み取りのみです。 |
| OneLake から CSV を書き出す | 加工済みのテーブルを CSV に書き出し、自作の画面で読み込みます。 |

このデータは全テーブルに主キーとなる列を用意しています（`docs/data_dictionary.md` の「主キー」）。
ウェアハウスに取り込む場合は、次のように主キー制約（NOT ENFORCED）を付けられます。

```sql
ALTER TABLE dbo.stores ADD CONSTRAINT pk_stores PRIMARY KEY NONCLUSTERED (store_id) NOT ENFORCED;
```

## 8. 非構造データと AI

試用版では AI 関数を使えないため、問い合わせ本文などの非構造データは次のように扱います。

- **AI を使わない処理**：ノートブックでテキスト集計、形態素解析（例：`%pip install janome`）、正規表現での注文番号・ロット番号の抽出、Excel・JSON の取り込みと整形。
- **Fabric の外部の AI サービスと組み合わせる（任意）**：参加者自身の Azure サブスクリプションで Microsoft Foundry（Azure OpenAI）のモデルをデプロイし、ノートブックから Python の `openai` ライブラリで呼び出して要約・分類・抽出を行い、結果をレイクハウスに書き戻します（[Responses API](https://learn.microsoft.com/ja-jp/azure/foundry/openai/how-to/responses)）。Azure 側の利用料は参加者の負担です。
