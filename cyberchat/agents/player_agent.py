"""
player_agent.py — 选手 Agent
"""
import re
import time

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessageChunk, BaseMessage, HumanMessage, SystemMessage

from .prompts import PLAYER_SYSTEM

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
        self.avatar = avatar
        self.delay = delay

        self._system = SystemMessage(content=PLAYER_SYSTEM.format(
            player_name=name,
            occupation=occupation,
            secret_instruction=secret,
        ))

        self._model = init_chat_model(
            f"openrouter:{model_name}",
            temperature=0.92,
            max_tokens=180,
        )

    def stream_response(
        self,
        shared_history: list[BaseMessage],
        god_message: str,
    ):
        """
        流式生成选手回复，yield str token。
        """
        if self.delay > 0:
            time.sleep(self.delay)

        messages = [self._system] + list(shared_history) + [HumanMessage(content=god_message)]

        for chunk in self._model.stream(messages):
            if isinstance(chunk, AIMessageChunk) and chunk.content:
                yield _sanitize(chunk.content)
