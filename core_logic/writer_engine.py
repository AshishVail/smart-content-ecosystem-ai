```python name=writer_engine.py
import os
import logging
import json
import re
from typing import Optional, Dict
from groq import Groq, RateLimitError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("core_logic.writer_engine")

class SmartWriter:
    """
    SmartWriter generates elite-level SEO HTML blog articles using the Groq Llama 3.3 70B model.
    Ensures:
    - Proper heading hierarchy and semantic HTML.
    - Focus keyword SEO injection.
    - FAQ section and strict mobile-first paragraph length.
    - No markdown or tables, pure HTML only.
    """

    DEFAULT_MODEL = "llama-3.3-70b-versatile"
    DEFAULT_TIMEOUT = 120  # seconds
    FOCUS_MIN = 10
    FOCUS_MAX = 15

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize SmartWriter with Groq API key.

        Args:
            api_key (str, optional): Groq API Key. If not provided, load from env.
            **kwargs: Absorbs unexpected args for robustness.
        """
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise EnvironmentError("Groq API key not set. Use api_key or set GROQ_API_KEY.")
        self.client = Groq(api_key=self.api_key)
        self.model = self.DEFAULT_MODEL

    def generate_article(self, topic: str, keyword: str, word_count: int = 1200, **kwargs) -> Dict[str, str]:
        """
        Generate a fully HTML-formatted SEO blog post.

        Args:
            topic (str): The main topic/title (used in <h1>)
            keyword (str): The SEO focus keyword.
            word_count (int): Target word count (default 1200)

        Returns:
            dict: {"title": topic, "body": html_content, "status": "success" or "error"}
        """
        # Build AI system and user prompts
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(topic, keyword, word_count)

        try:
            logger.info("Requesting article from Groq Llama 3.3 70B...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.6,
                max_tokens=4096,
                timeout=self.DEFAULT_TIMEOUT
            )
            raw = response.choices[0].message.content.strip()
            html = self._clean_html(raw)
            title = self._extract_title(html, fallback=topic)
            logger.info("Article generated successfully.")
            return {"title": title, "body": html, "status": "success"}
        except RateLimitError as e:
            logger.error("Groq rate limit exceeded: %s", e)
            return {"title": topic, "body": "", "status": "error"}
        except Exception as e:
            logger.error("Groq API/Parsing error: %s", e)
            return {"title": topic, "body": "", "status": "error"}

    def _build_system_prompt(self) -> str:
        """
        Build the system prompt for Groq API, enforcing HTML/SEO guidelines.
        """
        return (
            "You are an expert SEO blog writer and strictly output PURE HTML code only. "
            "For every article:\n"
            "- Use exactly one <h1> at the top for the article title.\n"
            "- Organize with more than 6 <h2> and several <h3> subsections; use a deep heading hierarchy.\n"
            "- Integrate the focus keyword NATURALLY 10-15 times (not repetitive, well-distributed), always wrapped in <strong> tags.\n"
            "- Only use <ul> and <li> elements for bullet/numbered lists; strictly forbid <table>, Markdown, or any non-HTML markup.\n"
            "- Use short, mobile-first paragraphs (2-3 sentences per <p> at most) for readability.\n"
            "- End with a comprehensive FAQ using several <h4> questions with clear answers below each.\n"
            "- Absolutely NO Markdown wrappers, YAML blocks or code fences in your output – only valid HTML.\n"
            "Never use any <!-- --> comments."
        )

    def _build_user_prompt(self, topic: str, keyword: str, word_count: int) -> str:
        """
        Build the user prompt, providing all must-have logic for HTML and SEO.
        """
        return (
            f"Write a detailed, production-grade blog post in PURE HTML."
            f"\nTitle/Topic: {topic}\n"
            f"SEO Focus Keyword: {keyword}."
            f"\nTarget Word Count: {word_count}.\n"
            f"Article Requirements:\n"
            "- <h1> for the title.\n"
            "- Use at least 6 <h2> and several <h3> as a nested hierarchy.\n"
            "- Include the keyword {keyword} 10 to 15 times, each occurrence wrapped in <strong> tags for SEO (but never repetitive).\n"
            "- Keep each <p> to 2-3 sentences maximum for mobile readability.\n"
            "- End with a comprehensive <h2>FAQ</h2> section, using <h4> for each FAQ question and a clear answer after each.\n"
            "- Use only <ul> and <li> for all lists; never use <table> or markdown symbols.\n"
            "Strip all code fences or non-HTML wrappers from your response before sending."
        )

    def _clean_html(self, text: str) -> str:
        """
        Strip any markdown/code fences or non-HTML wrappers.
        Removes leading/trailing code blocks, ```html or ``` marks, and unwanted YAML/markdown.
        """
        cleaned = re.sub(r'^(```\w*|---|yaml:|html:)+', '', text, flags=re.IGNORECASE | re.MULTILINE)
        cleaned = re.sub(r'(```)+$', '', cleaned, flags=re.MULTILINE)
        cleaned = cleaned.strip()
        # Remove any lingering code fences anywhere in the text
        cleaned = re.sub(r'```[\s\S]*?```', '', cleaned)
        return cleaned

    def _extract_title(self, html: str, fallback: str) -> str:
        """
        Extract the <h1> title from the HTML. If not found, uses fallback topic.
        """
        match = re.search(r'<h1[^>]*>(.*?)</h1>', html, flags=re.IGNORECASE | re.DOTALL)
        if match:
            title = match.group(1).strip()
            title = re.sub(r'<.*?>', '', title)
            return title
        return fallback

if __name__ == "__main__":
    topic = input("Enter the article topic: ").strip()
    keyword = input("Enter the focus keyword: ").strip()
    writer = SmartWriter()
    result = writer.generate_article(topic=topic, keyword=keyword)
    print("\n=== TITLE ===\n", result["title"])
    print("\n=== HTML BODY ===\n", result["body"])
```
