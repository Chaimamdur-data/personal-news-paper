from llm_score import summarize_news

sample = """
Nvidia faces new export restrictions.
Databricks announces AI platform updates.
Salesforce expands Agentforce capabilities.
"""

print(summarize_news(sample))
