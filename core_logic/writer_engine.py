import os
import json
import logging
import re
from groq import Groq, RateLimitError

# Configure professional logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WriterEngine")

class SmartWriter:
    """
    High-Performance SEO Content Architect.
    Forces structural compliance (H1, H2, H3, Bullets) and high keyword density.
    """

    def __init__(self, model="llama-3.3-70b-versatile"):
        """
        Initializes the Groq client and handles configuration.
        """
        self.api_key = os.getenv("GROQ_API_KEY", "")
        if not self.api_key:
            logger.error("System Failure: GROQ_API_KEY is not defined.")
            raise EnvironmentError("Critical Configuration Missing: GROQ_API_KEY.")
        
        self.client = Groq(api_key=self.api_key)
        self.model = model

    def _generate_system_instructions(self, keyword):
        """
        Provides the AI with strict SEO and structural guidelines.
        """
        return (
            "You are a Senior SEO Content Specialist. Your goal is to write a viral, "
            "authoritative, and highly structured article. "
            f"FOCUS KEYWORD: '{keyword}'\n\n"
            "STRICT STRUCTURAL RULES:\n"
            "1. H1 TITLE: Create a magnetic, SEO-optimized title containing the keyword.\n"
            "2. H2 & H3 HEADINGS: Organize the content with at least 4-5 H2 headings and relevant H3 sub-headings.\n"
            "3. FORMATTING: Use bold text for importance, bullet points for lists, and numbered lists where appropriate.\n"
            "4. KEYWORD DENSITY: Naturally integrate the focus keyword throughout the introduction, headings, and conclusion.\n"
            "5. LENGTH: Target a minimum of 1500 words for deep coverage.\n"
            "6. TABLE: If relevant, include a summary table of key points.\n"
            "7. CONCLUSION: End with a powerful summary and a FAQ section.\n\n"
            "OUTPUT PROTOCOL:\n"
            "Respond ONLY with a valid JSON object. DO NOT include any text outside the JSON.\n"
            "Structure: {\"title\": \"H1 Title Here\", \"body\": \"Full Markdown Article Here\"}"
        )

    def generate_article(self, keyword, tone="professional"):
        """
        Executes the content generation workflow with SEO parameters.
        """
        logger.info(f"SEO Generation started for: {keyword}")
        
        system_prompt = self._generate_system_instructions(keyword)
        user_prompt = (
            f"Keyword: '{keyword}'. Tone: {tone}. Write a long-form, high-authority "
            "article that follows all provided structural and SEO guidelines."
        )

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.6, # Lower temperature for more structured/factual writing
                max_tokens=8192, # Allowing room for long articles
                top_p=1
            )

            response_payload = completion.choices[0].message.content.strip()
            return self._process_and_validate_payload(response_payload)

        except RateLimitError:
            logger.error("Rate limit hit.")
            return {"title": "Rate Limit Exceeded", "body": "Please wait a moment."}
        except Exception as e:
            logger.error(f"Engine Error: {str(e)}")
            return {"title": "Error", "body": f"The process failed: {str(e)}"}

    def _process_and_validate_payload(self, raw_content):
        """
        Processes and sanitizes the AI output to ensure perfect JSON parsing.
        """
        try:
            # Clean possible markdown wrap
            clean_content = raw_content
            if "```json" in raw_content:
                match = re.search(r'```json\s*(.*?)\s*```', raw_content, re.DOTALL)
                if match:
                    clean_content = match.group(1)
            
            # Initial Parse
            data = json.loads(clean_content)

            # Fix for nested JSON strings in title or body
            if isinstance(data.get('title'), str) and '{"title":' in data.get('title'):
                data = json.loads(data['title'])

            # Final check to ensure we have title and body
            return {
                "title": data.get('title', "Untitled SEO Article"),
                "body": data.get('body', clean_content)
            }
        
        except Exception as e:
            logger.warning(f"JSON Recovery triggered: {e}")
            # Manual fallback
            content_lines = raw_content.split('\n')
            title = content_lines[0].replace("#", "").strip()
            return {"title": title, "body": raw_content}

# End of SEO Logic.
