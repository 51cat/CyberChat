"""
ui/sidebar.py - 侧边栏 UI 组件
负责渲染左侧数据概览、示例查询按钮组以及会话重置入口。
"""

import streamlit as st

from deep_paper.config import MODEL_NAME
from .styles import SIDEBAR_CSS


# 侧边栏示例查询列表
EXAMPLE_QUERIES = [
    "帮我查一下 Nature Medicine 的影响因子和分区",
    "有哪些中科院1区的Top期刊？",
    "我做的是肺癌免疫治疗相关研究，推荐一些好的期刊",
    "帮我找影响因子大于10的Q1期刊",
    "ONCOLOGY 领域有哪些好的期刊？",
]


def render_sidebar(stats: dict) -> None:
    """
    渲染侧边栏内容。

    Args:
        stats: 数据库统计字典，包含 total / jcr_q1 / cas_1 / top 字段。
    """
    with st.sidebar:
        st.markdown(SIDEBAR_CSS, unsafe_allow_html=True)

        # 标题与状态行
        st.markdown(
            "<div style='font-size: 1rem; font-weight: 700; color: #c0caf5; "
            "margin-bottom: 2px; letter-spacing: 0.5px;'>⬡ 智能选刊助理</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div style='font-size: 0.7rem; color: #565f89; font-family: monospace; "
            f"margin-bottom: 20px;'>STATUS // READY<br>MODEL // {MODEL_NAME}</div>",
            unsafe_allow_html=True,
        )
        st.divider()

        # 数据库统计概览
        st.markdown(
            "<div style='font-size: 0.75rem; color: #7aa2f7; margin-bottom: 15px;'>⎈ DATABASE STATS</div>",
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns(2)
        col1.metric("总期刊数", f"{stats['total']:,}")
        col2.metric("JCR Q1", f"{stats['jcr_q1']:,}")
        col3, col4 = st.columns(2)
        col3.metric("CAS 1区", f"{stats['cas_1']:,}")
        col4.metric("Top 期刊", f"{stats['top']:,}")

        st.divider()

        # 示例查询快捷按钮
        st.markdown(
            "<div style='font-size: 0.75rem; color: #7aa2f7; margin-bottom: 10px;'>⎘ EXAMPLE QUERIES</div>",
            unsafe_allow_html=True,
        )
        for q in EXAMPLE_QUERIES:
            if st.button(q, key=f"ex_{hash(q)}", use_container_width=True):
                st.session_state["pending_query"] = q

        st.divider()
        st.caption("SOURCES: JCR 2024 & CAS 2025 & OpenAlex & Tavily")

        # 重置按钮
        if st.button("↺ 重置会话 / RESET", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
