"""
ui/styles.py - 全局样式与视觉资源
包含应用所有 CSS 注入代码、SVG Avatar 常量。
"""

# ---- SVG Avatars ----
AGENT_AVATAR = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>"""
USER_AVATAR = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>"""

# ---- 全局基础样式 ----
GLOBAL_CSS = """
<style>
    /* 隐藏顶部菜单、Deploy 按钮 */
    #MainMenu {visibility: hidden;}
    .stDeployButton {display:none;}
    header[data-testid="stHeader"] {display: none;}
    
    /* 隐藏侧边栏收起/展开按钮，使其始终展示 */
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="stSidebarCollapseButton"],
    button[data-testid="baseButton-header"] {
        display: none !important;
    }

    /* 强制始终展示侧边栏，防止 iframe 内自动折叠 */
    [data-testid="stSidebar"] {
        min-width: 16rem !important;
        max-width: 16rem !important;
        transform: translateX(0) !important;
        position: relative !important;
        visibility: visible !important;
    }
    [data-testid="stSidebar"] > div {
        visibility: visible !important;
    }

    html, body, .stMarkdown, .stButton {
        font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI",
                     "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei",
                     "Helvetica Neue", Helvetica, Arial, sans-serif !important;
    }
    html, body, .stMarkdown, .stButton, [class*="st-"] {
        font-size: 0.9rem !important;
    }
    .stButton p { font-size: 1.1rem !important; font-weight: 500 !important; }
    
    /* 聊天消息内的按钮（例如重新生成、停止生成）改写为不起眼的小链接样式 */
    .stChatMessage .stButton > button {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: #888 !important;
        padding: 0 !important;
        min-height: unset !important;
        height: auto !important;
        margin-top: 5px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
    }
    .stChatMessage .stButton > button p {
        font-size: 0.75rem !important;
        font-weight: 400 !important;
        margin: 0 !important;
    }
    .stChatMessage .stButton > button:hover p {
        color: #58a6ff !important;
        text-decoration: underline !important;
    }

    /* 将对话框下方的按钮列布局变为左右分布 */
    .stChatMessage [data-testid="stHorizontalBlock"] {
        gap: 0 !important;
        align-items: center !important;
        justify-content: space-between !important;
    }
    .stChatMessage [data-testid="column"] {
        width: auto !important;
        flex: 0 1 auto !important;
        min-width: unset !important;
        padding-right: 0px !important;
    }
    /* 第二列自动拉伸吸收剩余空间，使得内容靠右 */
    .stChatMessage [data-testid="column"]:nth-child(2) {
        flex: 1 1 auto !important;
        display: flex;
        justify-content: flex-end;
    }
    .stChatMessage iframe {
        margin-top: 5px !important;
    }

    .stChatMessage { font-size: 0.9rem !important; }
    .stMarkdown p, .stMarkdown li { font-size: 0.9rem !important; line-height: 1.6 !important; }
    .stMarkdown h1 { font-size: 1.25rem !important; }
    .stMarkdown h2 { font-size: 1.15rem !important; }
    .stMarkdown h3 { font-size: 1.05rem !important; }
    .stChatInput textarea { font-size: 0.9rem !important; }
    code {
        font-family: "JetBrains Mono", Consolas, Monaco, "Courier New", monospace !important;
        font-size: 0.82rem !important;
    }
    .block-container { padding-top: 2rem; }
</style>
"""

# ---- 侧边栏样式 ----
SIDEBAR_CSS = """
<style>
    section[data-testid="stSidebar"] p { font-size: 0.8rem; }

    section[data-testid="stSidebar"] .stButton > button {
        background-color: #1a1e24 !important;
        border: 1px solid #262c36 !important;
        border-radius: 6px !important;
        padding: 0.5rem 0.8rem !important;
        min-height: unset !important;
        justify-content: flex-start !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
        transition: background-color 0.2s ease, border-color 0.2s ease !important;
        width: 100% !important;
    }
    section[data-testid="stSidebar"] .stButton > button p {
        font-size: 0.75rem !important;
        color: #9098a5 !important;
        text-align: left !important;
        white-space: normal !important;
        line-height: 1.4 !important;
        margin: 0 !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: #222830 !important;
        border-color: #3b4352 !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover p,
    section[data-testid="stSidebar"] .stButton > button:active p {
        color: #9098a5 !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.25rem !important;
        color: #c9d1d9 !important;
        font-weight: 600 !important;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.7rem !important;
        color: #7d8590 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
</style>
"""
