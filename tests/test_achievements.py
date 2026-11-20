import unittest
from datetime import date

from pomodoro.achievements import ACHIEVEMENTS, unlocked_achievements
from pomodoro.rewards import pick_reward
from pomodoro.stats import DailyStat, StatsSummary
from pomodoro.tasks import Task


class FixedRng:
    def __init__(self, value: str) -> None:
        self.value = value

    def choice(self, values):
        return self.value


class AchievementsTests(unittest.TestCase):
    def test_unlocks_based_on_stats_and_tasks(self) -> None:
        day = date(2026, 11, 21)
        summary = StatsSummary(
            total_pomodoros=1,
            total_minutes=25,
            today_pomodoros=1,
            week_pomodoros=1,
            streak_days=1,
            last_7_days=(DailyStat(day, 1, 25),),
        )
        tasks = [Task("abc", "完成报告", 1, 1, True)]

        unlocked = unlocked_achievements(summary, tasks)
        keys = {item.key for item in unlocked}

        self.assertEqual(ACHIEVEMENTS[0].name, "初次专注")
        self.assertIn("first", keys)
        self.assertIn("task_finisher", keys)
        self.assertNotIn("ten", keys)

    def test_no_achievements_for_empty_state(self) -> None:
        day = date(2026, 11, 21)
        summary = StatsSummary(0, 0, 0, 0, 0, (DailyStat(day, 0, 0),))
        self.assertEqual(unlocked_achievements(summary, []), ())


class RewardTests(unittest.TestCase):
    def test_pick_reward_uses_injected_rng(self) -> None:
        self.assertEqual(pick_reward(rng=FixedRng("固定奖励")), "固定奖励")

    def test_empty_rewards_rejected(self) -> None:
        with self.assertRaises(ValueError):
            pick_reward([])


if __name__ == "__main__":
    unittest.main()
