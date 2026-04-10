"""
app.py - 智能选刊助理 · Streamlit 入口
职责：页面配置、会话状态管理、聊天主循环与流式输出渲染。
业务逻辑均已拆分至 agents / tools / ui / data 各子模块。
"""

import re
import time
import base64
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
from langchain_core.messages import HumanMessage, AIMessage

from deep_paper import load_config
from deep_paper.data import get_database
from deep_paper.agents import get_agent
from deep_paper.ui import AGENT_AVATAR, USER_AVATAR, GLOBAL_CSS
from deep_paper.ui.sidebar import render_sidebar

_cfg = load_config()
MODEL_NAME = _cfg["llm"]["model_name"]

# ============================================================
# 页面配置（必须为第一个 Streamlit 调用）
# ============================================================
st.set_page_config(
    page_title="期刊深度搜索助手🐱",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# ============================================================
# 数据预加载（带缓存）
# ============================================================
@st.cache_data(show_spinner=False)
def _load_stats() -> dict:
    db = get_database()
    return {
        "total": len(db),
        "jcr_q1": int((db["JCR分区"] == "Q1").sum()) if "JCR分区" in db.columns else 0,
        "cas_1": int((db["CAS分区"] == 1).sum()) if "CAS分区" in db.columns else 0,
        "top": int(db["是否Top"].sum()) if "是否Top" in db.columns else 0,
    }


# ============================================================
# 侧边栏
# ============================================================
render_sidebar(_load_stats())


# ============================================================
# 主区域头部
# ============================================================
col1, col2 = st.columns([4, 1], vertical_alignment="bottom")
with col1:
    st.markdown("## ⬡ 期刊深度搜索助手🐱")
    st.caption(f"JCR / CAS / OpenAlex / Tavily 多源检索 \\ `{MODEL_NAME}`")
with col2:
    if st.button("↺ 重置会话", key="reset_main", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

st.divider()


# ============================================================
# 会话状态初始化
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

# 渲染历史消息
for i, msg in enumerate(st.session_state.messages):
    avatar = USER_AVATAR if msg["role"] == "user" else AGENT_AVATAR
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            # 我们用一个单独的容器包装以便后续使用 CSS 定位
            with st.container():
                col_regen, col_copy = st.columns([1, 1], vertical_alignment="center")
                
                with col_regen:
                    if st.button("↺ 重新生成", key=f"regen_{i}"):
                        # 抓取当前 assistant 前一次的 user message
                        user_msg = st.session_state.messages[i-1]["content"] if i > 0 else ""
                        st.session_state.pending_query = user_msg
                        st.session_state.messages = st.session_state.messages[:max(0, i-1)]
                        st.rerun()
                        
                with col_copy:
                    text_b64 = base64.b64encode(msg["content"].encode('utf-8')).decode('utf-8')
                    copy_html = f"""
                    <style>
                    body {{ margin: 0; padding: 0; display: flex; align-items: center; justify-content: flex-end; overflow: hidden; background: transparent; }}
                    button {{
                        background: transparent; border: none; color: #888;
                        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif;
                        font-size: 0.75rem; cursor: pointer; outline: none; padding: 0; margin: 0; height: auto; line-height: 1.5;
                    }}
                    button:hover {{ color: #58a6ff; text-decoration: underline; }}
                    </style>
                    <button onclick="
                        const copyIcon = '\u003csvg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'15\\' height=\\'15\\' viewBox=\\'0 0 24 24\\' fill=\\'none\\' stroke=\\'currentColor\\' stroke-width=\\'2\\' stroke-linecap=\\'round\\' stroke-linejoin=\\'round\\'\u003e\u003crect x=\\'9\\' y=\\'9\\' width=\\'13\\' height=\\'13\\' rx=\\'2\\' ry=\\'2\\'\u003e\u003c/rect\u003e\u003cpath d=\\'M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1\\'\u003e\u003c/path\u003e\u003c/svg\u003e';
                        const checkIcon = '\u003csvg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'15\\' height=\\'15\\' viewBox=\\'0 0 24 24\\' fill=\\'none\\' stroke=\\'currentColor\\' stroke-width=\\'2\\' stroke-linecap=\\'round\\' stroke-linejoin=\\'round\\'\u003e\u003cpolyline points=\\'20 6 9 17 4 12\\'\u003e\u003c/polyline\u003e\u003c/svg\u003e';
                        const text = decodeURIComponent(escape(window.atob('{text_b64}')));
                        const btn = this;
                        const onSuccess = () => {{
                            btn.innerHTML = checkIcon;
                            btn.style.color = '#58a6ff';
                            setTimeout(() => {{ btn.innerHTML = copyIcon; btn.style.color = ''; }}, 2000);
                        }};
                        const parentFallback = (t) => {{
                            try {{
                                const ta = window.parent.document.createElement('textarea');
                                ta.value = t;
                                ta.style.cssText = 'position:fixed;opacity:0;left:-9999px;top:-9999px';
                                window.parent.document.body.appendChild(ta);
                                ta.focus();
                                ta.select();
                                const ok = window.parent.document.execCommand('copy');
                                window.parent.document.body.removeChild(ta);
                                if (ok) {{ onSuccess(); return; }}
                            }} catch(e) {{}}
                            localFallback(t);
                        }};
                        const localFallback = (t) => {{
                            try {{
                                const ta = document.createElement('textarea');
                                ta.value = t;
                                ta.style.cssText = 'position:fixed;opacity:0;left:-9999px;top:-9999px';
                                document.body.appendChild(ta);
                                ta.focus();
                                ta.select();
                                document.execCommand('copy');
                                onSuccess();
                                document.body.removeChild(ta);
                            }} catch(e) {{}}
                        }};
                        (async () => {{
                            try {{
                                await window.parent.navigator.clipboard.writeText(text);
                                onSuccess(); return;
                            }} catch(e) {{}}
                            try {{
                                await navigator.clipboard.writeText(text);
                                onSuccess(); return;
                            }} catch(e) {{}}
                            parentFallback(text);
                        }})();
                    ">
                        <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                    </button>
                    """
                    components.html(copy_html, height=30)


# ============================================================
# 辅助函数
# ============================================================
def _clean_think_tags(text: str) -> str:
    """移除大模型输出中的 <think>...</think> 推理标签。"""
    text = re.sub(r"<think>.*?</think>\n*", "", text, flags=re.DOTALL)
    text = re.sub(r"<think>.*$", "", text, flags=re.DOTALL)
    return text.strip()


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


# ============================================================
# 处理用户输入
# ============================================================
user_input = st.chat_input("请输入查询或描述您的论文研究背景 //")

# 处理侧边栏示例查询注入
if "pending_query" in st.session_state:
    user_input = st.session_state.pop("pending_query")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(user_input)

    agent, agent_type = get_agent(mode=st.session_state.get("search_mode", "deep"))

    # 构建 Agent 消息历史
    agent_messages = []
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            agent_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            agent_messages.append(AIMessage(content=msg["content"]))

    with st.chat_message("assistant", avatar=AGENT_AVATAR):
        # ── 状态行 + 日志（无框，小字直接展示） ──
        col_status, col_stop = st.columns([8, 2], vertical_alignment="center")
        with col_status:
            status_placeholder = st.empty()
            status_placeholder.caption("💭 LLM thinking...")
        with col_stop:
            stop_placeholder = st.empty()
            if stop_placeholder.button("⏹ 停止生成", key="stop_gen"):
                st.stop()
                
        log_placeholder = st.empty()     # 日志渲染区（无边框）
        response_placeholder = st.empty()
        full_response = ""

        log_events = []
        tool_call_count = 0
        t_start = time.time()

        # 用于捕获流式输出的 LangGraph 节点名称
        LLM_NODES = {
            "agent", "model", "llm", "model_request",
            "local-db-agent", "openalex-agent", "tavily-search-agent",
        }

        def _render_logs(is_done=False):
            """渲染原始 HTML 小字日志，带有平滑的不确定态 CSS 进度栏以反映底层 LLM 动态遍历本质。"""
            # 采用纯 CSS 动画进度条与旋转 Spinner，脱离后端阻塞持续渲染
            css = """
            <style>
            @keyframes load-bar {
                0% { left: -30%; width: 30%; }
                50% { left: 100%; width: 30%; }
                100% { left: -30%; width: 30%; }
            }
            @keyframes spin { 100% { transform: rotate(360deg); } }
            .prog-cont { width: 120px; background: #333; height: 4px; border-radius: 2px; overflow: hidden; position: relative; display: inline-block; margin-left: 10px; }
            .prog-bar { position: absolute; height: 100%; background: #58a6ff; animation: load-bar 1.5s infinite linear; }
            .spinner-icon {
                width: 10px; height: 10px;
                border: 2px solid rgba(88,166,255,0.2);
                border-top: 2px solid #58a6ff;
                border-radius: 50%;
                animation: spin 0.8s linear infinite;
                margin-right: 6px;
                display: inline-block;
            }
            </style>
            """
            
            if not is_done:
                prog_html = f'{css}<div style="padding-top:6px;color:#58a6ff;display:flex;align-items:center;"><div class="spinner-icon"></div> Executing... <div class="prog-cont"><div class="prog-bar"></div></div></div>'
            else:
                prog_html = f'<div style="padding-top:6px;color:#3fb950;display:flex;align-items:center;">✔ Complete   <div style="width:120px; background:#3fb950; height:4px; border-radius:2px; display:inline-block; margin-left:10px;"></div></div>'

            items = "".join(
                f'<div style="padding:0;white-space:pre-wrap;word-wrap:break-word;">{l}</div>'
                for l in log_events
            )

            html = (
                f'<div style="'
                f'max-height:160px;overflow-y:auto;'
                f'display:flex;flex-direction:column-reverse;'
                f'scrollbar-width:thin;'
                f'">'
                f'<div style="'
                f'font-family:ui-monospace,SFMono-Regular,Menlo,monospace;'
                f'font-size:0.65rem;line-height:1.4;color:#888;'
                f'">{items}{prog_html}</div>'
                f'</div>'
            )
            log_placeholder.markdown(html, unsafe_allow_html=True)

        def _log(text: str):
            ts = _ts()
            log_events.append(f'<span style="color:#555;margin-right:4px;">{ts}</span>{text}')
            _render_logs()

        _log("⚡ Systems Initialized")

        try:
            stream_kwargs = {
                "input": {"messages": agent_messages},
                "stream_mode": ["messages", "updates"],
            }
            if agent_type == "deep":
                stream_kwargs["subgraphs"] = True

            for stream_item in agent.stream(**stream_kwargs):
                # v1 格式：subgraphs=True → (ns, mode, data)；否则 → (mode, data)
                if agent_type == "deep":
                    ns, mode, chunk = stream_item
                else:
                    mode, chunk = stream_item
                    ns = ()

                # --- 流式 LLM Token ---
                if mode == "messages":
                    msg_chunk, metadata = chunk
                    node = metadata.get("langgraph_node", "")

                    is_main = (ns == () or ns == tuple())
                    if node in LLM_NODES and is_main:
                        if (
                            hasattr(msg_chunk, "content")
                            and isinstance(msg_chunk.content, str)
                            and msg_chunk.content
                        ):
                            full_response += msg_chunk.content
                            display = _clean_think_tags(full_response)
                            response_placeholder.markdown(display + "▌")

                # --- 节点更新事件 ---
                elif mode == "updates":
                    is_subagent = bool(ns)
                    source_tag = "[Sub Agent] " if is_subagent else ""

                    for node_name, node_output in chunk.items():
                        if not isinstance(node_output, dict):
                            continue
                        messages = node_output.get("messages", [])

                        # ── LLM 节点：捕获工具调用 ──
                        if node_name in LLM_NODES:
                            for m in messages:
                                if hasattr(m, "tool_calls") and m.tool_calls:
                                    for tc in m.tool_calls:
                                        name = tc.get("name", tc.get("type", "unknown"))
                                        args = tc.get("args", {})

                                        if name == "task":
                                            desc = args.get("description", "") if isinstance(args, dict) else ""
                                            subagent_type = args.get("subagent_type", "") if isinstance(args, dict) else ""
                                            brief_desc = desc[:80] + "..." if len(desc) > 80 else desc
                                            _log(f"Send to SubAgent: <b>{subagent_type}</b> — {brief_desc}")
                                            continue

                                        tool_call_count += 1
                                        args_str = ", ".join(
                                            f'{k}="{v}"' if isinstance(v, str) else f"{k}={v}"
                                            for k, v in args.items()
                                        ) if isinstance(args, dict) else str(args)
                                        if len(args_str) > 80:
                                            args_str = args_str[:77] + "..."
                                        _log(f"{source_tag}Tool Call: <b>{name}</b>({args_str})")

                        # ── 工具节点：捕获执行结果 ──
                        elif node_name == "tools":
                            for m in messages:
                                content = getattr(m, "content", "")
                                tool_name = getattr(m, "name", "tool")

                                if tool_name == "task":
                                    brief = str(content).replace("\n", " ")
                                    if len(brief) > 120:
                                        brief = brief[:117] + "..."
                                    _log(f"SubAgent Completed: {brief}")
                                    continue

                                if content:
                                    brief = str(content).replace("\n", " ")
                                    if len(brief) > 120:
                                        brief = brief[:117] + "..."
                                    _log(f"{source_tag}<b>{tool_name}</b> Return: {brief}")

            # ── 最终渲染 ──
            elapsed = time.time() - t_start

            if full_response:
                final_text = _clean_think_tags(full_response)
                response_placeholder.markdown(final_text)
                full_response = final_text
            else:
                full_response = "抱歉，我暂时无法处理这个请求。请稍后重试。"
                response_placeholder.markdown(full_response)

            # 完成后展示终端 Complete，并稍微延迟后再清理
            _render_logs(is_done=True)
            time.sleep(1.0)
            log_placeholder.empty()
            status_placeholder.caption(
                f"Done | {tool_call_count} tools · {elapsed:.1f}s"
            )

        except Exception as e:
            elapsed = time.time() - t_start
            full_response = f"Error: {str(e)}"
            response_placeholder.markdown(f"⨯ {full_response}")
            log_placeholder.empty()
            status_placeholder.caption(f"⨯ Error | {elapsed:.1f}s")

    st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.rerun()

