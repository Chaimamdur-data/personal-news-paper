"""Current high-fit data/analytics/AI roles for The Chai Ledger."""
from datetime import datetime
from html import escape

JOBS = [
    {
        "company":"Early Warning","title":"Sr Director, Data Platform & Analytics Engineering","location":"San Francisco · In-office",
        "salary":"$206K–$330K","comp":"Leadership role","match":97,"track":"Data Platform",
        "why":"Direct overlap with data-platform modernization, analytics engineering, governance, observability, trusted data products, and engineering leadership.",
        "url":"https://builtin.com/job/sr-director-data-platform-analytics-engineering/11490867","source":"Built In","freshness":"Current"
    },
    {
        "company":"Uber","title":"Director, Mobility Analytics, Strategy & Planning","location":"San Francisco · In-office",
        "salary":"$239K–$265K","comp":"Leadership role","match":96,"track":"Analytics Leadership",
        "why":"Excellent fit for executive analytics, data governance, self-service, AI-assisted workflows, planning, and cross-functional operating leadership.",
        "url":"https://builtin.com/job/director-mobility-analytics-strategy-planning/11247298","source":"Built In","freshness":"Current"
    },
    {
        "company":"Snorkel AI","title":"Director, GTM Systems & AI Transformation","location":"San Francisco · Hybrid",
        "salary":"Not surfaced","comp":"AI + GTM","match":96,"track":"AI + GTM",
        "why":"Very close to RevOps systems, GTM data architecture, workflow automation, AI-enabled process innovation, and hands-on transformation leadership.",
        "url":"https://job-boards.greenhouse.io/snorkelai/jobs/6190745004","source":"Greenhouse","freshness":"Current"
    },
    {
        "company":"Achieve","title":"Director, Product Management — Data & Agentic AI Platform","location":"San Mateo · Hybrid",
        "salary":"$220K–$250K","comp":"Data + Agentic AI","match":95,"track":"AI Platform",
        "why":"Strong match for semantic layers, governed data products, agent orchestration, evaluation, monitoring, AI workflows, and enterprise change.",
        "url":"https://builtin.com/job/director-product-management-data-agentic-ai-platform/11737111","source":"Built In","freshness":"Current"
    },
    {
        "company":"Microsoft AI","title":"Director, AI Data Acquisition and Operations","location":"Bay Area / U.S.",
        "salary":"$165.6K–$272.3K Bay Area","comp":"Additional comp may apply","match":92,"track":"AI Data",
        "why":"Strong AI-data operations and cross-functional program fit; slightly less aligned to your analytics-engineering/GTM core than the top roles.",
        "url":"https://job-boards.greenhouse.io/microsoftcorporation/jobs/4393853009","source":"Greenhouse","freshness":"Current"
    },
    {
        "company":"Scribd","title":"Director of Analytics Engineering","location":"San Francisco · Hybrid",
        "salary":"Not surfaced","comp":"Check posting","match":94,"track":"Analytics Engineering",
        "why":"Excellent fit for analytics engineering leadership, metric foundations, self-service analytics, and modern data-stack architecture.",
        "url":"https://jobs.ashbyhq.com/ScribdInc/de20593d-6bc8-4450-ba5c-5802819224da","source":"Ashby","freshness":"Current"
    },
    {
        "company":"Lila Sciences","title":"Senior Director, Data Platform Engineering","location":"San Francisco",
        "salary":"Not surfaced","comp":"Check posting","match":93,"track":"Data Platform",
        "why":"Strong fit for end-to-end data-platform architecture, reliability, self-service infrastructure, ML/AI workloads, and engineering leadership.",
        "url":"https://job-boards.greenhouse.io/lilasciences/jobs/4202443009","source":"Greenhouse","freshness":"Current"
    },
    {
        "company":"Crusoe","title":"Senior Director, Analytics & Data Science","location":"San Francisco · On-site",
        "salary":"Not surfaced","comp":"Check posting","match":91,"track":"Analytics Leadership",
        "why":"Strong analytics leadership fit in an AI-infrastructure company; the role is broader into data science and strategic initiatives.",
        "url":"https://jobs.ashbyhq.com/Crusoe/a47eea20-0f86-4d60-ab86-4e4f9ad9abc7","source":"Ashby","freshness":"Current"
    },
    {
        "company":"Instead","title":"Senior Director of Data Analytics & Business Systems","location":"San Francisco · On-site",
        "salary":"Not surfaced","comp":"Check posting","match":91,"track":"Analytics + Systems",
        "why":"Strong match for Salesforce, BI, pipelines, executive metrics, automation, and cross-functional business systems ownership.",
        "url":"https://job-boards.greenhouse.io/instead/jobs/7772740003","source":"Greenhouse","freshness":"Current"
    },
    {
        "company":"Figma","title":"Director, Data Science","location":"San Francisco / New York / U.S.",
        "salary":"Not surfaced","comp":"Check posting","match":88,"track":"AI + Analytics",
        "why":"Good leadership and AI-measurement fit, especially around AI product analytics and evals; heavier data-science depth makes it more of a stretch.",
        "url":"https://job-boards.greenhouse.io/figma/jobs/6130865004","source":"Greenhouse","freshness":"Current"
    },
    {
        "company":"Snorkel AI","title":"Director, Forward Deployed Researcher — Data as a Service","location":"San Francisco · Hybrid / U.S. Remote",
        "salary":"Not surfaced","comp":"AI data","match":86,"track":"AI Data",
        "why":"Interesting agentic-AI/data role with customer-facing technical leadership, but more research-heavy than your strongest analytics-engineering lane.",
        "url":"https://job-boards.greenhouse.io/snorkelai/jobs/5837448004","source":"Greenhouse","freshness":"Current"
    },
    {
        "company":"Snorkel AI","title":"Director, Data Partnerships","location":"San Francisco · Hybrid",
        "salary":"Not surfaced","comp":"AI data ecosystem","match":80,"track":"AI Data",
        "why":"Relevant AI/data ecosystem exposure, but partnership sourcing is less aligned to your hands-on data/analytics leadership background.",
        "url":"https://job-boards.greenhouse.io/snorkelai/jobs/6214981004","source":"Greenhouse","freshness":"Current"
    },
]

def _card(j):
    salary_class="job-salary unknown" if j["salary"]=="Not surfaced" else "job-salary"
    return f"""
    <article class="job-card" data-track="{escape(j['track'])}">
      <div class="job-top">
        <div class="job-company">{escape(j['company'])}</div>
        <div class="job-match">{j['match']}%</div>
      </div>
      <h2>{escape(j['title'])}</h2>
      <div class="job-meta"><span>{escape(j['location'])}</span><span>{escape(j['source'])}</span><span>{escape(j['freshness'])}</span></div>
      <div class="job-facts">
        <div><label>Base</label><strong class="{salary_class}">{escape(j['salary'])}</strong></div>
        <div><label>Track</label><strong>{escape(j['track'])}</strong></div>
        <div><label>Other</label><strong>{escape(j['comp'])}</strong></div>
      </div>
      <p>{escape(j['why'])}</p>
      <a class="job-link" href="{escape(j['url'])}" target="_blank" rel="noopener">View job description ↗</a>
    </article>"""

def render_jobs_section():
    jobs=sorted(JOBS,key=lambda x:x["match"],reverse=True)
    cards="".join(_card(j) for j in jobs)
    tracks=sorted({j["track"] for j in jobs})
    chips='<button class="job-filter active" data-job-filter="All">All</button>'+''.join(
        f'<button class="job-filter" data-job-filter="{escape(t)}">{escape(t)}</button>' for t in tracks
    )
    return f"""
<style>
.jobs-page{{min-height:100vh;background:
radial-gradient(780px 390px at 14% -5%,rgba(52,210,123,.08),transparent 58%),
radial-gradient(720px 360px at 88% 0%,rgba(99,169,255,.08),transparent 58%),
#0e1116;color:#f2f5f7;padding:28px 22px 44px;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
.jobs-shell{{max-width:1220px;margin:0 auto}}
.jobs-head{{display:flex;justify-content:space-between;gap:24px;align-items:flex-start;padding-bottom:18px;border-bottom:1px solid #2b323e}}
.jobs-eyebrow{{font-size:9px;font-weight:850;letter-spacing:1px;color:#34d27b;margin-bottom:8px;text-transform:uppercase}}
.jobs-head h1{{font-size:36px;line-height:1;margin:0 0 8px;letter-spacing:-1.2px}}
.jobs-head p{{margin:0;max-width:760px;font-size:12px;line-height:1.5;color:#94a0ad}}
.jobs-date{{font:600 10px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;color:#94a0ad;text-align:right;white-space:nowrap}}
.jobs-toolbar{{display:flex;justify-content:space-between;gap:14px;align-items:center;margin:16px 0 18px}}
.jobs-filters{{display:flex;gap:7px;overflow-x:auto;scrollbar-width:none}}
.jobs-filters::-webkit-scrollbar{{display:none}}
.job-filter{{border:1px solid #2b323e;background:#161a21;color:#96a2af;padding:8px 10px;border-radius:999px;white-space:nowrap;font-size:10px;font-weight:750;cursor:pointer}}
.job-filter.active{{background:#34d27b;color:#07130c;border-color:#34d27b}}
.jobs-count{{font:650 10px/1 ui-monospace,SFMono-Regular,Menlo,monospace;color:#7f8b97;white-space:nowrap}}
.jobs-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}}
.job-card{{border:1px solid #2b323e;background:linear-gradient(180deg,#161a21,#13171d);border-radius:20px;padding:16px;transition:.18s ease}}
.job-card:hover{{border-color:#414b59;transform:translateY(-1px)}}
.job-card.hidden{{display:none}}
.job-top{{display:flex;justify-content:space-between;gap:12px;align-items:center}}
.job-company{{font-size:10px;font-weight:850;color:#34d27b;text-transform:uppercase;letter-spacing:.7px}}
.job-match{{font:800 12px/1 ui-monospace,SFMono-Regular,Menlo,monospace;background:rgba(52,210,123,.12);color:#59e595;border:1px solid rgba(52,210,123,.22);border-radius:999px;padding:6px 8px}}
.job-card h2{{font-size:20px;line-height:1.12;margin:9px 0 9px;letter-spacing:-.3px}}
.job-meta{{display:flex;gap:7px;flex-wrap:wrap;color:#7e8996;font-size:9px}}
.job-meta span{{background:#1d222b;border:1px solid #29313b;padding:5px 7px;border-radius:999px}}
.job-facts{{display:grid;grid-template-columns:1.1fr .9fr .9fr;gap:8px;margin:14px 0}}
.job-facts div{{background:#1a1f27;border:1px solid rgba(255,255,255,.04);border-radius:12px;padding:9px}}
.job-facts label{{display:block;font-size:8px;color:#7f8a96;margin-bottom:5px;text-transform:uppercase;letter-spacing:.55px}}
.job-facts strong{{display:block;font-size:11px;line-height:1.25}}
.job-salary{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-variant-numeric:tabular-nums}}
.job-salary.unknown{{color:#f4b740}}
.job-card p{{font-size:11px;line-height:1.5;color:#aeb8c3;margin:0 0 14px}}
.job-link{{display:inline-flex;text-decoration:none;border:1px solid #36404d;background:#20262f;color:#f0f4f6;border-radius:999px;padding:9px 11px;font-size:10px;font-weight:800}}
.job-link:hover{{border-color:#34d27b;color:#c8f7dc}}
.jobs-note{{margin-top:18px;padding-top:11px;border-top:1px solid #2b323e;color:#707c89;font-size:9px;line-height:1.55}}
@media(max-width:780px){{.jobs-page{{padding:20px 11px 34px}}.jobs-head{{display:block}}.jobs-head h1{{font-size:30px}}.jobs-date{{text-align:left;margin-top:10px}}.jobs-toolbar{{display:block}}.jobs-count{{display:block;margin-top:10px}}.jobs-grid{{grid-template-columns:1fr}}}}
@media(max-width:480px){{.job-facts{{grid-template-columns:1fr 1fr}}.job-facts div:last-child{{grid-column:1/-1}}}}
@media(prefers-reduced-motion:reduce){{.job-card{{transition:none}}}}
</style>
<section class="jobs-page"><div class="jobs-shell">
  <header class="jobs-head"><div><div class="jobs-eyebrow">The Chai Ledger / Career Radar</div><h1>Jobs Worth Checking</h1><p>Broader current search across data, analytics, AI and platform leadership. Match % is a resume-fit estimate, not an employer score.</p></div><div class="jobs-date">Current snapshot<br><strong>{datetime.now().strftime('%b %d, %Y')}</strong></div></header>
  <div class="jobs-toolbar"><div class="jobs-filters">{chips}</div><span class="jobs-count" id="jobs-count">{len(jobs)} roles</span></div>
  <div class="jobs-grid" id="jobs-grid">{cards}</div>
  <div class="jobs-note">Compensation is shown only when surfaced by the current posting/search result. “Not surfaced” is intentional—not guessed. Always confirm the live job description before applying.</div>
</div></section>
<script>
(()=>{{
 const buttons=[...document.querySelectorAll('.job-filter')], cards=[...document.querySelectorAll('.job-card')], count=document.getElementById('jobs-count');
 buttons.forEach(b=>b.addEventListener('click',()=>{{
  buttons.forEach(x=>x.classList.toggle('active',x===b));
  const f=b.dataset.jobFilter;let n=0;
  cards.forEach(c=>{{const show=f==='All'||c.dataset.track===f;c.classList.toggle('hidden',!show);if(show)n++;}});
  count.textContent=n+' roles';
 }}));
}})();
</script>"""
