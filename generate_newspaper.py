import feedparser
import yaml
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import escape
from pathlib import Path
import re
import hashlib
import ssl
import os

from llm_score import summarize_news
from stock_health import run_watchlist
from render_stocks import render_stock_section

ssl._create_default_https_context = ssl._create_unverified_context

CONFIG_FILE = "config.yml"
OUTPUT_FILE = "index.html"


def clean_html(text: str) -> str:
    if not text:
        return ""
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


def simple_summary(title: str, description: str) -> str:
    description = clean_html(description)
    if not description:
        return f"This story discusses: {title}"
    if len(description) > 280:
        return description[:280].rsplit(" ", 1)[0] + "..."
    return description


def article_id(title, link):
    raw = f"{title}|{link}".encode("utf-8")
    return hashlib.md5(raw).hexdigest()


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

            if not title or not link:
                continue

            unique_id = article_id(title, link)
            if unique_id in seen:
                continue

            seen.add(unique_id)

            articles.append({
                "title": title,
                "link": link,
                "source": feed_title,
                "published": published,
                "summary": simple_summary(title, description),
                "topic": topic.get("name", "General")
            })

    articles.sort(key=lambda x: x["published"], reverse=True)
    return articles


def format_date(dt):
    try:
        return dt.astimezone().strftime("%b %d, %Y %I:%M %p")
    except Exception:
        return "Unknown time"


def build_ai_input(all_topics):
    lines = []
    for topic_name, articles in all_topics.items():
        lines.append(f"\nTOPIC: {topic_name}")
        for i, article in enumerate(articles[:6], start=1):
            lines.append(
                f"{i}. Title: {article['title']}\n"
                f"Source: {article['source']}\n"
                f"Published: {format_date(article['published'])}\n"
                f"Summary: {article['summary']}\n"
                f"URL: {article['link']}\n"
            )
    return "\n".join(lines)


def safe_ai_summary(all_topics):
    news_text = build_ai_input(all_topics)
    if not news_text.strip():
        return "No news articles found to summarize."
    try:
        return summarize_news(news_text)
    except Exception as e:
        return f"AI summary unavailable. Reason: {str(e)}"


def render_ai_summary(ai_summary):
    safe = escape(ai_summary)
    safe = safe.replace("\n", "<br>")
    return f"""
    <section class="ai-summary">
        <h2>AI Executive Summary</h2>
        <div class="ai-box">
            {safe}
        </div>
    </section>
    """


def render_html(config, all_topics, ai_summary, stock_html):
    now = datetime.now().strftime("%b %d, %Y %I:%M %p")

    title    = escape(config["site"].get("title",    "Personal Newspaper"))
    subtitle = escape(config["site"].get("subtitle", "Hourly refreshed news"))

    topic_blocks = []
    for topic_name, articles in all_topics.items():
        cards = []
        for article in articles:
            cards.append(f"""
            <article class="card">
                <div class="meta">
                    <span>{escape(article["source"])}</span>
                    <span>{format_date(article["published"])}</span>
                </div>
                <h3>{escape(article["title"])}</h3>
                <p>{escape(article["summary"])}</p>
                <a href="{escape(article["link"])}" target="_blank" rel="noopener noreferrer">
                    Read original source / citation →
                </a>
            </article>
            """)
        if not cards:
            cards.append("<p>No articles found for this topic.</p>")

        topic_blocks.append(f"""
        <section class="topic">
            <h2>{escape(topic_name)}</h2>
            <div class="grid">
                {''.join(cards)}
            </div>
        </section>
        """)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="3600">
    <style>
        body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; background: #f4f1ea; color: #1f2933; }}
        header {{ background: #111827; color: white; padding: 32px 20px; text-align: center; }}
        header h1 {{ margin: 0; font-size: 36px; }}
        header p {{ margin: 8px 0 0; color: #d1d5db; }}
        nav {{ background: #1f2937; padding: 10px 20px; text-align: center; position: sticky; top: 0; z-index: 100; }}
        nav a {{ color: #d1d5db; text-decoration: none; margin: 0 12px; font-size: 14px; }}
        nav a:hover {{ color: white; }}
        main {{ max-width: 1180px; margin: 0 auto; padding: 24px; }}
        .ai-summary {{ margin-bottom: 36px; }}
        .ai-summary h2 {{ font-size: 28px; border-bottom: 3px solid #111827; padding-bottom: 8px; }}
        .ai-box {{ background: #ffffff; border-left: 6px solid #0f766e; padding: 22px; border-radius: 14px;
                   box-shadow: 0 4px 12px rgba(0,0,0,0.08); line-height: 1.6; font-size: 16px; }}
        .topic {{ margin-bottom: 36px; }}
        .topic h2 {{ border-bottom: 3px solid #111827; padding-bottom: 8px; font-size: 26px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 18px; }}
        .card {{ background: white; padding: 18px; border-radius: 14px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
        .card h3 {{ margin: 10px 0; font-size: 20px; line-height: 1.3; }}
        .card p {{ line-height: 1.5; color: #374151; }}
        .card a {{ display: inline-block; margin-top: 10px; color: #0f766e; font-weight: bold; text-decoration: none; }}
        .meta {{ display: flex; justify-content: space-between; gap: 12px; font-size: 12px; color: #6b7280; }}
        footer {{ text-align: center; padding: 24px; color: #6b7280; font-size: 13px; }}
    </style>
</head>
<body>
    <header>
        <h1>{title}</h1>
        <p>{subtitle}</p>
        <p>Last refreshed: {escape(now)}</p>
    </header>

    <nav>
        <a href="#stocks">📈 Stocks</a>
        <a href="#summary">🧠 AI Summary</a>
        {''.join(f'<a href="#topic-{i}">{escape(name)}</a>' for i, name in enumerate(all_topics.keys()))}
    </nav>

    <main>
        <div id="stocks">{stock_html}</div>

        <div id="summary">{render_ai_summary(ai_summary)}</div>

        {''.join(f'<div id="topic-{i}">{block}</div>' for i, block in enumerate(topic_blocks))}
    </main>

    <footer>
        Built from RSS feeds + AI executive summary. Each story links to the original source as citation.
    </footer>
</body>
</html>
"""


def main():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    max_articles = config["site"].get("max_articles_per_topic", 6)

    # ── Stock health dashboard ─────────────────────────────────────────────────
    stock_tickers = config["site"].get(
        "stock_tickers",
        ["NVDA", "MU", "MSFT", "META", "AMZN", "AAPL", "VUG", "SMH", "CRM", "NFLX"]
    )
    print(f"Fetching stock health for: {stock_tickers}")
    stock_data = run_watchlist(stock_tickers)
    stock_html = render_stock_section(stock_data)

    # ── News topics ────────────────────────────────────────────────────────────
    all_topics = {}
    for topic in config.get("topics", []):
        name = topic["name"]
        print(f"Fetching news: {name}")
        articles = fetch_topic_articles(topic)
        all_topics[name] = articles[:max_articles]

    print("Generating AI executive summary...")
    ai_summary = safe_ai_summary(all_topics)

    html = render_html(config, all_topics, ai_summary, stock_html)
    Path(OUTPUT_FILE).write_text(html, encoding="utf-8")
    print(f"✅ Done. Open {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
