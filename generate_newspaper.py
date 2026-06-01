import feedparser
import yaml
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import escape
from pathlib import Path
import re, hashlib, ssl, os

from stock_health import run_watchlist
from render_stocks import render_stock_section

ssl._create_default_https_context = ssl._create_unverified_context
CONFIG_FILE = "config.yml"
OUTPUT_FILE = "index.html"

TOPIC_ICONS = {
    "India — National Politics & News": "🇮🇳",
    "Telugu & Andhra Pradesh": "🏛️",
    "Pakistan & South Asia": "🌏",
    "Geopolitics": "🌍",
    "US Politics": "🇺🇸",
    "Business & Markets": "📊",
    "AI & Tech": "🤖",
    "Cloud & SaaS": "☁️",
    "Bay Area": "🌉",
}

def clean_html(text):
    if not text: return ""
    soup = BeautifulSoup(text, "html.parser")
    clean = soup.get_text(" ", strip=True)
    clean = re.sub(r"\s+", " ", clean)
    return clean[:500]

def get_published(entry):
    for key in ["published", "updated", "created"]:
        if key in entry:
            try:
                dt = parsedate_to_datetime(entry[key])
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except Exception:
                pass
    return datetime.now(timezone.utc)

def simple_summary(title, description):
    description = clean_html(description)
    if not description:
        return f"This story discusses: {title}"
    if len(description) > 220:
        return description[:220].rsplit(" ", 1)[0] + "…"
    return description

def article_id(title, link):
    return hashlib.md5(f"{title}|{link}".encode()).hexdigest()

def fetch_topic_articles(topic):
    articles = []
    seen = set()
    for feed_url in topic.get("feeds", []):
        parsed = feedparser.parse(feed_url)
        feed_title = parsed.feed.get("title", "Unknown Source")
        for entry in parsed.entries[:20]:
            title = clean_html(entry.get("title", "Untitled"))
            link = entry.get("link", "")
            description = entry.get("summary", entry.get("description", ""))
            published = get_published(entry)
            if not title or not link: continue
            uid = article_id(title, link)
            if uid in seen: continue
            seen.add(uid)
            articles.append({
                "title": title, "link": link,
                "source": feed_title, "published": published,
                "summary": simple_summary(title, description),
                "topic": topic.get("name", "General")
            })
    articles.sort(key=lambda x: x["published"], reverse=True)
    return articles

def format_time_ago(dt):
    try:
        now = datetime.now(timezone.utc)
        diff = now - dt.astimezone(timezone.utc)
        mins = int(diff.total_seconds() / 60)
        if mins < 60: return f"{mins}m ago"
        hrs = mins // 60
        if hrs < 24: return f"{hrs}h ago"
        days = hrs // 24
        return f"{days}d ago"
    except:
        return ""

def format_source(source):
    # Shorten long feed source names
    for pattern, short in [
        ("The Hindu", "The Hindu"), ("NDTV", "NDTV"),
        ("India Today", "India Today"), ("Hindustan Times", "HT"),
        ("FirstPost", "Firstpost"), ("News18", "News18"),
        ("The Print", "The Print"), ("Sunday Guardian", "Sun. Guardian"),
        ("The Hill", "The Hill"), ("New York Times", "NYT"),
        ("Washington Post", "WaPo"), ("Politico", "Politico"),
        ("TechCrunch", "TechCrunch"), ("WIRED", "WIRED"),
        ("Ars Technica", "Ars Technica"), ("VentureBeat", "VentureBeat"),
        ("MarketWatch", "MarketWatch"), ("CNBC", "CNBC"),
        ("Economic Times", "ET"), ("Mint", "Mint"),
        ("Dawn", "Dawn"), ("Tribune", "Tribune"),
        ("Arab News", "Arab News"), ("Eurasian Times", "Eurasian Times"),
        ("KQED", "KQED"), ("Mercury News", "Mercury News"),
        ("SF Standard", "SF Standard"), ("ABC7", "ABC7"),
    ]:
        if pattern.lower() in source.lower():
            return short
    return source[:28]

def render_topic_section(name, articles):
    icon = TOPIC_ICONS.get(name, "📰")
    if not articles:
        return ""

    lead = articles[0]
    rest = articles[1:]

    lead_html = f"""
    <article class="lead-card">
        <div class="lead-meta">
            <span class="source-tag">{escape(format_source(lead['source']))}</span>
            <span class="time-tag">{format_time_ago(lead['published'])}</span>
        </div>
        <h3 class="lead-title">
            <a href="{escape(lead['link'])}" target="_blank" rel="noopener">{escape(lead['title'])}</a>
        </h3>
        <p class="lead-summary">{escape(lead['summary'])}</p>
    </article>"""

    side_items = ""
    for a in rest[:5]:
        side_items += f"""
        <article class="side-item">
            <div class="side-meta">
                <span class="source-tag">{escape(format_source(a['source']))}</span>
                <span class="time-tag">{format_time_ago(a['published'])}</span>
            </div>
            <h4 class="side-title">
                <a href="{escape(a['link'])}" target="_blank" rel="noopener">{escape(a['title'])}</a>
            </h4>
        </article>"""

    return f"""
    <section class="topic-section" id="topic-{name.lower().replace(' ', '-').replace('&', '')}">
        <div class="topic-header">
            <span class="topic-icon">{icon}</span>
            <h2 class="topic-name">{escape(name)}</h2>
        </div>
        <div class="topic-grid">
            {lead_html}
            <div class="side-list">{side_items}</div>
        </div>
    </section>"""

def render_html(config, all_topics, stock_html):
    now = datetime.now().strftime("%b %d, %Y · %I:%M %p")
    title = escape(config["site"].get("title", "My Newspaper"))
    subtitle = escape(config["site"].get("subtitle", ""))

    nav_links = ""
    for name in all_topics.keys():
        icon = TOPIC_ICONS.get(name, "📰")
        slug = name.lower().replace(" ", "-").replace("&", "")
        nav_links += f'<a href="#topic-{slug}" class="nav-link">{icon} {escape(name)}</a>'

    topic_sections = "".join(
        render_topic_section(name, articles)
        for name, articles in all_topics.items()
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="3600">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800&family=Source+Sans+3:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root {{
  --bg: #f8f7f4;
  --surface: #ffffff;
  --border: #e5e2db;
  --text-primary: #1a1a1a;
  --text-secondary: #555555;
  --text-muted: #888888;
  --accent: #1a73e8;
  --accent-hover: #1557b0;
  --green: #137333;
  --red: #c5221f;
  --amber: #b06000;
  --tag-bg: #f1f3f4;
  --header-bg: #202124;
  --nav-bg: #ffffff;
  --nav-border: #e5e2db;
  --lead-border: #dadce0;
  --score-a: #137333;
  --score-b: #1a73e8;
  --score-c: #b06000;
  --score-d: #c5221f;
}}

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
  font-family: 'Source Sans 3', system-ui, sans-serif;
  background: var(--bg);
  color: var(--text-primary);
  font-size: 15px;
  line-height: 1.5;
}}

/* ── HEADER ─────────────────────────────────────────────────── */
.site-header {{
  background: var(--header-bg);
  padding: 18px 24px 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}}
.site-title {{
  font-family: 'Playfair Display', Georgia, serif;
  font-size: 26px;
  font-weight: 800;
  color: #ffffff;
  letter-spacing: -0.3px;
}}
.site-subtitle {{
  font-size: 12px;
  color: #9aa0a6;
  margin-top: 1px;
}}
.header-right {{
  text-align: right;
  flex-shrink: 0;
}}
.refresh-badge {{
  font-size: 11px;
  color: #9aa0a6;
  background: rgba(255,255,255,0.08);
  padding: 3px 10px;
  border-radius: 20px;
  white-space: nowrap;
}}

/* ── STICKY NAV ──────────────────────────────────────────────── */
.sticky-nav {{
  position: sticky;
  top: 0;
  z-index: 200;
  background: var(--nav-bg);
  border-bottom: 1px solid var(--nav-border);
  padding: 0 24px;
  display: flex;
  gap: 0;
  overflow-x: auto;
  scrollbar-width: none;
}}
.sticky-nav::-webkit-scrollbar {{ display: none; }}
.nav-link {{
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  text-decoration: none;
  padding: 11px 14px;
  white-space: nowrap;
  border-bottom: 3px solid transparent;
  transition: color 0.15s, border-color 0.15s;
}}
.nav-link:hover {{
  color: var(--accent);
  border-bottom-color: var(--accent);
}}
.nav-link.stocks-link {{
  color: var(--accent);
  border-bottom-color: var(--accent);
}}

/* ── MAIN LAYOUT ─────────────────────────────────────────────── */
.main-wrap {{
  max-width: 1280px;
  margin: 0 auto;
  padding: 20px 24px;
}}

/* ── STOCK SECTION ───────────────────────────────────────────── */
.stock-section {{
  margin-bottom: 32px;
  background: var(--surface);
  border-radius: 12px;
  border: 1px solid var(--border);
  overflow: hidden;
}}
.stock-section-header {{
  padding: 14px 20px 12px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fafafa;
}}
.stock-section-title {{
  font-family: 'Playfair Display', serif;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}}
.stock-meta-note {{
  font-size: 11px;
  color: var(--text-muted);
}}

/* Stock ticker strip — horizontal scroll */
.stock-ticker-strip {{
  display: flex;
  gap: 0;
  overflow-x: auto;
  scrollbar-width: none;
  padding: 0;
}}
.stock-ticker-strip::-webkit-scrollbar {{ display: none; }}
.stock-chip {{
  flex-shrink: 0;
  padding: 12px 18px;
  border-right: 1px solid var(--border);
  cursor: default;
  transition: background 0.12s;
  min-width: 130px;
}}
.stock-chip:hover {{ background: #f5f8ff; }}
.stock-chip:last-child {{ border-right: none; }}
.chip-top {{
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 4px;
}}
.chip-ticker {{
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
}}
.chip-price {{
  font-size: 13px;
  color: var(--text-secondary);
}}
.chip-change-pos {{ font-size: 12px; color: var(--green); font-weight: 600; }}
.chip-change-neg {{ font-size: 12px; color: var(--red); font-weight: 600; }}
.chip-bottom {{
  display: flex;
  align-items: center;
  gap: 6px;
}}
.chip-score {{
  font-size: 11px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 4px;
  color: white;
}}
.chip-rec {{
  font-size: 10px;
  color: var(--text-muted);
}}
.score-a  {{ background: var(--score-a); }}
.score-b  {{ background: var(--score-b); }}
.score-c  {{ background: var(--amber); }}
.score-d  {{ background: var(--score-d); }}
.score-f  {{ background: #666; }}

/* Stock detail table */
.stock-table-wrap {{
  overflow-x: auto;
  border-top: 1px solid var(--border);
}}
.stock-table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 12.5px;
}}
.stock-table th {{
  background: #f1f3f4;
  padding: 8px 14px;
  text-align: left;
  font-weight: 600;
  color: var(--text-secondary);
  white-space: nowrap;
  border-bottom: 1px solid var(--border);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}}
.stock-table td {{
  padding: 9px 14px;
  border-bottom: 1px solid #f1f3f4;
  white-space: nowrap;
  color: var(--text-primary);
}}
.stock-table tr:last-child td {{ border-bottom: none; }}
.stock-table tr:hover td {{ background: #f8f9ff; }}
.td-ticker {{ font-weight: 700; font-size: 13px; }}
.td-name {{ color: var(--text-secondary); max-width: 160px; overflow: hidden; text-overflow: ellipsis; }}
.pos {{ color: var(--green); font-weight: 600; }}
.neg {{ color: var(--red); font-weight: 600; }}
.disq-flag {{ color: var(--red); font-size: 11px; }}
.stock-disclaimer {{
  padding: 10px 20px;
  font-size: 11px;
  color: var(--text-muted);
  border-top: 1px solid var(--border);
  background: #fafafa;
}}

/* ── TOPIC SECTIONS ──────────────────────────────────────────── */
.topic-section {{
  margin-bottom: 24px;
  background: var(--surface);
  border-radius: 12px;
  border: 1px solid var(--border);
  overflow: hidden;
}}
.topic-header {{
  padding: 12px 20px 10px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 8px;
  background: #fafafa;
}}
.topic-icon {{ font-size: 16px; }}
.topic-name {{
  font-family: 'Playfair Display', serif;
  font-size: 17px;
  font-weight: 700;
  color: var(--text-primary);
}}
.topic-grid {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
}}
@media (max-width: 700px) {{
  .topic-grid {{ grid-template-columns: 1fr; }}
}}

/* Lead story */
.lead-card {{
  padding: 18px 20px;
  border-right: 1px solid var(--border);
}}
.lead-meta {{
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}}
.lead-title {{
  font-family: 'Playfair Display', serif;
  font-size: 17px;
  font-weight: 700;
  line-height: 1.35;
  margin-bottom: 8px;
}}
.lead-title a {{
  color: var(--text-primary);
  text-decoration: none;
}}
.lead-title a:hover {{ color: var(--accent); }}
.lead-summary {{
  font-size: 13.5px;
  color: var(--text-secondary);
  line-height: 1.5;
}}

/* Side list */
.side-list {{
  display: flex;
  flex-direction: column;
  padding: 6px 0;
}}
.side-item {{
  padding: 10px 18px;
  border-bottom: 1px solid #f3f3f0;
}}
.side-item:last-child {{ border-bottom: none; }}
.side-meta {{
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}}
.side-title {{
  font-size: 13.5px;
  font-weight: 600;
  line-height: 1.35;
  color: var(--text-primary);
}}
.side-title a {{
  color: var(--text-primary);
  text-decoration: none;
}}
.side-title a:hover {{ color: var(--accent); }}

/* Shared tags */
.source-tag {{
  font-size: 11px;
  font-weight: 600;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}}
.time-tag {{
  font-size: 11px;
  color: var(--text-muted);
}}

/* ── TWO-COLUMN TOPIC LAYOUT ─────────────────────────────────── */
.topics-columns {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 0;
}}
@media (max-width: 900px) {{
  .topics-columns {{ grid-template-columns: 1fr; }}
}}
.topics-columns .topic-section {{
  margin-bottom: 0;
}}

/* ── FOOTER ──────────────────────────────────────────────────── */
.site-footer {{
  text-align: center;
  padding: 24px;
  font-size: 12px;
  color: var(--text-muted);
  border-top: 1px solid var(--border);
  margin-top: 16px;
}}
</style>
</head>
<body>

<header class="site-header">
  <div>
    <div class="site-title">{title}</div>
    <div class="site-subtitle">{subtitle}</div>
  </div>
  <div class="header-right">
    <span class="refresh-badge">🔄 {escape(now)}</span>
  </div>
</header>

<nav class="sticky-nav">
  <a href="#stocks" class="nav-link stocks-link">📈 Markets</a>
  {nav_links}
</nav>

<main class="main-wrap">

  <div id="stocks">{stock_html}</div>

  <div class="topics-columns">
    {topic_sections}
  </div>

</main>

<footer class="site-footer">
  Chai's Briefing · RSS + Yahoo Finance · Links cite original sources
</footer>

</body>
</html>"""


def main():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    max_articles = config["site"].get("max_articles_per_topic", 6)
    stock_tickers = config["site"].get("stock_tickers", ["NVDA", "MSFT", "META"])

    print(f"Fetching stock health for {len(stock_tickers)} tickers...")
    stock_data = run_watchlist(stock_tickers)
    stock_html = render_stock_section(stock_data)

    all_topics = {}
    for topic in config.get("topics", []):
        name = topic["name"]
        print(f"Fetching: {name}")
        articles = fetch_topic_articles(topic)
        all_topics[name] = articles[:max_articles]

    html = render_html(config, all_topics, stock_html)
    Path(OUTPUT_FILE).write_text(html, encoding="utf-8")
    print(f"✅ Done → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
