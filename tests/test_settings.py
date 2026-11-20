import json
import tempfile
import unittest
from pathlib import Path

from pomodoro.settings import AppSettings, load_settings, save_settings
from pomodoro.timer import TimerConfig


class SettingsTests(unittest.TestCase):
    def test_save_and_load_round_trip(self) -> None:
        settings = AppSettings(
            timer=TimerConfig(
                focus_minutes=30,
                short_break_minutes=8,
                long_break_minutes=20,
                sessions_before_long_break=3,
            ),
            auto_start_next=False,
            sound_enabled=False,
            always_on_top=True,
            calendar_alerts_enabled=False,
            task_name="写季度总结",
            theme_key="apple_purple",
        )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config" / "settings.json"
            save_settings(settings, path)
            loaded = load_settings(path)

        self.assertEqual(loaded, settings)

    def test_invalid_json_falls_back_to_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text("{ not json", encoding="utf-8")
            loaded = load_settings(path)

        self.assertEqual(loaded, AppSettings())

    def test_partial_settings_use_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text(
                json.dumps(
                    {
                        "focus_minutes": 40,
                        "sound_enabled": False,
                        "theme_key": "unknown",
                    }
                ),
                encoding="utf-8",
            )
            loaded = load_settings(path)

        self.assertEqual(loaded.timer.focus_minutes, 40)
        self.assertEqual(loaded.timer.short_break_minutes, 5)
        self.assertFalse(loaded.sound_enabled)
        self.assertTrue(loaded.auto_start_next)
        self.assertTrue(loaded.calendar_alerts_enabled)
        self.assertEqual(loaded.theme_key, "apple_light")


if __name__ == "__main__":
    unittest.main()
