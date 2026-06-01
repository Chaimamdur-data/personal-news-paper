import os
import google.generativeai as genai

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
model = genai.GenerativeModel(MODEL_NAME)


def summarize_news(news_text):
    prompt = f"""
You are Chai's personal executive intelligence analyst.

Chai cares about:
- AI and LLMs
- Data analytics, Databricks, Snowflake, dbt, Tableau
- GTM, RevOps, Salesforce, Pure Storage
- Stocks and market-moving business news
- Bay Area
- Debate, robotics, education, STEM

Use ONLY the news items provided below.
Do not invent facts.
Cite sources by mentioning source names from the provided news.
Keep it concise and executive-friendly.

Return this exact format:

## Executive Summary
- Bullet 1
- Bullet 2
- Bullet 3
- Bullet 4
- Bullet 5

## Top Opportunities
- Opportunity 1
- Opportunity 2
- Opportunity 3

## Top Risks
- Risk 1
- Risk 2
- Risk 3

## Health Score
XX / 100

## Why It Matters
Short paragraph explaining what Chai should pay attention to.

News items:
{news_text}
"""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"""## Executive Summary
- AI summary unavailable.

## Top Opportunities
- Review the latest article links manually.

## Top Risks
- Gemini API call failed or quota/model access is unavailable.

## Health Score
50 / 100

## Why It Matters
The RSS newspaper still works, but AI summarization failed.

Error: {str(e)}
"""
