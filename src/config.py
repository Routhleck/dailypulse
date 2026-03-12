"""
DailyPulse - 统一配置模块
所有硬编码常量集中管理
"""
import os
import logging
import sys
from dotenv import load_dotenv

load_dotenv()

# --- Logging ---
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: str = "INFO", log_file: str = None):
    """配置全局日志。"""
    log_level = getattr(logging, level.upper(), logging.INFO)
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(
        level=log_level,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        handlers=handlers,
        force=True,
    )


# --- LLM Config (OpenAI-compatible, supports any provider) ---
# LLM_API_KEY: set via secret; falls back to GEMINI_API_KEY for backwards compat
LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY")
# LLM_BASE_URL: OpenAI-compatible endpoint (default: Gemini's OpenAI-compat endpoint)
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash-lite")

# --- Translation Config ---
# LLM_TRANSLATE: set to "true" to enable translation, default off
LLM_TRANSLATE = os.getenv("LLM_TRANSLATE", "false").lower() == "true"
# LLM_TRANSLATE_MODEL: separate lite model for translation (falls back to LLM_MODEL)
LLM_TRANSLATE_MODEL = os.getenv("LLM_TRANSLATE_MODEL") or LLM_MODEL
# LLM_SUMMARY_MODEL: model for section summaries (falls back to LLM_MODEL)
LLM_SUMMARY_MODEL = os.getenv("LLM_SUMMARY_MODEL") or LLM_MODEL

# Backwards-compat alias
GEMINI_API_KEY = LLM_API_KEY

JINA_READER_URL = "https://r.jina.ai/"

# --- Timeouts (seconds) ---
DEFAULT_TIMEOUT = 15
GEMINI_TIMEOUT = 120
JINA_TIMEOUT = 30

# --- Content Limits ---
CONTENT_TRUNCATE_LIMIT = 3000
JINA_MAX_CHARS = 15000
GEMINI_MAX_OUTPUT_TOKENS = 1024
GEMINI_SUMMARY_MAX_TOKENS = 256
GEMINI_DETAIL_MAX_TOKENS = 1024

# --- Rate Limiting ---
GEMINI_RATE_LIMIT_DELAY = 1.5  # seconds between LLM API calls
GEMINI_MAX_RETRIES = 3

# --- RSS Fetch Limits ---
RSS_FETCH_TIMEOUT = 10
RSS_MAX_PER_FEED = 5
RSS_POLITICS_LIMIT = 10
RSS_ECONOMICS_LIMIT = 8
RSS_MILITARY_LIMIT = 8
RSS_SOCIETY_LIMIT = 8
RSS_ASIA_LIMIT = 10
RSS_ANALYSIS_LIMIT = 6
