#!/usr/bin/env python3
import sys
from pathlib import Path
import yaml
import yfinance as yf

CONFIG = Path("config.yml")

def quote_52w_low(ticker: str):
    tk = yf.Ticker(ticker)
    info = tk.info or {}
    low = info.get("fiftyTwoWeekLow")
    if low:
        return float(low)
    hist = tk.history(period="1y", auto_adjust=False)
    if hist is not None and not hist.empty:
        return float(hist["Low"].min())
    raise RuntimeError(f"Could not determine 52-week low for {ticker}")

def main():
    if len(sys.argv) < 3 or sys.argv[1].lower() != "add":
        raise SystemExit("Usage: manage_watchlist.py add TICKER")
    ticker = sys.argv[2].upper().strip()
    if not ticker or len(ticker) > 10:
        raise SystemExit("Invalid ticker")

    cfg = yaml.safe_load(CONFIG.read_text())
    site = cfg.setdefault("site", {})
    tickers = site.setdefault("stock_tickers", [])
    levels = site.setdefault("stock_entry_levels", {})

    if ticker not in tickers:
        tickers.append(ticker)

    low = round(quote_52w_low(ticker), 2)
    levels[ticker] = low

    CONFIG.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True))
    print(f"{ticker}: stored 52-week-low reference = {low:.2f}")

if __name__ == "__main__":
    main()
