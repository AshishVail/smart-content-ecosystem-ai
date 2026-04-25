```python name=utils/__init__.py
"""
utils package

This module centralizes all helper utilities for the system, including
secure configuration management, environment validation, and robust logging.
It establishes a unified foundation for all packages to manage global settings,
paths, and diagnostics in a consistent and safe manner.

Main Exports:
    - Config: Centralized application configuration (from config.py)
    - logger: Singleton advanced logger (from logger.py)
"""

__author__ = "Your Name"
__version__ = "1.0.0"
__description__ = "Utilities for configuration and logging."

from .config import Config
from .logger import logger

__all__ = [
    "Config",
    "logger",
]

import os

# Environment file check on import
_env_path = os.path.join(os.getcwd(), ".env")
if not os.path.isfile(_env_path):
    logger.warning(
        "utils: .env file not found in the current working directory. "
        "Environment variables and secrets may be missing."
)
```

