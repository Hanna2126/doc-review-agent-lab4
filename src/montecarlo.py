# -*- coding: utf-8 -*-
"""进阶一：用蒙特卡洛模拟估计“新文档对核心关键词的覆盖程度”。"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np


@dataclass
class MonteCarloResult:
    trials: int
    keyword_count: int
    doc_token_length: int
    threshold: float
    mean_coverage: float
    std_coverage: float
    p05: float
    p95: float
    pass_probability: float

    def to_dict(self) -> dict:
        return asdict(self)


def simulate_keyword_coverage(
    top_words: list[tuple[str, int]],
    total_tokens: int,
    doc_token_length: int,
    trials: int = 20000,
    keyword_count: int = 8,
    threshold: float = 0.5,
    seed: int = 20261118,
) -> MonteCarloResult:
    """把每个高频词的出现概率视为 p=freq/total，模拟新文档的关键词覆盖分布。

    单篇文档长度固定为 doc_token_length，每个关键词的出现次数服从二项分布；
    覆盖率定义为“至少出现一次的关键词数 / 关键词总数”。
    """
    if total_tokens <= 0 or not top_words:
        raise ValueError("缺少词频数据，无法进行蒙特卡洛模拟")
    if doc_token_length <= 0:
        raise ValueError("文档长度必须为正数")
    k = min(keyword_count, len(top_words))
    probabilities = np.array([count / total_tokens for _, count in top_words[:k]], dtype=float)
    rng = np.random.default_rng(seed)
    occurrences = rng.binomial(doc_token_length, probabilities, size=(trials, k))
    covered = occurrences >= 1
    coverage = covered.mean(axis=1)
    return MonteCarloResult(
        trials=trials,
        keyword_count=k,
        doc_token_length=doc_token_length,
        threshold=threshold,
        mean_coverage=round(float(coverage.mean()), 4),
        std_coverage=round(float(coverage.std()), 4),
        p05=round(float(np.percentile(coverage, 5)), 4),
        p95=round(float(np.percentile(coverage, 95)), 4),
        pass_probability=round(float((coverage >= threshold).mean()), 4),
    )
