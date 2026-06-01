"""
render_stocks.py — Renders the stock health dashboard HTML section.
Called by generate_newspaper.py
"""

from html import escape


GRADE_COLOR = {
    "A": ("#14532d", "#dcfce7"),   # dark green text, light green bg
    "B": ("#1e3a5f", "#dbeafe"),   # dark blue / light blue
    "C": ("#713f12", "#fef9c3"),   # amber
    "D": ("#7f1d1d", "#fee2e2"),   # red
    "F": ("#3f0f0f", "#fca5a5"),
    "?": ("#374151", "#f3f4f6"),
}

REC_EMOJI = {
    "Strong Buy": "🚀",
    "Buy":        "🟢",
    "Hold":       "🟡",
    "Avoid":      "🔴",
    "Strong Sell":"💀",
    "N/A":        "❓",
}

SIGNAL_EMOJI = {10: "🟢", 9: "🟢", 8: "🟢", 7: "🟢", 6: "🟡", 5: "🟡", 4: "🟡", 3: "🔴", 2: "🔴", 1: "🔴"}


def _sig(score_10):
    return SIGNAL_EMOJI.get(int(score_10), "🟡")


def _fmt(val, suffix="", na="—"):
    if val is None:
        return na
    return f"{val}{suffix}"


def _day_arrow(change):
    if change > 0:  return f'<span style="color:#16a34a">▲ {change:.2f}%</span>'
    if change < 0:  return f'<span style="color:#dc2626">▼ {abs(change):.2f}%</span>'
    return f'<span style="color:#6b7280">— 0.00%</span>'


def render_stock_section(stocks: list) -> str:
    if not stocks:
        return "<section class='stock-section'><p>No stock data available.</p></section>"

    # ── Summary cards ──────────────────────────────────────────────────────────
    cards_html = []
    for s in stocks:
        g = s.get("grade", "?")
        g_txt, g_bg = GRADE_COLOR.get(g, ("#374151", "#f3f4f6"))
        rec = s.get("recommendation", "N/A")
        rec_em = REC_EMOJI.get(rec, "❓")
        disq = s.get("disqualifiers", [])
        disq_html = ""
        if disq:
            disq_html = f'<div class="disq">⚠️ {", ".join(disq)}</div>'

        upside = s.get("upside_pct")
        upside_html = f'<span class="upside">🎯 {upside:+.1f}% upside</span>' if upside is not None else ""

        score = s.get("health_score", 0)
        bar_w = min(int(score), 100)
        bar_color = "#16a34a" if score >= 70 else "#f59e0b" if score >= 50 else "#dc2626"

        cards_html.append(f"""
        <div class="stock-card">
            <div class="sc-header">
                <div>
                    <span class="sc-ticker">{escape(s['ticker'])}</span>
                    <span class="sc-name">{escape(s.get('name', s['ticker']))}</span>
                    <span class="sc-sector">{escape(s.get('sector', ''))}</span>
                </div>
                <div class="sc-grade-badge" style="color:{g_txt};background:{g_bg}">
                    {g} &nbsp;·&nbsp; {score}/100
                </div>
            </div>

            <div class="sc-price-row">
                <span class="sc-price">${s.get('price', 0):,.2f}</span>
                {_day_arrow(s.get('day_change', 0))}
                {upside_html}
            </div>

            <div class="sc-bar-wrap">
                <div class="sc-bar" style="width:{bar_w}%;background:{bar_color}"></div>
            </div>

            <div class="sc-metrics">
                <div class="sc-metric"><span>Rec</span><strong>{rec_em} {rec}</strong></div>
                <div class="sc-metric"><span>P/E</span><strong>{_fmt(s.get('pe'))}</strong></div>
                <div class="sc-metric"><span>PEG</span><strong>{_fmt(s.get('peg'))}</strong></div>
                <div class="sc-metric"><span>Rev↑</span><strong>{_fmt(s.get('rev_growth_pct'), '%')}</strong></div>
                <div class="sc-metric"><span>Margin</span><strong>{_fmt(s.get('net_margin_pct'), '%')}</strong></div>
                <div class="sc-metric"><span>D/E</span><strong>{_fmt(s.get('de_ratio'))}</strong></div>
                <div class="sc-metric"><span>ROE</span><strong>{_fmt(s.get('roe_pct'), '%')}</strong></div>
                <div class="sc-metric"><span>Short</span><strong>{_fmt(s.get('short_pct'), '%')}</strong></div>
            </div>

            <div class="sc-ma">
                MA50 <strong>{_fmt(s.get('ma50'), '')}</strong> &nbsp;|&nbsp;
                MA200 <strong>{_fmt(s.get('ma200'), '')}</strong> &nbsp;|&nbsp;
                52W <strong>{_fmt(s.get('week52_lo'))}–{_fmt(s.get('week52_hi'))}</strong>
            </div>

            {disq_html}
            <div class="sc-updated">Updated: {escape(s.get('fetched_at',''))}</div>
        </div>
        """)

    # ── Comparison table ───────────────────────────────────────────────────────
    table_rows = []
    for i, s in enumerate(stocks, 1):
        g = s.get("grade", "?")
        g_txt, g_bg = GRADE_COLOR.get(g, ("#374151", "#f3f4f6"))
        rec = s.get("recommendation", "N/A")
        score = s.get("health_score", 0)

        params_map = {p[0]: p[2] for p in s.get("params", [])}
        analyst_s  = params_map.get("Analyst Consensus", 5)
        peg_s      = params_map.get("PEG Ratio", 5)
        rev_s      = params_map.get("Revenue Growth YoY", 5)
        de_s       = params_map.get("Debt-to-Equity", 5)
        ma_s       = params_map.get("50/200-Day MA", 5)
        moat_s     = params_map.get("Free Cash Flow", 5)

        disq_mark = "⚠️" if s.get("disqualifiers") else ""

        table_rows.append(f"""
        <tr>
            <td class="t-rank">{i}</td>
            <td class="t-ticker"><strong>{escape(s['ticker'])}</strong>{disq_mark}</td>
            <td>${s.get('price', 0):,.2f} {_day_arrow(s.get('day_change', 0))}</td>
            <td style="color:{g_txt};background:{g_bg};font-weight:700;text-align:center">
                {g} {score}
            </td>
            <td>{REC_EMOJI.get(rec,'')} {rec}</td>
            <td>{_sig(analyst_s)} {s.get('analyst_rec','—').replace('_',' ').title()}</td>
            <td>{_sig(peg_s)} {_fmt(s.get('peg'))}</td>
            <td>{_sig(rev_s)} {_fmt(s.get('rev_growth_pct'), '%')}</td>
            <td>{_sig(de_s)} {_fmt(s.get('de_ratio'))}</td>
            <td>{_sig(ma_s)} {_fmt(s.get('ma50'))} / {_fmt(s.get('ma200'))}</td>
            <td>{_fmt(s.get('upside_pct'), '%')}</td>
        </tr>
        """)

    best = stocks[0] if stocks else None
    best_note = f"🏆 Best Pick: <strong>{best['ticker']}</strong> — {best.get('recommendation','')}, score {best.get('health_score',0)}/100" if best else ""

    return f"""
    <section class="stock-section">
        <h2>📈 Stock Health Dashboard</h2>
        <p class="stock-subtitle">Live data via Yahoo Finance · Scored across 16 parameters · Sorted by Health Score</p>

        <div class="stock-grid">
            {''.join(cards_html)}
        </div>

        <div class="stock-table-wrap">
            <table class="stock-table">
                <thead>
                    <tr>
                        <th>#</th><th>Ticker</th><th>Price</th><th>Score</th>
                        <th>Rec</th><th>Analyst</th><th>PEG</th><th>Rev↑</th>
                        <th>D/E</th><th>MA50/200</th><th>Upside</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(table_rows)}
                </tbody>
            </table>
        </div>

        <div class="best-pick-bar">{best_note}</div>

        <p class="stock-disclaimer">⚠️ Not financial advice. Always consult a professional before investing. Data from Yahoo Finance.</p>
    </section>

    <style>
    .stock-section {{ margin-bottom: 40px; }}
    .stock-section h2 {{ border-bottom: 3px solid #111827; padding-bottom: 8px; font-size: 26px; }}
    .stock-subtitle {{ color: #6b7280; font-size: 13px; margin-top: -8px; margin-bottom: 18px; }}

    .stock-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 16px;
        margin-bottom: 28px;
    }}

    .stock-card {{
        background: white;
        border-radius: 14px;
        padding: 18px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-top: 4px solid #111827;
    }}

    .sc-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; }}
    .sc-ticker {{ font-size: 22px; font-weight: 800; color: #111827; margin-right: 6px; }}
    .sc-name {{ font-size: 12px; color: #6b7280; display: block; margin-top: 2px; }}
    .sc-sector {{ font-size: 11px; color: #9ca3af; display: block; }}
    .sc-grade-badge {{ font-size: 15px; font-weight: 700; padding: 4px 10px; border-radius: 8px; white-space: nowrap; }}

    .sc-price-row {{ display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }}
    .sc-price {{ font-size: 24px; font-weight: 700; color: #111827; }}
    .upside {{ font-size: 12px; background: #f0fdf4; color: #15803d; padding: 2px 8px; border-radius: 20px; }}

    .sc-bar-wrap {{ background: #e5e7eb; border-radius: 999px; height: 6px; margin-bottom: 12px; }}
    .sc-bar {{ height: 6px; border-radius: 999px; transition: width 0.4s; }}

    .sc-metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 10px; }}
    .sc-metric {{ background: #f9fafb; border-radius: 8px; padding: 6px 8px; text-align: center; }}
    .sc-metric span {{ font-size: 10px; color: #6b7280; display: block; }}
    .sc-metric strong {{ font-size: 13px; color: #111827; }}

    .sc-ma {{ font-size: 11px; color: #6b7280; margin-bottom: 8px; }}
    .disq {{ font-size: 12px; color: #b91c1c; background: #fef2f2; padding: 4px 8px; border-radius: 6px; margin-bottom: 6px; }}
    .sc-updated {{ font-size: 10px; color: #9ca3af; text-align: right; }}

    .stock-table-wrap {{ overflow-x: auto; margin-bottom: 16px; }}
    .stock-table {{ width: 100%; border-collapse: collapse; font-size: 13px; background: white;
                    border-radius: 10px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.07); }}
    .stock-table th {{ background: #111827; color: white; padding: 10px 12px; text-align: left; white-space: nowrap; }}
    .stock-table td {{ padding: 9px 12px; border-bottom: 1px solid #f3f4f6; white-space: nowrap; }}
    .stock-table tr:last-child td {{ border-bottom: none; }}
    .stock-table tr:hover td {{ background: #f9fafb; }}
    .t-rank {{ color: #9ca3af; font-weight: 600; }}
    .t-ticker {{ font-size: 14px; }}

    .best-pick-bar {{ background: #f0fdf4; border-left: 5px solid #16a34a; padding: 12px 16px;
                      border-radius: 8px; font-size: 14px; color: #15803d; margin-bottom: 12px; }}
    .stock-disclaimer {{ font-size: 11px; color: #9ca3af; }}
    </style>
    """
