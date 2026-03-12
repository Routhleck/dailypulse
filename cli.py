#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Intel Briefing CLI - 命令行入口
国际时事日报生成器
"""

import argparse
import os
import sys
from datetime import datetime

SRC_PATH = os.path.join(os.path.dirname(__file__), "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from src.config import DEFAULT_DB_PATH
from src.event_processor import build_events, build_quality_metrics, classify_trends, score_events
from src.history_repo import HistoryRepo
from src.intel_collector import fetch_all_sources
from src.report_generator import generate_report


def main():
    parser = argparse.ArgumentParser(description="国际时事日报生成器")
    parser.add_argument("--limit", type=int, default=10, help="Items per source")
    parser.add_argument("--test", action="store_true", help="Test mode (1 item per source)")
    parser.add_argument("--output", type=str, help="Custom output path")
    parser.add_argument("--db-path", type=str, default=DEFAULT_DB_PATH, help="SQLite state DB path")
    parser.add_argument("--no-event-mode", action="store_true", help="Disable event clustering mode")
    parser.add_argument("--no-trend", action="store_true", help="Disable history trend classification")
    args = parser.parse_args()

    limit = 1 if args.test else args.limit
    date_str = datetime.now().strftime("%Y-%m-%d")
    event_mode = not args.no_event_mode
    trend_mode = not args.no_trend

    print(f"\n{'=' * 60}")
    print("  国际时事日报 (World Affairs Daily Briefing)")
    print(f"  Date: {date_str} | Limit: {limit}/source | Event Mode: {event_mode}")
    print(f"{'=' * 60}\n")

    raw_intel = fetch_all_sources(limit_per_source=limit, include_meta=True)
    collector_meta = raw_intel.pop("__meta__", {})

    final_intel = raw_intel
    history_repo = None

    if event_mode:
        final_intel = build_events(raw_intel, run_date=date_str)
        final_intel = score_events(final_intel, run_date=date_str)

        if args.db_path:
            history_repo = HistoryRepo(args.db_path)
            if trend_mode:
                final_intel = classify_trends(final_intel, history_repo=history_repo, run_date=date_str)

    metrics = build_quality_metrics(raw_intel, final_intel, collector_meta=collector_meta)

    report = generate_report(
        final_intel,
        date_str,
        event_mode=event_mode,
        metrics=metrics,
    )

    if args.output:
        output_path = args.output
    else:
        reports_dir = os.path.join(os.path.dirname(__file__), "reports", "daily_briefings")
        os.makedirs(reports_dir, exist_ok=True)
        output_path = (
            os.path.join(reports_dir, "Morning_Report_TEST.md")
            if args.test
            else os.path.join(reports_dir, f"Morning_Report_{date_str}.md")
        )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    if event_mode and history_repo:
        history_repo.save_day_snapshot(date_str, final_intel, metrics)

    print(f"\n[SUCCESS] Report saved to: {output_path}")
    print(
        "[METRICS] raw={raw} dedup={dedup} events={events} dedup_rate={rate}% translation_rate={tr}%".format(
            raw=metrics.get("total_raw", 0),
            dedup=metrics.get("total_dedup", 0),
            events=metrics.get("total_events", 0),
            rate=metrics.get("dedup_rate", 0),
            tr=metrics.get("translation_rate", 0),
        )
    )

    print("\n--- Preview (first 40 lines) ---\n")
    for line in report.split("\n")[:40]:
        print(line)


if __name__ == "__main__":
    main()
