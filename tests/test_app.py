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
                app.theme_var.set("国风")
                app.apply_settings()
                root.update()

                self.assertEqual(app.theme.key, "guofeng")
                self.assertEqual(app.colors["bg"], "#F3EBDD")
                self.assertEqual(load_settings(settings_path).theme_key, "guofeng")
                self.assertTrue(app._settings_visible)
                self.assertEqual(app.theme_var.get(), "国风")

                app.on_close()
        finally:
            try:
                root.destroy()
            except tk.TclError:
                pass


if __name__ == "__main__":
    unittest.main()
