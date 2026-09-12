"""Stocks-only personalized dashboard renderer."""
from html import escape

CATEGORY_DEFS = [
    {"name":"AI Compute & Semis","icon":"⚡","tone":"purple","tickers":["MU","NVDA","AVGO"],"thesis":"AI infrastructure leaders. Best entries usually come on pullbacks toward support, not after vertical moves."},
    {"name":"Mega-cap Platforms","icon":"☁️","tone":"blue","tickers":["GOOGL","AMZN","MSFT","META","AAPL","ORCL"],"thesis":"Cloud, AI distribution and durable cash-flow platforms. Oracle is included here for cloud and database AI exposure."},
    {"name":"Data Infrastructure","icon":"💾","tone":"teal","tickers":["PSTG","SNOW","CRM","WDAY"],"thesis":"Enterprise data, storage and software. Pure Storage adds the physical data layer behind AI workloads."},
    {"name":"Payments & Data Moats","icon":"💳","tone":"green","tickers":["V","MA","SPGI"],"thesis":"High-quality transaction and information toll roads with durable margins and recurring demand."},
    {"name":"Travel & Cyclicals","icon":"✈️","tone":"rose","tickers":["DAL","UAL","EXPE"],"thesis":"More cyclical names where peer confirmation and disciplined entry prices matter most."},
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
        return low, high, "Curated target zone"

    price = s.get("price") or 0
    ma50 = s.get("ma50")
    ma200 = s.get("ma200")
    anchors = [x for x in (ma50, ma200) if x and x > 0]
    if anchors:
        below_or_near = [x for x in anchors if x <= price * 1.05]
        anchor = max(below_or_near) if below_or_near else min(anchors)
        return anchor * 0.985, anchor * 1.015, "MA support-derived zone"
    if price:
        anchor = price * 0.95
        return anchor * 0.985, anchor * 1.015, "5% pullback fallback"
    return 0, 0, "No price data"


def _zone_status(price, low, high):
    if not price or not low or not high:
        return {"key":"no-data","label":"NO DATA","detail":"Price unavailable"}
    if low <= price <= high:
        return {"key":"in-zone","label":"🔥🔥 ENTRY ZONE HIT","detail":"Price is inside the defined entry zone."}
    if price < low:
        pct = (low-price)/low*100
        return {"key":"below-zone","label":"⚠️ BELOW RANGE","detail":f"{pct:.1f}% below the zone floor — recheck thesis/news before acting."}
    pct = (price-high)/high*100
    if pct <= 3:
        return {"key":"near-zone","label":"🔥 NEAR ENTRY","detail":f"Only {pct:.1f}% above the zone ceiling."}
    return {"key":"wait","label":"⏳ WAIT","detail":f"{pct:.1f}% above the zone ceiling."}


def _day_change(v):
    if v is None:
        return '<span class="pw-muted">—</span>'
    cls = "pw-up" if v >= 0 else "pw-down"
    sym = "▲" if v >= 0 else "▼"
    return f'<span class="{cls}">{sym} {abs(v):.2f}%</span>'


def _render_card(s):
    ticker = s["ticker"]
    meta = STOCK_META[ticker]
    price = s.get("price") or 0
    low, high, zone_basis = _entry_zone(s, meta)
    z = _zone_status(price, low, high)
    target = _target_6m(s)
    score = s.get("health_score",0)
    grade = s.get("grade","?")
    analyst = (s.get("analyst_rec") or "none").replace("_"," ").title()
    reasons = "".join(f"<li>{escape(r)}</li>" for r in meta["reasons"])
    target_up = s.get("upside_pct")
    return f"""
    <article class="pw-card pw-card-{z['key']}">
      <div class="pw-card-top">
        <div><div class="pw-symbol-row"><span class="pw-symbol">{escape(ticker)}</span><span class="pw-role">{escape(meta['label'])}</span></div><div class="pw-company">{escape(s.get('name',ticker))}</div></div>
        <span class="pw-status pw-status-{z['key']}">{z['label']}</span>
      </div>
      <div class="pw-price-row">
        <div><div class="pw-price">{_money(price)}</div><div class="pw-change">{_day_change(s.get('day_change'))} today</div></div>
        <div class="pw-zone-box"><div class="pw-zone-label">ENTRY ZONE</div><div class="pw-zone-value">${low:,.0f}–${high:,.0f}</div></div>
      </div>
      <div class="pw-action-line">{escape(z['detail'])}</div>
      <div class="pw-target-box"><div><span>6-MONTH TARGET*</span><strong>{_money(target)}</strong></div><div><span>UPSIDE TO TARGET</span><strong>{('+'+str(target_up)+'%') if target_up is not None else '—'}</strong></div></div>
      <div class="pw-mini-metrics">
        <div><span>Watchlist score</span><strong>{score:.1f} <small>{escape(grade)}</small></strong></div>
        <div><span>Analyst</span><strong>{escape(analyst)}</strong></div>
        <div><span>Entry basis</span><strong>{escape(zone_basis)}</strong></div>
      </div>
      <div class="pw-why-title">Why it stays on the list</div><ul class="pw-reasons">{reasons}</ul>
    </article>"""


def render_stock_section(stocks:list)->str:
    if not stocks:
        return ""
    by_ticker={s.get("ticker"):s for s in stocks}
    ordered=[]
    for c in CATEGORY_DEFS:
        for t in c["tickers"]:
            if t in by_ticker:
                ordered.append(by_ticker[t])

    hot=[]; near=[]
    for s in ordered:
        low,high,_=_entry_zone(s,STOCK_META[s["ticker"]])
        k=_zone_status(s.get("price") or 0,low,high)["key"]
        if k=="in-zone": hot.append(s["ticker"])
        elif k=="near-zone": near.append(s["ticker"])

    sections=[]
    for c in CATEGORY_DEFS:
        items=[by_ticker[t] for t in c["tickers"] if t in by_ticker]
        if not items: continue
        cards="".join(_render_card(s) for s in items)
        sections.append(f"""
        <section class="pw-category pw-tone-{c['tone']}">
          <div class="pw-category-head"><div class="pw-category-title-wrap"><div class="pw-category-icon">{c['icon']}</div><div><h3>{escape(c['name'])}</h3><p>{escape(c['thesis'])}</p></div></div></div>
          <div class="pw-card-grid">{cards}</div>
        </section>""")

    hot_text=", ".join(hot) if hot else "None right now"
    near_text=", ".join(near) if near else "None right now"

    return f"""
    <style>
      .portfolio-watch{{--pw-ink:#172033;--pw-muted:#667085;--pw-line:#e7eaf0;--pw-green:#0f8a5f;--pw-green-bg:#e8f8f1;--pw-blue:#2563eb;--pw-blue-bg:#edf4ff;--pw-red:#c24157;--pw-red-bg:#fff0f2;--pw-amber:#9a5a00;--pw-amber-bg:#fff4df;--pw-slate:#475467;--pw-slate-bg:#f2f4f7;color:var(--pw-ink);font-family:'Source Sans 3',system-ui,sans-serif}}
      .portfolio-watch *{{box-sizing:border-box}} .pw-hero{{border-radius:22px;padding:26px;color:white;background:linear-gradient(135deg,#07111f,#172a46 55%,#273f69);box-shadow:0 18px 45px rgba(15,23,42,.16);margin-bottom:14px}}
      .pw-kicker{{font-size:11px;font-weight:850;letter-spacing:1.2px;text-transform:uppercase;color:#b8c6ff}} .pw-hero h2{{font-family:'Playfair Display',Georgia,serif;font-size:30px;margin:3px 0 6px}} .pw-hero p{{color:#d5deeb;font-size:13px;max-width:850px}}
      .pw-alerts{{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin:15px 0}} .pw-alert{{border-radius:13px;padding:12px 14px;font-size:12px;font-weight:700}} .pw-alert.hot{{background:#fff0ec;border:1px solid #ffd2c8;color:#a6341f}} .pw-alert.near{{background:#edf4ff;border:1px solid #cfe0ff;color:#2459a9}}
      .pw-rules{{background:#fff;border:1px solid var(--pw-line);border-radius:16px;padding:16px;margin-bottom:16px;box-shadow:0 4px 18px rgba(15,23,42,.04)}} .pw-rules h3{{margin:0 0 10px;font-size:16px}} .pw-rule-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}} .pw-rule{{padding:10px;border-radius:10px;background:#f8fafc;border:1px solid #eef1f5;font-size:11.5px;line-height:1.4}} .pw-rule strong{{display:block;color:#243247;margin-bottom:2px}}
      .pw-cheat{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-bottom:18px}} .pw-cheat div{{background:#fff;border:1px solid var(--pw-line);border-radius:10px;padding:9px 10px;font-size:11px}} .pw-cheat b{{display:block;font-size:10px;text-transform:uppercase;letter-spacing:.4px;color:#344054}}
      .pw-category{{background:#fff;border:1px solid var(--pw-line);border-radius:18px;margin-bottom:18px;overflow:hidden;box-shadow:0 5px 20px rgba(15,23,42,.04)}} .pw-category-head{{padding:16px 18px;border-bottom:1px solid var(--pw-line)}} .pw-category-title-wrap{{display:flex;gap:10px}} .pw-category-icon{{width:36px;height:36px;display:grid;place-items:center;border-radius:10px;background:#f4f6fa;font-size:18px}} .pw-category h3{{margin:0 0 3px;font-family:'Playfair Display',Georgia,serif;font-size:18px}} .pw-category p{{margin:0;color:var(--pw-muted);font-size:11.5px}}
      .pw-card-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr))}} .pw-card{{padding:15px;border-right:1px solid var(--pw-line);border-bottom:1px solid var(--pw-line);min-width:0}} .pw-card:nth-child(3n){{border-right:none}} .pw-card-in-zone{{background:linear-gradient(180deg,#fff7f3,#fff)}} .pw-card-near-zone{{background:linear-gradient(180deg,#f4f8ff,#fff)}}
      .pw-card-top{{display:flex;justify-content:space-between;gap:8px}} .pw-symbol-row{{display:flex;align-items:center;gap:6px}} .pw-symbol{{font-size:17px;font-weight:850}} .pw-role{{font-size:9px;background:#f2f4f7;color:#667085;border-radius:6px;padding:3px 5px}} .pw-company{{font-size:10.5px;color:var(--pw-muted);max-width:180px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
      .pw-status{{font-size:9px;font-weight:900;padding:5px 7px;border-radius:999px;white-space:nowrap}} .pw-status-in-zone{{color:#9f2d18;background:#ffe5dd;box-shadow:0 0 0 2px rgba(255,94,53,.08)}} .pw-status-near-zone{{color:#2459a9;background:#e6efff}} .pw-status-wait{{color:var(--pw-slate);background:var(--pw-slate-bg)}} .pw-status-below-zone{{color:var(--pw-red);background:var(--pw-red-bg)}} .pw-status-no-data{{color:var(--pw-amber);background:var(--pw-amber-bg)}}
      .pw-price-row{{display:flex;justify-content:space-between;align-items:end;gap:9px;margin:12px 0 8px}} .pw-price{{font-size:23px;font-weight:850}} .pw-change{{font-size:10.5px;color:var(--pw-muted)}} .pw-up{{color:var(--pw-green)!important;font-weight:750}} .pw-down{{color:var(--pw-red)!important;font-weight:750}} .pw-zone-box{{text-align:right;background:#f8fafc;border:1px solid #edf0f4;border-radius:9px;padding:7px 9px}} .pw-zone-label{{font-size:8px;color:var(--pw-muted);font-weight:850;letter-spacing:.5px}} .pw-zone-value{{font-size:13px;font-weight:850}}
      .pw-action-line{{font-size:10.5px;color:#475467;background:#fbfcfe;border:1px solid #f0f2f5;border-radius:8px;padding:7px 8px}} .pw-target-box{{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin:9px 0;background:#0f172a;color:#fff;border-radius:10px;padding:9px}} .pw-target-box span{{display:block;font-size:8px;color:#aab4c5;font-weight:800;letter-spacing:.45px}} .pw-target-box strong{{display:block;font-size:14px;margin-top:1px}}
      .pw-mini-metrics{{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin:10px 0}} .pw-mini-metrics span{{display:block;font-size:8px;color:var(--pw-muted);text-transform:uppercase;font-weight:800}} .pw-mini-metrics strong{{display:block;font-size:10.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}} .pw-mini-metrics small{{color:var(--pw-muted);font-size:8px}} .pw-why-title{{border-top:1px solid #f0f2f5;padding-top:9px;font-size:9px;font-weight:850;text-transform:uppercase}} .pw-reasons{{margin:6px 0 0 15px;padding:0;font-size:10.5px;line-height:1.4;color:#475467}}
      .pw-foot{{font-size:10px;color:var(--pw-muted);padding:4px 2px 0;line-height:1.45}}
      @media(max-width:1050px){{.pw-card-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.pw-card:nth-child(3n){{border-right:1px solid var(--pw-line)}}.pw-card:nth-child(2n){{border-right:none}}}}
      @media(max-width:720px){{.pw-hero{{padding:20px 16px;border-radius:16px}}.pw-hero h2{{font-size:24px}}.pw-card-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.pw-card{{padding:11px}}.pw-symbol{{font-size:15px}}.pw-role{{display:none}}.pw-status{{font-size:7.5px;padding:4px 5px}}.pw-price{{font-size:19px}}.pw-zone-value{{font-size:11px}}.pw-target-box strong{{font-size:12px}}.pw-rule-grid,.pw-cheat,.pw-alerts{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}
      @media(max-width:430px){{.pw-card-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.pw-company{{max-width:105px}}.pw-mini-metrics{{grid-template-columns:1fr 1fr}}.pw-mini-metrics div:last-child{{grid-column:1/-1}}}}
    </style>
    <section class="portfolio-watch" id="stocks">
      <div class="pw-hero"><div class="pw-kicker">Stocks only · action first</div><h2>Chai's Stock Command Center</h2><p>Entry zones, live prices, six-month planning targets and simple action signals in one compact view.</p></div>
      <div class="pw-alerts"><div class="pw-alert hot">🔥🔥 ENTRY ZONE HIT: {escape(hot_text)}</div><div class="pw-alert near">🔥 NEAR ENTRY: {escape(near_text)}</div></div>
      <div class="pw-rules"><h3>How an entry signal is defined</h3><div class="pw-rule-grid">
        <div class="pw-rule"><strong>🔥🔥 Entry Zone Hit</strong>Current price is inside the defined buy zone. This is the strongest price-based action signal.</div>
        <div class="pw-rule"><strong>🔥 Near Entry</strong>Current price is no more than 3% above the zone ceiling. Watch closely rather than chase.</div>
        <div class="pw-rule"><strong>⏳ Wait</strong>Price is more than 3% above the zone. Wait for a pullback instead of buying extended.</div>
        <div class="pw-rule"><strong>⚠️ Below Range</strong>Price has fallen below the zone floor. Treat this as a thesis/news recheck, not an automatic bargain.</div>
        <div class="pw-rule"><strong>33% Tranche Rule</strong>When you choose to act, deploy in thirds rather than all at once: roughly 33% / 33% / 33%.</div>
        <div class="pw-rule"><strong>ORCL / PSTG Rule</strong>Their zones are derived from the nearest useful 50-day or 200-day moving-average support, ±1.5% around that support.</div>
      </div></div>
      <div class="pw-cheat">
        <div><b>MA50</b>Average price over the last 50 trading days — short/medium-term trend support.</div><div><b>MA200</b>Average price over the last 200 trading days — long-term trend support.</div>
        <div><b>Entry Zone</b>The price band where the risk/reward becomes attractive enough to consider a tranche.</div><div><b>6M Target</b>Current analyst mean price target used here as a practical six-month planning proxy.</div>
        <div><b>Upside</b>Percent gain from today's price to the six-month target.</div><div><b>Watchlist Score</b>Composite quality/valuation/growth/technical score from the stock-health model.</div>
      </div>
      {''.join(sections)}
      <div class="pw-foot">* The 6-month target is not a guaranteed forecast. It uses the latest analyst mean target available from Yahoo Finance as a planning proxy and refreshes with the page.</div>
    </section>"""
