```python name=media_manager/__init__.py
"""
media_manager package

This module provides high-level tools for AI-powered image generation, compression,
dynamic watermarking, SEO-friendly metadata tagging, and automated file renaming.
The package is essential for creating and managing SEO-optimized images
and media assets within modern content ecosystems.

Main Exports:
    - SmartMedia: AI image generation and processing (from image_creator.py)
    - MetaManager: Metadata tagging, alt text generation, and file renaming (from meta_tagger.py)
"""

__author__ = "Your Name"
__version__ = "1.0.0"
__description__ = "Handles image generation and metadata tagging."

from .image_creator import SmartMedia
from .meta_tagger import MetaManager

__all__ = [
    "SmartMedia",
    "MetaManager"
]

import logging

def _init_media_manager():
    msg = "Media Manager Module Initialized"
    try:
        logging.getLogger("media_manager").info(msg)
    except Exception:
        print(msg)

_init_media_manager()
```
