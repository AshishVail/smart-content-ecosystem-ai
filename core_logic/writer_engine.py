import os
import requests

class SmartWriter:
    def __init__(self, GROQ_API_KEY=None, **kwargs):
        # 1. Sabse pehle check karega ki main.py se key aayi hai ya nahi
        # 2. Agar nahi aayi, toh seedhe Render ke Environment se uthayega
        self.api_key = GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def generate_article(self, topic):
        # Yahan 'self.GROQ_API_KEY' galat tha, use 'self.api_key' hona chahiye
        if not self.api_key:
            return {"title": topic, "body": "Error: API Key is missing in Render settings", "status": "error"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "You are a professional SEO content writer. Use HTML format."},
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
            # Error aane par bhi system crash nahi hoga
            return {"title": topic, "body": f"API Error: {str(e)}", "status": "error"}
