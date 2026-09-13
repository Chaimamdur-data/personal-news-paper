from pathlib import Path

from render_jobs import render_jobs_section


INDEX = Path("index.html")


def main():
    html = INDEX.read_text(encoding="utf-8")
    jobs_button = '<button class="ledger-tab-btn" data-tab="jobs">Jobs</button>'
    jobs_panel = f'<div class="ledger-tab-panel" id="tab-jobs">{render_jobs_section()}</div>'

    if 'data-tab="jobs"' not in html:
        html = html.replace('</nav></div>', jobs_button + '</nav></div>', 1)

    if 'id="tab-jobs"' not in html:
        html = html.replace('<script>\n(function(){', jobs_panel + '\n<script>\n(function(){', 1)

    INDEX.write_text(html, encoding="utf-8")
    print("✅ Jobs tab injected")


if __name__ == "__main__":
    main()
