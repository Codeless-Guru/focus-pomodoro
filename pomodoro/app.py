"""番茄钟的 Tkinter 桌面界面。

界面只负责渲染和交互；计时规则由 PomodoroTimer 提供，设置由 settings 模块保存。
"""

from __future__ import annotations

import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import ttk

from .calendar_dialog import CalendarDialog
from .calendar_store import CalendarStore
from .duration_dialog import DurationDialog
from .feature_dialogs import RewardDialog, StatsDialog, TaskDialog
from .settings import load_settings, save_settings
from .stats import StatsStore
from .tasks import TaskStore
from .theme_presets import (
    THEME_NAMES,
    ThemePreset,
    find_theme_by_name,
    get_theme,
)
from .timer import (
    Phase,
    PomodoroTimer,
    TimerConfig,
    TimerEvent,
    format_duration,
)
from .ui_utils import draw_gradient

class PomodoroApp:
    """主窗口控制器：创建界面、绑定交互，并把计时状态渲染到窗口。"""

    def __init__(self, root: tk.Tk, settings_path: Path | str | None = None) -> None:
        """装配应用；settings_path 主要用于测试时隔离用户配置。"""
        self.root = root
        self.settings_path = Path(settings_path) if settings_path is not None else None
        self.settings = load_settings(self.settings_path)
        self.theme: ThemePreset = get_theme(self.settings.theme_key)
        self.colors = self.theme.colors
        self.font = self.theme.font
        self.timer = PomodoroTimer(
            self.settings.timer,
            auto_start_next=self.settings.auto_start_next,
        )

        # 测试时传入的 settings_path 同时决定任务与统计文件的位置。
        data_dir = self.settings_path.parent if self.settings_path is not None else None
        self.task_store = TaskStore(data_dir / "tasks.json" if data_dir else None)
        self.stats_store = StatsStore(data_dir / "stats.json" if data_dir else None)
        self.calendar_store = CalendarStore(
            data_dir / "calendar.json" if data_dir else None
        )

        # 记录弹窗、设置面板、定时回调和窗口抖动等界面状态。
        self._toast: tk.Toplevel | None = None
        self._settings_visible = False
        self._tick_id: str | None = None
        self._shaking = False
        self._topmost_reset_id: str | None = None
        self._preview_theme_key: str | None = None

        # 固定顺序：先配置窗口，再建样式和控件，最后启动定时刷新。
        self._configure_window()
        self._build_styles()
        self._build_ui()
        self._apply_window_settings()
        self._render()
        self._schedule_tick()

    def _configure_window(self) -> None:
        """设置窗口标题、尺寸、关闭协议和全局快捷键。"""
        self.root.title("专注番茄钟")
        self.root.configure(bg=self.colors["bg"])
        self.root.resizable(True, True)
        self.root.minsize(500, 680)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.bind("<Key>", self._on_key)

        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = min(520, max(500, screen_width - 40))
        height = min(840, max(680, screen_height - 40))
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.eval("tk::PlaceWindow . center")

    def _build_styles(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", background=self.colors["bg"])
        style.configure("Card.TFrame", background=self.colors["card"])
        style.configure(
            "TLabel",
            background=self.colors["bg"],
            foreground=self.colors["text"],
            font=(self.font, 10),
        )
        style.configure(
            "Title.TLabel",
            background=self.colors["bg"],
            foreground=self.colors["text"],
            font=(self.font, 22, "bold"),
        )
        style.configure(
            "Sub.TLabel",
            background=self.colors["bg"],
            foreground=self.colors["muted"],
            font=(self.font, 9),
        )
        style.configure(
            "Hint.TLabel",
            background=self.colors["bg"],
            foreground=self.colors["muted"],
            font=(self.font, 8),
        )
        style.configure(
            "TButton",
            font=(self.font, 10),
            padding=8,
            borderwidth=0,
        )
        style.configure(
            "Primary.TButton",
            background=self.colors["focus"],
            foreground=self.colors["on_accent"],
            font=(self.font, 11, "bold"),
            padding=(12, 11),
        )
        style.map(
            "Primary.TButton",
            background=[("active", self.colors["focus_hover"])],
        )
        style.configure(
            "Secondary.TButton",
            background=self.colors["card_light"],
            foreground=self.colors["text"],
            padding=(12, 11),
        )
        style.map(
            "Secondary.TButton",
            background=[("active", self.colors["track"])],
        )
        style.configure(
            "TCheckbutton",
            background=self.colors["card"],
            foreground=self.colors["text"],
            font=(self.font, 9),
        )
        style.map("TCheckbutton", background=[("active", self.colors["card"])])
        style.configure(
            "TEntry",
            fieldbackground=self.colors["card_light"],
            foreground=self.colors["text"],
            insertcolor=self.colors["text"],
            borderwidth=0,
            padding=8,
        )
        style.configure(
            "TSpinbox",
            fieldbackground=self.colors["card_light"],
            foreground=self.colors["text"],
            insertcolor=self.colors["text"],
            borderwidth=0,
            padding=5,
        )
        style.configure(
            "TCombobox",
            fieldbackground=self.colors["card_light"],
            background=self.colors["card"],
            foreground=self.colors["text"],
            borderwidth=0,
            padding=5,
        )
        style.configure(
            "Tool.TButton",
            background=self.colors["card"],
            foreground=self.colors["text"],
            font=(self.font, 9),
            padding=(8, 9),
        )
        style.map(
            "Tool.TButton",
            background=[("active", self.colors["card_light"])],
        )

    def _build_ui(self) -> None:
        """创建可滚动主界面：状态、进度环、任务、按钮、统计和设置区。"""
        shell = ttk.Frame(self.root)
        shell.pack(fill="both", expand=True)

        self.main_canvas = tk.Canvas(
            shell,
            bg=self.colors["bg"],
            highlightthickness=0,
        )
        scrollbar = ttk.Scrollbar(
            shell,
            orient="vertical",
            command=self.main_canvas.yview,
        )
        container = ttk.Frame(self.main_canvas, padding=20)
        container.bind(
            "<Configure>",
            lambda _event: self._update_scrollregion(),
        )
        self._canvas_window_item = self.main_canvas.create_window(
            (0, 0),
            window=container,
            anchor="nw",
            width=460,
        )
        self.main_canvas.bind("<Configure>", self._center_content)
        self.main_canvas.configure(yscrollcommand=scrollbar.set)
        self.main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)

        self.header_canvas = tk.Canvas(
            container,
            width=460,
            height=74,
            bg=self.colors["card"],
            highlightthickness=0,
        )
        self.header_canvas.bind(
            "<Configure>",
            lambda event: self._draw_header(event.width),
        )
        self._draw_header(460)
        self.header_canvas.pack(fill="x")

        ring_card = tk.Frame(
            container,
            bg=self.colors["card"],
            padx=12,
            pady=10,
            highlightbackground=self.colors["track"],
            highlightthickness=1,
        )
        ring_card.pack(fill="x", pady=(12, 4))
        self.phase_pill = tk.Label(
            ring_card,
            text="专注 · 准备开始",
            bg=self.colors["card"],
            fg=self.colors["focus"],
            font=(self.font, 10, "bold"),
            padx=14,
            pady=4,
        )
        self.phase_pill.pack()

        self.canvas = tk.Canvas(
            ring_card,
            width=300,
            height=300,
            bg=self.colors["card"],
            highlightthickness=0,
        )
        self.canvas.pack(pady=(4, 0))

        ttk.Label(container, text="当前任务", style="Sub.TLabel").pack(
            anchor="w", pady=(0, 4)
        )
        self.task_var = tk.StringVar(value=self.settings.task_name)
        task_entry = ttk.Entry(container, textvariable=self.task_var, style="TEntry")
        task_entry.pack(fill="x")
        task_entry.bind("<FocusOut>", lambda _event: self._save_task_name())
        self.active_task_label = tk.Label(
            container,
            text="当前计划：未设置",
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            font=(self.font, 8),
            anchor="w",
        )
        self.active_task_label.pack(fill="x", pady=(3, 0))

        controls = ttk.Frame(container)
        controls.pack(fill="x", pady=(14, 0))
        self.start_button = ttk.Button(
            controls,
            text="开始专注",
            style="Primary.TButton",
            command=self.toggle_timer,
        )
        self.reset_button = ttk.Button(
            controls,
            text="重置",
            style="Secondary.TButton",
            command=self.reset_timer,
        )
        self.skip_button = ttk.Button(
            controls,
            text="跳过",
            style="Secondary.TButton",
            command=self.skip_phase,
        )
        self.start_button.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.reset_button.pack(side="left", fill="x", expand=True, padx=6)
        self.skip_button.pack(side="left", fill="x", expand=True, padx=(6, 0))

        stats = tk.Frame(container, bg=self.colors["bg"])
        stats.pack(fill="x", pady=(14, 0))

        def make_stat_card(title: str, value: str, color: str) -> tk.Label:
            card = tk.Frame(
                stats,
                bg=self.colors["card"],
                padx=8,
                pady=8,
                highlightbackground=self.colors["track"],
                highlightthickness=1,
            )
            card.pack(side="left", fill="x", expand=True, padx=(0, 6))
            tk.Label(
                card,
                text=title,
                bg=self.colors["card"],
                fg=self.colors["muted"],
                font=(self.font, 8),
            ).pack(anchor="w")
            value_label = tk.Label(
                card,
                text=value,
                bg=self.colors["card"],
                fg=color,
                font=(self.font, 14, "bold"),
                anchor="w",
            )
            value_label.pack(anchor="w", pady=(3, 0))
            return value_label

        today_count = self.stats_store.summary().today_pomodoros
        self.today_label = make_stat_card("今日番茄", str(today_count), self.colors["focus"])
        self.completed_label = make_stat_card(
            "累计完成", "0 个", self.colors["short"]
        )
        self.round_label = make_stat_card(
            "当前轮次", "1/4", self.colors["long"]
        )

        utility_row = ttk.Frame(container)
        utility_row.pack(fill="x", pady=(12, 0))
        self.duration_button = ttk.Button(
            utility_row,
            text="时长自定义",
            style="Secondary.TButton",
            command=self.open_duration_dialog,
        )
        self.duration_button.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.settings_button = ttk.Button(
            utility_row,
            text="设置",
            style="Secondary.TButton",
            command=self.toggle_settings,
        )
        self.settings_button.pack(side="left", fill="x", expand=True, padx=(6, 0))

        advanced_row = ttk.Frame(container)
        advanced_row.pack(fill="x", pady=(6, 0))
        ttk.Button(
            advanced_row,
            text="任务计划",
            style="Tool.TButton",
            command=self.open_task_dialog,
        ).pack(side="left", fill="x", expand=True, padx=(0, 3))
        ttk.Button(
            advanced_row,
            text="日历闹钟",
            style="Tool.TButton",
            command=self.open_calendar_dialog,
        ).pack(side="left", fill="x", expand=True, padx=3)
        ttk.Button(
            advanced_row,
            text="专注数据",
            style="Tool.TButton",
            command=self.open_stats_dialog,
        ).pack(side="left", fill="x", expand=True, padx=3)
        ttk.Button(
            advanced_row,
            text="休息奖励",
            style="Tool.TButton",
            command=self.open_reward_dialog,
        ).pack(side="left", fill="x", expand=True, padx=(3, 0))

        calendar_card = tk.Frame(
            container,
            bg=self.colors["card"],
            padx=12,
            pady=8,
            highlightbackground=self.colors["track"],
            highlightthickness=1,
        )
        calendar_card.pack(fill="x", pady=(8, 0))
        self.calendar_summary_label = tk.Label(
            calendar_card,
            text="今日提醒：暂无安排",
            bg=self.colors["card"],
            fg=self.colors["muted"],
            font=(self.font, 9),
            anchor="w",
            justify="left",
            wraplength=400,
        )
        self.calendar_summary_label.pack(fill="x")

        self.settings_frame = ttk.Frame(container, style="Card.TFrame", padding=12)
        self._build_settings(self.settings_frame)

        ttk.Label(
            container,
            text="快捷键：空格 开始/暂停    R 重置    S 跳过",
            style="Hint.TLabel",
        ).pack(pady=(10, 0))
        self._update_scrollregion()
        self._center_content()

    def _update_scrollregion(self) -> None:
        """根据内容高度更新滚动区域。"""
        if not hasattr(self, "main_canvas"):
            return
        try:
            self.main_canvas.update_idletasks()
            self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        except tk.TclError:
            pass

    def _center_content(self, _event: object | None = None) -> None:
        """把固定宽度的主内容区域水平居中。"""
        if not hasattr(self, "_canvas_window_item"):
            return
        try:
            canvas_width = self.main_canvas.winfo_width()
            content_width = 460
            x = max(0, (canvas_width - content_width) // 2)
            self.main_canvas.coords(self._canvas_window_item, x, 0)
        except tk.TclError:
            pass

    def _draw_header(self, width: int) -> None:
        """按标题卡实际宽度绘制渐变、文字和右侧装饰图标。"""
        if not hasattr(self, "header_canvas"):
            return
        try:
            canvas = self.header_canvas
            canvas.delete("all")
            actual_width = max(260, int(width))
            draw_gradient(
                canvas,
                0,
                0,
                actual_width,
                74,
                self.colors["card"],
                self.colors["card_light"],
                48,
            )
            canvas.create_text(
                18,
                23,
                text="专注番茄钟",
                fill=self.colors["text"],
                font=(self.font, 20, "bold"),
                anchor="w",
            )
            canvas.create_text(
                19,
                51,
                text="一次只做一件事",
                fill=self.colors["muted"],
                font=(self.font, 9),
                anchor="w",
            )
            if actual_width > 320:
                right = actual_width - 18
                canvas.create_oval(
                    right - 28,
                    17,
                    right,
                    45,
                    outline=self.colors["focus"],
                    width=2,
                )
                canvas.create_oval(
                    right - 19,
                    26,
                    right - 9,
                    36,
                    fill=self.colors["focus"],
                    outline="",
                )
        except (tk.TclError, ValueError):
            pass

    def _on_mousewheel(self, event: tk.Event) -> None:
        """鼠标滚轮滚动主区域；输入框和数字框保持原行为。"""
        if not hasattr(self, "main_canvas"):
            return
        try:
            if event.widget.winfo_class() in (
                "Entry",
                "TEntry",
                "Spinbox",
                "TSpinbox",
                "TCombobox",
            ):
                return
            self.main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except tk.TclError:
            pass

    def _build_settings(self, parent: ttk.Frame) -> None:
        """创建常规设置面板；时长配置已独立到“时长自定义”模块。"""
        self.auto_start_var = tk.BooleanVar(value=self.settings.auto_start_next)
        self.sound_var = tk.BooleanVar(value=self.settings.sound_enabled)
        self.topmost_var = tk.BooleanVar(value=self.settings.always_on_top)
        self.calendar_alerts_var = tk.BooleanVar(
            value=self.settings.calendar_alerts_enabled
        )
        self.theme_var = tk.StringVar(value=self.theme.name)

        theme_row = ttk.Frame(parent)
        theme_row.pack(fill="x", pady=(0, 6))
        tk.Label(
            theme_row,
            text="界面风格（选择后预览）",
            bg=self.colors["card"],
            fg=self.colors["text"],
            font=(self.font, 9),
        ).pack(side="left")
        theme_combo = ttk.Combobox(
            theme_row,
            textvariable=self.theme_var,
            values=THEME_NAMES,
            state="readonly",
            width=12,
        )
        theme_combo.bind("<<ComboboxSelected>>", self.on_theme_selected)
        theme_combo.pack(side="right")

        self.preview_status_label = tk.Label(
            parent,
            text="",
            bg=self.colors["card"],
            fg=self.colors["muted"],
            font=(self.font, 8),
            anchor="w",
        )
        self.preview_status_label.pack(fill="x", pady=(0, 4))
        ttk.Button(
            parent,
            text="还原主题预览",
            style="Tool.TButton",
            command=self.cancel_theme_preview,
        ).pack(fill="x", pady=(0, 8))

        ttk.Checkbutton(
            parent,
            text="阶段结束后自动开始下一阶段",
            variable=self.auto_start_var,
            style="TCheckbutton",
        ).pack(anchor="w", pady=4)
        ttk.Checkbutton(
            parent,
            text="结束提示音",
            variable=self.sound_var,
            style="TCheckbutton",
        ).pack(anchor="w", pady=4)
        ttk.Checkbutton(
            parent,
            text="窗口始终在最前",
            variable=self.topmost_var,
            style="TCheckbutton",
        ).pack(anchor="w", pady=4)
        ttk.Checkbutton(
            parent,
            text="启用日历闹钟提醒",
            variable=self.calendar_alerts_var,
            style="TCheckbutton",
        ).pack(anchor="w", pady=4)

        ttk.Button(
            parent,
            text="应用设置",
            style="Primary.TButton",
            command=self.apply_settings,
        ).pack(fill="x", pady=(8, 0))

    def toggle_timer(self) -> None:
        """按钮/空格键入口：在暂停和开始之间切换当前阶段。"""
        if self.timer.is_running:
            self.timer.pause()
        else:
            self.timer.start()
        self._render()

    def reset_timer(self) -> None:
        """按钮/R 键入口：把当前阶段恢复到完整时长。"""
        self.timer.reset()
        self._render()

    def skip_phase(self) -> None:
        """按钮/S 键入口：跳过当前阶段，并提示进入的下一阶段。"""
        event = self.timer.skip()
        self._notify(event)
        self._render()

    def toggle_settings(self) -> None:
        """展开或收起设置，并在展开后自动滚动到设置区域。"""
        self._settings_visible = not self._settings_visible
        if self._settings_visible:
            self.settings_frame.pack(fill="x", pady=(8, 0))
            self.settings_button.configure(text="收起设置")
            self._update_scrollregion()
            self.root.after(60, lambda: self.main_canvas.yview_moveto(1.0))
        else:
            self.settings_frame.pack_forget()
            self.settings_button.configure(text="设置")
            self._update_scrollregion()

    def open_duration_dialog(self) -> None:
        """打开“时长自定义”弹窗，确认后由回调保存并应用新方案。"""
        dialog = DurationDialog(
            self.root,
            self.settings.timer,
            self._apply_duration_config,
            theme=self.theme,
        )
        self.root.wait_window(dialog)

    def open_task_dialog(self) -> None:
        """打开任务计划窗口，管理当前任务与番茄估算。"""
        dialog = TaskDialog(self.root, self.task_store, self.theme)
        self.root.wait_window(dialog)
        self._render()

    def open_stats_dialog(self) -> None:
        """打开专注数据与成就窗口。"""
        dialog = StatsDialog(self.root, self.stats_store, self.task_store, self.theme)
        self.root.wait_window(dialog)

    def open_reward_dialog(self) -> None:
        """打开休息奖励转盘。"""
        dialog = RewardDialog(self.root, self.theme)
        self.root.wait_window(dialog)

    def open_calendar_dialog(self) -> None:
        """打开桌面日历，新增或修改的提醒会立即写入本地数据。"""
        dialog = CalendarDialog(
            self.root,
            self.calendar_store,
            self.theme,
            on_change=self._render,
        )
        self.root.wait_window(dialog)
        self._render()

    def _apply_duration_config(self, config: TimerConfig) -> None:
        """应用时长自定义模块返回的配置并写入设置文件。"""
        self.settings.timer = config
        self.timer.configure(config, auto_start_next=self.settings.auto_start_next)
        save_settings(self.settings, self.settings_path)
        self._render()

    def on_theme_selected(self, _event: object | None = None) -> None:
        """选择主题时只预览效果，不写入配置文件。"""
        selected_theme = find_theme_by_name(self.theme_var.get())
        if selected_theme is None or selected_theme.key == self.theme.key:
            return
        self._preview_theme_key = selected_theme.key
        self._apply_theme(selected_theme)

    def cancel_theme_preview(self) -> None:
        """放弃主题预览，恢复到已保存的风格。"""
        saved_theme = get_theme(self.settings.theme_key)
        self._preview_theme_key = None
        if self.theme.key != saved_theme.key:
            self._apply_theme(saved_theme)
        else:
            self.theme_var.set(saved_theme.name)
            self._render()

    def apply_settings(self) -> None:
        """保存主题预览和常规设置，然后同步窗口状态。"""
        selected_theme = find_theme_by_name(self.theme_var.get())
        if selected_theme is None:
            selected_theme = get_theme(self.settings.theme_key)
        if selected_theme.key != self.settings.theme_key:
            self.settings.theme_key = selected_theme.key
        self._preview_theme_key = None

        self.settings.auto_start_next = self.auto_start_var.get()
        self.settings.sound_enabled = self.sound_var.get()
        self.settings.always_on_top = self.topmost_var.get()
        self.settings.calendar_alerts_enabled = self.calendar_alerts_var.get()
        self.settings.task_name = self.task_var.get().strip()
        self.task_var.set(self.settings.task_name)

        self.timer.configure(
            self.settings.timer,
            auto_start_next=self.settings.auto_start_next,
        )
        self._apply_window_settings()
        save_settings(self.settings, self.settings_path)

        if selected_theme.key != self.theme.key:
            self._apply_theme(selected_theme)
        else:
            self._render()

    def _apply_theme(self, theme: ThemePreset) -> None:
        """切换主题时重建全部控件，并尽量保留设置面板展开状态。"""
        settings_visible = self._settings_visible
        self.theme = theme
        self.colors = theme.colors
        self.font = theme.font

        if self._toast is not None:
            try:
                if self._toast.winfo_exists():
                    self._toast.destroy()
            except tk.TclError:
                pass
            self._toast = None

        for child in list(self.root.winfo_children()):
            child.destroy()

        self.root.configure(bg=self.colors["bg"])
        self._build_styles()
        self._build_ui()
        self._apply_window_settings()

        self._settings_visible = settings_visible
        if settings_visible:
            self.settings_frame.pack(fill="x", pady=(8, 0))
            self.settings_button.configure(text="收起设置")
            self._update_scrollregion()
            self.root.after(60, lambda: self.main_canvas.yview_moveto(1.0))
        self._render()

    def _apply_window_settings(self) -> None:
        self.root.attributes("-topmost", self.settings.always_on_top)

    def _save_task_name(self) -> None:
        value = self.task_var.get().strip()
        if value != self.settings.task_name:
            self.settings.task_name = value
            save_settings(self.settings, self.settings_path)

    def _on_key(self, event: tk.Event) -> None:
        """处理全局快捷键；输入框和按钮获得焦点时不拦截按键。"""
        if event.widget.winfo_class() in (
            "Entry",
            "TEntry",
            "Spinbox",
            "TSpinbox",
            "Button",
            "TButton",
        ):
            return
        key = event.keysym.lower()
        if key == "space":
            self.toggle_timer()
        elif key == "r":
            self.reset_timer()
        elif key == "s":
            self.skip_phase()

    def _schedule_tick(self) -> None:
        """每 100 毫秒安排一次计时刷新，保证倒计时显示平滑。"""
        self._tick_id = self.root.after(100, self._tick)

    def _tick(self) -> None:
        """定时刷新：推进计时、检查日历提醒、处理阶段事件并重绘界面。"""
        event = self.timer.update()
        if event is not None:
            self._notify(event)
        self._check_calendar_alarms()
        self._render()
        self._schedule_tick()

    def _notify(self, event: TimerEvent) -> None:
        """处理阶段变化提示：跳过只提示，自然完成还会弹窗、抖动并响铃。"""
        if not event.is_completion:
            self._show_toast("已跳过", f"已进入{event.to_phase.label}阶段")
            return

        self._restore_and_shake()
        if event.from_phase is Phase.FOCUS:
            self.stats_store.record_focus(self.timer.config.focus_minutes)
            finished_task = self.task_store.record_focus()
            message = "起来活动一下，准备进入休息阶段"
            if finished_task:
                message += f"；任务已完成：{finished_task}"
            self._show_toast("专注完成", message)
        else:
            self._show_toast("休息结束", "回到专注，开始下一个番茄钟")
        self._play_sound()

    def _check_calendar_alarms(self, now: datetime | None = None) -> None:
        """检查到点的日历闹钟，用一条通知合并本轮到期的提醒。"""
        if not self.settings.calendar_alerts_enabled:
            return
        due_events = self.calendar_store.due_events(now)
        if not due_events:
            return

        self._restore_and_shake()
        if len(due_events) == 1:
            event = due_events[0]
            message = f"{event.event_time.strftime('%H:%M')} · {event.title}"
            if event.note:
                message += f"\n{event.note}"
        else:
            message = "；".join(
                f"{event.event_time.strftime('%H:%M')} {event.title}"
                for event in due_events
            )
        self._show_toast("日历提醒", message)
        self._play_sound()

        current = now or datetime.now()
        for event in due_events:
            self.calendar_store.mark_triggered(event.id, current)

    def _restore_and_shake(self) -> None:
        """阶段结束时恢复最小化窗口，并让主窗口短暂左右抖动提醒。"""
        try:
            state = self.root.state()
        except tk.TclError:
            return

        # 最小化窗口先恢复；最大化窗口先临时普通化，抖动结束后再还原。
        was_zoomed = False
        try:
            if state in ("iconic", "withdrawn"):
                self.root.deiconify()
            elif state == "zoomed":
                was_zoomed = True
                self.root.state("normal")
            self.root.lift()
            self.root.focus_force()
            self._make_temporarily_topmost()
            self.root.update_idletasks()
            x, y = self._window_origin()
        except tk.TclError:
            return

        # 多个完成事件同时到达时只执行一次抖动，避免回调叠加。
        if self._shaking:
            return
        self._shaking = True
        # 依次左右偏移并回到原位，形成轻微抖动效果。
        offsets = (12, -10, 8, -6, 4, -2, 0)
        for index, offset in enumerate(offsets):
            self.root.after(
                index * 70,
                lambda dx=offset, px=x, py=y: self._set_window_position(px + dx, py),
            )
        self.root.after(
            len(offsets) * 70,
            lambda px=x, py=y, zoomed=was_zoomed: self._finish_shake(px, py, zoomed),
        )

    def _window_origin(self) -> tuple[int, int]:
        """取得窗口左上角坐标；最小化时从 geometry 字符串兜底解析。"""
        x, y = self.root.winfo_x(), self.root.winfo_y()
        if x <= -1000 or y <= -1000:
            parts = self.root.geometry().split("+")
            if len(parts) >= 3:
                x, y = int(parts[-2]), int(parts[-1])
        return x, y

    def _set_window_position(self, x: int, y: int) -> None:
        """只调整窗口位置，不改变窗口尺寸。"""
        try:
            self.root.geometry(f"+{int(x)}+{int(y)}")
        except (tk.TclError, ValueError, TypeError):
            pass

    def _finish_shake(self, x: int, y: int, was_zoomed: bool) -> None:
        """抖动结束后回到原位置，并恢复最大化状态。"""
        self._set_window_position(x, y)
        if was_zoomed:
            try:
                self.root.state("zoomed")
            except tk.TclError:
                pass
        self._shaking = False

    def _make_temporarily_topmost(self) -> None:
        """临时置顶 4 秒，确保提醒不会被其他窗口挡住。"""
        try:
            self.root.attributes("-topmost", True)
        except tk.TclError:
            return
        if self._topmost_reset_id is not None:
            try:
                self.root.after_cancel(self._topmost_reset_id)
            except tk.TclError:
                pass
        self._topmost_reset_id = self.root.after(4000, self._restore_topmost)

    def _restore_topmost(self) -> None:
        """按用户设置恢复窗口的置顶状态。"""
        self._topmost_reset_id = None
        try:
            self.root.attributes("-topmost", self.settings.always_on_top)
        except tk.TclError:
            pass

    def _play_sound(self) -> None:
        """阶段完成时播放系统提示音，平台不支持时使用窗口铃声。"""
        if not self.settings.sound_enabled:
            return
        try:
            import winsound

            winsound.MessageBeep(winsound.MB_ICONINFORMATION)
        except Exception:
            try:
                self.root.bell()
            except tk.TclError:
                pass

    def _show_toast(self, title: str, message: str) -> None:
        """在屏幕右上角显示 5 秒的非阻塞提示窗。"""
        if self._toast is not None:
            try:
                if self._toast.winfo_exists():
                    self._toast.destroy()
            except tk.TclError:
                pass

        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        frame = tk.Frame(
            toast,
            bg=self.colors["card"],
            padx=16,
            pady=12,
            highlightbackground=self.colors["focus"],
            highlightthickness=1,
        )
        frame.pack(fill="both", expand=True)
        tk.Label(
            frame,
            text=title,
            bg=self.colors["card"],
            fg=self.colors["focus"],
            font=(self.font, 11, "bold"),
        ).pack(anchor="w")
        tk.Label(
            frame,
            text=message,
            bg=self.colors["card"],
            fg=self.colors["text"],
            font=(self.font, 9),
        ).pack(anchor="w", pady=(4, 0))

        toast.update_idletasks()
        x = self.root.winfo_screenwidth() - toast.winfo_width() - 24
        toast.geometry(f"+{max(0, x)}+24")
        self._toast = toast
        toast.after(5000, lambda: self._close_toast(toast))

    def _close_toast(self, toast: tk.Toplevel) -> None:
        try:
            toast.destroy()
        except tk.TclError:
            pass
        if self._toast is toast:
            self._toast = None

    def _render(self) -> None:
        """用最新的计时快照刷新所有可见控件。"""
        snapshot = self.timer.snapshot()
        phase = snapshot.phase
        accent = {
            Phase.FOCUS: self.colors["focus"],
            Phase.SHORT_BREAK: self.colors["short"],
            Phase.LONG_BREAK: self.colors["long"],
        }[phase]

        if hasattr(self, "preview_status_label"):
            if self._preview_theme_key:
                preview_text = "主题预览中：点击“应用设置”后保存"
                preview_color = self.colors["focus"]
            else:
                preview_text = "选择主题会立即预览，点击“应用设置”后保存"
                preview_color = self.colors["muted"]
            self.preview_status_label.configure(
                text=preview_text,
                fg=preview_color,
            )

        self._draw_ring(
            snapshot.remaining_whole_seconds,
            snapshot.progress,
            accent,
            phase.label,
        )

        if snapshot.is_running:
            status = "进行中"
        elif snapshot.remaining_seconds < snapshot.total_seconds - 0.5:
            status = "已暂停"
        else:
            status = "准备开始"
        self.phase_pill.configure(
            text=f"{phase.label} · {status}",
            fg=accent,
        )

        if snapshot.is_running:
            action = "暂停"
        elif snapshot.remaining_seconds < snapshot.total_seconds - 0.5:
            action = "继续"
        else:
            action = f"开始{phase.label}"
        self.start_button.configure(text=action)

        summary = self.stats_store.summary()
        self.today_label.configure(text=str(summary.today_pomodoros))
        self.completed_label.configure(
            text=f"{snapshot.completed_focus_sessions} 个"
        )
        self.round_label.configure(
            text=f"{snapshot.cycle_index}/{snapshot.cycle_length}"
        )

        active_task = self.task_store.active_task()
        if active_task is None:
            task_text = "当前计划：未设置"
        else:
            task_text = (
                f"当前计划：{active_task.name} "
                f"({active_task.completed}/{active_task.estimate})"
            )
        self.active_task_label.configure(text=task_text)

        if hasattr(self, "calendar_summary_label"):
            self.calendar_summary_label.configure(
                text=self.calendar_store.next_summary()
            )

    def _draw_ring(
        self,
        remaining_seconds: int,
        progress: float,
        accent: str,
        phase_label: str,
    ) -> None:
        """重绘进度环：外圈显示进度，中间显示剩余时间和阶段名称。"""
        self.canvas.delete("all")
        bounds = (24, 24, 276, 276)
        self.canvas.create_arc(
            *bounds,
            start=90,
            extent=-360,
            style=tk.ARC,
            outline=self.colors["track"],
            width=14,
        )
        if progress > 0:
            self.canvas.create_arc(
                *bounds,
                start=90,
                extent=-360 * progress,
                style=tk.ARC,
                outline=accent,
                width=14,
            )
        self.canvas.create_oval(
            54, 54, 246, 246, fill=self.colors["card"], outline=self.colors["track"]
        )
        self.canvas.create_oval(143, 12, 157, 26, fill=accent, outline="")
        self.canvas.create_text(
            150,
            128,
            text=format_duration(remaining_seconds),
            fill=self.colors["text"],
            font=(self.font, 46, "bold"),
        )
        self.canvas.create_text(
            150,
            178,
            text=f"{phase_label}阶段",
            fill=self.colors["muted"],
            font=(self.font, 11),
        )

    def on_close(self) -> None:
        """关闭前保存设置并取消尚未执行的定时回调。"""
        self._save_task_name()
        save_settings(self.settings, self.settings_path)
        self.task_store.save()
        self.stats_store.save()
        self.calendar_store.save()
        if self._tick_id is not None:
            try:
                self.root.after_cancel(self._tick_id)
            except tk.TclError:
                pass
            self._tick_id = None
        if self._topmost_reset_id is not None:
            try:
                self.root.after_cancel(self._topmost_reset_id)
            except tk.TclError:
                pass
            self._topmost_reset_id = None
        self.root.destroy()
