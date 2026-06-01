# Chai's Personal Newspaper — with Stock Health Dashboard

Pulls RSS news + live Yahoo Finance stock scores into one HTML page.
Runs locally anytime, or auto-refreshes hourly via GitHub Actions.

---

## What's inside

| File | Purpose |
|------|---------|
| `config.yml` | Your topics, feeds, AND stock watchlist |
| `generate_newspaper.py` | Main script — runs everything |
| `stock_health.py` | Scores each stock across 16 parameters |
| `render_stocks.py` | Renders the stock dashboard HTML |
| `llm_score.py` | Gemini AI executive summary |
| `requirements.txt` | Python packages |
| `index.html` | Output — open in browser |
| `.github/workflows/refresh.yml` | Auto-runs hourly on GitHub |

---

## Quick Start (Local)

### 1. Install Python 3.11+

### 2. Install packages
```bash
pip install -r requirements.txt
```

### 3. Set your Gemini API key (optional — news still works without it)
```bash
# Mac/Linux
export GEMINI_API_KEY="your-key-here"

# Windows
set GEMINI_API_KEY=your-key-here
```

### 4. Run it
```bash
python generate_newspaper.py
```

### 5. Open index.html in your browser
Double-click it, or:
```bash
open index.html        # Mac
start index.html       # Windows
```

---

## Update your stock watchlist

Edit `config.yml` — find the `stock_tickers` section:

```yaml
site:
  stock_tickers:
    - NVDA
    - MU
    - MSFT
    - TSLA      # ← add any ticker here
    - AAPL
```

Save and re-run `python generate_newspaper.py`. That's it.

---

## Run only stock scores (no news fetch)

```bash
python stock_health.py NVDA MU TSLA MSFT
```

Prints JSON scores to terminal. Useful for quick checks.

---

## Auto-refresh on GitHub (free)

1. Create a GitHub repo
2. Upload all files
3. Go to **Settings → Secrets → Actions**
4. Add secret: `GEMINI_API_KEY` = your key
5. Go to **Settings → Pages** → Deploy from `main` branch, root folder
6. GitHub Actions runs every hour and pushes fresh `index.html`
7. Your newspaper lives at `https://yourusername.github.io/your-repo/`

**Manual refresh:** Go to Actions tab → "Refresh Personal Newspaper" → "Run workflow"

---

## What the Stock Health Score means

| Score | Grade | Meaning |
|-------|-------|---------|
| 80–100 | A | Excellent — Strong Buy territory |
| 65–79  | B | Good — Buy |
| 50–64  | C | Average — Hold |
| 35–49  | D | Weak — Avoid |
| 0–34   | F | Poor — Strong Sell |

Scored across 16 parameters with these weights:
- Analyst Consensus (8%) · P/E vs Industry (6%) · Revenue Growth (5%)
- PEG Ratio (5%) · Earnings Growth (5%) · Price Target Upside (5%)
- Debt/Equity (4%) · Free Cash Flow (4%) · Institutional Ownership (4%)
- Profit Margin (3%) · ROE (3%) · Cash vs Debt (3%) · 50/200-day MA (3%)
- Short Interest (2%) · 52-Week Position (2%) · Beta/Volatility (2%)

⚠️ **Not financial advice.** Always consult a professional before investing.

---

## Troubleshooting

**Stock shows 0 / no data** → yfinance occasionally rate-limits; re-run after a minute.

**AI summary fails** → Newspaper still works. Just no Gemini summary. Check your API key.

**RSS feed returns nothing** → That feed may be temporarily down. Others will still load.
