# -*- coding: utf-8 -*-
"""在终端以对齐表格展示 review_report.csv，便于截图与人工核对。"""
from __future__ import annotations

import csv
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "output" / "review_report.csv"


def display_width(text: str) -> int:
    return sum(2 if unicodedata.east_asian_width(char) in "WF" else 1 for char in text)


def pad(text: str, width: int) -> str:
    return text + " " * max(0, width - display_width(text))


def main() -> int:
    if not CSV_PATH.exists():
        print(f"找不到 {CSV_PATH}，请先运行 cli.py")
        return 1
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    columns = [("文件名", 40), ("字数", 6), ("段", 4), ("词次", 6), ("评分", 6), ("结论", 10), ("主要问题", 50)]
    print("逐篇审查结果（review_report.csv）")
    print("-" * 124)
    print("".join(pad(name, width) for name, width in columns))
    print("-" * 124)
    for row in rows:
        opinion = row["审查意见"].split("；")[0]
        if len(opinion) > 22:
            opinion = opinion[:22] + "…"
        values = [
            row["文件名"], row["字数"], row["段落数"], row["词次"], row["审查评分"], row["审查结论"], opinion
        ]
        print("".join(pad(str(value), width) for value, (_, width) in zip(values, columns)))
    print("-" * 124)
    average = sum(int(row["审查评分"]) for row in rows) / max(1, len(rows))
    print(f"共 {len(rows)} 篇，平均评分 {average:.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
