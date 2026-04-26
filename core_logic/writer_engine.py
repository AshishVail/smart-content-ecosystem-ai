import os
import json
import logging
import re
from groq import Groq, RateLimitError

# प्रोफेशनल लॉगिंग सेटअप
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WriterEngine")

# FIXED: Class name changed from SmartWriter to ContentWriter to match main.py
class ContentWriter:
    """
    Advanced SEO Content Engine.
    यह इंजन विशेष रूप से H1, H2, H3 और Bullet Points को सुरक्षित रखने के लिए बनाया गया है।
    """

    def __init__(self, api_key=None, model="llama-3.3-70b-versatile"):
        # FIXED: main.py से आने वाली API Key को प्राथमिकता दी गई है
        self.api_key = api_key or os.getenv("GROQ_API_KEY") or os.getenv("AI_API_KEY")
        
        if not self.api_key:
            logger.error("API KEY Missing.")
            raise EnvironmentError("Configuration Error: API KEY is not set.")
        
        self.client = Groq(api_key=self.api_key)
        self.model = model

    def _generate_strict_prompt(self, keyword):
        """
        AI को कड़े निर्देश देने के लिए प्रोम्पट।
        """
        return f"""
        Act as a Senior SEO Content Strategist. Your goal is to write a high-ranking article.
        
        KEYWORD: {keyword}
        
        CONTENT STRUCTURE RULES:
        1. H1 TITLE: Start with a catchy H1 title including the keyword.
        2. HEADINGS: Use at least 5-6 '##' (H2) and relevant '###' (H3) for sub-points.
        3. LISTS: Use '-' for bullet points and '1.' for steps. No exceptions.
        4. BOLDING: Bold all critical terms and keywords using **text**.
        5. TABLES: Create a Markdown table for key takeaways or data summary.
        6. LENGTH: The article must exceed 1500 words.
        
        OUTPUT FORMAT:
        You MUST respond ONLY with a JSON object in this format:
        {{
            "title": "Your H1 Title Here",
            "body": "Your full markdown content starting from Introduction..."
        }}
        """

    def generate_article(self, keyword, tone="professional"):
        logger.info(f"SEO Article Sequence Initiated: {keyword}")
        
        system_instructions = self._generate_strict_prompt(keyword)
        user_input = f"Topic: {keyword}. Tone: {tone}. Create a complete SEO optimized masterpiece."

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_instructions},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.5, 
                max_tokens=8192,
                top_p=1,
                stream=False
            )

            raw_text = completion.choices[0].message.content.strip()
            # Parse result and return only the 'body' string for main.py compatibility
            result = self._parse_and_clean_content(raw_text)
            return result.get("body") if isinstance(result, dict) else result

        except Exception as e:
            logger.error(f"Engine Failure: {str(e)}")
            return None

    def _parse_and_clean_content(self, raw_text):
        """
        यह फंक्शन AI के गंदे JSON को साफ़ करके उसे सुंदर Markdown में बदलता है।
        """
        try:
            if "```json" in raw_text:
                raw_text = re.search(r'```json\s*(.*?)\s*```', raw_text, re.DOTALL).group(1)
            
            data = json.loads(raw_text)
            body_content = data.get('body', "")
            
            if body_content.startswith('{"title":'):
                nested = json.loads(body_content)
                body_content = nested.get('body', body_content)

            return {
                "title": data.get('title', "Professional SEO Article"),
                "body": body_content
            }

        except Exception as e:
            logger.warning(f"Standard JSON parse failed, using regex recovery. Error: {e}")
            try:
                title_match = re.search(r'"title":\s*"(.*?)"', raw_text)
                body_match = re.search(r'"body":\s*"(.*)"', raw_text, re.DOTALL)
                
                title = title_match.group(1) if title_match else "SEO Optimized Content"
                body = body_match.group(1) if body_match else raw_text
                
                body = body.replace("\\n", "\n").replace('\\"', '"')
                return {"title": title, "body": body}
            except:
                return {"title": "Article Generated", "body": raw_text}

# Logic Complete.
