"""Stocks-only Chai Ledger renderer."""
from html import escape
from datetime import datetime

CATEGORY_DEFS = [
    {"name":"AI Compute & Semis","tickers":["MU","NVDA","AVGO"],"thesis":"Infrastructure leaders — best entries come on disciplined pullbacks, not vertical moves."},
    {"name":"Mega-cap Platforms","tickers":["GOOGL","AMZN","MSFT","META","AAPL","ORCL"],"thesis":"Cloud, AI distribution, and durable cash-flow compounders — Oracle included for cloud/database AI exposure."},
    {"name":"Data Infrastructure","tickers":["PSTG","SNOW","CRM","WDAY"],"thesis":"Enterprise data, storage, and software — Pure Storage adds the physical data layer behind AI workloads."},
    {"name":"Payments & Data Moats","tickers":["V","MA","SPGI"],"thesis":"High-quality transaction and information toll roads with durable margins and recurring demand."},
    {"name":"Travel & Cyclicals","tickers":["DAL","UAL","EXPE"],"thesis":"More cyclical names where peer confirmation and disciplined entry prices matter most."},
]

ENTRY_LEVELS = {
    "MU":925, "NVDA":200, "AVGO":335,
    "GOOGL":320, "AMZN":245, "MSFT":435, "META":575, "AAPL":300,
    "V":350, "MA":545, "SPGI":410,
    "CRM":215, "SNOW":280, "WDAY":160,
    "DAL":70, "UAL":90, "EXPE":235,
    "ORCL":None, "PSTG":None,
}

STOCK_META = {
    "MU":{"reasons":["HBM and AI-memory demand","Memory pricing leverage","Higher cyclicality = stricter entry discipline"]},
    "NVDA":{"reasons":["AI accelerator leadership","CUDA ecosystem moat","Hyperscaler AI capex remains the demand engine"]},
    "AVGO":{"reasons":["AI networking + custom silicon","VMware recurring software cash flow","Strong free-cash-flow profile"]},
    "GOOGL":{"reasons":["Search + YouTube cash engine","Cloud and AI growth optionality","Mega-cap quality"]},
    "AMZN":{"reasons":["AWS cloud + AI demand","Retail margin expansion","Advertising is a high-margin engine"]},
    "MSFT":{"reasons":["Azure + enterprise AI distribution","Recurring software revenue","Balance-sheet quality"]},
    "META":{"reasons":["AI improves ad efficiency","Large engagement base","Strong cash generation"]},
    "AAPL":{"reasons":["Sticky device + services ecosystem","Huge installed base","Capital returns provide support"]},
    "V":{"reasons":["Digital payments tailwind","High-margin global network","Cross-border volume"]},
    "MA":{"reasons":["Global payments moat","Strong cross-border economics","Asset-light compounding model"]},
    "SPGI":{"reasons":["Ratings + indices + market data moat","Recurring information products","Capital-markets recovery upside"]},
    "CRM":{"reasons":["Large enterprise installed base","FCF improvement","AI monetization is the key upside test"]},
    "SNOW":{"reasons":["Cloud data platform for AI workflows","Consumption can reaccelerate","Valuation discipline matters"]},
    "WDAY":{"reasons":["Sticky HR + finance subscriptions","Buybacks support per-share value","Support area matters"]},
    "DAL":{"reasons":["Premium travel + loyalty economics","Operating leverage","UAL confirmation improves signal"]},
    "UAL":{"reasons":["Strong international network","Capacity discipline","DAL confirmation matters"]},
    "EXPE":{"reasons":["Scaled travel platform","B2B + Vrbo growth levers","200-day MA is useful support context"]},
    "ORCL":{"reasons":["OCI + database cloud exposure","AI infrastructure demand","Large recurring enterprise base"]},
    "PSTG":{"reasons":["Flash storage for AI/data workloads","Subscription mix improves durability","AI infrastructure demand"]},
}

def _money(v):
    return f"${v:,.2f}" if v not in (None, 0) else "—"

def _target_6m(s):
    if s.get("target_mean"):return s["target_mean"]
    price=s.get("price") or 0;upside=s.get("upside_pct")
    if not price or upside is None:return None
    return price*(1+upside/100)

def _entry_level(s):
    ticker=s["ticker"];curated=ENTRY_LEVELS.get(ticker)
    if curated:return float(curated),"Curated conservative level"
    price=s.get("price") or 0;anchors=[x for x in (s.get("ma50"),s.get("ma200")) if x and x>0]
    if anchors:
        below=[x for x in anchors if not price or x<=price];anchor=max(below) if below else min(anchors)
        return round(anchor*.98,2),"2% below MA support"
    if price:return round(price*.92,2),"8% pullback fallback"
    return 0,"No price data"

def _action(price,level):
    if not price or not level:return "WAIT","Price/entry unavailable","wait"
    if price<=level:
        pct=(level-price)/level*100;return "ENTER",f"{pct:.1f}% at/below entry threshold","enter"
    pct=(price-level)/level*100;return "WAIT",f"{pct:.1f}% above entry threshold","wait"

def _day_change(v):
    if v is None:return '<span class="ledger-muted">—</span>'
    cls="ledger-up" if v>=0 else "ledger-down";sym="▲" if v>=0 else "▼"
    return f'<span class="{cls}">{sym} {abs(v):.2f}%</span>'

def _signal_class(sig):
    return {"STRONG BUY":"sig-strong","BUY":"sig-buy","HOLD":"sig-hold","SELL":"sig-sell"}.get(sig,"sig-hold")

def _render_card(s):
    ticker=s["ticker"];meta=STOCK_META.get(ticker,{"reasons":[]});price=s.get("price") or 0;level,basis=_entry_level(s);action,detail,akey=_action(price,level);target=_target_6m(s);upside=s.get("upside_pct");score=s.get("health_score",0);grade=s.get("grade","?");signal=s.get("signal","HOLD");lifecycle=s.get("lifecycle","—");regime=s.get("weight_profile","—");reasons="".join(f"<li>{escape(r)}</li>" for r in meta["reasons"])
    return f"""
    <article class="ledger-card action-{akey}">
      <div class="ledger-card-head">
        <div class="ticker-stack">
          <div class="ticker-line"><span class="ledger-ticker">{escape(ticker)}</span><span class="health-inline"><b>{score:.1f} {escape(grade)}</b> · <b class="{_signal_class(signal)}">{escape(signal)}</b></span></div>
          <div class="ledger-company">{escape(s.get('name',ticker))}</div>
          <div class="ledger-lifecycle">{escape(lifecycle.upper())}</div>
        </div>
        <div class="ledger-action action-label-{akey}">{action}</div>
      </div>
      <div class="ledger-price-row"><div class="ledger-price">{_money(price)}</div><div class="ledger-day">{_day_change(s.get('day_change'))}</div></div>
      <div class="entry-row"><span>ENTER AT / BELOW</span><strong>{_money(level)}</strong><small>{escape(detail)}</small></div>
      <div class="target-strip"><div><span>6-MO TARGET*</span><strong>{_money(target)}</strong></div><div class="target-right"><span>UPSIDE</span><strong>{('+'+str(upside)+'%') if upside is not None else '—'}</strong></div></div>
      <div class="ledger-metrics"><div><strong>{escape(s.get('market_regime','—'))}</strong><span>Market</span></div><div><strong>{escape(s.get('sector_health','—'))}</strong><span>Sector</span></div><div><strong>{escape(s.get('conviction','—'))}</strong><span>Conviction</span></div><div><strong>{escape(basis)}</strong><span>Entry basis</span></div></div>
      <div class="model-line"><b>40-factor profile:</b> {escape(regime)}</div>
      <div class="ledger-why">WHY IT STAYS ON THE LIST</div><ul class="ledger-reasons">{reasons}</ul>
    </article>"""

def render_stock_section(stocks:list)->str:
    if not stocks:return ""
    by={s.get("ticker"):s for s in stocks};ordered=[]
    for c in CATEGORY_DEFS:
        for t in c["tickers"]:
            if t in by:ordered.append(by[t])
    enter=[s["ticker"] for s in ordered if _action(s.get("price") or 0,_entry_level(s)[0])[0]=="ENTER"];wait=[s["ticker"] for s in ordered if _action(s.get("price") or 0,_entry_level(s)[0])[0]=="WAIT"]
    sections=[]
    for c in CATEGORY_DEFS:
        items=[by[t] for t in c["tickers"] if t in by]
        if not items:continue
        sections.append(f"""<section class="ledger-section"><div class="ledger-section-title"><h2>{escape(c['name'])}</h2><span>{escape(c['thesis'])}</span></div><div class="ledger-grid">{''.join(_render_card(s) for s in items)}</div></section>""")
    now=datetime.now().strftime("%b %d, %Y · %I:%M %p");enter_text=" · ".join(enter) if enter else "none right now";wait_text=" · ".join(wait) if wait else "none"
    return f"""
    <style>
      :root{{--paper:#f3ede2;--ink:#171713;--muted:#69645b;--rule:#25241f;--green:#1f6b49;--amber:#a56a16;--red:#a54336;--bar:#15211c}}
      body{{background:#e9e4da!important}} .ledger-page{{max-width:1180px;margin:0 auto;background:var(--paper);color:var(--ink);font-family:Georgia,'Times New Roman',serif;padding:22px 28px 34px}}
      .ledger-masthead{{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;border-bottom:2px solid var(--rule);padding-bottom:12px}} .ledger-title{{font-size:40px;line-height:.95;font-weight:700;letter-spacing:-1px;margin:0}} .ledger-deck{{font-size:11px;font-style:italic;color:var(--muted);margin-top:6px}} .ledger-edition{{font-family:Arial,sans-serif;text-align:right;font-size:9px;line-height:1.55;white-space:nowrap}}
      .tape{{display:flex;align-items:center;gap:10px;flex-wrap:wrap;border-bottom:1px solid var(--rule);padding:8px 0 7px;font-family:Arial,sans-serif;font-size:9px;text-transform:uppercase}} .tape-label{{font-family:Georgia,serif;font-style:italic;font-weight:700}} .tape-dot{{width:7px;height:7px;border-radius:50%;display:inline-block;margin-right:4px;vertical-align:middle}} .dot-green{{background:var(--green)}} .dot-amber{{background:var(--amber)}}
      .ledger-section{{margin-top:25px}} .ledger-section-title{{display:flex;align-items:baseline;gap:10px;border-bottom:2px solid var(--rule);padding-bottom:5px}} .ledger-section-title h2{{font-size:21px;margin:0}} .ledger-section-title span{{font-size:9px;font-style:italic;color:var(--muted)}} .ledger-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));border-left:1px solid var(--rule)}}
      .ledger-card{{padding:10px 12px 12px;border-right:1px solid var(--rule);border-bottom:1px solid #a49d90;min-width:0}} .ledger-card.action-enter{{border-left:3px solid var(--green);background:rgba(255,255,255,.13)}} .ledger-card-head{{display:flex;justify-content:space-between;gap:8px;align-items:flex-start}} .ticker-line{{display:flex;align-items:baseline;gap:7px;flex-wrap:wrap}} .ledger-ticker{{font-size:17px;font-weight:700;line-height:1}} .health-inline{{font-family:Arial,sans-serif;font-size:8.5px;letter-spacing:.1px}} .sig-strong,.sig-buy{{color:var(--green)}} .sig-hold{{color:var(--amber)}} .sig-sell{{color:var(--red)}}
      .ledger-company{{font-family:Arial,sans-serif;font-size:8px;color:var(--muted);margin:2px 0 4px;max-width:190px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}} .ledger-lifecycle{{display:inline-block;border:1px solid var(--rule);padding:1px 4px;font-family:Arial,sans-serif;font-size:6.7px}} .ledger-action{{font-family:Arial,sans-serif;font-size:8px;font-weight:800;letter-spacing:.6px}} .action-label-enter{{color:var(--green)}} .action-label-wait{{color:#6b665c}}
      .ledger-price-row{{display:flex;align-items:baseline;gap:8px;margin-top:8px}} .ledger-price{{font-family:Arial,sans-serif;font-size:24px;font-weight:700;letter-spacing:-.5px}} .ledger-day{{font-family:Arial,sans-serif;font-size:8px}} .ledger-up{{color:var(--green);font-weight:700}} .ledger-down{{color:var(--red);font-weight:700}}
      .entry-row{{display:grid;grid-template-columns:auto auto;align-items:baseline;gap:3px 7px;border-top:1px solid #756f65;border-bottom:1px solid #756f65;padding:5px 0;margin:7px 0;font-family:Arial,sans-serif}} .entry-row span{{font-size:6.5px;letter-spacing:.5px}} .entry-row strong{{font-size:12px;text-align:right}} .entry-row small{{grid-column:1/-1;font-size:7px;color:var(--muted)}}
      .target-strip{{display:grid;grid-template-columns:1fr 1fr;background:var(--bar);color:#fff;padding:7px 8px;font-family:Arial,sans-serif}} .target-strip span{{display:block;font-size:6.4px;color:#c9d1cd;letter-spacing:.4px}} .target-strip strong{{display:block;font-size:12px;margin-top:2px}} .target-right{{text-align:right}} .target-right strong{{color:#71d39a}}
      .ledger-metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:5px;margin:8px 0 6px;font-family:Arial,sans-serif}} .ledger-metrics strong{{display:block;font-size:7.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}} .ledger-metrics span{{font-size:6.2px;color:var(--muted)}} .model-line{{font-family:Arial,sans-serif;font-size:7px;color:#49453e;border-top:1px solid #c1baae;padding-top:5px}} .ledger-why{{font-family:Arial,sans-serif;font-size:6.8px;font-weight:700;margin-top:6px}} .ledger-reasons{{font-family:Arial,sans-serif;font-size:7.2px;line-height:1.35;padding-left:12px;margin:3px 0 0}}
      .how-read{{border:1.5px solid var(--rule);margin-top:28px;padding:12px 14px}} .how-read h3{{font-size:13px;margin:0 0 8px}} .read-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}} .read-item{{font-family:Arial,sans-serif;font-size:7px;line-height:1.4}} .read-item b{{display:block;font-family:Georgia,serif;font-size:8px;margin-bottom:2px}} .footnote{{font-family:Arial,sans-serif;font-size:6.8px;color:var(--muted);margin-top:8px;line-height:1.4}}
      @media(max-width:800px){{.ledger-page{{padding:14px 10px 24px}}.ledger-title{{font-size:29px}}.ledger-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.ledger-section-title{{display:block}}.ledger-section-title span{{display:block;margin-top:3px}}.read-grid{{grid-template-columns:repeat(2,1fr)}}.ledger-edition{{font-size:7px}}}} @media(max-width:430px){{.ledger-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.ledger-card{{padding:8px 7px}}.ledger-ticker{{font-size:15px}}.health-inline{{font-size:7px}}.ledger-price{{font-size:19px}}.ledger-metrics{{grid-template-columns:repeat(2,1fr)}}.ledger-title{{font-size:26px}}}}
    </style>
    <section class="ledger-page" id="stocks">
      <header class="ledger-masthead"><div><h1 class="ledger-title">The Chai Ledger</h1><div class="ledger-deck">Entry levels, live prices, six-month targets — one glance tells you ENTER or WAIT.</div></div><div class="ledger-edition"><b>Edition:</b> Stocks Only · Action First<br><b>Updated:</b> {escape(now)}</div></header>
      <div class="tape"><span class="tape-label">ON THE TAPE</span><span><i class="tape-dot dot-green"></i><b>ENTER:</b> {escape(enter_text)}</span><span><i class="tape-dot dot-amber"></i><b>WAIT:</b> {escape(wait_text)}</span></div>
      {''.join(sections)}
      <section class="how-read"><h3>How to read this page</h3><div class="read-grid">
        <div class="read-item"><b>● ENTER</b>Price is at or below the conservative entry threshold. This is the only positive action state.</div>
        <div class="read-item"><b>● WAIT</b>Price is above the entry threshold. Do not chase; wait for the level.</div>
        <div class="read-item"><b>Health score</b>The bold score next to each ticker uses the regime-aware 40-parameter model. Grade: A+ 90–100, A 80–89, B 70–79, C 60–69, D 50–59, F below 50.</div>
        <div class="read-item"><b>Signal</b>STRONG BUY / BUY / HOLD / SELL follows the weighted score, hard-disqualifier rules, and data conviction. Missing data is N/A and renormalized—not guessed.</div>
        <div class="read-item"><b>Entry level</b>Curated levels are intentionally conservative. NVDA is now ENTER at or below $200. ORCL/PSTG use 2% below useful MA support.</div>
        <div class="read-item"><b>40-factor weights</b>Weights change with Risk-on/Neutral/Risk-off conditions and lifecycle: Hypergrowth, Compounder, Turnaround, or Cyclical-trough.</div>
        <div class="read-item"><b>GICS peer data</b>Official GICS peer-median fields remain N/A unless an authoritative peer feed is available; the bucket is renormalized exactly per the model.</div>
        <div class="read-item"><b>6-month target</b>Uses the current consensus mean analyst target as a planning proxy, not a guaranteed forecast.</div>
      </div><div class="footnote">The health model is a decision-support framework, not a guarantee of returns. Technical, ownership, filing, and peer-group fields can be unavailable or delayed in public market feeds.</div></section>
    </section>"""
