# -*- coding: utf-8 -*-
"""汇总报告输出：CSV（逐文件审查表）与 TXT（整批摘要）。"""
from __future__ import annotations

import csv
from pathlib import Path

from .analyzer import AnalysisResult

CSV_HEADER = ["文件名", "字数", "段落数", "词次", "关键词", "审查评分", "审查结论", "审查意见"]


def write_csv(result: AnalysisResult, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(CSV_HEADER)
        for insight in result.insights:
            keywords = "、".join(f"{word}({count})" for word, count in insight.keywords)
            opinions = "；".join(text for text, _ in insight.review_flags)
            writer.writerow([
                insight.title,
                insight.char_count,
                insight.paragraph_count,
                insight.token_count,
                keywords,
                insight.score,
                insight.verdict,
                opinions,
            ])
    return output_path


def write_summary(result: AnalysisResult, output_path: Path, top_words: int = 10) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "本地文档智能审查与摘要报告",
        "=" * 36,
        f"文档数量：{result.total_docs}",
        f"总字数：{result.total_chars}",
        f"有效词次：{result.total_tokens}",
        f"平均审查评分：{result.average_score}",
        "",
        f"全库高频词 Top {min(top_words, len(result.top_words))}：",
    ]
    for rank, (word, count) in enumerate(result.top_words[:top_words], start=1):
        lines.append(f"  {rank:>2}. {word}（{count} 次）")
    lines.append("")
    lines.append("逐篇摘要与审查：")
    for index, insight in enumerate(result.insights, start=1):
        lines.append("")
        lines.append(f"[{index}] {insight.title}（{insight.char_count} 字 / {insight.paragraph_count} 段）")
        lines.append(f"    关键词：{'、'.join(word for word, _ in insight.keywords)}")
        lines.append(f"    摘要：{insight.summary}")
        lines.append(f"    评分：{insight.score}（{insight.verdict}）")
        for text, _ in insight.review_flags:
            lines.append(f"    - {text}")
    if result.errors:
        lines.append("")
        lines.append("读取异常：")
        lines.extend(f"  - {error}" for error in result.errors)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path
