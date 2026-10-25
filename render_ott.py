"""OTT recommendations tab for The Chai Ledger.

Primary source: Gadgets 360 entertainment release pages.
Supplement: current Korean drama calendar / official release pages.
"""
from __future__ import annotations

from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from html import escape
from urllib.request import Request, urlopen
import re

UA = "Mozilla/5.0 (compatible; ChaiLedger/4.0; +https://github.com/Chaimamdur-data/personal-news-paper)"

SOURCE_PAGES = [
    ("Series", "English/Hindi", "https://www.gadgets360.com/entertainment/new-web-series"),
    ("Movie", "Hindi", "https://www.gadgets360.com/entertainment/new-hindi-movies"),
    ("Movie", "Telugu", "https://www.gadgets360.com/entertainment/new-telugu-movies"),
    ("Movie", "English", "https://www.gadgets360.com/entertainment/new-english-movies"),
    ("Movie", "Hindi", "https://www.gadgets360.com/entertainment/upcoming-hindi-movies"),
    ("Movie", "Telugu", "https://www.gadgets360.com/entertainment/upcoming-telugu-movies"),
    ("Movie", "English", "https://www.gadgets360.com/entertainment/upcoming-english-movies"),
]

GENRES = [
    "Thriller","Mystery","Crime","Horror","Drama","Action","Adventure","Sci-Fi",
    "Fantasy","Comedy","Romance","History","Animation","Reality","Game Show"
]
PLATFORMS = ["Netflix","Prime Video","Amazon Prime Video","JioHotstar","Hotstar","SonyLIV","Zee5","ZEE5","Apple TV+","MX Player","Sun Nxt","Viki"]

# Current Korean titles are supplemental because Gadgets 360's main list is not a complete K-drama calendar.
KOREAN_CURRENT = [
    {
        "title":"Love in Disguise","date":"19 October 2026","type":"Series","language":"Korean",
        "genre":"Romance, Thriller","platform":"tvN","rating":None,
        "url":"https://www.soompi.com/article/1874726wpp/12-new-k-dramas-to-check-out-in-october-2026",
        "source":"Soompi","why":"Murder-suspect mystery with an undercover investigation."
    },
    {
        "title":"Dead-End Job","date":"30 October 2026","type":"Series","language":"Korean",
        "genre":"Mystery, Horror, Thriller","platform":"Netflix","rating":None,
        "url":"https://about.netflix.com/en/news/dead-end-job-sets-october-30-premiere-drops-teaser-trailer-and-poster",
        "source":"Netflix","why":"A strange high-paying job turns into a mystery-horror survival story."
    },
    {
        "title":"The Perfect Lie","date":"30 October 2026","type":"Series","language":"Korean",
        "genre":"Psychological Thriller","platform":"MBC","rating":None,
        "url":"https://www.soompi.com/article/1872302wpp/watch-yoo-yeon-seok-and-seo-hyun-jins-upcoming-drama-the-perfect-lie-confirms-premiere-date-with-glimpse-of-script-reading",
        "source":"Soompi","why":"Two people remember the same event differently, creating a truth-versus-lies psychological mystery."
    },
]

def _fetch(url):
    req=Request(url,headers={"User-Agent":UA,"Accept":"text/html,*/*"})
    with urlopen(req,timeout=24) as r:
        return r.read()

def _parse_date(text):
    m=re.search(r"\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+20\d{2})\b",text,re.I)
    if not m:return None
    try:return datetime.strptime(m.group(1),"%d %B %Y").date()
    except Exception:return None

def _rating(text):
    m=re.search(r"\((\d(?:\.\d)?)/5\)",text)
    if m:
        try:return float(m.group(1))
        except Exception:return None
    return None

def _guess_platform(text):
    lower=text.lower()
    for p in PLATFORMS:
        if p.lower() in lower:return p
    return None

def _guess_genre(text):
    found=[]
    low=text.lower()
    for g in GENRES:
        if g.lower() in low and g not in found:found.append(g)
    return ", ".join(found[:4]) if found else "Not listed"

def _language(default_lang,title,text):
    low=(title+" "+text).lower()
    if "telugu" in low:return "Telugu"
    if "hindi" in low:return "Hindi"
    if "korean" in low or "k-drama" in low:return "Korean"
    if default_lang=="English/Hindi":
        # Gadgets 360's web-series page mixes languages. Hindi names/platform context are not always explicit.
        return "English / Hindi"
    return default_lang

def _extract_items(kind,default_lang,url):
    try:soup=BeautifulSoup(_fetch(url),"html.parser")
    except Exception as exc:
        print(f"  ⚠️ OTT source skipped: {url} — {type(exc).__name__}: {exc}")
        return []
    out=[]
    headings=soup.find_all(["h3"])
    for h in headings:
        title=" ".join(h.stripped_strings).strip()
        if not title or len(title)>120 or title.lower() in {"trailers","latest tech news"}:continue
        link=h.find("a",href=True)
        href=link["href"] if link else url
        if href.startswith("/"):href="https://www.gadgets360.com"+href
        chunks=[]
        node=h
        for _ in range(18):
            node=node.find_next_sibling()
            if node is None:break
            if getattr(node,"name",None) in {"h2","h3"}:break
            txt=" ".join(node.stripped_strings).strip()
            if txt:chunks.append(txt)
        block=" ".join(chunks)
        d=_parse_date(block)
        if not d:continue
        # Nearby "Watch on" often sits before the title; look backwards too.
        prev=[]
        node=h
        for _ in range(5):
            node=node.find_previous_sibling()
            if node is None:break
            txt=" ".join(node.stripped_strings).strip()
            if txt:prev.append(txt)
        context=" ".join(reversed(prev))+" "+block
        platform=_guess_platform(context)
        theatrical=("book your tickets" in context.lower()) and not platform
        out.append({
            "title":title,"date_obj":d,"date":d.strftime("%d %b %Y"),"type":kind,
            "language":_language(default_lang,title,block),"genre":_guess_genre(block),
            "platform":platform or ("Theatrical / OTT TBA" if theatrical else "Platform TBA"),
            "rating":_rating(block),"url":href,"source":"Gadgets 360",
            "theatrical":theatrical,
        })
    return out

def _why(item):
    genre=item.get("genre","")
    if "Thriller" in genre or "Mystery" in genre or "Crime" in genre:
        return "High fit: mystery/crime/thriller elements match your preferred genres."
    if item.get("rating") and item["rating"]>=4.0:
        return "Strong rating makes this worth a look even outside your main thriller preference."
    return "New or upcoming title in one of your preferred languages."

def fetch_ott_recommendations():
    today=datetime.now(timezone.utc).date()
    start=today-timedelta(days=30);end=today+timedelta(days=30)
    items=[]
    seen=set()
    for kind,lang,url in SOURCE_PAGES:
        for x in _extract_items(kind,lang,url):
            key=(x["title"].lower(),x["date_obj"])
            if key in seen:continue
            seen.add(key);items.append(x)

    for x in KOREAN_CURRENT:
        try:d=datetime.strptime(x["date"],"%d %B %Y").date()
        except Exception:continue
        key=(x["title"].lower(),d)
        if key in seen:continue
        y=dict(x);y["date_obj"]=d;y["date"]=d.strftime("%d %b %Y");y["theatrical"]=False
        items.append(y);seen.add(key)

    # User preference: thrillers first; high ratings next; then recency.
    def fit(x):
        g=x.get("genre","").lower()
        thriller=any(k in g for k in ["thriller","mystery","crime","horror"])
        rating=x.get("rating")
        return (5 if thriller else 0)+(3 if rating is not None and rating>=4 else 0)+(1 if x.get("platform") not in {"Platform TBA","Theatrical / OTT TBA"} else 0)

    for x in items:
        x["fit_score"]=fit(x);x["why"]=x.get("why") or _why(x)

    recent=[x for x in items if start<=x["date_obj"]<=today]
    upcoming=[x for x in items if today<x["date_obj"]<=end]
    # Watch-now is stricter: OTT known + strong user rating OR thriller/mystery on a major platform.
    watch_now=[x for x in recent if not x.get("theatrical") and x.get("platform") not in {"Platform TBA","Theatrical / OTT TBA"} and (
        (x.get("rating") is not None and x["rating"]>=4.0) or
        any(k in x.get("genre","").lower() for k in ["thriller","mystery","crime"])
    )]
    watch_now.sort(key=lambda x:(x["fit_score"],x.get("rating") or 0,x["date_obj"]),reverse=True)
    recent.sort(key=lambda x:(x["fit_score"],x.get("rating") or 0,x["date_obj"]),reverse=True)
    upcoming.sort(key=lambda x:(x["fit_score"],x["date_obj"]),reverse=True)
    return {"today":today,"watch_now":watch_now[:12],"recent":recent[:24],"upcoming":upcoming[:24]}

def _rating_badge(x):
    r=x.get("rating")
    if r is None:return '<span class="ott-rating unrated">Not rated yet</span>'
    cls="great" if r>=4.0 else ("good" if r>=3.5 else "low")
    return f'<span class="ott-rating {cls}">★ {r:.1f}/5</span>'

def _card(x,compact=False):
    tags="".join(f'<span>{escape(t.strip())}</span>' for t in [x.get("language",""),x.get("type",""),x.get("genre","")] if t)
    cls="ott-card compact" if compact else "ott-card"
    return f"""
    <article class="{cls}">
      <div class="ott-card-top"><div class="ott-date">{escape(x['date'])}</div>{_rating_badge(x)}</div>
      <h3><a href="{escape(x['url'])}" target="_blank" rel="noopener">{escape(x['title'])}</a></h3>
      <div class="ott-platform">{escape(x.get('platform') or 'Platform TBA')}</div>
      <div class="ott-tags">{tags}</div>
      <p>{escape(x.get('why') or '')}</p>
      <div class="ott-source">{escape(x.get('source','Source'))} ↗</div>
    </article>"""

def render_ott_tab(data):
    watch=data["watch_now"];recent=data["recent"];upcoming=data["upcoming"];today=data["today"]
    lead=watch[0] if watch else (recent[0] if recent else None)
    lead_html=""
    if lead:
        lead_html=f"""
        <article class="ott-hero">
          <div><span class="ott-kicker">BEST MATCH NOW</span>{_rating_badge(lead)}</div>
          <h2><a href="{escape(lead['url'])}" target="_blank" rel="noopener">{escape(lead['title'])}</a></h2>
          <div class="ott-hero-meta">{escape(lead['date'])} · {escape(lead.get('platform') or 'Platform TBA')} · {escape(lead.get('language',''))} · {escape(lead.get('genre',''))}</div>
          <p>{escape(lead.get('why') or '')}</p>
          <a class="ott-open" href="{escape(lead['url'])}" target="_blank" rel="noopener">View details ↗</a>
        </article>"""
    watch_cards="".join(_card(x) for x in watch[1:9]) if watch else ""
    recent_cards="".join(_card(x,True) for x in recent[:18])
    upcoming_cards="".join(_card(x,True) for x in upcoming[:18])
    return f"""
<style>
.ott-page{{min-height:100vh;background:
radial-gradient(760px 420px at 12% -6%,rgba(52,210,123,.09),transparent 60%),
radial-gradient(760px 420px at 88% 0%,rgba(99,169,255,.08),transparent 58%),
#0e1116;color:#f2f5f7;padding:28px 22px 44px;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
.ott-shell{{max-width:1220px;margin:0 auto}}.ott-head{{display:flex;justify-content:space-between;gap:20px;align-items:flex-start;border-bottom:1px solid #2b323e;padding-bottom:18px}}
.ott-eyebrow{{font-size:9px;font-weight:850;letter-spacing:1px;color:#34d27b;text-transform:uppercase;margin-bottom:8px}}.ott-head h1{{font-size:36px;line-height:1;margin:0 0 8px;letter-spacing:-1.2px}}.ott-head p{{margin:0;max-width:800px;color:#94a0ad;font-size:12px;line-height:1.5}}.ott-asof{{font:650 10px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;color:#84909d;text-align:right;white-space:nowrap}}
.ott-lens{{display:flex;gap:7px;flex-wrap:wrap;margin:15px 0 18px}}.ott-lens span{{border:1px solid #2b323e;background:#161a21;color:#a8b3be;border-radius:999px;padding:7px 9px;font-size:9px;font-weight:750}}.ott-lens .hot{{color:#34d27b;border-color:rgba(52,210,123,.3);background:rgba(52,210,123,.07)}}
.ott-hero{{border:1px solid rgba(52,210,123,.28);background:linear-gradient(145deg,rgba(52,210,123,.07),#161a21 42%,#13171d);border-radius:24px;padding:22px;margin-bottom:12px;box-shadow:0 18px 52px rgba(0,0,0,.18)}}.ott-kicker{{display:inline-block;font-size:8px;font-weight:850;letter-spacing:.8px;color:#34d27b;margin-right:8px}}.ott-hero h2{{font-size:30px;line-height:1.05;margin:12px 0 8px;letter-spacing:-.7px}}.ott-hero h2 a,.ott-card h3 a{{text-decoration:none}}.ott-hero h2 a:hover,.ott-card h3 a:hover{{color:#c9f8dc}}.ott-hero-meta{{font:650 10px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;color:#9ba6b2}}.ott-hero p{{font-size:12px;line-height:1.5;color:#b6c0c9;max-width:760px}}.ott-open{{display:inline-flex;text-decoration:none;border:1px solid #35404c;background:#20262f;border-radius:999px;padding:9px 11px;font-size:10px;font-weight:800}}
.ott-section{{margin-top:24px}}.ott-section-head{{display:flex;justify-content:space-between;align-items:end;gap:12px;margin-bottom:10px}}.ott-section-head h2{{font-size:15px;margin:0}}.ott-section-head span{{font-size:9px;color:#73808c}}.ott-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:11px}}.ott-grid.compact{{grid-template-columns:repeat(4,minmax(0,1fr))}}
.ott-card{{border:1px solid #2b323e;background:linear-gradient(180deg,#161a21,#13171d);border-radius:18px;padding:13px;min-width:0}}.ott-card.compact{{padding:12px}}.ott-card-top{{display:flex;justify-content:space-between;gap:8px;align-items:center}}.ott-date{{font:700 9px/1 ui-monospace,SFMono-Regular,Menlo,monospace;color:#8f9aa6}}.ott-rating{{font:800 9px/1 ui-monospace,SFMono-Regular,Menlo,monospace;border-radius:999px;padding:5px 7px;border:1px solid #39424e}}.ott-rating.great{{color:#34d27b;border-color:rgba(52,210,123,.28);background:rgba(52,210,123,.07)}}.ott-rating.good{{color:#f4b740}}.ott-rating.low{{color:#ff856d}}.ott-rating.unrated{{color:#7f8a96}}
.ott-card h3{{font-size:16px;line-height:1.16;margin:10px 0 6px;letter-spacing:-.2px}}.ott-platform{{font-size:10px;font-weight:800;color:#63a9ff;margin-bottom:8px}}.ott-tags{{display:flex;gap:5px;flex-wrap:wrap}}.ott-tags span{{font-size:8px;color:#8c98a5;border:1px solid #29313b;background:#1b2028;border-radius:999px;padding:4px 6px}}.ott-card p{{font-size:10px;line-height:1.45;color:#9da9b5;margin:9px 0}}.ott-source{{font-size:8px;color:#687480;text-transform:uppercase;letter-spacing:.45px}}
.ott-note{{margin-top:22px;border-top:1px solid #2b323e;padding-top:11px;color:#6f7b87;font-size:9px;line-height:1.55}}
@media(max-width:950px){{.ott-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.ott-grid.compact{{grid-template-columns:repeat(3,minmax(0,1fr))}}}}
@media(max-width:700px){{.ott-page{{padding:20px 11px 34px}}.ott-head{{display:block}}.ott-head h1{{font-size:30px}}.ott-asof{{text-align:left;margin-top:10px}}.ott-grid,.ott-grid.compact{{grid-template-columns:1fr}}.ott-hero{{padding:17px}}.ott-hero h2{{font-size:25px}}}}
</style>
<section class="ott-page"><div class="ott-shell">
  <header class="ott-head"><div><div class="ott-eyebrow">The Chai Ledger / OTT Picks</div><h1>What to Watch</h1><p>Thrillers first. Hindi, Telugu, English and Korean. Recent 30 days + next 30 days, with dates, platforms and ratings when available.</p></div><div class="ott-asof">Window<br><strong>{(today-timedelta(days=30)).strftime('%b %d')} → {(today+timedelta(days=30)).strftime('%b %d')}</strong></div></header>
  <div class="ott-lens"><span class="hot">Thriller first</span><span>Hindi</span><span>Telugu</span><span>English</span><span>Korean</span><span>Good ratings prioritized</span></div>
  {lead_html}
  <section class="ott-section"><div class="ott-section-head"><h2>Best to watch now</h2><span>OTT known · thriller/high-rating bias</span></div><div class="ott-grid">{watch_cards or '<div class="ott-note">No additional strong matches found in the current 30-day window.</div>'}</div></section>
  <section class="ott-section"><div class="ott-section-head"><h2>Released in the last 30 days</h2><span>{len(recent)} relevant titles</span></div><div class="ott-grid compact">{recent_cards or '<div class="ott-note">No recent matches found.</div>'}</div></section>
  <section class="ott-section"><div class="ott-section-head"><h2>Coming in the next 30 days</h2><span>{len(upcoming)} upcoming titles</span></div><div class="ott-grid compact">{upcoming_cards or '<div class="ott-note">No dated upcoming matches found yet.</div>'}</div></section>
  <div class="ott-note">Primary release metadata comes from Gadgets 360. Korean picks are supplemented with current Soompi/official platform announcements. Ratings shown are source user ratings when available; “Not rated yet” is intentionally left unrated rather than guessed. Upcoming dates can change.</div>
</div></section>"""
