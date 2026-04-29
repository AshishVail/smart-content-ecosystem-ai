import os
import requests

class SmartWriter:
    def __init__(self, GROQ_API_KEY=None, **kwargs):
        self.api_key = kwargs.get('api_key') or GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def generate_article(self, topic):
        if not self.api_key:
            return {"title": topic, "body": "Error: API Key missing", "status": "error"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Professional Prompt with No Columns and Strict HTML
        prompt = f"""
        Write a massive, 1000-word highly professional SEO article about "{topic}".
        
        STRICT FORMATTING RULES:
        1. HEADING 1: Use <h1> for the main title once.
        2. HEADING 2 & 3: Use at least five <h2> and three <h3> tags for sub-sections.
        3. KEYWORD BOLDING: Find the focus keyword "{topic}" and related terms, and make them <strong>BOLD</strong> at least 10 times in the article.
        4. NO TABLES: Do not use <table> tags. Use professional bullet points (<ul> <li>) instead.
        5. BLANK SPACE: Every paragraph must be very short (max 2-3 sentences) to ensure lots of blank space for mobile users.
        6. FAQ SECTION: At the end, add a "Frequently Asked Questions" section with 4-5 questions using <h4>.
        7. NO MARKDOWN: Do not use stars (***) or dashes. Use ONLY clean HTML tags like <p>, <h2>, <ul>, <strong>.
        8. CONTENT: Write like a high-paid human tech journalist, not a boring bot.
        
        Make sure "{topic}" is mentioned in the first paragraph and the last paragraph.
        """

        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system", 
                    "content": "You are a senior SEO expert. You only output pure HTML code. No talk, no markdown stars, just clean HTML."
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.5, # Consistency ke liye temperature kam rakha hai
            "max_tokens": 4000
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=120)
            response.raise_for_status()
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Cleaning: Kabhi-kabhi AI markdown block ```html...``` bhej deta hai, use hatane ke liye
            clean_content = content.replace("```html", "").replace("```", "").strip()
            
            return {"title": topic, "body": clean_content, "status": "success"}
        except Exception as e:
            return {"title": topic, "body": f"Bot Logic Error: {str(e)}", "status": "error"}
