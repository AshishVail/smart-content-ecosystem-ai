import os
import requests
import json

class SmartWriter:
    def __init__(self, api_key):
        """
        AI Article Writer Engine
        api_key: Groq API Key jo main.py se pass hogi
        """
        self.api_key = api_key
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def generate_article(self, topic):
        """
        Groq API ka use karke SEO article generate karega
        """
        if not self.api_key:
            return {"error": "API Key missing", "body": ""}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # SEO Optimized Prompt
        prompt = f"""
        Write a professional, high-quality SEO blog post about: {topic}.
        Include a catchy title, introduction, subheadings, and a conclusion.
        Format the output in clean HTML (using <h2>, <p> tags).
        Language: Hinglish (mix of Hindi and English) for better engagement.
        """

        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "You are an expert SEO Content Writer."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            content = result['choices'][0]['message']['content']
            
            # Simple parsing for Title and Body
            lines = content.split('\n')
            title = lines[0].replace('#', '').strip()
            body = "\n".join(lines[1:])
            
            return {
                "title": title if title else topic,
                "body": body
            }

        except Exception as e:
            return {"error": str(e), "body": f"Failed to generate content: {e}"}

# Testing code (Optional)
if __name__ == "__main__":
    test_key = "your_test_key_here"
    writer = SmartWriter(api_key=test_key)
    print(writer.generate_article("Testing AI"))
