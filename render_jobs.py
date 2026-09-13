"""Curated high-compensation data/analytics job tab for The Chai Ledger."""
from datetime import datetime
from html import escape


JOBS = [
    {
        "company": "Airwallex",
        "title": "Director of AI Analytics & CEO Office",
        "location": "San Francisco · Hybrid",
        "salary": "$300K–$320K",
        "comp": "Equity + Bonus",
        "match": 96,
        "type": "AI + Analytics Leadership",
        "why": "Exceptional match for your AI-enabled analytics leadership, executive partnership, data strategy, and enterprise transformation background.",
        "summary": "Leads AI analytics from the CEO Office within Engineering/Data Science, combining strategic analytics, AI adoption, executive decision support, and high-impact cross-functional execution.",
        "url": "https://jobs.ashbyhq.com/airwallex/5f17444c-fea7-4394-8bab-6284b46f1a1c?departmentId=866a2bea-da1c-4818-ad99-5fbd0ea8a5fb",
        "verified": "Sep 2026",
    },
    {
        "company": "DoorDash",
        "title": "Director, Analytics — Commerce Platform",
        "location": "San Francisco / Sunnyvale",
        "salary": "$255K–$375K",
        "comp": "Equity",
        "match": 94,
        "type": "Product + GTM Analytics",
        "why": "Strong overlap with your 0→1 analytics, product/GTM measurement, executive metrics, and scaled data-platform experience.",
        "summary": "Owns analytics and data science for Commerce Platform across new products and scaling businesses, shaping metrics, GTM investments, and the data foundations behind product decisions.",
        "url": "https://jobs.khoslaventures.com/companies/doordash/jobs/78563094-director-analytics-commerce-platform",
        "verified": "Sep 2026",
    },
    {
        "company": "Hims & Hers",
        "title": "Principal Data Engineer",
        "location": "U.S. Remote",
        "salary": "$220K–$260K",
        "comp": "Equity",
        "match": 93,
        "type": "Principal Data Engineering",
        "why": "Very strong fit for your Snowflake/dbt/data architecture, streaming, governance, and hands-on principal-level engineering depth.",
        "summary": "Principal-level data engineering role focused on scalable data architecture, production pipelines, platform standards, and technical leadership across analytics and data science.",
        "url": "https://jobs.ashbyhq.com/hims-and-hers/a321e167-59ab-46cc-9b50-75154f122bdb?category=operational_accounting",
        "verified": "Sep 2026",
    },
    {
        "company": "Collective Health",
        "title": "Director of Analytics",
        "location": "San Francisco · Hybrid",
        "salary": "$200K–$250K",
        "comp": "350,000 Stock Options",
        "match": 92,
        "type": "Analytics + BI Modernization",
        "why": "Excellent fit for your BI modernization, governed reporting, LLM/RAG analytics, metric governance, and team-building experience.",
        "summary": "Leads modernization of analytics and client reporting infrastructure, metric governance and data quality, with explicit use of LLM/RAG-enabled insights and cross-functional analytics leadership.",
        "url": "https://builtin.com/job/director-analytics/9723826",
        "verified": "Sep 2026",
    },
    {
        "company": "Jazz Pharmaceuticals",
        "title": "Senior Director, Analytics and Insights",
        "location": "San Francisco / Remote",
        "salary": "$232K–$348K",
        "comp": "Bonus + Equity",
        "match": 86,
        "type": "Commercial Analytics",
        "why": "Strong executive analytics and AI-workflow fit, though healthcare/pharma domain depth is a larger gap than the top four roles.",
        "summary": "Leads customer analytics, insights and performance reporting, including AI, automation and agentic workflows, with ownership of analytics strategy, talent, vendors and executive decision support.",
        "url": "https://careers.jazzpharma.com/job/1505/senior-director-analytics-and-insights-commercial-us-ca-san-francisco/",
        "verified": "Sep 2026",
    },
]


def _card(job):
    match = job["match"]
    match_class = "match-top" if match >= 93 else "match-strong" if match >= 88 else "match-good"
    return f"""
    <article class="job-card">
      <div class="job-card-top">
        <div>
          <div class="job-company">{escape(job['company'])}</div>
          <h2>{escape(job['title'])}</h2>
          <div class="job-type">{escape(job['type'])}</div>
        </div>
        <div class="job-match {match_class}"><strong>{match}%</strong><span>RESUME MATCH</span></div>
      </div>
      <div class="job-facts">
        <div><span>BASE</span><strong>{escape(job['salary'])}</strong></div>
        <div><span>LOCATION</span><strong>{escape(job['location'])}</strong></div>
        <div><span>UPSIDE</span><strong>{escape(job['comp'])}</strong></div>
      </div>
      <div class="job-why"><span>WHY IT FITS</span>{escape(job['why'])}</div>
      <p class="job-summary">{escape(job['summary'])}</p>
      <div class="job-actions">
        <span>Verified {escape(job['verified'])}</span>
        <a href="{escape(job['url'])}" target="_blank" rel="noopener">View Job →</a>
      </div>
    </article>"""


def render_jobs_section():
    cards = "".join(_card(j) for j in sorted(JOBS, key=lambda x: x["match"], reverse=True))
    return f"""
    <style>
      .jobs-page{{max-width:1180px;margin:0 auto;background:#f3ede2;min-height:100vh;padding:24px 28px 40px;color:#171713;font-family:Georgia,'Times New Roman',serif}}
      .jobs-masthead{{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;border-bottom:3px double #24221e;padding-bottom:13px;margin-bottom:12px}}
      .jobs-eyebrow{{font:700 9px/1.2 Arial,sans-serif;letter-spacing:.8px;color:#6e675b;margin-bottom:7px}}
      .jobs-masthead h1{{font-size:40px;line-height:.95;margin:0 0 7px;letter-spacing:-1.1px}}
      .jobs-masthead p{{font-size:11px;font-style:italic;color:#6e675b;margin:0;max-width:720px}}
      .jobs-edition{{font:9px/1.5 Arial,sans-serif;text-align:right;white-space:nowrap}}
      .jobs-rule{{display:flex;flex-wrap:wrap;gap:7px 16px;border-bottom:1px solid #24221e;padding:8px 0 10px;margin-bottom:16px;font:8px/1.3 Arial,sans-serif;text-transform:uppercase;letter-spacing:.45px}}
      .jobs-rule b{{color:#674e25}}
      .jobs-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));border-left:1px solid #24221e;border-top:1px solid #24221e}}
      .job-card{{padding:16px;border-right:1px solid #24221e;border-bottom:1px solid #24221e;min-width:0}}
      .job-card-top{{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}}
      .job-company{{font:800 9px/1 Arial,sans-serif;text-transform:uppercase;letter-spacing:.65px;color:#674e25;margin-bottom:5px}}
      .job-card h2{{font-size:20px;line-height:1.05;margin:0 0 6px;letter-spacing:-.2px}}
      .job-type{{font:7.5px/1 Arial,sans-serif;text-transform:uppercase;letter-spacing:.45px;border:1px solid #24221e;display:inline-block;padding:3px 5px}}
      .job-match{{min-width:72px;text-align:center;border:1px solid #24221e;padding:7px 6px 6px;font-family:Arial,sans-serif}}
      .job-match strong{{display:block;font-size:21px;line-height:1}}
      .job-match span{{display:block;font-size:6.5px;line-height:1.1;margin-top:3px;letter-spacing:.4px}}
      .match-top{{background:#183f2f;color:#fff;border-color:#183f2f}}
      .match-strong{{background:#d6b36c}}
      .match-good{{background:#ddd5c6}}
      .job-facts{{display:grid;grid-template-columns:.8fr 1.1fr 1fr;gap:0;border-top:1px solid #8f877a;border-bottom:1px solid #8f877a;margin:13px 0 11px}}
      .job-facts div{{padding:8px 8px 7px 0}}
      .job-facts span{{display:block;font:6.5px/1 Arial,sans-serif;color:#776f63;letter-spacing:.45px;margin-bottom:3px}}
      .job-facts strong{{font:700 10px/1.2 Arial,sans-serif}}
      .job-why{{font-size:10px;line-height:1.4;color:#4f4a42;margin-bottom:8px}}
      .job-why span{{font:800 7px/1 Arial,sans-serif;letter-spacing:.45px;color:#171713;margin-right:6px}}
      .job-summary{{font-size:11px;line-height:1.42;color:#595349;margin:0 0 13px}}
      .job-actions{{display:flex;justify-content:space-between;align-items:center;gap:10px;font:7.5px/1 Arial,sans-serif;text-transform:uppercase;letter-spacing:.4px;color:#756e62}}
      .job-actions a{{background:#171713;color:#f3ede2;text-decoration:none;padding:8px 10px;font-weight:800}}
      .job-actions a:hover{{background:#674e25}}
      .jobs-note{{margin-top:15px;border-top:2px solid #24221e;padding-top:9px;font:8px/1.45 Arial,sans-serif;color:#746d61}}
      @media(max-width:760px){{
        .jobs-page{{padding:18px 14px 30px}}
        .jobs-masthead h1{{font-size:31px}}
        .jobs-grid{{grid-template-columns:1fr}}
        .job-card h2{{font-size:19px}}
        .job-facts{{grid-template-columns:1fr 1fr}}
        .job-facts div:last-child{{grid-column:1/-1}}
      }}
    </style>
    <section class="jobs-page">
      <header class="jobs-masthead">
        <div>
          <div class="jobs-eyebrow">◇ THE CHAI LEDGER / CAREER RADAR</div>
          <h1>Jobs Worth Your Time</h1>
          <p>High-compensation data, analytics and AI leadership roles ranked against your resume — strict Bay Area/remote focus.</p>
        </div>
        <div class="jobs-edition">Shortlist<br><strong>{datetime.now().strftime('%b %d, %Y')}</strong></div>
      </header>
      <div class="jobs-rule"><span><b>FILTER</b> Salary ceiling ≥ $250K</span><span><b>COMP</b> Equity / options / bonus required</span><span><b>FIT</b> Data · BI · GTM · AI · Analytics Engineering</span></div>
      <div class="jobs-grid">{cards}</div>
      <div class="jobs-note">Match % is a resume-fit estimate, not an employer score. Job availability and compensation can change; use “View Job” to confirm the live posting before applying.</div>
    </section>"""
