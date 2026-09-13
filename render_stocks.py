"""Stocks-only Chai Ledger renderer."""
from html import escape
from datetime import datetime

CATEGORY_DEFS = [
    {"name":"AI Compute & Semis","tickers":["MU","NVDA","AVGO"],"thesis":"Infrastructure leaders — best entries come on pullbacks toward support, not vertical moves."},
    {"name":"Mega-cap Platforms","tickers":["GOOGL","AMZN","MSFT","META","AAPL","ORCL"],"thesis":"Cloud, AI distribution, and durable cash-flow compounders — Oracle included for cloud/database AI exposure."},
    {"name":"Data Infrastructure","tickers":["PSTG","SNOW","CRM","WDAY"],"thesis":"Enterprise data, storage, and software — Pure Storage adds the physical data layer behind AI workloads."},
    {"name":"Payments & Data Moats","tickers":["V","MA","SPGI"],"thesis":"High-quality transaction and information toll roads with durable margins and recurring demand."},
    {"name":"Travel & Cyclicals","tickers":["DAL","UAL","EXPE"],"thesis":"More cyclical names where peer confirmation and disciplined entry prices matter most."},
]

STOCK_META = {
    "MU":{"zone":(935,945),"label":"High priority","reasons":["HBM and AI-memory demand","Memory pricing leverage","Higher cyclicality = stricter entry discipline"]},
    "NVDA":{"zone":(205,212),"label":"High priority","reasons":["AI accelerator leadership","CUDA ecosystem moat","Hyperscaler AI capex remains the demand engine"]},
    "AVGO":{"zone":(340,350),"label":"High priority","reasons":["AI networking + custom silicon","VMware recurring software cash flow","Strong free-cash-flow profile"]},
    "GOOGL":{"zone":(325,335),"label":"High priority","reasons":["Search + YouTube cash engine","Cloud and AI growth optionality","Mega-cap quality"]},
    "AMZN":{"zone":(248,254),"label":"High priority","reasons":["AWS cloud + AI demand","Retail margin expansion","Advertising is a high-margin engine"]},
    "MSFT":{"zone":(440,450),"label":"Core compounder","reasons":["Azure + enterprise AI distribution","Recurring software revenue","Balance-sheet quality"]},
    "META":{"zone":(585,595),"label":"Core compounder","reasons":["AI improves ad efficiency","Large engagement base","Strong cash generation"]},
    "AAPL":{"zone":(305,315),"label":"Core compounder","reasons":["Sticky device + services ecosystem","Huge installed base","Capital returns provide support"]},
    "V":{"zone":(355,363),"label":"Core compounder","reasons":["Digital payments tailwind","High-margin global network","Cross-border volume"]},
    "MA":{"zone":(550,558),"label":"Core compounder","reasons":["Global payments moat","Strong cross-border economics","Asset-light compounding model"]},
    "SPGI":{"zone":(415,425),"label":"Data moat","reasons":["Ratings + indices + market data moat","Recurring information products","Capital-markets recovery upside"]},
    "CRM":{"zone":(220,230),"label":"Turnaround","reasons":["Large enterprise installed base","FCF improvement","AI monetization is the key upside test"]},
    "SNOW":{"zone":(285,300),"label":"Growth data","reasons":["Cloud data platform for AI workflows","Consumption can reaccelerate","Valuation discipline matters"]},
    "WDAY":{"zone":(165,175),"label":"Turnaround","reasons":["Sticky HR + finance subscriptions","Buybacks support per-share value","Support area matters"]},
    "DAL":{"zone":(72,78),"label":"Cyclical value","reasons":["Premium travel + loyalty economics","Operating leverage","UAL confirmation improves signal"]},
    "UAL":{"zone":(92,98),"label":"Cyclical value","reasons":["Strong international network","Capacity discipline","DAL confirmation matters"]},
    "EXPE":{"zone":(240,250),"label":"Travel platform","reasons":["Scaled travel platform","B2B + Vrbo growth levers","200-day MA is useful support context"]},
    "ORCL":{"zone":None,"label":"Cloud compounder","reasons":["OCI + database cloud exposure","AI infrastructure demand","Large recurring enterprise base"]},
    "PSTG":{"zone":None,"label":"AI data infrastructure","reasons":["Flash storage for AI/data workloads","Subscription mix improves durability","High-growth infrastructure name needs disciplined entries"]},
}


def _money(v):
    return f"${v:,.2f}" if v not in (None, 0) else "—"


def _target_6m(s):
    price = s.get("price") or 0
    upside = s.get("upside_pct")
    if not price or upside is None:
        return None
    return price * (1 + upside / 100.0)


def _entry_zone(s, meta):
    if meta.get("zone"):
        low, high = meta["zone"]
        return low, high, "Curated zone"
    price = s.get("price") or 0
    ma50 = s.get("ma50")
    ma200 = s.get("ma200")
    anchors = [x for x in (ma50, ma200) if x and x > 0]
    if anchors:
        below_or_near = [x for x in anchors if x <= price * 1.05]
        anchor = max(below_or_near) if below_or_near else min(anchors)
        return anchor * 0.985, anchor * 1.015, "MA-derived zone"
    if price:
        anchor = price * 0.95
        return anchor * 0.985, anchor * 1.015, "5% pullback zone"
    return 0, 0, "No price data"


def _zone_status(price, low, high):
    if not price or not low or not high:
        return {"key":"no-data","label":"NO DATA","detail":"Price unavailable"}
    if low <= price <= high:
        return {"key":"in-zone","label":"ENTRY","detail":"Inside buy zone"}
    if price < low:
        pct = (low-price)/low*100
        return {"key":"below-zone","label":"BELOW","detail":f"{pct:.1f}% below floor"}
    pct = (price-high)/high*100
    if pct <= 3:
        return {"key":"near-zone","label":"NEAR ENTRY","detail":f"Only {pct:.1f}% above ceiling"}
    return {"key":"wait","label":"WAIT","detail":f"{pct:.1f}% above ceiling"}


def _day_change(v):
    if v is None:
        return '<span class="ledger-muted">—</span>'
    cls = "ledger-up" if v >= 0 else "ledger-down"
    sym = "▲" if v >= 0 else "▼"
    return f'<span class="{cls}">{sym} {abs(v):.2f}%</span>'


def _score_desc(score):
    if score >= 80: return "A", "Strong Buy"
    if score >= 70: return "B", "Buy"
    if score >= 55: return "C", "Hold"
    if score >= 40: return "D", "Caution"
    return "F", "Weak"


def _render_card(s):
    ticker = s["ticker"]
    meta = STOCK_META[ticker]
    price = s.get("price") or 0
    low, high, zone_basis = _entry_zone(s, meta)
    z = _zone_status(price, low, high)
    target = _target_6m(s)
    target_up = s.get("upside_pct")
    score = s.get("health_score", 0)
    grade, stance = _score_desc(score)
    analyst = (s.get("analyst_rec") or "none").replace("_", " ").title()
    reasons = "".join(f"<li>{escape(r)}</li>" for r in meta["reasons"])
    zone_text = f"${low:,.0f}–${high:,.0f}" if low and high else "—"
    return f"""
    <article class="ledger-card status-{z['key']}">
      <div class="ledger-card-head">
        <div>
          <div class="ledger-ticker">{escape(ticker)}</div>
          <div class="ledger-company">{escape(s.get('name', ticker))}</div>
          <div class="ledger-tag">{escape(meta['label'].upper())}</div>
        </div>
        <div class="ledger-status">{escape(z['label'])}</div>
      </div>

      <div class="ledger-price-row">
        <div class="ledger-price">{_money(price)}</div>
        <div class="ledger-day">{_day_change(s.get('day_change'))}</div>
      </div>

      <div class="zone-line">
        <span>Zone {zone_text}</span>
        <span>{escape(z['detail'])}</span>
      </div>
      <div class="zone-gauge"><span class="zone-mark zone-low"></span><span class="zone-fill"></span><span class="zone-mark zone-high"></span></div>

      <div class="target-strip">
        <div><span>6-MO TARGET*</span><strong>{_money(target)}</strong></div>
        <div class="target-right"><span>UPSIDE</span><strong>{('+' + str(target_up) + '%') if target_up is not None else '—'}</strong></div>
      </div>

      <div class="ledger-metrics">
        <div><strong>{score:.1f} {grade}</strong><span>Watchlist</span></div>
        <div><strong>{escape(stance)}</strong><span>Strategy</span></div>
        <div><strong>{escape(analyst)}</strong><span>Street</span></div>
        <div><strong>{escape(zone_basis)}</strong><span>Zone basis</span></div>
      </div>

      <div class="ledger-why">WHY IT STAYS ON THE LIST</div>
      <ul class="ledger-reasons">{reasons}</ul>
    </article>"""


def render_stock_section(stocks:list)->str:
    if not stocks:
        return ""

    by_ticker = {s.get("ticker"): s for s in stocks}
    ordered = []
    for c in CATEGORY_DEFS:
        for t in c["tickers"]:
            if t in by_ticker:
                ordered.append(by_ticker[t])

    hot, near = [], []
    for s in ordered:
        low, high, _ = _entry_zone(s, STOCK_META[s["ticker"]])
        status = _zone_status(s.get("price") or 0, low, high)["key"]
        if status == "in-zone": hot.append(s["ticker"])
        elif status == "near-zone": near.append(s["ticker"])

    sections = []
    for c in CATEGORY_DEFS:
        items = [by_ticker[t] for t in c["tickers"] if t in by_ticker]
        if not items:
            continue
        cards = "".join(_render_card(s) for s in items)
        sections.append(f"""
        <section class="ledger-section">
          <div class="ledger-section-title">
            <h2>{escape(c['name'])}</h2>
            <span>{escape(c['thesis'])}</span>
          </div>
          <div class="ledger-grid">{cards}</div>
        </section>""")

    hot_text = " · ".join(hot) if hot else "none right now"
    near_text = " · ".join(near) if near else "none right now"
    now = datetime.now().strftime("%b %d, %Y · %I:%M %p")

    return f"""
    <style>
      :root{{--paper:#f3ede2;--ink:#171713;--muted:#69645b;--rule:#25241f;--green:#1f6b49;--amber:#a56a16;--red:#a54336;--bar:#15211c}}
      body{{background:#e9e4da!important}}
      .ledger-page{{max-width:1180px;margin:0 auto;background:var(--paper);color:var(--ink);font-family:Georgia,'Times New Roman',serif;padding:22px 28px 34px;box-shadow:0 0 0 1px rgba(0,0,0,.02)}}
      .ledger-masthead{{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;border-bottom:2px solid var(--rule);padding-bottom:12px}}
      .ledger-title{{font-size:40px;line-height:.95;font-weight:700;letter-spacing:-1px;margin:0}}
      .ledger-deck{{font-size:11px;font-style:italic;color:var(--muted);margin-top:6px}}
      .ledger-edition{{font-family:Arial,sans-serif;text-align:right;font-size:9px;line-height:1.55;white-space:nowrap}}
      .ledger-edition b{{font-weight:700}}
      .tape{{display:flex;align-items:center;gap:9px;flex-wrap:wrap;border-bottom:1px solid var(--rule);padding:8px 0 7px;font-family:Arial,sans-serif;font-size:9px;text-transform:uppercase;letter-spacing:.2px}}
      .tape-label{{font-family:Georgia,serif;font-style:italic;font-weight:700}}
      .tape-dot{{width:7px;height:7px;border-radius:50%;display:inline-block;margin-right:4px;vertical-align:middle}}
      .dot-green{{background:var(--green)}} .dot-amber{{background:var(--amber)}}

      .ledger-section{{margin-top:25px}}
      .ledger-section-title{{display:flex;align-items:baseline;gap:10px;border-bottom:2px solid var(--rule);padding-bottom:5px;margin-bottom:0}}
      .ledger-section-title h2{{font-size:21px;line-height:1;margin:0;font-weight:700}}
      .ledger-section-title span{{font-size:9px;font-style:italic;color:var(--muted)}}
      .ledger-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:0;border-left:1px solid var(--rule)}}
      .ledger-card{{padding:10px 12px 12px;border-right:1px solid var(--rule);border-bottom:1px solid #a49d90;min-width:0;position:relative}}
      .ledger-card.status-near-zone{{border-left:3px solid var(--amber)}}
      .ledger-card.status-in-zone{{border-left:3px solid var(--green);background:rgba(255,255,255,.13)}}
      .ledger-card.status-below-zone{{border-left:3px solid var(--red)}}
      .ledger-card-head{{display:flex;justify-content:space-between;gap:8px;align-items:flex-start}}
      .ledger-ticker{{font-size:17px;font-weight:700;line-height:1}}
      .ledger-company{{font-family:Arial,sans-serif;font-size:8px;color:var(--muted);margin:2px 0 4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:175px}}
      .ledger-tag{{display:inline-block;border:1px solid var(--rule);padding:1px 4px;font-family:Arial,sans-serif;font-size:6.7px;line-height:1.1;letter-spacing:.2px}}
      .ledger-status{{font-family:Arial,sans-serif;font-size:7px;text-transform:uppercase;letter-spacing:.5px;color:#6b665c;white-space:nowrap}}
      .status-near-zone .ledger-status{{color:var(--amber)}} .status-in-zone .ledger-status{{color:var(--green);font-weight:700}} .status-below-zone .ledger-status{{color:var(--red)}}
      .ledger-price-row{{display:flex;align-items:baseline;gap:8px;margin-top:8px}}
      .ledger-price{{font-family:Arial,sans-serif;font-size:24px;font-weight:700;letter-spacing:-.5px}}
      .ledger-day{{font-family:Arial,sans-serif;font-size:8px}}
      .ledger-up{{color:var(--green);font-weight:700}} .ledger-down{{color:var(--red);font-weight:700}} .ledger-muted{{color:var(--muted)}}
      .zone-line{{display:flex;justify-content:space-between;gap:8px;font-family:Arial,sans-serif;font-size:6.8px;color:#4f4b43;margin-top:5px}}
      .zone-line span:last-child{{text-align:right}}
      .zone-gauge{{position:relative;height:8px;border-bottom:1px solid #777166;margin:0 0 8px}}
      .zone-fill{{position:absolute;left:38%;right:38%;bottom:-2px;height:3px;background:var(--green)}}
      .zone-mark{{position:absolute;bottom:-3px;width:2px;height:5px;background:var(--rule)}} .zone-low{{left:38%}} .zone-high{{right:38%}}
      .target-strip{{display:grid;grid-template-columns:1fr 1fr;background:var(--bar);color:#f3ede2;padding:7px 9px;margin:3px 0 8px;font-family:Arial,sans-serif}}
      .target-strip span{{display:block;font-size:6.5px;color:#bfc5bd;letter-spacing:.5px}}
      .target-strip strong{{display:block;font-size:12px;margin-top:1px}}
      .target-right{{text-align:right}} .target-right strong{{color:#8bd2a9}}
      .ledger-metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:5px;font-family:Arial,sans-serif;margin-bottom:7px}}
      .ledger-metrics div{{min-width:0}}
      .ledger-metrics strong{{display:block;font-size:8.2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
      .ledger-metrics span{{display:block;font-size:6.5px;color:#746e64}}
      .ledger-why{{font-family:Arial,sans-serif;font-size:6.5px;font-weight:700;letter-spacing:.3px;margin-top:4px}}
      .ledger-reasons{{margin:3px 0 0 12px;padding:0;font-family:Arial,sans-serif;font-size:7.3px;line-height:1.45;color:#454139}}

      .how-box{{border:1.5px solid var(--rule);padding:12px 14px;margin-top:28px}}
      .how-box h3{{font-size:13px;margin:0 0 8px}}
      .how-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;font-family:Arial,sans-serif}}
      .how-grid b{{display:block;font-size:7.5px;margin-bottom:2px}} .how-grid p{{font-size:7px;line-height:1.4;color:#4f4a42;margin:0}}
      .how-dot{{width:7px;height:7px;border-radius:50%;display:inline-block;margin-right:3px}}
      .how-green{{background:var(--green)}} .how-amber{{background:var(--amber)}} .how-gray{{background:#6f6a60}} .how-red{{background:var(--red)}}

      @media(max-width:820px){{.ledger-page{{padding:16px 14px}}.ledger-title{{font-size:31px}}.ledger-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.ledger-section-title{{display:block}}.ledger-section-title span{{display:block;margin-top:4px}}.how-grid{{grid-template-columns:repeat(2,1fr)}}}}
      @media(max-width:520px){{.ledger-page{{padding:12px 9px}}.ledger-title{{font-size:27px}}.ledger-deck{{font-size:9px}}.ledger-edition{{font-size:7px}}.ledger-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.ledger-card{{padding:8px}}.ledger-price{{font-size:19px}}.ledger-company{{max-width:120px}}.ledger-metrics{{grid-template-columns:repeat(2,1fr)}}.how-grid{{grid-template-columns:repeat(2,1fr);gap:9px}}}}
    </style>

    <main class="ledger-page" id="stocks">
      <header class="ledger-masthead">
        <div>
          <h1 class="ledger-title">The Chai Ledger</h1>
          <div class="ledger-deck">Entry zones, live prices, and six-month targets — one glance tells you act or wait.</div>
        </div>
        <div class="ledger-edition"><b>Edition:</b> Stocks Only · Action First<br><b>Updated:</b> {escape(now)}</div>
      </header>

      <div class="tape">
        <span class="tape-label">ON THE TAPE</span>
        <span><i class="tape-dot dot-green"></i>ENTRY ZONE HIT: {escape(hot_text)}</span>
        <span><i class="tape-dot dot-amber"></i>NEAR ENTRY: {escape(near_text)}</span>
      </div>

      {''.join(sections)}

      <section class="how-box">
        <h3>How to read this page</h3>
        <div class="how-grid">
          <div><b><i class="how-dot how-green"></i>Entry zone hit</b><p>Price sits inside the buy zone. Strongest action signal — deploy a tranche, not the whole position.</p></div>
          <div><b><i class="how-dot how-amber"></i>Near entry</b><p>Within 3% of the zone ceiling. Watch closely; do not chase.</p></div>
          <div><b><i class="how-dot how-gray"></i>Wait</b><p>More than 3% above the zone. Wait for a pullback instead of buying extended.</p></div>
          <div><b><i class="how-dot how-red"></i>Below range</b><p>Price fell below the zone floor. Recheck the thesis — not an automatic bargain.</p></div>
          <div><b>The gauge</b><p>A dot on a track: green band is the entry zone, dot is today's price. Dot inside band = act.</p></div>
          <div><b>Tranche rule</b><p>When you choose to act, deploy in thirds rather than all at once — roughly 33% / 33% / 33%.</p></div>
          <div><b>Zone basis</b><p>Most zones are curated. ORCL and PSTG use the nearest useful MA50/MA200 support with a ±1.5% band.</p></div>
          <div><b>6-mo target</b><p>Current analyst mean price target used as a practical six-month planning proxy — not a guarantee.</p></div>
        </div>
      </section>
    </main>"""
