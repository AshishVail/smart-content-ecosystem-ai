import os
import requests

class SmartWriter:
    def __init__(self, api_key=None):
        # Fallback to environment variable if api_key is not provided
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def generate_article(self, topic):
        # Double check the key before making the request
        active_key = self.api_key or os.environ.get("GROQ_API_KEY")
        
        if not active_key:
            return {"title": topic, "body": "Critical Error: GROQ_API_KEY is missing", "status": "error"}

        headers = {
            "Authorization": f"Bearer {active_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "You are a professional SEO content writer. Provide output in HTML format only."},
                {"role": "user", "content": f"Write a high-quality blog post about: {topic}. Use <h2> and <p> tags."}
            ]
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            return {"title": topic, "body": content, "status": "success"}
        except Exception as e:
            return {"title": topic, "body": str(e), "status": "failed"}
