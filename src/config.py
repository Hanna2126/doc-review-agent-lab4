# -*- coding: utf-8 -*-
"""路径与字体等基础配置。"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
CONFIG_DIR = ROOT / "config"
OUTPUT_DIR = ROOT / "output"

STOPWORDS_FILE = CONFIG_DIR / "stopwords.txt"
USER_DICT_FILE = CONFIG_DIR / "user_dict.txt"

FONT_CANDIDATES = [
    Path(r"C:\Windows\Fonts\msyh.ttc"),
    Path(r"C:\Windows\Fonts\msyh.ttf"),
    Path(r"C:\Windows\Fonts\simhei.ttf"),
    Path(r"C:\Windows\Fonts\simsun.ttc"),
    Path("/System/Library/Fonts/PingFang.ttc"),
    Path("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"),
]


def resolve_font(explicit: str | None = None) -> str:
    """返回一个可用的中文字体路径；找不到时给出明确错误。"""
    if explicit:
        path = Path(explicit)
        if path.exists():
            return str(path)
        raise FileNotFoundError(f"指定的字体不存在：{explicit}")
    for candidate in FONT_CANDIDATES:
        if candidate.exists():
            return str(candidate)
    raise FileNotFoundError("未找到可用的中文字体，请用 --font 指定 .ttf/.ttc 文件")
