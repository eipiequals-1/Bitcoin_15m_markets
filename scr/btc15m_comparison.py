import tkinter as tk
from tkinter import ttk
import json
from datetime import datetime, timezone
from pathlib import Path
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

_HERE = Path(__file__).parent
_DATA_DIR = _HERE.parent / "data"

# ── Data Loading ───────────────────────────────────────────────────────────────

def load_data():
    with open(_DATA_DIR / "kalshi_btc15m_extracted.json") as f:
        kalshi = json.load(f)
    with open(_DATA_DIR / "polymarket_btc15m_extracted.json") as f:
        polymarket = json.load(f)
    return kalshi, polymarket

kalshi_all, polymarket_all = load_data()

# ── Helpers ────────────────────────────────────────────────────────────────────

def parse_iso(dtstr):
    try:
        return datetime.fromisoformat(dtstr.replace("Z", "+00:00"))
    except Exception:
        return datetime.strptime(dtstr[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)

def time_key(dtstr):
    if not dtstr:
        return ""
    try:
        return parse_iso(dtstr).strftime("%Y-%m-%dT%H:%M")
    except Exception:
        return dtstr[:16]

def fmt_price(val):
    try:
        return f"{float(val):,.2f}"
    except (TypeError, ValueError):
        return "—" if val is None else str(val)

def kalshi_direction(result):
    if result == "yes":
        return "Up"
    if result == "no":
        return "Down"
    return None

def build_kalshi_index(markets):
    """Index by end_time key, keeping highest-volume market per slot."""
    index = {}
    for m in markets:
        key = time_key(m.get("end_time", ""))
        if not key:
            continue
        existing = index.get(key)
        if existing is None:
            index[key] = m
        else:
            try:
                if float(m.get("volume", 0)) > float(existing.get("volume", 0)):
                    index[key] = m
            except (TypeError, ValueError):
                pass
    return index

# ── GUI ────────────────────────────────────────────────────────────────────────

COLS = (
    "time_period",
    "k_target", "k_exp_value", "k_result", "k_volume",
    "pm_target", "pm_exp_value", "pm_result", "pm_volume",
    "match",
)
COL_HEADINGS = {
    "time_period":  "Time Period (UTC)",
    "k_target":     "K Target Price",
    "k_exp_value":  "K Expiry Value",
    "k_result":     "K Result",
    "k_volume":     "K Volume",
    "pm_target":    "PM Target Price",
    "pm_exp_value": "PM Expiry Value",
    "pm_result":    "PM Result",
    "pm_volume":    "PM Volume",
    "match":        "Match",
}
COL_WIDTHS = {
    "time_period": 200,
    "k_target":    110, "k_exp_value": 110, "k_result": 75, "k_volume": 100,
    "pm_target":   110, "pm_exp_value": 110, "pm_result": 75, "pm_volume": 100,
    "match":       65,
}


class CompareApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Kalshi vs Polymarket — BTC 15-Min Comparison")
        self.root.geometry("1420x700")

        self._filtered_pm = []
        self._page = 0
        self._page_size = 50
        self._load_markets()
        self._build_ui()
        self._apply_filter()

    def _load_markets(self):
        self.kalshi_index = build_kalshi_index(kalshi_all)
        self.pm_markets = sorted(polymarket_all, key=lambda m: m.get("end_time", ""), reverse=True)

    # ── UI ──────────────────────────────────────────────────────────────────

    def _build_ui(self):
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill="x")

        ttk.Label(top, text="Date (YYYY-MM-DD):").pack(side="left")
        self.date_var = tk.StringVar(value="")
        ttk.Entry(top, textvariable=self.date_var, width=12).pack(side="left", padx=(4, 10))
        ttk.Button(top, text="Filter", command=self._apply_filter).pack(side="left")
        ttk.Button(top, text="Reload Files", command=self._reload).pack(side="left", padx=(10, 0))
        ttk.Button(top, text="Plot Targets", command=self._plot_targets).pack(side="left", padx=(10, 0))

        ttk.Label(top, text="Plot N:").pack(side="left", padx=(14, 2))
        self.plot_n_var = tk.StringVar(value="50")
        ttk.Spinbox(top, textvariable=self.plot_n_var, from_=10, to=5000, increment=10,
                    width=6).pack(side="left")

        ttk.Separator(top, orient="vertical").pack(side="left", fill="y", padx=10)
        ttk.Button(top, text="◀ Prev", command=self._prev_page).pack(side="left")
        self.page_entry_var = tk.StringVar(value="1")
        page_entry = ttk.Entry(top, textvariable=self.page_entry_var, width=5, justify="center")
        page_entry.pack(side="left", padx=(4, 2))
        page_entry.bind("<Return>", lambda _: self._go_to_page())
        self.total_pages_var = tk.StringVar(value="/ 1")
        ttk.Label(top, textvariable=self.total_pages_var).pack(side="left", padx=(0, 4))
        ttk.Button(top, text="Next ▶", command=self._next_page).pack(side="left")

        self.summary_var = tk.StringVar(value="")
        ttk.Label(top, textvariable=self.summary_var).pack(side="right")

        frame = ttk.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=8, pady=(0, 4))

        self.tree = ttk.Treeview(frame, columns=COLS, show="headings", selectmode="browse")
        for c in COLS:
            self.tree.heading(c, text=COL_HEADINGS[c])
            self.tree.column(c, width=COL_WIDTHS.get(c, 100), anchor="center")

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.tag_configure("match_yes", background="#2d6a4f", foreground="white")
        self.tree.tag_configure("match_no",  background="#9b2335", foreground="white")

        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(self.root, textvariable=self.status_var, relief="sunken", padding=4).pack(fill="x")

    # ── Data ────────────────────────────────────────────────────────────────

    def _reload(self):
        global kalshi_all, polymarket_all
        kalshi_all, polymarket_all = load_data()
        self._load_markets()
        self.status_var.set("Reloaded from files.")
        self._apply_filter()

    def _apply_filter(self):
        date_str = self.date_var.get().strip()
        filtered = self.pm_markets
        if date_str:
            filtered = [m for m in filtered if m.get("end_time", "").startswith(date_str)]
        self._filtered_pm = filtered  # full set kept for plotting
        self._page = 0
        self._show_page()

    def _go_to_page(self):
        total_pages = max(1, -(-len(self._filtered_pm) // self._page_size))
        try:
            pg = int(self.page_entry_var.get()) - 1
            self._page = max(0, min(pg, total_pages - 1))
        except ValueError:
            pass
        self._show_page()

    def _prev_page(self):
        if self._page > 0:
            self._page -= 1
            self._show_page()

    def _next_page(self):
        total_pages = max(1, -(-len(self._filtered_pm) // self._page_size))  # ceiling div
        if self._page < total_pages - 1:
            self._page += 1
            self._show_page()

    def _show_page(self):
        ps   = self._page_size
        pg   = self._page
        page_data = self._filtered_pm[pg * ps : (pg + 1) * ps]
        total_pages = max(1, -(-len(self._filtered_pm) // ps))
        self.page_entry_var.set(str(pg + 1))
        self.total_pages_var.set(f"/ {total_pages}")

        rows = []
        for pm in page_data:
            start_time = pm.get("start_time", "")
            end_time   = pm.get("end_time", "")
            time_period = ""
            if start_time and end_time:
                try:
                    s = parse_iso(start_time)
                    e = parse_iso(end_time)
                    time_period = f"{s.strftime('%Y-%m-%d %H:%M')} – {e.strftime('%H:%M')} UTC"
                except Exception:
                    pass

            pm_target    = fmt_price(pm.get("target_price"))
            pm_exp_value = fmt_price(pm.get("expiration_value"))
            pm_res       = pm.get("result") or "—"
            pm_vol       = fmt_price(pm.get("volume"))

            key = time_key(end_time)
            km = self.kalshi_index.get(key)
            k_target    = fmt_price(km.get("target_price"))    if km else "—"
            k_exp_value = fmt_price(km.get("expiration_value")) if km else "—"
            k_result    = km.get("result") or "—"              if km else "—"
            k_vol       = fmt_price(km.get("volume"))          if km else "—"

            k_dir = kalshi_direction(k_result) if km else None
            if k_dir and pm_res != "—":
                match = "✓" if k_dir == pm_res else "✗"
            else:
                match = "—"

            rows.append({
                "time_period":  time_period,
                "k_target":     k_target,
                "k_exp_value":  k_exp_value,
                "k_result":     k_result,
                "k_volume":     k_vol,
                "pm_target":    pm_target,
                "pm_exp_value": pm_exp_value,
                "pm_result":    pm_res,
                "pm_volume":    pm_vol,
                "match":        match,
            })

        self._populate_tree(rows)
        date_str = self.date_var.get().strip()
        n_match = sum(1 for r in rows if r["match"] == "✓")
        n_total = sum(1 for r in rows if r["match"] in ("✓", "✗"))
        pct     = f"  ({100*n_match//n_total}%)" if n_total else ""
        start_idx = pg * ps + 1
        end_idx   = pg * ps + len(rows)
        self.summary_var.set(
            f"{start_idx}–{end_idx} of {len(self._filtered_pm)}  |  "
            f"{n_match}/{n_total} match{pct}  |  date: {date_str or 'all'}"
        )

    def _plot_targets(self):
        try:
            n = max(1, int(self.plot_n_var.get()))
        except ValueError:
            n = 50
        # Start at the top of the current page, take N markets, plot oldest → newest
        offset = self._page * self._page_size
        source = list(reversed(self._filtered_pm[offset : offset + n]))

        times, k_prices, pm_prices, matches = [], [], [], []
        for pm in source:
            end_time = pm.get("end_time", "")
            km = self.kalshi_index.get(time_key(end_time))
            try:
                k_val = float(km.get("target_price")) if km else None
                if k_val is not None and k_val < 1000:
                    k_val = None  # exclude bad data points
            except (TypeError, ValueError):
                k_val = None
            try:
                pm_val = float(pm.get("target_price"))
            except (TypeError, ValueError):
                pm_val = None
            if k_val is None and pm_val is None:
                continue
            try:
                t = parse_iso(end_time)
            except Exception:
                continue

            # Determine match status
            k_result = km.get("result") if km else None
            pm_result = pm.get("result")
            k_dir = kalshi_direction(k_result) if k_result else None
            if k_dir and pm_result and pm_result != "—":
                matched = k_dir == pm_result
            else:
                matched = None  # one or both results unknown

            times.append(t)
            k_prices.append(k_val)
            pm_prices.append(pm_val)
            matches.append(matched)

        if not times:
            self.status_var.set("No data to plot for the current filter.")
            return

        # Diff series (only where both exist)
        diff_times  = [t for t, k, p in zip(times, k_prices, pm_prices) if k is not None and p is not None]
        diff_values = [p - k for k, p in zip(k_prices, pm_prices) if k is not None and p is not None]

        win = tk.Toplevel(self.root)
        date_str = self.date_var.get().strip()
        win.title(f"Target Price Comparison — {date_str or 'all dates'} (last {n})")
        win.geometry("1100x640")

        fig = Figure(figsize=(11, 6.4), tight_layout=True)
        ax1 = fig.add_subplot(2, 1, 1)
        ax2 = fig.add_subplot(2, 1, 2, sharex=ax1)

        # ── Top: both target prices ──────────────────────────────────────
        k_t  = [t for t, k in zip(times, k_prices)  if k  is not None]
        k_v  = [k for k in k_prices  if k  is not None]
        pm_t = [t for t, p in zip(times, pm_prices) if p  is not None]
        pm_v = [p for p in pm_prices if p  is not None]

        ax1.plot(k_t,  k_v,  color="#1f77b4", linewidth=1.2, label="Kalshi floor strike")
        ax1.plot(pm_t, pm_v, color="#ff7f0e", linewidth=1.2, label="Polymarket priceToBeat", linestyle="--")

        # Highlight mismatches: band starts at t (result determination time)
        # and extends one full 15-min period to the right, since target_price[i]
        # equals expiration_value[i-1] — the result belongs to the window ending at t.
        from datetime import timedelta as _td
        period = _td(minutes=15)
        mismatch_label_added = False
        for t, matched in zip(times, matches):
            if matched is False:
                label = "Result mismatch" if not mismatch_label_added else "_nolegend_"
                ax1.axvspan(t, t + period, color="#e63946", alpha=0.25, label=label)
                ax2.axvspan(t, t + period, color="#e63946", alpha=0.25)
                mismatch_label_added = True

        ax1.set_ylabel("Price (USD)")
        ax1.set_title("Kalshi vs Polymarket — Target Price")
        ax1.legend(loc="upper left")
        ax1.grid(True, alpha=0.3)
        ax1.yaxis.set_major_formatter(
            __import__("matplotlib.ticker", fromlist=["FuncFormatter"]).FuncFormatter(
                lambda x, _: f"${x:,.0f}"
            )
        )

        # ── Bottom: PM − K difference ────────────────────────────────────
        colors = ["#2d6a4f" if d >= 0 else "#9b2335" for d in diff_values]
        ax2.bar(diff_times, diff_values, color=colors, width=0.008, alpha=0.8)
        ax2.axhline(0, color="black", linewidth=0.8, linestyle=":")
        ax2.set_ylabel("PM − K (USD)")
        ax2.set_title("Difference (Polymarket target − Kalshi floor strike)")
        ax2.grid(True, alpha=0.3)
        fig.autofmt_xdate(rotation=30)

        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        toolbar = NavigationToolbar2Tk(canvas, win)
        toolbar.update()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _populate_tree(self, rows):
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            tag = "match_yes" if row["match"] == "✓" else ("match_no" if row["match"] == "✗" else "")
            self.tree.insert("", "end", values=tuple(row[c] for c in COLS), tags=(tag,))


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    app = CompareApp(root)
    root.mainloop()