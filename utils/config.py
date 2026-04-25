```python name=utils/config.py
"""
config.py

Highly secure, production-grade configuration management module.

- Secure loading of sensitive credentials and settings using python-dotenv
- Centralized Config singleton class for all environment/application parameters
- Path management (logs, media, outputs) via pathlib (absolute, normalized)
- Credential validation for all mission-critical services (fails fast on startup)
- All fields, methods, and properties extensively documented and type-hinted

Dependencies:
    pip install python-dotenv

Usage:
    from utils.config import Config
    config = Config()
    print(config.OPENAI_API_KEY)
"""

import os
import threading
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

class ConfigMeta(type):
    """
    Metaclass for Singleton implementation of Config.
    """
    _instance_lock = threading.Lock()
    _instance: Optional["Config"] = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._instance_lock:
                if not cls._instance:
                    cls._instance = super().__call__(*args, **kwargs)
        return cls._instance

class Config(metaclass=ConfigMeta):
    """
    Singleton class for central application configuration.

    Loads settings from environment variables (securely via python-dotenv)
    and exposes validation and convenience path management.
    """

    # -------- Initializer ----------
    def __init__(self) -> None:
        """
        Load .env, initialize config, and optionally validate immediately.
        """
        load_dotenv()
        self._load_settings()
        self._validate_critical_env()

    def _load_settings(self) -> None:
        """Loads settings from environment variables."""
        # === API SETTINGS ===
        self.OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
        self.WORDPRESS_USER: str = os.getenv("WORDPRESS_USER", "")
        self.WORDPRESS_PASSWORD: str = os.getenv("WORDPRESS_PASSWORD", "")
        self.WORDPRESS_URL: str = os.getenv("WORDPRESS_URL", "")
        self.INSTAGRAM_TOKEN: str = os.getenv("INSTAGRAM_GRAPH_TOKEN", "")
        self.INSTAGRAM_BUSINESS_ID: str = os.getenv("INSTAGRAM_BUSINESS_ID", "")
        self.TWITTER_BEARER: str = os.getenv("TWITTER_BEARER_TOKEN", "")
        self.TWITTER_API_KEY: str = os.getenv("TWITTER_API_KEY", "")
        self.TWITTER_API_SECRET: str = os.getenv("TWITTER_API_SECRET", "")
        self.TWITTER_ACCESS_TOKEN: str = os.getenv("TWITTER_ACCESS_TOKEN", "")
        self.TWITTER_ACCESS_SECRET: str = os.getenv("TWITTER_ACCESS_SECRET", "")

        self.DALLE_API_URL: str = os.getenv("DALLE_API_URL", "https://api.openai.com/v1/images/generations")
        self.TIMEOUT: int = int(os.getenv("API_TIMEOUT", 30))
        self.LANGUAGE: str = os.getenv("CONTENT_LANGUAGE", "en")
        self.AI_MODEL: str = os.getenv("AI_MODEL_VERSION", "gpt-4o")

        # === CONTENT SETTINGS ===
        self.DEFAULT_WORD_COUNT: int = int(os.getenv("DEFAULT_WORD_COUNT", 2000))

        # === PATH MANAGEMENT (Pathlib; ensures absolute paths) ===
        self.ROOT_DIR: Path = Path(os.getenv("PROJECT_ROOT", os.getcwd())).resolve()
        self.LOGS_DIR: Path = self.ROOT_DIR / "logs"
        self.MEDIA_DIR: Path = self.ROOT_DIR / "media"
        self.OUTPUTS_DIR: Path = self.ROOT_DIR / "outputs"

        # Auto-create folders if missing (secure)
        for p in [self.LOGS_DIR, self.MEDIA_DIR, self.OUTPUTS_DIR]:
            p.mkdir(parents=True, exist_ok=True)

    def _validate_critical_env(self) -> None:
        """
        Checks for presence of all critical environment variables.
        Raises ImportError with details if anything is missing.
        """
        required_keys = {
            "OPENAI_API_KEY": self.OPENAI_API_KEY,
            "WORDPRESS_USER": self.WORDPRESS_USER,
            "WORDPRESS_PASSWORD": self.WORDPRESS_PASSWORD,
            "WORDPRESS_URL": self.WORDPRESS_URL,
            "INSTAGRAM_TOKEN": self.INSTAGRAM_TOKEN,
            "INSTAGRAM_BUSINESS_ID": self.INSTAGRAM_BUSINESS_ID,
            "TWITTER_BEARER": self.TWITTER_BEARER,
            "TWITTER_API_KEY": self.TWITTER_API_KEY,
            "TWITTER_API_SECRET": self.TWITTER_API_SECRET,
            "TWITTER_ACCESS_TOKEN": self.TWITTER_ACCESS_TOKEN,
            "TWITTER_ACCESS_SECRET": self.TWITTER_ACCESS_SECRET
        }
        missing = [k for k, v in required_keys.items() if not v]
        if missing:
            raise ImportError(
                f"Missing critical environment variables in .env: {', '.join(missing)}.\n"
                "Check your .env file or environment settings."
            )

    # ----- Doc Properties -----
    @property
    def description(self) -> str:
        """
        :return: High-level summary of this configuration object.
        """
        return ("Centralized configuration for all app services and credentials. "
                "Secured via environment and validated on load.")

    @property
    def is_ready(self) -> bool:
        """
        :return: True if all critical environment variables are present and paths exist.
        """
        try:
            self._validate_critical_env()
            return all([p.exists() for p in [self.LOGS_DIR, self.MEDIA_DIR, self.OUTPUTS_DIR]])
        except Exception:
            return False

    def __repr__(self) -> str:
        return (
            f"Config(AI_MODEL={self.AI_MODEL}, WORDCOUNT={self.DEFAULT_WORD_COUNT}, "
            f"LANGUAGE={self.LANGUAGE}, ROOT={self.ROOT_DIR})"
        )
```
