import argparse
import datetime
import logging
import os

from src.config import DEFAULT_DB_PATH, setup_logging
from src.event_processor import build_events, build_quality_metrics, classify_trends, score_events
from src.history_repo import HistoryRepo
from src.intel_collector import fetch_all_sources
from src.report_generator import generate_report

logger = logging.getLogger(__name__)

REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports", "daily_briefings")


def generate_morning_report(
    days: int = 1,
    db_path: str = DEFAULT_DB_PATH,
    event_mode: bool = True,
    trend_mode: bool = True,
):
    """Generate daily/periodic briefing with event processing and optional trend analysis."""
    setup_logging()
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")

    if days == 1:
        report_title = f"国际时事日报: {date_str}"
        file_name = f"Morning_Report_{date_str}.md"
        limit = 15
    else:
        report_title = f"周期性情报简报 (过去 {days} 天): {date_str}"
        file_name = f"Weekly_Report_{days}Days_{date_str}.md"
        limit = 30

    report_file = os.path.join(REPORT_DIR, file_name)
    os.makedirs(REPORT_DIR, exist_ok=True)

    logger.info(
        "开始生成情报简报 - 周期: %s 天, event_mode=%s, trend_mode=%s, 目标: %s",
        days,
        event_mode,
        trend_mode,
        file_name,
    )

    raw_intel = fetch_all_sources(limit_per_source=limit, include_meta=True)
    collector_meta = raw_intel.pop("__meta__", {})

    final_intel = raw_intel
    history_repo = None

    if event_mode:
        logger.info("Building event clusters...")
        final_intel = build_events(raw_intel, run_date=date_str)
        final_intel = score_events(final_intel, run_date=date_str)

        if db_path:
            history_repo = HistoryRepo(db_path)
            if trend_mode:
                final_intel = classify_trends(final_intel, history_repo=history_repo, run_date=date_str)

    metrics = build_quality_metrics(raw_intel, final_intel, collector_meta=collector_meta)

    body = generate_report(
        final_intel,
        date_str,
        event_mode=event_mode,
        metrics=metrics,
    )
    final_content = f"# {report_title}\n\n" + body.replace(
        "# 🌍 国际时事日报 (World Affairs Daily Briefing)", ""
    )

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(final_content)

    if event_mode and history_repo:
        history_repo.save_day_snapshot(date_str, final_intel, metrics)

    logger.info("简报已生成: %s", report_file)


def main():
    parser = argparse.ArgumentParser(description="生成国际时事情报简报")
    parser.add_argument("days", nargs="?", type=int, default=1, help="分析天数 (默认: 1)")
    parser.add_argument("--db-path", type=str, default=DEFAULT_DB_PATH, help="SQLite state DB path")
    parser.add_argument("--no-event-mode", action="store_true", help="Disable event clustering mode")
    parser.add_argument("--no-trend", action="store_true", help="Disable history trend classification")
    args = parser.parse_args()

    generate_morning_report(
        days=args.days,
        db_path=args.db_path,
        event_mode=not args.no_event_mode,
        trend_mode=not args.no_trend,
    )


if __name__ == "__main__":
    main()
