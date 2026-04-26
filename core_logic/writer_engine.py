import os
import json
import logging
import re
from groq import Groq, RateLimitError

# प्रोफेशनल लॉगिंग सेटअप
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WriterEngine")

class SmartWriter:
    """
    Advanced SEO Content Engine.
    यह इंजन विशेष रूप से H1, H2, H3 और Bullet Points को सुरक्षित रखने के लिए बनाया गया है।
    """

    def __init__(self, model="llama-3.3-70b-versatile"):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        if not self.api_key:
            logger.error("GROQ_API_KEY Missing.")
            raise EnvironmentError("Configuration Error: GROQ_API_KEY is not set.")
        
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
                temperature=0.5, # स्ट्रक्चर बनाए रखने के लिए कम टेम्परेचर
                max_tokens=8192,
                top_p=1,
                stream=False
            )

            raw_text = completion.choices[0].message.content.strip()
            return self._parse_and_clean_content(raw_text)

        except Exception as e:
            logger.error(f"Engine Failure: {str(e)}")
            return {"title": "Error", "body": f"Technical Issue: {str(e)}"}

    def _parse_and_clean_content(self, raw_text):
        """
        यह फंक्शन AI के गंदे JSON को साफ़ करके उसे सुंदर Markdown में बदलता है।
        """
        try:
            # Markdown Code Blocks हटाना
            if "```json" in raw_text:
                raw_text = re.search(r'```json\s*(.*?)\s*```', raw_text, re.DOTALL).group(1)
            
            # JSON लोड करना
            data = json.loads(raw_text)
            
            # 'body' को साफ़ करना (Escaped characters को असली New Lines में बदलना)
            body_content = data.get('body', "")
            
            # अगर AI ने JSON के अंदर JSON डाल दिया है, तो उसे ठीक करें
            if body_content.startswith('{"title":'):
                nested = json.loads(body_content)
                body_content = nested.get('body', body_content)

            return {
                "title": data.get('title', "Professional SEO Article"),
                "body": body_content
            }

        except Exception as e:
            logger.warning(f"Standard JSON parse failed, using regex recovery. Error: {e}")
            # Regex के ज़रिए टाइटल और बॉडी निकालना अगर JSON टूट गया है
            try:
                title_match = re.search(r'"title":\s*"(.*?)"', raw_text)
                body_match = re.search(r'"body":\s*"(.*)"', raw_text, re.DOTALL)
                
                title = title_match.group(1) if title_match else "SEO Optimized Content"
                body = body_match.group(1) if body_match else raw_text
                
                # \n को असली न्यू लाइन में बदलना
                body = body.replace("\\n", "\n").replace('\\"', '"')
                
                return {"title": title, "body": body}
            except:
                return {"title": "Article Generated", "body": raw_text}

# Logic Complete.
