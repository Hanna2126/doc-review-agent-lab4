import json
from pathlib import Path

import pytest

from src.analyzer import AnalysisResult, DocInsight
from src.llm import ReviewResult, build_prompt, generate_review, offline_review


@pytest.fixture()
def result():
    return AnalysisResult(
        total_docs=2,
        total_chars=600,
        total_tokens=120,
        word_counts={},
        top_words=[("文档审查", 12), ("词云", 9), ("分词", 7)],
        insights=[
            DocInsight(
                title="草稿",
                char_count=120,
                paragraph_count=2,
                token_count=30,
                keywords=[("文档审查", 8)],
                summary="摘要一。",
                review_flags=[("篇幅偏短（120 字，建议不少于 200 字）", 15), ("结构单薄（仅 2 段）", 10)],
            ),
            DocInsight(
                title="规范文档",
                char_count=480,
                paragraph_count=4,
                token_count=90,
                keywords=[("词云", 5)],
                summary="摘要二。",
                review_flags=[("未发现明显问题", 0)],
            ),
        ],
    )


def test_offline_review_contains_sections(result):
    content = offline_review(result)
    for section in ("【整体结论】", "【主要问题】", "【修改建议】", "【总体摘要】"):
        assert section in content
    assert "草稿" in content


def test_generate_review_defaults_to_offline(result, monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    review = generate_review(result)
    assert review.mode == "offline"
    assert isinstance(review, ReviewResult)


def test_prompt_contains_keywords_and_quality(result):
    prompt = build_prompt(result)
    assert "文档审查(12)" in prompt or "文档审查" in prompt
    assert "草稿" in prompt
    assert "JSON" not in prompt


def test_api_failure_falls_back_to_offline(result, monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "fake-key")
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:9")
    review = generate_review(result, prefer_api=True)
    assert review.mode.startswith("offline")
    assert "【整体结论】" in review.content
