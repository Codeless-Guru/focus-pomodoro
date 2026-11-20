"""时长自定义弹窗。

提供常用预设和完全自定义两种配置方式，确认后回调主界面保存并应用。
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from .duration_presets import PRESETS, DurationPreset, find_preset
from .timer import TimerConfig

FONT = "Microsoft YaHei UI"
BG = "#0B1220"
CARD = "#111C31"
TEXT = "#F1F5F9"
MUTED = "#94A3B8"
TRACK = "#24314A"
ACCENT = "#38BDF8"

CUSTOM_VALUE = "__custom__"

RANGES = {
    "focus_minutes": (1, 180),
    "short_break_minutes": (1, 60),
    "long_break_minutes": (1, 90),
    "sessions_before_long_break": (2, 12),
}


class DurationDialog(tk.Toplevel):
    """选择预设或填写自定义时长的模态窗口。"""

    def __init__(
        self,
        master: tk.Misc,
        current: TimerConfig,
        on_apply: Callable[[TimerConfig], None],
    ) -> None:
        super().__init__(master)
        self.title("时长自定义")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.transient(master)
        self.on_apply = on_apply
        self.result: TimerConfig | None = None
        self._loading = False

        selected = find_preset(current)
        self.preset_var = tk.StringVar(
            value=selected.name if selected is not None else CUSTOM_VALUE
        )
        self.vars = {
            "focus_minutes": tk.IntVar(value=current.focus_minutes),
            "short_break_minutes": tk.IntVar(value=current.short_break_minutes),
            "long_break_minutes": tk.IntVar(value=current.long_break_minutes),
            "sessions_before_long_break": tk.IntVar(
                value=current.sessions_before_long_break
            ),
        }
        for variable in self.vars.values():
            variable.trace_add("write", self._on_value_changed)

        self._build_styles()
        self._build_ui()
        self._center_on_parent(master)
        self.bind("<Escape>", lambda _event: self.cancel())
        self.grab_set()

    def _build_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Dialog.TCheckbutton", font=(FONT, 9))
        style.configure(
            "Dialog.TButton",
            font=(FONT, 9),
            padding=(10, 7),
        )
        style.configure(
            "Dialog.Primary.TButton",
            background=ACCENT,
            foreground="#06121F",
            font=(FONT, 9, "bold"),
            padding=(10, 7),
        )
        style.configure(
            "TSpinbox",
            fieldbackground=CARD,
            foreground=TEXT,
            insertcolor=TEXT,
            borderwidth=0,
            padding=5,
        )

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        container = ttk.Frame(self, padding=18)
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)

        tk.Label(
            container,
            text="时长自定义",
            bg=BG,
            fg=TEXT,
            font=(FONT, 16, "bold"),
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            container,
            text="选择预设方案，或在下方填写自己的节奏。",
            bg=BG,
            fg=MUTED,
            font=(FONT, 9),
        ).grid(row=1, column=0, sticky="w", pady=(4, 12))

        presets_frame = tk.LabelFrame(
            container,
            text="预设方案",
            bg=BG,
            fg=MUTED,
            font=(FONT, 9),
            padx=10,
            pady=8,
        )
        presets_frame.grid(row=2, column=0, sticky="ew")
        presets_frame.columnconfigure(0, weight=1)
        self._build_presets(presets_frame)

        custom_frame = tk.LabelFrame(
            container,
            text="自定义参数",
            bg=BG,
            fg=MUTED,
            font=(FONT, 9),
            padx=10,
            pady=8,
        )
        custom_frame.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        self._build_custom_fields(custom_frame)

        buttons = ttk.Frame(container)
        buttons.grid(row=4, column=0, sticky="ew", pady=(14, 0))
        ttk.Button(
            buttons,
            text="取消",
            style="Dialog.TButton",
            command=self.cancel,
        ).pack(side="right", padx=(8, 0))
        ttk.Button(
            buttons,
            text="应用方案",
            style="Dialog.Primary.TButton",
            command=self.apply_and_close,
        ).pack(side="right")

    def _build_presets(self, parent: tk.LabelFrame) -> None:
        for index, preset in enumerate(PRESETS):
            self._build_preset_row(parent, preset, row=index)
        self._build_preset_row(
            parent,
            DurationPreset("自定义", "使用下方参数，不套用预设。", TimerConfig()),
            row=len(PRESETS),
            value=CUSTOM_VALUE,
        )

    def _build_preset_row(
        self,
        parent: tk.LabelFrame,
        preset: DurationPreset,
        *,
        row: int,
        value: str | None = None,
    ) -> None:
        card = tk.Frame(parent, bg=CARD, padx=10, pady=6)
        card.grid(row=row, column=0, sticky="ew", pady=3)
        card.columnconfigure(0, weight=1)
        tk.Radiobutton(
            card,
            text=f"{preset.name}   {preset.summary}",
            variable=self.preset_var,
            value=value or preset.name,
            command=self._select_preset,
            bg=CARD,
            fg=TEXT,
            activebackground=CARD,
            selectcolor=TRACK,
            font=(FONT, 9, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            card,
            text=preset.description,
            bg=CARD,
            fg=MUTED,
            font=(FONT, 8),
            wraplength=360,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

    def _build_custom_fields(self, parent: tk.LabelFrame) -> None:
        rows = [
            ("专注时长（分钟）", "focus_minutes"),
            ("短休息（分钟）", "short_break_minutes"),
            ("长休息（分钟）", "long_break_minutes"),
            ("几轮后长休息", "sessions_before_long_break"),
        ]
        for row, (label, key) in enumerate(rows):
            minimum, maximum = RANGES[key]
            tk.Label(
                parent,
                text=label,
                bg=BG,
                fg=TEXT,
                font=(FONT, 9),
            ).grid(row=row, column=0, sticky="w", pady=4)
            ttk.Spinbox(
                parent,
                from_=minimum,
                to=maximum,
                width=8,
                textvariable=self.vars[key],
                style="TSpinbox",
            ).grid(row=row, column=1, sticky="e", pady=4)

    def _center_on_parent(self, master: tk.Misc) -> None:
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        if master.winfo_viewable():
            x = master.winfo_rootx() + master.winfo_width() // 2 - width // 2
            y = master.winfo_rooty() + master.winfo_height() // 2 - height // 2
        else:
            x = (self.winfo_screenwidth() - width) // 2
            y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

    def _on_value_changed(self, *_args: object) -> None:
        if not self._loading:
            self.preset_var.set(CUSTOM_VALUE)

    def _select_preset(self) -> None:
        """选中预设时把参数填入自定义字段，方便用户继续微调。"""
        preset = next(
            (item for item in PRESETS if item.name == self.preset_var.get()),
            None,
        )
        if preset is None:
            return

        self._loading = True
        self.vars["focus_minutes"].set(preset.config.focus_minutes)
        self.vars["short_break_minutes"].set(preset.config.short_break_minutes)
        self.vars["long_break_minutes"].set(preset.config.long_break_minutes)
        self.vars["sessions_before_long_break"].set(
            preset.config.sessions_before_long_break
        )
        self._loading = False

    def apply_and_close(self) -> None:
        """校验输入、回调主界面并关闭窗口。"""
        try:
            config = TimerConfig(
                focus_minutes=self.vars["focus_minutes"].get(),
                short_break_minutes=self.vars["short_break_minutes"].get(),
                long_break_minutes=self.vars["long_break_minutes"].get(),
                sessions_before_long_break=self.vars[
                    "sessions_before_long_break"
                ].get(),
            )
        except (ValueError, tk.TclError) as exc:
            messagebox.showerror("时长无效", str(exc), parent=self)
            return

        self.result = config
        self.on_apply(config)
        self.destroy()

    def cancel(self) -> None:
        """放弃修改并关闭窗口。"""
        self.result = None
        self.destroy()
