"""桌面番茄钟启动入口。

直接运行本文件时创建 Tk 根窗口，装配主界面并进入事件循环。
"""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path

# 直接执行 main.py 时，Python 不会自动把当前目录视为包根目录。
# 这里补上项目根目录，保证 `from pomodoro.app import ...` 可用。
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from pomodoro.app import PomodoroApp


def main() -> None:
    """创建主窗口并启动 Tk 事件循环。"""
    root = tk.Tk()
    PomodoroApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
