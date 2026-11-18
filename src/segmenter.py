# -*- coding: utf-8 -*-
"""jieba 分词、停用词与自定义词典加载。"""
from __future__ import annotations

import re
from pathlib import Path

import jieba

PUNCT_ONLY = re.compile(r"^[\W_]+$", re.UNICODE)
MARKDOWN_NOISE = re.compile(r"[#*`>|]")

DEFAULT_STOPWORDS = {
    "的", "了", "和", "在", "是", "我", "你", "他", "她", "它", "我们", "你们",
    "他们", "为", "以", "等", "并", "对", "与", "也", "就", "都", "而", "及",
    "或", "被", "把", "让", "从", "到", "中", "上", "下", "里", "这", "那",
    "一个", "没有", "可以", "进行", "通过", "需要", "如果", "因为", "所以",
    "但是", "然后", "已经", "还是", "这个", "那个", "不是", "就是",
}


class Segmenter:
    """封装 jieba 的加载与分词逻辑，便于测试时注入自定义词典。"""

    def __init__(self, stopwords_file: Path | None = None, user_dict: Path | None = None):
        self.stopwords = set(DEFAULT_STOPWORDS)
        self.loaded_dict = False
        if stopwords_file and Path(stopwords_file).exists():
            self.stopwords |= self._load_word_file(stopwords_file)
        if user_dict and Path(user_dict).exists():
            jieba.load_userdict(str(user_dict))
            self.loaded_dict = True

    @staticmethod
    def _load_word_file(path: Path) -> set[str]:
        """每行一个词，忽略空行与 # 注释。"""
        words: set[str] = set()
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            word = line.strip()
            if word and not word.startswith("#"):
                words.add(word)
        return words

    def cut(self, text: str) -> list[str]:
        """精确模式分词，并完成清洗、停用词与单字过滤。"""
        cleaned = MARKDOWN_NOISE.sub(" ", text)
        tokens = jieba.lcut(cleaned)
        result: list[str] = []
        for token in tokens:
            word = token.strip()
            if len(word) < 2:
                continue
            if PUNCT_ONLY.match(word) or word.isdigit():
                continue
            if word.lower() in self.stopwords or word in self.stopwords:
                continue
            result.append(word)
        return result

    def describe(self) -> str:
        return f"停用词 {len(self.stopwords)} 个，自定义词典{'已加载' if self.loaded_dict else '未加载'}"
