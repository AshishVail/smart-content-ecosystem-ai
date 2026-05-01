import os
import re
import logging
from typing import Optional, Dict
from groq import Groq, RateLimitError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("core_logic.writer_engine")

class SmartWriter:
    """
    SmartWriter generates 2500+ word, first-person, high-authority HTML articles
    that pass AI detection and dominate Google rankings.
    - First-person, conversational, narrative flow with varied sentence length and hooks
    - Analytical analogies, scenarios, and rhetorical questions
    - AGGRESSIVE FORMATTING: <h1>-<h4> headings bolded; focus keyword bolded only 4-5 times
    - Catchy, real-world, non-boring headings
    - Clean HTML: complex <table>, <ul>/<li> lists, <br> for white space, 2-3 sentences per <p>
    - Internal link placeholders (twice)
    - Conclusion section fully bolded
    - Key Takeaways forbidden
    - Markdown/code/preamble cleaning
    """

    DEFAULT_MODEL = "llama-3.3-70b-versatile"
    TIMEOUT = 300  # seconds

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise EnvironmentError("Must provide GROQ_API_KEY in env or as argument.")
        self.client = Groq(api_key=self.api_key)
        self.model = self.DEFAULT_MODEL

    def generate_article(self, topic: str, keyword: str, **kwargs) -> Dict[str, str]:
        system_prompt = self._build_system_prompt(topic, keyword)
        user_message = self._build_user_message(topic, keyword)
        try:
            logger.info("Requesting 2500+ word, SEO-optimized article from Groq...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.6,
                max_tokens=4000,
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
        return (
            f"You are SmartWriter, a senior SEO content strategist and tech blogger."
            f"\nINSTRUCTIONS (Follow exactly, be creative, 100% HTML):"
            f"\n1. Use only pure HTML output. No markdown, no yaml, no code fences, no explanations."
            f"\n2. Start immediately with an <h1>—the article title—with all inner text in <strong> tags: <h1><strong>Title Here</strong></h1>."
            f"\n3. All <h2>, <h3>, and <h4> headings must also wrap ALL their content in <strong> tags (e.g. <h3><strong>Why This Changes Everything</strong></h3>)."
            f"\n4. Absolutely NEVER include a Key Takeaways box, summary panels, or anything of the sort. Go straight into the narrative."
            f"\n5. Write in 1st person, conversational style (use I, We, Our). Use contractions for authenticity."
            f"\n6. Every section and heading must be catchy and benefit-driven. Boring headings are forbidden."
            f"\n   Example: Instead of 'Artificial Intelligence in Healthcare', write 'Saving Lives: The Unexpected Way Algorithms are Redefining Surgery.'"
            f"\n7. Use analogies (e.g., compare AI to the invention of electricity), hypothetical scenarios, and rhetorical questions."
            f"\n8. For perplexity and burstiness, alternate between short, punchy sentences and long, detailed ones—never monotone."
            f"\n9. Use a minimum of 15 section headers (<h2> to <h4>), building a deep silo around the topic."
            f"\n10. Bold the keyword '{keyword}' with <strong> tags, but only where most impactful—strictly 4 to 5 times in the entire article. Use plain text for all other mentions."
            f"\n11. The entire conclusion section, starting with <h2><strong>Conclusion</strong></h2>, must be bolded (wrap all conclusion body text in <strong>)."
            f"\n12. No <p> should be longer than 2-3 sentences (use <br> for more white space if sections start looking dense)."
            f"\n13. For any lists, always use <ul> and <li>. For comparisons (e.g., pros/cons or alternatives or technology features), use a fully semantic HTML <table> with headers."
            f"\n14. Somewhere near the 1/3 mark and again near the end, include this paragraph exactly (adjust for topic):"
            f"\n   <p><em>Check out our deep dive into [Internal Link Placeholder] for more details.</em></p>"
            f"\n15. After conclusion, add an 'Advanced FAQ' with at least 6 <h4><strong>...</strong></h4> expert questions and substantial answers."
            f"\n16. Only output clean, semantic HTML. No markdown symbols (***, ###, **, -), no code fences (```html), no 'Sure, here is', no AI filler, no comments, no explanations."
            f"\n17. Target at least 2500 words. If it's too short, keep expanding."
        )

    def _build_user_message(self, topic: str, keyword: str) -> str:
        return (
            f"Write a very long, SEO-optimized, human-sounding HTML article titled '{topic}'."
            f" Focus on the keyword '{keyword}' as instructed. Follow all above rules exactly. Use only HTML, never markdown, yaml, or any code fence."
        )

    def _clean_html(self, text: str) -> str:
        # Remove all code fences, markdown, comments, and AI filler/preambles
        cleaned = re.sub(r"^(```[a-zA-Z0-9\-]*\s*)+", "", text, flags=re.MULTILINE)
        cleaned = re.sub(r"(```)+$", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"<!--.*?-->", "", cleaned, flags=re.DOTALL)
        cleaned = re.sub(r"^---.*?---\s*", "", cleaned, flags=re.MULTILINE | re.DOTALL)
        cleaned = re.sub(r"\*\*\*.*\*\*\*", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"^#+\s.*$", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"Type\s*/\s*to\s*choose\s*a\s*block.*(\n|$)", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"(Here is|Sure,|Below is|Output:|Answer:|Take a look at the following|Let's get started).*?(<h1>)", r"\2", cleaned, flags=re.DOTALL | re.IGNORECASE)
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
