#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Event processing for DailyPulse:
- cluster similar articles into events
- score event importance
- classify cross-day trends using history snapshots
"""

from __future__ import annotations

import datetime as dt
import hashlib
import html
import logging
import re
from collections import Counter
from difflib import SequenceMatcher
from email.utils import parsedate_to_datetime
from typing import Any, Dict, Iterable, List, Optional, Set

try:
    from config import (
        EVENT_MATCH_THRESHOLD,
        EVENT_WINDOW_HOURS,
        SOURCE_DEFAULT_WEIGHT,
        SOURCE_WEIGHTS,
    )
except ImportError:
    from src.config import (
        EVENT_MATCH_THRESHOLD,
        EVENT_WINDOW_HOURS,
        SOURCE_DEFAULT_WEIGHT,
        SOURCE_WEIGHTS,
    )

logger = logging.getLogger(__name__)

SECTION_KEYS = ["politics", "economics", "military", "society", "asia", "analysis"]
_TOKEN_PATTERN = re.compile(r"[0-9a-zA-Z\u4e00-\u9fff]+")
_CLEAN_PATTERN = re.compile(r"[^0-9a-zA-Z\u4e00-\u9fff\s]+")

_STOPWORDS = {
    "the",
    "a",
    "an",
    "of",
    "to",
    "in",
    "on",
    "for",
    "with",
    "and",
    "from",
    "at",
    "as",
    "after",
    "amid",
    "over",
    "under",
    "says",
    "say",
    "saying",
    "will",
    "new",
    "how",
    "what",
    "why",
    "where",
    "when",
    "is",
    "are",
    "be",
    "by",
    "into",
    "via",
    "今日",
    "最新",
    "表示",
    "称",
    "一个",
    "我们",
    "他们",
}

_TREND_NEW = "🆕 新出现"
_TREND_HEATING = "🔥 持续发酵"
_TREND_COOLING = "⬇️ 降温"
_TREND_STEADY = "➡️ 持续关注"
_TREND_SPIKE = "🚨 突发"


def _parse_pub_datetime(pub_date: str) -> Optional[dt.datetime]:
    if not pub_date:
        return None

    text = pub_date.strip()
    if not text:
        return None

    candidates = [text]
    if "T" not in text and len(text) == 16 and text[4] == "-" and text[7] == "-":
        candidates.append(text + ":00")

    for candidate in candidates:
        try:
            parsed = parsedate_to_datetime(candidate)
            if parsed:
                if parsed.tzinfo is None:
                    return parsed.replace(tzinfo=dt.timezone.utc)
                return parsed.astimezone(dt.timezone.utc)
        except (TypeError, ValueError):
            pass

        try:
            parsed = dt.datetime.fromisoformat(candidate)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=dt.timezone.utc)
            return parsed.astimezone(dt.timezone.utc)
        except ValueError:
            pass

    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            parsed = dt.datetime.strptime(text, fmt)
            return parsed.replace(tzinfo=dt.timezone.utc)
        except ValueError:
            continue

    return None


def _normalize_title(title: str) -> str:
    plain = html.unescape(title or "").lower()
    plain = re.sub(r"<[^>]+>", " ", plain)
    plain = _CLEAN_PATTERN.sub(" ", plain)
    plain = re.sub(r"\s+", " ", plain).strip()
    return plain


def _tokenize(title: str) -> List[str]:
    tokens = _TOKEN_PATTERN.findall(title.lower())
    return [token for token in tokens if token and token not in _STOPWORDS and len(token) > 1]


def _jaccard(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _pair_similarity(norm_a: str, norm_b: str, tok_a: Set[str], tok_b: Set[str]) -> float:
    token_score = _jaccard(tok_a, tok_b)
    seq_score = SequenceMatcher(None, norm_a, norm_b).ratio()
    return 0.65 * token_score + 0.35 * seq_score


def _within_event_window(a: Optional[dt.datetime], b: Optional[dt.datetime], hours: int) -> bool:
    if not a or not b:
        return True
    return abs((a - b).total_seconds()) <= hours * 3600


def _build_event_id(section: str, tokens: Iterable[str], fallback: str) -> str:
    key_tokens = sorted(set(tokens))
    signature = " ".join(key_tokens[:8]) if key_tokens else fallback[:80]
    digest = hashlib.sha1(f"{section}:{signature}".encode("utf-8")).hexdigest()[:12]
    return f"{section[:3]}_{digest}"


def _primary_article(mentions: List[Dict[str, Any]]) -> Dict[str, Any]:
    def _key(item: Dict[str, Any]) -> tuple:
        parsed = _parse_pub_datetime(item.get("pub_date", ""))
        ts = parsed.timestamp() if parsed else 0
        return (ts, len(item.get("summary", "")))

    return max(mentions, key=_key)


def _section_items(intel: Dict[str, Any], section: str) -> List[Dict[str, Any]]:
    value = intel.get(section, [])
    return value if isinstance(value, list) else []


def build_events(intel: Dict[str, Any], run_date: str) -> Dict[str, List[Dict[str, Any]]]:
    """Cluster raw news items into event items for each section."""
    del run_date  # reserved for future heuristics

    output: Dict[str, List[Dict[str, Any]]] = {}

    for section in SECTION_KEYS:
        clusters: List[Dict[str, Any]] = []
        for item in _section_items(intel, section):
            title = item.get("title", "").strip()
            if not title:
                continue

            norm_title = _normalize_title(title)
            token_set = set(_tokenize(norm_title))
            pub_dt = _parse_pub_datetime(item.get("pub_date", ""))

            best_cluster: Optional[Dict[str, Any]] = None
            best_score = 0.0
            for cluster in clusters:
                if not _within_event_window(pub_dt, cluster["latest_pub_dt"], EVENT_WINDOW_HOURS):
                    continue
                score = _pair_similarity(
                    norm_title, cluster["norm_title"], token_set, cluster["token_set"]
                )
                if score >= EVENT_MATCH_THRESHOLD and score > best_score:
                    best_cluster = cluster
                    best_score = score

            mention = {
                "source": item.get("source", ""),
                "title": title,
                "url": item.get("url", ""),
                "pub_date": item.get("pub_date", ""),
                "summary": item.get("summary", ""),
                "lang": item.get("lang", "en"),
            }

            if not best_cluster:
                clusters.append(
                    {
                        "mentions": [mention],
                        "token_set": set(token_set),
                        "token_counter": Counter(token_set),
                        "norm_title": norm_title,
                        "latest_pub_dt": pub_dt,
                    }
                )
                continue

            best_cluster["mentions"].append(mention)
            best_cluster["token_set"].update(token_set)
            best_cluster["token_counter"].update(token_set)
            if pub_dt and (not best_cluster["latest_pub_dt"] or pub_dt > best_cluster["latest_pub_dt"]):
                best_cluster["latest_pub_dt"] = pub_dt
            # Keep the most representative (longest) normalized title for matching.
            if len(norm_title) > len(best_cluster["norm_title"]):
                best_cluster["norm_title"] = norm_title

        events: List[Dict[str, Any]] = []
        for cluster in clusters:
            mentions = cluster["mentions"]
            primary = _primary_article(mentions)
            ordered_sources = sorted({m.get("source", "") for m in mentions if m.get("source")})
            token_counter = cluster["token_counter"]
            top_tokens = [tok for tok, _ in token_counter.most_common(8)]
            event = {
                "event_id": _build_event_id(section, top_tokens, cluster["norm_title"]),
                "title": primary.get("title", ""),
                "title_norm": _normalize_title(primary.get("title", "")),
                "url": primary.get("url", ""),
                "pub_date": primary.get("pub_date", ""),
                "summary": primary.get("summary", ""),
                "lang": primary.get("lang", "en"),
                "source": primary.get("source", ""),
                "sources": ordered_sources,
                "source_count": len(ordered_sources),
                "mention_count": len(mentions),
                "mentions": mentions,
                "score": 0.0,
                "trend": _TREND_NEW,
            }
            events.append(event)

        output[section] = events

    return output


def _source_quality_score(sources: List[str]) -> float:
    if not sources:
        return SOURCE_DEFAULT_WEIGHT
    weights = [float(SOURCE_WEIGHTS.get(source, SOURCE_DEFAULT_WEIGHT)) for source in sources]
    return sum(weights) / len(weights)


def _recency_score(pub_date: str, run_date: str) -> float:
    pub_dt = _parse_pub_datetime(pub_date)
    if not pub_dt:
        return 0.4

    run_day = dt.date.fromisoformat(run_date)
    run_dt = dt.datetime.combine(run_day, dt.time(23, 59, 59), tzinfo=dt.timezone.utc)
    delta_hours = max(0.0, (run_dt - pub_dt).total_seconds() / 3600)
    return max(0.0, min(1.0, 1 - delta_hours / 72))


def score_events(events_by_section: Dict[str, List[Dict[str, Any]]], run_date: str) -> Dict[str, List[Dict[str, Any]]]:
    """Score events by recency + source quality + multi-source strength."""
    for section, events in events_by_section.items():
        for event in events:
            recency = _recency_score(event.get("pub_date", ""), run_date)
            source_quality = _source_quality_score(event.get("sources", []))
            multi_source = min(1.0, float(event.get("source_count", 1)) / 4.0)
            score = 0.45 * recency + 0.30 * source_quality + 0.25 * multi_source
            event["score"] = round(score, 4)

        events.sort(
            key=lambda x: (
                float(x.get("score", 0)),
                int(x.get("mention_count", 0)),
                int(x.get("source_count", 0)),
            ),
            reverse=True,
        )
        events_by_section[section] = events

    return events_by_section


def _best_history_match(
    event: Dict[str, Any], historical: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    current_id = event.get("event_id", "")
    current_norm = event.get("title_norm", "")
    current_tokens = set(_tokenize(current_norm))

    exact = [row for row in historical if row.get("event_id") == current_id]
    if exact:
        return exact[0]

    best_row = None
    best_score = 0.0
    for row in historical:
        row_norm = row.get("title_norm", "")
        row_tokens = set(_tokenize(row_norm))
        score = _pair_similarity(current_norm, row_norm, current_tokens, row_tokens)
        if score > best_score:
            best_score = score
            best_row = row

    if best_row and best_score >= EVENT_MATCH_THRESHOLD:
        return best_row
    return None


def classify_trends(
    events_by_section: Dict[str, List[Dict[str, Any]]], history_repo: Any, run_date: str
) -> Dict[str, List[Dict[str, Any]]]:
    """Classify events using recent snapshots stored in history repo."""
    if not history_repo:
        return events_by_section

    for section, events in events_by_section.items():
        historical = history_repo.load_recent_events(section=section, run_date=run_date, days=7)

        # Build per-event_id historical mention counts for spike detection
        hist_mentions_by_id: Dict[str, List[int]] = {}
        for row in historical:
            eid = row.get("event_id", "")
            if eid:
                hist_mentions_by_id.setdefault(eid, []).append(int(row.get("mention_count", 0)))

        for event in events:
            match = _best_history_match(event, historical)
            if not match:
                event["trend"] = _TREND_NEW
                continue

            prev_mentions = int(match.get("mention_count", 0))
            curr_mentions = int(event.get("mention_count", 0))

            # Spike: current mentions >= 2× historical average (avg must be >= 2)
            matched_id = match.get("event_id", "")
            hist_counts = hist_mentions_by_id.get(matched_id, [prev_mentions])
            hist_avg = sum(hist_counts) / len(hist_counts)
            if hist_avg >= 2 and curr_mentions >= hist_avg * 2:
                event["trend"] = _TREND_SPIKE
            elif curr_mentions > prev_mentions:
                event["trend"] = _TREND_HEATING
            elif curr_mentions < prev_mentions:
                event["trend"] = _TREND_COOLING
            elif int(event.get("source_count", 1)) >= 2:
                event["trend"] = _TREND_HEATING
            else:
                event["trend"] = _TREND_STEADY

            event["previous_run_date"] = match.get("run_date", "")

    return events_by_section


def build_quality_metrics(
    raw_intel: Dict[str, List[Dict[str, Any]]],
    events_by_section: Dict[str, List[Dict[str, Any]]],
    collector_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build quality metrics used by reports and history snapshots."""
    collector_meta = collector_meta or {}
    total_raw = int(collector_meta.get("total_raw", 0))
    total_dedup = int(collector_meta.get("total_dedup", 0))

    if total_raw == 0:
        total_raw = sum(len(raw_intel.get(section, [])) for section in SECTION_KEYS)
    if total_dedup == 0:
        total_dedup = total_raw

    section_counts = {
        section: len(events_by_section.get(section, []))
        for section in SECTION_KEYS
    }
    total_events = sum(section_counts.values())

    dedup_rate = 0.0
    if total_raw > 0:
        dedup_rate = round((1 - (total_dedup / total_raw)) * 100, 2)

    # Count trend distribution across all events
    trend_counts: Dict[str, int] = {
        "new": 0, "heating": 0, "cooling": 0, "steady": 0, "spike": 0
    }
    _trend_map = {
        _TREND_NEW: "new",
        _TREND_HEATING: "heating",
        _TREND_COOLING: "cooling",
        _TREND_STEADY: "steady",
        _TREND_SPIKE: "spike",
    }
    for events in events_by_section.values():
        for event in events:
            trend = event.get("trend", _TREND_NEW)
            key = _trend_map.get(trend, "new")
            trend_counts[key] += 1

    return {
        "total_raw": total_raw,
        "total_dedup": total_dedup,
        "total_events": total_events,
        "dedup_rate": dedup_rate,
        "translation_total": 0,
        "translation_success": 0,
        "translation_rate": 0.0,
        "section_counts": section_counts,
        "trend_counts": trend_counts,
    }

