from pathlib import Path
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import escape
import hashlib
import json
import os
import re
import ssl
import urllib.request
from urllib.error import HTTPError, URLError

import feedparser
import yaml
from bs4 import BeautifulSoup

from stock_health import run_watchlist
from render_stocks import render_stock_section

CONFIG_FILE = "config.yml"
OUTPUT_FILE = "index.html"
NEWS_WINDOW_HOURS = 24
ssl._create_default_https_context = ssl._create_unverified_context

TAB_ICONS = {
    "ap-telangana": "◆",
    "india-neighbors": "◎",
    "us": "★",
    "ai-data": "⌘",
    "sports": "●",
    "entertainment": "✦",
}

PRIORITY_TERMS = {
    "ap-telangana": ["andhra", "telangana", "naidu", "pawan", "jagan", "revanth", "kcr", "ktr", "tdp", "ysrcp", "brs"],
    "india-neighbors": ["pakistan", "china", "bangladesh", "nepal", "sri lanka", "maldives", "border", "diplomatic", "foreign", "modi"],
    "us": ["white house", "congress", "supreme court", "economy", "inflation", "jobs", "election", "policy", "fed"],
    "ai-data": ["agent", "agentic", "multi-agent", "mcp", "model context protocol", "tool use", "reasoning", "rag", "inference", "llm", "embedding", "vector", "ai workflow", "enterprise ai"],
    "sports": ["cricket", "india", "icc", "ipl", "test", "odi", "t20", "tennis", "atp", "wta", "grand slam"],
    "entertainment": ["telugu", "tollywood", "bollywood", "movie", "film", "actor", "actress", "director", "streaming", "celebrity"],
}

AI_REQUIRED_TERMS = [
    "agent", "agentic", "multi-agent", "mcp", "model context protocol", "tool use",
    "reasoning model", "llm", "rag", "retrieval", "vector", "embedding", "inference",
    "ai workflow", "ai coding", "foundation model", "enterprise ai", "ai infrastructure",
]


def clean_text(value, limit=360):
    if not value:
        return ""
    soup = BeautifulSoup(value, "html.parser")
    text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0] + "…"
    return text


def entry_time(entry):
    for key in ("published", "updated", "created"):
        raw = entry.get(key)
        if not raw:
            continue
        try:
            dt = parsedate_to_datetime(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            pass
    for key in ("published_parsed", "updated_parsed"):
        parsed = entry.get(key)
        if parsed:
            try:
                return datetime(*parsed[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def time_ago(dt):
    if not dt:
        return "fresh"
    delta = datetime.now(timezone.utc) - dt
    mins = max(0, int(delta.total_seconds() // 60))
    if mins < 60:
        return f"{mins}m"
    return f"{mins // 60}h"


def source_name(entry, feed_title):
    src = entry.get("source")
    if isinstance(src, dict) and src.get("title"):
        return clean_text(src.get("title"), 40)
    title = clean_text(entry.get("title", ""), 220)
    if " - " in title:
        tail = title.rsplit(" - ", 1)[1].strip()
        if 1 < len(tail) < 45:
            return tail
    return clean_text(feed_title or "Source", 40)


def normalized_title(title):
    base = title.lower()
    if " - " in base:
        base = base.rsplit(" - ", 1)[0]
    return re.sub(r"[^a-z0-9]+", " ", base).strip()


def extract_image(entry):
    for key in ("media_content", "media_thumbnail"):
        items = entry.get(key, []) or []
        for item in items:
            if isinstance(item, dict):
                url = item.get("url")
                if url and url.startswith("http"):
                    return url
    for item in entry.get("enclosures", []) or []:
        if isinstance(item, dict):
            url = item.get("href") or item.get("url")
            mime = item.get("type", "")
            if url and url.startswith("http") and ("image" in mime or not mime):
                return url
    raw = entry.get("summary", "") or entry.get("description", "")
    if raw:
        try:
            img = BeautifulSoup(raw, "html.parser").find("img")
            if img and img.get("src", "").startswith("http"):
                return img.get("src")
        except Exception:
            pass
    return ""


def fetch_feed(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; ChaiLedger/3.0; +https://github.com/Chaimamdur-data/personal-news-paper)",
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
        },
    )
    with urllib.request.urlopen(request, timeout=22) as response:
        return feedparser.parse(response.read())


def fallback_simple_take(story):
    summary = story.get("summary", "")
    if not summary:
        return "This is a new AI development worth watching because it may change how people build or use AI systems."
    first = re.split(r"(?<=[.!?])\s+", summary)[0]
    first = clean_text(first, 180)
    return f"In simple terms: {first}"


def simplify_ai_stories(stories):
    for story in stories:
        story["simple_take"] = fallback_simple_take(story)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or not stories:
        return

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        payload = [
            {"id": i, "title": s["title"], "summary": s["summary"][:700]}
            for i, s in enumerate(stories[:25])
        ]
        prompt = (
            "You are an AI teacher for a 10th-grade student. For each news item below, write ONE short, plain-English explanation, "
            "maximum 28 words. Explain what happened and why it matters. Avoid hype, jargon, investment advice, and unsupported claims. "
            "Return ONLY valid JSON as an array of objects with keys id and simple.\n\n"
            + json.dumps(payload, ensure_ascii=False)
        )
        response = model.generate_content(prompt)
        text = (response.text or "").strip()
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I | re.S).strip()
        rows = json.loads(text)
        for row in rows:
            idx = row.get("id")
            simple = clean_text(row.get("simple", ""), 220)
            if isinstance(idx, int) and 0 <= idx < len(stories) and simple:
                stories[idx]["simple_take"] = simple
    except Exception as exc:
        print(f"  ⚠️ AI simplifier fallback used — {type(exc).__name__}: {exc}")


def fetch_tab(tab, max_articles=25):
    stories = []
    seen = set()
    terms = PRIORITY_TERMS.get(tab["slug"], [])
    now = datetime.now(timezone.utc)

    for feed_url in tab.get("feeds", []):
        try:
            parsed = fetch_feed(feed_url)
            if not parsed.entries:
                print(f"  ⚠️ No entries: {feed_url}")
                continue
            feed_title = parsed.feed.get("title", "")
            for entry in parsed.entries[:50]:
                title = clean_text(entry.get("title", ""), 220)
                link = entry.get("link", "")
                if not title or not link:
                    continue

                published = entry_time(entry)
                if not published:
                    continue
                age_hours = (now - published).total_seconds() / 3600
                if age_hours < -2 or age_hours > NEWS_WINDOW_HOURS:
                    continue

                summary = clean_text(entry.get("summary", entry.get("description", "")), 360)
                searchable = f"{title} {summary}".lower()
                if tab["slug"] == "ai-data" and not any(term in searchable for term in AI_REQUIRED_TERMS):
                    continue

                key = normalized_title(title)
                digest = hashlib.md5(key.encode()).hexdigest()
                if digest in seen:
                    continue
                seen.add(digest)

                if not summary:
                    summary = "Open the story for the full report and context."
                priority = sum(1 for term in terms if term in searchable)
                stories.append({
                    "title": title,
                    "link": link,
                    "summary": summary,
                    "source": source_name(entry, feed_title),
                    "published": published,
                    "priority": priority,
                    "image": extract_image(entry),
                })
        except (HTTPError, URLError, TimeoutError) as exc:
            print(f"  ⚠️ Feed skipped: {feed_url} — {exc}")
        except Exception as exc:
            print(f"  ⚠️ Feed failed: {feed_url} — {type(exc).__name__}: {exc}")

    for story in stories:
        age_hours = max(0.0, (now - story["published"]).total_seconds() / 3600)
        story["rank"] = story["priority"] * 8 - age_hours / 24

    stories.sort(key=lambda s: (s["rank"], s["published"]), reverse=True)
    stories = stories[:max_articles]
    if tab["slug"] == "ai-data":
        simplify_ai_stories(stories)
    return stories


def strip_source_from_title(title, source):
    suffix = f" - {source}"
    if source and title.lower().endswith(suffix.lower()):
        return title[:-len(suffix)].strip()
    return title


def render_story_meta(story):
    return f'<span class="story-source">{escape(story["source"])}</span><span class="story-age">{escape(time_ago(story["published"]))} ago</span>'


def image_html(story, css_class):
    image = story.get("image", "")
    if not image:
        return ""
    return f'<a class="{css_class}" href="{escape(story["link"])}" target="_blank" rel="noopener"><img src="{escape(image)}" alt="" loading="lazy" referrerpolicy="no-referrer"></a>'


def simple_take_html(tab, story):
    if tab["slug"] != "ai-data":
        return ""
    take = escape(story.get("simple_take", fallback_simple_take(story)))
    return f'<div class="simple-take"><strong>SIMPLE TAKE</strong> {take}</div>'


def render_news_tab(tab, stories):
    title = escape(tab["title"])
    kicker = escape(tab.get("kicker", ""))
    icon = TAB_ICONS.get(tab["slug"], "◆")

    if not stories:
        body = '<div class="empty-news">No qualifying stories were published in the last 24 hours. The next hourly refresh will try again.</div>'
    else:
        lead = stories[0]
        lead_title = escape(strip_source_from_title(lead["title"], lead["source"]))
        lead_html = f"""
        <article class="lead-story">
          {image_html(lead, 'lead-image')}
          <div class="story-meta">{render_story_meta(lead)}</div>
          <h2><a href="{escape(lead['link'])}" target="_blank" rel="noopener">{lead_title}</a></h2>
          <p>{escape(lead['summary'])}</p>
          {simple_take_html(tab, lead)}
          <a class="read-link" href="{escape(lead['link'])}" target="_blank" rel="noopener">Read full story →</a>
        </article>"""

        side_html = ""
        for story in stories[1:4]:
            story_title = escape(strip_source_from_title(story["title"], story["source"]))
            side_html += f"""
            <article class="side-story">
              {image_html(story, 'side-image')}
              <div class="story-meta">{render_story_meta(story)}</div>
              <h3><a href="{escape(story['link'])}" target="_blank" rel="noopener">{story_title}</a></h3>
              <p>{escape(story['summary'])}</p>
              {simple_take_html(tab, story)}
            </article>"""

        briefs_html = ""
        for i, story in enumerate(stories[4:25], start=5):
            story_title = escape(strip_source_from_title(story["title"], story["source"]))
            briefs_html += f"""
            <article class="brief-story">
              {image_html(story, 'brief-image')}
              <div class="brief-head"><span class="brief-num">{i:02d}</span><div class="story-meta">{render_story_meta(story)}</div></div>
              <h3><a href="{escape(story['link'])}" target="_blank" rel="noopener">{story_title}</a></h3>
              {simple_take_html(tab, story)}
            </article>"""

        body = f"""
        <div class="news-front-grid">
          {lead_html}
          <div class="side-stack">{side_html}</div>
        </div>
        <div class="briefs-title"><span>THE REST OF THE LAST 24 HOURS</span><span>{len(stories)} curated stories</span></div>
        <div class="briefs-grid">{briefs_html}</div>"""

    special = ""
    if tab["slug"] == "ai-data":
        special = """
        <div class="learning-ribbon">
          <strong>AI LEARNING LENS</strong>
          <span>Agents · Agentic AI · MCP · reasoning · RAG · AI workflows · new model and data trends — explained in simple language.</span>
        </div>"""
    elif tab["slug"] == "sports":
        special = '<div class="learning-ribbon"><strong>SPORTS LENS</strong><span>Cricket first · tennis second · only stories from the last 24 hours</span></div>'
    elif tab["slug"] == "entertainment":
        special = '<div class="learning-ribbon"><strong>FUN LENS</strong><span>Telugu cinema first · Bollywood · Hollywood · streaming · celebrity buzz · last 24 hours only</span></div>'

    return f"""
    <section class="news-page">
      <header class="news-masthead">
        <div>
          <div class="news-eyebrow">{icon} THE CHAI LEDGER / {title.upper()}</div>
          <h1>{title}</h1>
          <p>{kicker}</p>
        </div>
        <div class="news-date">Rolling 24h<br><strong>{datetime.now().strftime('%b %d, %Y')}</strong></div>
      </header>
      {special}
      {body}
      <footer class="news-footer">Only stories with a publish time inside the last 24 hours are eligible. Images appear when the source feed supplies one. Headlines link to the source.</footer>
    </section>"""


def render_shell(stock_html, news_html):
    tabs = [
        ("markets", "Markets"),
        ("ap-telangana", "AP + Telangana"),
        ("india-neighbors", "India + Neighbors"),
        ("us", "U.S."),
        ("ai-data", "AI + Data"),
        ("sports", "Sports"),
        ("entertainment", "Movies + Gossip"),
    ]
    nav = "".join(
        f'<button class="ledger-tab-btn{" active" if slug == "markets" else ""}" data-tab="{slug}">{escape(label)}</button>'
        for slug, label in tabs
    )
    panels = f'<div class="ledger-tab-panel active" id="tab-markets">{stock_html}</div>'
    panels += "".join(f'<div class="ledger-tab-panel" id="tab-{slug}">{html}</div>' for slug, html in news_html.items())

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>The Chai Ledger</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="3600">
<style>
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0;background:#e9e4da;color:#171713}}
body{{min-height:100vh}}
a{{color:inherit}}
.ledger-tabs-wrap{{position:sticky;top:0;z-index:500;background:#171713;border-bottom:1px solid #3d3b35;box-shadow:0 4px 12px rgba(0,0,0,.16)}}
.ledger-tabs{{max-width:1180px;margin:0 auto;display:flex;overflow-x:auto;scrollbar-width:none;padding:0 8px}}
.ledger-tabs::-webkit-scrollbar{{display:none}}
.ledger-tab-btn{{appearance:none;border:0;background:transparent;color:#d7d0c3;font:700 11px/1 Arial,sans-serif;text-transform:uppercase;letter-spacing:.45px;padding:14px 15px 12px;white-space:nowrap;border-bottom:3px solid transparent;cursor:pointer}}
.ledger-tab-btn:hover{{color:#fff}}
.ledger-tab-btn.active{{color:#fff;border-bottom-color:#c79c4b;background:#24231f}}
.ledger-tab-panel{{display:none}}
.ledger-tab-panel.active{{display:block}}
.news-page{{max-width:1180px;margin:0 auto;background:#f3ede2;min-height:100vh;padding:24px 28px 36px;font-family:Georgia,'Times New Roman',serif}}
.news-masthead{{display:flex;justify-content:space-between;gap:24px;align-items:flex-start;border-bottom:3px double #24221e;padding-bottom:13px;margin-bottom:16px}}
.news-eyebrow{{font:700 9px/1.2 Arial,sans-serif;letter-spacing:.8px;color:#6e675b;margin-bottom:7px}}
.news-masthead h1{{font-size:40px;line-height:.95;margin:0 0 7px;letter-spacing:-1.1px}}
.news-masthead p{{font-size:11px;font-style:italic;color:#6e675b;margin:0;max-width:760px}}
.news-date{{text-align:right;font:9px/1.5 Arial,sans-serif;white-space:nowrap}}
.learning-ribbon{{display:flex;gap:9px;align-items:center;border-top:1px solid #24221e;border-bottom:1px solid #24221e;padding:7px 0;margin-bottom:18px;font:9px/1.4 Arial,sans-serif}}
.learning-ribbon strong{{font-size:8px;letter-spacing:.7px;background:#171713;color:#f3ede2;padding:4px 6px}}
.news-front-grid{{display:grid;grid-template-columns:1.35fr .85fr;border-top:1px solid #24221e;border-bottom:1px solid #24221e}}
.lead-story{{padding:18px 20px 20px 0;border-right:1px solid #716b61}}
.lead-image,.side-image,.brief-image{{display:block;overflow:hidden;background:#ddd5c7}}
.lead-image{{height:320px;margin-bottom:13px}}
.side-image{{height:120px;margin-bottom:8px}}
.brief-image{{height:110px;margin-bottom:9px}}
.lead-image img,.side-image img,.brief-image img{{width:100%;height:100%;object-fit:cover;display:block}}
.story-meta{{display:flex;gap:7px;align-items:center;font:8px/1.2 Arial,sans-serif;text-transform:uppercase;letter-spacing:.35px;margin-bottom:7px}}
.story-source{{font-weight:800;color:#674e25}}
.story-age{{color:#777065}}
.lead-story h2{{font-size:30px;line-height:1.02;margin:0 0 11px;letter-spacing:-.6px}}
.lead-story h2 a,.side-story h3 a,.brief-story h3 a{{text-decoration:none}}
.lead-story h2 a:hover,.side-story h3 a:hover,.brief-story h3 a:hover{{text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:2px}}
.lead-story p{{font-size:13px;line-height:1.5;margin:0 0 13px;color:#4e4941}}
.read-link{{font:700 9px/1 Arial,sans-serif;text-transform:uppercase;letter-spacing:.4px;text-decoration:none;border-bottom:1px solid #171713;padding-bottom:2px}}
.side-stack{{padding-left:18px}}
.side-story{{padding:14px 0;border-bottom:1px solid #a59e92}}
.side-story:last-child{{border-bottom:0}}
.side-story h3{{font-size:17px;line-height:1.1;margin:0 0 7px}}
.side-story p{{font-size:10.5px;line-height:1.4;color:#5d574e;margin:0}}
.simple-take{{margin:8px 0 10px;padding:8px 9px;background:#e6ddcd;border-left:3px solid #8b6d34;font:10px/1.42 Arial,sans-serif;color:#3f3b34}}
.simple-take strong{{font-size:8px;letter-spacing:.45px;margin-right:4px}}
.briefs-title{{display:flex;justify-content:space-between;align-items:center;border-bottom:2px solid #24221e;padding:18px 0 6px;font:700 8px/1 Arial,sans-serif;letter-spacing:.65px}}
.briefs-title span:last-child{{font-weight:400;color:#777065}}
.briefs-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));column-gap:20px}}
.brief-story{{border-bottom:1px solid #b5ada0;padding:13px 0}}
.brief-head{{display:flex;align-items:center;gap:8px}}
.brief-num{{font-size:22px;line-height:1;color:#b9ae9c;font-weight:700}}
.brief-story h3{{font-size:14px;line-height:1.18;margin:5px 0 0}}
.empty-news{{border:1px solid #25231f;padding:35px;text-align:center;font-style:italic;color:#6e675b}}
.news-footer{{border-top:2px solid #24221e;margin-top:24px;padding-top:8px;font:8px/1.45 Arial,sans-serif;color:#746d61}}
@media(max-width:900px){{.briefs-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}
@media(max-width:760px){{
  .ledger-tab-btn{{padding:12px 11px 10px;font-size:9px}}
  .news-page{{padding:18px 14px 28px}}
  .news-masthead h1{{font-size:31px}}
  .news-masthead p{{font-size:10px}}
  .news-front-grid{{grid-template-columns:1fr}}
  .lead-story{{padding:15px 0;border-right:0;border-bottom:1px solid #716b61}}
  .lead-story h2{{font-size:25px}}
  .lead-image{{height:220px}}
  .side-stack{{padding-left:0}}
  .briefs-grid{{grid-template-columns:1fr}}
  .learning-ribbon{{align-items:flex-start;flex-direction:column}}
}}
</style>
</head>
<body>
<div class="ledger-tabs-wrap"><nav class="ledger-tabs">{nav}</nav></div>
{panels}
<script>
(function(){{
  const buttons=[...document.querySelectorAll('.ledger-tab-btn')];
  const panels=[...document.querySelectorAll('.ledger-tab-panel')];
  function show(slug, updateHash=true){{
    buttons.forEach(b=>b.classList.toggle('active',b.dataset.tab===slug));
    panels.forEach(p=>p.classList.toggle('active',p.id==='tab-'+slug));
    if(updateHash) history.replaceState(null,'','#'+slug);
    window.scrollTo({{top:0,behavior:'instant'}});
  }}
  buttons.forEach(b=>b.addEventListener('click',()=>show(b.dataset.tab)));
  const requested=(location.hash||'').replace('#','');
  if(buttons.some(b=>b.dataset.tab===requested)) show(requested,false);
}})();
</script>
</body>
</html>"""


def main():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    stock_tickers = config["site"].get("stock_tickers", [])
    print(f"Fetching stock health for {len(stock_tickers)} tickers...")
    stock_data = run_watchlist(stock_tickers)
    stock_html = render_stock_section(stock_data)

    max_articles = config["site"].get("max_articles_per_topic", 25)
    news_html = {}
    for tab in config.get("news_tabs", []):
        print(f"Fetching news tab: {tab['title']}")
        stories = fetch_tab(tab, max_articles=max_articles)
        print(f"  ✅ {len(stories)} stories inside last {NEWS_WINDOW_HOURS}h")
        news_html[tab["slug"]] = render_news_tab(tab, stories)

    html = render_shell(stock_html, news_html)
    Path(OUTPUT_FILE).write_text(html, encoding="utf-8")
    print(f"✅ Done → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
