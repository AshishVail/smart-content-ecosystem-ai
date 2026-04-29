import os
import requests

class SmartWriter:
    def __init__(self, GROQ_API_KEY=None, **kwargs):
        # Multiple sources se API key check karna taaki error na aaye
        self.api_key = kwargs.get('api_key') or GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def generate_article(self, topic):
        if not self.api_key:
            return {"title": topic, "body": "Error: API Key missing in Render Environment", "status": "error"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Ab hum AI ko ek Professional Content Strategist banayenge
        prompt = f"""
        Write an advanced, high-quality, and SEO-optimized professional blog post about: "{topic}".
        
        STRICT LAYOUT RULES:
        1. Use <h1> for the catchy main title.
        2. Use a mix of <h2> and <h3> subheadings to break down the topic.
        3. KEYWORD INTEGRATION: Naturally use the focus keyword "{topic}" 5 to 6 times throughout the article body.
        4. READABILITY: Keep paragraphs short (3-4 lines max) to create 'Blank Space' for better user experience.
        5. PROFESSIONAL COLUMN/TABLE: Create a detailed HTML <table> to compare key features, pros/cons, or data related to "{topic}". Make it look professional.
        6. BULLET POINTS: Use <ul> and <li> for explaining complex points or lists.
        7. BOLD TEXT: Use <strong> tags for important terms within the text.
        8. CONCLUSION: Write a strong final thought with a 'Call to Action'.
        9. NO "Focus Keywords" section at the end—instead, embed them naturally in the text.
        
        Write at least 800-1000 words. Output MUST be in clean, ready-to-paste HTML format.
        """

        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system", 
                    "content": "You are a world-class SEO Writer who specializes in high-ranking digital content. You write in a human-like, engaging, and professional tone."
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.6, # Balance between factual and creative
            "max_tokens": 4000  # Taaki lamba article beech mein na kate
        }

        try:
            # Timeout ko 90 seconds rakha hai kyunki lamba article time leta hai
            response = requests.post(self.api_url, headers=headers, json=data, timeout=90)
            response.raise_for_status()
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            return {
                "title": topic, 
                "body": content, 
                "status": "success"
            }
        except Exception as e:
            return {
                "title": topic, 
                "body": f"Technical Error: {str(e)}", 
                "status": "error"
            }
