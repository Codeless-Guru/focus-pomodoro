"""v0.3.0 桌面日历与闹钟弹窗。"""

from __future__ import annotations

import calendar
import tkinter as tk
from datetime import date, datetime, time
from tkinter import messagebox, ttk
from typing import Callable

from .calendar_store import (
    REPEAT_NAMES,
    CalendarEvent,
    CalendarStore,
)
from .theme_presets import ThemePreset

WEEKDAYS: tuple[str, ...] = ("一", "二", "三", "四", "五", "六", "日")
CalendarChangeCallback = Callable[[], None]


class CalendarDialog(tk.Toplevel):
    """月历视图 + 当天提醒列表 + 新增/编辑表单。"""

    def __init__(
        self,
        master: tk.Misc,
        store: CalendarStore,
        theme: ThemePreset,
        on_change: CalendarChangeCallback | None = None,
    ) -> None:
        super().__init__(master)
        self.store = store
        self.theme = theme
        self.colors = theme.colors
        self.font = theme.font
        self.on_change = on_change
        self.today = date.today()
        self.view_year = self.today.year
        self.view_month = self.today.month
        self.selected_date = self.today
        self._day_buttons: list[tk.Button] = []
        self._tree_event_ids: dict[str, str] = {}
        self._editing_id: str | None = None

        self.title("桌面日历 · 闹钟提醒")
        self.configure(bg=self.colors["bg"])
        self.transient(master)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self._build_styles()
        self._build_ui()
        self._refresh_grid()
        self._refresh_list()
        self._center(master, 580, 680)
        self.grab_set()

    def _build_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Calendar.TButton",
            font=(self.font, 9),
            padding=(8, 6),
        )
        style.configure(
            "Calendar.Primary.TButton",
            background=self.colors["focus"],
            foreground=self.colors["on_accent"],
            font=(self.font, 9, "bold"),
            padding=(10, 7),
        )
        style.map(
            "Calendar.Primary.TButton",
            background=[("active", self.colors["focus_hover"])],
        )
        style.configure(
            "Calendar.Treeview",
            background=self.colors["card"],
            fieldbackground=self.colors["card"],
            foreground=self.colors["text"],
            borderwidth=0,
            rowheight=25,
        )
        style.configure(
            "Calendar.Treeview.Heading",
            background=self.colors["card_light"],
            foreground=self.colors["text"],
            font=(self.font, 9, "bold"),
        )
        style.map(
            "Calendar.Treeview",
            background=[("selected", self.colors["focus"])],
            foreground=[("selected", self.colors["on_accent"])],
        )

    def _build_ui(self) -> None:
        container = ttk.Frame(self, padding=16)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)

        tk.Label(
            container,
            text="桌面日历",
            bg=self.colors["bg"],
            fg=self.colors["text"],
            font=(self.font, 18, "bold"),
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            container,
            text="点击日期查看或添加提醒，到点会弹出桌面通知。",
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            font=(self.font, 9),
        ).grid(row=1, column=0, sticky="w", pady=(4, 10))

        nav = ttk.Frame(container)
        nav.grid(row=2, column=0, sticky="ew")
        ttk.Button(
            nav, text="‹", width=3, style="Calendar.TButton", command=self.previous_month
        ).pack(side="left")
        self.month_label = tk.Label(
            nav,
            text="",
            bg=self.colors["bg"],
            fg=self.colors["text"],
            font=(self.font, 12, "bold"),
        )
        self.month_label.pack(side="left", expand=True)
        ttk.Button(
            nav, text="›", width=3, style="Calendar.TButton", command=self.next_month
        ).pack(side="right")
        ttk.Button(
            nav, text="今天", style="Calendar.TButton", command=self.go_today
        ).pack(side="right", padx=(0, 6))

        weekday_frame = ttk.Frame(container)
        weekday_frame.grid(row=3, column=0, sticky="ew", pady=(8, 2))
        for index, label in enumerate(WEEKDAYS):
            tk.Label(
                weekday_frame,
                text=label,
                bg=self.colors["card_light"],
                fg=self.colors["muted"],
                font=(self.font, 9, "bold"),
                width=5,
            ).grid(row=0, column=index, padx=1, pady=1)

        self.grid_frame = ttk.Frame(container)
        self.grid_frame.grid(row=4, column=0, sticky="ew")

        selected_frame = ttk.Frame(container)
        selected_frame.grid(row=5, column=0, sticky="ew", pady=(12, 4))
        self.selected_label = tk.Label(
            selected_frame,
            text="",
            bg=self.colors["bg"],
            fg=self.colors["focus"],
            font=(self.font, 11, "bold"),
        )
        self.selected_label.pack(side="left")
        tk.Label(
            selected_frame,
            text="重复事件也会显示在对应日期",
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            font=(self.font, 8),
        ).pack(side="right")

        self.tree = ttk.Treeview(
            container,
            columns=("time", "title", "repeat"),
            displaycolumns=("time", "title", "repeat"),
            show="headings",
            style="Calendar.Treeview",
            height=5,
        )
        self.tree.heading("time", text="时间")
        self.tree.heading("title", text="提醒")
        self.tree.heading("repeat", text="重复")
        self.tree.column("time", width=65, anchor="center")
        self.tree.column("title", width=300, anchor="w")
        self.tree.column("repeat", width=70, anchor="center")
        self.tree.grid(row=6, column=0, sticky="ew")
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        form = ttk.Frame(container)
        form.grid(row=7, column=0, sticky="ew", pady=(10, 0))
        tk.Label(
            form,
            text="提醒标题",
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            font=(self.font, 9),
        ).grid(row=0, column=0, sticky="w")
        self.title_var = tk.StringVar()
        tk.Entry(
            form,
            textvariable=self.title_var,
            bg=self.colors["card"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat",
            width=24,
        ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=(0, 8))

        tk.Label(
            form,
            text="时间",
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            font=(self.font, 9),
        ).grid(row=0, column=2, sticky="w")
        self.time_var = tk.StringVar(value="09:00")
        tk.Entry(
            form,
            textvariable=self.time_var,
            bg=self.colors["card"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat",
            width=9,
        ).grid(row=1, column=2, sticky="w")

        tk.Label(
            form,
            text="重复",
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            font=(self.font, 9),
        ).grid(row=0, column=3, sticky="w")
        self.repeat_var = tk.StringVar(value=REPEAT_NAMES[0])
        ttk.Combobox(
            form,
            textvariable=self.repeat_var,
            values=REPEAT_NAMES,
            state="readonly",
            width=8,
        ).grid(row=1, column=3, sticky="w")

        tk.Label(
            form,
            text="备注",
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            font=(self.font, 9),
        ).grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.note_var = tk.StringVar()
        tk.Entry(
            form,
            textvariable=self.note_var,
            bg=self.colors["card"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat",
            width=48,
        ).grid(row=3, column=0, columnspan=4, sticky="ew", pady=(2, 0))

        actions = ttk.Frame(container)
        actions.grid(row=8, column=0, sticky="ew", pady=(12, 0))
        ttk.Button(
            actions,
            text="保存提醒",
            style="Calendar.Primary.TButton",
            command=self.save_event,
        ).pack(side="left")
        ttk.Button(
            actions,
            text="删除",
            style="Calendar.TButton",
            command=self.delete_event,
        ).pack(side="left", padx=6)
        ttk.Button(
            actions,
            text="清空表单",
            style="Calendar.TButton",
            command=self.clear_form,
        ).pack(side="left")
        ttk.Button(
            actions,
            text="关闭",
            style="Calendar.TButton",
            command=self.close,
        ).pack(side="right")

    def _center(self, master: tk.Misc, width: int, height: int) -> None:
        self.update_idletasks()
        if master.winfo_viewable():
            x = master.winfo_rootx() + master.winfo_width() // 2 - width // 2
            y = master.winfo_rooty() + master.winfo_height() // 2 - height // 2
        else:
            x = (self.winfo_screenwidth() - width) // 2
            y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{max(0, x)}+{max(0, y)}")

    def previous_month(self) -> None:
        if self.view_month == 1:
            self.view_year -= 1
            self.view_month = 12
        else:
            self.view_month -= 1
        self._refresh_grid()

    def next_month(self) -> None:
        if self.view_month == 12:
            self.view_year += 1
            self.view_month = 1
        else:
            self.view_month += 1
        self._refresh_grid()

    def go_today(self) -> None:
        self.today = date.today()
        self.view_year = self.today.year
        self.view_month = self.today.month
        self.select_date(self.today)

    def select_date(self, day: date) -> None:
        self.selected_date = day
        self.view_year = day.year
        self.view_month = day.month
        self._refresh_grid()
        self._refresh_list()
        self.clear_form()

    def _refresh_grid(self) -> None:
        for child in list(self.grid_frame.winfo_children()):
            child.destroy()
        self._day_buttons = []
        self.month_label.configure(text=f"{self.view_year} 年 {self.view_month} 月")

        first_weekday = calendar.monthrange(self.view_year, self.view_month)[0]
        days_in_month = calendar.monthrange(self.view_year, self.view_month)[1]
        leading = (first_weekday + 1) % 7

        for index in range(42):
            day_number = index - leading + 1
            if 1 <= day_number <= days_in_month:
                day = date(self.view_year, self.view_month, day_number)
                has_event = bool(self.store.events_for(day))
                is_today = day == self.today
                is_selected = day == self.selected_date
                text = f"{day_number}\n{'●' if has_event else ' '}"
                background = (
                    self.colors["focus"]
                    if is_selected
                    else self.colors["card_light"]
                    if is_today
                    else self.colors["card"]
                )
                foreground = (
                    self.colors["on_accent"]
                    if is_selected
                    else self.colors["focus"]
                    if is_today
                    else self.colors["text"]
                )
                button = tk.Button(
                    self.grid_frame,
                    text=text,
                    bg=background,
                    fg=foreground,
                    activebackground=self.colors["card_light"],
                    activeforeground=self.colors["text"],
                    relief="flat",
                    width=5,
                    height=2,
                    font=(self.font, 9),
                    command=lambda current=day: self.select_date(current),
                )
                self._day_buttons.append(button)
            else:
                button = tk.Button(
                    self.grid_frame,
                    text="",
                    bg=self.colors["bg"],
                    fg=self.colors["muted"],
                    relief="flat",
                    width=5,
                    height=2,
                    state="disabled",
                )
            button.grid(row=index // 7, column=index % 7, padx=1, pady=1)

    def _refresh_list(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._tree_event_ids = {}
        self.selected_label.configure(text=f"选中日期：{self.selected_date.isoformat()}")
        for event in self.store.events_for(self.selected_date):
            item = self.tree.insert(
                "",
                "end",
                values=(
                    event.event_time.strftime("%H:%M"),
                    event.title if event.enabled else f"{event.title}（已停用）",
                    event.repeat_label(),
                ),
            )
            self._tree_event_ids[str(item)] = event.id
        if self._editing_id not in self._tree_event_ids.values():
            self.clear_form()

    def _on_tree_select(self, _event: object | None = None) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        event_id = self._tree_event_ids.get(str(selection[0]))
        if event_id is None:
            return
        event = self.store.find(event_id)
        if event is None:
            return
        self._editing_id = event.id
        self.title_var.set(event.title)
        self.time_var.set(event.event_time.strftime("%H:%M"))
        self.repeat_var.set(event.repeat_label())
        self.note_var.set(event.note)

    def _read_form(self) -> tuple[str, time, str, str] | None:
        title = self.title_var.get().strip()
        if not title:
            messagebox.showerror("提醒无效", "请填写提醒标题", parent=self)
            return None
        try:
            event_time = datetime.strptime(self.time_var.get().strip(), "%H:%M").time()
        except ValueError:
            messagebox.showerror("时间无效", "请按 HH:MM 格式填写时间", parent=self)
            return None
        repeat_label = self.repeat_var.get()
        repeat = next(
            (key for key, label in {
                "none": REPEAT_NAMES[0],
                "daily": REPEAT_NAMES[1],
                "weekly": REPEAT_NAMES[2],
            }.items() if label == repeat_label),
            "none",
        )
        return title, event_time, self.note_var.get().strip(), repeat

    def save_event(self) -> None:
        values = self._read_form()
        if values is None:
            return
        title, event_time, note, repeat = values
        try:
            if self._editing_id is None:
                self.store.add(
                    title,
                    self.selected_date,
                    event_time,
                    note=note,
                    repeat=repeat,
                )
            else:
                self.store.update(
                    self._editing_id,
                    title=title,
                    event_date=self.selected_date,
                    event_time=event_time,
                    note=note,
                    repeat=repeat,
                    enabled=True,
                )
        except ValueError as exc:
            messagebox.showerror("提醒无效", str(exc), parent=self)
            return
        self.clear_form()
        self._refresh_grid()
        self._refresh_list()
        self._notify_change()

    def delete_event(self) -> None:
        if self._editing_id is None:
            messagebox.showinfo("提示", "请先选择一个提醒", parent=self)
            return
        event = self.store.find(self._editing_id)
        if event is None:
            return
        confirmed = messagebox.askyesno(
            "删除提醒",
            f"确定删除“{event.title}”吗？",
            parent=self,
        )
        if not confirmed:
            return
        self.store.remove(event.id)
        self.clear_form()
        self._refresh_grid()
        self._refresh_list()
        self._notify_change()

    def clear_form(self) -> None:
        self._editing_id = None
        self.title_var.set("")
        self.time_var.set("09:00")
        self.repeat_var.set(REPEAT_NAMES[0])
        self.note_var.set("")
        self.tree.selection_remove(self.tree.selection())

    def _notify_change(self) -> None:
        if self.on_change is not None:
            self.on_change()

    def close(self) -> None:
        """关闭弹窗。"""
        self.destroy()
