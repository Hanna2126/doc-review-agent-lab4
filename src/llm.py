# -*- coding: utf-8 -*-
"""进阶二：把词频与审查结果交给大模型生成审查意见。

默认走离线模板，保证无网络、无密钥也能跑通；配置环境变量后可切换为
OpenAI 兼容接口（任何实现 /chat/completions 的服务均可）。
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass

from .analyzer import AnalysisResult


@dataclass
class ReviewResult:
    mode: str
    content: str
    model: str = "offline-template"


def build_prompt(result: AnalysisResult, max_docs: int = 5) -> str:
    lines = [
        "你是一名文档质量审阅助手。请基于以下统计结果，输出结构化的审查意见：",
        "1) 整体质量结论；2) 主要问题（按严重程度排序）；3) 可执行的修改建议；4) 一段 100 字以内的总体摘要。",
        "",
        f"文档数量：{result.total_docs}，总字数：{result.total_chars}，平均评分：{result.average_score}",
        f"高频词：{'、'.join(f'{w}({c})' for w, c in result.top_words[:20])}",
    ]
    for insight in result.insights[:max_docs]:
        flags = "；".join(text for text, _ in insight.review_flags)
        lines.append(
            f"- 《{insight.title}》：{insight.char_count} 字，评分 {insight.score}（{insight.verdict}），"
            f"关键词 {'、'.join(w for w, _ in insight.keywords)}，问题：{flags}"
        )
    return "\n".join(lines)


def offline_review(result: AnalysisResult) -> str:
    """不依赖大模型的规则化审查意见，作为默认实现与兜底。"""
    weak = [item for item in result.insights if item.score < 85]
    weak_names = "、".join(item.title for item in weak) or "无"
    issues: list[str] = []
    for insight in weak:
        for text, _ in insight.review_flags:
            if text != "未发现明显问题":
                issues.append(f"《{insight.title}》：{text}")
    top_keywords = "、".join(word for word, _ in result.top_words[:8])
    issue_block = "\n".join(f"{i}. {text}" for i, text in enumerate(issues[:6], 1)) or "1. 未发现明显问题。"
    return (
        "【整体结论】\n"
        f"本批共 {result.total_docs} 篇文档，平均审查评分 {result.average_score}；"
        f"低于 85 分的文档：{weak_names}。\n\n"
        "【主要问题】\n"
        f"{issue_block}\n\n"
        "【修改建议】\n"
        "1. 对篇幅偏短的文档补充背景、过程与结论三段式内容；\n"
        "2. 对用词集中的文档做同义替换，并在小节内拆分层级；\n"
        "3. 清理“待补充/TODO”等占位标记后再提交评审。\n\n"
        f"【总体摘要】\n本批文档围绕 {top_keywords} 展开，整体结构可用，"
        f"但 {len(weak)} 篇在完整性与表达多样性上仍需打磨。"
    )


def call_openai_compatible(prompt: str, timeout: float = 30.0) -> ReviewResult:
    """调用 OpenAI 兼容接口；失败时抛出异常，由上层回退到离线模板。"""
    base_url = os.environ.get("LLM_BASE_URL", "").rstrip("/")
    api_key = os.environ.get("LLM_API_KEY", "")
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
    if not base_url or not api_key:
        raise RuntimeError("未配置 LLM_BASE_URL / LLM_API_KEY")
    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": "你是严谨的中文文档审阅助手，只输出结构化审查意见。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    content = data["choices"][0]["message"]["content"].strip()
    return ReviewResult(mode="api", content=content, model=model)


def generate_review(result: AnalysisResult, prefer_api: bool = True) -> ReviewResult:
    """优先调用大模型，任何失败都回退到离线模板，保证流程不中断。"""
    if prefer_api and os.environ.get("LLM_API_KEY") and os.environ.get("LLM_BASE_URL"):
        try:
            return call_openai_compatible(build_prompt(result))
        except (urllib.error.URLError, RuntimeError, KeyError, json.JSONDecodeError, TimeoutError) as exc:
            return ReviewResult(mode=f"offline（API 失败：{exc}）", content=offline_review(result))
    return ReviewResult(mode="offline", content=offline_review(result))
