import os
import re
import logging
import time
from typing import Optional, Dict, Any, List, Callable
from groq import Groq, RateLimitError

# Custom logging levels
API_CALL_LEVEL = 25
CLEANING_LEVEL = 21
VALIDATION_LEVEL = 22
FORMATTING_LEVEL = 23

logging.addLevelName(API_CALL_LEVEL, "API_CALL")
logging.addLevelName(CLEANING_LEVEL, "CLEANING")
logging.addLevelName(VALIDATION_LEVEL, "VALIDATION")
logging.addLevelName(FORMATTING_LEVEL, "FORMATTING")

def log_api(message):
    logging.log(API_CALL_LEVEL, message)

def log_clean(message):
    logging.log(CLEANING_LEVEL, message)

def log_validate(message):
    logging.log(VALIDATION_LEVEL, message)

def log_format(message):
    logging.log(FORMATTING_LEVEL, message)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("core_logic.writer_engine")

# 1. Regex cleaning suite: 40+ rules
CLEANING_PATTERNS = {
    "triple_backtick": r"^(```[a-zA-Z0-9\-]*\s*)+|(```)+$",
    "html_comments": r"<!--.*?-->",
    "yaml_block": r"^---.*?---\s*",
    "md_heading": r"^#+\s.*$",
    "md_blockquote": r"\n\s*>\s.*\n",
    "yaml_label": r"^yaml:.*",
    "ai_preamble": r"^\s*(Here is|Sure,|Below is).*?(<h1>)",
    "wp_block": r"Type\s*/\s*to\s*choose\s*a\s*block.*",
    "output_label": r"^Output:\s*",
    "answer_label": r"Answer:",
    "ai_intro": r"Let's get started.*",
    "take_look": r"Take a look at the following.*",
    "md_link": r"\[.*?]: https?://.*",
    "extra_newlines": r"\n{3,}",
    "script_tag": r"(</{0,1}script.*?>)",
    "style_tag": r"<style.*?>.*?</style>",
    "json_block": r"{.*?}",
    "ellipsis": r'\.\.\.',
    "md_list_dash": r"\n *- .*",
    "md_list_star": r"\n *\* .*",
    "ai_marketing": r"AI[- ]?powered",
    "ai_signature": r"Written by [A-Za-z ]+ with AI",
    "blank_line": r"^\s+$",
    "footnote": r"\[\d+\]",
    "md_table": r"\|.+\|",
    "md_bold": r"\*\*(.*?)\*\*",
    "md_italic": r"__(.*?)__",
    "md_inline": r"\[(.*?)\]",
    "excess_spaces": r" +",
    "md_hr": r"^-{3,}$",
    "html_doctype": r"<!DOCTYPE[^>]+>",
    "md_codeblock": r"^~~~.*?^~~~",
    "yaml_metadata": r"^---\n.*?\n---",
    "ai_context": r"^Context:.*",
    "ai_asst": r"^As an AI language model,.*",
    "ai_action": r"Action:",
    "ai_command": r"Command:",
    "ai_instruction": r"Instruction:",
    "ai_notice": r"Note:",
    "ai_blankdesc": r"____+",
    "ai_hereis": r"Here are some",
    "ai_code": r"^Code:\s*",
    "ai_bullet": r"^\s*-\s*",
    "ai_a": r"^\s*a\.\s*",
    "ai_b": r"^\s*b\.\s*",
    "ai_c": r"^\s*c\.\s*",
    "ai_number": r"^\s*\d+\.\s*",
    "ai_line": r"^_\s*",
    "trailing_space": r"[ \t]+$",
    "ai_block_noise": r"WordPress.*Block.*",
    "stray_md_asterisks": r"\*",
    "odd_spacing": r"\s+([.,!?])"
}

def retry_on_fail(max_retries=3, exceptions=(RateLimitError, Exception), delay=7):
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

class ContentValidator:
    """
    Validates final HTML content structure---headings, <strong> tags, keyword density, table, FAQ.
    """

    def __init__(self, keyword):
        self.keyword = keyword.lower()

    def validate(self, html: str) -> Dict[str, Any]:
        errors = []
        score = 1.0

        # 1. Headings must have <strong>
        for tag in ["h1", "h2", "h3", "h4"]:
            pattern = rf'<{tag}[^>]*>\s*<strong>.*?</strong>\s*</{tag}>'
            found = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
            if not found and tag != "h1":
                errors.append(f"Not enough <strong> in <{tag}> tags.")
                score -= 0.05

        # 2. Focus keyword bolding
        strong_keyword = re.findall(r'<strong>\s*' + re.escape(self.keyword) + r'\s*</strong>', html, re.IGNORECASE)
        if not (4 <= len(strong_keyword) <= 5):
            errors.append(f"Focus keyword bolded {len(strong_keyword)} times, should be 4 or 5.")
            score -= 0.05

        # 3. Conclusion section: Everything must be bolded
        concl_head = re.search(r'<h2[^>]*>\s*<strong>Conclusion</strong>\s*</h2>(.*?)(<h2|<h3|<h4|</body|</html|$)', html, re.IGNORECASE | re.DOTALL)
        if concl_head:
            body = concl_head.group(1)
            if not re.sub(r'<strong>.*?</strong>', '', body).strip():
                pass
            else:
                errors.append("Not all Conclusion section is bolded.")
                score -= 0.05
        else:
            errors.append("No <h2><strong>Conclusion</strong></h2> found.")
            score -= 0.1

        # 4. Table
        if '<table' not in html or '<th>' not in html:
            errors.append("No valid comparison table found in content.")
            score -= 0.1
        # 5. Internal link
        ilinks = len(re.findall(r'<p><em>Check out \[Internal Link\]</em></p>', html, re.IGNORECASE))
        if ilinks < 2:
            errors.append("Less than 2 internal links found.")
            score -= 0.05
        # 6. FAQ
        faqs = re.findall(r'<h4[^>]*>\s*<strong>.*?</strong>\s*</h4>', html, re.IGNORECASE)
        if len(faqs) < 8:
            errors.append(f"Less than 8 FAQ items found ({len(faqs)}).")
            score -= 0.1

        # 7. Paragraphs: max 3 sentences
        for p in re.findall(r"<p>(.*?)</p>", html, re.IGNORECASE | re.DOTALL):
            sentences = re.findall(r'[.!?]', p)
            if len(sentences) > 3:
                errors.append("Paragraph has more than 3 sentences.")
                score -= 0.04

        validated = score >= 0.85
        return {
            "valid": validated,
            "score": max(0.0, round(score, 2)),
            "errors": errors
        }

class SmartWriter:
    """
    SmartWriter: Massive, human-optimized AI article generator with rigorous cleaning,
    validation, analogies, and world-class SEO+HTML compliance.
    """

    DEFAULT_MODEL = "llama-3.3-70b-versatile"
    TIMEOUT = 300

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            logger.critical("No GROQ_API_KEY provided or found in environment.")
            raise EnvironmentError("Must provide GROQ_API_KEY in env or as argument.")
        self.client = Groq(api_key=self.api_key)
        self.model = kwargs.get("model", self.DEFAULT_MODEL)
        self.validator = None  # Will be set per article

    def _build_system_prompt(self, topic: str, keyword: str) -> str:
        return (
            "I am a Senior Tech Journalist and SEO Expert with twenty years at the frontlines of writing. "
            "Every article should sound uniquely human, weaving stories, opinions, and lived experience. \n"
            "Tone: Write in a 100% conversational style. Use 'I', 'we', 'our', 'let's'. Add personal stories, analogies (comparing AI to electricity or other real inventions), and "
            "casual rhetorical questions. Vary sentence length and always avoid AI-cliches like 'paradigm', 'transformative', 'unlock the potential', etc. Instead, use punchy, everyday language.\n"
            "ARTICLE STRUCTURE: Start with an impactful <h1> whose text is always inside <strong>, never one word. Every section uses a Problem-Agitate-Solution framework. "
            "All <h2>, <h3>, <h4> must have <strong> around inner text; make titles catchy and loaded with benefit/curiosity, not generic labels. "
            f"Focus keyword '{keyword}' is bolded using <strong> exactly 4 to 5 times, and never more. The <h2><strong>Conclusion</strong></h2> section's ENTIRE body must be bold. "
            "Paragraphs max 2-3 sentences, always inject <br /><br /> liberally for white space. Keep each <p> short and mobile-friendly.\n"
            "- There must be a styled HTML <table> comparing at least two options (with <th>, <tr>, CSS inline), and at least 8 FAQ questions with schema.org HTML microdata. "
            "- At two points, organically insert <p><em>Check out [Internal Link]</em></p> for internal linking.\n"
            "NO markdown or code fences ANYWHERE, and no 'Key Takeaways', explanation, or summary box at start. "
            "End with a 300-word conclusion and expert-level FAQ. Titles like UnlockingTheSecrets must be fixed to Unlocking The Secrets. "
            "Embrace stylistic variety, mixed paragraph/sentence lengths, and human emotion---don't generate robotic prose.\n"
        )

    def _build_user_message(self, topic: str, keyword: str) -> str:
        return (
            f"Write a 2500+ word, SEO-dominant HTML article on '{topic}', using the focus keyword '{keyword}'. "
            "Follow SYSTEM instructions exactly for headings, analogies, PAS, spacing, bolding."
        )

    @retry_on_fail(max_retries=3, exceptions=(RateLimitError, Exception), delay=7)
    def _llm_generate(self, system_prompt: str, user_message: str) -> str:
        log_api("[API] Llama 3.3 70B article generation requested.")
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
        log_api("[API] LLM response received.")
        return response.choices[0].message.content.strip()

    def _clean_html(self, text: str) -> str:
        log_clean("[CLEANING] Cleaning HTML and removing AI footprints.")
        for rule in CLEANING_PATTERNS.values():
            text = re.sub(rule, '', text, flags=re.MULTILINE|re.DOTALL|re.IGNORECASE)
        # Insert space in "UnlockingTheSecrets"
        text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
        # Remove repeated spaces, stray stars afterwards
        text = re.sub(r"\s+", " ", text).replace("*", "")
        return text.strip()

    def _inject_internal_link(self, html: str) -> str:
        log_format("[FORMATTING] Injecting internal linking placeholders.")
        lines = re.split(r'</p>', html)
        link_html = '<p><em>Check out [Internal Link]</em></p>'
        # Insert after 3rd paragraph and at about 2/3 length
        if len(lines) > 5:
            lines.insert(4, link_html)
            lines.insert(int(len(lines) * 0.67), link_html)
        return "</p>".join(lines)

    def _ensure_comparison_table(self, html: str, keyword: str) -> str:
        log_format("[FORMATTING] Ensuring at least one comparison table exists.")
        if "<table" in html and "<th>" in html:
            return html
        table = (
            "<table style='width:100%;border:1px solid #ccc;margin:20px 0;'>"
            "<thead>"
            "<tr><th><strong>Feature</strong></th><th><strong>Solution A</strong></th><th><strong>Solution B</strong></th></tr>"
            "</thead>"
            "<tbody>"
            f"<tr><td>{keyword} Speed</td><td>Lightning fast</td><td>Moderate</td></tr>"
            "<tr><td>Adoption Cost</td><td>Budget friendly</td><td>Significant investment</td></tr>"
            "<tr><td>Scalability</td><td>Enterprise ready</td><td>Good for small teams</td></tr>"
            "</tbody>"
            "</table>"
        )
        return html + table

    def _generate_faq_section(self, keyword: str) -> str:
        log_format("[FORMATTING] Adding Schema.org FAQ section.")
        faq_html = ''
        for i in range(1, 9):
            faq_html += (
                f"<div itemscope itemtype='https://schema.org/Question'>"
                f"<h4><strong>{keyword.title()} FAQ #{i}</strong></h4>"
                f"<div itemscope itemprop='acceptedAnswer' itemtype='https://schema.org/Answer'>"
                "<p>Expert, nuanced answer goes here. Use examples and a candid, direct style.</p>"
                "</div></div>"
            )
        return "<section>" + faq_html + "</section>"

    def _bold_conclusion(self, html: str) -> str:
        log_format("[FORMATTING] Ensuring conclusion section is fully bolded.")
        concl_pattern = re.compile(
            r'(<h2[^>]*>\s*<strong>Conclusion</strong>\s*</h2>)(.*?)(?=<h2|<h3|<h4|</body|</html|$)',
            re.IGNORECASE | re.DOTALL
        )
        def make_bold(match):
            header, body = match.group(1), match.group(2)
            # Strip nested bolds then wrap ALL in <strong>
            body = re.sub(r'<strong>(.*?)</strong>', r'\1', body, flags=re.DOTALL)
            return f"{header}<strong>{body.strip()}</strong>"
        return concl_pattern.sub(make_bold, html)

    def _whitespace_engine(self, html: str) -> str:
        log_format("[FORMATTING] Optimizing for mobile white space.")
        def para_whitespace(match):
            p = match.group(1)
            # Split by punct+space and add <br /><br /> after 2 sentences
            sentences = re.split(r'(?<=[.!?])\s+', p)
            result = []
            while sentences:
                group = " ".join(sentences[:2])
                result.append(group)
                sentences = sentences[2:]
            return ''.join([x + "<br /><br />" for x in result if x.strip()])
        return re.sub(r'<p>(.*?)</p>', lambda m: f"<p>{para_whitespace(m)}</p>", html, flags=re.DOTALL)

    def _fix_heading_spaces(self, html: str) -> str:
        log_format("[FORMATTING] Fixing missing spaces in headings.")
        # Fix titles like UnlockingTheSecrets
        return re.sub(r'<h([1-4])[^>]*>\s*<strong>([A-Za-z0-9]+)([A-Z][a-z]+)', r'<h\1><strong>\2 \3', html)

    def generate_article(self, topic: str, keyword: str, **kwargs) -> Dict[str, Any]:
        system_prompt = self._build_system_prompt(topic, keyword)
        user_message = self._build_user_message(topic, keyword)
        self.validator = ContentValidator(keyword)
        try:
            raw = self._llm_generate(system_prompt, user_message)
        except Exception as e:
            logger.error(f"LLM generation failed after retries: {e}")
            return {"title": topic, "body": "", "status": "error", "error": str(e)}

        cleaned = self._clean_html(raw)
        cleaned = self._whitespace_engine(cleaned)
        cleaned = self._inject_internal_link(cleaned)
        cleaned = self._ensure_comparison_table(cleaned, keyword)
        cleaned = self._bold_conclusion(cleaned)
        cleaned = self._fix_heading_spaces(cleaned)
        cleaned += self._generate_faq_section(keyword)

        result = self.validator.validate(cleaned)
        log_validate(f"Validation result: {result}")
        title = self._extract_title(cleaned, fallback=topic)
        status = "success" if result["valid"] else "partial"
        return {"title": title, "body": cleaned, "status": status, "validation": result}

    def _extract_title(self, html: str, fallback: str) -> str:
        match = re.search(r'<h1[^>]*>\s*<strong>(.*?)</strong>\s*</h1>', html, re.IGNORECASE | re.DOTALL)
        if match:
            title = match.group(1)
            # Insert space before capitals for UnlockingTheSecrets style
            title = re.sub(r'([a-z])([A-Z])', r'\1 \2', title)
            title = re.sub(r"<.*?>", "", title)
            return title.strip()
        return fallback

if __name__ == "__main__":
    topic = input("Enter article topic: ").strip()
    keyword = input("Enter SEO focus keyword: ").strip()
    writer = SmartWriter()
    result = writer.generate_article(topic=topic, keyword=keyword)
    print("\n=== TITLE ===\n" + result["title"])
    print("\n=== HTML BODY ===\n" + result["body"])
    print("\n=== VALIDATION ===\n", result.get("validation", {}))
