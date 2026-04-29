Import os
import requests

class SmartWriter:
    def __init__(self, GROQ_API_KEY):
        # API Key seedhe main.py se yahan aayegi
        self.api_key = GROQ_API_KEY
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def generate_article(self, topic):
        if not self.GROQ_API_KEY:
            return "Error: API Key missing"

        headers = {
            "Authorization": f"Bearer {self.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "You are a professional SEO content writer."},
                {"role": "user", "content": f"Write a high-quality blog post about: {topic}. Use HTML tags like <h2> and <p>."}
            ]
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Simple title/body separation
            return {"title": topic, "body": content}
        except Exception as e:
            return {"error": str(e), "body": ""}
