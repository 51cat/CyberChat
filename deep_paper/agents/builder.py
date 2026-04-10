"""
agents/builder.py - Agent 构建与初始化
提供 get_agent() 接口，负责实例化 LangChain LLM 以及
Deep Agent（优先）或 ReAct Agent（兜底）的完整生命周期。
"""

import streamlit as st
from langchain_openai import ChatOpenAI

from deep_paper import load_config
from deep_paper.tools import LOCAL_DB_TOOLS, OPENALEX_TOOLS, TAVILY_TOOLS, ALL_TOOLS
from deep_paper.agents.prompts import (
    LOCAL_DB_SUBAGENT,
    OPENALEX_SUBAGENT,
    TAVILY_SUBAGENT,
    MAIN_AGENT_PROMPT,
    REACT_AGENT_PROMPT,
)

_cfg = load_config()
API_KEY       = _cfg["llm"]["api_key"]
API_BASE      = _cfg["llm"]["api_base"]
MODEL_NAME    = _cfg["llm"]["model_name"]
LLM_TEMPERATURE = _cfg["llm"]["temperature"]


def _build_llm() -> ChatOpenAI:
    """构建 LangChain LLM 实例。"""
    return ChatOpenAI(
        model=MODEL_NAME,
        api_key=API_KEY,
        base_url=API_BASE,
        temperature=LLM_TEMPERATURE,
        streaming=True,
    )


def get_agent(mode: str = "fast"):
    """
    构建并返回 Agent 实例以及 Agent 类型标识。

    Args:
        mode: "fast" 使用 ReAct Agent（单轮直接调用工具），
              "deep" 使用 Deep Agent（多子Agent调度模式）。

    Returns:
        tuple: (agent, agent_type)
            agent_type: "deep" | "react"
    """
    llm = _build_llm()

    if mode == "deep":
        try:
            from deepagents import create_deep_agent

            # 注入工具列表到子 Agent 字典
            local_db = {**LOCAL_DB_SUBAGENT, "tools": LOCAL_DB_TOOLS}
            openalex = {**OPENALEX_SUBAGENT, "tools": OPENALEX_TOOLS}
            tavily = {**TAVILY_SUBAGENT, "tools": TAVILY_TOOLS}

            agent = create_deep_agent(
                model=llm,
                tools=[],  # 主 Agent 通过子 Agent 调度，不直接持有工具
                subagents=[local_db, openalex, tavily],
                system_prompt=MAIN_AGENT_PROMPT,
            )
            return agent, "deep"

        except Exception as e:
            st.warning(f"Deep Agent 初始化失败 ({e})，自动回退到快速搜索模式。")

    # fast 模式 或 deep 回退
    from langgraph.prebuilt import create_react_agent

    agent = create_react_agent(
        model=llm,
        tools=ALL_TOOLS,
        prompt=REACT_AGENT_PROMPT,
    )
    return agent, "react"
