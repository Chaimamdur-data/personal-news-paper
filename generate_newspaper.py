from pathlib import Path
import yaml

from stock_health import run_watchlist
from render_stocks import render_stock_section

CONFIG_FILE = "config.yml"
OUTPUT_FILE = "index.html"


def render_html(stock_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>The Chai Ledger</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="3600">
<style>
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0;background:#e9e4da}}
body{{min-height:100vh}}
</style>
</head>
<body>
{stock_html}
</body>
</html>"""


def main():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    stock_tickers = config["site"].get("stock_tickers", [])
    print(f"Fetching stock health for {len(stock_tickers)} tickers...")
    stock_data = run_watchlist(stock_tickers)
    stock_html = render_stock_section(stock_data)

    Path(OUTPUT_FILE).write_text(render_html(stock_html), encoding="utf-8")
    print(f"✅ Done → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
