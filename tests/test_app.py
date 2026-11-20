import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from pomodoro.app import PomodoroApp
from pomodoro.settings import load_settings
from pomodoro.timer import Phase, TimerConfig, TimerEvent


class AppSmokeTests(unittest.TestCase):
    def test_window_can_be_created_and_controlled(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"当前环境没有图形界面：{exc}")
            return

        root.withdraw()
        try:
            with tempfile.TemporaryDirectory() as directory:
                settings_path = Path(directory) / "settings.json"
                app = PomodoroApp(root, settings_path)
                app.settings.sound_enabled = False
                root.update()

                app.toggle_timer()
                root.update()
                self.assertTrue(app.timer.is_running)

                app.toggle_timer()
                root.update()
                self.assertFalse(app.timer.is_running)

                app.reset_timer()
                app.toggle_settings()
                root.update()
                self.assertTrue(app._settings_visible)

                app.skip_phase()
                root.update()
                self.assertIs(app.timer.snapshot().phase, Phase.SHORT_BREAK)

                app.on_close()
                self.assertTrue(settings_path.exists())
        finally:
            try:
                root.destroy()
            except tk.TclError:
                pass

    def test_only_completed_phases_trigger_window_alert(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"当前环境没有图形界面：{exc}")
            return

        root.withdraw()
        try:
            with tempfile.TemporaryDirectory() as directory:
                settings_path = Path(directory) / "settings.json"
                app = PomodoroApp(root, settings_path)
                app.settings.sound_enabled = False

                completion = TimerEvent("completed", Phase.FOCUS, Phase.SHORT_BREAK)
                skip = TimerEvent("skipped", Phase.FOCUS, Phase.SHORT_BREAK)

                with patch.object(app, "_restore_and_shake") as alert:
                    app._notify(completion)
                    alert.assert_called_once_with()

                with patch.object(app, "_restore_and_shake") as alert:
                    app._notify(skip)
                    alert.assert_not_called()

                root.update()
                app.on_close()
        finally:
            try:
                root.destroy()
            except tk.TclError:
                pass

    def test_minimized_window_is_restored_on_alert(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"当前环境没有图形界面：{exc}")
            return

        try:
            with tempfile.TemporaryDirectory() as directory:
                settings_path = Path(directory) / "settings.json"
                app = PomodoroApp(root, settings_path)
                app.settings.sound_enabled = False
                root.update()

                try:
                    root.iconify()
                    root.update()
                except tk.TclError as exc:
                    self.skipTest(f"窗口管理器不支持最小化：{exc}")
                    return
                if root.state() != "iconic":
                    self.skipTest("窗口管理器未报告最小化状态")

                app._restore_and_shake()
                root.update()

                self.assertNotEqual(root.state(), "iconic")
                app.on_close()
        finally:
            try:
                root.destroy()
            except tk.TclError:
                pass

    def test_duration_config_is_applied_and_saved(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"当前环境没有图形界面：{exc}")
            return

        root.withdraw()
        try:
            with tempfile.TemporaryDirectory() as directory:
                settings_path = Path(directory) / "settings.json"
                app = PomodoroApp(root, settings_path)
                root.update()

                config = TimerConfig(15, 3, 10, 4)
                app._apply_duration_config(config)
                root.update()

                self.assertEqual(app.timer.config, config)
                self.assertEqual(app.settings.timer, config)
                self.assertEqual(load_settings(settings_path).timer, config)
                self.assertEqual(app.timer.snapshot().cycle_length, 4)

                app.on_close()
        finally:
            try:
                root.destroy()
            except tk.TclError:
                pass

    def test_theme_can_be_switched_and_saved(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"当前环境没有图形界面：{exc}")
            return

        root.withdraw()
        try:
            with tempfile.TemporaryDirectory() as directory:
                settings_path = Path(directory) / "settings.json"
                app = PomodoroApp(root, settings_path)
                root.update()

                app.toggle_settings()
                self.assertTrue(hasattr(app, "main_canvas"))

                app.theme_var.set("国风")
                app.on_theme_selected()
                root.update()

                self.assertEqual(app.theme.key, "guofeng")
                self.assertEqual(app.colors["bg"], "#F3EBDD")
                self.assertEqual(app._preview_theme_key, "guofeng")
                self.assertEqual(load_settings(settings_path).theme_key, "business")
                self.assertTrue(app._settings_visible)
                self.assertEqual(app.theme_var.get(), "国风")

                app.apply_settings()
                root.update()

                self.assertIsNone(app._preview_theme_key)
                self.assertEqual(load_settings(settings_path).theme_key, "guofeng")
                self.assertEqual(app.theme.key, "guofeng")

                app.on_close()
        finally:
            try:
                root.destroy()
            except tk.TclError:
                pass

    def test_theme_preview_can_be_reverted(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"当前环境没有图形界面：{exc}")
            return

        root.withdraw()
        try:
            with tempfile.TemporaryDirectory() as directory:
                settings_path = Path(directory) / "settings.json"
                app = PomodoroApp(root, settings_path)
                root.update()

                app.theme_var.set("儿童")
                app.on_theme_selected()
                root.update()
                self.assertEqual(app.theme.key, "children")

                app.cancel_theme_preview()
                root.update()

                self.assertEqual(app.theme.key, "business")
                self.assertIsNone(app._preview_theme_key)
                self.assertEqual(load_settings(settings_path).theme_key, "business")

                app.on_close()
        finally:
            try:
                root.destroy()
            except tk.TclError:
                pass

    def test_focus_completion_records_task_and_stats(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"当前环境没有图形界面：{exc}")
            return

        root.withdraw()
        try:
            with tempfile.TemporaryDirectory() as directory:
                settings_path = Path(directory) / "settings.json"
                app = PomodoroApp(root, settings_path)
                app.settings.sound_enabled = False
                task = app.task_store.add("写发布说明", 1)
                app.task_store.select(task.id)

                event = TimerEvent("completed", Phase.FOCUS, Phase.SHORT_BREAK)
                with patch.object(app, "_restore_and_shake"), patch.object(
                    app, "_show_toast"
                ) as toast, patch.object(app, "_play_sound"):
                    app._notify(event)

                self.assertEqual(app.stats_store.summary().today_pomodoros, 1)
                self.assertEqual(app.task_store.active_task().completed, 1)
                self.assertIn("任务已完成", toast.call_args[0][1])

                app.on_close()
        finally:
            try:
                root.destroy()
            except tk.TclError:
                pass


if __name__ == "__main__":
    unittest.main()
