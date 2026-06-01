import os
import json
import re
import google.generativeai as genai

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
model = genai.GenerativeModel(MODEL_NAME)


def _extract_json(text):
    text = text.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)


def score_article(article, topic_name):
    prompt = f"""
You are Chai's personal executive intelligence analyst.

Use ONLY the article data below. Do not invent facts.
Score the article for Chai, who cares about AI, data analytics, GTM/RevOps, stocks, Bay Area, debate, robotics, and education.

Return valid JSON only.

JSON fields:
{{
  "health_score": 0-100,
  "signal": "High" or "Medium" or "Low",
  "category": "Opportunity" or "Risk" or "Watch",
  "why_it_matters": "one short sentence",
  "executive_takeaway": "one short sentence",
  "confidence": "High" or "Medium" or "Low"
}}

Topic: {topic_name}
Title: {article.get("title")}
Source: {article.get("source")}
Summary: {article.get("summary")}
URL: {article.get("link")}
"""

    try:
        response = model.generate_content(prompt)
        return _extract_json(response.text)
    except Exception as e:
        return {
            "health_score": 50,
            "signal": "Medium",
            "category": "Watch",
            "why_it_matters": "AI scoring unavailable or data limited.",
            "executive_takeaway": "Review original source.",
            "confidence": "Low",
        }
