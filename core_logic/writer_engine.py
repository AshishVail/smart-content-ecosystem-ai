import os
import requests

class SmartWriter:
    def __init__(self, GROQ_API_KEY=None, **kwargs):
        # Multiple sources se API key fetch karna
        self.api_key = kwargs.get('api_key') or GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def generate_article(self, topic):
        if not self.api_key:
            return {"title": topic, "body": "Error: API Key missing in Environment", "status": "error"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Sabse Solid Prompt jo AI ko majboor karega professional likhne ke liye
        prompt = f"""
        Write a 1200-word deep-dive, professional SEO article about "{topic}".
        
        STRICT STRUCTURE (Follow exactly):
        1. MAIN TITLE: Use <h1> exactly once at the top.
        2. SUBHEADINGS: Use at least 6-8 <h2> tags and 4-5 <h3> tags for a proper hierarchy.
        3. KEYWORD BOLDING: Find the focus keyword "{topic}" and related LSI keywords. Make them <strong>BOLD</strong> at least 15 times throughout the text.
        4. READABILITY: Use extremely short paragraphs (2 sentences max). Use <br> or <p> tags for plenty of white space.
        5. LISTS: Use <ul> and <li> for features or key points. DO NOT use tables/columns.
        6. FAQ SECTION: At the end, create a detailed "Frequently Asked Questions" section using <h2> for the heading and <h4> for each question.
        7. NO MARKDOWN: Output ONLY clean HTML tags. No stars (***), no dashes (-), no code blocks.
        8. TONE: Expert, engaging, and high-authority human-like writing.
        """

        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system", 
                    "content": "You are a Master SEO Architect. You only speak in clean, high-quality HTML. You never use markdown symbols like stars or hashes."
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.4, # Consistency banaye rakhne ke liye
            "max_tokens": 4096
        }

        try:
            # Lamba article hai toh timeout 120 seconds
            response = requests.post(self.api_url, headers=headers, json=data, timeout=120)
            response.raise_for_status()
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # HTML cleaning logic
            clean_content = content.replace("```html", "").replace("```", "").strip()
            
            return {"title": topic, "body": clean_content, "status": "success"}
        except Exception as e:
            return {"title": topic, "body": f"Logic Error: {str(e)}", "status": "error"}
