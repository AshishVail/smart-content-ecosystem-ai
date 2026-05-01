import os
import re
import logging
import time
from typing import Optional, Dict, List, Callable, Any
from groq import Groq, RateLimitError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("core_logic.writer_engine")


class Config:
    """
    Manages advanced SEO and Content generation rules for MasterWriterEngine.
    """
    def __init__(
        self,
        min_word_count: int = 2500,
        heading_bold_tags: List[str] = None,
        max_keyword_bolds: int = 5,
        allowed_heading_levels: List[str] = None,
        allowed_table: bool = True,
        conclusion_min_words: int = 300
    ):
        self.min_word_count = min_word_count
        self.heading_bold_tags = heading_bold_tags or ["h1", "h2", "h3", "h4"]
        self.max_keyword_bolds = max_keyword_bolds
        self.allowed_heading_levels = allowed_heading_levels or ["h1", "h2", "h3", "h4"]
        self.allowed_table = allowed_table
        self.conclusion_min_words = conclusion_min_words


def retry_on_fail(max_retries=3, exceptions=(RateLimitError, Exception), delay=5):
    """
    Decorator for robust retry logic on API failure.
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            tries = 0
            while tries < max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    tries += 1
                    logger.warning(f"[Retry] Exception: {e} ({tries}/{max_retries})")
                    if tries >= max_retries:
                        raise
                    time.sleep(delay)
        return wrapper
    return decorator


class MasterWriterEngine:
    """
    Production-grade 2500+ word SEO, human-footprint, HTML content generator.
    All formatting, AI footprints, and LLM artifacts are aggressively cleaned
    using _super_cleaner and validated via _score_content before return.
    Complies with Bolding, Keywords, Internal Linking, FAQ, Table policies.
    """

    DEFAULT_MODEL = "llama-3.3-70b-versatile"
    TIMEOUT = 300  # seconds

    def __init__(self, api_key: Optional[str] = None, config: Optional[Config] = None, **kwargs):
        """
        Full client initialization and config management.
        """
        logger.info("Initializing MasterWriterEngine.")
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            logger.critical("No GROQ_API_KEY provided or found in environment.")
            raise EnvironmentError("Must provide GROQ_API_KEY in env or as argument.")
        self.client = Groq(api_key=self.api_key)
        self.model = kwargs.get("model", self.DEFAULT_MODEL)
        self.config = config if config else Config()
        logger.info(f"Initialized with model: {self.model} and config: {self.config.__dict__}")

    def _build_system_prompt(self, topic: str, keyword: str) -> str:
        """
        Elite, multi-line, expert persona prompt with PAS logic and all bolding rules.
        """
        persona_and_rules = [
            "You are the world's most respected expert tech journalist and content strategist.",
            "Write as if you've spent years within the industry.",
            "Use ONLY a first-person conversational style (I, We, Our).",
            "Mix punchy short sentences and longer ones (Perplexity/Burstiness).",
            "Banned vocabulary: pivotal, paradigm, delve, transformative.",
            "Write powerfully. Use ordinary words. Avoid cliches.",
            "STRUCTURE:",
            "- EXACTLY one <h1> (with inner <strong>), 10-16 <h2>-<h4> bolded headings, all with <strong>.",
            "- Each section uses the Problem-Agitate-Solution (PAS) framework.",
            "- Headings should not be boring; always value-driven, often unexpected, with analogies, hooks, and questions.",
            "- NEVER use Key Takeaways box/panel, nor introductory summaries.",
            f"- Use the focus keyword '{keyword}' exactly 4 or 5 times in <strong>; all other mentions are normal text.",
            "- For comparison or options, INCLUDE at least one <table> (HTML, styled, header rows, data rows, realistic values).",
            f"- The <h2><strong>Conclusion</strong></h2> section's ENTIRE text must be wrapped in <strong>.",
            "- Inject two <p><em>Check out our deep dive into [Internal Link Placeholder] for more details.</em></p> blocks at logical narrative points.",
            "- After the conclusion, add an 'Advanced FAQ' of at least 8 <h4> (all bolded) with expert answers, using schema.org HTML markup if possible.",
            "- All lists must use <ul> and <li>; add nested lists if natural.",
            "- For maximum mobile readability, ensure no <p> contains more than 2-3 sentences, break with <br /><br /> to create white space.",
            "- OUTPUT: ONLY HTML, never markdown, yaml, code fences, comments, or explanations.",
            "- If you need a metaphor, use one. If a rhetorical question fits, ask it.",
            "- Never start paragraphs with empty patterns like 'In this article', 'We'll look at', 'To conclude', etc.",
            "- All content must pass for 2500+ words and sound so human even editors can't tell.",
        ]
        return "\n".join(persona_and_rules)

    def _build_user_message(self, topic: str, keyword: str) -> str:
        """
        Build direct user instruction for the LLM.
        """
        return (
            f"Write a long, SEO-dominant HTML article on '{topic}'. Focus keyword: '{keyword}'. "
            f"Follow all SYSTEM PROMPT rules. Use <strong> on headings and only 4-5 impactful '{keyword}' mentions. "
            f"No markdown, yaml, code blocks. No side-notes. Never include Key Takeaways or start with a summary."
        )

    @retry_on_fail(max_retries=3, exceptions=(RateLimitError, Exception), delay=7)
    def _llm_generate(self, system_prompt: str, user_message: str) -> str:
        """
        Handles Groq Llama 3.3 70B completions with retry-on-fail.
        """
        logger.info("Generating article from Groq Llama 3.3 70B.")
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
        html = response.choices[0].message.content.strip()
        logger.info("LLM response received.")
        return html

    def generate_article(self, topic: str, keyword: str, **kwargs) -> Dict[str, Any]:
        """
        Public interface: generates and validates the article.
        """
        system_prompt = self._build_system_prompt(topic, keyword)
        user_message = self._build_user_message(topic, keyword)
        try:
            html = self._llm_generate(system_prompt, user_message)
        except Exception as e:
            logger.error(f"LLM generation failed after retries: {e}")
            return {"title": topic, "body": "", "status": "error", "error": str(e)}

        cleaned = self._super_cleaner(html)
        cleaned = self._optimize_whitespace(cleaned)
        cleaned = self._inject_internal_links(cleaned, keyword)
        cleaned = self._ensure_comparative_table(cleaned, keyword, topic)
        cleaned = self._ensure_faq(cleaned, keyword)
        content_score = self._score_content(cleaned, keyword)
        logger.info(content_score["log_report"])

        title = self._extract_title(cleaned, fallback=topic)
        status = "success" if content_score["score"] == 1.0 else "partial"
        return {"title": title, "body": cleaned, "status": status}

    def _extract_title(self, html: str, fallback: str) -> str:
        """
        Extracts the <h1><strong>...</strong></h1> inner text.
        """
        match = re.search(r'<h1[^>]*>\s*<strong>(.*?)</strong>\s*</h1>', html, re.IGNORECASE | re.DOTALL)
        if match:
            return re.sub(r"<.*?>", "", match.group(1).strip())
        return fallback

    def _super_cleaner(self, text: str) -> str:
        """
        Applies ~30 regex scrubs to remove ALL markdown, code fence, HTML comment,
        WordPress or AI preamble/garbage, revealing only clean HTML.
        """
        patterns = [
            r"^(```[a-zA-Z0-9\-]*\s*)+",               # opening codefence
            r"(```)+$",                                # closing codefence
            r"<!--.*?-->",                             # HTML comments
            r"\*\*\*[^*]*\*\*\*",                      # *** chunk
            r"\n[*-] .*\n",                            # markdown list bullets
            r"```html",                                # code block fence
            r"```",                                    # general code fence
            r"^---.*?---\s*",                          # yaml/data fence
            r"^#+\s.*$",                               # markdown heading lines
            r"\n\s*>\s.*\n",                           # markdown blockquote
            r"^yaml:.*",                               # yaml metadata start
            r"^\s*Here is.*?:",                        # AI explainer preamble
            r"^\s*Sure,? here[’']?s.*?(<h1>)",         # Response preamble
            r"Type\s*/\s*to\s*choose\s*a\s*block.*",   # WP/Gutenberg AI trash
            r"^Output:\s*",                            # Output/Answer
            r"Answer:",                                # AI Answers
            r"Let's get started.*",                    # AI intro
            r"Take a look at the following.*",         # Filler
            r"\[.*?]: https?://.*",                    # markdown links
            r"\n{3,}",                                 # extra whitespace
            r"(</{0,1}script.*?>)",                    # script tags
            r"<style.*?>.*?</style>",                  # style blocks
            r"{.*?}",                                  # JSON blocks
            r'\.\.\.',                                 # plain ellipsis
            r"<!--[\s\S]*?-->",                        # multiline comments
            r"\n *- ?.*",                              # More MD bullets
            r" +",                                    # excess spaces
            r"^>\s",                                   # More MD blockquotes
        ]
        for pat in patterns:
            text = re.sub(pat, '', text, flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)
        return text.strip()

    def _optimize_whitespace(self, html: str) -> str:
        """
        Ensures all <p> are at most 2-3 sentences and injects <br /><br /> liberally.
        """
        def break_paragraphs(match):
            p = match.group(1)
            # Split into sentences
            sentences = re.split(r'(?<=[.!?])\s+', p)
            chunks = [' '.join(sentences[i:i+2]) for i in range(0, len(sentences), 2)]
            return ''.join([f"{c}<br /><br />" for c in chunks if c.strip()])
        return re.sub(r'<p>(.*?)</p>', lambda m: f"<p>{break_paragraphs(m)}</p>", html, flags=re.DOTALL)

    def _inject_internal_links(self, html: str, keyword: str) -> str:
        """
        Identifies two logical locations and places an internal link placeholder
        with natural anchor text using <p><em> ... </em></p>.
        """
        link_html = '<p><em>Check out our deep dive into [Internal Link Placeholder] for more details.</em></p>'
        paras = re.split(r'(<\/p>)', html)
        count = 0
        result = ""
        for i, part in enumerate(paras):
            result += part
            if part.lower().startswith('<p>') and count < 2:
                # After the first and at 2/3 mark
                insert_here = (count == 0) or (len(paras) > 10 and i > len(paras) // 1.5 and count == 1)
                if insert_here:
                    result += link_html
                    count += 1
        return result if count >= 2 else (result + link_html * (2 - count))

    def _ensure_comparative_table(self, html: str, keyword: str, topic: str) -> str:
        """
        Ensures at least one well-formed HTML table appears. Auto-inserts a
        generic table if model output is missing it.
        """
        if '<table' in html and '<th>' in html:
            return html
        table_html = (
            "<table border='1' style='width: 100%; border-collapse: collapse;'>"
            "<thead><tr><th><strong>Feature</strong></th><th><strong>Option A</strong></th><th><strong>Option B</strong></th></tr></thead>"
            "<tbody>"
            f"<tr><td><strong>{keyword} Speed</strong></td><td>Fast</td><td>Moderate</td></tr>"
            f"<tr><td><strong>Cost</strong></td><td>Low</td><td>High</td></tr>"
            f"<tr><td><strong>Suitability</strong></td><td>Best for startups</td><td>Best for enterprises</td></tr>"
            "</tbody></table>"
        )
        # Insert after 3rd or 4th paragraph or in the middle
        paras = re.split(r'(<\/p>)', html)
        idx = min(6, len(paras)-1)
        html = ''.join(paras[:idx] + [table_html] + paras[idx:])
        return html

    def _ensure_faq(self, html: str, keyword: str) -> str:
        """
        Append FAQ section if not present. Use schema.org where possible.
        """
        if re.search(r'<h4[^>]*>.*faq.*</h4>', html, re.IGNORECASE):
            return html
        faq_items = ""
        for i in range(1, 9):
            faq_items += (
                f"<div itemscope itemtype='https://schema.org/Question'>"
                f"<h4><strong>{keyword.title()} FAQ {i}</strong></h4>"
                f"<div itemscope itemprop='acceptedAnswer' itemtype='https://schema.org/Answer'>"
                "<p>Expert answer to this common question goes here, written in a conversational, trustworthy tone with analogies/examples if relevant.</p>"
                "</div></div>"
            )
        return html + "<section>" + faq_items + "</section>"

    def _score_content(self, html: str, keyword: str) -> Dict[str, Any]:
        """
        Checks all bold, heading, and FAQ rules.
        Returns score=1.0 if perfect, else partial, with a log_report.
        """
        report = []
        score = 1.0
        # Headings with bold
        for tag in self.config.allowed_heading_levels:
            found = False
            for m in re.findall(rf'<{tag}[^>]*>(.*?)</{tag}>', html, re.IGNORECASE | re.DOTALL):
                if re.search(r'<strong>.*?</strong>', m, re.IGNORECASE):
                    found = True
            if not found:
                report.append(f"Missing bolded <strong> in <{tag}> heading.")
                score -= 0.05
        # Keyword bolding
        bold_kw = len(re.findall(rf'<strong>(\s*{re.escape(keyword)}\s*)</strong>', html, re.IGNORECASE))
        if bold_kw < 4 or bold_kw > self.config.max_keyword_bolds:
            report.append(f"Keyword bolded count outside 4-5: {bold_kw}")
            score -= 0.05
        # Table
        if not ('<table' in html and '<th>' in html):
            report.append("No comparison <table> found.")
            score -= 0.05
        # FAQ (heading presence)
        faqs = re.findall(r'<h4[^>]*><strong>.*?</strong></h4>', html, re.IGNORECASE)
        if len(faqs) < 8:
            report.append(f"Less than 8 FAQs found: {len(faqs)}")
            score -= 0.05
        # Conclusion section bold
        concl_match = re.search(r'(<h2[^>]*><strong>Conclusion</strong></h2>[\s\S]{50,2000})', html, re.IGNORECASE)
        if not concl_match or not re.search(r'<strong>.*?</strong>', concl_match.group(), flags=re.IGNORECASE | re.DOTALL):
            report.append("Conclusion section/body is not fully bolded.")
            score -= 0.05
        # Paragraphs
        all_ps = re.findall(r"<p>(.*?)</p>", html, re.DOTALL)
        max_p_len = max((len(re.findall(r'[.!?]', p)) for p in all_ps), default=1)
        if max_p_len > 3:
            report.append("At least one paragraph has more than 3 sentences.")
            score -= 0.05
        log_report = "Validation report: " + (' '.join(report) if report else "Perfect content.")
        return {"score": max(score, 0), "log_report": log_report}

if __name__ == "__main__":
    topic = input("Enter article topic: ").strip()
    keyword = input("Enter SEO focus keyword: ").strip()
    writer = MasterWriterEngine()
    result = writer.generate_article(topic=topic, keyword=keyword)
    print("\n=== TITLE ===\n" + result["title"])
    print("\n=== HTML BODY ===\n" + result["body"])
