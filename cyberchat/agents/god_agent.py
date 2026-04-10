"""
god_agent.py — 裁判 Agent（The God / THE GOD）
负责话题广播、点名、突发事件注入。
"""
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage

from .prompts import GOD_SYSTEM


class GodAgent:
    """
    裁判 Agent。
    使用轻量级模型（gpt-4o-mini），快速响应，不参与游戏内容。
    """

    def __init__(self, model_name: str = "openai/gpt-4o-mini"):
        self._model = init_chat_model(
            f"openrouter:{model_name}",
            temperature=0.7,
            max_tokens=80,
        )
        self._system = SystemMessage(content=GOD_SYSTEM)

    def _invoke(self, user_msg: str) -> str:
        result = self._model.invoke([self._system, HumanMessage(content=user_msg)])
        return result.content.strip() if isinstance(result.content, str) else ""

    def broadcast_topic(self, topic: str) -> str:
        """将用户注入的话题包装成裁判播报语气"""
        return self._invoke(
            f"请把这个话题广播给所有选手，渲染一下气氛：「{topic}」"
        )

    def announce_speaker(self, player_name: str) -> str:
        """点名某个选手发言"""
        return self._invoke(f"现在点名「{player_name}」发言")

    def inject_event(self, event: str) -> str:
        """注入突发事件干扰"""
        return self._invoke(
            f"突然发生了一件事，请以裁判口吻播报给所有人：「{event}」"
        )
