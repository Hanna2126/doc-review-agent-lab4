# -*- coding: utf-8 -*-
"""本地文档智能审查与摘要 Agent：一条命令完成读取、分词、词云与审查报告。"""
from __future__ import annotations

import argparse
import json
import time
import warnings
from pathlib import Path

# jieba 0.42.1 在 Python 3.12+ 会触发正则转义的 SyntaxWarning，屏蔽掉以免干扰运行输出
warnings.filterwarnings("ignore", category=SyntaxWarning)

from src.analyzer import analyze_documents
from src.config import DOCS_DIR, OUTPUT_DIR, STOPWORDS_FILE, USER_DICT_FILE, resolve_font
from src.llm import generate_review
from src.loader import load_documents
from src.montecarlo import simulate_keyword_coverage
from src.report import write_csv, write_summary
from src.segmenter import Segmenter
from src.visualizer import build_wordcloud, save_wordcloud
from src.watcher import watch_folder

LINE = "-" * 60


def run_pipeline(
    input_dir: Path,
    output_dir: Path,
    top_n: int = 50,
    font: str | None = None,
    use_llm: bool = True,
) -> dict:
    """执行一次完整分析，返回关键产物路径。"""
    started = time.perf_counter()
    print(LINE)
    print(f"[1/5] 读取文档：{input_dir}")
    documents, errors = load_documents(input_dir)
    if not documents:
        raise RuntimeError("没有读取到可分析的 .txt/.md 文档，请检查目录")
    for doc in documents:
        print(f"  ✓ {doc.path.name:<28} {doc.char_count:>6} 字  {doc.paragraph_count:>3} 段  编码={doc.encoding}")
    for error in errors:
        print(f"  ! {error}")

    print(f"\n[2/5] 加载词典与停用词")
    segmenter = Segmenter(STOPWORDS_FILE, USER_DICT_FILE)
    print(f"  {segmenter.describe()}")

    print(f"\n[3/5] 分词、词频统计与审查")
    result = analyze_documents(documents, segmenter, top_n=top_n)
    result.errors = errors
    for insight in result.insights:
        print(f"  《{insight.title}》 {insight.token_count} 词次 | 评分 {insight.score}（{insight.verdict}）")
        print(f"    关键词：{'、'.join(f'{w}({c})' for w, c in insight.keywords)}")
    print("\n  Top 10 高频词：" + "、".join(f"{word}({count})" for word, count in result.top_words[:10]))

    print(f"\n[4/5] 生成词云与报告")
    font_path = resolve_font(font)
    cloud = build_wordcloud(dict(result.top_words), font_path, max_words=top_n)
    image_path = save_wordcloud(cloud, output_dir / "document_wordcloud.png")
    csv_path = write_csv(result, output_dir / "review_report.csv")
    txt_path = write_summary(result, output_dir / "summary_report.txt")
    print(f"  字体：{font_path}")
    print(f"  词云：{image_path}")
    print(f"  CSV ：{csv_path}")
    print(f"  TXT ：{txt_path}")

    print(f"\n[5/5] 进阶分析：蒙特卡洛 + 审查意见")
    average_length = max(1, result.total_tokens // max(1, result.total_docs))
    mc = simulate_keyword_coverage(result.top_words, result.total_tokens, average_length)
    print(
        f"  蒙特卡洛 {mc.trials} 次：平均覆盖 {mc.mean_coverage:.1%}，"
        f"90% 区间 [{mc.p05:.1%}, {mc.p95:.1%}]，覆盖率≥{mc.threshold:.0%} 的概率 {mc.pass_probability:.1%}"
    )
    mc_path = output_dir / "montecarlo.json"
    mc_path.write_text(json.dumps(mc.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    review = generate_review(result, prefer_api=use_llm)
    review_path = output_dir / "ai_review.txt"
    review_path.write_text(f"模式：{review.mode}\n模型：{review.model}\n\n{review.content}", encoding="utf-8")
    print(f"  审查意见模式：{review.mode}")
    print(f"  审查意见：{review_path}")

    elapsed = time.perf_counter() - started
    print(LINE)
    print(f"完成：{len(documents)} 篇文档，{result.total_tokens} 词次，用时 {elapsed:.2f}s")
    return {
        "documents": len(documents),
        "tokens": result.total_tokens,
        "elapsed": round(elapsed, 2),
        "image": str(image_path),
        "csv": str(csv_path),
        "summary": str(txt_path),
        "review": str(review_path),
        "montecarlo": mc.to_dict(),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="本地文档智能审查与摘要 Agent")
    parser.add_argument("--input", type=Path, default=DOCS_DIR, help="待分析文档目录")
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR, help="产物输出目录")
    parser.add_argument("--top", type=int, default=50, help="词云与高频词数量")
    parser.add_argument("--font", default=None, help="中文字体路径，默认自动探测 msyh.ttc")
    parser.add_argument("--no-llm", action="store_true", help="强制使用离线审查模板")
    parser.add_argument("--watch", action="store_true", help="监控目录，新文档落地后自动重跑")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.watch:
        def on_change(path: Path) -> None:
            print(f"\n[触发] 检测到 {path.name}，重新分析整批文档")
            try:
                run_pipeline(args.input, args.output, args.top, args.font, not args.no_llm)
            except Exception as exc:  # 监控模式不能因单次失败退出
                print(f"[错误] 本次分析失败：{exc}")

        watch_folder(args.input, on_change)
        return 0
    try:
        run_pipeline(args.input, args.output, args.top, args.font, not args.no_llm)
        return 0
    except (FileNotFoundError, NotADirectoryError, RuntimeError, ValueError) as exc:
        print(f"[错误] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
