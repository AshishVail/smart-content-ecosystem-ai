```python name=integrations/__init__.py
"""
integrations package

This package provides integration tools that act as a bridge between the smart content engine
and external publishing/distribution platforms. It handles secure posting to WordPress
(including media and SEO meta), as well as cross-platform social media automation on
Instagram, Threads, and X (Twitter).

Main Exports:
    - WordPressClient (from wordpress_api.py): Robust WordPress publishing and media API access.
    - SocialDistributor (from social_share.py): Social media distribution and scheduling.

"""

__author__ = "Your Name"
__version__ = "1.0.0"
__description__ = "Handles WordPress posting and Social Media distribution."

from .wordpress_api import WordPressClient
from .social_share import SocialDistributor

__all__ = [
    "WordPressClient",
    "SocialDistributor",
]

def _check_required_libraries():
    """
    Checks that all essential integration libraries are installed.
    Logs or prints warnings if any are missing.
    """
    required = ["requests"]
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        msg = (
            "[integrations] WARNING: Missing required libraries: " +
            ", ".join(missing) +
            ". Please install them before using integration features."
        )
        try:
            import logging
            logging.getLogger("integrations").warning(msg)
        except Exception:
            print(msg)

_check_required_libraries()
```
