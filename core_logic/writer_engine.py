import os
import json
import logging
from groq import Groq, RateLimitError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("core_logic.writer_engine")

DEFAULT_MODEL = "llama-3-70b-8192"

SYSTEM_PROMPT = (
    "You are SmartWriter, an AI that generates SEO-optimized, human-like long-form articles with:\n"
    "- Title as an H1 (Markdown)\n"
    "- H2 and H3 headings for structure\n"
    "- Bullet points and numbered lists where relevant\n"
    "- Bold main keywords and important terms (Markdown: **like this**)\n"
    "- Engaging introduction and strong conclusion\n"
    "Always return a JSON as:\n"
    "{\n  \"title\": \"...\",\n  \"body\": \"...\" \n}\n"
    "The body should be at least 2000 words, return all well-formatted in Markdown."
)

class SmartWriter:
    """
    SmartWriter generates SEO-optimized articles using Groq's Llama-3 model.
    """

    def __init__(self, model: str = DEFAULT_MODEL):
        """
        Initialize Groq client and set model.
        """
        groq_api_key = os.getenv("GROQ_API_KEY", "")
        if not groq_api_key:
            raise EnvironmentError("GROQ_API_KEY not set in environment.")
        self.client = Groq(api_key=groq_api_key)
        self.model = model

    def generate_article(self, keyword: str, tone: str = "professional") -> dict:
        """
        Generate an article based on the keyword and tone.
        Returns a dict with keys 'title', 'body', and 'raw'.
        """
        user_prompt = (
            f'Write an in-depth article about "{keyword}".\n'
            f'Tone: {tone}.\n'
            "Strictly return ONLY the JSON object {\"title\":..., \"body\":...} as instructed above."
        )
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,
                max_tokens=4096
            )
            text = response.choices[0].message.content.strip()
            data = self._parse_output(text)
            return {"title": data.get("title", ""), "body": data.get("body", ""), "raw": text}
        except RateLimitError as e:
            logger.error(f"Groq Rate Limit: {e}")
            return {"title": "", "body": "", "raw": "", "error": "Rate limit exceeded."}
        except Exception as e:
            logger.error(f"Groq error or JSON parsing failed: {e}")
            return {"title": "", "body": "", "raw": "", "error": str(e)}

    def _parse_output(self, text: str) -> dict:
        """
        Robust JSON output parser. Handles common LLM formatting issues.
        """
        try:
            t = text
            if t.startswith("```json"):
                t = t.lstrip("` \n")[6:]
            t = t.strip()
            if t.endswith("```"):
                t = t[: -3].strip()
            return json.loads(t)
        except Exception:
            lines = text.splitlines()
            title = ""
            body = ""
            found_title = False
            for line in lines:
                if line.startswith("# "):
                    title = line.strip("# ").strip()
                    found_title = True
                    continue
                if found_title:
                    body += line + "\n"
            if not title:
                title = ""
            if not body:
                body = text
            return {"title": title, "body": body}

if __name__ == "__main__":
    keyword = input("Enter the keyword for the article: ").strip()
    tone = input("Enter the tone (professional, casual, informative, creative): ").strip() or "professional"
    writer = SmartWriter()
    result = writer.generate_article(keyword=keyword, tone=tone)
    print("\nTITLE:\n", result["title"])
    print("\nBODY:\n", result["body"] if result["body"] else result["raw"])
```
