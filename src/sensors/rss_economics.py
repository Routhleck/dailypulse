#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RSS Economics Sensor - 经济与金融
"""

import logging
import feedparser
from dataclasses import dataclass
from typing import List

logger = logging.getLogger(__name__)

FEEDS = [
    {"title": "Reuters Business",  "url": "https://feeds.reuters.com/reuters/businessNews"},
    {"title": "FT World Economy",  "url": "https://www.ft.com/world?format=rss"},
    {"title": "Bloomberg Markets", "url": "https://feeds.bloomberg.com/markets/news.rss"},
    {"title": "WSJ World",         "url": "https://feeds.a.dj.com/rss/RSSWorldNews.xml"},
    {"title": "WSJ Markets",       "url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml"},
    {"title": "WSJ US Business",   "url": "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml"},
    {"title": "WSJ Technology",    "url": "https://feeds.a.dj.com/rss/RSSWSJD.xml"},
    {"title": "The Economist",     "url": "https://www.economist.com/finance-and-economics/rss.xml"},
    {"title": "SCMP Business",     "url": "https://www.scmp.com/rss/92/feed"},
    {"title": "BBC中文财经",       "url": "https://feeds.bbci.co.uk/zhongwen/simp/business/rss.xml", "lang": "zh"},
]

MAX_PER_FEED = 5


@dataclass
class NewsArticle:
    title: str
    url: str
    source: str
    pub_date: str = ""
    summary: str = ""
    lang: str = "en"


def fetch_economics_news(limit: int = 8) -> List[NewsArticle]:
    articles = []
    seen_titles = set()

    for feed_cfg in FEEDS:
        try:
            parsed = feedparser.parse(feed_cfg["url"])
            lang = feed_cfg.get("lang", "en")
            count = 0
            for entry in parsed.entries:
                if count >= MAX_PER_FEED:
                    break
                title = (entry.get("title") or "").strip()
                url = entry.get("link") or entry.get("url") or ""
                if not title or not url:
                    continue
                key = title.lower()
                if key in seen_titles:
                    continue
                seen_titles.add(key)
                summary = entry.get("summary") or entry.get("description") or ""
                pub_date = entry.get("published") or entry.get("updated") or ""
                articles.append(NewsArticle(
                    title=title, url=url, source=feed_cfg["title"],
                    pub_date=pub_date[:16], summary=summary[:300], lang=lang,
                ))
                count += 1
        except Exception as e:
            logger.warning(f"[rss_economics] {feed_cfg['title']} failed: {e}")

    return articles[:limit]
