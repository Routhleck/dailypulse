#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SQLite-backed history storage for event snapshots and quality metrics.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import os
import sqlite3
from typing import Any, Dict, List

try:
    from config import HISTORY_RETENTION_DAYS
except ImportError:
    from src.config import HISTORY_RETENTION_DAYS

logger = logging.getLogger(__name__)


class HistoryRepo:
    """Persist daily events and metrics into a local SQLite database."""

    def __init__(self, db_path: str, retention_days: int = HISTORY_RETENTION_DAYS):
        self.db_path = db_path
        self.retention_days = retention_days
        self._ensure_parent_dir()
        self._initialize_schema()

    def _ensure_parent_dir(self) -> None:
        parent = os.path.dirname(self.db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    run_date TEXT NOT NULL,
                    section TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    title_norm TEXT NOT NULL,
                    primary_url TEXT,
                    primary_summary TEXT,
                    lang TEXT,
                    mention_count INTEGER NOT NULL DEFAULT 1,
                    source_count INTEGER NOT NULL DEFAULT 1,
                    sources_json TEXT NOT NULL DEFAULT '[]',
                    score REAL NOT NULL DEFAULT 0,
                    trend TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (run_date, section, event_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS event_mentions (
                    run_date TEXT NOT NULL,
                    section TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    source TEXT,
                    title TEXT,
                    url TEXT,
                    pub_date TEXT,
                    summary TEXT,
                    lang TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS daily_metrics (
                    run_date TEXT PRIMARY KEY,
                    total_raw INTEGER NOT NULL DEFAULT 0,
                    total_dedup INTEGER NOT NULL DEFAULT 0,
                    total_events INTEGER NOT NULL DEFAULT 0,
                    dedup_rate REAL NOT NULL DEFAULT 0,
                    translation_total INTEGER NOT NULL DEFAULT 0,
                    translation_success INTEGER NOT NULL DEFAULT 0,
                    translation_rate REAL NOT NULL DEFAULT 0,
                    politics_count INTEGER NOT NULL DEFAULT 0,
                    economics_count INTEGER NOT NULL DEFAULT 0,
                    military_count INTEGER NOT NULL DEFAULT 0,
                    society_count INTEGER NOT NULL DEFAULT 0,
                    asia_count INTEGER NOT NULL DEFAULT 0,
                    analysis_count INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_section_date ON events(section, run_date)"
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO schema_meta(key, value)
                VALUES ('version', '1')
                """
            )

    def load_recent_events(self, section: str, run_date: str, days: int = 7) -> List[Dict[str, Any]]:
        run_day = dt.date.fromisoformat(run_date)
        lower = (run_day - dt.timedelta(days=days)).isoformat()

        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT run_date, section, event_id, title, title_norm, mention_count,
                       source_count, score, trend, sources_json
                FROM events
                WHERE section = ?
                  AND run_date < ?
                  AND run_date >= ?
                ORDER BY run_date DESC
                """,
                (section, run_date, lower),
            ).fetchall()

        items: List[Dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            try:
                item["sources"] = json.loads(item.get("sources_json") or "[]")
            except json.JSONDecodeError:
                item["sources"] = []
            items.append(item)
        return items

    def load_day_snapshot(self, run_date: str) -> Dict[str, Any]:
        with self._connect() as conn:
            events_rows = conn.execute(
                """
                SELECT run_date, section, event_id, title, title_norm, primary_url, primary_summary,
                       lang, mention_count, source_count, sources_json, score, trend
                FROM events
                WHERE run_date = ?
                ORDER BY section, score DESC
                """,
                (run_date,),
            ).fetchall()
            metrics_row = conn.execute(
                "SELECT * FROM daily_metrics WHERE run_date = ?",
                (run_date,),
            ).fetchone()

        events_by_section: Dict[str, List[Dict[str, Any]]] = {}
        for row in events_rows:
            section = row["section"]
            payload = dict(row)
            try:
                payload["sources"] = json.loads(payload.get("sources_json") or "[]")
            except json.JSONDecodeError:
                payload["sources"] = []
            events_by_section.setdefault(section, []).append(payload)

        return {
            "events": events_by_section,
            "metrics": dict(metrics_row) if metrics_row else {},
        }

    def save_day_snapshot(
        self, run_date: str, events_by_section: Dict[str, List[Dict[str, Any]]], metrics: Dict[str, Any]
    ) -> None:
        now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

        with self._connect() as conn:
            conn.execute("DELETE FROM events WHERE run_date = ?", (run_date,))
            conn.execute("DELETE FROM event_mentions WHERE run_date = ?", (run_date,))
            conn.execute("DELETE FROM daily_metrics WHERE run_date = ?", (run_date,))

            for section, events in events_by_section.items():
                for event in events:
                    sources = event.get("sources", [])
                    conn.execute(
                        """
                        INSERT INTO events(
                            run_date, section, event_id, title, title_norm, primary_url,
                            primary_summary, lang, mention_count, source_count, sources_json,
                            score, trend, created_at
                        ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            run_date,
                            section,
                            event.get("event_id", ""),
                            event.get("title", ""),
                            event.get("title_norm", ""),
                            event.get("url", ""),
                            event.get("summary", ""),
                            event.get("lang", ""),
                            int(event.get("mention_count", 1)),
                            int(event.get("source_count", len(sources) or 1)),
                            json.dumps(sources, ensure_ascii=False),
                            float(event.get("score", 0.0)),
                            event.get("trend", ""),
                            now,
                        ),
                    )

                    mentions = event.get("mentions", [])
                    for mention in mentions:
                        conn.execute(
                            """
                            INSERT INTO event_mentions(
                                run_date, section, event_id, source, title, url, pub_date, summary, lang
                            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                run_date,
                                section,
                                event.get("event_id", ""),
                                mention.get("source", ""),
                                mention.get("title", ""),
                                mention.get("url", ""),
                                mention.get("pub_date", ""),
                                mention.get("summary", ""),
                                mention.get("lang", ""),
                            ),
                        )

            section_counts = metrics.get("section_counts", {})
            conn.execute(
                """
                INSERT INTO daily_metrics(
                    run_date, total_raw, total_dedup, total_events, dedup_rate,
                    translation_total, translation_success, translation_rate,
                    politics_count, economics_count, military_count, society_count,
                    asia_count, analysis_count, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_date,
                    int(metrics.get("total_raw", 0)),
                    int(metrics.get("total_dedup", 0)),
                    int(metrics.get("total_events", 0)),
                    float(metrics.get("dedup_rate", 0)),
                    int(metrics.get("translation_total", 0)),
                    int(metrics.get("translation_success", 0)),
                    float(metrics.get("translation_rate", 0)),
                    int(section_counts.get("politics", 0)),
                    int(section_counts.get("economics", 0)),
                    int(section_counts.get("military", 0)),
                    int(section_counts.get("society", 0)),
                    int(section_counts.get("asia", 0)),
                    int(section_counts.get("analysis", 0)),
                    now,
                ),
            )

        self.prune_old_data(run_date=run_date, retention_days=self.retention_days)

    def prune_old_data(self, run_date: str, retention_days: int | None = None) -> None:
        retention = retention_days if retention_days is not None else self.retention_days
        cutoff = (dt.date.fromisoformat(run_date) - dt.timedelta(days=retention)).isoformat()

        with self._connect() as conn:
            conn.execute("DELETE FROM event_mentions WHERE run_date < ?", (cutoff,))
            conn.execute("DELETE FROM events WHERE run_date < ?", (cutoff,))
            conn.execute("DELETE FROM daily_metrics WHERE run_date < ?", (cutoff,))

        logger.info("History pruned with cutoff=%s", cutoff)
