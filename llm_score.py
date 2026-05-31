import os
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

model = genai.GenerativeModel("gemini-2.0-flash")

def summarize_news(news_text):
    prompt = f"""
You are my personal executive news analyst.

Analyze these news stories.

Return:
1. Executive Summary (5 bullets)
2. Top Opportunities
3. Top Risks
4. Health Score (0-100)
5. Why It Matters

News:
{news_text}
"""

    response = model.generate_content(prompt)
    return response.text
