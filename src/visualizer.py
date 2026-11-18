# -*- coding: utf-8 -*-
"""词云生成。"""
from __future__ import annotations

from pathlib import Path

from wordcloud import WordCloud


def build_wordcloud(
    frequencies: dict[str, int],
    font_path: str,
    width: int = 1000,
    height: int = 800,
    max_words: int = 50,
    background_color: str = "white",
    colormap: str = "viridis",
) -> WordCloud:
    """按词频字典构建词云对象，方便测试时检查配置。"""
    if not frequencies:
        raise ValueError("词频为空，无法生成词云")
    cloud = WordCloud(
        font_path=font_path,
        width=width,
        height=height,
        background_color=background_color,
        max_words=max_words,
        collocations=False,
        colormap=colormap,
        prefer_horizontal=0.9,
        margin=6,
    )
    cloud.generate_from_frequencies(frequencies)
    return cloud


def save_wordcloud(cloud: WordCloud, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cloud.to_file(str(output_path))
    return output_path
