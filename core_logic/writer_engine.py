import os
import re
import logging
from typing import Optional, Dict
from groq import Groq, RateLimitError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("core_logic.writer_engine")

class SmartWriter:
    """
    SmartWriter generates high-authority, 2000+ word SEO articles as pure, semantic HTML using Groq's Llama 3.3 70B.
    - Handles key via init or os.environ["GROQ_API_KEY"], absorbs extra kwargs.
    - AI produces: <h1>, 8-10+ <h2>, nested <h3>/<h4>; {keyword} 15-20 times in <strong>;
      expert <ul>/<li>, comparative HTML <table> (if relevant),
      intro/key takeaways, body, 6+ advanced FAQ <h4>, mobile-first <p>.
    - Output is dict {title, body, status} with all markdown and fences stripped.
    """

    DEFAULT_MODEL = "llama-3.3-70b-versatile"
    TIMEOUT = 180  # seconds for 2000+ words

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Args:
            api_key (str, optional): Groq API key. If not provided, uses GROQ_API_KEY env var.
            **kwargs: For argument mismatch tolerance.
        """
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise EnvironmentError("GROQ_API_KEY not set and api_key not passed.")
        self.client = Groq(api_key=self.api_key)
        self.model = self.DEFAULT_MODEL

    def generate_article(self, topic: str, keyword: str, **kwargs) -> Dict[str, str]:
        """
        Generates a 2000+ word, HTML, SEO-perfect long-form article.

        Args:
            topic (str): Article topic/title (in <h1>)
            keyword (str): Focus keyword, used 15-20 times in <strong>
        Returns:
            dict: {title, body, status}
        """
        prompt = self._build_system_prompt(topic, keyword)
        user_message = self._build_user_message(topic, keyword)
        try:
            logger.info("Requesting Groq Llama 3.3 70B article...")
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
            # Expect all HTML in response
            raw = response.choices[0].message.content.strip()
            html = self._clean_html(raw)
            title = self._extract_title(html, fallback=topic)
            logger.info("Article generated and cleaned successfully.")
            return {"title": title, "body": html, "status": "success"}
        except RateLimitError as e:
            logger.error("Groq rate limit exceeded: %s", e)
            return {"title": topic, "body": "", "status": "error"}
        except Exception as e:
            logger.error("Error in Groq/parse: %s", e)
            return {"title": topic, "body": "", "status": "error"}

    def _build_system_prompt(self, topic: str, keyword: str) -> str:
        """
        Create the detailed system prompt for the LLM.
        """
        return (
            f"You are 'SmartWriter', the world's top-tier SEO+HTML blog generator. "
            "Write an article about the given topic using these STRICT RULES:\n"
            "1. Output PURE HTML (absolutely no markdown, yaml, or codeblocks).\n"
            "2. Exactly one <h1> at the top for the title.\n"
            "3. Organize the article into at least ten sections:\n"
            "  - Use at least 8-10 <h2> tags for section headings.\n"
            "  - For nested topics within a section, use <h3> and <h4> as needed.\n"
            "4. Integrate the focus keyword '{keyword}' naturally 15-20 times, always in <strong> tags, well-spaced, never stuffed.\n"
            "5. Introduction: Engaging hook (<p>), immediately followed by a <div class='key-takeaways'><h2>Key Takeaways</h2><ul>...</ul></div> box.\n"
            "6. For any lists, always use <ul> and <li> (never <ol> or markdown lists).\n"
            "7. If the data is comparative (vs, benefits vs drawbacks, etc), use a valid, semantic HTML <table> with <thead>, <tr>, <th>, <td>.\n"
            "8. Mobile-first readability: No <p> should have more than 2 sentences; frequently break into extra <p> for visual white space. If a rule or list is repeated, use <br> for further breaks.\n"
            "9. Advanced FAQ: At least 6 deep expert questions in <h4>, each with a thorough answer below.\n"
            "10. Conclude with a full summary section and a strong call-to-action (<h2>Conclusion</h2>)."
            "11. DO NOT USE markdown symbols, YAML, *** or --- or ```html anywhere. "
            "12. Output only pure HTML, no comments, no instructions, no explanations. "
            "13. Any keyword synonym/variant should also appear in a <strong> tag for SEO boost."
        )

    def _build_user_message(self, topic: str, keyword: str) -> str:
        """
        Provides concrete user instruction for LLM for the topic and keyword context.
        """
        return (
            f"Write an elite-quality, human-like, SEO-optimized article about '{topic}', "
            f"targeting the focus keyword '{keyword}'. "
            "The article MUST be at least 2000 words, very detailed, with all sections and requirements above."
        )

    def _clean_html(self, text: str) -> str:
        """
        Strip all markdown/triple-backtick blocks, YAML, or any AI preamble. Return pure HTML.
        """
        # Remove code fences and any trailing markdown
        cleaned = re.sub(r"^(```[a-zA-Z0-9]*\s*)+", "", text, flags=re.MULTILINE)
        cleaned = re.sub(r"(```)+$", "", cleaned, flags=re.MULTILINE)
        cleaned = cleaned.strip(" \n")
        # Remove standalone Markdown headings or lines starting with * or --- etc
        cleaned = re.sub(r"\n\*+\s*\n", "\n", cleaned)
        cleaned = re.sub(r"\n-{3,}\n", "\n", cleaned)
        # Remove yaml front-matter if present
        cleaned = re.sub(r"^---\s*[\s\S]{0,200}?---\s*", "", cleaned, flags=re.MULTILINE)
        # Remove lines like 'Here is the article:', 'Below is the HTML:', etc.
        cleaned = re.sub(r"^.*?(<h1[\s>])", r"\1", cleaned, flags=re.DOTALL | re.IGNORECASE)
        return cleaned

    def _extract_title(self, html: str, fallback: str) -> str:
        """
        Extract <h1> from HTML, else fallback to topic.
        """
        match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.IGNORECASE | re.DOTALL)
        if match:
            title = match.group(1).strip()
            title = re.sub(r"<.*?>", "", title)
            return title
        return fallback
        
if __name__ == "__main__":
    topic = input("Enter article topic: ").strip()
    keyword = input("Enter SEO focus keyword: ").strip()
    writer = SmartWriter()
    result = writer.generate_article(topic=topic, keyword=keyword)
    print("\n=== TITLE ===\n", result)
