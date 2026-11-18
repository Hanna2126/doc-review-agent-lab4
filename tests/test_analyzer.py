from pathlib import Path

from src.analyzer import DocInsight, analyze_documents, review_document, summarize
from src.loader import Document

CONFIG = Path(__file__).resolve().parents[1] / "config"


def make_doc(text: str, name: str = "demo.txt", paragraphs: int = 4) -> Document:
    return Document(
        path=Path(name),
        title=Path(name).stem,
        text=text,
        encoding="utf-8",
        paragraphs=[f"段落{i}" for i in range(paragraphs)],
    )


def make_insight(char_count: int, paragraphs: int, keywords: list[tuple[str, int]]) -> DocInsight:
    return DocInsight(
        title="demo",
        char_count=char_count,
        paragraph_count=paragraphs,
        token_count=sum(count for _, count in keywords),
        keywords=keywords,
        summary="摘要",
    )


def test_short_document_gets_two_flags():
    doc = make_doc("太短了。", paragraphs=2)
    insight = make_insight(60, 2, [("内容", 3)])
    flags = review_document(doc, insight)
    assert any("篇幅偏短" in text for text, _ in flags)
    assert any("结构单薄" in text for text, _ in flags)


def test_single_marker_mention_is_not_a_flag():
    doc = make_doc("这里只是在解释规则：出现待补充标记才算问题。", paragraphs=3)
    insight = make_insight(400, 4, [("规则", 4)])
    flags = review_document(doc, insight)
    assert all("未完成标记" not in text for text, _ in flags)


def test_repeated_markers_are_flagged():
    doc = make_doc("待补充一段。待补充两段。TODO 截图。", paragraphs=3)
    insight = make_insight(400, 4, [("补充", 4)])
    flags = review_document(doc, insight)
    assert any("未完成标记" in text for text, _ in flags)


def test_concentrated_words_are_flagged():
    doc = make_doc("正常内容", paragraphs=4)
    insight = make_insight(400, 4, [("词云", 20), ("文档", 5)])
    flags = review_document(doc, insight)
    assert any("用词集中" in text for text, _ in flags)


def test_summary_picks_sentences_with_high_frequency_words():
    from collections import Counter

    text = "词云可以展示高频词。今天天气不错。词云需要中文字体，否则会出现方框。"
    summary = summarize(text, Counter({"词云": 3, "字体": 2}), max_sentences=2)
    assert "词云" in summary
    assert summary.endswith("。")


def test_analyze_documents_builds_global_and_per_doc_stats():
    from src.segmenter import Segmenter

    docs = [
        make_doc("文档审查需要词频统计。文档审查还要生成词云。", "a.txt"),
        make_doc("词云需要中文字体。停用词表决定关键词质量。", "b.md"),
    ]
    segmenter = Segmenter(CONFIG / "stopwords.txt", CONFIG / "user_dict.txt")
    result = analyze_documents(docs, segmenter, top_n=10)
    assert result.total_docs == 2
    assert result.total_tokens > 0
    assert len(result.insights) == 2
    assert len(result.top_words) <= 10
    assert result.top_words[0][1] >= result.top_words[-1][1]
