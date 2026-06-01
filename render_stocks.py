"""
render_stocks.py — Google News-style stock section
Horizontal ticker strip + compact sortable table
"""
from html import escape

GRADE_COLOR = {
    "A": ("score-a", "#137333"),
    "B": ("score-b", "#1a73e8"),
    "C": ("score-c", "#b06000"),
    "D": ("score-d", "#c5221f"),
    "F": ("score-f", "#666666"),
    "?": ("score-f", "#666666"),
}

REC_SHORT = {
    "Strong Buy": "S.Buy",
    "Buy":        "Buy",
    "Hold":       "Hold",
    "Avoid":      "Avoid",
    "Strong Sell":"S.Sell",
    "N/A":        "—",
}

def _chg(change):
    if change is None: return '<span style="color:#888">—</span>'
    if change >= 0:
        return f'<span class="pos">▲ {change:.2f}%</span>'
    return f'<span class="neg">▼ {abs(change):.2f}%</span>'

def _fmt(val, suffix="", na="—"):
    return f"{val}{suffix}" if val is not None else na

def render_stock_section(stocks: list) -> str:
    if not stocks:
        return ""

    # ── Ticker strip ───────────────────────────────────────────────────────────
    chips = []
    for s in stocks:
        g = s.get("grade", "?")
        cls, _ = GRADE_COLOR.get(g, ("score-f", "#666"))
        score = s.get("health_score", 0)
        rec = REC_SHORT.get(s.get("recommendation", "N/A"), "—")
        chg = s.get("day_change", 0)
        chg_cls = "chip-change-pos" if chg >= 0 else "chip-change-neg"
        chg_sym = "▲" if chg >= 0 else "▼"
        disq = "⚠️" if s.get("disqualifiers") else ""

        chips.append(f"""
        <div class="stock-chip">
          <div class="chip-top">
            <span class="chip-ticker">{escape(s['ticker'])}{disq}</span>
            <span class="chip-price">${s.get('price',0):,.2f}</span>
          </div>
          <div class="chip-top" style="margin-bottom:4px">
            <span class="{chg_cls}">{chg_sym} {abs(chg):.2f}%</span>
          </div>
          <div class="chip-bottom">
            <span class="chip-score {cls}">{score}</span>
            <span class="chip-rec">{rec}</span>
          </div>
        </div>""")

    # ── Detail table ───────────────────────────────────────────────────────────
    rows = []
    for i, s in enumerate(stocks, 1):
        g = s.get("grade", "?")
        cls, _ = GRADE_COLOR.get(g, ("score-f", "#666"))
        score  = s.get("health_score", 0)
        rec    = s.get("recommendation", "N/A")
        disq   = ' <span class="disq-flag">⚠️</span>' if s.get("disqualifiers") else ""
        up     = s.get("upside_pct")
        upside = f'<span class="pos">+{up}%</span>' if up and up > 0 else (f'<span class="neg">{up}%</span>' if up else "—")

        analyst = s.get("analyst_rec", "—").replace("_", " ").title()

        ma50  = s.get("ma50")
        ma200 = s.get("ma200")
        ma_sig = ""
        if ma50 and ma200:
            if ma50 > ma200:  ma_sig = ' <span class="pos" style="font-size:10px">↑</span>'
            else:              ma_sig = ' <span class="neg" style="font-size:10px">↓</span>'

        rows.append(f"""
        <tr>
          <td class="td-ticker">{escape(s['ticker'])}{disq}</td>
          <td class="td-name">{escape(s.get('name', s['ticker'])[:22])}</td>
          <td>${s.get('price',0):,.2f}</td>
          <td>{_chg(s.get('day_change'))}</td>
          <td><span class="chip-score {cls}" style="display:inline-block;padding:2px 7px;border-radius:4px;color:white;font-size:11px;font-weight:700">{score}</span> {g}</td>
          <td>{rec}</td>
          <td>{analyst}</td>
          <td>{_fmt(s.get('peg'))}</td>
          <td>{_fmt(s.get('rev_growth_pct'), '%')}</td>
          <td>{_fmt(s.get('net_margin_pct'), '%')}</td>
          <td>{_fmt(s.get('de_ratio'))}</td>
          <td>{_fmt(s.get('roe_pct'), '%')}</td>
          <td>{upside}</td>
          <td>{_fmt(s.get('ma50'))}{ma_sig}</td>
        </tr>""")

    best = stocks[0] if stocks else None
    worst = stocks[-1] if stocks else None
    best_bar = ""
    if best and worst:
        best_bar = f"""
        <div style="padding:10px 20px;font-size:12px;color:#137333;background:#f0fdf4;border-top:1px solid #e5e2db">
          🏆 Top Pick: <strong>{best['ticker']}</strong> · {best.get('recommendation','')} · {best.get('health_score',0)}/100
          &nbsp;&nbsp;|&nbsp;&nbsp;
          <span style="color:#c5221f">⚠️ Lowest: <strong>{worst['ticker']}</strong> · {worst.get('health_score',0)}/100</span>
        </div>"""

    return f"""
    <div class="stock-section" id="stocks">
      <div class="stock-section-header">
        <span class="stock-section-title">📈 Markets & Portfolio</span>
        <span class="stock-meta-note">Yahoo Finance · {len(stocks)} stocks · Scored across 16 parameters</span>
      </div>

      <div class="stock-ticker-strip">
        {''.join(chips)}
      </div>

      <div class="stock-table-wrap">
        <table class="stock-table">
          <thead>
            <tr>
              <th>Ticker</th><th>Company</th><th>Price</th><th>Day</th>
              <th>Score</th><th>Rec</th><th>Analyst</th>
              <th>PEG</th><th>Rev↑</th><th>Margin</th>
              <th>D/E</th><th>ROE</th><th>Upside</th><th>MA50</th>
            </tr>
          </thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
      </div>

      {best_bar}

      <div class="stock-disclaimer">
        ⚠️ Not financial advice. Data from Yahoo Finance. Consult a professional before investing.
      </div>
    </div>"""
