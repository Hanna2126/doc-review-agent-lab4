import pytest

from src.loader import load_documents, split_paragraphs


def test_split_paragraphs_ignores_blank_blocks():
    assert split_paragraphs("第一段\n\n\n第二段\n") == ["第一段", "第二段"]


def test_loads_utf8_and_gbk(tmp_path):
    (tmp_path / "utf8.txt").write_text("中文内容一", encoding="utf-8")
    (tmp_path / "gbk.txt").write_text("中文内容二", encoding="gbk")
    docs, errors = load_documents(tmp_path)
    assert [doc.path.name for doc in docs] == ["gbk.txt", "utf8.txt"]
    assert docs[1].encoding == "utf-8"
    assert docs[0].encoding in {"gbk", "gb18030"}
    assert errors == []


def test_empty_and_unsupported_files_are_skipped(tmp_path):
    (tmp_path / "empty.txt").write_text("   ", encoding="utf-8")
    (tmp_path / "image.png").write_bytes(b"not a document")
    (tmp_path / "ok.md").write_text("# 标题\n\n正文内容", encoding="utf-8")
    docs, errors = load_documents(tmp_path)
    assert len(docs) == 1
    assert docs[0].paragraph_count == 2
    assert any("文件为空" in error for error in errors)


def test_missing_folder_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_documents(tmp_path / "not-exist")


def test_file_path_not_folder_raises(tmp_path):
    target = tmp_path / "a.txt"
    target.write_text("x", encoding="utf-8")
    with pytest.raises(NotADirectoryError):
        load_documents(target)
