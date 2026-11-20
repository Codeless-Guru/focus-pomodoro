"""Tkinter 界面绘制工具。"""

from __future__ import annotations

import tkinter as tk


def blend_color(start: str, end: str, ratio: float) -> str:
    """在两个 #RRGGBB 颜色之间插值。"""
    value = min(1.0, max(0.0, ratio))
    left = start.lstrip("#")
    right = end.lstrip("#")
    channels = []
    for offset in (0, 2, 4):
        first = int(left[offset : offset + 2], 16)
        second = int(right[offset : offset + 2], 16)
        mixed = round(first + (second - first) * value)
        channels.append(f"{mixed:02X}")
    return "#" + "".join(channels)


def draw_gradient(
    canvas: tk.Canvas,
    x: int,
    y: int,
    width: int,
    height: int,
    start: str,
    end: str,
    steps: int = 32,
) -> None:
    """用竖向矩形模拟横向渐变背景。"""
    step_width = max(1, width // steps)
    for index in range(steps):
        left = x + index * step_width
        right = min(x + width, left + step_width + 1)
        color = blend_color(start, end, index / max(1, steps - 1))
        canvas.create_rectangle(left, y, right, y + height, fill=color, outline="")


def draw_round_rect(
    canvas: tk.Canvas,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    radius: int,
    fill: str,
    outline: str = "",
    width: int = 1,
) -> int:
    """用多边形和圆弧绘制圆角矩形。"""
    points = [
        x1 + radius,
        y1,
        x2 - radius,
        y1,
        x2,
        y1,
        x2,
        y1 + radius,
        x2,
        y2 - radius,
        x2,
        y2,
        x2 - radius,
        y2,
        x1 + radius,
        y2,
        x1,
        y2,
        x1,
        y2 - radius,
        x1,
        y1 + radius,
        x1,
        y1,
    ]
    item = canvas.create_polygon(points, smooth=True, fill=fill, outline=outline, width=width)
    return item
