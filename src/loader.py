# -*- coding: utf-8 -*-
"""批量读取本地文档，兼容 UTF-8 / GBK 等常见编码。"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

SUPPORTED_SUFFIXES = {".txt", ".md"}
ENCODINGS = ("utf-8", "utf-8-sig", "gbk", "gb18030")


@dataclass
class Document:
    """一篇文档的元信息与正文。"""

    path: Path
    title: str
    text: str
    encoding: str
    paragraphs: list[str] = field(default_factory=list)
    error: str | None = None

    @property
    def char_count(self) -> int:
        return len(self.text)

    @property
    def paragraph_count(self) -> int:
        return len(self.paragraphs)


def _read_text(path: Path) -> tuple[str, str]:
    """按候选编码依次尝试，返回 (正文, 实际编码)。"""
    last_error: Exception | None = None
    for encoding in ENCODINGS:
        try:
            return path.read_text(encoding=encoding), encoding
        except UnicodeDecodeError as exc:
            last_error = exc
    raise UnicodeDecodeError("utf-8", b"", 0, 1, f"无法解码 {path.name}：{last_error}")


def split_paragraphs(text: str) -> list[str]:
    """按空行切段，去掉首尾空白与空段。"""
    blocks = [block.strip() for block in text.replace("\r\n", "\n").split("\n\n")]
    return [block for block in blocks if block]


def load_documents(folder: Path) -> tuple[list[Document], list[str]]:
    """读取文件夹下的 .txt/.md，返回 (文档列表, 错误信息列表)。"""
    if not folder.exists():
        raise FileNotFoundError(f"输入目录不存在：{folder}")
    if not folder.is_dir():
        raise NotADirectoryError(f"输入路径不是文件夹：{folder}")

    documents: list[Document] = []
    errors: list[str] = []
    for path in sorted(folder.iterdir()):
        if path.suffix.lower() not in SUPPORTED_SUFFIXES or not path.is_file():
            continue
        try:
            text, encoding = _read_text(path)
        except UnicodeDecodeError as exc:
            errors.append(f"{path.name}: {exc}")
            continue
        if not text.strip():
            errors.append(f"{path.name}: 文件为空，已跳过")
            continue
        documents.append(
            Document(
                path=path,
                title=path.stem,
                text=text,
                encoding=encoding,
                paragraphs=split_paragraphs(text),
            )
        )
    return documents, errors
