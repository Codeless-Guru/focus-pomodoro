"""休息奖励转盘内容。"""

from __future__ import annotations

import random
from typing import Sequence

REWARDS: tuple[str, ...] = (
    "喝水，让大脑休息一下",
    "站起来伸展 1 分钟",
    "看向远处，放松眼睛",
    "闭眼深呼吸 10 次",
    "在房间里走一圈",
    "听一首喜欢的歌",
    "整理一下桌面",
    "给自己倒一杯茶",
    "和同事或家人聊两句",
    "什么都不做，安静坐一会儿",
)


def pick_reward(values: Sequence[str] = REWARDS, rng: random.Random | None = None) -> str:
    """随机抽取一个休息奖励。"""
    if not values:
        raise ValueError("奖励列表不能为空")
    chooser = rng or random
    return chooser.choice(values)
