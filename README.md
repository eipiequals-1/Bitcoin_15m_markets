# BTC 15-Minute Market Comparison: Kalshi vs Polymarket

Side-by-side analysis of BTC price prediction markets across Kalshi and Polymarket, aligned on 15-minute intervals.

## Files

| File | Description |
|------|-------------|
| `KalshiData3.ipynb` | Used to get Kalshi market data |
| `PolymarketData.ipynb` | Used to get Polymarket market data |
| `btc15m_comparison.py` | Tkinter GUI app to browse and compare Kalshi/Polymarket markets side-by-side |
| `kalshi_btc15m_all.json` | Raw Kalshi market records |
| `polymarket_btc15m_all.json` | Raw Polymarket market records |
| `polymarket_series_10192.json` | Raw Polymarket series |
| `extract_kalshi.py` | Extracts fields from `kalshi_btc15m_all.json` → `kalshi_btc15m_extracted.json` |
| `extract_polymarket.py` | Extracts fields from `polymarket_btc15m_all.json` → `polymarket_btc15m_extracted.json` |
| `kalshi_btc15m_extracted.json` | Kalshi market records (id, start/end time, target price, expiry value, result, volume) |
| `polymarket_btc15m_extracted.json` | Polymarket market records (id, start/end time, target price, expiry value, result, volume) |

## Data Pipeline

```
KashiData3.ipynb      →  kalshi_btc15m_all.json      →  extract_kalshi.py     →  kalshi_btc15m_extracted.json
PolymarketData.ipynb  →  polymarket_btc15m_all.json  →  extract_polymarket.py →  polymarket_btc15m_extracted.json
                                                                                               ↓
                                                                                    btc15m_comparison.py (GUI)
```

## Data Coverage Note

The extracted data only goes back approximately 2.5 months. For markets older than that, the metadata containing `target_price` and `expiration_value` could not be extracted — and were not included in the extracted data.

## Usage

**Run the comparison GUI:**
```bash
python btc15m_comparison.py
```

The GUI displays a table of 15-minute periods with columns for each platform's target price, expiry value, settlement result, and volume. Rows are color-coded by whether the two platforms agree on the result.

## Side Story about Data 

Kalshi and Polymarket are blocked on school Wifi so I downloaded the data to continue working at school. The raw `*_btc15m_all.json` files (which are not included in this folder) were laggy to read and difficult to transfer between my devices because they are >100 MB combined. Extracting only the necessary data for the GUI has solved both problems for me, but removing the extracted .json files would streamline the data pipeline.

