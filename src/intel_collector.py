#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Intel Collector - 数据采集模块（国际时事日报版）
负责从所有 RSS 传感器并行收集新闻数据
"""

import sys
import os
import logging
import concurrent.futures
from typing import Dict, List

logger = logging.getLogger(__name__)

FETCH_TIMEOUT = 120

# --- Path Setup ---
LOCAL_SRC_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src')
if LOCAL_SRC_PATH not in sys.path:
    sys.path.insert(0, LOCAL_SRC_PATH)

# --- Imports: RSS Sensors (graceful degradation) ---
POLITICS_AVAILABLE = False
ECONOMICS_AVAILABLE = False
MILITARY_AVAILABLE = False
SOCIETY_AVAILABLE = False
ASIA_AVAILABLE = False
ANALYSIS_AVAILABLE = False

try:
    from sensors.rss_politics import fetch_politics_news
    POLITICS_AVAILABLE = True
except ImportError:
    logger.info("Politics sensor not available.")

try:
    from sensors.rss_economics import fetch_economics_news
    ECONOMICS_AVAILABLE = True
except ImportError:
    logger.info("Economics sensor not available.")

try:
    from sensors.rss_military import fetch_military_news
    MILITARY_AVAILABLE = True
except ImportError:
    logger.info("Military sensor not available.")

try:
    from sensors.rss_society import fetch_society_news
    SOCIETY_AVAILABLE = True
except ImportError:
    logger.info("Society sensor not available.")

try:
    from sensors.rss_asia import fetch_asia_news
    ASIA_AVAILABLE = True
except ImportError:
    logger.info("Asia sensor not available.")

try:
    from sensors.rss_analysis import fetch_analysis_news
    ANALYSIS_AVAILABLE = True
except ImportError:
    logger.info("Analysis sensor not available.")


def _article_to_dict(article) -> Dict:
    return {
        "source": article.source,
        "title": article.title,
        "url": article.url,
        "pub_date": article.pub_date,
        "summary": article.summary,
        "lang": article.lang,
    }


def _fetch_politics(limit: int) -> List[Dict]:
    if not POLITICS_AVAILABLE:
        return []
    try:
        return [_article_to_dict(a) for a in fetch_politics_news(limit)]
    except Exception as e:
        logger.warning(f"Politics fetch failed: {e}")
        return []


def _fetch_economics(limit: int) -> List[Dict]:
    if not ECONOMICS_AVAILABLE:
        return []
    try:
        return [_article_to_dict(a) for a in fetch_economics_news(limit)]
    except Exception as e:
        logger.warning(f"Economics fetch failed: {e}")
        return []


def _fetch_military(limit: int) -> List[Dict]:
    if not MILITARY_AVAILABLE:
        return []
    try:
        return [_article_to_dict(a) for a in fetch_military_news(limit)]
    except Exception as e:
        logger.warning(f"Military fetch failed: {e}")
        return []


def _fetch_society(limit: int) -> List[Dict]:
    if not SOCIETY_AVAILABLE:
        return []
    try:
        return [_article_to_dict(a) for a in fetch_society_news(limit)]
    except Exception as e:
        logger.warning(f"Society fetch failed: {e}")
        return []


def _fetch_asia(limit: int) -> List[Dict]:
    if not ASIA_AVAILABLE:
        return []
    try:
        return [_article_to_dict(a) for a in fetch_asia_news(limit)]
    except Exception as e:
        logger.warning(f"Asia fetch failed: {e}")
        return []


def _fetch_analysis(limit: int) -> List[Dict]:
    if not ANALYSIS_AVAILABLE:
        return []
    try:
        return [_article_to_dict(a) for a in fetch_analysis_news(limit)]
    except Exception as e:
        logger.warning(f"Analysis fetch failed: {e}")
        return []


def _dedup_items(items: List[Dict], key: str = "title") -> List[Dict]:
    """去重：基于标题去除重复条目。"""
    seen = set()
    unique = []
    for item in items:
        title = item.get(key, "").strip().lower()
        if title and title not in seen:
            seen.add(title)
            unique.append(item)
        elif not title:
            unique.append(item)
    return unique


def fetch_all_sources(limit_per_source: int = 10, include_meta: bool = False) -> dict:
    """从所有 RSS 传感器并行抓取国际新闻。"""
    logger.info(f"Starting fetch from all RSS sources (limit={limit_per_source})...")

    def _safe_result(future, name):
        try:
            return future.result(timeout=FETCH_TIMEOUT)
        except (concurrent.futures.TimeoutError, Exception) as e:
            logger.warning(f"{name} timed out or failed: {e}")
            return []

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        f_politics  = executor.submit(_fetch_politics,  limit_per_source)
        f_economics = executor.submit(_fetch_economics, limit_per_source)
        f_military  = executor.submit(_fetch_military,  limit_per_source)
        f_society   = executor.submit(_fetch_society,   limit_per_source)
        f_asia      = executor.submit(_fetch_asia,      limit_per_source)
        f_analysis  = executor.submit(_fetch_analysis,  6)

        politics  = _safe_result(f_politics,  "Politics")
        economics = _safe_result(f_economics, "Economics")
        military  = _safe_result(f_military,  "Military")
        society   = _safe_result(f_society,   "Society")
        asia      = _safe_result(f_asia,      "Asia")
        analysis  = _safe_result(f_analysis,  "Analysis")

    raw = {
        "politics": politics,
        "economics": economics,
        "military": military,
        "society": society,
        "asia": asia,
        "analysis": analysis,
    }
    deduped = {key: _dedup_items(items) for key, items in raw.items()}
    intel = dict(deduped)

    total = sum(len(v) for v in deduped.values())
    logger.info(f"Fetch complete: {total} total items collected")

    if include_meta:
        raw_counts = {key: len(items) for key, items in raw.items()}
        dedup_counts = {key: len(items) for key, items in deduped.items()}
        intel["__meta__"] = {
            "section_raw_counts": raw_counts,
            "section_dedup_counts": dedup_counts,
            "total_raw": sum(raw_counts.values()),
            "total_dedup": sum(dedup_counts.values()),
        }

    return intel


__all__ = ['fetch_all_sources']
