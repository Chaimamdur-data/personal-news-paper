"""Dark entry-watchlist renderer for The Chai Ledger Markets tab."""
from __future__ import annotations

import json
from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

CATEGORY_DEFS = [
    {"name":"AI Compute & Semis","tickers":["MU","NVDA","AVGO"],"thesis":"AI compute, memory and networking"},
    {"name":"Mega-cap Platforms","tickers":["GOOGL","AMZN","MSFT","META","AAPL","ORCL"],"thesis":"Cloud, platforms and enterprise AI"},
    {"name":"Data Infrastructure","tickers":["PSTG","SNOW","CRM","WDAY"],"thesis":"Data, storage and enterprise software"},
    {"name":"Payments & Data Moats","tickers":["V","MA","SPGI"],"thesis":"Networks and information toll roads"},
    {"name":"Travel & Cyclicals","tickers":["DAL","UAL","EXPE"],"thesis":"Cyclical travel and operating leverage"},
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
    "MU":"AI-memory demand and memory-cycle leverage keep Micron on the list.",
    "NVDA":"AI accelerator leadership and the CUDA ecosystem remain the core thesis.",
    "AVGO":"AI networking, custom silicon and recurring software cash flow support the thesis.",
    "GOOGL":"Search cash flow plus Cloud and AI optionality make Alphabet a durable platform name.",
    "AMZN":"AWS, advertising and retail margin expansion are the key long-term engines.",
    "MSFT":"Azure, enterprise distribution and recurring software revenue support durable compounding.",
    "META":"AI-driven ad efficiency and strong cash generation support the core thesis.",
    "AAPL":"A sticky ecosystem and huge installed base support durable cash generation.",
    "ORCL":"OCI, databases and AI infrastructure demand are the main reasons Oracle stays on the list.",
    "PSTG":"Flash storage, subscriptions and AI-data workloads are the core Pure Storage thesis.",
    "SNOW":"Cloud data workloads and AI use cases provide upside if consumption growth reaccelerates.",
    "CRM":"Free-cash-flow improvement and AI monetization are the key turnaround tests.",
    "WDAY":"Sticky HR/finance subscriptions and capital returns support the recovery thesis.",
    "V":"A global digital-payments network with strong margins creates a durable moat.",
    "MA":"Global payment rails and cross-border economics support long-term compounding.",
    "SPGI":"Ratings, indices and market data create recurring information economics.",
    "DAL":"Premium travel and loyalty economics can amplify earnings when the cycle is healthy.",
    "UAL":"International network strength and capacity discipline drive the cyclical thesis.",
    "EXPE":"Scale, B2B growth and Vrbo provide multiple travel-platform growth levers.",
}

def _entry_level(s):
    curated = ENTRY_LEVELS.get(s["ticker"])
    if curated:
        return float(curated), "Curated planned entry"
    price = s.get("price") or 0
    anchors = [x for x in (s.get("ma50"), s.get("ma200")) if x and x > 0]
    if anchors:
        below = [x for x in anchors if not price or x <= price]
        anchor = max(below) if below else min(anchors)
        return round(anchor * .98, 2), "2% below moving-average support"
    if price:
        return round(price * .92, 2), "8% pullback fallback"
    return None, "Not set"

def _state(price, entry):
    if not price or not entry:
        return "CHECK DATA", "check"
    return ("ENTER", "enter") if price <= entry else ("WAIT", "wait")

def _peer_pulse(items):
    vals = [(x["ticker"], x.get("return_20d")) for x in items if x.get("return_20d") is not None]
    if len(vals) < 2:
        return "Not enough recent peer data."
    vals.sort(key=lambda x: x[1], reverse=True)
    best, worst = vals[0], vals[-1]
    if best[0] == worst[0]:
        return f"{best[0]} {best[1]:+.1f}% over ~4 weeks."
    return f"{best[0]} leads at {best[1]:+.1f}%; {worst[0]} trails at {worst[1]:+.1f}% over ~4 weeks."

def _payload(stocks):
    by = {s.get("ticker"): s for s in stocks}
    payload = []
    for cat in CATEGORY_DEFS:
        items = [by[t] for t in cat["tickers"] if t in by]
        pulse = _peer_pulse(items)
        for s in items:
            entry, basis = _entry_level(s)
            price = s.get("price") or None
            state, state_key = _state(price, entry)
            target = s.get("target_mean")
            upside = s.get("upside_pct")
            payload.append({
                "ticker": s["ticker"],
                "company": s.get("name") or s["ticker"],
                "category": cat["name"],
                "category_thesis": cat["thesis"],
                "why": STOCK_META.get(s["ticker"], "Watchlist thesis not yet written."),
                "price": price,
                "chg": s.get("day_change"),
                "entry": entry,
                "entry_basis": basis,
                "state": state,
                "state_key": state_key,
                "target": target,
                "target_horizon": "6M proxy" if target else None,
                "target_upside": upside,
                "target_note": "Model/analyst target proxy; not validated.",
                "score": s.get("health_score"),
                "grade": s.get("grade"),
                "signal": s.get("signal"),
                "conviction": s.get("conviction"),
                "type": s.get("lifecycle"),
                "analyst_rec": s.get("analyst_rec"),
                "analyst_count": s.get("analyst_count", 0),
                "analyst_breakdown": s.get("analyst_breakdown") or {},
                "industry_outlook": s.get("recent_sector_outlook") or {},
                "peer_pulse": pulse,
                "stop": None,
                "size": None,
                "local_only": False,
            })
    return payload

def render_stock_section(stocks:list)->str:
    if not stocks:
        return ""
    data = _payload(stocks)
    now = datetime.now(ZoneInfo("America/Los_Angeles")).strftime("%b %d, %Y · %I:%M:%S %p PT")
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    categories = json.dumps([c["name"] for c in CATEGORY_DEFS])
    html = """
<style>
@font-face{{font-family:Geist;src:local("Geist"),local("Geist Regular");font-display:swap}}
@font-face{{font-family:"Geist Mono";src:local("Geist Mono"),local("GeistMono");font-display:swap}}
:root{{--ew-bg:#0e1116;--ew-surface:#161a21;--ew-surface2:#1d222b;--ew-line:#2b323e;--ew-text:#f2f5f7;--ew-muted:#8f9baa;--ew-green:#34d27b;--ew-red:#ff6a4d;--ew-amber:#f4b740;--ew-blue:#5fa8ff;--ew-radius:22px}}
.entry-watchlist{{min-height:100vh;background:
radial-gradient(900px 480px at 18% -8%,rgba(52,210,123,.12),transparent 58%),
radial-gradient(760px 420px at 86% 0%,rgba(95,168,255,.10),transparent 58%),
var(--ew-bg);color:var(--ew-text);font-family:Geist,Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;padding:24px 22px 46px}}
.ew-shell{{max-width:1220px;margin:0 auto}}
.ew-top{{position:sticky;top:42px;z-index:60;margin:-2px 0 24px;padding:14px 16px;border:1px solid rgba(255,255,255,.08);background:rgba(22,26,33,.91);backdrop-filter:blur(18px);border-radius:20px;box-shadow:0 18px 50px rgba(0,0,0,.24);display:grid;grid-template-columns:1fr auto;gap:14px;align-items:center}}
.ew-brand{{display:flex;align-items:center;gap:12px;min-width:0}}.ew-logo{{width:38px;height:38px;border-radius:13px;background:linear-gradient(145deg,#2fe17f,#238c5a);box-shadow:0 0 24px rgba(52,210,123,.25);position:relative;flex:0 0 auto}}.ew-logo:before{{content:"";position:absolute;inset:9px;border:2px solid #08150e;border-radius:50%;box-shadow:inset 0 0 0 4px rgba(255,255,255,.18)}}.ew-title{{font-size:18px;font-weight:760;letter-spacing:-.25px}}.ew-subtitle{{font:500 11px/1.35 "Geist Mono",ui-monospace,monospace;color:var(--ew-muted);margin-top:3px;font-variant-numeric:tabular-nums}}
.ew-actions{{display:flex;gap:9px;align-items:center}}.ew-btn{{border:1px solid var(--ew-line);border-radius:999px;padding:10px 14px;background:var(--ew-surface2);color:var(--ew-text);font:700 12px/1 Geist,ui-sans-serif,sans-serif;cursor:pointer;display:inline-flex;align-items:center;gap:8px;transition:.18s ease}}.ew-btn:hover{{transform:translateY(-1px);border-color:#465062}}.ew-btn.primary{{background:var(--ew-green);color:#07130c;border-color:transparent}}.ew-btn .spin{{display:inline-block}}.ew-btn.loading .spin{{animation:ewspin .8s linear infinite}}@keyframes ewspin{{to{{transform:rotate(360deg)}}}}
.ew-summary{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:26px}}.ew-summary-card{{border:1px solid var(--ew-line);background:linear-gradient(180deg,rgba(255,255,255,.025),rgba(255,255,255,.01));border-radius:18px;padding:13px 15px}}.ew-summary-label{{font-size:10px;color:var(--ew-muted);text-transform:uppercase;letter-spacing:.7px}}.ew-summary-value{{font:750 22px/1.2 "Geist Mono",ui-monospace,monospace;margin-top:5px;font-variant-numeric:tabular-nums}}
.ew-section{{margin:28px 0 34px}}.ew-section-head{{display:flex;align-items:end;justify-content:space-between;gap:14px;margin-bottom:12px}}.ew-section-head h2{{font-size:15px;margin:0;letter-spacing:-.1px}}.ew-section-head span{{font-size:11px;color:var(--ew-muted)}}.ew-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:13px}}
.ew-card{{position:relative;border:1px solid var(--ew-line);background:linear-gradient(180deg,var(--ew-surface),#13171d);border-radius:var(--ew-radius);padding:16px;min-width:0;transition:border-color .18s ease,transform .18s ease,box-shadow .18s ease}}.ew-card:hover{{transform:translateY(-2px);border-color:#3c4656}}.ew-card.enter{{border-color:rgba(52,210,123,.62);box-shadow:0 0 0 1px rgba(52,210,123,.10),0 14px 38px rgba(22,112,67,.14)}}.ew-card.check{{border-color:rgba(244,183,64,.45)}}
.ew-card-top{{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}}.ew-ticker-row{{display:flex;gap:8px;align-items:center;flex-wrap:wrap}}.ew-ticker{{font-size:18px;font-weight:820;letter-spacing:-.3px}}.ew-score{{font:700 10px/1 "Geist Mono",ui-monospace,monospace;padding:5px 7px;border:1px solid var(--ew-line);border-radius:999px;color:#cbd4dc;font-variant-numeric:tabular-nums}}.ew-company{{font-size:11px;color:var(--ew-muted);margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:220px}}
.ew-info{{width:29px;height:29px;border-radius:50%;border:1px solid var(--ew-line);background:var(--ew-surface2);color:#cdd5dd;font:800 12px/1 Georgia,serif;cursor:pointer;position:relative;flex:0 0 auto}}.ew-info.warn:after{{content:"";position:absolute;width:7px;height:7px;border-radius:50%;background:var(--ew-amber);right:-1px;top:-1px;box-shadow:0 0 0 2px var(--ew-surface)}}
.ew-price-row{{display:flex;align-items:baseline;justify-content:space-between;gap:12px;margin:18px 0 12px}}.ew-price{{font:760 29px/1 "Geist Mono",ui-monospace,monospace;letter-spacing:-1px;font-variant-numeric:tabular-nums}}.ew-chg{{font:700 11px/1 "Geist Mono",ui-monospace,monospace;font-variant-numeric:tabular-nums}}.up{{color:var(--ew-green)}}.down{{color:var(--ew-red)}}.muted{{color:var(--ew-muted)}}
.ew-state{{font-size:10px;font-weight:820;letter-spacing:.65px;text-transform:uppercase;border-radius:999px;padding:6px 9px;white-space:nowrap}}.ew-state.enter{{background:rgba(52,210,123,.12);color:var(--ew-green)}}.ew-state.wait{{background:rgba(244,183,64,.11);color:var(--ew-amber)}}.ew-state.check{{background:rgba(244,183,64,.11);color:var(--ew-amber)}}
.ew-bar-wrap{{margin-top:14px}}.ew-bar-labels{{display:flex;justify-content:space-between;font:600 9px/1.2 "Geist Mono",ui-monospace,monospace;color:var(--ew-muted);font-variant-numeric:tabular-nums}}.ew-bar{{position:relative;height:8px;border-radius:999px;background:linear-gradient(90deg,rgba(52,210,123,.26) 0 50%,rgba(244,183,64,.16) 50% 100%);margin:7px 0 6px;overflow:visible}}.ew-entry-mark{{position:absolute;left:50%;top:-4px;width:2px;height:16px;background:#d9e2e8;border-radius:2px}}.ew-price-mark{{position:absolute;top:50%;transform:translate(-50%,-50%);width:12px;height:12px;border-radius:50%;background:var(--ew-text);border:3px solid var(--ew-bg);box-shadow:0 0 0 1px #6d7784}}
.ew-mini{{display:flex;justify-content:space-between;gap:10px;margin-top:13px;padding-top:11px;border-top:1px solid rgba(255,255,255,.06)}}.ew-mini div{{min-width:0}}.ew-mini label{{display:block;color:var(--ew-muted);font-size:9px;margin-bottom:4px}}.ew-mini strong{{display:block;font:700 12px/1.2 "Geist Mono",ui-monospace,monospace;font-variant-numeric:tabular-nums;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}.not-set{{color:var(--ew-amber)!important}}
.ew-pop{{position:fixed;z-index:1000;width:min(390px,calc(100vw - 24px));max-height:min(680px,calc(100vh - 24px));overflow:auto;padding:17px;border:1px solid #384252;border-radius:20px;background:rgba(22,26,33,.98);box-shadow:0 28px 80px rgba(0,0,0,.52);display:none}}.ew-pop.open{{display:block}}.ew-pop-head{{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;border-bottom:1px solid var(--ew-line);padding-bottom:12px;margin-bottom:13px}}.ew-pop-title{{font-size:17px;font-weight:800}}.ew-pop-company{{font-size:11px;color:var(--ew-muted);margin-top:3px}}.ew-pop-close{{border:0;background:transparent;color:var(--ew-muted);font-size:18px;cursor:pointer}}.ew-pop-why{{font-size:12px;line-height:1.45;color:#dbe2e7;margin-bottom:14px}}.ew-detail-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}}.ew-detail{{background:var(--ew-surface2);border:1px solid rgba(255,255,255,.05);border-radius:12px;padding:10px}}.ew-detail label{{display:block;color:var(--ew-muted);font-size:9px;margin-bottom:5px}}.ew-detail strong{{font:700 12px/1.25 "Geist Mono",ui-monospace,monospace;font-variant-numeric:tabular-nums}}.ew-pop-section{{border-top:1px solid var(--ew-line);margin-top:13px;padding-top:12px}}.ew-pop-section h4{{font-size:10px;text-transform:uppercase;letter-spacing:.6px;color:var(--ew-muted);margin:0 0 8px}}.ew-ratings{{display:flex;flex-wrap:wrap;gap:6px}}.ew-chip{{font:650 10px/1 "Geist Mono",ui-monospace,monospace;padding:6px 7px;border:1px solid var(--ew-line);border-radius:999px;color:#d1dae2}}.ew-outlook{{font-size:11px;line-height:1.45;color:#d5dde4}}.ew-warning{{margin-top:11px;padding:9px 10px;border-radius:11px;background:rgba(244,183,64,.08);border:1px solid rgba(244,183,64,.22);font-size:10px;color:#d8c89f}}.ew-remove{{width:100%;margin-top:13px;border:1px solid rgba(255,106,77,.36);background:rgba(255,106,77,.08);color:#ff9a86;border-radius:999px;padding:10px;font-weight:750;cursor:pointer}}
.ew-modal-backdrop{{position:fixed;inset:0;z-index:900;background:rgba(0,0,0,.66);display:none;align-items:center;justify-content:center;padding:16px}}.ew-modal-backdrop.open{{display:flex}}.ew-modal{{width:min(520px,100%);background:var(--ew-surface);border:1px solid #3a4351;border-radius:22px;padding:20px;box-shadow:0 28px 90px rgba(0,0,0,.55)}}.ew-modal-head{{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}}.ew-modal-head h3{{margin:0;font-size:18px}}.ew-form{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}.ew-field.full{{grid-column:1/-1}}.ew-field label{{display:block;font-size:10px;color:var(--ew-muted);margin-bottom:6px}}.ew-input{{width:100%;background:#10141a;color:var(--ew-text);border:1px solid var(--ew-line);border-radius:12px;padding:11px 12px;font:600 12px/1.2 Geist,ui-sans-serif,sans-serif;outline:none}}.ew-input:focus{{border-color:#4c8f70;box-shadow:0 0 0 3px rgba(52,210,123,.08)}}.ew-error{{min-height:14px;color:#ff8c76;font-size:9px;margin-top:4px}}.ew-modal-actions{{display:flex;justify-content:flex-end;gap:8px;margin-top:14px}}
.ew-toast-stack{{position:fixed;right:18px;bottom:18px;z-index:1200;display:grid;gap:8px}}.ew-toast{{min-width:250px;max-width:360px;background:#1c222b;border:1px solid #384251;border-radius:13px;padding:11px 13px;box-shadow:0 16px 50px rgba(0,0,0,.4);font-size:11px;color:#e6ebef}}.ew-toast.good{{border-color:rgba(52,210,123,.45)}}.ew-toast.bad{{border-color:rgba(255,106,77,.45)}}.ew-toast.warn{{border-color:rgba(244,183,64,.45)}}
.ew-footer{{border-top:1px solid var(--ew-line);margin-top:34px;padding-top:22px;color:#a8b2bd}}.ew-footer strong{{color:#eef2f5}}.ew-footer p{{font-size:11px;line-height:1.55;margin:7px 0}}.ew-score-explain{{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin-top:15px}}.ew-score-box{{border:1px solid var(--ew-line);border-radius:14px;background:rgba(255,255,255,.018);padding:11px}}.ew-score-box b{{display:block;color:#edf2f5;font-size:10px;margin-bottom:4px}}.ew-score-box span{{font-size:9.5px;line-height:1.42;color:var(--ew-muted)}}
@media(max-width:900px){{.ew-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.ew-score-explain{{grid-template-columns:repeat(2,1fr)}}}}
@media(max-width:680px){{.entry-watchlist{{padding:14px 10px 34px}}.ew-top{{position:relative;top:auto;grid-template-columns:1fr;border-radius:18px}}.ew-actions{{width:100%;display:grid;grid-template-columns:1fr 1fr}}.ew-btn{{justify-content:center}}.ew-summary{{grid-template-columns:1fr 1fr 1fr}}.ew-grid{{grid-template-columns:1fr}}.ew-card{{border-radius:19px}}.ew-price-row{{margin-bottom:8px}}.ew-bar-wrap{{margin-top:16px;padding-top:12px;border-top:1px solid rgba(255,255,255,.06)}}.ew-form{{grid-template-columns:1fr}}.ew-field.full{{grid-column:auto}}}}
@media(max-width:430px){{.ew-summary{{grid-template-columns:1fr}}.ew-score-explain{{grid-template-columns:1fr}}}}
@media(prefers-reduced-motion:reduce){{*,*:before,*:after{{scroll-behavior:auto!important;animation-duration:.01ms!important;transition-duration:.01ms!important}}}}
</style>

<section class="entry-watchlist" id="stocks">
  <div class="ew-shell">
    <header class="ew-top">
      <div class="ew-brand">
        <div class="ew-logo" aria-hidden="true"></div>
        <div><div class="ew-title">Entry Watchlist</div><div class="ew-subtitle">Prices: <span id="ew-price-time">__NOW__</span></div></div>
      </div>
      <div class="ew-actions">
        <button class="ew-btn primary" id="ew-refresh"><span class="spin">↻</span> Refresh</button>
        <button class="ew-btn" id="ew-add">＋ Add stock</button>
      </div>
    </header>

    <div class="ew-summary" id="ew-summary"></div>
    <div id="ew-sections"></div>

    <footer class="ew-footer">
      <strong>Not advice.</strong>
      <p>The entry bar is centered on your planned entry. Green is at/below the plan; amber is above it. <b>ENTER</b> means current price is at or below your planned entry, <b>WAIT</b> means it is above, and <b>CHECK DATA</b> means price or entry is missing. The bar is a price-distance visual, not a prediction.</p>
      <p>Targets shown here are model/analyst outputs or user-entered targets. They are <b>not validated</b> and should not be treated as facts or guaranteed returns.</p>
      <div class="ew-score-explain">
        <div class="ew-score-box"><b>1 · Market setup</b><span>The model first checks whether markets are risk-on, neutral or risk-off, plus whether the sector is expanding, stable or contracting.</span></div>
        <div class="ew-score-box"><b>2 · Company type</b><span>It classifies the stock as hypergrowth, compounder, turnaround or cyclical so the score can weight the right things.</span></div>
        <div class="ew-score-box"><b>3 · 40 checks</b><span>Valuation, growth, profitability, analyst sentiment, technicals, macro/sector and catalysts/risks are scored from 0–10.</span></div>
        <div class="ew-score-box"><b>4 · Missing data</b><span>Missing inputs are N/A, never guessed. The remaining available inputs are reweighted inside that bucket.</span></div>
        <div class="ew-score-box"><b>5 · Dynamic weights</b><span>Growth matters more in risk-on/hypergrowth setups; valuation and balance sheet matter more in risk-off conditions.</span></div>
        <div class="ew-score-box"><b>6 · Hard checks</b><span>Major cash-flow, debt, filing or multi-quarter revenue problems can cap the recommendation even when the raw score is high.</span></div>
        <div class="ew-score-box"><b>7 · Score + grade</b><span>The weighted result becomes a 0–100 score and A+ through F grade. Higher means the available evidence is stronger.</span></div>
        <div class="ew-score-box"><b>8 · Signal ≠ entry</b><span>The model signal rates the company/setup. ENTER or WAIT only compares today's price with your planned entry. Keep those two decisions separate.</span></div>
      </div>
    </footer>
  </div>
</section>

<div class="ew-pop" id="ew-pop" role="dialog" aria-modal="false"></div>
<div class="ew-modal-backdrop" id="ew-modal-bg">
  <div class="ew-modal" role="dialog" aria-modal="true" aria-labelledby="ew-modal-title">
    <div class="ew-modal-head"><h3 id="ew-modal-title">Add or update stock</h3><button class="ew-pop-close" id="ew-modal-x" aria-label="Close">×</button></div>
    <form id="ew-form" novalidate>
      <div class="ew-form">
        <div class="ew-field"><label>Ticker *</label><input class="ew-input" id="f-ticker" autocomplete="off" placeholder="MU"><div class="ew-error" id="e-ticker"></div></div>
        <div class="ew-field"><label>Planned entry *</label><input class="ew-input" id="f-entry" inputmode="decimal" placeholder="200"><div class="ew-error" id="e-entry"></div></div>
        <div class="ew-field full"><label>Company</label><input class="ew-input" id="f-company" placeholder="Optional"></div>
        <div class="ew-field"><label>Current price</label><input class="ew-input" id="f-price" inputmode="decimal" placeholder="Optional"><div class="ew-error" id="e-price"></div></div>
        <div class="ew-field"><label>Target price</label><input class="ew-input" id="f-target" inputmode="decimal" placeholder="Optional"><div class="ew-error" id="e-target"></div></div>
        <div class="ew-field full"><label>Target horizon</label><select class="ew-input" id="f-horizon"><option value="">Not set</option><option>1M</option><option>3M</option><option>6M</option><option>12M</option></select></div>
      </div>
      <div class="ew-modal-actions"><button type="button" class="ew-btn" id="ew-cancel">Cancel</button><button class="ew-btn primary" type="submit">Save stock</button></div>
    </form>
  </div>
</div>
<div class="ew-toast-stack" id="ew-toasts"></div>

<script>
(() => {{
  const BASE = __PAYLOAD__;
  const CATEGORY_ORDER = __CATEGORIES__;
  const PRICE_URL = window.CHAI_PRICE_URL || './prices.json';
  const LS = {{add:'chai-ew-add-v1',removed:'chai-ew-removed-v1',overrides:'chai-ew-overrides-v1'}};
  const $ = s => document.querySelector(s);
  const fmt = n => (Number.isFinite(Number(n)) ? '$'+Number(n).toLocaleString(undefined,{{minimumFractionDigits:2,maximumFractionDigits:2}}) : '—');
  const pct = n => Number.isFinite(Number(n)) ? (Number(n)>=0?'+':'')+Number(n).toFixed(1)+'%' : '—';
  const safeParse = (k,fallback) => {{try{{return JSON.parse(localStorage.getItem(k)||'')||fallback}}catch(e){{return fallback}}}};
  const safeSet = (k,v) => {{try{{localStorage.setItem(k,JSON.stringify(v));return true}}catch(e){{toast('Could not save locally: '+e.message,'bad');return false}}}};
  let additions=safeParse(LS.add,{{}}), removed=new Set(safeParse(LS.removed,[])), overrides=safeParse(LS.overrides,{{}});
  let active=null, hoverTimer=null;

  function mergedData(){{
    const base=BASE.filter(x=>!removed.has(x.ticker)).map(x=>Object.assign({{}},x,overrides[x.ticker]||{{}}));
    const locals=Object.values(additions).filter(x=>!removed.has(x.ticker));
    const seen=new Set(base.map(x=>x.ticker));
    locals.forEach(x=>{{if(!seen.has(x.ticker))base.push(x)}});
    return base;
  }}
  function derive(s){{
    const p=Number(s.price),e=Number(s.entry);
    if(!Number.isFinite(p)||p<=0||!Number.isFinite(e)||e<=0)return ['CHECK DATA','check'];
    return p<=e?['ENTER','enter']:['WAIT','wait'];
  }}
  function barPos(s){{
    const p=Number(s.price),e=Number(s.entry); if(!p||!e)return 50;
    const lo=e*.8,hi=e*1.2; return Math.max(2,Math.min(98,(p-lo)/(hi-lo)*100));
  }}
  function ratingText(s){{
    const b=s.analyst_breakdown||{{}};
    const parts=[['Strong buy',b.strong_buy],['Buy',b.buy],['Hold',b.hold],['Sell',b.sell],['Strong sell',b.strong_sell]].filter(x=>x[1]!==null&&x[1]!==undefined);
    return parts.length?parts.map(x=>'<span class="ew-chip">'+x[0]+' '+x[1]+'</span>').join(''):'<span class="ew-chip">Breakdown unavailable</span>';
  }}
  function targetUpside(s){{
    const p=Number(s.price),t=Number(s.target); if(!p||!t)return null; return (t/p-1)*100;
  }}
  function card(s){{
    const [state,key]=derive(s), pos=barPos(s), chg=Number(s.chg), score=Number(s.score);
    const warn=!s.stop||!s.size;
    return `<article class="ew-card ${key}" data-ticker="${s.ticker}">
      <div class="ew-card-top"><div><div class="ew-ticker-row"><span class="ew-ticker">${s.ticker}</span><span class="ew-score">${Number.isFinite(score)?score.toFixed(1)+' '+(s.grade||''):'Score —'}</span></div><div class="ew-company">${s.company||s.ticker}</div></div><button class="ew-info ${warn?'warn':''}" data-info="${s.ticker}" aria-label="Details for ${s.ticker}">i</button></div>
      <div class="ew-price-row"><div class="ew-price">${fmt(s.price)}</div><div class="ew-chg ${Number.isFinite(chg)?(chg>=0?'up':'down'):'muted'}">${Number.isFinite(chg)?pct(chg):'change —'}</div></div>
      <div class="ew-state ${key}">${state}</div>
      <div class="ew-bar-wrap"><div class="ew-bar-labels"><span>${s.entry?fmt(Number(s.entry)*.8):'—'}</span><span>Entry ${fmt(s.entry)}</span><span>${s.entry?fmt(Number(s.entry)*1.2):'—'}</span></div><div class="ew-bar"><span class="ew-entry-mark"></span><span class="ew-price-mark" style="left:${pos}%"></span></div></div>
      <div class="ew-mini"><div><label>Planned entry</label><strong>${fmt(s.entry)}</strong></div><div><label>Target / horizon</label><strong>${s.target?fmt(s.target)+' · '+(s.target_horizon||'Not set'):'Not set'}</strong></div></div>
    </article>`;
  }}
  function render(){{
    const data=mergedData(), sections=$('#ew-sections'); sections.innerHTML='';
    const states=data.map(derive).map(x=>x[0]);
    $('#ew-summary').innerHTML=`<div class="ew-summary-card"><div class="ew-summary-label">Watchlist</div><div class="ew-summary-value">${data.length}</div></div><div class="ew-summary-card"><div class="ew-summary-label">At entry</div><div class="ew-summary-value" style="color:var(--ew-green)">${states.filter(x=>x==='ENTER').length}</div></div><div class="ew-summary-card"><div class="ew-summary-label">Check data</div><div class="ew-summary-value" style="color:var(--ew-amber)">${states.filter(x=>x==='CHECK DATA').length}</div></div>`;
    const cats=[...CATEGORY_ORDER,'My additions'];
    cats.forEach(cat=>{{
      const items=data.filter(x=>(x.category||'My additions')===cat); if(!items.length)return;
      const thesis=items[0].category_thesis||'Locally saved watchlist additions';
      const sec=document.createElement('section'); sec.className='ew-section';
      sec.innerHTML=`<div class="ew-section-head"><div><h2>${cat}</h2><span>${thesis}</span></div><span>${items.length} stocks</span></div><div class="ew-grid">${items.map(card).join('')}</div>`;
      sections.appendChild(sec);
    }});
    bindInfo();
  }}
  function stock(ticker){{return mergedData().find(x=>x.ticker===ticker)}}
  function openPop(ticker,btn){{
    const s=stock(ticker);if(!s)return;active=ticker;
    const pop=$('#ew-pop'), u=targetUpside(s), out=s.industry_outlook||{{}};
    const stop=s.stop?fmt(s.stop):'<span class="not-set">Not set</span>', size=s.size||'<span class="not-set">Not set</span>';
    pop.innerHTML=`<div class="ew-pop-head"><div><div class="ew-pop-title">${s.ticker} · ${derive(s)[0]}</div><div class="ew-pop-company">${s.company||s.ticker}</div></div><button class="ew-pop-close" data-pop-close aria-label="Close">×</button></div>
      <div class="ew-pop-why">${s.why||'No thesis note set.'}</div>
      <div class="ew-detail-grid">
        <div class="ew-detail"><label>Planned entry</label><strong>${fmt(s.entry)}</strong></div>
        <div class="ew-detail"><label>Stop</label><strong>${stop}</strong></div>
        <div class="ew-detail"><label>Size</label><strong>${size}</strong></div>
        <div class="ew-detail"><label>Model score</label><strong>${Number.isFinite(Number(s.score))?Number(s.score).toFixed(1)+' '+(s.grade||''):'Not available'}</strong></div>
        <div class="ew-detail"><label>Type</label><strong>${s.type||'Not set'}</strong></div>
        <div class="ew-detail"><label>Model signal</label><strong>${s.signal||'Not available'}</strong></div>
        <div class="ew-detail"><label>${s.target_horizon||'Target'} target</label><strong>${s.target?fmt(s.target):'<span class="not-set">Not set</span>'}</strong></div>
        <div class="ew-detail"><label>Target vs price</label><strong>${u===null?'—':pct(u)}</strong></div>
      </div>
      <div class="ew-warning">Targets are model/analyst output or user-entered values and are <b>not validated</b>. They are not guaranteed outcomes.</div>
      <div class="ew-pop-section"><h4>Analyst ratings</h4><div class="ew-ratings">${ratingText(s)}</div><div class="ew-outlook" style="margin-top:8px">Consensus: <b>${(s.analyst_rec||'unavailable').replaceAll('_',' ')}</b> · ${s.analyst_count||0} analyst opinions · Target price: <b>${fmt(s.target)}</b></div></div>
      <div class="ew-pop-section"><h4>Recent industry outlook · ~2–4 weeks</h4><div class="ew-outlook"><b>${out.label||'N/A'}</b> — ${out.note||'Recent sector trend unavailable.'}<br><br><b>Watchlist peer pulse:</b> ${s.peer_pulse||'Not enough peer data.'}</div></div>
      <button class="ew-remove" data-remove="${s.ticker}">Remove from watchlist</button>`;
    pop.classList.add('open');
    const r=btn.getBoundingClientRect(), pw=Math.min(390,innerWidth-24), ph=Math.min(pop.scrollHeight,innerHeight-24);
    let left=Math.min(innerWidth-pw-12,Math.max(12,r.right-pw)), top=r.bottom+8;
    if(top+ph>innerHeight-12)top=Math.max(12,r.top-ph-8);
    pop.style.left=left+'px';pop.style.top=top+'px';
    pop.querySelector('[data-pop-close]').onclick=closePop;
    pop.querySelector('[data-remove]').onclick=()=>removeStock(s.ticker);
  }}
  function closePop(){{const p=$('#ew-pop');p.classList.remove('open');active=null}}
  function bindInfo(){{
    const hover=matchMedia('(hover:hover) and (pointer:fine)').matches;
    document.querySelectorAll('[data-info]').forEach(btn=>{{
      btn.onclick=e=>{{e.stopPropagation();active===btn.dataset.info?closePop():openPop(btn.dataset.info,btn)}};
      if(hover){{btn.onmouseenter=()=>{{clearTimeout(hoverTimer);openPop(btn.dataset.info,btn)}};btn.onmouseleave=()=>{{hoverTimer=setTimeout(closePop,240)}}}}
    }});
    const p=$('#ew-pop'); if(hover){{p.onmouseenter=()=>clearTimeout(hoverTimer);p.onmouseleave=()=>{{hoverTimer=setTimeout(closePop,240)}}}}
  }}
  function toast(msg,type='good'){{const n=document.createElement('div');n.className='ew-toast '+type;n.textContent=msg;$('#ew-toasts').appendChild(n);setTimeout(()=>n.remove(),4200)}}
  async function refreshPrices(){{
    const b=$('#ew-refresh');b.classList.add('loading');b.disabled=true;
    if(!PRICE_URL){{toast('No PRICE_URL feed is configured.','warn');b.classList.remove('loading');b.disabled=false;return}}
    try{{
      const res=await fetch(PRICE_URL+(PRICE_URL.includes('?')?'&':'?')+'t='+Date.now(),{{cache:'no-store'}});
      if(!res.ok)throw new Error('HTTP '+res.status);
      const j=await res.json();let count=0;
      BASE.forEach(s=>{{const x=j[s.ticker];if(x&&Number.isFinite(Number(x.price))){{s.price=Number(x.price);if(Number.isFinite(Number(x.chg)))s.chg=Number(x.chg);count++}}}});
      Object.values(additions).forEach(s=>{{const x=j[s.ticker];if(x&&Number.isFinite(Number(x.price))){{s.price=Number(x.price);if(Number.isFinite(Number(x.chg)))s.chg=Number(x.chg);count++}}}});
      safeSet(LS.add,additions);$('#ew-price-time').textContent=new Date().toLocaleString(undefined,{{hour12:true}});render();toast('Prices refreshed for '+count+' stocks.','good');
    }}catch(err){{toast('Refresh failed. Keeping last prices: '+err.message,'bad')}}
    finally{{b.classList.remove('loading');b.disabled=false}}
  }}
  function openModal(){{$('#ew-modal-bg').classList.add('open');setTimeout(()=>$('#f-ticker').focus(),30)}}
  function closeModal(){{$('#ew-modal-bg').classList.remove('open');$('#ew-form').reset();['ticker','entry','price','target'].forEach(x=>$('#e-'+x).textContent='')}}
  function num(v){{if(v.trim()==='')return null;const n=Number(v);return Number.isFinite(n)?n:NaN}}
  function submit(e){{
    e.preventDefault();['ticker','entry','price','target'].forEach(x=>$('#e-'+x).textContent='');
    const ticker=$('#f-ticker').value.trim().toUpperCase(),entry=num($('#f-entry').value),price=num($('#f-price').value),target=num($('#f-target').value);
    let bad=false;if(!/^[A-Z][A-Z0-9.-]{{0,9}}$/.test(ticker)){{$('#e-ticker').textContent='Enter a valid ticker.';bad=true}}if(!Number.isFinite(entry)||entry<=0){{$('#e-entry').textContent='Planned entry is required and must be above 0.';bad=true}}if(Number.isNaN(price)||price!==null&&price<=0){{$('#e-price').textContent='Use a positive number or leave blank.';bad=true}}if(Number.isNaN(target)||target!==null&&target<=0){{$('#e-target').textContent='Use a positive number or leave blank.';bad=true}}if(bad)return;
    removed.delete(ticker);safeSet(LS.removed,[...removed]);
    const existing=BASE.find(x=>x.ticker===ticker);
    const patch={{entry,company:$('#f-company').value.trim()||(existing?.company||ticker)}};if(price!==null)patch.price=price;if(target!==null)patch.target=target;const h=$('#f-horizon').value;if(h)patch.target_horizon=h;
    if(existing){{overrides[ticker]=Object.assign({{}},overrides[ticker]||{{}},patch);safeSet(LS.overrides,overrides);toast(ticker+' updated.','good')}}
    else{{additions[ticker]=Object.assign({{ticker,category:'My additions',category_thesis:'Locally saved watchlist additions',why:'Added locally. Thesis note not set.',price:null,chg:null,target:null,target_horizon:null,target_upside:null,target_note:'User-entered target; not validated.',score:null,grade:null,signal:null,conviction:null,type:null,analyst_rec:null,analyst_count:0,analyst_breakdown:{{}},industry_outlook:{{label:'N/A',note:'Industry data unavailable for local-only stock.'}},peer_pulse:'Peer data unavailable.',stop:null,size:null,local_only:true}},patch);safeSet(LS.add,additions);toast(ticker+' added to this browser.','good')}}
    closeModal();render();
  }}
  function removeStock(ticker){{removed.add(ticker);delete additions[ticker];safeSet(LS.removed,[...removed]);safeSet(LS.add,additions);closePop();render();toast(ticker+' removed from this browser watchlist.','warn')}}
  document.addEventListener('keydown',e=>{{if(e.key==='Escape'){{closePop();closeModal()}}}});
  document.addEventListener('click',e=>{{if(active&&!e.target.closest('#ew-pop')&&!e.target.closest('[data-info]'))closePop()}});
  $('#ew-refresh').onclick=refreshPrices;$('#ew-add').onclick=openModal;$('#ew-modal-x').onclick=closeModal;$('#ew-cancel').onclick=closeModal;$('#ew-modal-bg').onclick=e=>{{if(e.target===e.currentTarget)closeModal()}};$('#ew-form').onsubmit=submit;
  render();
}})();
</script>
"""
    return (html
        .replace("__PAYLOAD__", payload)
        .replace("__CATEGORIES__", categories)
        .replace("__NOW__", escape(now))
        .replace("{{", "{")
        .replace("}}", "}")
    )
