import json
import ast

INPUT_FILE  = "polymarket_btc15m_all.json"
OUTPUT_FILE = "polymarket_btc15m_extracted.json"


def get_meta(market):
    """Return eventMetadata dict if it contains priceToBeat, else None."""
    meta = market.get("eventMetadata")
    if meta and meta.get("priceToBeat") is not None:
        return meta
    for event in market.get("events", []):
        if isinstance(event, dict):
            meta = event.get("eventMetadata")
            if meta and meta.get("priceToBeat") is not None:
                return meta
    return None


def get_result(market):
    prices = market.get("outcomePrices")
    try:
        if isinstance(prices, str):
            prices = ast.literal_eval(prices)
        if isinstance(prices, list) and len(prices) == 2:
            up, dn = float(prices[0]), float(prices[1])
            if up == 1.0:
                return "Up"
            if dn == 1.0:
                return "Down"
    except Exception:
        pass
    return None




with open(INPUT_FILE) as f:
    markets = json.load(f)

# Sort chronologically by period end time
markets.sort(key=lambda m: m.get("endDate", ""))

# Drop all markets before the first one that has price metadata
first_meta_idx = next(
    (i for i, m in enumerate(markets) if get_meta(m) is not None), None
)
if first_meta_idx is None:
    raise RuntimeError("No markets with eventMetadata found.")

markets = markets[first_meta_idx:]

records = []
for m in markets:
    meta = get_meta(m)
    if meta is None:
        continue

    record = {
        "id":               m.get("id"),
        "start_time":       m.get("eventStartTime"),
        "end_time":         m.get("endDate"),
        "target_price":     meta.get("priceToBeat"),
        "expiration_value": meta.get("finalPrice"),
        "result":           get_result(m),
        "volume":           m.get("volumeNum"),
    }
    records.append(record)

with open(OUTPUT_FILE, "w") as f:
    json.dump(records, f, indent=2)

print(f"Extracted {len(records)} records → {OUTPUT_FILE}")
if records:
    print(f"  Date range: {records[0]['end_time']} → {records[-1]['end_time']}")
    no_final = sum(1 for r in records if r["expiration_value"] is None)
    if no_final:
        print(f"  Note: {no_final} records missing finalPrice (market not yet settled)")