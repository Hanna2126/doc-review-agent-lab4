from pathlib import Path

import pytest

from cli import run_pipeline


@pytest.fixture()
def sample_docs(tmp_path):
    folder = tmp_path / "docs"
    folder.mkdir()
    (folder / "a.txt").write_text(
        "文档审查需要先做文本清洗，再进行分词。" * 6, encoding="utf-8"
    )
    (folder / "b.md").write_text(
        "# 词云\n\n词云需要指定中文字体，否则会显示方框。\n\n停用词表决定关键词质量。" * 4,
        encoding="utf-8",
    )
    return folder


def test_pipeline_generates_all_outputs(sample_docs, tmp_path):
    output = tmp_path / "out"
    summary = run_pipeline(sample_docs, output, top_n=50, use_llm=False)
    assert summary["documents"] == 2
    for key in ("image", "csv", "summary", "review"):
        assert Path(summary[key]).exists()
    assert Path(summary["image"]).stat().st_size > 10_000
    assert summary["montecarlo"]["trials"] > 0


def test_pipeline_rejects_missing_folder(tmp_path):
    with pytest.raises(FileNotFoundError):
        run_pipeline(tmp_path / "missing", tmp_path / "out", use_llm=False)
