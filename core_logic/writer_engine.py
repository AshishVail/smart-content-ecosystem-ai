import os
import requests

class SmartWriter:
    def __init__(self, GROQ_API_KEY=None, **kwargs):
        self.api_key = kwargs.get('api_key') or GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def generate_article(self, topic):
        if not self.api_key:
            return {"title": topic, "body": "Error: API Key is missing", "status": "error"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Professional SEO Prompt
        prompt = (
            f"Write a professional SEO-optimized blog post about '{topic}'. "
            "Follow these rules strictly:\n"
            "1. Use <h1> for the main title.\n"
            "2. Use <h2> and <h3> for subheadings.\n"
            "3. Use <p> for detailed paragraphs.\n"
            "4. Use <ul> and <li> for bullet points to explain benefits or features.\n"
            "5. If relevant, use an HTML <table> to compare data or features.\n"
            "6. Include a 'Focus Keywords' section at the end.\n"
            "7. Keep the tone engaging and expert-level."
        )

        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "You are an expert SEO Content Strategist. Always output in clean HTML format."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7 # Thoda creativity badhane ke liye
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            return {"title": topic, "body": content, "status": "success"}
        except Exception as e:
            return {"title": topic, "body": f"API Error: {str(e)}", "status": "error"}
