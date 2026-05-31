import os
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

for model in genai.list_models():
    methods = getattr(model, "supported_generation_methods", [])
    if "generateContent" in methods:
        print(model.name)
