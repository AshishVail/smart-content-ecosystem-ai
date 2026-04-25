"""
SEOAnalyzer Module for Smart Content Ecosystem

Author: [Your Name]
Date: 2026-04-25

Features:
- Keyword Density Calculation (primary and secondary)
- Readability Scoring (Flesch Reading Ease)
- Heading Structure Check (H1, H2, H3, keywords in headings)
- LSI Keyword Suggestions (missing LSI terms)
- Meta Description Generation (150-160 chars, high quality)
- SEO Report (Score out of 100 + Improvements as clean JSON)
- OOP design for integration

Requirements:
- Python 3.10+
"""

import re
import json
import math
from typing import List, Dict, Any, Tuple, Optional


class SEOAnalyzer:
    """
    SEOAnalyzer:
        Class for analyzing content and computing detailed SEO metrics.
    """

    def __init__(
        self,
        content: str,
        primary_keyword: str,
        secondary_keywords: Optional[List[str]] = None,
        lsi_keywords: Optional[List[str]] = None,
    ):
        """
        Initialize the SEOAnalyzer.

        Args:
            content (str): Raw text or Markdown content.
            primary_keyword (str): Main keyword to audit.
            secondary_keywords (List[str], optional): Secondary keywords to check density for.
            lsi_keywords (List[str], optional): List of LSI keywords to check presence.
        """
        self.content = content
        self.primary_keyword = primary_keyword.lower()
        self.secondary_keywords = [k.lower() for k in (secondary_keywords or [])]
        self.lsi_keywords = [k.lower() for k in (lsi_keywords or [])]
        self._words = self._extract_words(self.content)

    # --------- Utility Methods ---------

    @staticmethod
    def _extract_words(text: str) -> List[str]:
        """Extract words from content for keyword analysis."""
        return re.findall(r'\b\w+\b', text.lower())

    @staticmethod
    def _count_syllables(word: str) -> int:
        """
        Estimate syllable count for a single word.
        (Heuristics-based; for robust analysis use an NLP library.)
        """
        word = word.lower()
        if len(word) <= 3:
            return 1
        # Remove silent e's
        word = re.sub(r'e$', '', word)
        vowel_groups = re.findall(r'[aeiouy]+', word)
        return max(1, len(vowel_groups))

    @staticmethod
    def _extract_headings(text: str) -> List[Tuple[str, str]]:
        """
        Parse headings from Markdown content.

        Returns:
            List of tuples: (heading_level, heading_text)
            Example: [('H1', 'Main Title'), ('H2', 'Section'), ...]
        """
        headings = []
        for line in text.splitlines():
            stripped = line.strip()
            match = re.match(r'^(#{1,6})\s+(.*)', stripped)
            if match:
                level = f"H{len(match.group(1))}"
                headings.append((level, match.group(2)))
        return headings

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """Naive sentence split for readability computation."""
        # A more robust approach would use nltk or spaCy, kept simple here.
        return re.split(r'(?<=[.!?]) +', text)

    # --------- SEO Analyses ---------

    def keyword_density(self) -> Dict[str, float]:
        """
        Calculate percentage density for the primary and all secondary keywords.

        Returns:
            Dict with keyword as key and float density value (% in total words).
        """
        word_list = self._words
        total_words = len(word_list)
        densities = {}
        for k in [self.primary_keyword] + self.secondary_keywords:
            match_count = sum(1 for w in word_list if w == k)
            densities[k] = (match_count / total_words * 100) if total_words > 0 else 0.0
        return densities

    def readability_score(self) -> float:
        """
        Compute Flesch Reading Ease Score.

        Returns:
            Flesch Reading Ease score (float, higher = easier).
        """
        sentences = self._split_sentences(self.content)
        total_sentences = max(1, len([s for s in sentences if len(s.strip()) > 0]))
        total_words = len(self._words)
        total_syllables = sum(self._count_syllables(w) for w in self._words)

        # Flesch Reading Ease formula
        # 206.835 − 1.015 × (words/sentences) − 84.6 × (syllables/words)
        words_per_sentence = total_words / total_sentences if total_sentences > 0 else 0
        syllables_per_word = total_syllables / total_words if total_words > 0 else 0
        score = 206.835 - (1.015 * words_per_sentence) - (84.6 * syllables_per_word)
        return round(score, 2)

    def heading_structure(self) -> Dict[str, Any]:
        """
        Verify heading hierarchy and keyword inclusion.

        Returns:
            Dict containing
                - 'present': which of 'H1', 'H2', 'H3' are present (bool)
                - 'keyword_in_heading_levels': which levels include keywords (list)
                - 'heading_texts': all headings with their levels
        """
        result = {
            'H1': False,
            'H2': False,
            'H3': False,
            'keyword_in_headings': [],
            'heading_texts': [],
        }
        headings = self._extract_headings(self.content)
        result['heading_texts'] = headings
        found_levels = set()
        keyword_levels = set()
        for level, text in headings:
            if level in ('H1', 'H2', 'H3'):
                found_levels.add(level)
                if self.primary_keyword in text.lower():
                    keyword_levels.add(level)
        for level in ('H1', 'H2', 'H3'):
            result[level] = level in found_levels
        result['keyword_in_headings'] = list(keyword_levels)
        return result

    def missing_lsi_keywords(self) -> List[str]:
        """
        Report which LSI keywords (from provided list) are NOT in content.

        Returns:
            Missing LSI keywords (lowercase).
        """
        content_set = set(self._words)
        missing = [lsi for lsi in self.lsi_keywords if lsi not in content_set]
        return missing

    def generate_meta_description(self) -> str:
        """
        Extract a meta description (150-160 chars) from the first part of the content.

        Returns:
            String - Meta description, clipped at nearest word.
        """
        raw = self.content.replace('\n', ' ').strip()
        # Naively pick first 160 chars, clip at full word
        if len(raw) <= 160:
            return raw
        possible = raw[:160]
        if ' ' in possible:
            possible = possible.rsplit(' ', 1)[0]
        # Ensure it ends with a period if possible.
        if not possible.endswith('.'):
            possible += '...'
        return possible

    def seo_score_and_improvements(self) -> Dict[str, Any]:
        """
        Generate a numeric SEO score (out of 100) and list improvements.

        Returns:
            Dict: {'score': int, 'improvements': List[str], ...subscores}
        """
        points = 100
        improvements = []

        # 1. Keyword Densities
        densities = self.keyword_density()
        prime_density = densities.get(self.primary_keyword, 0)
        # SEO optimal density heuristic: 0.8-2.5%
        if prime_density < 0.8:
            points -= 10
            improvements.append(f"Primary keyword density too low ({prime_density:.2f}%). Consider higher usage.")
        elif prime_density > 2.7:
            points -= 10
            improvements.append(f"Primary keyword density too high ({prime_density:.2f}%). May be considered keyword stuffing.")

        for sk in self.secondary_keywords:
            density = densities.get(sk, 0)
            if density == 0:
                points -= 3
                improvements.append(f"Secondary keyword \"{sk}\" not found in text.")

        # 2. Readability (Flesch Ease 60 - 100 is ideal)
        readability = self.readability_score()
        if readability < 50:
            points -= 10
            improvements.append(f"Text is hard to read (Flesch {readability}). Shorten sentences or simplify vocabulary.")
        elif readability < 60:
            points -= 5
            improvements.append(f"Text could be easier to read (Flesch {readability}). Consider improving flow.")

        # 3. Heading structure
        heading = self.heading_structure()
        for level in ('H1', 'H2'):
            if not heading[level]:
                points -= 8
                improvements.append(f"Missing {level} heading.")

        if self.primary_keyword not in heading['keyword_in_headings']:
            points -= 6
            improvements.append(f"Primary keyword not present in any main heading (H1/H2/H3).")

        # 4. LSI coverage
        missing_lsi = self.missing_lsi_keywords()
        if missing_lsi:
            points -= len(missing_lsi)  # can adjust penalty
            improvements.append(f"LSI terms not found: {missing_lsi}")

        # 5. Meta description quality
        meta_desc = self.generate_meta_description()
        if not (140 <= len(meta_desc) <= 165):
            points -= 3
            improvements.append(f"Meta description should be 150-160 characters. Current: {len(meta_desc)}")

        points = max(points, 0)

        return {
            'score': points,
            'improvements': improvements,
            'keyword_densities': densities,
            'readability': readability,
            'heading_structure': heading,
            'missing_lsi_keywords': missing_lsi,
            'meta_description': meta_desc
        }

    # --------- JSON Output ---------

    def seo_report_json(self) -> str:
        """
        Return the full SEO report as a pretty-formatted JSON string.

        Returns:
            str: JSON string
        """
        report = self.seo_score_and_improvements()
        return json.dumps(report, indent=2, ensure_ascii=False)


# -------------- Optional CLI Demo/Test --------------

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SEOAnalyzer Standalone SEO Audit")
    parser.add_argument("--file", type=str, help="Content file (Markdown)")
    parser.add_argument("--primary", type=str, required=True, help="Primary keyword")
    parser.add_argument("--secondary", nargs="*", default=[], help="Secondary keywords")
    parser.add_argument("--lsi", nargs="*", default=[], help="LSI (related) keywords")
    args = parser.parse_args()

    if args.file:
        with open(args.file, encoding="utf-8") as f:
            content = f.read()
    else:
        print("Please provide a --file argument.")
        exit(1)

    analyzer = SEOAnalyzer(
        content=content,
        primary_keyword=args.primary,
        secondary_keywords=args.secondary,
        lsi_keywords=args.lsi
    )
    print(analyzer.seo_report_json())
