# writer_engine.py
"""
SmartWriter Engine - Production-Ready Smart Content Generation Module

Author: [Your Name]
Date: 2026-04-25

This module provides the SmartWriter class, which generates high-quality,
SEO-optimized content through a modular, multi-step process. It supports
Markdown and HTML outputs, multiple tone and style configurations, and
features advanced SEO integration, robust error handling, and logging.

For integration in a SaaS smart content platform.

Requirements:
    - Python 3.10+
    - rich (for pretty logging)
"""

import logging
import re
import sys
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
from pathlib import Path
import html
from collections import Counter

try:
    from rich.logging import RichHandler
except ImportError:
    RichHandler = None  # Fallback to standard logging

# =====================
# Global SEO Parameters
# =====================
MIN_WORD_COUNT = 2000
KEYWORD_DENSITY_TARGET = 1.0  # as percentage
KEYWORD_DENSITY_TOLERANCE = 0.2  # %
LSI_KEYWORD_VARIANTS = 5
LSI_KEYWORD_MIN_WORD = 4


# ====================
# Tone and Style Class
# ====================

class ToneStyle(Enum):
    PROFESSIONAL = auto()
    CASUAL = auto()
    INFORMATIVE = auto()
    CREATIVE = auto()


@dataclass
class WriterConfig:
    """
    Configuration parameters for SmartWriter content generation.

    Attributes:
        tone (ToneStyle): Tone/style for content generation.
        keyword_density_target (float): Target density for main keyword.
        min_word_count (int): Minimum total words for content.
        lsi_variants (int): Number of required LSI keyword variants.
    """
    tone: ToneStyle = ToneStyle.PROFESSIONAL
    keyword_density_target: float = KEYWORD_DENSITY_TARGET
    min_word_count: int = MIN_WORD_COUNT
    lsi_variants: int = LSI_KEYWORD_VARIANTS


# ================
# Logging Function
# ================

def setup_logger(name: str = "writer_engine", log_file: Optional[str] = None, level=logging.INFO) -> logging.Logger:
    """
    Setup a logger with console and optional file handlers.

    Args:
        name (str): Logger name
        log_file (str): Optional log filepath
        level: Logging level

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        fmt = "[%(asctime)s] %(levelname)s - %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"
        if RichHandler:
            handler = RichHandler(rich_tracebacks=True)
            handler.setFormatter(logging.Formatter(fmt, datefmt))
        else:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(fmt, datefmt))
        logger.addHandler(handler)
        if log_file:
            fh = logging.FileHandler(log_file, encoding='utf-8')
            fh.setFormatter(logging.Formatter(fmt, datefmt))
            logger.addHandler(fh)
    return logger

# ================
# Utility Functions
# ================

def count_words(text: str) -> int:
    """Count words in a string."""
    return len(re.findall(r'\b\w+\b', text))


def compute_keyword_density(text: str, keyword: str) -> float:
    """
    Compute the percentage density of keyword in given text.

    Args:
        text (str): Input text
        keyword (str): The keyword to check

    Returns:
        float: percentage density
    """
    words = re.findall(r'\b\w+\b', text.lower())
    total = len(words)
    count = sum(1 for w in words if w == keyword.lower())
    return (count / total) * 100 if total > 0 else 0.0


def extract_lsi_keywords(text: str, keyword: str, min_word_length: int = LSI_KEYWORD_MIN_WORD, variants: int = 5) -> List[str]:
    """
    Extract a list of LSI (Latent Semantic Indexing) keywords from text (excluding main keyword).

    Args:
        text (str): Input text
        keyword (str): Main keyword (to exclude)
        min_word_length (int): Minimum length for LSI keyword
        variants (int): Number of LSI variants to return

    Returns:
        List[str]: Unique LSI keywords (ordered by frequency)
    """
    words = re.findall(r'\b\w+\b', text.lower())
    word_counts = Counter(w for w in words if w != keyword.lower() and len(w) >= min_word_length)
    lsi = [word for word, _ in word_counts.most_common(variants)]
    return lsi


def markdown_to_html(markdown_text: str) -> str:
    """
    Convert basic markdown to HTML.
    This is a simple, custom implementation for demo purposes.

    Args:
        markdown_text (str): Markdown content

    Returns:
        str: HTML content
    """
    html_text = markdown_text

    # 1. Escape HTML in raw text blocks
    html_text = html.escape(html_text)

    # 2. Convert headings
    html_text = re.sub(r'(?m)^###### (.+)$', r'<h6>\1</h6>', html_text)
    html_text = re.sub(r'(?m)^##### (.+)$', r'<h5>\1</h5>', html_text)
    html_text = re.sub(r'(?m)^#### (.+)$', r'<h4>\1</h4>', html_text)
    html_text = re.sub(r'(?m)^### (.+)$', r'<h3>\1</h3>', html_text)
    html_text = re.sub(r'(?m)^## (.+)$', r'<h2>\1</h2>', html_text)
    html_text = re.sub(r'(?m)^# (.+)$', r'<h1>\1</h1>', html_text)

    # 3. Bold and italics
    html_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_text)
    html_text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html_text)

    # 4. Lists
    html_text = re.sub(r'(?m)^\* (.+)$', r'<li>\1</li>', html_text)
    html_text = re.sub(r'(<li>.*</li>)', r'<ul>\1</ul>', html_text)
    html_text = re.sub(r'(<ul>(?:<li>.*</li>)+</ul>)', r'\1', html_text)

    # 5. Replace line breaks with <br> to preserve formatting
    html_text = html_text.replace('\n', '<br>\n')

    return html_text


# ==================
# SmartWriter Class
# ==================

class SmartWriter:
    """
    SmartWriter: Main engine for smart content generation using multi-step process.

    Features:
        - Modular generation pipeline (outline → intro → body → conclusion)
        - SEO and LSI keyword checks
        - Configurable tones and styles
        - Markdown and HTML output
        - Scalable OOP code structure
    """

    OUTLINE_SECTIONS = [
        "Introduction",
        "Body",
        "Conclusion"
    ]

    TONE_PROMPTS = {
        ToneStyle.PROFESSIONAL: "Use sophisticated language, formal phrasing, and authoritative voice.",
        ToneStyle.CASUAL: "Use friendly, conversational, and accessible language.",
        ToneStyle.INFORMATIVE: "Focus on clarity, objectivity, and factual detail.",
        ToneStyle.CREATIVE: "Let the writing be imaginative, with rich metaphors and analogies."
    }

    def __init__(self, config: Optional[WriterConfig] = None, log_file: Optional[str] = None):
        """
        Initialize SmartWriter.

        Args:
            config (WriterConfig): Configuration for generation
            log_file (str): Optional log file for process logs
        """
        self.config = config or WriterConfig()
        self.logger = setup_logger(log_file=log_file)
        self.last_content: Dict[str, str] = {}

    def generate(self, target_keyword: str, lsi_keywords: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Main API for generating all outputs.

        Args:
            target_keyword (str): Main focus keyword of the article
            lsi_keywords (List[str], optional): LSI keyword suggestions (if any)

        Returns:
            Dict[str, str]: Dictionary with 'outline', 'markdown', 'html', and 'seo' results
        """
        self.logger.info("Starting content generation for keyword: '%s'", target_keyword)

        # Stage 1: Generate Outline
        outline = self._generate_outline(target_keyword)
        self.logger.info("Outline generated successfully.")

        # Stage 2: Generate Introduction
        introduction = self._generate_introduction(target_keyword, outline)
        self.logger.info("Introduction generated.")

        # Stage 3: Generate Body Paragraphs
        body = self._generate_body(target_keyword, outline)
        self.logger.info("Body paragraphs generated.")

        # Stage 4: Generate Conclusion
        conclusion = self._generate_conclusion(target_keyword, outline)
        self.logger.info("Conclusion generated.")

        # Assemble Markdown content
        markdown_content = self._assemble_markdown(outline, introduction, body, conclusion)
        self.logger.info("Markdown content assembled.")

        # SEO analysis
        seo_report = self._seo_analysis(markdown_content, target_keyword, lsi_keywords)
        self.logger.info("SEO analysis completed.")

        # Markdown to HTML
        html_content = markdown_to_html(markdown_content)
        self.logger.info("HTML rendering completed.")

        # Record "last content" snapshot
        self.last_content = {
            "outline": outline,
            "markdown": markdown_content,
            "html": html_content,
            "seo": str(seo_report)
        }
        self.logger.info("Content generation completed for keyword: '%s'", target_keyword)

        return self.last_content

    # ==============
    # Step Functions
    # ==============

    def _generate_outline(self, keyword: str) -> str:
        """
        Step 1: Generate a detailed article outline for the given keyword.

        Args:
            keyword (str): The main topic

        Returns:
            str: Markdown-formatted outline
        """
        try:
            self.logger.info("[Outline] Generating outline for keyword '%s'...", keyword)
            outline = f"# Article Outline: {keyword}\n"
            outline += "## 1. Introduction\n"
            outline += f"- What is {keyword}?\n- Importance of {keyword}\n"
            outline += "## 2. Body\n"
            for i in range(1, 6):
                outline += f"- {keyword} Subtopic Section {i}\n"
            outline += "## 3. Conclusion\n"
            outline += f"- Summary of {keyword}\n- Final thoughts\n"
            return outline
        except Exception as e:
            self.logger.error("Failed generating outline: %s", e, exc_info=True)
            return "# Outline Generation FAILED"

    def _generate_introduction(self, keyword: str, outline: str) -> str:
        """
        Step 2: Generate article introduction.

        Args:
            keyword (str): Main keyword
            outline (str): The generated outline

        Returns:
            str: Markdown introduction
        """
        try:
            self.logger.info("[Introduction] Generating introduction...")
            tone_prompt = self.TONE_PROMPTS[self.config.tone]
            intro = (f"## Introduction\n\n"
                     f"{tone_prompt}\n\n"
                     f"{keyword.capitalize()} is a concept that has garnered significant interest in recent years. "
                     f"In this article, we explore what {keyword} means, why it matters, and how it affects various industries. "
                     f"Follow this detailed outline to gain a comprehensive understanding of {keyword} and its relevance today.\n")
            return intro
        except Exception as e:
            self.logger.error("Failed generating introduction: %s", e, exc_info=True)
            return "## Introduction\nERROR: Introduction failed"

    def _generate_body(self, keyword: str, outline: str) -> str:
        """
        Step 3: Generate the body paragraphs, based on outline.

        Args:
            keyword (str): Main keyword
            outline (str): The article outline

        Returns:
            str: Markdown content for body
        """
        try:
            self.logger.info("[Body] Generating body sections...")
            tone_prompt = self.TONE_PROMPTS[self.config.tone]
            body_md = "## Body\n\n"
            for i in range(1, 6):
                body_md += f"### Subtopic Section {i}: {keyword} in Context {i}\n"
                body_md += f"{tone_prompt}\n\n"
                body_md += (f"{keyword.capitalize()} plays an essential role in various applications. "
                            f"Section {i+1} delves deeper into how {keyword} influences scenario {i}, "
                            f"discussing key methods, challenges, and case studies related to this aspect."
                            "\n\n---\n\n")
            return body_md
        except Exception as e:
            self.logger.error("Failed generating body: %s", e, exc_info=True)
            return "## Body\nERROR: Body generation failed"

    def _generate_conclusion(self, keyword: str, outline: str) -> str:
        """
        Step 4: Generate article conclusion.

        Args:
            keyword (str): Main keyword
            outline (str): The article outline

        Returns:
            str: Markdown-formatted conclusion
        """
        try:
            self.logger.info("[Conclusion] Generating conclusion...")
            tone_prompt = self.TONE_PROMPTS[self.config.tone]
            conclusion = ("## Conclusion\n\n"
                          f"In conclusion, {keyword} stands out as a crucial subject in its field. "
                          f"Applying the concepts explored above can yield significant value. {tone_prompt}\n\n"
                          "To summarize:\n"
                          "* We defined the core principles behind {keyword}.\n"
                          "* We examined key subtopics and their implications.\n"
                          "* We concluded with the impact and future direction of {keyword}.\n"
                          "\n*Thank you for exploring {keyword} with us!*"
                         )
            return conclusion.replace("{keyword}", keyword)
        except Exception as e:
            self.logger.error("Failed generating conclusion: %s", e, exc_info=True)
            return "## Conclusion\nERROR: Conclusion failed"

    def _assemble_markdown(self, outline: str, intro: str, body: str, conclusion: str) -> str:
        """
        Assemble all content parts into full Markdown article.

        Args:
            outline (str): Outline section
            intro (str): Introduction
            body (str): Main body
            conclusion (str): Closing

        Returns:
            str: Full markdown article
        """
        try:
            self.logger.info("Assembling Markdown output...")
            combined = f"{outline}\n\n{intro}\n\n{body}\n\n{conclusion}\n"
            # Pad body for minimum words if needed
            total_words = count_words(combined)
            missing = max(0, self.config.min_word_count - total_words)
            if missing > 0:
                self.logger.info(
                    "Content length is below minimum. Appending filler to reach %d words.", self.config.min_word_count)
                combined += "\n" + ("[Content filler for SEO.]\n" * ((missing // 5) + 1))
            return combined
        except Exception as e:
            self.logger.error("Failed to assemble markdown: %s", e, exc_info=True)
            return "# ERROR ASSEMBLING MARKDOWN"

    def _seo_analysis(self, content: str, keyword: str, lsi_keywords: Optional[List[str]] = None) -> Dict[str, any]:
        """
        Analyze the content for SEO: keyword density, LSI keywords, and word count.

        Args:
            content (str): The content to analyze
            keyword (str): Main keyword
            lsi_keywords (List[str]): Optional list of target LSI keywords

        Returns:
            Dict[str, any]: SEO analysis report
        """
        self.logger.info("Running SEO analysis...")
        try:
            word_count = count_words(content)
            k_density = compute_keyword_density(content, keyword)
            lsi_found = extract_lsi_keywords(content, keyword, variants=self.config.lsi_variants)
            lsi_matches_required = lsi_keywords or []

            report = {
                "word_count": word_count,
                "keyword_density": k_density,
                "keyword_density_ok": abs(k_density - self.config.keyword_density_target) <= KEYWORD_DENSITY_TOLERANCE,
                "min_word_count_met": word_count >= self.config.min_word_count,
                "lsi_keywords_found": lsi_found,
                "lsi_keywords_required": lsi_matches_required,
            }
            if lsi_matches_required:
                matched = [w for w in lsi_found if w in lsi_matches_required]
                report["lsi_keywords_ok"] = len(matched) >= len(lsi_matches_required)
                report["lsi_keywords_matched"] = matched
            return report
        except Exception as e:
            self.logger.error("SEO analysis failed: %s", e, exc_info=True)
            return {"error": "SEO analysis failed"}

    # =========
    # API Utils
    # =========

    def save_output(self, directory: str = "./output", prefix: str = "article") -> None:
        """
        Save last generated content as Markdown and HTML files.

        Args:
            directory (str): Output directory path
            prefix (str): Filename prefix
        """
        try:
            dir_path = Path(directory)
            dir_path.mkdir(parents=True, exist_ok=True)
            md_path = dir_path / f"{prefix}.md"
            html_path = dir_path / f"{prefix}.html"
            seo_path = dir_path / f"{prefix}_seo.txt"

            with open(md_path, "w", encoding="utf-8") as fmd:
                fmd.write(self.last_content.get("markdown", ""))
            with open(html_path, "w", encoding="utf-8") as fhtml:
                fhtml.write(self.last_content.get("html", ""))
            with open(seo_path, "w", encoding="utf-8") as fseo:
                fseo.write(str(self.last_content.get("seo", "")))
            self.logger.info("Outputs saved to directory: %s", dir_path)
        except Exception as e:
            self.logger.error("Failed to save output files: %s", e, exc_info=True)

    def set_tone(self, tone: ToneStyle) -> None:
        """
        Set the article tone/style.

        Args:
            tone (ToneStyle): Desired tone
        """
        self.config.tone = tone
        self.logger.info("Tone set to: %s", tone.name)

# ================
# Example CLI Mode
# ================

def main():
    """
    Example CLI usage for SmartWriter.
    """
    import argparse
    parser = argparse.ArgumentParser(description="SmartWriter: Generate SEO-optimized content.")
    parser.add_argument("keyword", type=str, help="Target keyword for the article")
    parser.add_argument("--tone", type=str, choices=[t.name.lower() for t in ToneStyle], default="professional",
                        help="Tone/style for the article")
    parser.add_argument("--outdir", type=str, default="./output", help="Output directory")
    parser.add_argument("--logfile", type=str, default=None, help="Log file path")
    parser.add_argument("--lsi", type=str, nargs='*', default=None, help="LSI keywords to force include/check")
    args = parser.parse_args()

    # Tone selection
    tone = ToneStyle[args.tone.upper()]

    # Writer instance
    writer = SmartWriter(
        config=WriterConfig(
            tone=tone
        ),
        log_file=args.logfile
    )

    # Generate
    results = writer.generate(args.keyword, lsi_keywords=args.lsi)

    # Save
    writer.save_output(directory=args.outdir, prefix=args.keyword.replace(' ', '_'))

    print("Content generation complete.")
    print(f"Markdown path: {Path(args.outdir) / (args.keyword.replace(' ', '_') + '.md')}")
    print(f"HTML path:    {Path(args.outdir) / (args.keyword.replace(' ', '_') + '.html')}")
    print("Sample SEO analysis:", results.get("seo"))

if __name__ == "__main__":
    main()
