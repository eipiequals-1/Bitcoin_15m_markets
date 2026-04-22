# BTC 15-Minute Market Comparison: Kalshi vs Polymarket

Side-by-side analysis of BTC price prediction markets across Kalshi and Polymarket, aligned on 15-minute intervals.

## Files

| File | Description |
|------|-------------|
| `extract_kalshi.py` | Extracts fields from `kalshi_btc15m_all.json` → `kalshi_btc15m_extracted.json` |
| `extract_polymarket.py` | Extracts fields from `polymarket_btc15m_all.json` → `polymarket_btc15m_extracted.json` |
| `btc15m_comparison.py` | Tkinter GUI app to browse and compare Kalshi/Polymarket markets side-by-side |
| `kalshi_btc15m_extracted.json` | Kalshi market records (id, start/end time, target price, expiry value, result, volume) |
| `polymarket_btc15m_extracted.json` | Polymarket market records (id, start/end time, target price, expiry value, result, volume) |
| `KalshiData3.ipynb` | Notebook for exploring and analyzing Kalshi market data |
| `PolymarketData.ipynb` | Notebook for exploring and analyzing Polymarket market data |

## Data Pipeline

```
kalshi_btc15m_all.json      →  extract_kalshi.py     →  kalshi_btc15m_extracted.json
polymarket_btc15m_all.json  →  extract_polymarket.py →  polymarket_btc15m_extracted.json
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

## Side Story about Wonky Data 

Kalshi and Polymarket are blocked on school Wifi so I downloaded the data to continue working at school. It was also hard to transfer the raw `*_btc15m_all.json` files (which are not included in this folder) between my devices because they are >100 MB combined, so I decided to extract only the necessary data for the GUI. 

