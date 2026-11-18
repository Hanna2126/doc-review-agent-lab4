# -*- coding: utf-8 -*-
"""词频统计、关键词提取、抽取式摘要与文档审查规则。"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

from .loader import Document
from .segmenter import Segmenter

SENTENCE_SPLIT = re.compile(r"[。！？!?\n]+")
RISK_MARKERS = ("待补充", "TODO", "todo", "未完成", "占位", "待定", "存疑")
MIN_CHARS = 200


@dataclass
class DocInsight:
    """单篇文档的分析结果。"""

    title: str
    char_count: int
    paragraph_count: int
    token_count: int
    keywords: list[tuple[str, int]]
    summary: str
    review_flags: list[tuple[str, int]] = field(default_factory=list)

    @property
    def score(self) -> int:
        penalty = sum(item[1] for item in self.review_flags)
        return max(0, 100 - penalty)

    @property
    def verdict(self) -> str:
        if self.score >= 85:
            return "通过"
        if self.score >= 65:
            return "建议修改"
        return "需要重写"


@dataclass
class AnalysisResult:
    """整批文档的分析结果。"""

    total_docs: int
    total_chars: int
    total_tokens: int
    word_counts: Counter
    top_words: list[tuple[str, int]]
    insights: list[DocInsight]
    errors: list[str] = field(default_factory=list)

    @property
    def average_score(self) -> float:
        return round(sum(item.score for item in self.insights) / max(1, len(self.insights)), 1)


def iter_sentences(text: str) -> list[str]:
    parts = [part.strip() for part in SENTENCE_SPLIT.split(text)]
    return [part for part in parts if len(part) >= 6]


def summarize(text: str, word_counts: Counter, max_sentences: int = 3) -> str:
    """按句子内词频权重打分，取前几句做抽取式摘要。"""
    sentences = iter_sentences(text)
    if not sentences:
        return "（无可用于摘要的正文）"
    scored: list[tuple[float, int, str]] = []
    for index, sentence in enumerate(sentences):
        score = 0.0
        for word, count in word_counts.items():
            if word in sentence:
                score += count
        score = score / (len(sentence) ** 0.5 + 1)
        scored.append((score, index, sentence))
    top = sorted(scored, key=lambda item: (-item[0], item[1]))[:max_sentences]
    ordered = sorted(top, key=lambda item: item[1])
    return "；".join(sentence for _, _, sentence in ordered) + "。"


def review_document(doc: Document, insight: DocInsight) -> list[tuple[str, int]]:
    """按可解释的规则给出审查意见，每条意见带扣分。"""
    flags: list[tuple[str, int]] = []
    if insight.char_count < MIN_CHARS:
        flags.append((f"篇幅偏短（{insight.char_count} 字，建议不少于 {MIN_CHARS} 字）", 15))
    if insight.paragraph_count < 3:
        flags.append((f"结构单薄（仅 {insight.paragraph_count} 段）", 10))
    if insight.keywords:
        top_word, top_count = insight.keywords[0]
        share = top_count / max(1, insight.token_count)
        if share > 0.30:
            flags.append((f"用词集中：“{top_word}”占全部词次 {share:.0%}，建议同义替换", 10))
    hits = [marker for marker in RISK_MARKERS if marker in doc.text]
    hit_count = sum(doc.text.count(marker) for marker in RISK_MARKERS)
    # 单次提及可能只是在描述规则，重复出现才视为真正的未完成标记
    if hit_count >= 2:
        flags.append((f"存在未完成标记（{hit_count} 处）：{'、'.join(hits)}", 20))
    if doc.path.suffix.lower() == ".md" and "#" not in doc.text:
        flags.append(("Markdown 文档缺少小标题层级", 5))
    if not flags:
        flags.append(("未发现明显问题", 0))
    return flags


def analyze_documents(documents: list[Document], segmenter: Segmenter, top_n: int = 50) -> AnalysisResult:
    """对整批文档做词频、关键词、摘要与审查。"""
    all_words: list[str] = []
    total_chars = 0
    insights: list[DocInsight] = []

    for doc in documents:
        words = segmenter.cut(doc.text)
        all_words.extend(words)
        total_chars += doc.char_count
        counter = Counter(words)
        insight = DocInsight(
            title=doc.title,
            char_count=doc.char_count,
            paragraph_count=doc.paragraph_count,
            token_count=len(words),
            keywords=counter.most_common(5),
            summary=summarize(doc.text, counter),
        )
        insight.review_flags = review_document(doc, insight)
        insights.append(insight)

    word_counts = Counter(all_words)
    return AnalysisResult(
        total_docs=len(documents),
        total_chars=total_chars,
        total_tokens=len(all_words),
        word_counts=word_counts,
        top_words=word_counts.most_common(top_n),
        insights=insights,
    )
