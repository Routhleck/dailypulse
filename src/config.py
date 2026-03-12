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
LLM_FALLBACK_BASE_URL = os.getenv("LLM_FALLBACK_BASE_URL", "").strip()
LLM_FALLBACK_API_KEY = os.getenv("LLM_FALLBACK_API_KEY", "").strip()
LLM_FALLBACK_MODEL = os.getenv("LLM_FALLBACK_MODEL", "").strip()

# OpenAI fallback (optional)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
OPENAI_FALLBACK_ENABLED = os.getenv("OPENAI_FALLBACK_ENABLED", "true").lower() == "true"
OPENAI_FALLBACK_MODEL = os.getenv("OPENAI_FALLBACK_MODEL", "gpt-5.4").strip()

# NVIDIA fallback (optional)
NVIDIA_API_KEY = (os.getenv("NVIDIA_API_KEY") or os.getenv("NV_API_KEY") or "").strip()
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1").strip()
NVIDIA_FALLBACK_ENABLED = os.getenv("NVIDIA_FALLBACK_ENABLED", "true").lower() == "true"
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "z-ai/glm5").strip()

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
GEMINI_MAX_RETRIES = 5
TRANSLATION_MAX_WORKERS = int(os.getenv("TRANSLATION_MAX_WORKERS", "6"))

# --- RSS Fetch Limits ---
RSS_FETCH_TIMEOUT = 10
RSS_MAX_PER_FEED = 5
RSS_POLITICS_LIMIT = 10
RSS_ECONOMICS_LIMIT = 8
RSS_MILITARY_LIMIT = 8
RSS_SOCIETY_LIMIT = 8
RSS_ASIA_LIMIT = 10
RSS_ANALYSIS_LIMIT = 6

# --- Event Processing ---
EVENT_WINDOW_HOURS = 72
EVENT_MATCH_THRESHOLD = 0.62
HISTORY_RETENTION_DAYS = 90
DEFAULT_DB_PATH = os.path.join(".state", "dailypulse.db")

# --- Source Reliability Weights ---
# Higher is better. Used by event scoring.
SOURCE_DEFAULT_WEIGHT = 0.6
SOURCE_WEIGHTS = {
    "Reuters World": 1.0,
    "Reuters Business": 1.0,
    "Reuters": 1.0,
    "AP Top News": 0.95,
    "AP": 0.95,
    "BBC World News": 0.9,
    "BBC": 0.9,
    "FT World Economy": 0.9,
    "FT Opinion": 0.88,
    "SCMP World": 0.82,
    "SCMP Business": 0.82,
    "Al Jazeera": 0.8,
    "The Economist": 0.86,
    "Bloomberg Markets": 0.88,
    "WSJ World": 0.87,
    "NHK World": 0.78,
    "Yonhap": 0.78,
    "The Guardian": 0.78,
    "Guardian Opinion": 0.76,
    "Foreign Affairs": 0.92,
    "NYT Opinion": 0.86,
    "VOA中文": 0.72,
    "RFI中文": 0.74,
    "BBC中文": 0.82,
    "BBC中文财经": 0.82,
    "BBC中文评论": 0.82,
}
