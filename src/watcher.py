# -*- coding: utf-8 -*-
"""进阶三：用 watchdog 监控文档目录，新文件落地后自动触发分析。"""
from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

SUPPORTED = {".txt", ".md"}


class _Handler(FileSystemEventHandler):
    def __init__(self, callback: Callable[[Path], None], debounce: float = 1.0):
        super().__init__()
        self.callback = callback
        self.debounce = debounce
        self._timers: dict[str, threading.Timer] = {}

    def _schedule(self, path: Path) -> None:
        if path.suffix.lower() not in SUPPORTED or path.name.startswith("~$"):
            return
        key = str(path)
        old = self._timers.pop(key, None)
        if old:
            old.cancel()
        timer = threading.Timer(self.debounce, self._fire, args=(path,))
        timer.daemon = True
        self._timers[key] = timer
        timer.start()

    def _fire(self, path: Path) -> None:
        self._timers.pop(str(path), None)
        if path.exists():
            self.callback(path)

    def on_created(self, event) -> None:
        if not event.is_directory:
            self._schedule(Path(event.src_path))

    def on_modified(self, event) -> None:
        if not event.is_directory:
            self._schedule(Path(event.src_path))


def watch_folder(folder: Path, callback: Callable[[Path], None], debounce: float = 1.0) -> None:
    """阻塞式监控目录，Ctrl+C 结束。"""
    observer = Observer()
    observer.schedule(_Handler(callback, debounce), str(folder), recursive=False)
    observer.start()
    print(f"[watch] 正在监控 {folder}，把新的 .txt/.md 放进去即可触发；Ctrl+C 退出。")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[watch] 已停止监控。")
    finally:
        observer.stop()
        observer.join()
