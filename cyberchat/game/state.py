"""
state.py — 游戏全局状态（纯数据，不依赖 LangChain 类型）
"""

# 滑动窗口：传给模型的对话历史最多保留最近 N 条
MAX_HISTORY_ROUNDS = 15


class GameState:
    is_running = False
    topic = ""
    round_idx = 0
    shared_history: list = []       # 纯字典列表: [{"speaker": str, "type": str, "content": str}]
    display_messages: list = []
    topic_announced = False
    next_speaker_name = None

    @staticmethod
    def add_message(speaker: str, content: str, role: str):
        """
        存入一条消息。
        - shared_history: 结构化字典，用于构建 JSON prompt 传给模型
        - display_messages: 传给前端展示
        """
        # 存入结构化历史（用于传给模型的 JSON）
        GameState.shared_history.append({
            "speaker": speaker,
            "type": role,       # "god" | "player" | "event"
            "content": content,
        })

        # 存盘展示历史（传给前端的）
        GameState.display_messages.append({
            "speaker": speaker,
            "content": content,
            "role": role,
        })

    @staticmethod
    def get_recent_history() -> list[dict]:
        """返回最近 MAX_HISTORY_ROUNDS 条对话记录（滑动窗口）"""
        return GameState.shared_history[-MAX_HISTORY_ROUNDS:]
