"""
logger.py

Robust, production-grade logging utility for Python applications.

Features:
- RotatingFileHandler with 5MB max per log, up to 5 backups
- Dual output: File and Console
- Advanced formatting: [Timestamp] [Level] [File:Line] - Message
- Error tracking with traceback logging
- Singleton: import 'from utils.logger import logger' (ready-to-use)

Usage:
    from utils.logger import logger
    logger.info("Message")
    try:
        ...
    except Exception:
        logger.log_traceback("context message")
"""

import logging
import os
import sys
import traceback
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(os.getenv('LOGS_DIR', './logs')).resolve()
LOG_DIR.mkdir(exist_ok=True, parents=True)
LOG_FILE = LOG_DIR / "app_activity.log"

class ContextFilter(logging.Filter):
    """
    Adds file name and line number to log records.
    """
    def filter(self, record):
        record.filename_line = f"{record.filename}:{record.lineno}"
        return True

class LoggerSingleton:
    """
    Singleton Logger provider.
    """
    _instance = None

    def __new__(cls):
        if not cls._instance:
            # Logger setup
            logger = logging.getLogger("SmartAppLogger")
            logger.setLevel(logging.INFO)
            if getattr(logger, '_init_done', False):
                return logger  # Already configured

            # Formatter
            formatter = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] [%(filename_line)s] - %(message)s",
                "%Y-%m-%d %H:%M:%S"
            )

            # File Handler (Rotating)
            file_handler = RotatingFileHandler(
                filename=str(LOG_FILE),
                maxBytes=5 * 1024 * 1024,  # 5 MB
                backupCount=5,
                encoding='utf-8',
                delay=False
            )
            file_handler.setFormatter(formatter)
            file_handler.addFilter(ContextFilter())

            # Console Handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            console_handler.addFilter(ContextFilter())

            # Prevent double logs if imported in a subprocess
            if not logger.handlers:
                logger.addHandler(file_handler)
                logger.addHandler(console_handler)

            logger._init_done = True
            cls._instance = logger
        return cls._instance

# Singleton instance for import
logger: logging.Logger = LoggerSingleton()

def log_traceback(context_msg: str = ""):
    """
    Log full traceback with context message at ERROR level.
    Usage: in except block, call log_traceback("API X failed")
    """
    exc_type, exc_value, exc_tb = sys.exc_info()
    tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    msg = f"{context_msg}\n{tb_str}"
    logger.error(msg)

# Attach method to logger object for ergonomic import/use
setattr(logger, "log_traceback", log_traceback)
