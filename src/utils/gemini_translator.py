"""
LLM Translator - 使用 OpenAI-compatible API 翻译文本为中文
支持 Gemini、OpenAI、DeepSeek、Qwen 等任意兼容提供商
"""
import sys
import time
import logging
import httpx

logger = logging.getLogger(__name__)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

try:
    from config import LLM_API_KEY, LLM_BASE_URL, LLM_TRANSLATE, LLM_TRANSLATE_MODEL, GEMINI_TIMEOUT, GEMINI_MAX_RETRIES
except ImportError:
    from src.config import LLM_API_KEY, LLM_BASE_URL, LLM_TRANSLATE, LLM_TRANSLATE_MODEL, GEMINI_TIMEOUT, GEMINI_MAX_RETRIES

# Backwards-compat: keep GEMINI_API_KEY alias for any external callers
GEMINI_API_KEY = LLM_API_KEY


def _chat(prompt: str, max_tokens: int = 1024, model: str = None) -> str:
    """Call OpenAI-compatible /v1/chat/completions endpoint."""
    if not LLM_API_KEY:
        return ""

    url = f"{LLM_BASE_URL.rstrip('/')}/v1/chat/completions"
    headers = {"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": model or LLM_TRANSLATE_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": max_tokens,
    }

    for attempt in range(GEMINI_MAX_RETRIES):
        try:
            response = httpx.post(url, json=payload, headers=headers, timeout=GEMINI_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            result = data["choices"][0]["message"]["content"]
            if result:
                return result.strip()
            if attempt < GEMINI_MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
        except (httpx.HTTPError, httpx.TimeoutException, KeyError, IndexError) as e:
            if attempt < GEMINI_MAX_RETRIES - 1:
                logger.warning(f"LLM call failed ({attempt + 1}/{GEMINI_MAX_RETRIES}): {e}")
                time.sleep(2 ** attempt)
            else:
                logger.error(f"LLM call ultimately failed: {e}")
    return ""


def translate_to_chinese(text: str, max_chars: int = 100) -> str:
    if not LLM_TRANSLATE or not LLM_API_KEY:
        return text[:max_chars] + "..." if len(text) > max_chars else text

    if not text or len(text) < 10:
        return text

    prompt = f"""请将以下新闻标题或摘要翻译成简体中文，要求：
1. 保持原意，用词准确
2. 只输出翻译结果，不要添加任何解释

原文：
{text}"""

    result = _chat(prompt, max_tokens=1024)
    if result:
        return result
    return text[:max_chars] + "..." if len(text) > max_chars else text


def translate_summary_pair(summary: str) -> tuple[str, str]:
    if not summary:
        return ("", "")
    brief_cn = translate_to_chinese(summary[:200], max_chars=80)
    detail_cn = translate_to_chinese(summary, max_chars=500)
    return (brief_cn, detail_cn)


def summarize_blog_article(content: str, mode: str = "brief") -> str:
    if not LLM_API_KEY or not content or len(content) < 50:
        return ""

    if mode == "brief":
        prompt = f"""请阅读以下文章，用一句话中文概括核心观点（最多100字）。
要求：直接说重点，忽略作者信息、日期、URL等元数据。

文章内容：
{content[:2000]}"""
        max_tokens = 256
    else:
        prompt = f"""请作为分析师，阅读以下文章并生成中文深度分析报告。
要求：
1. 忽略作者信息、URL、图片链接等元数据
2. 提取核心观点
3. 用3-4个段落组织：背景、关键发现、细节、实用价值
4. 总长度控制在300-500字

文章内容：
{content[:6000]}"""
        max_tokens = 1024

    return _chat(prompt, max_tokens=max_tokens)


def summarize_section(titles_and_summaries: list[str], section_name: str) -> str:
    """用主模型生成板块总结，输入为该板块所有文章的标题+摘要列表。"""
    if not LLM_API_KEY or not titles_and_summaries:
        return ""
    content = "\n".join(f"- {t}" for t in titles_and_summaries)
    prompt = f"""以下是今日{section_name}板块的新闻条目：

{content}

请用2-3句话总结今日该板块的整体动态和核心趋势，语言简洁，直接输出总结，不要加标题或前缀。"""
    return _chat(prompt, max_tokens=256)
