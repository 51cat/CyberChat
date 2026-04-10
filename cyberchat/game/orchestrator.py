"""
orchestrator.py — 游戏编排器（三阶段流程）
"""
from __future__ import annotations

import random
import re

from ..agents.player_agent import PlayerAgent
from ..agents.god_agent import GodAgent
from .state import GameState


class GameOrchestrator:
    """
    负责游戏三阶段的编排。
    - 第1轮：裁判点名第一位发言者
    - 后续轮：解析上一位选手 @提到的名字作为下一发言者（随机兜底）
    """

    def __init__(self, players: list[PlayerAgent], god: GodAgent):
        self.players = players
        self.god = god
        self._player_map = {p.name: p for p in players}
        self._player_names = [p.name for p in players]

    # ── 阶段三：发言者选取 ───────────────────────────────────────────────────

    def first_speaker(self) -> PlayerAgent:
        """随机选取第一位发言者"""
        player = random.choice(self.players)
        GameState.next_speaker_name = player.name
        return player

    def current_speaker(self) -> PlayerAgent:
        """
        返回本轮应发言的选手。
        - 第1轮（round_idx==0）：随机选
        - 后续轮：从 GameState.next_speaker_name 中取
        """
        name = getattr(GameState, "next_speaker_name", "")
        if name and name in self._player_map:
            return self._player_map[name]
        # 兜底：随机选一个
        return random.choice(self.players)

    def parse_next_speaker(self, response: str, current_name: str) -> str:
        """
        从选手发言中解析 @Name 确定下一位发言者。
        兜底：从其他选手中随机选。
        """
        # 匹配 @名字（任意位置，名字在 player_names 列表中）
        for name in self._player_names:
            if re.search(rf"@\s*{re.escape(name)}", response):
                if name != current_name:
                    return name
        # 随机兜底：不能是自己
        others = [n for n in self._player_names if n != current_name]
        return random.choice(others)

    def god_first_announce(self, player_name: str) -> str:
        """第一轮：裁判点名（仅调用一次）"""
        return self.god.announce_speaker(player_name)

    def inject_event(self, event_text: str) -> str:
        """突发事件：裁判播报 + 注入 shared_history"""
        announcement = self.god.inject_event(event_text)
        GameState.add_message("裁判", announcement, role="event")
        return announcement


_global_orch = None

def get_orchestrator(config: dict) -> GameOrchestrator:
    """
    从 config.json 构建 GameOrchestrator。
    """
    global _global_orch
    if _global_orch is None:
        players = [
            PlayerAgent(
                name=p["name"],
                occupation=p["occupation"],
                secret=p["secret"],
                model_name=p["model"],
                avatar=p.get("avatar", "🤖"),
                delay=p.get("delay", 1.0),
            )
            for p in config["players"]
        ]
        god = GodAgent(model_name=config["god"]["model"])
        _global_orch = GameOrchestrator(players, god)

    return _global_orch
