import os
import json
import logging
from groq import Groq

# Logging setup for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SmartWriter")

class SmartWriter:
    """
    Professional AI Writer Engine optimized for Render deployment.
    Uses Llama-3-70b via Groq for high-speed article generation.
    """

    def __init__(self, model="llama-3-70b-8192"):
        # Fetching API Key from environment variables
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            logger.error("Environment variable GROQ_API_KEY is missing!")
            raise EnvironmentError("GROQ_API_KEY not found.")
        
        self.client = Groq(api_key=api_key)
        self.model = model

    def generate_article(self, keyword, tone="professional"):
        """
        Generates a structured SEO article.
        Returns a dictionary with 'title' and 'body'.
        """
        system_instructions = (
            "You are a master SEO content writer. Create a detailed, long-form article. "
            "Structure: H1 for Title, H2/H3 for subheadings, bullet points, and bold text. "
            "STRICT RULE: Return ONLY a valid JSON object like this: "
            "{\"title\": \"Article Title\", \"body\": \"Full Markdown Content\"}"
        )

        user_query = f"Write a comprehensive SEO article about '{keyword}' in a '{tone}' tone."

        try:
            logger.info(f"Starting generation for keyword: {keyword}")
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_instructions},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.7,
                max_tokens=4096
            )

            raw_response = completion.choices[0].message.content.strip()
            return self._parse_json_safely(raw_response)

        except Exception as e:
            logger.error(f"Generation failed: {str(e)}")
            return {"title": "Error", "body": f"Failed to generate content: {str(e)}"}

    def _parse_json_safely(self, text):
        """
        Cleans the AI response and converts it into a Python dictionary.
        """
        try:
            # Removing markdown code blocks if AI adds them
            cleaned_text = text
            if "```json" in cleaned_text:
                cleaned_text = cleaned_text.split("```json")[1].split("```")[0]
            elif "```" in cleaned_text:
                cleaned_text = cleaned_text.split("```")[1].split("```")[0]
            
            return json.loads(cleaned_text.strip())
        except Exception:
            logger.warning("JSON parsing failed, returning raw text as body.")
            return {"title": "Generated Content", "body": text}

if __name__ == "__main__":
    # This block is only for local testing. 
    # Hardcoded values prevent Render from hanging on input()
    test_keyword = "Future of Artificial Intelligence"
    writer = SmartWriter()
    result = writer.generate_article(test_keyword)
    print(f"Status: Success\nTitle: {result.get('title')}")
