"""
LLM Translator - 使用 OpenAI-compatible API 翻译文本为中文
支持主模型 + 多 provider fallback（OpenAI/NVIDIA/自定义）
"""

from __future__ import annotations

import logging
import sys
import time
from dataclasses import dataclass
from typing import List, Optional

import httpx

logger = logging.getLogger(__name__)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    from config import (
        GEMINI_MAX_RETRIES,
        GEMINI_TIMEOUT,
        LLM_API_KEY,
        LLM_BASE_URL,
        LLM_FALLBACK_API_KEY,
        LLM_FALLBACK_BASE_URL,
        LLM_FALLBACK_MODEL,
        LLM_SUMMARY_MODEL,
        LLM_TRANSLATE,
        LLM_TRANSLATE_MODEL,
        NVIDIA_API_KEY,
        NVIDIA_BASE_URL,
        NVIDIA_FALLBACK_ENABLED,
        NVIDIA_MODEL,
        OPENAI_API_KEY,
        OPENAI_BASE_URL,
        OPENAI_FALLBACK_ENABLED,
        OPENAI_FALLBACK_MODEL,
        TRANSLATION_MAX_WORKERS,
    )
except ImportError:
    from src.config import (
        GEMINI_MAX_RETRIES,
        GEMINI_TIMEOUT,
        LLM_API_KEY,
        LLM_BASE_URL,
        LLM_FALLBACK_API_KEY,
        LLM_FALLBACK_BASE_URL,
        LLM_FALLBACK_MODEL,
        LLM_SUMMARY_MODEL,
        LLM_TRANSLATE,
        LLM_TRANSLATE_MODEL,
        NVIDIA_API_KEY,
        NVIDIA_BASE_URL,
        NVIDIA_FALLBACK_ENABLED,
        NVIDIA_MODEL,
        OPENAI_API_KEY,
        OPENAI_BASE_URL,
        OPENAI_FALLBACK_ENABLED,
        OPENAI_FALLBACK_MODEL,
        TRANSLATION_MAX_WORKERS,
    )

# Backwards-compat alias for any external callers
GEMINI_API_KEY = LLM_API_KEY


@dataclass(frozen=True)
class Provider:
    name: str
    base_url: str
    api_key: str
    model: str


def _build_chat_url(base_url: str) -> str:
    base = (base_url or "").rstrip("/")
    if not base:
        return ""
    if base.endswith("/chat/completions"):
        return base
    if base.endswith("/v1") or base.endswith("/openai") or base.endswith("/openai/v1"):
        return f"{base}/chat/completions"
    return f"{base}/v1/chat/completions"


def _provider_chain(primary_model: Optional[str]) -> List[Provider]:
    providers: List[Provider] = []
    seen = set()

    def _push(name: str, base_url: str, api_key: str, model_name: str) -> None:
        chat_url = _build_chat_url(base_url)
        if not chat_url or not api_key or not model_name:
            return
        dedup_key = (chat_url, model_name, api_key)
        if dedup_key in seen:
            return
        seen.add(dedup_key)
        providers.append(Provider(name=name, base_url=chat_url, api_key=api_key, model=model_name))

    _push("primary", LLM_BASE_URL, LLM_API_KEY, primary_model or LLM_TRANSLATE_MODEL)

    if OPENAI_FALLBACK_ENABLED:
        _push("openai-fallback", OPENAI_BASE_URL, OPENAI_API_KEY, OPENAI_FALLBACK_MODEL)

    if NVIDIA_FALLBACK_ENABLED:
        _push("nvidia-fallback", NVIDIA_BASE_URL, NVIDIA_API_KEY, NVIDIA_MODEL)

    _push("custom-fallback", LLM_FALLBACK_BASE_URL, LLM_FALLBACK_API_KEY, LLM_FALLBACK_MODEL)

    return providers


def _call_provider(provider: Provider, prompt: str, max_tokens: int) -> str:
    headers = {
        "Authorization": f"Bearer {provider.api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": provider.model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": max_tokens,
    }

    response = httpx.post(
        provider.base_url,
        json=payload,
        headers=headers,
        timeout=GEMINI_TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()
    return (data.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()


def _chat(prompt: str, max_tokens: int = 1024, model: str = None) -> str:
    """Call OpenAI-compatible chat endpoint with provider fallback chain."""
    providers = _provider_chain(primary_model=model)
    if not providers:
        return ""

    retries = max(1, int(GEMINI_MAX_RETRIES))
    for idx, provider in enumerate(providers):
        for attempt in range(retries):
            try:
                result = _call_provider(provider, prompt, max_tokens=max_tokens)
                if result:
                    return result
                logger.warning(
                    "LLM returned empty content provider=%s attempt=%s/%s",
                    provider.name,
                    attempt + 1,
                    retries,
                )
            except (httpx.HTTPError, httpx.TimeoutException, KeyError, IndexError) as e:
                logger.warning(
                    "LLM call failed provider=%s attempt=%s/%s error=%s",
                    provider.name,
                    attempt + 1,
                    retries,
                    e,
                )

            if attempt < retries - 1:
                time.sleep(min(2 ** attempt, 6))

        if idx < len(providers) - 1:
            logger.warning("Switching LLM fallback: %s -> %s", provider.name, providers[idx + 1].name)

    return ""


def translate_to_chinese(text: str, max_chars: int = 100) -> str:
    if not LLM_TRANSLATE:
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
    if not content or len(content) < 50:
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
    if not titles_and_summaries:
        return ""
    content = "\n".join(f"- {t}" for t in titles_and_summaries)
    prompt = f"""以下是今日{section_name}板块的新闻标题与摘要：

{content}

请作为新闻编辑，用2-3句话客观概括今日该板块的整体动态与主要议题，语言简洁中立，直接输出内容，不要加标题或前缀。"""
    return _chat(prompt, max_tokens=512, model=LLM_SUMMARY_MODEL)


__all__ = [
    "translate_to_chinese",
    "translate_summary_pair",
    "summarize_blog_article",
    "summarize_section",
    "TRANSLATION_MAX_WORKERS",
]
