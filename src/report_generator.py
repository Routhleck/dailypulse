#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Report Generator - 国际时事日报报告生成模块
"""

import logging
import concurrent.futures
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from utils.gemini_translator import translate_to_chinese, summarize_section
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

if not GEMINI_AVAILABLE:
    logger.info("Gemini translator not available, using original text.")
    def translate_to_chinese(text, max_chars=100):
        return text[:max_chars] + "..." if len(text) > max_chars else text
    def summarize_section(titles_and_summaries, section_name):
        return ""


def _translate_all(items_by_section: dict) -> dict:
    """并行翻译所有英文条目的标题和摘要，返回 {(section, idx): (title_cn, summary_cn)}"""
    tasks = {}  # key -> (text, max_chars)
    for section, items in items_by_section.items():
        for i, item in enumerate(items):
            if item.get("lang") == "zh" or not GEMINI_AVAILABLE:
                continue
            tasks[(section, i, "title")]   = (item.get("title", ""),   100)
            tasks[(section, i, "summary")] = (item.get("summary", ""), 500)

    if not tasks:
        return {}

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(translate_to_chinese, text, max_chars): key
            for key, (text, max_chars) in tasks.items()
            if text
        }
        for future in concurrent.futures.as_completed(futures):
            key = futures[future]
            try:
                results[key] = future.result()
            except Exception as e:
                logger.warning(f"Translation failed for {key}: {e}")
                results[key] = tasks[key][0]  # fallback to original

    return results


_SECTION_NAMES = {
    "politics": "国际政治与外交", "economics": "经济与金融",
    "military": "军事与安全", "society": "社会与人文",
    "asia": "亚洲焦点", "analysis": "深度分析",
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
                _SECTION_NAMES.get(key, key)
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


def _render_section(items, limit, translations, section_key, section_summary=""):
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
        if lang == "en" and display_title != title:
            lines.append(f"*{title}*")
        meta = f"📰 {source}"
        if pub_date:
            meta += f" | 📅 {pub_date}"
        lines.append(meta)
        if display_summary:
            lines.append(f"> {display_summary}")
        lines.append("")

    return lines


def generate_report(intel: dict, date_str: str) -> str:
    """Generate international news daily briefing in Markdown."""
    sections = [
        ("politics",  "🏛️ 国际政治与外交 (International Politics & Diplomacy)", 10),
        ("economics", "💹 经济与金融 (Economics & Markets)",                     8),
        ("military",  "⚔️ 军事与安全 (Military & Security)",                    8),
        ("society",   "🌱 社会与人文 (Society & Humanitarian)",                  8),
        ("asia",      "🌏 亚洲焦点 (Asia Focus)",                               10),
        ("analysis",  "📖 深度分析 (Analysis & Opinion)",                        5),
    ]

    # 收集每个 section 实际要渲染的条目
    items_by_section = {
        key: intel.get(key, [])[:limit]
        for key, _, limit in sections
    }

    # 并行翻译
    translations = _translate_all(items_by_section)

    # 并行生成板块总结
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

    for key, heading, limit in sections:
        lines.append(f"## {heading}")
        lines.append("")
        lines.extend(_render_section(items_by_section[key], limit, translations, key, section_summaries.get(key, "")))

    lines.append("---")
    lines.append("*报告由 DailyPulse 自动生成*")

    return "\n".join(lines)


__all__ = ['generate_report']
