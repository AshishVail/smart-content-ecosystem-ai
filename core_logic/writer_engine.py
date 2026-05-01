import os
import re
import logging
from typing import Optional, Dict
from groq import Groq, RateLimitError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("core_logic.writer_engine")

class SmartWriter:
    """
    SmartWriter: Generates 2000+ word, highly formatted SEO HTML articles using Groq Llama 3.3 70B.
    - All heading tags (<h1>-<h4>) bolded (inner text wrapped in <strong>)
    - Focus keyword & synonyms strictly bolded via <strong>
    - <h2>Conclusion</h2> section fully bolded
    - Aggressive variability in sentence structure and hooks per NLP best practices
    - Complex <table> is required if the topic allows for comparison
    - Deep heading structure (12-15 subheads, silo-style)
    - Internal linking placeholder: "[Learn more about {keyword} here]"
    - __init__ absorbs **kwargs for interface stability
    - regex-based _clean_html() strips all markdown, code fences, and AI preambles
    - 300s timeout for long-generation reliability
    """

    DEFAULT_MODEL = "llama-3.3-70b-versatile"
    TIMEOUT = 300  # Allow up to 5 minutes for generation

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Args:
            api_key (str, optional): GROQ API key. If None, uses GROQ_API_KEY from env.
            **kwargs: absorbs extras for import safety
        """
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise EnvironmentError("GROQ_API_KEY env variable must be set or passed to SmartWriter.")
        self.client = Groq(api_key=self.api_key)
        self.model = self.DEFAULT_MODEL

    def generate_article(self, topic: str, keyword: str, **kwargs) -> Dict[str, str]:
        """
        Generates a 2000+ word SEO-optimized HTML article as described above.
        Args:
            topic (str): The <h1> title.
            keyword (str): The main focus keyword for SEO bolding.
        Returns:
            dict: {"title": topic, "body": clean_html, "status": "success"|"error"}
        """
        prompt = self._build_system_prompt(topic, keyword)
        user_message = self._build_user_message(topic, keyword)
        try:
            logger.info("Requesting Groq Llama 3.3 70B for SEO HTML generation...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.4,
                max_tokens=4096,
                timeout=self.TIMEOUT
            )
            raw = response.choices[0].message.content.strip()
            html = self._clean_html(raw)
            title = self._extract_bolded_title(html, fallback=topic)
            logger.info("Article generated and cleaned successfully.")
            return {"title": title, "body": html, "status": "success"}
        except RateLimitError as e:
            logger.error(f"Groq rate limit exceeded: {e}")
            return {"title": topic, "body": "", "status": "error"}
        except Exception as e:
            logger.error(f"Groq/parse error: {e}")
            return {"title": topic, "body": "", "status": "error"}

    def _build_system_prompt(self, topic: str, keyword: str) -> str:
        """
        Compose instructions for Llama 3.3 70B:
        - Aggressive bolding of headings
        - Reiterate all critical SEO/HTML format requirements
        """
        return (
            f"You are SmartWriter, an elite-level HTML SEO content generator."
            f" REQUIREMENTS (Strict, NO markdown, NO Key Takeaways section, NO introductory summaries):\n"
            f"1. The article must start IMMEDIATELY with an <h1> whose content is wrapped in <strong> tags: <h1><strong>Title Here</strong></h1>.\n"
            f"2. Break the subject into 12-15 or more deep, siloed sections using <h2>, <h3>, <h4>; all must have inner text wrapped in <strong> (e.g. <h3><strong>...</strong></h3> ).\n"
            f"3. Absolutely NO Key Takeaways box or summary at the start.\n"
            f"4. Whenever '{keyword}' or clear synonyms of it are used, always wrap with <strong>. (15-20 times, but only naturally placed; never keyword-stuffed!)\n"
            f"5. For each <h2> that acts as 'Conclusion', ensure the ENTIRE section (<h2><strong>Conclusion</strong></h2> plus all its text) is bolded.\n"
            f"6. Use at least one complex <table> with headers and multiple rows if the topic allows comparisons. Use <thead>, <tr>, <th>, <td> as appropriate.\n"
            f"7. Use professional <ul> and <li> for features/lists (no markdown bullets/ol/asterisks!).\n"
            f"8. Enforce strict mobile-first readability: break up text such that NO <p> exceeds two sentences; white space is created via frequent <br> or extra <p> tags.\n"
            f"9. The article must use rhetorical questions, conversational hooks, sentence variety, and burstiness for maximum human-like quality. Begin with a high-impact statement (never 'In this article...').\n"
            f"10. Insert at least one placeholder per article for internal linking: 'Learn more about {keyword} here' (verbatim, in context).\n"
            f"11. End with an 'Advanced FAQ' section: 6+ expert-level questions as <h4><strong>Question</strong></h4> with detailed answers after each.\n"
            f"12. The final product must be at least 2000 words long; otherwise add more content and detail."
            f"13. Absolutely NO markdown, YAML, *** or --- lines, or code fences anywhere (not even ```html). NO AI preambles or explanations."
        )

    def _build_user_message(self, topic: str, keyword: str) -> str:
        """
        Returns the concrete user prompt for the requested article.
        """
        return (
            f"Write a very long (at least 2000 words), SEO-focused, human-sounding HTML article about '{topic}'. "
            f"Follow all system instructions exactly. Never add 'Key Takeaways' or summary box, and NEVER use markdown."
        )

    def _clean_html(self, text: str) -> str:
        """
        Strips ALL code blocks, markdown, YAML, and any preamble or AI explanation.
        """
        # Remove code fences, <!-- comments -- >, markdown lines
        cleaned = re.sub(r"^(```[a-zA-Z0-9\-]*\s*)+", "", text, flags=re.MULTILINE)
        cleaned = re.sub(r"(```)+$", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"\A.*?(<h1>)", r"\1", cleaned, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r"^---.*?---\s*", "", cleaned, flags=re.MULTILINE | re.DOTALL)
        cleaned = re.sub(r"\*\*\*.*\*\*\*", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"^#+\s.*$", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"(<!--.*?-->)", "", cleaned, flags=re.DOTALL)
        cleaned = cleaned.strip(" \n")
        return cleaned

    def _extract_bolded_title(self, html: str, fallback: str) -> str:
        """
        Extract <h1><strong>Title</strong></h1> inner text. Fallback on topic.
        """
        match = re.search(r'<h1[^>]*>\s*<strong>(.*?)</strong>\s*</h1>', html, flags=re.IGNORECASE | re.DOTALL)
        if match:
            title = match.group(1).strip()
            title = re.sub(r"<.*?>", "", title)  # strip stray tags
            return title
        return fallback

if __name__ == "__main__":
    topic = input("Enter article topic: ").strip()
    keyword = input("Enter SEO focus keyword: ").strip()
    writer = SmartWriter()
    result = writer.generate_article(topic=topic, keyword=keyword)
    print("\n=== TITLE ===\n" + result["title"])
    print("\n=== HTML BODY ===\n" + result["body"])
