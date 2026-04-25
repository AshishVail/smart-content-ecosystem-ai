"""
core_logic package

High-level smart content and SEO core for AI-driven content platforms.

This package provides core classes and utilities for:
    - Advanced, modular content generation with SEO and formatting support.
    - Automated, professional SEO analysis and reporting.

Main Exports:
    - SmartWriter (from writer_engine)
    - SEOAnalyzer (from seo_analyzer)
"""

__author__ = "Your Name"
__version__ = "1.0.0"
__description__ = "Core logic package for smart content generation and SEO auditing."

from .writer_engine import SmartWriter
from .seo_analyzer import SEOAnalyzer

__all__ = [
    "SmartWriter",
    "SEOAnalyzer",
]

# Initialization logic
import logging

def _init_core_logic():
    msg = "[core_logic] Core package initialized. (Content engine & SEO tools ready.)"
    try:
        logging.getLogger("core_logic").info(msg)
    except Exception:
        print(msg)

_init_core_logic()
