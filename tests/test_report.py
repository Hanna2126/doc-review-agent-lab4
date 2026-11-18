from collections import Counter
from pathlib import Path

from src.analyzer import AnalysisResult, DocInsight
from src.report import write_csv, write_summary


def build_result() -> AnalysisResult:
    insight = DocInsight(
        title="示例文档",
        char_count=320,
        paragraph_count=4,
        token_count=60,
        keywords=[("文档", 5), ("词云", 3)],
        summary="这是一段摘要。",
        review_flags=[("未发现明显问题", 0)],
    )
    return AnalysisResult(
        total_docs=1,
        total_chars=320,
        total_tokens=60,
        word_counts=Counter({"文档": 5, "词云": 3}),
        top_words=[("文档", 5), ("词云", 3)],
        insights=[insight],
    )


def test_csv_contains_header_and_review(tmp_path):
    path = write_csv(build_result(), tmp_path / "review.csv")
    content = path.read_text(encoding="utf-8-sig")
    assert content.splitlines()[0] == "文件名,字数,段落数,词次,关键词,审查评分,审查结论,审查意见"
    assert "示例文档" in content
    assert "未发现明显问题" in content


def test_summary_contains_top_words_and_per_doc_block(tmp_path):
    path = write_summary(build_result(), tmp_path / "summary.txt")
    content = path.read_text(encoding="utf-8")
    assert "本地文档智能审查与摘要报告" in content
    assert "全库高频词" in content
    assert "[1] 示例文档" in content
    assert "摘要：这是一段摘要。" in content
