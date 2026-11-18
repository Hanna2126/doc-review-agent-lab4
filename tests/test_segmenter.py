from pathlib import Path

from src.segmenter import Segmenter

CONFIG = Path(__file__).resolve().parents[1] / "config"


def test_filters_single_char_stopwords_and_digits():
    segmenter = Segmenter(CONFIG / "stopwords.txt", CONFIG / "user_dict.txt")
    tokens = segmenter.cut("我们 的 文档 2024 年 有 3 个 段落，需要 进行 文本清洗。")
    assert "的" not in tokens
    assert "2024" not in tokens
    assert "3" not in tokens
    assert "文本清洗" in tokens


def test_user_dict_keeps_professional_phrase():
    segmenter = Segmenter(CONFIG / "stopwords.txt", CONFIG / "user_dict.txt")
    tokens = segmenter.cut("文档审查需要先做词频统计，再生成词云。")
    assert "文档审查" in tokens
    assert "词频统计" in tokens
    assert "词云" in tokens


def test_markdown_markers_are_stripped():
    segmenter = Segmenter(CONFIG / "stopwords.txt", CONFIG / "user_dict.txt")
    tokens = segmenter.cut("# 标题\n\n**关键词**：`分词`")
    assert all(not token.startswith("#") for token in tokens)
    assert "分词" in tokens


def test_describe_reports_stopword_size():
    segmenter = Segmenter(CONFIG / "stopwords.txt", CONFIG / "user_dict.txt")
    assert "停用词" in segmenter.describe()
    assert len(segmenter.stopwords) > 100
