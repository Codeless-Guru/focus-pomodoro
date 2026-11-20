"""v0.2.0 功能弹窗：任务计划、专注数据、休息奖励。"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .achievements import ACHIEVEMENTS, unlocked_achievements
from .rewards import pick_reward
from .stats import StatsStore
from .tasks import TaskStore
from .theme_presets import ThemePreset


class FeatureDialog(tk.Toplevel):
    """功能弹窗的通用样式和居中逻辑。"""

    def __init__(self, master: tk.Misc, theme: ThemePreset, title: str) -> None:
        super().__init__(master)
        self.theme = theme
        self.colors = theme.colors
        self.font = theme.font
        self.title(title)
        self.configure(bg=self.colors["bg"])
        self.resizable(False, False)
        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self._build_styles()
        self.grab_set()

    def _build_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Feature.TButton", font=(self.font, 9), padding=(10, 7))
        style.configure(
            "Feature.Primary.TButton",
            background=self.colors["focus"],
            foreground=self.colors["on_accent"],
            font=(self.font, 9, "bold"),
            padding=(10, 7),
        )
        style.configure(
            "Feature.Treeview",
            background=self.colors["card"],
            fieldbackground=self.colors["card"],
            foreground=self.colors["text"],
            borderwidth=0,
            rowheight=26,
        )
        style.configure(
            "Feature.Treeview.Heading",
            background=self.colors["card_light"],
            foreground=self.colors["text"],
            font=(self.font, 9, "bold"),
        )
        style.map(
            "Feature.Treeview",
            background=[("selected", self.colors["focus"])],
        )
        style.configure(
            "Feature.Horizontal.TProgressbar",
            background=self.colors["focus"],
            troughcolor=self.colors["track"],
            borderwidth=0,
        )

    def _center(self, master: tk.Misc, width: int, height: int) -> None:
        self.update_idletasks()
        if master.winfo_viewable():
            x = master.winfo_rootx() + master.winfo_width() // 2 - width // 2
            y = master.winfo_rooty() + master.winfo_height() // 2 - height // 2
        else:
            x = (self.winfo_screenwidth() - width) // 2
            y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{max(0, x)}+{max(0, y)}")

    def close(self) -> None:
        """关闭弹窗。"""
        self.destroy()


class TaskDialog(FeatureDialog):
    """管理任务、估算番茄数和当前任务。"""

    def __init__(self, master: tk.Misc, store: TaskStore, theme: ThemePreset) -> None:
        super().__init__(master, theme, "任务计划")
        self.store = store
        self.name_var = tk.StringVar()
        self.estimate_var = tk.IntVar(value=2)
        self._build_ui()
        self._center(master, 480, 470)

    def _build_ui(self) -> None:
        container = ttk.Frame(self, padding=16)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)

        tk.Label(
            container,
            text="任务计划",
            bg=self.colors["bg"],
            fg=self.colors["text"],
            font=(self.font, 16, "bold"),
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            container,
            text="选择当前任务，专注完成后会自动累加进度。",
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            font=(self.font, 9),
        ).grid(row=1, column=0, sticky="w", pady=(3, 10))

        self.tree = ttk.Treeview(
            container,
            columns=("id", "name", "estimate", "completed"),
            displaycolumns=("name", "estimate", "completed"),
            show="headings",
            style="Feature.Treeview",
            height=8,
        )
        self.tree.heading("name", text="任务")
        self.tree.heading("estimate", text="预计")
        self.tree.heading("completed", text="完成")
        self.tree.column("name", width=250, anchor="w")
        self.tree.column("estimate", width=70, anchor="center")
        self.tree.column("completed", width=70, anchor="center")
        self.tree.tag_configure(
            "active",
            background=self.colors["card_light"],
            foreground=self.colors["focus"],
        )
        self.tree.grid(row=2, column=0, sticky="nsew", pady=(0, 10))

        form = ttk.Frame(container)
        form.grid(row=3, column=0, sticky="ew")
        tk.Entry(
            form,
            textvariable=self.name_var,
            bg=self.colors["card"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat",
            width=28,
        ).pack(side="left", padx=(0, 6))
        ttk.Spinbox(
            form,
            from_=1,
            to=50,
            width=5,
            textvariable=self.estimate_var,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            form,
            text="添加",
            style="Feature.Primary.TButton",
            command=self.add_task,
        ).pack(side="left")

        actions = ttk.Frame(container)
        actions.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        ttk.Button(
            actions,
            text="设为当前",
            style="Feature.TButton",
            command=self.select_task,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            actions,
            text="删除",
            style="Feature.TButton",
            command=self.remove_task,
        ).pack(side="left", padx=6)
        ttk.Button(
            actions,
            text="关闭",
            style="Feature.TButton",
            command=self.close,
        ).pack(side="right")

        self.refresh()

    def refresh(self) -> None:
        """重新加载任务列表。"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        for task in self.store.tasks:
            name = f"* {task.name}" if task.active else task.name
            tags = ("active",) if task.active else ()
            self.tree.insert(
                "",
                "end",
                values=(task.id, name, task.estimate, task.completed),
                tags=tags,
            )

    def add_task(self) -> None:
        """添加新任务。"""
        try:
            self.store.add(self.name_var.get(), self.estimate_var.get())
        except ValueError as exc:
            messagebox.showerror("任务无效", str(exc), parent=self)
            return
        self.name_var.set("")
        self.estimate_var.set(2)
        self.refresh()

    def selected_task_id(self) -> str | None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个任务", parent=self)
            return None
        return str(self.tree.item(selection[0], "values")[0])

    def select_task(self) -> None:
        task_id = self.selected_task_id()
        if task_id is None:
            return
        self.store.select(task_id)
        self.refresh()

    def remove_task(self) -> None:
        task_id = self.selected_task_id()
        if task_id is None:
            return
        self.store.remove(task_id)
        self.refresh()


class StatsDialog(FeatureDialog):
    """展示专注统计和成就。"""

    def __init__(
        self,
        master: tk.Misc,
        stats_store: StatsStore,
        task_store: TaskStore,
        theme: ThemePreset,
    ) -> None:
        super().__init__(master, theme, "专注数据")
        self.summary = stats_store.summary()
        self.unlocked = unlocked_achievements(self.summary, task_store.tasks)
        self._build_ui()
        self._center(master, 460, 560)

    def _build_ui(self) -> None:
        container = ttk.Frame(self, padding=16)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)

        tk.Label(
            container,
            text="专注数据",
            bg=self.colors["bg"],
            fg=self.colors["text"],
            font=(self.font, 16, "bold"),
        ).grid(row=0, column=0, sticky="w")

        summary = self.summary
        cards = (
            ("累计番茄", str(summary.total_pomodoros)),
            ("累计专注", f"{summary.total_minutes} 分钟"),
            ("今日番茄", str(summary.today_pomodoros)),
            ("近 7 天", str(summary.week_pomodoros)),
            ("连续打卡", f"{summary.streak_days} 天"),
        )
        for index, (label, value) in enumerate(cards, start=1):
            row = ttk.Frame(container, style="TFrame")
            row.grid(row=index, column=0, sticky="ew", pady=2)
            tk.Label(
                row,
                text=label,
                bg=self.colors["bg"],
                fg=self.colors["muted"],
                font=(self.font, 9),
            ).pack(side="left")
            tk.Label(
                row,
                text=value,
                bg=self.colors["bg"],
                fg=self.colors["text"],
                font=(self.font, 10, "bold"),
            ).pack(side="right")

        tk.Label(
            container,
            text="近 7 天",
            bg=self.colors["bg"],
            fg=self.colors["text"],
            font=(self.font, 11, "bold"),
        ).grid(row=6, column=0, sticky="w", pady=(12, 6))

        maximum = max(1, max(stat.pomodoros for stat in summary.last_7_days))
        for offset, stat in enumerate(summary.last_7_days):
            line = ttk.Frame(container)
            line.grid(row=7 + offset, column=0, sticky="ew", pady=2)
            tk.Label(
                line,
                text=stat.day.strftime("%m-%d"),
                bg=self.colors["bg"],
                fg=self.colors["muted"],
                font=(self.font, 8),
                width=7,
            ).pack(side="left")
            ttk.Progressbar(
                line,
                orient="horizontal",
                length=250,
                maximum=maximum,
                value=stat.pomodoros,
                style="Feature.Horizontal.TProgressbar",
            ).pack(side="left", padx=6)
            tk.Label(
                line,
                text=str(stat.pomodoros),
                bg=self.colors["bg"],
                fg=self.colors["text"],
                font=(self.font, 8),
                width=3,
            ).pack(side="left")

        start_row = 15
        tk.Label(
            container,
            text="成就",
            bg=self.colors["bg"],
            fg=self.colors["text"],
            font=(self.font, 11, "bold"),
        ).grid(row=start_row, column=0, sticky="w", pady=(12, 6))
        unlocked_keys = {item.key for item in self.unlocked}
        for offset, achievement in enumerate(ACHIEVEMENTS, start=1):
            unlocked = achievement.key in unlocked_keys
            prefix = "已解锁" if unlocked else "未解锁"
            color = self.colors["focus"] if unlocked else self.colors["muted"]
            tk.Label(
                container,
                text=f"{prefix}  {achievement.name}：{achievement.description}",
                bg=self.colors["bg"],
                fg=color,
                font=(self.font, 8),
                anchor="w",
            ).grid(row=start_row + offset, column=0, sticky="w", pady=1)

        ttk.Button(
            container,
            text="关闭",
            style="Feature.TButton",
            command=self.close,
        ).grid(row=start_row + len(ACHIEVEMENTS) + 2, column=0, sticky="e", pady=(14, 0))


class RewardDialog(FeatureDialog):
    """休息奖励转盘。"""

    def __init__(self, master: tk.Misc, theme: ThemePreset) -> None:
        super().__init__(master, theme, "休息奖励")
        self.reward_var = tk.StringVar(value="点击下方按钮，抽取休息奖励")
        self._spin_id: str | None = None
        self._remaining = 0
        self._build_ui()
        self._center(master, 420, 260)

    def _build_ui(self) -> None:
        container = ttk.Frame(self, padding=18)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)

        tk.Label(
            container,
            text="休息奖励转盘",
            bg=self.colors["bg"],
            fg=self.colors["text"],
            font=(self.font, 16, "bold"),
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            container,
            text="让随机决定你怎么休息。",
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            font=(self.font, 9),
        ).grid(row=1, column=0, sticky="w", pady=(4, 12))

        result = tk.Label(
            container,
            textvariable=self.reward_var,
            bg=self.colors["card"],
            fg=self.colors["focus"],
            font=(self.font, 12, "bold"),
            wraplength=360,
            justify="center",
            padx=12,
            pady=22,
        )
        result.grid(row=2, column=0, sticky="ew")

        buttons = ttk.Frame(container)
        buttons.grid(row=3, column=0, sticky="ew", pady=(14, 0))
        ttk.Button(
            buttons,
            text="开始转动",
            style="Feature.Primary.TButton",
            command=self.start_spin,
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            buttons,
            text="关闭",
            style="Feature.TButton",
            command=self.close,
        ).pack(side="right")

    def start_spin(self) -> None:
        """开始转盘动画。"""
        if self._spin_id is not None:
            return
        self._remaining = 24
        self._spin()

    def _spin(self) -> None:
        self.reward_var.set(pick_reward())
        self._remaining -= 1
        if self._remaining > 0:
            self._spin_id = self.after(70, self._spin)
            return
        self._spin_id = None
        self.reward_var.set(f"本次奖励：{pick_reward()}")

    def close(self) -> None:
        if self._spin_id is not None:
            try:
                self.after_cancel(self._spin_id)
            except tk.TclError:
                pass
            self._spin_id = None
        super().close()
