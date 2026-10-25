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
    ("Series", "Mixed", "https://www.gadgets360.com/entertainment/new-web-series"),
    ("Series", "Mixed", "https://www.gadgets360.com/entertainment/upcoming-web-series"),
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
PLATFORMS = ["Netflix","Prime Video","Amazon Prime Video","JioHotstar","Disney+ Hotstar","Hotstar","SonyLIV","Sony Liv","Zee5","ZEE5","Apple TV+","MX Player","Sun Nxt","Sun NXT","Aha","aha","Viki","Paramount+","Hulu","Max","HBO Max"]

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

def _series_language_map(soup):
    """Read Gadgets 360 language tables instead of guessing series language."""
    mapping={}
    for h in soup.find_all(["h2","h3"]):
        text=" ".join(h.stripped_strings).strip().lower()
        lang=None
        if "hindi web series" in text:lang="Hindi"
        elif "english web series" in text:lang="English"
        elif "telugu web series" in text:lang="Telugu"
        elif "korean web series" in text or "k-drama" in text:lang="Korean"
        if not lang:continue
        node=h.find_next()
        hops=0
        while node is not None and hops<180:
            if node is not h and getattr(node,"name",None) in {"h2","h3"}:
                break
            if getattr(node,"name",None)=="tr":
                cells=[" ".join(x.stripped_strings).strip() for x in node.find_all(["td","th"])]
                if cells and cells[0] and "web series" not in cells[0].lower():
                    mapping[cells[0].lower()]=lang
            node=node.find_next();hops+=1
    return mapping

def _language(default_lang,title,text,series_map=None):
    low=(title+" "+text).lower()
    if series_map and title.lower() in series_map:return series_map[title.lower()]
    if "telugu" in low:return "Telugu"
    if "hindi" in low:return "Hindi"
    if "korean" in low or "k-drama" in low:return "Korean"
    if default_lang in {"Hindi","Telugu","English","Korean"}:return default_lang
    return "English"

def _extract_items(kind,default_lang,url):
    try:soup=BeautifulSoup(_fetch(url),"html.parser")
    except Exception as exc:
        print(f"  ⚠️ OTT source skipped: {url} — {type(exc).__name__}: {exc}")
        return []
    out=[]
    series_map=_series_language_map(soup) if kind=="Series" else {}
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
            "language":_language(default_lang,title,block,series_map),"genre":_guess_genre(block),
            "platform":platform or ("OTT TBA" if theatrical else "Platform TBA"),
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
    items=[];seen=set()
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

    def fit(x):
        g=x.get("genre","").lower();rating=x.get("rating");lang=x.get("language")
        thriller=any(k in g for k in ["thriller","mystery","crime","horror"])
        # Hindi/Telugu: breadth matters. English/Korean: thriller preference gets a boost.
        preference=(4 if thriller and lang in {"English","Korean"} else (2 if thriller else 0))
        quality=3 if rating is not None and rating>=4.0 else (1 if rating is not None and rating>=3.5 else 0)
        ott=1 if x.get("platform") not in {"Platform TBA","OTT TBA"} else 0
        return preference+quality+ott

    for x in items:
        x["fit_score"]=fit(x);x["why"]=x.get("why") or _why(x)
        x["window"]="Recent" if start<=x["date_obj"]<=today else ("Upcoming" if today<x["date_obj"]<=end else "Outside")

    items=[x for x in items if x["window"]!="Outside" and x.get("language") in {"Hindi","Telugu","English","Korean"}]
    items.sort(key=lambda x:(x["type"],x["window"]=="Recent",x["fit_score"],x.get("rating") or 0,x["date_obj"]),reverse=True)

    movies=[x for x in items if x["type"]=="Movie"]
    series=[x for x in items if x["type"]=="Series"]
    return {
        "today":today,
        "items":items,
        "movies":movies,
        "series":series,
        "movie_recent":[x for x in movies if x["window"]=="Recent"],
        "movie_upcoming":[x for x in movies if x["window"]=="Upcoming"],
        "series_recent":[x for x in series if x["window"]=="Recent"],
        "series_upcoming":[x for x in series if x["window"]=="Upcoming"],
    }

def _rating_badge(x):
    r=x.get("rating")
    if r is None:return '<span class="ott-rating unrated">Not rated yet</span>'
    cls="great" if r>=4.0 else ("good" if r>=3.5 else "low")
    return f'<span class="ott-rating {cls}">★ {r:.1f}/5</span>'

def _card(x,compact=False):
    tags="".join(f'<span>{escape(t.strip())}</span>' for t in [x.get("genre","")] if t)
    cls="ott-card compact" if compact else "ott-card"
    platform=x.get("platform") or "Platform TBA"
    window=x.get("window","")
    return f"""
    <article class="{cls}" data-ott-type="{escape(x.get('type',''))}" data-ott-lang="{escape(x.get('language',''))}" data-ott-window="{escape(window)}" data-ott-platform="{escape(platform)}">
      <div class="ott-card-top"><div class="ott-date">{escape(x['date'])}</div>{_rating_badge(x)}</div>
      <h3><a href="{escape(x['url'])}" target="_blank" rel="noopener">{escape(x['title'])}</a></h3>
      <div class="ott-platform"><span class="ott-platform-label">OTT</span>{escape(platform)}</div>
      <div class="ott-card-sub">{escape(x.get('language',''))} · {escape(x.get('type',''))} · {escape(window)}</div>
      <div class="ott-tags">{tags}</div>
      <p>{escape(x.get('why') or '')}</p>
      <div class="ott-source">{escape(x.get('source','Source'))} ↗</div>
    </article>"""

def render_ott_tab(data):
    today=data["today"];items=data["items"]
    movie_recent=data["movie_recent"];movie_upcoming=data["movie_upcoming"]
    series_recent=data["series_recent"];series_upcoming=data["series_upcoming"]

    movie_recent_html="".join(_card(x,True) for x in movie_recent)
    movie_upcoming_html="".join(_card(x,True) for x in movie_upcoming)
    series_recent_html="".join(_card(x,True) for x in series_recent)
    series_upcoming_html="".join(_card(x,True) for x in series_upcoming)

    platforms=sorted({x.get("platform") for x in items if x.get("platform") and x.get("platform") not in {"Platform TBA","OTT TBA"}})
    platform_options='<option value="All">All platforms</option>'+''.join(f'<option value="{escape(p)}">{escape(p)}</option>' for p in platforms)

    return f"""
<style>
.ott-page{{min-height:100vh;background:
radial-gradient(760px 420px at 12% -6%,rgba(52,210,123,.09),transparent 60%),
radial-gradient(760px 420px at 88% 0%,rgba(99,169,255,.08),transparent 58%),
#0e1116;color:#f2f5f7;padding:28px 22px 44px;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
.ott-shell{{max-width:1220px;margin:0 auto}}.ott-head{{display:flex;justify-content:space-between;gap:20px;align-items:flex-start;border-bottom:1px solid #2b323e;padding-bottom:18px}}
.ott-eyebrow{{font-size:9px;font-weight:850;letter-spacing:1px;color:#34d27b;text-transform:uppercase;margin-bottom:8px}}.ott-head h1{{font-size:36px;line-height:1;margin:0 0 8px;letter-spacing:-1.2px}}.ott-head p{{margin:0;max-width:820px;color:#94a0ad;font-size:12px;line-height:1.5}}.ott-asof{{font:650 10px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;color:#84909d;text-align:right;white-space:nowrap}}
.ott-toolbar{{display:flex;gap:10px;align-items:center;justify-content:space-between;margin:15px 0 8px;flex-wrap:wrap}}.ott-toggle-group{{display:flex;gap:6px;flex-wrap:wrap}}.ott-filter{{border:1px solid #2b323e;background:#161a21;color:#93a0ad;border-radius:999px;padding:8px 10px;font-size:9px;font-weight:800;cursor:pointer}}.ott-filter.active{{background:#27312c;color:#34d27b;border-color:rgba(52,210,123,.34)}}.ott-select{{border:1px solid #2b323e;background:#161a21;color:#e7edf1;border-radius:999px;padding:8px 28px 8px 10px;font-size:9px;font-weight:750}}
.ott-summary{{font:650 9px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace;color:#74808c;margin:8px 0 18px}}
.ott-section{{margin-top:25px}}.ott-section.hidden{{display:none}}.ott-section-head{{display:flex;justify-content:space-between;align-items:end;gap:12px;margin-bottom:10px;border-bottom:1px solid #2b323e;padding-bottom:8px}}.ott-section-head h2{{font-size:17px;margin:0}}.ott-section-head span{{font-size:9px;color:#73808c}}.ott-subhead{{font-size:10px;color:#63a9ff;text-transform:uppercase;letter-spacing:.65px;margin:17px 0 8px;font-weight:850}}
.ott-grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:11px}}.ott-card{{border:1px solid #2b323e;background:linear-gradient(180deg,#161a21,#13171d);border-radius:18px;padding:12px;min-width:0;transition:.16s ease}}.ott-card:hover{{border-color:#414b59;transform:translateY(-1px)}}.ott-card.filtered-out{{display:none}}
.ott-card-top{{display:flex;justify-content:space-between;gap:8px;align-items:center}}.ott-date{{font:700 9px/1 ui-monospace,SFMono-Regular,Menlo,monospace;color:#8f9aa6}}.ott-rating{{font:800 9px/1 ui-monospace,SFMono-Regular,Menlo,monospace;border-radius:999px;padding:5px 7px;border:1px solid #39424e}}.ott-rating.great{{color:#34d27b;border-color:rgba(52,210,123,.28);background:rgba(52,210,123,.07)}}.ott-rating.good{{color:#f4b740}}.ott-rating.low{{color:#ff856d}}.ott-rating.unrated{{color:#7f8a96}}
.ott-card h3{{font-size:15px;line-height:1.16;margin:10px 0 7px;letter-spacing:-.2px}}.ott-card h3 a{{text-decoration:none}}.ott-card h3 a:hover{{color:#c9f8dc}}.ott-platform{{display:flex;align-items:center;gap:6px;font-size:11px;font-weight:850;color:#63a9ff;margin-bottom:6px}}.ott-platform-label{{font-size:7px;letter-spacing:.6px;color:#07131d;background:#63a9ff;border-radius:999px;padding:4px 5px}}.ott-card-sub{{font:650 8px/1.35 ui-monospace,SFMono-Regular,Menlo,monospace;color:#7f8b98;margin-bottom:7px}}.ott-tags{{display:flex;gap:5px;flex-wrap:wrap}}.ott-tags span{{font-size:8px;color:#8c98a5;border:1px solid #29313b;background:#1b2028;border-radius:999px;padding:4px 6px}}.ott-card p{{font-size:9.5px;line-height:1.45;color:#9da9b5;margin:8px 0}}.ott-source{{font-size:8px;color:#687480;text-transform:uppercase;letter-spacing:.45px}}
.ott-empty{{display:none;border:1px solid #2b323e;border-radius:16px;padding:20px;color:#7c8894;font-size:10px}}.ott-note{{margin-top:22px;border-top:1px solid #2b323e;padding-top:11px;color:#6f7b87;font-size:9px;line-height:1.55}}
@media(max-width:1000px){{.ott-grid{{grid-template-columns:repeat(3,minmax(0,1fr))}}}}@media(max-width:760px){{.ott-page{{padding:20px 11px 34px}}.ott-head{{display:block}}.ott-head h1{{font-size:30px}}.ott-asof{{text-align:left;margin-top:10px}}.ott-toolbar{{align-items:flex-start;flex-direction:column}}.ott-select{{width:100%}}.ott-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}@media(max-width:500px){{.ott-grid{{grid-template-columns:1fr}}}}
@media(prefers-reduced-motion:reduce){{.ott-card{{transition:none}}}}
</style>
<section class="ott-page"><div class="ott-shell">
  <header class="ott-head"><div><div class="ott-eyebrow">The Chai Ledger / OTT Picks</div><h1>OTT Movies + Web Series</h1><p>Comprehensive 60-day window: releases from the last 30 days plus the next 30 days. Hindi and Telugu include good titles across genres; English and Korean put extra weight on thrillers, mysteries and crime.</p></div><div class="ott-asof">Window<br><strong>{(today-timedelta(days=30)).strftime('%b %d')} → {(today+timedelta(days=30)).strftime('%b %d')}</strong></div></header>

  <div class="ott-toolbar">
    <div class="ott-toggle-group" id="ott-type-filters"><button class="ott-filter active" data-ott-type-filter="All">All</button><button class="ott-filter" data-ott-type-filter="Movie">Movies</button><button class="ott-filter" data-ott-type-filter="Series">Web Series</button></div>
    <div class="ott-toggle-group" id="ott-lang-filters"><button class="ott-filter active" data-ott-lang-filter="All">All languages</button><button class="ott-filter" data-ott-lang-filter="Hindi">Hindi</button><button class="ott-filter" data-ott-lang-filter="Telugu">Telugu</button><button class="ott-filter" data-ott-lang-filter="English">English</button><button class="ott-filter" data-ott-lang-filter="Korean">Korean</button></div>
    <select class="ott-select" id="ott-window-filter"><option value="All">Last + next 30 days</option><option value="Recent">Released · last 30 days</option><option value="Upcoming">Coming · next 30 days</option></select>
    <select class="ott-select" id="ott-platform-filter">{platform_options}</select>
  </div>
  <div class="ott-summary" id="ott-summary">{len(items)} titles · OTT platform shown when known · strong ratings rise to the top</div>

  <section class="ott-section" data-section-type="Movie"><div class="ott-section-head"><h2>Movies</h2><span>{len(data['movies'])} titles</span></div>
    <div class="ott-subhead">Released in the last 30 days</div><div class="ott-grid">{movie_recent_html}</div>
    <div class="ott-subhead">Coming in the next 30 days</div><div class="ott-grid">{movie_upcoming_html}</div>
  </section>

  <section class="ott-section" data-section-type="Series"><div class="ott-section-head"><h2>Web Series</h2><span>{len(data['series'])} titles</span></div>
    <div class="ott-subhead">Released in the last 30 days</div><div class="ott-grid">{series_recent_html}</div>
    <div class="ott-subhead">Coming in the next 30 days</div><div class="ott-grid">{series_upcoming_html}</div>
  </section>

  <div class="ott-empty" id="ott-empty">No titles match these filters.</div>
  <div class="ott-note">Primary release metadata comes from Gadgets 360’s movie and web-series calendars. Korean series are supplemented with current Soompi/official platform announcements. OTT platform is shown when the source identifies it; theatrical releases without a confirmed streaming home show <b>OTT TBA</b>. Ratings are source user ratings, not IMDb scores. Upcoming dates and platforms can change.</div>
</div></section>
<script>
(()=>{{
 let type='All',lang='All',windowF='All',platform='All';
 const cards=[...document.querySelectorAll('.ott-card')],sections=[...document.querySelectorAll('.ott-section')],summary=document.getElementById('ott-summary'),empty=document.getElementById('ott-empty');
 function apply(){{
   let n=0;
   cards.forEach(c=>{{
     const show=(type==='All'||c.dataset.ottType===type)&&(lang==='All'||c.dataset.ottLang===lang)&&(windowF==='All'||c.dataset.ottWindow===windowF)&&(platform==='All'||c.dataset.ottPlatform===platform);
     c.classList.toggle('filtered-out',!show);if(show)n++;
   }});
   sections.forEach(s=>{{const visible=[...s.querySelectorAll('.ott-card')].some(c=>!c.classList.contains('filtered-out'));s.classList.toggle('hidden',!visible)}});
   summary.textContent=n+' matching titles · OTT platform shown when known';
   empty.style.display=n?'none':'block';
 }}
 document.querySelectorAll('[data-ott-type-filter]').forEach(b=>b.onclick=()=>{{document.querySelectorAll('[data-ott-type-filter]').forEach(x=>x.classList.toggle('active',x===b));type=b.dataset.ottTypeFilter;apply()}});
 document.querySelectorAll('[data-ott-lang-filter]').forEach(b=>b.onclick=()=>{{document.querySelectorAll('[data-ott-lang-filter]').forEach(x=>x.classList.toggle('active',x===b));lang=b.dataset.ottLangFilter;apply()}});
 document.getElementById('ott-window-filter').onchange=e=>{{windowF=e.target.value;apply()}};
 document.getElementById('ott-platform-filter').onchange=e=>{{platform=e.target.value;apply()}};
 apply();
}})();
</script>"""
