"""40-parameter regime-aware stock health model for The Chai Ledger.

The model follows the user's scoring framework:
- regime check before scoring
- dynamic bucket weights
- 40 parameters scored 0-10
- N/A parameters excluded and bucket weights renormalized
- hard disqualifiers
- grade/recommendation/signal derivation

Important data-quality rule:
Official GICS Sub-Industry peer medians and some filing/ownership fields are
not available from the current free Yahoo Finance feed. Those parameters are
left N/A rather than guessed, exactly as requested.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from statistics import mean

try:
    import yfinance as yf
    import pandas as pd
    YF_AVAILABLE = True
except Exception:
    YF_AVAILABLE = False
    yf = None
    pd = None

DEFAULT_TICKERS = [
    "MU","NVDA","AVGO","GOOGL","AMZN","MSFT","META","AAPL","ORCL",
    "PSTG","SNOW","CRM","WDAY","V","MA","SPGI","DAL","UAL","EXPE"
]

BASE_PROFILES = {
    "Risk-on / Expanding": {
        "Valuation": .15, "Growth": .30, "Profitability/Balance Sheet": .15,
        "Sentiment": .15, "Technicals": .10, "Macro/Sector": .05, "Catalysts/Risk": .10,
    },
    "Neutral / Stable": {
        "Valuation": .20, "Growth": .20, "Profitability/Balance Sheet": .20,
        "Sentiment": .15, "Technicals": .10, "Macro/Sector": .10, "Catalysts/Risk": .05,
    },
    "Risk-off / Contracting": {
        "Valuation": .30, "Growth": .10, "Profitability/Balance Sheet": .25,
        "Sentiment": .10, "Technicals": .10, "Macro/Sector": .10, "Catalysts/Risk": .05,
    },
}

PARAM_BUCKET = {
    **{i: "Valuation" for i in range(1, 7)},
    **{i: "Growth" for i in range(7, 13)},
    **{i: "Profitability/Balance Sheet" for i in range(13, 20)},
    **{i: "Sentiment" for i in range(20, 27)},
    **{i: "Technicals" for i in range(27, 34)},
    **{i: "Macro/Sector" for i in range(34, 38)},
    **{i: "Catalysts/Risk" for i in range(38, 41)},
}

PARAM_NAMES = {
    1:"Trailing P/E vs GICS Sub-Industry Median",2:"Forward P/E vs GICS Sub-Industry Median",3:"PEG ratio",4:"EV/EBITDA vs GICS Sub-Industry Median",5:"Price/FCF vs GICS Sub-Industry Median",6:"Price target upside vs consensus mean",
    7:"Revenue growth YoY",8:"Revenue growth trend (last 4 qtrs)",9:"Earnings growth YoY",10:"Earnings surprise history (last 4 qtrs)",11:"Forward guidance direction",12:"TAM expansion / new-product optionality",
    13:"FCF absolute trend",14:"Profit margin trend",15:"ROE",16:"Debt-to-equity vs GICS sub-industry",17:"Cash vs total debt",18:"Capex intensity trend",19:"Accounting quality / restatement history",
    20:"Analyst consensus + count",21:"Rating changes, last 90 days",22:"Institutional ownership level",23:"Institutional activity trend, last 2 qtrs",24:"Short interest % of float",25:"News sentiment, last 30 days",26:"Insider buying/selling ex-10b5-1",
    27:"Position in 52-week range",28:"Price vs MA alignment (50d + 200d)",29:"ATR / short-term swing character",30:"RSI (14-day)",31:"MACD signal",32:"Volume trend vs 90-day avg",33:"Put/call ratio",
    34:"Sector momentum vs broad index, 90 days",35:"Rate sensitivity of business model",36:"Regulatory/legal exposure, active only",37:"Competitive position, last 2 qtrs",
    38:"Confirmed near-term catalysts within 45 days",39:"Concentration risk",40:"Capital allocation quality",
}

SECTOR_ETF = {"Technology":"XLK","Communication Services":"XLC","Consumer Cyclical":"XLY","Financial Services":"XLF","Industrials":"XLI"}
CYCLICAL_TICKERS={"DAL","UAL","EXPE","MU"}
HYPERGROWTH_TICKERS={"SNOW","PSTG"}
TURNAROUND_TICKERS={"CRM","WDAY"}

def safe(v, default=None):
    try:
        if v is None:return default
        if isinstance(v,float) and math.isnan(v):return default
        return v
    except Exception:return default

def _clip(v,lo=0,hi=10): return max(lo,min(hi,float(v)))

def _score_band(value,bands):
    if value is None:return None
    for pred,score in bands:
        if pred(value):return float(score)
    return None

def _series_values(df,row_names):
    if df is None or getattr(df,"empty",True):return []
    for name in row_names:
        if name in df.index:
            vals=[]
            for x in df.loc[name].tolist():
                try:
                    if x is not None and not math.isnan(float(x)): vals.append(float(x))
                except Exception: pass
            return vals
    return []

def _trend_score(vals):
    if len(vals)<4:return None
    recent=list(reversed(vals[:4]));d=[]
    for i in range(1,len(recent)):
        if recent[i-1]!=0:d.append((recent[i]-recent[i-1])/abs(recent[i-1]))
    if len(d)<2:return None
    slope=d[-1]-d[0]
    if slope>.08:return 9
    if slope>.02:return 8
    if slope>-.02:return 6
    if slope>-.08:return 3
    return 1

def _history(tk,period="1y"):
    try:
        h=tk.history(period=period,auto_adjust=False)
        return h if h is not None and not h.empty else None
    except Exception:return None

def _regime_context():
    out={"market_regime":"Neutral","vix":None,"rate_3m_change":None,"tech_breadth":None}
    if not YF_AVAILABLE:return out
    try:
        vix_h=_history(yf.Ticker("^VIX"),"3mo");tnx_h=_history(yf.Ticker("^TNX"),"6mo")
        out["vix"]=float(vix_h["Close"].iloc[-1]) if vix_h is not None else None
        if tnx_h is not None and len(tnx_h)>=45:out["rate_3m_change"]=float(tnx_h["Close"].iloc[-1]-tnx_h["Close"].iloc[-45])
        tech=["NVDA","MSFT","AAPL","AMZN","META","GOOGL","AVGO","CRM","ORCL","SNOW"]
        above=valid=0
        for t in tech:
            h=_history(yf.Ticker(t),"3mo")
            if h is not None and len(h)>=50:
                valid+=1
                if float(h["Close"].iloc[-1])>=float(h["Close"].tail(50).mean()):above+=1
        out["tech_breadth"]=above/valid if valid else None
        vix=out["vix"];rate=out["rate_3m_change"];breadth=out["tech_breadth"]
        risk_off=(vix is not None and vix>=25) or (breadth is not None and breadth<.35 and (rate or 0)>.15)
        risk_on=(vix is not None and vix<18) and (breadth is not None and breadth>.60) and ((rate or 0)<=.20)
        out["market_regime"]="Risk-off" if risk_off else ("Risk-on" if risk_on else "Neutral")
    except Exception:pass
    return out

_REGIME_CACHE=None
def get_regime_context():
    global _REGIME_CACHE
    if _REGIME_CACHE is None:_REGIME_CACHE=_regime_context()
    return _REGIME_CACHE

def _sector_health(info):
    sector=info.get("sector") or "";etf=SECTOR_ETF.get(sector)
    if not etf or not YF_AVAILABLE:return "Stable",None
    try:
        h=_history(yf.Ticker(etf),"6mo");spy=_history(yf.Ticker("SPY"),"6mo")
        if h is None or len(h)<64:return "Stable",None
        mom=float(h["Close"].iloc[-1]/h["Close"].iloc[-64]-1);rel=None
        if spy is not None and len(spy)>=64:rel=mom-float(spy["Close"].iloc[-1]/spy["Close"].iloc[-64]-1)
        if mom>.08 and (rel is None or rel>-.02):return "Expanding",rel
        if mom<-.08:return "Contracting",rel
        return "Stable",rel
    except Exception:return "Stable",None

def _lifecycle(ticker,info):
    rev=safe(info.get("revenueGrowth"));fcf=safe(info.get("freeCashflow"));margin=safe(info.get("profitMargins"))
    if ticker in HYPERGROWTH_TICKERS or (rev is not None and rev>.25 and (margin is None or margin<.15)):return "Hypergrowth"
    if ticker in TURNAROUND_TICKERS or (rev is not None and rev<.05 and fcf and fcf>0):return "Turnaround"
    if ticker in CYCLICAL_TICKERS:return "Cyclical-trough"
    return "Compounder"

def _profile(market_regime,sector_health,lifecycle):
    if market_regime=="Risk-off" or sector_health=="Contracting":name="Risk-off / Contracting"
    elif market_regime=="Risk-on" and sector_health=="Expanding":name="Risk-on / Expanding"
    else:name="Neutral / Stable"
    weights=BASE_PROFILES[name].copy()
    if lifecycle in {"Cyclical-trough","Turnaround"}:
        shift=min(.05,weights["Growth"]);weights["Growth"]-=shift;weights["Profitability/Balance Sheet"]+=shift
    elif lifecycle=="Hypergrowth":
        shift=min(.05,weights["Profitability/Balance Sheet"]);weights["Profitability/Balance Sheet"]-=shift;weights["Growth"]+=shift
    return name,weights

def _news_sentiment(tk):
    try:items=tk.news or []
    except Exception:return None,None
    if not items:return None,None
    pos={"beat","surge","growth","record","upgrade","raises","raise","strong","wins","expands","profit","bullish"};neg={"miss","cuts","cut","downgrade","lawsuit","probe","decline","weak","warning","fraud","bearish","slump"}
    score=n=0
    for item in items[:30]:
        title=(item.get("title") or item.get("content",{}).get("title") or "").lower() if isinstance(item,dict) else ""
        if not title:continue
        n+=1;score+=sum(1 for w in pos if w in title);score-=sum(1 for w in neg if w in title)
    if not n:return None,None
    avg=score/n
    if avg>.25:return 9,"positive headline balance"
    if avg<-.25:return 2,"negative headline balance"
    return 6,"mixed/neutral headline balance"

def _rsi(close,n=14):
    if close is None or len(close)<n+2:return None
    d=close.diff();gain=d.clip(lower=0).rolling(n).mean();loss=(-d.clip(upper=0)).rolling(n).mean();rs=gain/loss.replace(0,float("nan"));r=100-(100/(1+rs))
    try:return float(r.iloc[-1])
    except Exception:return None

def _atr(hist,n=14):
    if hist is None or len(hist)<n+2:return None
    prev=hist["Close"].shift(1);tr=pd.concat([(hist["High"]-hist["Low"]).abs(),(hist["High"]-prev).abs(),(hist["Low"]-prev).abs()],axis=1).max(axis=1)
    try:return float(tr.rolling(n).mean().iloc[-1])
    except Exception:return None

def _macd_signal(close):
    if close is None or len(close)<35:return None
    ema12=close.ewm(span=12,adjust=False).mean();ema26=close.ewm(span=26,adjust=False).mean();macd=ema12-ema26;sig=macd.ewm(span=9,adjust=False).mean();diff=macd-sig
    if diff.iloc[-1]>0 and diff.iloc[-1]>diff.iloc[-3]:return 9
    if abs(diff.iloc[-1])<max(abs(macd.iloc[-1])*.08,1e-9):return 5
    if diff.iloc[-1]<0:return 2
    return 6

def _put_call_score(tk):
    try:
        opts=tk.options
        if not opts:return None,None
        ch=tk.option_chain(opts[0]);cv=float(ch.calls["volume"].fillna(0).sum());pv=float(ch.puts["volume"].fillna(0).sum())
        if cv<=0:return None,None
        ratio=pv/cv
        if ratio<.7:return 9,ratio
        if ratio<=1.1:return 6,ratio
        return 3,ratio
    except Exception:return None,None

def _rating_changes(tk):
    try:
        df=tk.upgrades_downgrades
        if df is None or df.empty:return None,None
        idx=df.index;cutoff=(pd.Timestamp.now(tz=idx.tz)-pd.Timedelta(days=90)) if getattr(idx,"tz",None) is not None else (pd.Timestamp.now()-pd.Timedelta(days=90));work=df[df.index>=cutoff]
        if work.empty:return 6,"no recent changes"
        acts=" ".join(str(x).lower() for x in work.get("Action",[]));ups=acts.count("up");downs=acts.count("down")
        if ups>downs:return 9,f"{ups} upgrades vs {downs} downgrades"
        if downs>ups:return 2,f"{downs} downgrades vs {ups} upgrades"
        return 6,f"{ups} upgrades / {downs} downgrades"
    except Exception:return None,None

def _earnings_surprise(tk):
    try:
        df=tk.get_earnings_dates(limit=8)
        if df is None or df.empty:return None,None
        col=next((c for c in df.columns if "Surprise" in str(c)),None)
        if col is None:return None,None
        vals=[float(x) for x in df[col].dropna().head(4).tolist()]
        if not vals:return None,None
        avg=mean(vals);score=9 if all(x>0 for x in vals) else (2 if all(x<0 for x in vals) else 6)
        return score,avg
    except Exception:return None,None

def _near_term_catalyst(tk):
    try:
        cal=tk.calendar
        if not cal:return 6,"No dated positive catalyst verified"
        dates=[]
        if isinstance(cal,dict):
            for key,val in cal.items():
                if "Earnings" in str(key) or "Ex-Dividend" in str(key):dates.extend(val if isinstance(val,(list,tuple)) else [val])
        now=datetime.now(timezone.utc)
        for d in dates:
            try:
                ts=pd.Timestamp(d)
                if ts.tzinfo is None:ts=ts.tz_localize("UTC")
                days=(ts.to_pydatetime()-now).days
                if 0<=days<=45:return 6,f"Scheduled event in {days} days; not assumed positive"
            except Exception:pass
        return 6,"No dated positive catalyst verified"
    except Exception:return 6,"No dated positive catalyst verified"

def _score_stock_core(ticker):
    tk=yf.Ticker(ticker);info=tk.info or {};price=safe(info.get("currentPrice") or info.get("regularMarketPrice"),0) or 0;prev=safe(info.get("regularMarketPreviousClose"),price) or price;day=((price-prev)/prev*100) if prev else 0
    hist=_history(tk,"1y");qfin=qcf=None
    try:qfin=tk.quarterly_financials
    except Exception:pass
    try:qcf=tk.quarterly_cashflow
    except Exception:pass
    market=get_regime_context();sector_health,sector_rel=_sector_health(info);lifecycle=_lifecycle(ticker,info);profile_name,weights=_profile(market["market_regime"],sector_health,lifecycle)
    p={};low_conf=[]
    def add(i,score,finding,source="Yahoo Finance",confidence="normal"):
        p[i]={"parameter":PARAM_NAMES[i],"bucket":PARAM_BUCKET[i],"score":None if score is None else round(_clip(score),2),"finding":finding,"source":source,"confidence":confidence}
        if confidence=="low":low_conf.append(i)
    for i,label in [(1,"Official GICS sub-industry median feed not connected"),(2,"Official GICS sub-industry median feed not connected"),(4,"Official GICS sub-industry median feed not connected"),(5,"Official GICS sub-industry median feed not connected")]:add(i,None,label,"N/A")
    peg=safe(info.get("pegRatio"));add(3,_score_band(peg,[(lambda x:x<1,9),(lambda x:x<1.5,6),(lambda x:x<2,3.5),(lambda x:True,1)]),f"PEG {peg:.2f}" if peg is not None else "PEG unavailable")
    target=safe(info.get("targetMeanPrice"));upside=(target-price)/price*100 if target and price else None;add(6,_score_band(upside,[(lambda x:x>40,9.5),(lambda x:x>=20,7),(lambda x:x>=0,4),(lambda x:True,1)]),f"Consensus target {target:.2f}; upside {upside:.1f}%" if upside is not None else "Consensus target unavailable")
    rev=safe(info.get("revenueGrowth"));add(7,_score_band(rev,[(lambda x:x>.25,9.5),(lambda x:x>=.12,7),(lambda x:x>=0,4),(lambda x:True,1)]),f"Revenue growth {rev*100:.1f}%" if rev is not None else "Revenue growth unavailable")
    revs=_series_values(qfin,["Total Revenue","Operating Revenue"]);add(8,_trend_score(revs),f"Quarterly revenue values available: {len(revs)}")
    eg=safe(info.get("earningsGrowth"));add(9,_score_band(eg,[(lambda x:x>.25,9.5),(lambda x:x>=.10,7),(lambda x:x>=0,4),(lambda x:True,1)]),f"Earnings growth {eg*100:.1f}%" if eg is not None else "Earnings growth unavailable")
    es,esv=_earnings_surprise(tk);add(10,es,f"Avg last-4 surprise {esv:.2f}%" if esv is not None else "Earnings surprise history unavailable");add(11,None,"Forward guidance direction not available reliably from current feed","N/A");add(12,None,"TAM/new-product optionality requires sourced qualitative research","N/A")
    fcfs=_series_values(qcf,["Free Cash Flow"])
    if not fcfs:
        cfo=_series_values(qcf,["Operating Cash Flow","Total Cash From Operating Activities"]);capex=_series_values(qcf,["Capital Expenditure","Capital Expenditures"])
        if cfo and capex:fcfs=[a+b for a,b in zip(cfo,capex)]
    fcf_score=None
    if len(fcfs)>=3:
        newest=fcfs[0];older=fcfs[min(3,len(fcfs)-1)];fcf_score=9 if newest>0 and newest>older else (6 if newest>0 else (3.5 if newest<0 and newest>older else 1))
    add(13,fcf_score,f"{len(fcfs)} quarterly FCF observations")
    nis=_series_values(qfin,["Net Income","Net Income Common Stockholders"]);margin_vals=[ni/rv for ni,rv in zip(nis,revs) if rv];mscore=None
    if len(margin_vals)>=3:mscore=9 if margin_vals[0]>margin_vals[-1]+.02 else (2 if margin_vals[0]<margin_vals[-1]-.02 else 6)
    add(14,mscore,f"{len(margin_vals)} quarterly net-margin observations")
    roe=safe(info.get("returnOnEquity"));add(15,_score_band(roe,[(lambda x:x>.20,9.5),(lambda x:x>=.10,7),(lambda x:x>=0,4),(lambda x:True,1)]),f"ROE {roe*100:.1f}%" if roe is not None else "ROE unavailable");add(16,None,"Official GICS sub-industry leverage median feed not connected","N/A")
    cash=safe(info.get("totalCash"),0) or 0;debt=safe(info.get("totalDebt"),0) or 0;cs=9 if cash>=debt else (3.5 if debt<=cash*2 else 1);add(17,cs,f"Cash {cash:,.0f}; debt {debt:,.0f}")
    capex=_series_values(qcf,["Capital Expenditure","Capital Expenditures"]);cap_int=[abs(cp)/rv for cp,rv in zip(capex,revs) if rv];cscore=None
    if len(cap_int)>=3 and len(revs)>=3:
        rev_up=revs[0]>=revs[-1];cscore=9 if cap_int[0]<=cap_int[-1] and rev_up else (6 if cap_int[0]>cap_int[-1] and rev_up else (2 if cap_int[0]>cap_int[-1] and not rev_up else 5))
    add(18,cscore,f"{len(cap_int)} quarterly capex-intensity observations");add(19,None,"Restatement/accounting-quality history requires filing-quality data feed","N/A")
    rec=(safe(info.get("recommendationKey"),"none") or "none").lower();n_analysts=safe(info.get("numberOfAnalystOpinions"),0) or 0;ars=9 if rec=="strong_buy" and n_analysts>=20 else (6.5 if rec in {"buy","strong_buy"} else (3 if rec=="hold" else (1 if rec in {"sell","underperform"} else None)));add(20,ars,f"{rec.replace('_',' ').title()} from {n_analysts} analysts")
    rs,rf=_rating_changes(tk);add(21,rs,rf or "Rating-change data unavailable");inst=safe(info.get("heldPercentInstitutions"));add(22,_score_band(inst,[(lambda x:x>.70,8.5),(lambda x:x>=.40,5),(lambda x:True,2)]),f"Institutional ownership {inst*100:.1f}%" if inst is not None else "Institutional ownership unavailable");add(23,None,"Two-quarter institutional flow trend unavailable from current feed","N/A")
    short=safe(info.get("shortPercentOfFloat"));add(24,_score_band(short,[(lambda x:x<.03,9),(lambda x:x<.08,6),(lambda x:x<.15,3),(lambda x:True,1)]),f"Short float {short*100:.1f}%" if short is not None else "Short interest unavailable");ns,nf=_news_sentiment(tk);add(25,ns,nf or "Recent news unavailable","Yahoo Finance headlines","low" if ns is not None else "normal");add(26,None,"Open-market vs scheduled 10b5-1 insider activity cannot be separated reliably","N/A")
    hi=safe(info.get("fiftyTwoWeekHigh"));lo=safe(info.get("fiftyTwoWeekLow"));pos=(price-lo)/(hi-lo) if hi and lo and hi>lo and price else None;p27=None
    if pos is not None:p27=(8 if (fcfs and fcfs[0]>0) else 6) if pos<1/3 else (5 if pos<2/3 else 4)
    add(27,p27,f"52-week position {pos*100:.1f}%" if pos is not None else "52-week range unavailable")
    ma50=safe(info.get("fiftyDayAverage"));ma200=safe(info.get("twoHundredDayAverage"));ma_score=None
    if ma50 and ma200 and price:ma_score=9 if price>ma50>ma200 else (5.5 if price>ma200 or price>ma50 else 2)
    add(28,ma_score,f"Price {price:.2f}; MA50 {ma50}; MA200 {ma200}")
    atr=_atr(hist);atr_pct=(atr/price) if atr and price else None;add(29,_score_band(atr_pct,[(lambda x:x<.025,8.5),(lambda x:x<.05,5),(lambda x:True,2)]),f"ATR/price {atr_pct*100:.1f}%" if atr_pct is not None else "ATR unavailable")
    rsi=_rsi(hist["Close"]) if hist is not None else None;rsis=7 if rsi is not None and 40<=rsi<=60 else (5 if rsi is not None and (30<=rsi<40 or 60<rsi<=70) else (3 if rsi is not None else None));add(30,rsis,f"RSI {rsi:.1f}" if rsi is not None else "RSI unavailable");macs=_macd_signal(hist["Close"]) if hist is not None else None;add(31,macs,"Bullish / flat / bearish derived from MACD spread" if macs is not None else "MACD unavailable")
    vscore=None;vf="Volume data unavailable"
    if hist is not None and len(hist)>=90:
        recent=hist.tail(90).copy();avg=float(recent["Volume"].mean());up=recent[recent["Close"].diff()>0]["Volume"].mean();down=recent[recent["Close"].diff()<0]["Volume"].mean()
        if avg>0 and not math.isnan(up) and not math.isnan(down):vscore=8.5 if up>down*1.10 else (3 if down>up*1.10 else 5.5);vf=f"Up-day avg volume {up:,.0f}; down-day {down:,.0f}"
    add(32,vscore,vf);pcs,pcr=_put_call_score(tk);add(33,pcs,f"Nearest-expiry put/call volume ratio {pcr:.2f}" if pcr is not None else "Put/call unavailable")
    s34=None if sector_rel is None else (9 if sector_rel>.05 else (6 if sector_rel>=-.03 else 2));add(34,s34,f"Sector ETF 90d relative return {sector_rel*100:.1f}%" if sector_rel is not None else "Sector relative momentum unavailable")
    de_raw=safe(info.get("debtToEquity"));de=(de_raw/100.0) if de_raw is not None else None;net_cash=cash-debt;rate_score=9 if net_cash>0 else (6 if de is not None and de<.75 else (4 if de is not None and de<1.5 else 2));add(35,rate_score,f"Net cash {net_cash:,.0f}; D/E {de:.2f}" if de is not None else f"Net cash {net_cash:,.0f}");add(36,None,"Active legal/regulatory exposure requires current filing/news verification","N/A");add(37,None,"Two-quarter market-share trend requires industry research feed","N/A")
    cats,catf=_near_term_catalyst(tk);add(38,cats,catf);add(39,None,"Customer/geographic concentration requires filing-level segment/customer data","N/A")
    buybacks=_series_values(qcf,["Repurchase Of Capital Stock","Repurchase Of Stock"]);dividends=_series_values(qcf,["Cash Dividends Paid","Common Stock Dividend Paid"]);ca=None
    if fcfs and fcfs[0]>0:
        ca=8
        if debt>cash*3 and ((buybacks and abs(buybacks[0])>fcfs[0]) or (dividends and abs(dividends[0])>fcfs[0])):ca=4
    elif fcfs:ca=5
    add(40,ca,"FCF-funded distributions/debt heuristic" if ca is not None else "Capital-allocation data insufficient")
    bucket_scores={};weighted_total=0;na_high_bucket=False
    for bucket,w in weights.items():
        rows=[p[i] for i in range(1,41) if PARAM_BUCKET[i]==bucket];avail=[r for r in rows if r["score"] is not None]
        if not avail:bucket_scores[bucket]=None;continue
        bscore=sum(r["score"] for r in avail)/len(avail);bucket_scores[bucket]=bscore;weighted_total+=(bscore/10)*w
        if w>=.15 and len(avail)<len(rows):na_high_bucket=True
    score=round(weighted_total*100,1);disq=[];neg4=len(fcfs)>=4 and all(x<0 for x in fcfs[:4])
    if neg4:
        exempt=False
        if lifecycle=="Hypergrowth":
            burn=abs(mean(fcfs[:4])) if fcfs[:4] else 0;exempt=burn>0 and cash/burn>=8
        if not exempt:disq.append("Negative FCF for 4+ consecutive quarters")
    if len(revs)>=7:
        yoy=[revs[i]<revs[i+4] for i in range(3)]
        if all(yoy):disq.append("Revenue declining YoY for 3+ consecutive quarters")
    grade="A+" if score>=90 else ("A" if score>=80 else ("B" if score>=70 else ("C" if score>=60 else ("D" if score>=50 else "F"))))
    rec_out="Sell" if len(disq)>=2 else ("Hold" if disq else ("Strong Buy" if score>=85 else ("Buy" if score>=70 else ("Hold" if score>=50 else "Sell"))))
    near_boundary=any(abs(score-b)<=5 for b in [90,85,80,70,60,50]);low_conv=na_high_bucket or bool(low_conf) or near_boundary;conviction="Low" if low_conv else "Normal";signal="SELL" if rec_out=="Sell" else ("HOLD" if rec_out=="Hold" or low_conv else ("STRONG BUY" if rec_out=="Strong Buy" else "BUY"))
    for bucket,w in weights.items():
        ids=[i for i in range(1,41) if PARAM_BUCKET[i]==bucket and p[i]["score"] is not None];each=(w/len(ids)) if ids else 0
        for i in range(1,41):
            if PARAM_BUCKET[i]==bucket:
                p[i]["effective_weight"]=round(each*100,2) if p[i]["score"] is not None else 0;p[i]["weighted_points"]=round((p[i]["score"]/10)*each*100,2) if p[i]["score"] is not None else None
    return {"ticker":ticker,"name":safe(info.get("shortName") or info.get("longName"),ticker),"sector":safe(info.get("sector"),"N/A"),"price":round(price,2),"day_change":round(day,2),"health_score":score,"grade":grade,"recommendation":rec_out,"signal":signal,"conviction":conviction,"market_regime":market["market_regime"],"sector_health":sector_health,"lifecycle":lifecycle,"weight_profile":profile_name,"bucket_weights":{k:round(v*100,1) for k,v in weights.items()},"bucket_scores":{k:(round(v,2) if v is not None else None) for k,v in bucket_scores.items()},"params40":[p[i] for i in range(1,41)],"disqualifiers":disq,"low_confidence_params":low_conf,"upside_pct":round(upside,1) if upside is not None else None,"target_mean":round(target,2) if target is not None else None,"analyst_rec":rec,"ma50":round(ma50,2) if ma50 else None,"ma200":round(ma200,2) if ma200 else None,"fetched_at":datetime.now().strftime("%b %d %Y %I:%M %p"),"model_note":"Official GICS peer-median inputs are N/A until an authoritative peer feed is connected; affected buckets are renormalized."}

def _dummy_score(ticker,reason):
    return {"ticker":ticker,"name":ticker,"sector":"N/A","price":0,"day_change":0,"health_score":0,"grade":"?","recommendation":"Hold","signal":"HOLD","conviction":"Low","market_regime":"Neutral","sector_health":"Stable","lifecycle":"Unknown","weight_profile":"Neutral / Stable","bucket_weights":{},"bucket_scores":{},"params40":[],"disqualifiers":[],"low_confidence_params":[],"upside_pct":None,"target_mean":None,"analyst_rec":"none","ma50":None,"ma200":None,"fetched_at":datetime.now().strftime("%b %d %Y %I:%M %p"),"error":reason}

def score_stock(ticker):
    if not YF_AVAILABLE:return _dummy_score(ticker,"yfinance not installed")
    try:return _score_stock_core(ticker)
    except Exception as e:return _dummy_score(ticker,f"{type(e).__name__}: {e}")

def run_watchlist(tickers=None):
    tickers=tickers or DEFAULT_TICKERS;results=[]
    for t in tickers:
        print(f"  40-factor scoring {t}...");results.append(score_stock(t))
    return results

if __name__=="__main__":
    import sys
    for r in run_watchlist(sys.argv[1:] or DEFAULT_TICKERS):print(f"{r['ticker']:<6} {r['health_score']:>5.1f} {r['grade']:<2} {r['signal']:<10} {r['market_regime']}/{r['sector_health']} {r['lifecycle']}")
