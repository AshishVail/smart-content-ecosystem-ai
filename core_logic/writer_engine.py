import os
import re
import logging
from typing import Optional, Dict
from groq import Groq, RateLimitError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("core_logic.writer_engine")

class SmartWriter:
    """
    SmartWriter: Generates long, human-like, SEO-dominating HTML articles using Groq Llama 3.3 70B.
    - Every heading tags (<h1>-<h4>) content bolded (<strong>)
    - Focus keyword always bolded using <strong>
    - Conclusion section fully bolded
    - Conversational, story-driven journalist tone with perplexity
    - Never use boring headings; always rephrase, always catchy
    - At least one in-depth comparison <table>
    - No Key Takeaways/summary box, no AI trash or markdown
    - At least 2500 words with 15+ deep subheadings (<h2>-<h4>)
    - Internal link placeholder: "For more insights, check out our guide on [Internal Link Here]."
    - __init__ with **kwargs for API/CLI stability
    - timeout=300 for long completions
    - Clean-up removes all markdown, code fences, and AI noise
    """

    DEFAULT_MODEL = "llama-3.3-70b-versatile"
    TIMEOUT = 300  # up to 5 minutes for long, complex responses

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise EnvironmentError("GROQ_API_KEY env variable must be set or passed to SmartWriter.")
        self.client = Groq(api_key=self.api_key)
        self.model = self.DEFAULT_MODEL

    def generate_article(self, topic: str, keyword: str, **kwargs) -> Dict[str, str]:
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
        Returns the most advanced, human-like SEO and HTML instruction set
        for Llama 3.3 70B under the 'bold everything' and anti-AI-detection mandate.
        """
        return (
            f"INSTRUCTIONS (Strict; follow precisely):\n\n"
            f"1. OUTPUT: Only pure, production-ready HTML (never markdown, never a code block, never YAML, never wrap in ``` or similar).\n"
            f"2. 'BOLD EVERYTHING' RULE:\n"
            f" - Every <h1>, <h2>, <h3>, <h4> content MUST be wrapped with <strong> tags. "
            f"   e.g. <h2><strong>This is a bold heading</strong></h2>.\n"
            f" - EVERY time the focus keyword '{keyword}' or any direct synonym appears in the article body, wrap it in <strong> tags. NEVER miss one.\n"
            f"3. STRUCTURE:\n"
            f" - Begin IMMEDIATELY with <h1><strong>{topic}</strong></h1> (no intro text before the h1).\n"
            f" - Create a 2500+ word body organized into at least 15 clever, deep, siloed sections "
            f"(<h2>, <h3>, <h4> as needed; always catchy, journalistic-style section titles, NO boring/generic headings, rephrase everything catchy and human).\n"
            f" - Every heading at any level must have inner contents wrapped in <strong> as above.\n"
            f" - NO 'Key Takeaways', no introductory summary box, no summary at start.\n"
            f"4. BODY CONTENT:\n"
            f" - Start with a true 'hook': a shocking stat, bold claim, or rhetorical question (never use 'In this article...'). "
            f"Use first-person, storytelling style; mix rhetorical hooks and commentary.\n"
            f" - Vary sentence lengths for human 'perplexity' and 'burstiness' (short, punchy lines then deeper dives; "
            f"use rhetorical questions and asides liberally; imagine a top journalist is writing for WIRED or TechCrunch).\n"
            f" - Feature lists must use semantic <ul> and <li>. Comparative information must use a well-structured HTML <table> with <thead>, <tr>, <th>, <td>—be creative, realistic, and detailed. If a table ever feels relevant, include it.\n"
            f" - At least 15-20 natural {keyword} (and close synonym) mentions, ALL bolded (<strong>).\n"
            f" - Insert, at a natural place, this sentence for internal linking: 'For more insights, check out our guide on [Internal Link Here].'\n"
            f"5. CONCLUSION:\n"
            f" - End with a clear heading: <h2><strong>Conclusion</strong></h2>.\n"
            f" - The ENTIRE conclusion section body text—everything from <h2>Conclusion</h2> to the closing—must be fully wrapped in <strong> tags. The text itself must be direct and have a strong call-to-action or final insight, never formulaic.\n"
            f"6. FAQ:\n"
            f" - After the conclusion, write an 'Advanced FAQ' section with at least 6 bolded <h4> questions and substantial, expert answers after each.\n"
            f"7. OUTPUT QUALITY:\n"
            f" - NEVER output markdown, triple backticks, yaml blocks, html comments, or any AI-styled preamble text. Only pure, semantically valid HTML, clean lines—ready for publishing as-is. No explanations, just the content.\n"
        )

    def _build_user_message(self, topic: str, keyword: str) -> str:
        """
        Yields the user message with explicit topic and keyword context.
        """
        return (
            f"Write a long, highly persuasive, narrative-style HTML article titled '{topic}' focused on the keyword '{keyword}'. "
            f"Make sure every subheading is catchy and bolded, every use of {keyword} is wrapped in <strong>, and the article fulfills all instructions above."
        )

    def _clean_html(self, text: str) -> str:
        """
        Removes ALL markdown, code fences, comments, AI-generated trash (e.g. "Type / to choose a block"), or HTML explanations.
        Leaves only pure HTML.
        """
        cleaned = re.sub(r"^(```[a-zA-Z0-9\-]*\s*)+", "", text, flags=re.MULTILINE)
        cleaned = re.sub(r"(```)+$", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"<!--.*?-->", "", cleaned, flags=re.DOTALL)
        cleaned = re.sub(r"^---.*?---\s*", "", cleaned, flags=re.MULTILINE | re.DOTALL)
        cleaned = re.sub(r"\*\*\*.*\*\*\*", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"^#+\s.*$", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"Type\s*/\s*to\s*choose\s*a\s*block.*(\n|$)", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"Here is( the)? (article|HTML code|a detailed answer):?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"^.+?(<h1>)", r"\1", cleaned, flags=re.DOTALL | re.IGNORECASE)
        cleaned = cleaned.strip(" \n\r\t")
        return cleaned

    def _extract_bolded_title(self, html: str, fallback: str) -> str:
        match = re.search(r'<h1[^>]*>\s*<strong>(.*?)</strong>\s*</h1>', html, flags=re.IGNORECASE | re.DOTALL)
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
    print("\n=== TITLE ===\n" + result["title"])
    print("\n=== HTML BODY ===\n" + result["body"])
