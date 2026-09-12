"""
render_stocks.py — Personalized stock watchlist dashboard

Designed around Chai's predefined entry zones and category-level context.
The dashboard reports objective price-vs-zone signals and highlights when a
predefined tranche zone is active. Live prices and health scores come from
stock_health.py.
"""
from html import escape


CATEGORY_DEFS = [
    {
        "name": "AI Compute & Semis", "icon": "⚡", "tone": "purple",
        "tickers": ["MU", "NVDA", "AVGO"],
        "thesis": "AI infrastructure demand is the secular driver. Peer participation matters: strength across memory, accelerators and networking is healthier than a one-stock move.",
    },
    {
        "name": "Mega-cap Platforms", "icon": "☁️", "tone": "blue",
        "tickers": ["GOOGL", "AMZN", "MSFT", "META", "AAPL"],
        "thesis": "Cloud, ads, AI distribution and ecosystem cash flows. The bucket is strongest when several platforms participate instead of one name carrying the group.",
    },
    {
        "name": "Payments & Data Moats", "icon": "💳", "tone": "green",
        "tickers": ["V", "MA", "SPGI"],
        "thesis": "High-quality transaction and data toll roads. Watch spending, cross-border activity and capital-markets volume for confirmation.",
    },
    {
        "name": "AI Software Turnarounds", "icon": "🧠", "tone": "amber",
        "tickers": ["CRM", "SNOW", "WDAY"],
        "thesis": "A higher-variance recovery bucket. Better setups require improving growth, durable free cash flow and evidence that AI products are monetizing—not just good narratives.",
    },
    {
        "name": "Travel & Cyclicals", "icon": "✈️", "tone": "rose",
        "tickers": ["DAL", "UAL", "EXPE"],
        "thesis": "Peer confirmation matters here. DAL and UAL moving together is a stronger industry signal than either airline moving alone; EXPE adds a broader travel-demand check.",
    },
]


STOCK_META = {
    "MU": {"zone": (935, 945), "label": "High priority", "reasons": ["HBM and AI-memory demand", "Memory pricing and mix leverage", "High upside potential, but cyclical"]},
    "NVDA": {"zone": (205, 212), "label": "High priority", "reasons": ["AI accelerator leadership", "CUDA + software ecosystem moat", "Hyperscaler AI capex remains key demand driver"]},
    "AVGO": {"zone": (340, 350), "label": "High priority", "reasons": ["AI networking + custom silicon exposure", "VMware adds recurring software cash flow", "Strong free-cash-flow profile"]},
    "GOOGL": {"zone": (325, 335), "label": "High priority", "reasons": ["Search + YouTube cash engine", "Cloud and AI growth optionality", "Mega-cap quality with valuation support"]},
    "AMZN": {"zone": (248, 254), "label": "High priority", "reasons": ["AWS cloud + AI demand", "Retail margin expansion", "Advertising is a high-margin growth engine"]},
    "MSFT": {"zone": (440, 450), "label": "Core compounder", "reasons": ["Azure + enterprise AI distribution", "Durable recurring software revenue", "Balance-sheet and cash-flow quality"]},
    "META": {"zone": (585, 595), "label": "Core compounder", "reasons": ["AI improves ad targeting and efficiency", "Large engagement + monetization base", "Strong cash generation and capital returns"]},
    "AAPL": {"zone": (305, 315), "label": "Core compounder", "reasons": ["Sticky device + services ecosystem", "Huge installed base", "Capital returns provide support"]},
    "V": {"zone": (355, 363), "label": "Core compounder", "reasons": ["Secular shift to digital payments", "High-margin global network", "Cross-border volume is a strong tailwind"]},
    "MA": {"zone": (550, 558), "label": "Core compounder", "reasons": ["Global payments network moat", "Strong cross-border economics", "Asset-light compounding model"]},
    "SPGI": {"zone": (415, 425), "label": "Data moat", "reasons": ["Ratings + indices + market data moat", "Recurring, high-value information products", "Capital-markets recovery can add upside"]},
    "CRM": {"zone": (220, 230), "label": "Turnaround", "reasons": ["Large enterprise installed base", "Margin and free-cash-flow improvement", "AI monetization is the key upside test"]},
    "SNOW": {"zone": (285, 300), "label": "Turnaround", "reasons": ["Cloud data platform at center of AI workflows", "Consumption growth can reaccelerate", "Higher valuation sensitivity creates better entry discipline"]},
    "WDAY": {"zone": (165, 175), "label": "Turnaround", "reasons": ["Sticky HR + finance subscriptions", "Buybacks can support per-share value", "Your thesis watches the ~$170 support area"]},
    "DAL": {"zone": (72, 78), "label": "Cyclical value", "reasons": ["Premium travel + loyalty economics", "Operating leverage when demand is firm", "UAL peer confirmation improves the signal"]},
    "UAL": {"zone": (92, 98), "label": "Cyclical value", "reasons": ["Strong international network", "Capacity discipline can support margins", "DAL peer confirmation matters"]},
    "EXPE": {"zone": (240, 250), "label": "Travel platform", "reasons": ["Scaled online travel platform", "B2B + Vrbo provide multiple growth levers", "Your thesis also watches the 200-day MA area"]},
}


def _money(v):
    return f"${v:,.2f}" if v is not None else "—"


def _day_change(v):
    if v is None:
        return '<span class="pw-muted">—</span>'
    cls = "pw-up" if v >= 0 else "pw-down"
    sym = "▲" if v >= 0 else "▼"
    return f'<span class="{cls}">{sym} {abs(v):.2f}%</span>'


def _zone_status(price, low, high):
    if not price:
        return {"key": "no-data", "label": "NO DATA", "detail": "Price unavailable", "distance": None}
    if low <= price <= high:
        pos = ((price - low) / max(high - low, 0.01)) * 100
        return {"key": "in-zone", "label": "IN ZONE", "detail": f"Inside target range · {pos:.0f}% through zone", "distance": 0}
    if price < low:
        pct = (low - price) / low * 100
        return {"key": "below-zone", "label": "BELOW ZONE · CHECK", "detail": f"{pct:.1f}% below zone floor · recheck thesis/news", "distance": -pct}
    pct = (price - high) / high * 100
    if pct <= 3:
        return {"key": "near-zone", "label": "NEAR ZONE", "detail": f"{pct:.1f}% above target ceiling", "distance": pct}
    return {"key": "wait", "label": "WAIT FOR PULLBACK", "detail": f"{pct:.1f}% above target ceiling", "distance": pct}


def _action_signal(z):
    signals = {
        "in-zone": ("🔥🔥", "ENTRY ZONE HIT", "Your predefined range is active · review Tranche 1 now"),
        "near-zone": ("🔥", "NEAR ENTRY", "Within 3% of your range · keep this at the top of the watchlist"),
        "below-zone": ("⚠️", "BELOW RANGE", "Cheaper than planned · pause and recheck thesis/news before acting"),
        "wait": ("⏳", "WAIT", "Still above your target · no chase"),
        "no-data": ("❔", "NO DATA", "Price unavailable · do not act on stale data"),
    }
    return signals[z["key"]]


def _category_health(items):
    real_scores = [x.get("health_score", 0) for x in items if x.get("health_score", 0) > 0]
    avg_score = sum(real_scores) / len(real_scores) if real_scores else 0
    changes = [x.get("day_change") for x in items if x.get("day_change") is not None]
    avg_change = sum(changes) / len(changes) if changes else 0
    leader = max(items, key=lambda x: x.get("day_change", -999)) if items else None
    if avg_score >= 80:
        label, key = "Strong", "strong"
    elif avg_score >= 72:
        label, key = "Healthy", "healthy"
    elif avg_score >= 65:
        label, key = "Mixed", "mixed"
    else:
        label, key = "Caution", "caution"
    return label, key, avg_score, avg_change, leader


def _render_card(s):
    ticker = s["ticker"]
    meta = STOCK_META[ticker]
    low, high = meta["zone"]
    price = s.get("price") or 0
    z = _zone_status(price, low, high)
    fire, action, action_detail = _action_signal(z)
    score = s.get("health_score", 0)
    grade = s.get("grade", "?")
    analyst = (s.get("analyst_rec") or "none").replace("_", " ").title()
    reasons = "".join(f"<li>{escape(r)}</li>" for r in meta["reasons"])

    return f"""
    <article class="pw-card pw-card-{z['key']}">
      <div class="pw-action pw-action-{z['key']}">
        <span class="pw-action-fire">{fire}</span>
        <div><strong>{action}</strong><small>{escape(action_detail)}</small></div>
      </div>
      <div class="pw-card-top">
        <div>
          <div class="pw-symbol-row"><span class="pw-symbol">{escape(ticker)}</span><span class="pw-role">{escape(meta['label'])}</span></div>
          <div class="pw-company">{escape(s.get('name', ticker))}</div>
        </div>
        <span class="pw-status pw-status-{z['key']}">{z['label']}</span>
      </div>
      <div class="pw-price-row">
        <div><div class="pw-price">{_money(price)}</div><div class="pw-change">{_day_change(s.get('day_change'))} today</div></div>
        <div class="pw-zone-box"><div class="pw-zone-label">YOUR ENTRY ZONE</div><div class="pw-zone-value">${low:,.0f}–${high:,.0f}</div></div>
      </div>
      <div class="pw-zone-detail">{escape(z['detail'])}</div>
      <div class="pw-mini-metrics">
        <div><span>Score</span><strong>{score:.1f} <small>{escape(grade)}</small></strong></div>
        <div><span>Analyst</span><strong>{escape(analyst)}</strong></div>
        <div><span>Upside</span><strong>{('+' + str(s.get('upside_pct')) + '%') if s.get('upside_pct') is not None else '—'}</strong></div>
      </div>
      <div class="pw-why-title">Why it stays on the watchlist</div>
      <ul class="pw-reasons">{reasons}</ul>
    </article>"""


def render_stock_section(stocks: list) -> str:
    if not stocks:
        return ""
    by_ticker = {s.get("ticker"): s for s in stocks}
    ordered = []
    for category in CATEGORY_DEFS:
        for ticker in category["tickers"]:
            if ticker in by_ticker:
                ordered.append(by_ticker[ticker])

    status_counts = {"in-zone": 0, "near-zone": 0, "wait": 0, "below-zone": 0, "no-data": 0}
    for s in ordered:
        low, high = STOCK_META[s["ticker"]]["zone"]
        status_counts[_zone_status(s.get("price") or 0, low, high)["key"]] += 1

    hot_names = []
    near_names = []
    for s in ordered:
        low, high = STOCK_META[s["ticker"]]["zone"]
        key = _zone_status(s.get("price") or 0, low, high)["key"]
        if key == "in-zone": hot_names.append(s["ticker"])
        if key == "near-zone": near_names.append(s["ticker"])

    category_html = []
    for category in CATEGORY_DEFS:
        items = [by_ticker[t] for t in category["tickers"] if t in by_ticker]
        if not items:
            continue
        health_label, health_key, avg_score, avg_change, leader = _category_health(items)
        leader_text = f"{leader['ticker']} {leader.get('day_change', 0):+.2f}%" if leader else "—"
        active = 0
        for item in items:
            low, high = STOCK_META[item["ticker"]]["zone"]
            if _zone_status(item.get("price") or 0, low, high)["key"] in {"in-zone", "near-zone"}:
                active += 1
        cards = "".join(_render_card(s) for s in items)
        category_html.append(f"""
        <section class="pw-category pw-tone-{category['tone']}">
          <div class="pw-category-head">
            <div class="pw-category-title-wrap"><div class="pw-category-icon">{category['icon']}</div><div><h3>{escape(category['name'])}</h3><p>{escape(category['thesis'])}</p></div></div>
            <div class="pw-health-card"><span class="pw-health-label pw-health-{health_key}">{health_label}</span><div class="pw-health-grid">
              <div><span>Group score</span><strong>{avg_score:.1f}</strong></div><div><span>Today</span><strong class="{'pw-up' if avg_change >= 0 else 'pw-down'}">{avg_change:+.2f}%</strong></div>
              <div><span>Leader</span><strong>{escape(leader_text)}</strong></div><div><span>In / near zone</span><strong>{active}/{len(items)}</strong></div>
            </div></div>
          </div><div class="pw-card-grid">{cards}</div>
        </section>""")

    hot_text = ", ".join(hot_names) if hot_names else "None right now"
    near_text = ", ".join(near_names) if near_names else "None right now"

    return f"""
    <style>
      .portfolio-watch{{--pw-ink:#172033;--pw-muted:#667085;--pw-line:#e7eaf0;--pw-green:#087a55;--pw-green-bg:#e8f8f0;--pw-blue:#155eef;--pw-blue-bg:#edf4ff;--pw-purple:#6d4aff;--pw-purple-bg:#f3efff;--pw-amber:#9a5b00;--pw-amber-bg:#fff4df;--pw-red:#c4324f;--pw-red-bg:#fff0f2;--pw-slate:#475467;--pw-slate-bg:#f2f4f7;margin-bottom:36px;color:var(--pw-ink);font-family:'Source Sans 3',system-ui,sans-serif}}
      .portfolio-watch *{{box-sizing:border-box}}
      .pw-hero{{position:relative;overflow:hidden;border-radius:22px;padding:28px 30px;color:#fff;background:linear-gradient(135deg,#07111f 0%,#142846 55%,#263f70 100%);box-shadow:0 18px 45px rgba(15,23,42,.18);margin-bottom:14px}}
      .pw-hero:after{{content:'';position:absolute;width:420px;height:420px;right:-160px;top:-245px;border-radius:50%;background:radial-gradient(circle,rgba(109,74,255,.46),rgba(109,74,255,0) 68%)}}
      .pw-kicker{{font-size:12px;font-weight:850;text-transform:uppercase;letter-spacing:1.35px;color:#b8c7ff;margin-bottom:5px}}
      .pw-hero h2{{font-family:'Playfair Display',Georgia,serif;font-size:31px;line-height:1.12;margin:0 0 7px;letter-spacing:-.5px}}
      .pw-hero p{{max-width:790px;margin:0;color:#d0d8e8;font-size:14px;line-height:1.55}}
      .pw-hero-meta{{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px}} .pw-hero-chip{{display:inline-flex;align-items:center;gap:6px;padding:7px 11px;border-radius:999px;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.11);color:#eef2ff;font-size:12px;font-weight:700}}
      .pw-alert-strip{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px}}
      .pw-alert{{border-radius:14px;padding:13px 15px;border:1px solid var(--pw-line);box-shadow:0 4px 15px rgba(15,23,42,.04)}} .pw-alert strong{{display:block;font-size:14px}} .pw-alert span{{display:block;font-size:12px;margin-top:2px}}
      .pw-alert-hot{{background:linear-gradient(135deg,#fff0eb,#fff7e8);border-color:#ffc7a8}} .pw-alert-near{{background:var(--pw-blue-bg);border-color:#c9dcff}}
      .pw-cheat{{background:#fff;border:1px solid var(--pw-line);border-radius:16px;padding:16px;margin-bottom:14px;box-shadow:0 5px 20px rgba(15,23,42,.04)}}
      .pw-cheat-head{{display:flex;justify-content:space-between;align-items:end;gap:12px;margin-bottom:10px}} .pw-cheat-head h3{{margin:0;font-size:16px}} .pw-cheat-head span{{font-size:11px;color:var(--pw-muted)}}
      .pw-cheat-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}} .pw-cheat-item{{border-radius:11px;padding:10px 11px;min-height:76px;border:1px solid #edf0f4;background:#fafbfc}}
      .pw-cheat-item b{{display:block;font-size:11px;letter-spacing:.25px;margin-bottom:3px}} .pw-cheat-item span{{display:block;color:#556176;font-size:11px;line-height:1.32}}
      .pw-cheat-item:nth-child(4n+1){{background:var(--pw-purple-bg)}} .pw-cheat-item:nth-child(4n+2){{background:var(--pw-blue-bg)}} .pw-cheat-item:nth-child(4n+3){{background:var(--pw-green-bg)}} .pw-cheat-item:nth-child(4n){{background:var(--pw-amber-bg)}}
      .pw-summary{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:0 0 18px}} .pw-summary-card{{background:#fff;border:1px solid var(--pw-line);border-radius:14px;padding:13px 15px;box-shadow:0 4px 15px rgba(15,23,42,.035)}} .pw-summary-card span{{display:block;color:var(--pw-muted);font-size:10px;text-transform:uppercase;letter-spacing:.55px;font-weight:800}} .pw-summary-card strong{{display:block;margin-top:2px;font-size:21px}} .pw-summary-card small{{display:block;color:var(--pw-muted);font-size:10.5px;margin-top:2px}}
      .pw-category{{background:#fff;border:1px solid var(--pw-line);border-radius:18px;margin-bottom:18px;overflow:hidden;box-shadow:0 5px 20px rgba(15,23,42,.04)}} .pw-category-head{{display:grid;grid-template-columns:minmax(0,1fr) 370px;gap:20px;align-items:center;padding:19px 20px 17px;border-bottom:1px solid var(--pw-line)}} .pw-category-title-wrap{{display:flex;gap:12px;align-items:flex-start}} .pw-category-icon{{width:38px;height:38px;border-radius:11px;display:grid;place-items:center;font-size:19px;flex:0 0 auto;background:#f5f7fb}} .pw-category h3{{margin:0 0 4px;font-family:'Playfair Display',Georgia,serif;font-size:19px}} .pw-category-head p{{margin:0;color:var(--pw-muted);font-size:12px;line-height:1.45;max-width:700px}}
      .pw-tone-purple .pw-category-icon{{background:var(--pw-purple-bg)}} .pw-tone-blue .pw-category-icon{{background:var(--pw-blue-bg)}} .pw-tone-green .pw-category-icon{{background:var(--pw-green-bg)}} .pw-tone-amber .pw-category-icon{{background:var(--pw-amber-bg)}} .pw-tone-rose .pw-category-icon{{background:var(--pw-red-bg)}}
      .pw-health-card{{border-left:1px solid var(--pw-line);padding-left:18px}} .pw-health-label{{display:inline-flex;padding:4px 9px;border-radius:999px;font-size:10px;font-weight:850;text-transform:uppercase;margin-bottom:8px}} .pw-health-strong,.pw-health-healthy{{color:var(--pw-green);background:var(--pw-green-bg)}} .pw-health-mixed{{color:var(--pw-amber);background:var(--pw-amber-bg)}} .pw-health-caution{{color:var(--pw-red);background:var(--pw-red-bg)}} .pw-health-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}} .pw-health-grid span{{display:block;color:var(--pw-muted);font-size:9px;text-transform:uppercase;font-weight:800}} .pw-health-grid strong{{display:block;margin-top:1px;font-size:12px;white-space:nowrap}}
      .pw-card-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:0}} .pw-card{{padding:12px 14px 16px;min-width:0;border-right:1px solid var(--pw-line);border-bottom:1px solid var(--pw-line);background:#fff;transition:.15s}} .pw-card:nth-child(3n){{border-right:none}} .pw-card-in-zone{{background:linear-gradient(180deg,#fff8ee 0,#fff 32%)}} .pw-card-near-zone{{background:linear-gradient(180deg,#f2f7ff 0,#fff 30%)}}
      .pw-action{{display:flex;gap:8px;align-items:center;border-radius:10px;padding:8px 9px;margin-bottom:10px;border:1px solid transparent}} .pw-action-fire{{font-size:19px;line-height:1}} .pw-action strong{{display:block;font-size:11px;letter-spacing:.35px}} .pw-action small{{display:block;margin-top:1px;font-size:9.5px;line-height:1.25;color:#556176}} .pw-action-in-zone{{background:linear-gradient(90deg,#fff1df,#fff8e8);border-color:#ffba75;box-shadow:0 0 0 2px rgba(255,132,0,.07)}} .pw-action-in-zone strong{{color:#a23d00;font-size:12px}} .pw-action-near-zone{{background:var(--pw-blue-bg);border-color:#bdd3ff}} .pw-action-near-zone strong{{color:var(--pw-blue)}} .pw-action-below-zone{{background:var(--pw-red-bg);border-color:#ffd1d9}} .pw-action-wait{{background:var(--pw-slate-bg);border-color:#e4e7ec}} .pw-action-no-data{{background:var(--pw-amber-bg)}}
      .pw-card-top{{display:flex;align-items:flex-start;justify-content:space-between;gap:8px;min-height:43px}} .pw-symbol-row{{display:flex;align-items:center;gap:6px}} .pw-symbol{{font-size:17px;font-weight:900}} .pw-role{{font-size:8.8px;color:var(--pw-muted);background:#f6f7f9;padding:3px 5px;border-radius:6px;font-weight:750;white-space:nowrap}} .pw-company{{margin-top:2px;color:var(--pw-muted);font-size:10.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:180px}} .pw-status{{flex:0 0 auto;font-size:8.8px;font-weight:900;border-radius:999px;padding:5px 7px;white-space:nowrap}} .pw-status-in-zone{{color:#9b3d00;background:#fff0d9}} .pw-status-near-zone{{color:var(--pw-blue);background:var(--pw-blue-bg)}} .pw-status-wait{{color:var(--pw-slate);background:var(--pw-slate-bg)}} .pw-status-below-zone{{color:var(--pw-red);background:var(--pw-red-bg)}} .pw-status-no-data{{color:var(--pw-amber);background:var(--pw-amber-bg)}}
      .pw-price-row{{display:flex;justify-content:space-between;align-items:flex-end;gap:8px;margin:10px 0 7px}} .pw-price{{font-size:22px;font-weight:900;line-height:1}} .pw-change{{margin-top:4px;color:var(--pw-muted);font-size:10px}} .pw-up{{color:var(--pw-green)!important;font-weight:800}} .pw-down{{color:var(--pw-red)!important;font-weight:800}} .pw-muted{{color:var(--pw-muted)}} .pw-zone-box{{text-align:right;padding:6px 8px;background:#f8fafc;border:1px solid #edf0f4;border-radius:9px}} .pw-zone-label{{font-size:7.8px;color:var(--pw-muted);font-weight:850;letter-spacing:.45px}} .pw-zone-value{{font-size:13px;font-weight:850;margin-top:1px}} .pw-zone-detail{{font-size:10px;color:var(--pw-muted);padding:6px 8px;border-radius:8px;background:#fbfcfe;border:1px solid #f0f2f5}}
      .pw-mini-metrics{{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin:9px 0 10px}} .pw-mini-metrics span{{display:block;color:var(--pw-muted);font-size:8px;text-transform:uppercase;font-weight:800}} .pw-mini-metrics strong{{display:block;margin-top:1px;font-size:10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}} .pw-mini-metrics small{{color:var(--pw-muted);font-size:8px}} .pw-why-title{{padding-top:9px;border-top:1px solid #f0f2f5;font-size:9px;font-weight:900;text-transform:uppercase;color:#344054}} .pw-reasons{{margin:6px 0 0 15px;padding:0;color:#475467;font-size:10.5px;line-height:1.38}} .pw-reasons li{{margin:2px 0}}
      .pw-foot{{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;padding:12px 3px 0;color:var(--pw-muted);font-size:10px;line-height:1.45}} .pw-foot strong{{color:#475467}}
      @media(max-width:1050px){{.pw-category-head{{grid-template-columns:1fr}}.pw-health-card{{border-left:none;padding-left:50px}}.pw-card-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.pw-card:nth-child(3n){{border-right:1px solid var(--pw-line)}}.pw-card:nth-child(2n){{border-right:none}}.pw-cheat-grid{{grid-template-columns:repeat(2,1fr)}}}}
      @media(max-width:720px){{.pw-hero{{padding:22px 18px;border-radius:16px}}.pw-hero h2{{font-size:25px}}.pw-alert-strip,.pw-summary{{grid-template-columns:repeat(2,1fr)}}.pw-cheat{{padding:13px}}.pw-cheat-head{{align-items:flex-start;flex-direction:column;gap:3px}}.pw-cheat-grid{{grid-template-columns:repeat(2,1fr);gap:6px}}.pw-cheat-item{{padding:8px;min-height:70px}}.pw-category-head{{padding:14px}}.pw-health-card{{padding-left:0}}.pw-health-grid{{grid-template-columns:repeat(2,1fr)}}.pw-card-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.pw-card{{padding:10px}}.pw-card,.pw-card:nth-child(2n),.pw-card:nth-child(3n){{border-right:1px solid var(--pw-line)}}.pw-card:nth-child(2n){{border-right:none}}.pw-action{{padding:7px 6px;gap:5px}}.pw-action-fire{{font-size:15px}}.pw-action small{{font-size:8px}}.pw-symbol{{font-size:15px}}.pw-role{{display:none}}.pw-company{{max-width:105px}}.pw-status{{font-size:7.4px;padding:4px 5px}}.pw-price{{font-size:18px}}.pw-zone-box{{padding:5px}}.pw-zone-label{{font-size:6.5px}}.pw-zone-value{{font-size:10.5px}}.pw-mini-metrics{{gap:3px}}.pw-reasons{{font-size:9.5px;margin-left:13px}}.pw-foot{{flex-direction:column;gap:6px}}}}
    </style>

    <section class="portfolio-watch" id="stocks">
      <div class="pw-hero">
        <div class="pw-kicker">Personal market dashboard</div>
        <h2>Chai's Entry-Zone Watchlist</h2>
        <p>Fast, action-first view of your predefined entry ranges. Bright fire signals mean price has reached or is approaching a range you already set; they are not a guarantee that the stock will rise.</p>
        <div class="pw-hero-meta"><span class="pw-hero-chip">{len(ordered)} stocks</span><span class="pw-hero-chip">{len(CATEGORY_DEFS)} focused buckets</span><span class="pw-hero-chip">33% tranche framework</span><span class="pw-hero-chip">Live Yahoo Finance inputs</span></div>
      </div>

      <div class="pw-alert-strip">
        <div class="pw-alert pw-alert-hot"><strong>🔥🔥 ENTRY ZONE HIT</strong><span>{escape(hot_text)} · predefined range active</span></div>
        <div class="pw-alert pw-alert-near"><strong>🔥 NEAR ENTRY</strong><span>{escape(near_text)} · within 3% above your range</span></div>
      </div>

      <div class="pw-cheat">
        <div class="pw-cheat-head"><h3>📌 Quick Cheat Sheet — plain English</h3><span>Keep this at the top so every signal is instantly understandable.</span></div>
        <div class="pw-cheat-grid">
          <div class="pw-cheat-item"><b>ENTRY ZONE</b><span>Your planned price range for starting a position.</span></div>
          <div class="pw-cheat-item"><b>TRANCHE</b><span>One piece of the buy. Your framework uses roughly 33% at a time.</span></div>
          <div class="pw-cheat-item"><b>MA50</b><span>Average closing price over 50 trading days — a medium-term trend guide.</span></div>
          <div class="pw-cheat-item"><b>MA200</b><span>Average closing price over 200 trading days — a long-term trend/support guide.</span></div>
          <div class="pw-cheat-item"><b>ROE</b><span>Return on equity — how efficiently a company turns shareholder capital into profit.</span></div>
          <div class="pw-cheat-item"><b>UPSIDE</b><span>How far the analyst target sits above today's price. It is an estimate, not a promise.</span></div>
          <div class="pw-cheat-item"><b>WATCHLIST SCORE</b><span>Combined model health score. Higher means the underlying signals look stronger.</span></div>
          <div class="pw-cheat-item"><b>SUPPORT</b><span>A price area where buyers have historically stepped in and declines may slow.</span></div>
        </div>
      </div>

      <div class="pw-summary">
        <div class="pw-summary-card"><span>🔥 Entry zone hit</span><strong>{status_counts['in-zone']}</strong><small>Your range is active</small></div>
        <div class="pw-summary-card"><span>🔥 Near zone</span><strong>{status_counts['near-zone']}</strong><small>Within 3% above ceiling</small></div>
        <div class="pw-summary-card"><span>⏳ Wait</span><strong>{status_counts['wait']}</strong><small>Still above target</small></div>
        <div class="pw-summary-card"><span>⚠️ Below zone</span><strong>{status_counts['below-zone']}</strong><small>Recheck thesis/news first</small></div>
      </div>

      {''.join(category_html)}

      <div class="pw-foot">
        <div><strong>Signal logic:</strong> 🔥🔥 means current price is inside your predefined zone; 🔥 means it is within 3% above the ceiling. The signal is price math, not a prediction.</div>
        <div>Informational dashboard only. Revalidate the company thesis, diversification, taxes and risk before placing an order.</div>
      </div>
    </section>"""