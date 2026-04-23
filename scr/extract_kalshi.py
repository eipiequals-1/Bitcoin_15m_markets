import json
from pathlib import Path

_DATA_DIR   = Path(__file__).parent.parent / "data"
INPUT_FILE  = _DATA_DIR / "kalshi_btc15m_all.json"
OUTPUT_FILE = _DATA_DIR / "kalshi_btc15m_extracted.json"

with open(INPUT_FILE) as f:
    markets = json.load(f)

# Sort chronologically by close_time
markets.sort(key=lambda m: m.get("close_time", ""))

records = []
for m in markets:
    result = m.get("result")

    try:
        expiration_value = float(m.get("expiration_value"))
    except (TypeError, ValueError):
        expiration_value = None

    try:
        volume = float(m.get("volume_fp"))
    except (TypeError, ValueError):
        volume = None

    record = {
        "id":               m.get("ticker"),
        "start_time":       m.get("open_time"),
        "end_time":         m.get("close_time"),
        "target_price":     m.get("floor_strike"),
        "expiration_value": expiration_value,
        "result":           result,
        "volume":           volume,
    }
    records.append(record)

with open(OUTPUT_FILE, "w") as f:
    json.dump(records, f, indent=2)

print(f"Extracted {len(records)} records → {OUTPUT_FILE}")
if records:
    print(f"  Date range: {records[0]['end_time']} → {records[-1]['end_time']}")
    no_result = sum(1 for r in records if r["result"] is None)
    if no_result:
        print(f"  Note: {no_result} records missing result (not yet settled)")