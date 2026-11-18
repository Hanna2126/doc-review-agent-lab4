# -*- coding: utf-8 -*-
"""watchdog 自动触发演示：启动监控后放入一篇新文档，观察无人值守分析。"""
from __future__ import annotations

import sys
import threading
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=SyntaxWarning)

from watchdog.observers import Observer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import STOPWORDS_FILE, USER_DICT_FILE  # noqa: E402
from src.loader import load_documents  # noqa: E402
from src.segmenter import Segmenter  # noqa: E402
from src.watcher import _Handler  # noqa: E402

DEMO_DIR = ROOT / "output" / "_watch_demo"
done = threading.Event()


def analyze_new_file(path: Path) -> None:
    print(f"\n[自动触发] 检测到新文档：{path.name}")
    docs, errors = load_documents(DEMO_DIR)
    segmenter = Segmenter(STOPWORDS_FILE, USER_DICT_FILE)
    for doc in docs:
        words = segmenter.cut(doc.text)
        top = sorted({word: words.count(word) for word in words}.items(), key=lambda x: -x[1])[:5]
        print(f"  《{doc.title}》 {doc.char_count} 字，{len(words)} 词次")
        print(f"  关键词：{'、'.join(f'{w}({c})' for w, c in top)}")
    if errors:
        print(f"  异常：{errors}")
    done.set()


def main() -> int:
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    for old in DEMO_DIR.glob("*.txt"):
        old.unlink()
    seed = DEMO_DIR / "00-基础说明.txt"
    seed.write_text("这是一篇用于启动监控的示例文档，介绍文档审查流程。" * 3, encoding="utf-8")

    observer = Observer()
    observer.schedule(_Handler(analyze_new_file, debounce=0.5), str(DEMO_DIR), recursive=False)
    observer.start()
    print(f"[watch] 正在监控 {DEMO_DIR}")
    print("[watch] 1 秒后模拟放入新文档，等待自动触发……")

    time.sleep(1.0)
    new_doc = DEMO_DIR / "09-新放入的文档.txt"
    new_doc.write_text(
        "新文档放入目录后，监控器应立即触发分析。\n\n"
        "这篇文档讨论关键词提取、词频统计与词云生成。\n\n"
        "无人值守流程需要在异常时保持运行，并记录每次触发的日志。",
        encoding="utf-8",
    )

    if not done.wait(timeout=10):
        print("[watch] 等待超时，未捕获到事件")
        observer.stop()
        observer.join()
        return 1

    time.sleep(0.5)
    observer.stop()
    observer.join()
    print("\n[watch] 演示结束，监控已停止。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
