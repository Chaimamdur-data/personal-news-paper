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

TERM_HELP = {
    "hypergrowth": "Fast-growing company; bigger upside, usually bigger price swings.",
    "compounder": "Proven business that can steadily grow earnings and cash over many years.",
    "turnaround": "Business trying to improve after a slowdown; results need to prove the recovery.",
    "cyclical-trough": "Business tied to the economic cycle and near a weaker part of that cycle.",
    "cyclical": "Results rise and fall more with the economy or industry cycle.",
    "risk-on": "Investors are comfortable taking risk; growth stocks usually get more support.",
    "neutral": "Market signals are mixed; neither clearly bullish nor defensive.",
    "risk-off": "Investors are defensive; high-growth and cyclical stocks can face pressure.",
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
    """Four simple states around the planned entry threshold."""
    if not price or not level:
        return "REVIEW","Price or entry level unavailable","review"
    diff=(price-level)/level*100
    if diff < -8:
        return "REVIEW",f"{abs(diff):.1f}% below planned entry — check what changed before acting","review"
    if diff <= 0:
        return "ENTER",f"{abs(diff):.1f}% at/below planned entry","enter"
    if diff <= 3:
        return "NEAR ENTRY",f"Only {diff:.1f}% above planned entry","near"
    return "WAIT",f"{diff:.1f}% above planned entry","wait"

def _day_change(v):
    if v is None:return '<span class="ledger-muted">—</span>'
    cls="ledger-up" if v>=0 else "ledger-down";sym="▲" if v>=0 else "▼"
    return f'<span class="{cls}">{sym} {abs(v):.2f}%</span>'

def _signal_class(sig):
    return {"STRONG BUY":"sig-strong","BUY":"sig-buy","HOLD":"sig-hold","SELL":"sig-sell"}.get(sig,"sig-hold")

def _plain_english(s,basis):
    lifecycle=(s.get("lifecycle") or "").lower()
    market=(s.get("market_regime") or "").lower()
    lifecycle_text=TERM_HELP.get(lifecycle, "Company type used by the model to decide which factors matter most.")
    market_text=TERM_HELP.get(market, "Current overall market backdrop used by the model.")
    conviction=(s.get("conviction") or "—").lower()
    conviction_text={
        "high":"Most important model inputs agree and data coverage is strong.",
        "medium":"Some signals agree, but not enough for maximum confidence.",
        "low":"Signals conflict or important data is missing.",
    }.get(conviction,"Confidence level based on how much the model signals agree.")
    basis_text="How the planned entry price was chosen. " + ("It is a manually selected conservative price." if "Curated" in basis else "It is based on moving-average support or a fallback pullback level.")
    return lifecycle_text,market_text,conviction_text,basis_text

def _render_card(s):
    ticker=s["ticker"];meta=STOCK_META.get(ticker,{"reasons":[]});price=s.get("price") or 0;level,basis=_entry_level(s);action,detail,akey=_action(price,level);target=_target_6m(s);upside=s.get("upside_pct");score=s.get("health_score",0);grade=s.get("grade","?");signal=s.get("signal","HOLD");lifecycle=s.get("lifecycle","—");regime=s.get("weight_profile","—");reasons="".join(f"<li>{escape(r)}</li>" for r in meta["reasons"]);life_help,market_help,conv_help,basis_help=_plain_english(s,basis)
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
      <div class="term-inline"><b>{escape(lifecycle.title())}:</b> {escape(life_help)}</div>
      <div class="ledger-price-row"><div class="ledger-price">{_money(price)}</div><div class="ledger-day">{_day_change(s.get('day_change'))}</div></div>
      <div class="entry-row"><span>PLANNED ENTRY</span><strong>{_money(level)}</strong><small>{escape(detail)}</small></div>
      <div class="target-strip"><div><span>6-MO TARGET*</span><strong>{_money(target)}</strong></div><div class="target-right"><span>UPSIDE</span><strong>{('+'+str(upside)+'%') if upside is not None else '—'}</strong></div></div>
      <div class="ledger-metrics"><div><strong>{escape(s.get('market_regime','—'))}</strong><span>Market</span></div><div><strong>{escape(s.get('sector_health','—'))}</strong><span>Sector</span></div><div><strong>{escape(s.get('conviction','—'))}</strong><span>Conviction</span></div><div><strong>{escape(basis)}</strong><span>Entry basis</span></div></div>
      <div class="plain-box"><b>Plain English</b><span><strong>Market:</strong> {escape(market_help)}</span><span><strong>Conviction:</strong> {escape(conv_help)}</span><span><strong>Entry basis:</strong> {escape(basis_help)}</span><span><strong>40-factor profile:</strong> the model changes factor weights for this company type and market environment. “N/A” means data was unavailable, not guessed.</span></div>
      <div class="ledger-why">WHY IT STAYS ON THE LIST</div><ul class="ledger-reasons">{reasons}</ul>
    </article>"""

def render_stock_section(stocks:list)->str:
    if not stocks:return ""
    by={s.get("ticker"):s for s in stocks};ordered=[]
    for c in CATEGORY_DEFS:
        for t in c["tickers"]:
            if t in by:ordered.append(by[t])
    states={"ENTER":[],"NEAR ENTRY":[],"WAIT":[],"REVIEW":[]}
    for s in ordered:
        states[_action(s.get("price") or 0,_entry_level(s)[0])[0]].append(s["ticker"])
    sections=[]
    for c in CATEGORY_DEFS:
        items=[by[t] for t in c["tickers"] if t in by]
        if not items:continue
        sections.append(f"""<section class="ledger-section"><div class="ledger-section-title"><h2>{escape(c['name'])}</h2><span>{escape(c['thesis'])}</span></div><div class="ledger-grid">{''.join(_render_card(s) for s in items)}</div></section>""")
    now=datetime.now().strftime("%b %d, %Y · %I:%M %p")
    def names(k):return " · ".join(states[k]) if states[k] else "none"
    return f"""
    <style>
      :root{{--paper:#f3ede2;--ink:#171713;--muted:#69645b;--rule:#25241f;--green:#1f6b49;--amber:#a56a16;--red:#a54336;--blue:#315f8c;--bar:#15211c}}
      body{{background:#e9e4da!important}} .ledger-page{{max-width:1180px;margin:0 auto;background:var(--paper);color:var(--ink);font-family:Georgia,'Times New Roman',serif;padding:22px 28px 34px}}
      .ledger-masthead{{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;border-bottom:2px solid var(--rule);padding-bottom:12px}} .ledger-title{{font-size:40px;line-height:.95;font-weight:700;letter-spacing:-1px;margin:0}} .ledger-deck{{font-size:11px;font-style:italic;color:var(--muted);margin-top:6px;max-width:720px}} .ledger-edition{{font-family:Arial,sans-serif;text-align:right;font-size:9px;line-height:1.55;white-space:nowrap}}
      .briefing-box{{border-bottom:1px solid var(--rule);padding:9px 0 10px;font-family:Arial,sans-serif;font-size:8px;line-height:1.45}} .briefing-box b{{font-family:Georgia,serif;font-size:10px}} .briefing-legend{{display:flex;gap:12px;flex-wrap:wrap;margin-top:5px}} .briefing-legend span{{white-space:nowrap}} .b-enter{{color:var(--green)}} .b-near{{color:var(--blue)}} .b-wait{{color:var(--amber)}} .b-review{{color:var(--red)}}
      .tape{{display:flex;align-items:center;gap:10px;flex-wrap:wrap;border-bottom:1px solid var(--rule);padding:8px 0 7px;font-family:Arial,sans-serif;font-size:8px;text-transform:uppercase}} .tape-label{{font-family:Georgia,serif;font-style:italic;font-weight:700}}
      .ledger-section{{margin-top:25px}} .ledger-section-title{{display:flex;align-items:baseline;gap:10px;border-bottom:2px solid var(--rule);padding-bottom:5px}} .ledger-section-title h2{{font-size:21px;margin:0}} .ledger-section-title span{{font-size:9px;font-style:italic;color:var(--muted)}} .ledger-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));border-left:1px solid var(--rule)}}
      .ledger-card{{padding:10px 12px 12px;border-right:1px solid var(--rule);border-bottom:1px solid #a49d90;min-width:0}} .ledger-card.action-enter{{border-left:3px solid var(--green);background:rgba(255,255,255,.13)}} .ledger-card.action-near{{border-left:3px solid var(--blue)}} .ledger-card.action-review{{border-left:3px solid var(--red)}} .ledger-card-head{{display:flex;justify-content:space-between;gap:8px;align-items:flex-start}} .ticker-line{{display:flex;align-items:baseline;gap:7px;flex-wrap:wrap}} .ledger-ticker{{font-size:17px;font-weight:700;line-height:1}} .health-inline{{font-family:Arial,sans-serif;font-size:8.5px;letter-spacing:.1px}} .sig-strong,.sig-buy{{color:var(--green)}} .sig-hold{{color:var(--amber)}} .sig-sell{{color:var(--red)}}
      .ledger-company{{font-family:Arial,sans-serif;font-size:8px;color:var(--muted);margin:2px 0 4px;max-width:190px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}} .ledger-lifecycle{{display:inline-block;border:1px solid var(--rule);padding:1px 4px;font-family:Arial,sans-serif;font-size:6.7px}} .term-inline{{font-family:Arial,sans-serif;font-size:7px;line-height:1.3;color:#514c44;margin-top:5px}} .ledger-action{{font-family:Arial,sans-serif;font-size:8px;font-weight:800;letter-spacing:.5px;white-space:nowrap}} .action-label-enter{{color:var(--green)}} .action-label-near{{color:var(--blue)}} .action-label-wait{{color:var(--amber)}} .action-label-review{{color:var(--red)}}
      .ledger-price-row{{display:flex;align-items:baseline;gap:8px;margin-top:8px}} .ledger-price{{font-family:Arial,sans-serif;font-size:24px;font-weight:700;letter-spacing:-.5px}} .ledger-day{{font-family:Arial,sans-serif;font-size:8px}} .ledger-up{{color:var(--green);font-weight:700}} .ledger-down{{color:var(--red);font-weight:700}}
      .entry-row{{display:grid;grid-template-columns:auto auto;align-items:baseline;gap:3px 7px;border-top:1px solid #756f65;border-bottom:1px solid #756f65;padding:5px 0;margin:7px 0;font-family:Arial,sans-serif}} .entry-row span{{font-size:6.5px;letter-spacing:.5px}} .entry-row strong{{font-size:12px;text-align:right}} .entry-row small{{grid-column:1/-1;font-size:7px;color:var(--muted)}}
      .target-strip{{display:grid;grid-template-columns:1fr 1fr;background:var(--bar);color:#fff;padding:7px 8px;font-family:Arial,sans-serif}} .target-strip span{{display:block;font-size:6.4px;color:#c9d1cd;letter-spacing:.4px}} .target-strip strong{{display:block;font-size:12px;margin-top:2px}} .target-right{{text-align:right}} .target-right strong{{color:#71d39a}}
      .ledger-metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:5px;margin:8px 0 6px;font-family:Arial,sans-serif}} .ledger-metrics strong{{display:block;font-size:7.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}} .ledger-metrics span{{font-size:6.2px;color:var(--muted)}} .plain-box{{font-family:Arial,sans-serif;font-size:6.8px;line-height:1.35;color:#49453e;border-top:1px solid #c1baae;border-bottom:1px solid #c1baae;padding:5px 0;display:grid;gap:2px}} .plain-box>b{{font-family:Georgia,serif;font-size:8px;color:var(--ink)}} .ledger-why{{font-family:Arial,sans-serif;font-size:6.8px;font-weight:700;margin-top:6px}} .ledger-reasons{{font-family:Arial,sans-serif;font-size:7.2px;line-height:1.35;padding-left:12px;margin:3px 0 0}}
      .how-read{{border:1.5px solid var(--rule);margin-top:28px;padding:12px 14px}} .how-read h3{{font-size:13px;margin:0 0 8px}} .read-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}} .read-item{{font-family:Arial,sans-serif;font-size:7px;line-height:1.4}} .read-item b{{display:block;font-family:Georgia,serif;font-size:8px;margin-bottom:2px}} .footnote{{font-family:Arial,sans-serif;font-size:6.8px;color:var(--muted);margin-top:8px;line-height:1.4}}
      @media(max-width:800px){{.ledger-page{{padding:14px 10px 24px}}.ledger-title{{font-size:29px}}.ledger-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.ledger-section-title{{display:block}}.ledger-section-title span{{display:block;margin-top:3px}}.read-grid{{grid-template-columns:repeat(2,1fr)}}.ledger-edition{{font-size:7px}}}} @media(max-width:430px){{.ledger-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.ledger-card{{padding:8px 7px}}.ledger-ticker{{font-size:15px}}.health-inline{{font-size:7px}}.ledger-price{{font-size:19px}}.ledger-metrics{{grid-template-columns:repeat(2,1fr)}}.ledger-title{{font-size:26px}}}}
    </style>
    <section class="ledger-page" id="stocks">
      <header class="ledger-masthead"><div><h1 class="ledger-title">The Chai Ledger</h1><div class="ledger-deck">Entry levels, live prices and six-month targets — with every model term translated into plain English.</div></div><div class="ledger-edition"><b>Edition:</b> Stocks Only · Action First<br><b>Updated:</b> {escape(now)}</div></header>
      <section class="briefing-box"><b>30-second briefing</b><div>This dashboard does not use only ENTER and WAIT anymore. It separates stocks that are close to your planned price from stocks that need more investigation.</div><div class="briefing-legend"><span class="b-enter"><b>ENTER</b> = at or slightly below planned price</span><span class="b-near"><b>NEAR ENTRY</b> = within 3% above it</span><span class="b-wait"><b>WAIT</b> = more than 3% above it</span><span class="b-review"><b>REVIEW</b> = over 8% below it or data missing; check why before buying</span></div></section>
      <div class="tape"><span class="tape-label">ON THE TAPE</span><span class="b-enter"><b>ENTER:</b> {escape(names('ENTER'))}</span><span class="b-near"><b>NEAR:</b> {escape(names('NEAR ENTRY'))}</span><span class="b-wait"><b>WAIT:</b> {escape(names('WAIT'))}</span><span class="b-review"><b>REVIEW:</b> {escape(names('REVIEW'))}</span></div>
      {''.join(sections)}
      <section class="how-read"><h3>Simple glossary — what the words mean</h3><div class="read-grid">
        <div class="read-item"><b>Compounder</b>A proven company that steadily grows profits/cash for years. Think “quality that keeps building on itself.”</div>
        <div class="read-item"><b>Hypergrowth</b>A company growing unusually fast. Bigger opportunity, but usually more volatility and valuation risk.</div>
        <div class="read-item"><b>Turnaround</b>A company recovering from slower growth or business problems. We want evidence the recovery is actually working.</div>
        <div class="read-item"><b>Cyclical / Cyclical-trough</b>A business whose results move with the economy or industry cycle. “Trough” means near a weaker point in that cycle.</div>
        <div class="read-item"><b>Risk-on / Neutral / Risk-off</b>Risk-on = investors favor growth and risk. Neutral = mixed signals. Risk-off = investors favor safety.</div>
        <div class="read-item"><b>Conviction</b>How strongly the available data agrees. High = many important signals line up; Low = conflicting or missing signals.</div>
        <div class="read-item"><b>Entry basis</b>Why that entry price exists: a manually chosen conservative level, moving-average support, or fallback pullback calculation.</div>
        <div class="read-item"><b>40-factor profile</b>The model looks at many valuation, growth, quality, technical and sentiment factors. Their importance changes by company type and market environment.</div>
        <div class="read-item"><b>Health score / Grade</b>A summary score from the model. Higher generally means stronger fundamentals/market setup; it is not a guarantee of future returns.</div>
        <div class="read-item"><b>Signal</b>STRONG BUY / BUY / HOLD / SELL is the model's broad attractiveness score. It is separate from whether today's price is at your planned entry.</div>
        <div class="read-item"><b>6-month target / Upside</b>The current analyst consensus target and the percentage difference from today's price. It is an estimate, not a promised return.</div>
        <div class="read-item"><b>N/A</b>The data source did not provide that metric. The model leaves it missing rather than inventing a number.</div>
      </div><div class="footnote">Action state answers “how close is price to my planned entry?” Signal answers “how attractive does the stock look overall?” Those are intentionally different questions.</div></section>
    </section>"""