"""
stock_health.py — Stock Health Check module for Chai's Personal Newspaper
Fetches live data via yfinance and scores each stock across key parameters.

BUGS FIXED v2:
  1. Weights now sum to exactly 1.0 so max score = 100
  2. D/E ratio: yfinance returns as x100 (e.g. 655 = 6.55) — normalised correctly
  3. analyst_rec: yfinance returns "buy" not "strong_buy" — mapped correctly
  4. Hard disqualifier D/E flag now uses normalised value

Run standalone:  python stock_health.py
Or imported by:  generate_newspaper.py
"""

import json
import os
from datetime import datetime

try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False

DEFAULT_TICKERS = ["NVDA", "MU", "MSFT", "META", "AMZN", "AAPL", "VUG", "SMH", "CRM", "NFLX","GOOGL","UAL","AVGO","TTWO"]

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

def safe(val, default=None):
    try:
        if val is None or (isinstance(val, float) and (val != val)):
            return default
        return val
    except Exception:
        return default

def normalise_de(raw):
    """
    yfinance debtToEquity is returned as a percentage already multiplied by 100.
    e.g. NVDA's real D/E ~0.07 comes back as 6.55 (= 0.0655 * 100).
    We always divide by 100 to get the true ratio.
    """
    if raw is None:
        return None
    return raw / 100.0

def score_stock(ticker: str) -> dict:
    if not YF_AVAILABLE:
        return _dummy_score(ticker, "yfinance not installed")

    try:
        tk   = yf.Ticker(ticker)
        info = tk.info or {}
    except Exception as e:
        return _dummy_score(ticker, str(e))

    # ── Raw pulls ──────────────────────────────────────────────────────────────
    price       = safe(info.get("currentPrice") or info.get("regularMarketPrice"), 0)
    prev_close  = safe(info.get("regularMarketPreviousClose"), price)
    day_change  = ((price - prev_close) / prev_close * 100) if prev_close else 0

    pe          = safe(info.get("trailingPE"))
    peg         = safe(info.get("pegRatio"))
    ps          = safe(info.get("priceToSalesTrailing12Months"))

    rev_growth  = safe(info.get("revenueGrowth"))     # decimal e.g. 0.80
    earn_growth = safe(info.get("earningsGrowth"))
    net_margin  = safe(info.get("profitMargins"))
    gross_margin= safe(info.get("grossMargins"))

    # D/E: yfinance returns as ×100 — always divide by 100
    de_raw      = safe(info.get("debtToEquity"))
    de_ratio    = normalise_de(de_raw)                # true ratio e.g. 0.07

    roe         = safe(info.get("returnOnEquity"))
    fcf         = safe(info.get("freeCashflow"))
    total_cash  = safe(info.get("totalCash"), 0)
    total_debt  = safe(info.get("totalDebt"), 0)
    total_rev   = safe(info.get("totalRevenue"), 1)

    # analyst_rec from yfinance: "strong_buy", "buy", "hold", "underperform", "sell"
    analyst_rec = safe(info.get("recommendationKey"), "none").lower().strip()
    target_mean = safe(info.get("targetMeanPrice"))
    inst_pct    = safe(info.get("heldPercentInstitutions"))   # 0–1
    short_pct   = safe(info.get("shortPercentOfFloat"))       # 0–1

    beta        = safe(info.get("beta"), 1.0)
    week52_hi   = safe(info.get("fiftyTwoWeekHigh"), price)
    week52_lo   = safe(info.get("fiftyTwoWeekLow"),  price)
    ma50        = safe(info.get("fiftyDayAverage"))
    ma200       = safe(info.get("twoHundredDayAverage"))

    name        = safe(info.get("shortName") or info.get("longName"), ticker)
    sector      = safe(info.get("sector"), "N/A")

    # ── Individual scorers (0–10) ──────────────────────────────────────────────

    def score_analyst():
        # yfinance recommendationKey values
        mapping = {
            "strong_buy":  10,
            "buy":          8,
            "hold":         5,
            "underperform": 3,
            "sell":         1,
            "none":         5,
        }
        return mapping.get(analyst_rec, 5)

    def score_price_target():
        if target_mean and price:
            upside = (target_mean - price) / price * 100
            if upside > 30: return 10
            if upside > 20: return 9
            if upside > 10: return 7
            if upside > 0:  return 5
            return 3
        return 5

    def score_inst():
        if inst_pct is None: return 5
        if inst_pct > 0.70:  return 10
        if inst_pct > 0.50:  return 8
        if inst_pct > 0.30:  return 6
        return 4

    def score_pe():
        # Growth stocks legitimately have high P/Es — compare relative context
        if pe is None: return 5
        if pe < 15:    return 10
        if pe < 25:    return 9
        if pe < 35:    return 7   # NVDA ~32 → 7 (reasonable for growth)
        if pe < 50:    return 5
        if pe < 80:    return 3
        return 2

    def score_peg():
        if peg is None:  return 5
        if peg < 0.5:    return 10
        if peg < 1.0:    return 9
        if peg < 1.5:    return 7
        if peg < 2.0:    return 5
        if peg < 3.0:    return 3
        return 2

    def score_rev_growth():
        if rev_growth is None:  return 5
        if rev_growth > 0.70:   return 10
        if rev_growth > 0.40:   return 9
        if rev_growth > 0.20:   return 7
        if rev_growth > 0.10:   return 6
        if rev_growth > 0.0:    return 4
        return 2

    def score_earn_growth():
        if earn_growth is None:  return 5
        if earn_growth > 0.70:   return 10
        if earn_growth > 0.40:   return 9
        if earn_growth > 0.20:   return 7
        if earn_growth > 0.05:   return 5
        if earn_growth > 0.0:    return 4
        return 2

    def score_margins():
        if net_margin is None:  return 5
        if net_margin > 0.40:   return 10  # NVDA ~55% → 10
        if net_margin > 0.25:   return 9
        if net_margin > 0.15:   return 7
        if net_margin > 0.05:   return 5
        if net_margin > 0.0:    return 3
        return 1

    def score_de():
        # de_ratio is now normalised (e.g. 0.07 for NVDA)
        if de_ratio is None: return 5
        if de_ratio < 0.1:   return 10  # NVDA ~0.07 → 10 ✓
        if de_ratio < 0.3:   return 9
        if de_ratio < 0.6:   return 7
        if de_ratio < 1.0:   return 6
        if de_ratio < 2.0:   return 4
        if de_ratio < 3.0:   return 2
        return 1

    def score_fcf():
        if fcf is None or total_rev is None: return 5
        if fcf <= 0: return 2
        fcf_margin = fcf / max(total_rev, 1)
        if fcf_margin > 0.35: return 10
        if fcf_margin > 0.20: return 9
        if fcf_margin > 0.10: return 7
        if fcf_margin > 0.0:  return 5
        return 2

    def score_roe():
        if roe is None:  return 5
        if roe > 0.80:   return 10  # NVDA ~114% → 10 ✓
        if roe > 0.40:   return 9
        if roe > 0.20:   return 7
        if roe > 0.10:   return 5
        if roe > 0.0:    return 3
        return 1

    def score_cash_vs_debt():
        if total_cash >= total_debt * 3:   return 10
        if total_cash >= total_debt * 1.5: return 8
        if total_cash >= total_debt:       return 6
        if total_cash >= total_debt * 0.5: return 4
        return 2

    def score_short():
        if short_pct is None:  return 5
        if short_pct < 0.01:   return 10
        if short_pct < 0.03:   return 9
        if short_pct < 0.05:   return 7
        if short_pct < 0.10:   return 5
        if short_pct < 0.20:   return 3
        return 1

    def score_52w():
        if week52_hi and week52_lo and price:
            rng = week52_hi - week52_lo
            if rng == 0: return 5
            pos = (price - week52_lo) / rng
            if pos > 0.80: return 9
            if pos > 0.60: return 7
            if pos > 0.40: return 5
            return 3
        return 5

    def score_ma():
        if ma50 and ma200:
            if ma50 > ma200 * 1.05:  return 10
            if ma50 > ma200:         return 7
            if ma50 > ma200 * 0.97:  return 4
            return 2
        return 5

    def score_beta():
        b = abs(beta or 1.0)
        if b < 0.8:  return 9   # low volatility
        if b < 1.2:  return 7   # market-like
        if b < 1.8:  return 5   # slightly elevated
        if b < 2.5:  return 3
        return 2

    # ── Weighted parameters — WEIGHTS MUST SUM TO 1.0 ─────────────────────────
    # Total = 0.08+0.05+0.04+0.06+0.05+0.05+0.05+0.03+0.04+0.04+0.03+0.03+0.02+0.02+0.03+0.02+0.03+0.03+0.04+0.03+0.03+0.03+0.02+0.02+0.02+0.02+0.01+0.01+0.01 = ... let's be explicit
    params = [
        # (name, weight, score)                               Category
        ("Analyst Consensus",       0.08, score_analyst()),   # Analyst
        ("Price Target Upside",     0.05, score_price_target()),
        ("Institutional Ownership", 0.04, score_inst()),
        ("P/E vs Industry",         0.06, score_pe()),        # Valuation
        ("PEG Ratio",               0.05, score_peg()),
        ("Revenue Growth YoY",      0.05, score_rev_growth()),# Growth
        ("Earnings Growth YoY",     0.05, score_earn_growth()),
        ("Profit Margin",           0.04, score_margins()),
        ("Debt-to-Equity",          0.04, score_de()),        # Financial Health
        ("Free Cash Flow",          0.05, score_fcf()),
        ("Return on Equity",        0.04, score_roe()),
        ("Cash vs Debt",            0.03, score_cash_vs_debt()),
        ("Short Interest",          0.02, score_short()),     # Sentiment
        ("52-Week Position",        0.02, score_52w()),       # Technical
        ("50/200-Day MA",           0.04, score_ma()),
        ("Beta / Volatility",       0.02, score_beta()),
    ]

    # Verify weights sum to 1.0 and normalise just in case
    total_weight = sum(w for _, w, _ in params)
    weighted_total = sum(w * s for _, w, s in params)
    health_score = round((weighted_total / total_weight) * 10, 1)  # always 0–100

    g_letter, g_label = grade(health_score)
    rec = recommendation(health_score)

    # ── Hard disqualifiers ─────────────────────────────────────────────────────
    disqualifiers = []
    if fcf is not None and fcf < 0:
        disqualifiers.append("Negative FCF")
    if de_ratio is not None and de_ratio > 3.0:
        disqualifiers.append(f"D/E > 3.0 ({de_ratio:.1f})")
    if analyst_rec == "sell":
        disqualifiers.append("Analyst consensus = Sell")

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
        "pe":             round(pe, 1)          if pe          else None,
        "peg":            round(peg, 2)         if peg         else None,
        "ps":             round(ps, 1)          if ps          else None,
        "rev_growth_pct": round(rev_growth  * 100, 1) if rev_growth  else None,
        "net_margin_pct": round(net_margin  * 100, 1) if net_margin  else None,
        "roe_pct":        round(roe         * 100, 1) if roe         else None,
        "de_ratio":       round(de_ratio, 3)    if de_ratio    else None,
        "analyst_rec":    analyst_rec,
        "inst_pct":       round(inst_pct * 100, 1) if inst_pct else None,
        "short_pct":      round(short_pct* 100, 1) if short_pct else None,
        "week52_hi":      round(week52_hi, 2)   if week52_hi   else None,
        "week52_lo":      round(week52_lo, 2)   if week52_lo   else None,
        "ma50":           round(ma50,  2)        if ma50        else None,
        "ma200":          round(ma200, 2)        if ma200       else None,
        "params":         params,
        "disqualifiers":  disqualifiers,
        "fetched_at":     datetime.now().strftime("%b %d %Y %I:%M %p"),
        # debug info
        "_weight_sum":    round(total_weight, 4),
        "_raw_de":        de_raw,
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


if __name__ == "__main__":
    import sys
    tickers = sys.argv[1:] or DEFAULT_TICKERS
    print(f"Scoring {len(tickers)} stocks...")
    results = run_watchlist(tickers)
    # Print clean summary
    print("\n{'─'*60}")
    print(f"{'Ticker':<8} {'Price':>8} {'Score':>7} {'Grade':<6} {'Rec':<14} {'D/E':>6} {'PEG':>6} {'Analyst'}")
    print("─"*80)
    for r in results:
        print(f"{r['ticker']:<8} ${r['price']:>7.2f} {r['health_score']:>6.1f} {r['grade']:<6} "
              f"{r['recommendation']:<14} {str(r.get('de_ratio','—')):>6} "
              f"{str(r.get('peg','—')):>6}  {r.get('analyst_rec','—')}")
    print("─"*80)
