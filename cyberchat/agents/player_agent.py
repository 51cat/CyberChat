"""
player_agent.py — 选手 Agent
"""
import re
import time

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessageChunk, HumanMessage, SystemMessage

from .prompts import PLAYER_SYSTEM, build_player_prompt

# AI 自我暴露词正则
_AI_PATTERN = re.compile(
    r"作为(一个|一名)?AI|作为(一个|一名)?大模型|作为语言模型"
    r"|as an AI|I'?m an AI|我是人工智能|我是AI|作为助手",
    re.IGNORECASE,
)


def _sanitize(text: str) -> str:
    """过滤输出中的 AI 身份暴露词"""
    return _AI_PATTERN.sub("我", text)


class PlayerAgent:
    """
    单个选手 Agent。
    每个选手持有独立的 model 实例，对话历史由外部共享传入。
    """

    def __init__(
        self,
        name: str,
        occupation: str,
        secret: str,
        model_name: str,
        avatar: str = "🤖",
        delay: float = 1.0,
    ):
        self.name = name
        self.occupation = occupation
        self.secret = secret
        self.avatar = avatar
        self.delay = delay

        self._system = SystemMessage(content=PLAYER_SYSTEM)

        self._model = init_chat_model(
            f"openrouter:{model_name}",
            temperature=0.92,
            max_tokens=180,
        )

    def stream_response(
        self,
        shared_history: list[dict],
        all_player_names: list[str],
    ):
        """
        流式生成选手回复，yield str token。

        参数:
          shared_history: 结构化字典列表（已经过滑动窗口截取）
          all_player_names: 所有选手名字列表
        """
        if self.delay > 0:
            time.sleep(self.delay)

        # 构建结构化 JSON prompt
        other_players = [n for n in all_player_names if n != self.name]
        prompt = build_player_prompt(
            player_name=self.name,
            occupation=self.occupation,
            secret=self.secret,
            other_players=other_players,
            conversation_history=shared_history,
        )

        messages = [self._system, HumanMessage(content=prompt)]

        for chunk in self._model.stream(messages):
            if isinstance(chunk, AIMessageChunk) and chunk.content:
                yield _sanitize(chunk.content)
