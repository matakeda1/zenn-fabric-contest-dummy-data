"""Replay 1-minute sensor readings to a Fabric Eventstream custom endpoint (Event Hub compatible) as if they were live.

    pip install pandas azure-eventhub
    set EVENTSTREAM_CONNECTION_STRING=Endpoint=sb://...;SharedAccessKeyName=...;SharedAccessKey=...;EntityPath=...
    python tools/replay_sensor_to_eventstream.py --file data/02_manufacturing_iot/sensor_readings/sensor_readings_2026-06.csv \
        --start "2026-06-15 06:00" --speed 60

--speed 60 sends one minute of data per second. --retime stamps events with the current time (original kept in source_timestamp).
--dry-run prints the events instead of sending them (no Azure resources needed).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--start", default=None, help="first timestamp to send, e.g. '2026-06-15 06:00'")
    ap.add_argument("--equipment", default=None, help="comma separated equipment_id filter, e.g. GRD-01,PKG-02")
    ap.add_argument("--speed", type=float, default=60.0, help="data minutes per real second")
    ap.add_argument("--limit", type=int, default=0, help="stop after N minutes of data (0 = all)")
    ap.add_argument("--retime", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    df = pd.read_csv(a.file)
    if a.start:
        df = df[df["timestamp"] >= a.start]
    if a.equipment:
        df = df[df["equipment_id"].isin(a.equipment.split(","))]
    producer = None
    if not a.dry_run:
        conn = os.environ.get("EVENTSTREAM_CONNECTION_STRING")
        if not conn:
            sys.exit("EVENTSTREAM_CONNECTION_STRING is not set (or use --dry-run)")
        from azure.eventhub import EventData, EventHubProducerClient

        producer = EventHubProducerClient.from_connection_string(conn)
    sent = 0
    for i, (ts, g) in enumerate(df.groupby("timestamp", sort=True)):
        if a.limit and i >= a.limit:
            break
        recs = []
        for r in g.to_dict(orient="records"):
            r = {k: (None if isinstance(v, float) and pd.isna(v) else v) for k, v in r.items()}
            if a.retime:
                r["source_timestamp"] = r["timestamp"]
                r["timestamp"] = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
            recs.append(r)
        if a.dry_run:
            for r in recs:
                print(json.dumps(r, ensure_ascii=False))
        else:
            batch = producer.create_batch()
            for r in recs:
                batch.add(EventData(json.dumps(r, ensure_ascii=False)))
            producer.send_batch(batch)
        sent += len(recs)
        time.sleep(1.0 / a.speed if a.speed > 0 else 0)
    if producer:
        producer.close()
    print(f"sent {sent} events", file=sys.stderr)


if __name__ == "__main__":
    main()
