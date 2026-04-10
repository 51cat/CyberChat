# 🤖 CyberChat · 赛博觉醒

![CyberChat](https://img.shields.io/badge/Status-Active-brightgreen) ![Python 3](https://img.shields.io/badge/Python-3.x-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-teal) ![LangChain](https://img.shields.io/badge/LangChain-Integration-orange)

**CyberChat** 是一个基于多智能体（Multi-Agent）大模型的硬核角色扮演与社交推理框架。在这个赛博空间中，多个配置了独特“系统秘密”的大语言模型（通过 OpenRouter 接入）会同台飙戏，隐藏在人群中参与辩论、聊天或是找茬。

用户可以自定义裁判（上帝）角色和各种奇葩的玩家人设（比如“暴躁码农”、“职场老油条”、“型月考据党”以及“宇宙能量导师”等），为它们配置不同的思维模式和隐藏任务。在这里，AI 会极力模仿人类的极低素质和非理性行为以图通过图灵测试，一场极具乐子和张力的“赛博找茬”就此展开。

## 🌟 核心特色

- **🎭 高自由度角色定制**: 通过 `config.json` 热更角色名字、职业、人设暗号甚至专属 Emoji 头像，配置即改即生效。
- **🧠 混合模型对战**: 每个角色可以独立配置不同的大语言模型（如 `gpt-4o`, `gemini-2.5-pro`, `deepseek-v3.2` 等），验证哪家厂商的模型“演技”最精湛、最会整活。
- **⚡ 流畅的实时交互**: 采用 FastAPI 提供后端服务与 SSE (Server-Sent Events) 支持，搭配极简清爽的 Web 前端，实现低延迟的打字机级联式多角色连贯会话。
- **🛠️ 终极 Prompt 演练场**: 测试在极端设定下，当前最强的大模型能否领悟诸如“抽象烂梗”、“阴阳怪气”、“中式人情世故”等纯正的复杂人类社交概念。

## 🚀 快速开始

### 1. 环境准备

确保您的本地环境已有 Python 3.x，然后安装所需的底层依赖：

```bash
pip install -r requirements.txt
pip install fastapi uvicorn
```

### 2. 配置环境变量

项目依赖 OpenRouter 进行多阵营模型的路由调度。
请将根目录下的 `.env.example` 复制或重命名为 `.env`，填入你的 API Key：

```env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxx
```

### 3. DIY 你的对局剧本 (`config.json`)

打开 `config.json`，配置属于你的“赛博舞台”。你可以增加或修改玩家 (`players`) 和裁判 (`god`)。支持调整的关键字段如下：
- `name`: 角色昵称
- `occupation`: 职业定位与头衔
- `secret`: 隐藏人设与阴谋设定（核心的扮演 Prompt）
- `model`: 接入的具体模型 ID（需能在 OpenRouter 上调用）
- `avatar`: 头像 Emoji 符号
- `delay`: 每回合发言延迟缓冲（辅助模拟人类正在输入的感觉）

*提示：配置实时生效，你完全可以一边挂着服务开战一边调整人设词，后端服务会自动热重载！*

### 4. 启动服务

使用以下方式启动后台进程：

```bash
python server.py
```

服务将会在 `http://0.0.0.0:8501` 启动。打开浏览器访问该地址即可加载玩家大厅与开始对决界面。

## 📂 项目结构

```text
CyberChat/
├── server.py              # FastAPI 后台服务端（含主循环、SSE分发与路由机制）
├── app.py                 # Streamlit 原型版（基于 UI 框架的原版/备用前端）
├── config.json            # 动态角色与对局配置数据源
├── requirements.txt       # 核心 Python 基础包依赖
├── .env.example           # 环境变量示例模板
├── cyberchat/
│   ├── game/
│   │   ├── orchestrator.py # Multi-Agent 编排与 LangChain 调用、规则调度管理
│   │   └── state.py        # 全局线程安全的游戏状态树及历史记录缓冲
│   └── ui/                 # Streamlit 下依赖的样板代码
└── static/                # 新版 Web 前端静态资源 (index.html, style.css, app.js 等)
```

## 🤝 参与贡献

我们欢迎各位开发者提供具有天马行空脑洞的角色设定配置集（config 模板），或是提交 Pull Request 优化流式输出性能和增加更长线的本地记忆管理机制。

## 📄 授权协议

本项目基于 MIT 协议开源。
