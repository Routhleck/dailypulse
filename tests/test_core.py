"""
DailyPulse - 基础测试
测试核心模块的基本功能，不依赖外部 API。
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

SECTIONS = ["politics", "economics", "military", "society", "asia", "analysis"]


class TestConfig:
    def test_config_imports(self):
        from src.config import LLM_BASE_URL, JINA_READER_URL, setup_logging

        assert callable(setup_logging)
        assert LLM_BASE_URL.startswith("https://")
        assert JINA_READER_URL.startswith("https://")

    def test_rss_limits_defined(self):
        from src.config import (
            RSS_ANALYSIS_LIMIT,
            RSS_ASIA_LIMIT,
            RSS_ECONOMICS_LIMIT,
            RSS_FETCH_TIMEOUT,
            RSS_MAX_PER_FEED,
            RSS_MILITARY_LIMIT,
            RSS_POLITICS_LIMIT,
            RSS_SOCIETY_LIMIT,
        )

        assert RSS_FETCH_TIMEOUT > 0
        assert RSS_MAX_PER_FEED > 0
        assert RSS_POLITICS_LIMIT > 0
        assert RSS_ECONOMICS_LIMIT > 0
        assert RSS_MILITARY_LIMIT > 0
        assert RSS_SOCIETY_LIMIT > 0
        assert RSS_ASIA_LIMIT > 0
        assert RSS_ANALYSIS_LIMIT > 0


class TestDedup:
    def test_dedup_removes_duplicates(self):
        from src.intel_collector import _dedup_items

        items = [
            {"title": "Hello World", "url": "a"},
            {"title": "hello world", "url": "b"},
            {"title": "Different", "url": "c"},
        ]
        result = _dedup_items(items)
        assert len(result) == 2

    def test_dedup_keeps_empty_titles(self):
        from src.intel_collector import _dedup_items

        items = [{"title": "", "url": "a"}, {"title": "", "url": "b"}]
        result = _dedup_items(items)
        assert len(result) == 2

    def test_dedup_empty_list(self):
        from src.intel_collector import _dedup_items

        assert _dedup_items([]) == []


class TestEventProcessor:
    def test_build_events_clusters_similar_titles(self):
        from src.event_processor import build_events

        intel = {
            "politics": [
                {
                    "title": "U.S. announces new sanctions on Country X",
                    "url": "https://a.example",
                    "source": "Reuters World",
                    "pub_date": "2026-01-01 08:00",
                    "summary": "Sanctions package details.",
                    "lang": "en",
                },
                {
                    "title": "US announces sanctions on Country X",
                    "url": "https://b.example",
                    "source": "AP Top News",
                    "pub_date": "2026-01-01 09:00",
                    "summary": "Another outlet covering same event.",
                    "lang": "en",
                },
                {
                    "title": "China hosts regional summit",
                    "url": "https://c.example",
                    "source": "BBC World News",
                    "pub_date": "2026-01-01 10:00",
                    "summary": "Separate event.",
                    "lang": "en",
                },
            ],
            "economics": [],
            "military": [],
            "society": [],
            "asia": [],
            "analysis": [],
        }

        events = build_events(intel, run_date="2026-01-01")
        assert len(events["politics"]) == 2
        assert max(e["mention_count"] for e in events["politics"]) == 2

    def test_score_events_prefers_multi_source_and_recency(self):
        from src.event_processor import score_events

        events = {
            "politics": [
                {
                    "title": "A",
                    "title_norm": "a",
                    "url": "https://a.example",
                    "summary": "",
                    "lang": "en",
                    "source": "Reuters World",
                    "sources": ["Reuters World", "AP Top News"],
                    "source_count": 2,
                    "mention_count": 3,
                    "pub_date": "2026-01-02 09:00",
                    "score": 0.0,
                },
                {
                    "title": "B",
                    "title_norm": "b",
                    "url": "https://b.example",
                    "summary": "",
                    "lang": "en",
                    "source": "BBC World News",
                    "sources": ["BBC World News"],
                    "source_count": 1,
                    "mention_count": 1,
                    "pub_date": "2025-12-29 09:00",
                    "score": 0.0,
                },
            ],
            "economics": [],
            "military": [],
            "society": [],
            "asia": [],
            "analysis": [],
        }

        ranked = score_events(events, run_date="2026-01-02")
        assert ranked["politics"][0]["title"] == "A"
        assert ranked["politics"][0]["score"] >= ranked["politics"][1]["score"]

    def test_classify_trends_from_history(self, tmp_path):
        from src.event_processor import classify_trends
        from src.history_repo import HistoryRepo

        db_path = str(tmp_path / "pulse.db")
        repo = HistoryRepo(db_path)

        historical_events = {
            "politics": [
                {
                    "event_id": "pol_abc123",
                    "title": "US sanctions Country X",
                    "title_norm": "us sanctions country x",
                    "url": "https://old.example",
                    "summary": "old",
                    "lang": "en",
                    "source": "Reuters World",
                    "sources": ["Reuters World"],
                    "source_count": 1,
                    "mention_count": 1,
                    "mentions": [
                        {
                            "source": "Reuters World",
                            "title": "US sanctions Country X",
                            "url": "https://old.example",
                            "pub_date": "2026-01-01 08:00",
                            "summary": "old",
                            "lang": "en",
                        }
                    ],
                    "score": 0.8,
                    "trend": "🆕 新出现",
                }
            ],
            "economics": [],
            "military": [],
            "society": [],
            "asia": [],
            "analysis": [],
        }

        metrics = {
            "total_raw": 1,
            "total_dedup": 1,
            "total_events": 1,
            "dedup_rate": 0.0,
            "translation_total": 0,
            "translation_success": 0,
            "translation_rate": 0.0,
            "section_counts": {k: 0 for k in SECTIONS},
        }
        metrics["section_counts"]["politics"] = 1

        repo.save_day_snapshot("2026-01-01", historical_events, metrics)

        today_events = {
            "politics": [
                {
                    "event_id": "pol_abc123",
                    "title": "US sanctions Country X",
                    "title_norm": "us sanctions country x",
                    "url": "https://new.example",
                    "summary": "new",
                    "lang": "en",
                    "source": "Reuters World",
                    "sources": ["Reuters World", "AP Top News"],
                    "source_count": 2,
                    "mention_count": 3,
                    "mentions": [],
                    "score": 0.9,
                    "trend": "",
                }
            ],
            "economics": [],
            "military": [],
            "society": [],
            "asia": [],
            "analysis": [],
        }

        classified = classify_trends(today_events, repo, run_date="2026-01-02")
        assert "持续发酵" in classified["politics"][0]["trend"]


class TestQualityMetrics:
    def test_build_quality_metrics(self):
        from src.event_processor import build_quality_metrics

        raw_intel = {k: [] for k in SECTIONS}
        raw_intel["politics"] = [{"title": "a"}, {"title": "b"}]

        events = {k: [] for k in SECTIONS}
        events["politics"] = [{"event_id": "x"}]

        metrics = build_quality_metrics(
            raw_intel,
            events,
            collector_meta={"total_raw": 2, "total_dedup": 2},
        )

        assert metrics["total_raw"] == 2
        assert metrics["total_dedup"] == 2
        assert metrics["total_events"] == 1
        assert metrics["section_counts"]["politics"] == 1
        assert "trend_counts" in metrics

    def test_build_quality_metrics_trend_counts(self):
        from src.event_processor import build_quality_metrics

        raw_intel = {k: [] for k in SECTIONS}
        events = {k: [] for k in SECTIONS}
        events["politics"] = [
            {"event_id": "a", "trend": "🆕 新出现"},
            {"event_id": "b", "trend": "🔥 持续发酵"},
            {"event_id": "c", "trend": "🚨 突发"},
        ]

        metrics = build_quality_metrics(raw_intel, events)
        tc = metrics["trend_counts"]
        assert tc["new"] == 1
        assert tc["heating"] == 1
        assert tc["spike"] == 1
        assert tc["cooling"] == 0

    def test_classify_trends_spike(self, tmp_path):
        from src.event_processor import classify_trends
        from src.history_repo import HistoryRepo

        db_path = str(tmp_path / "pulse.db")
        repo = HistoryRepo(db_path)

        # Save two historical days with mention_count=2 each → avg=2
        for day, run_date in [("2026-01-01", "2026-01-01"), ("2026-01-02", "2026-01-02")]:
            hist = {k: [] for k in SECTIONS}
            hist["politics"] = [{
                "event_id": "pol_spike1",
                "title": "Trade war escalates",
                "title_norm": "trade war escalates",
                "url": "https://example.com",
                "summary": "",
                "lang": "en",
                "source": "Reuters",
                "sources": ["Reuters"],
                "source_count": 1,
                "mention_count": 2,
                "mentions": [],
                "score": 0.5,
                "trend": "🆕 新出现",
            }]
            m = {"total_raw": 2, "total_dedup": 2, "total_events": 1, "dedup_rate": 0.0,
                 "translation_total": 0, "translation_success": 0, "translation_rate": 0.0,
                 "section_counts": {k: 0 for k in SECTIONS}}
            repo.save_day_snapshot(run_date, hist, m)

        # Today: same event with mention_count=6 (≥ avg*2 = 4)
        today = {k: [] for k in SECTIONS}
        today["politics"] = [{
            "event_id": "pol_spike1",
            "title": "Trade war escalates",
            "title_norm": "trade war escalates",
            "url": "https://example.com",
            "summary": "",
            "lang": "en",
            "source": "Reuters",
            "sources": ["Reuters"],
            "source_count": 1,
            "mention_count": 6,
            "mentions": [],
            "score": 0.9,
            "trend": "",
        }]

        classified = classify_trends(today, repo, run_date="2026-01-03")
        assert "突发" in classified["politics"][0]["trend"]


class TestReportGenerator:
    def test_generate_empty_report(self):
        from src.report_generator import generate_report

        intel = {k: [] for k in SECTIONS}
        metrics = {
            "total_raw": 0,
            "total_dedup": 0,
            "total_events": 0,
            "dedup_rate": 0.0,
            "translation_total": 0,
            "translation_success": 0,
            "translation_rate": 0.0,
            "section_counts": {k: 0 for k in SECTIONS},
        }
        report = generate_report(intel, "2026-01-01", event_mode=True, metrics=metrics)
        assert "国际时事日报" in report
        assert "2026-01-01" in report
        assert "暂无数据" in report
        assert "趋势" in report

    def test_generate_report_with_event_data(self):
        from src.report_generator import generate_report

        intel = {k: [] for k in SECTIONS}
        intel["politics"] = [
            {
                "title": "UN Summit",
                "url": "https://example.com",
                "source": "Reuters",
                "pub_date": "2026-01-01",
                "summary": "World leaders meet.",
                "lang": "en",
                "sources": ["Reuters", "AP"],
                "source_count": 2,
                "mention_count": 3,
                "trend": "🔥 持续发酵",
            }
        ]

        metrics = {
            "total_raw": 10,
            "total_dedup": 8,
            "total_events": 6,
            "dedup_rate": 20.0,
            "translation_total": 0,
            "translation_success": 0,
            "translation_rate": 0.0,
            "section_counts": {k: 0 for k in SECTIONS},
        }

        report = generate_report(intel, "2026-01-01", event_mode=True, metrics=metrics)
        assert "UN Summit" in report
        assert "https://example.com" in report
        assert "持续发酵" in report
        assert "趋势" in report


class TestSensorDataclasses:
    def test_news_article_defaults(self):
        from src.sensors.rss_politics import NewsArticle

        a = NewsArticle(title="Test", url="https://example.com", source="BBC")
        assert a.lang == "en"
        assert a.summary == ""

    def test_zh_article(self):
        from src.sensors.rss_politics import NewsArticle

        a = NewsArticle(title="标题", url="https://example.com", source="BBC中文", lang="zh")
        assert a.lang == "zh"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
