#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Report Generator - 国际时事日报报告生成模块
"""

import concurrent.futures
import logging
from datetime import datetime
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

try:
    from utils.gemini_translator import (
        TRANSLATION_MAX_WORKERS,
        summarize_section,
        translate_to_chinese,
    )
    from config import LLM_TRANSLATE
    GEMINI_AVAILABLE = True
except ImportError:
    try:
        from src.utils.gemini_translator import (
            TRANSLATION_MAX_WORKERS,
            summarize_section,
            translate_to_chinese,
        )
        from src.config import LLM_TRANSLATE
        GEMINI_AVAILABLE = True
    except ImportError:
        GEMINI_AVAILABLE = False
        LLM_TRANSLATE = False
        TRANSLATION_MAX_WORKERS = 4

if not GEMINI_AVAILABLE:
    logger.info("Gemini translator not available, using original text.")

    def translate_to_chinese(text, max_chars=100):
        return text[:max_chars] + "..." if len(text) > max_chars else text

    def summarize_section(titles_and_summaries, section_name):
        return ""


TRANSLATION_ENABLED = bool(GEMINI_AVAILABLE and LLM_TRANSLATE)


def _translate_all(items_by_section: dict) -> Tuple[Dict, Dict[str, int]]:
    """并行翻译所有英文条目的标题和摘要，返回翻译结果和统计信息。"""
    if not TRANSLATION_ENABLED:
        return {}, {"total": 0, "success": 0}

    tasks = {}  # key -> (text, max_chars)
    for section, items in items_by_section.items():
        for i, item in enumerate(items):
            if item.get("lang") == "zh":
                continue
            tasks[(section, i, "title")] = (item.get("title", ""), 100)
            tasks[(section, i, "summary")] = (item.get("summary", ""), 500)

    if not tasks:
        return {}, {"total": 0, "success": 0}

    results = {}
    success = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=TRANSLATION_MAX_WORKERS) as executor:
        futures = {
            executor.submit(translate_to_chinese, text, max_chars): (key, text)
            for key, (text, max_chars) in tasks.items()
            if text
        }
        for future in concurrent.futures.as_completed(futures):
            key, original = futures[future]
            try:
                translated = future.result() or ""
                results[key] = translated if translated else original
                if translated and translated.strip() and translated.strip() != original.strip():
                    success += 1
            except Exception as e:
                logger.warning(f"Translation failed for {key}: {e}")
                results[key] = original

    return results, {"total": len(futures), "success": success}


_SECTION_NAMES = {
    "politics": "国际政治与外交",
    "economics": "经济与金融",
    "military": "军事与安全",
    "society": "社会与人文",
    "asia": "亚洲焦点",
    "analysis": "深度分析",
}


def _summarize_sections(section_meta: list) -> dict:
    """并行生成各板块总结，返回 {section_key: summary_str}"""

    def _build_input(items):
        texts = []
        for item in items:
            title = item.get("title", "")
            summary = item.get("summary", "")
            texts.append(f"{title}. {summary[:100]}" if summary else title)
        return texts

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(
                summarize_section,
                _build_input(items),
                _SECTION_NAMES.get(key, key),
            ): key
            for key, items, _ in section_meta
            if items
        }
        for future in concurrent.futures.as_completed(futures):
            key = futures[future]
            try:
                results[key] = future.result()
            except Exception as e:
                logger.warning(f"Section summary failed for {key}: {e}")
    return results


def _render_summary_card(metrics: dict, date_str: str) -> List[str]:
    section_counts = metrics.get("section_counts", {})
    trend_counts = metrics.get("trend_counts", {})
    translation_rate = metrics.get("translation_rate", 0)

    lines: List[str] = [
        "> 📅 {date} | 采集 {raw} 条 → 去重 {dedup} 条 → 事件 {events} 个 | 翻译成功率 {rate}%".format(
            date=date_str,
            raw=metrics.get("total_raw", 0),
            dedup=metrics.get("total_dedup", 0),
            events=metrics.get("total_events", 0),
            rate=translation_rate,
        ),
        "> 📊 板块：政治 {politics} · 经济 {economics} · 军事 {military} · 社会 {society} · 亚洲 {asia} · 分析 {analysis}".format(
            politics=section_counts.get("politics", 0),
            economics=section_counts.get("economics", 0),
            military=section_counts.get("military", 0),
            society=section_counts.get("society", 0),
            asia=section_counts.get("asia", 0),
            analysis=section_counts.get("analysis", 0),
        ),
        "> 🏷️ 趋势：🆕 {new} · 🔥 {heating} · ⬇️ {cooling} · ➡️ {steady} · 🚨 {spike}".format(
            new=trend_counts.get("new", 0),
            heating=trend_counts.get("heating", 0),
            cooling=trend_counts.get("cooling", 0),
            steady=trend_counts.get("steady", 0),
            spike=trend_counts.get("spike", 0),
        ),
        "",
    ]
    return lines


def _render_section(items, limit, translations, section_key, section_summary="", event_mode=False):
    lines = []
    if not items:
        lines.append("*暂无数据*\n")
        return lines

    if section_summary:
        summary_oneline = " ".join(section_summary.split())
        lines.append(f"> 📊 **板块速览：** {summary_oneline}")
        lines.append("")

    for i, item in enumerate(items[:limit], 1):
        title = item.get("title", "Untitled")
        url = item.get("url", "#")
        source = item.get("source", "")
        pub_date = item.get("pub_date", "")
        summary = item.get("summary", "")
        lang = item.get("lang", "en")

        if lang == "zh":
            display_title = title
            display_summary = summary
        else:
            display_title = translations.get((section_key, i - 1, "title"), title)
            display_summary = translations.get((section_key, i - 1, "summary"), summary)

        lines.append(f"### {i}. [{display_title}]({url})")
        if lang != "zh" and TRANSLATION_ENABLED:
            lines.append(f"*{title}*")
            lines.append("")

        meta = f"📰 {source}" if source else "📰 未知来源"
        if pub_date:
            meta += f" | 📅 {pub_date}"

        if event_mode:
            source_count = item.get("source_count", 1)
            mention_count = item.get("mention_count", 1)
            trend = item.get("trend", "")
            meta += f" | 🔁 {source_count}源/{mention_count}条"
            if trend:
                meta += f" | {trend}"

        lines.append(meta)

        if display_summary:
            lines.append(f"> {' '.join(display_summary.split())}")
        lines.append("")

    return lines


def generate_report(
    intel: dict,
    date_str: str,
    event_mode: bool = False,
    metrics: dict | None = None,
) -> str:
    """Generate international news briefing in Markdown."""
    sections = [
        ("politics", "🏛️ 国际政治与外交 (International Politics & Diplomacy)", 10),
        ("economics", "💹 经济与金融 (Economics & Markets)", 8),
        ("military", "⚔️ 军事与安全 (Military & Security)", 8),
        ("society", "🌱 社会与人文 (Society & Humanitarian)", 8),
        ("asia", "🌏 亚洲焦点 (Asia Focus)", 10),
        ("analysis", "📖 深度分析 (Analysis & Opinion)", 5),
    ]

    items_by_section = {key: intel.get(key, [])[:limit] for key, _, limit in sections}

    translations, translation_stats = _translate_all(items_by_section)

    if metrics is not None:
        metrics["translation_total"] = int(translation_stats["total"])
        metrics["translation_success"] = int(translation_stats["success"])
        if translation_stats["total"] > 0:
            metrics["translation_rate"] = round(
                translation_stats["success"] / translation_stats["total"] * 100,
                2,
            )
        else:
            metrics["translation_rate"] = 0.0

    section_summaries = _summarize_sections(
        [(key, items_by_section[key], limit) for key, _, limit in sections]
    )

    lines = [
        "# 🌍 国际时事日报 (World Affairs Daily Briefing)",
        f"**日期:** {date_str}",
        f"**生成时间:** {datetime.now().strftime('%H:%M')}",
        "**数据源:** BBC · Reuters · AP · SCMP · Guardian · FT · NHK · Yonhap · Al Jazeera · VOA中文 · RFI中文 · BBC中文",
        "",
        "---",
        "",
    ]

    if metrics:
        lines.extend(_render_summary_card(metrics, date_str))

    for key, heading, limit in sections:
        lines.append(f"## {heading}")
        lines.append("")
        lines.extend(
            _render_section(
                items_by_section[key],
                limit,
                translations,
                key,
                section_summaries.get(key, ""),
                event_mode=event_mode,
            )
        )

    return "\n".join(lines)


__all__ = ["generate_report"]
