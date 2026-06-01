"""
stock_health.py — Stock Health Check module for Chai's Personal Newspaper
Fetches live data via yfinance and scores each stock across key parameters.
Run standalone:  python stock_health.py
Or imported by: generate_newspaper.py
"""

import json
import os
from datetime import datetime

try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False

# ── Default watchlist ──────────────────────────────────────────────────────────
DEFAULT_TICKERS = ["NVDA", "MU", "MSFT", "META", "AMZN", "AAPL", "VUG", "SMH", "CRM", "NFLX"]

GRADE_MAP = [
    (80, "A", "Excellent"),
    (65, "B", "Good"),
    (50, "C", "Average"),
    (35, "D", "Weak"),
    (0,  "F", "Poor"),
]

REC_MAP = [
    (80, "Strong Buy"),
    (70, "Buy"),
    (55, "Hold"),
    (40, "Avoid"),
    (0,  "Strong Sell"),
]

def grade(score):
    for threshold, letter, label in GRADE_MAP:
        if score >= threshold:
            return letter, label
    return "F", "Poor"

def recommendation(score):
    for threshold, rec in REC_MAP:
        if score >= threshold:
            return rec
    return "Strong Sell"

def signal(score_10):
    if score_10 >= 7:   return "🟢"
    if score_10 >= 4:   return "🟡"
    return "🔴"

def safe(val, default=None):
    try:
        if val is None or (isinstance(val, float) and (val != val)):
            return default
        return val
    except Exception:
        return default

def score_stock(ticker: str) -> dict:
    """Return a dict with scores, health_score, grade, rec, and raw info fields."""
    if not YF_AVAILABLE:
        return _dummy_score(ticker, "yfinance not installed")

    try:
        tk = yf.Ticker(ticker)
        info = tk.info or {}
        hist = tk.history(period="1y")
    except Exception as e:
        return _dummy_score(ticker, str(e))

    # ── Raw data pulls ─────────────────────────────────────────────────────────
    price        = safe(info.get("currentPrice") or info.get("regularMarketPrice"), 0)
    prev_close   = safe(info.get("regularMarketPreviousClose"), price)
    day_change   = ((price - prev_close) / prev_close * 100) if prev_close else 0

    pe           = safe(info.get("trailingPE"))
    fwd_pe       = safe(info.get("forwardPE"))
    peg          = safe(info.get("pegRatio"))
    ps           = safe(info.get("priceToSalesTrailing12Months"))
    pfcf_proxy   = safe(info.get("priceToBook"))          # approximation when P/FCF absent

    rev_growth   = safe(info.get("revenueGrowth"))        # decimal e.g. 0.19
    earn_growth  = safe(info.get("earningsGrowth"))
    gross_margin = safe(info.get("grossMargins"))
    net_margin   = safe(info.get("profitMargins"))

    de_ratio     = safe(info.get("debtToEquity"))         # already as ratio
    roe          = safe(info.get("returnOnEquity"))
    fcf          = safe(info.get("freeCashflow"))
    total_cash   = safe(info.get("totalCash"), 0)
    total_debt   = safe(info.get("totalDebt"), 0)
    shares_out   = safe(info.get("sharesOutstanding"), 1)

    analyst_rec  = safe(info.get("recommendationKey"), "none").lower()
    target_mean  = safe(info.get("targetMeanPrice"))
    inst_pct     = safe(info.get("heldPercentInstitutions"))
    short_pct    = safe(info.get("shortPercentOfFloat"))

    beta         = safe(info.get("beta"), 1.0)
    week52_hi    = safe(info.get("fiftyTwoWeekHigh"), price)
    week52_lo    = safe(info.get("fiftyTwoWeekLow"), price)
    ma50         = safe(info.get("fiftyDayAverage"))
    ma200        = safe(info.get("twoHundredDayAverage"))

    name         = safe(info.get("shortName") or info.get("longName"), ticker)
    sector       = safe(info.get("sector"), "N/A")

    # ── Scoring helpers ────────────────────────────────────────────────────────
    def score_analyst():
        mapping = {"strong_buy": 10, "buy": 8, "hold": 5, "underperform": 3, "sell": 1, "none": 5}
        return mapping.get(analyst_rec, 5)

    def score_price_target():
        if target_mean and price:
            upside = (target_mean - price) / price * 100
            if upside > 25: return 10
            if upside > 15: return 8
            if upside > 5:  return 6
            if upside > 0:  return 4
            return 2
        return 5

    def score_pe():
        if pe is None: return 5
        if pe < 15:    return 10
        if pe < 25:    return 8
        if pe < 40:    return 6
        if pe < 60:    return 4
        return 2

    def score_peg():
        if peg is None: return 5
        if peg < 0.5:   return 10
        if peg < 1.0:   return 8
        if peg < 1.5:   return 6
        if peg < 2.5:   return 4
        return 2

    def score_rev_growth():
        if rev_growth is None: return 5
        if rev_growth > 0.50:  return 10
        if rev_growth > 0.20:  return 8
        if rev_growth > 0.10:  return 6
        if rev_growth > 0.0:   return 4
        return 2

    def score_earn_growth():
        if earn_growth is None: return 5
        if earn_growth > 0.50:  return 10
        if earn_growth > 0.20:  return 8
        if earn_growth > 0.05:  return 6
        if earn_growth > 0.0:   return 4
        return 2

    def score_margins():
        if net_margin is None: return 5
        if net_margin > 0.30:  return 10
        if net_margin > 0.15:  return 8
        if net_margin > 0.05:  return 6
        if net_margin > 0.0:   return 4
        return 2

    def score_de():
        if de_ratio is None: return 5
        # yfinance returns as percentage (e.g. 29 = 0.29 D/E)
        de = de_ratio / 100 if de_ratio > 10 else de_ratio
        if de < 0.3:  return 10
        if de < 0.8:  return 8
        if de < 1.5:  return 6
        if de < 3.0:  return 4
        return 1   # hard disqualifier territory

    def score_fcf():
        if fcf is None: return 5
        if fcf > 0:
            fcf_margin = fcf / max(safe(info.get("totalRevenue"), 1), 1)
            if fcf_margin > 0.25: return 10
            if fcf_margin > 0.10: return 8
            return 6
        return 2

    def score_roe():
        if roe is None: return 5
        if roe > 0.40:  return 10
        if roe > 0.20:  return 8
        if roe > 0.10:  return 6
        if roe > 0.0:   return 4
        return 2

    def score_cash_vs_debt():
        if total_cash >= total_debt * 2: return 10
        if total_cash >= total_debt:     return 8
        if total_cash >= total_debt * 0.5: return 5
        return 3

    def score_inst():
        if inst_pct is None: return 5
        if inst_pct > 0.70:  return 10
        if inst_pct > 0.50:  return 8
        if inst_pct > 0.30:  return 6
        return 4

    def score_short():
        if short_pct is None: return 5
        if short_pct < 0.02:  return 10
        if short_pct < 0.05:  return 8
        if short_pct < 0.10:  return 6
        if short_pct < 0.20:  return 4
        return 2

    def score_52w():
        if week52_hi and week52_lo and price:
            rng = week52_hi - week52_lo
            pos = (price - week52_lo) / rng if rng else 0.5
            if pos > 0.80: return 9
            if pos > 0.60: return 7
            if pos > 0.40: return 5
            return 3
        return 5

    def score_ma():
        if ma50 and ma200:
            if ma50 > ma200 * 1.05: return 10
            if ma50 > ma200:        return 7
            if ma50 > ma200 * 0.95: return 4
            return 2
        return 5

    # ── Weighted score calculation ─────────────────────────────────────────────
    params = [
        ("Analyst Consensus",      0.08, score_analyst()),
        ("Price Target Upside",    0.05, score_price_target()),
        ("Institutional Ownership",0.04, score_inst()),
        ("P/E vs Industry",        0.06, score_pe()),
        ("PEG Ratio",              0.05, score_peg()),
        ("Revenue Growth YoY",     0.05, score_rev_growth()),
        ("Earnings Growth YoY",    0.05, score_earn_growth()),
        ("Profit Margin",          0.03, score_margins()),
        ("Debt-to-Equity",         0.04, score_de()),
        ("Free Cash Flow",         0.04, score_fcf()),
        ("Return on Equity",       0.03, score_roe()),
        ("Cash vs Debt",           0.03, score_cash_vs_debt()),
        ("Short Interest",         0.02, score_short()),
        ("52-Week Position",       0.02, score_52w()),
        ("50/200-Day MA",          0.03, score_ma()),
        ("Beta / Volatility",      0.02, max(1, 10 - int(abs(beta or 1) * 2))),
    ]

    weighted_total = sum(w * s for _, w, s in params)
    health_score   = round(weighted_total * 10, 1)   # scale 0–100
    g_letter, g_label = grade(health_score)
    rec = recommendation(health_score)

    # ── Hard disqualifiers ─────────────────────────────────────────────────────
    disqualifiers = []
    if fcf is not None and fcf < 0:
        disqualifiers.append("Negative FCF")
    de_norm = (de_ratio / 100) if (de_ratio and de_ratio > 10) else (de_ratio or 0)
    if de_norm > 3.0:
        disqualifiers.append("D/E > 3.0")
    if analyst_rec == "sell":
        disqualifiers.append("Analyst consensus = Sell")

    # ── Upside % ──────────────────────────────────────────────────────────────
    upside_pct = round((target_mean - price) / price * 100, 1) if (target_mean and price) else None

    return {
        "ticker":         ticker,
        "name":           name,
        "sector":         sector,
        "price":          round(price, 2),
        "day_change":     round(day_change, 2),
        "health_score":   health_score,
        "grade":          g_letter,
        "grade_label":    g_label,
        "recommendation": rec,
        "upside_pct":     upside_pct,
        "pe":             round(pe, 1) if pe else None,
        "peg":            round(peg, 2) if peg else None,
        "ps":             round(ps, 1) if ps else None,
        "rev_growth_pct": round(rev_growth * 100, 1) if rev_growth else None,
        "net_margin_pct": round(net_margin * 100, 1) if net_margin else None,
        "roe_pct":        round(roe * 100, 1) if roe else None,
        "de_ratio":       round(de_norm, 2) if de_ratio else None,
        "analyst_rec":    analyst_rec,
        "inst_pct":       round(inst_pct * 100, 1) if inst_pct else None,
        "short_pct":      round(short_pct * 100, 1) if short_pct else None,
        "week52_hi":      round(week52_hi, 2) if week52_hi else None,
        "week52_lo":      round(week52_lo, 2) if week52_lo else None,
        "ma50":           round(ma50, 2) if ma50 else None,
        "ma200":          round(ma200, 2) if ma200 else None,
        "params":         params,
        "disqualifiers":  disqualifiers,
        "fetched_at":     datetime.now().strftime("%b %d %Y %I:%M %p"),
    }


def _dummy_score(ticker, reason):
    return {
        "ticker": ticker, "name": ticker, "sector": "N/A",
        "price": 0, "day_change": 0, "health_score": 0,
        "grade": "?", "grade_label": "N/A", "recommendation": "N/A",
        "upside_pct": None, "pe": None, "peg": None, "ps": None,
        "rev_growth_pct": None, "net_margin_pct": None, "roe_pct": None,
        "de_ratio": None, "analyst_rec": "none", "inst_pct": None,
        "short_pct": None, "week52_hi": None, "week52_lo": None,
        "ma50": None, "ma200": None, "params": [], "disqualifiers": [],
        "fetched_at": datetime.now().strftime("%b %d %Y %I:%M %p"),
        "error": reason,
    }


def run_watchlist(tickers=None):
    tickers = tickers or DEFAULT_TICKERS
    results = []
    for t in tickers:
        print(f"  Scoring {t}...")
        results.append(score_stock(t))
    results.sort(key=lambda x: x["health_score"], reverse=True)
    return results


# ── Standalone run ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    tickers = sys.argv[1:] or DEFAULT_TICKERS
    print(f"Scoring {len(tickers)} stocks...")
    results = run_watchlist(tickers)
    print(json.dumps(results, indent=2, default=str))
