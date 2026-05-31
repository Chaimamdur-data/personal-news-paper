# Personal News Paper - Free Version

This is a simple personal newspaper that refreshes every hour using free RSS feeds.

## What it does

- Pulls latest articles from RSS feeds
- Keeps it cheap/free
- Creates a clean HTML newspaper
- Includes citations/links to original sources
- Can run locally or hourly using GitHub Actions

## Files

- `config.yml` - Your topics and RSS feeds
- `generate_newspaper.py` - Main script
- `requirements.txt` - Python packages
- `index.html` - Generated newspaper page
- `.github/workflows/refresh.yml` - Runs every hour on GitHub

## Step 1: Install Python

Install Python 3.11 or later.

## Step 2: Install packages

```bash
pip install -r requirements.txt
```

## Step 3: Run locally

```bash
python generate_newspaper.py
```

Then open `index.html` in your browser.

## Step 4: Customize topics

Edit `config.yml`.

Example:

```yaml
topics:
  - name: AI & Data
    feeds:
      - https://www.theverge.com/rss/index.xml
      - https://venturebeat.com/category/ai/feed/
```

## Step 5: Publish for free with GitHub Pages

1. Create a GitHub repo.
2. Upload these files.
3. Go to Settings → Pages.
4. Source: Deploy from branch.
5. Branch: main.
6. Folder: root.
7. Your newspaper will be visible as a website.

## Step 6: Auto-refresh hourly

GitHub Actions will run every hour and update `index.html`.

You can also manually run it from GitHub Actions.
