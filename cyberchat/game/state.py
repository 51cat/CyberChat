from langchain_core.messages import AIMessage, SystemMessage


class GameState:
    is_running = False
    topic = ""
    round_idx = 0
    shared_history: list = []
    display_messages: list = []
    topic_announced = False
    next_speaker_name = None

    @staticmethod
    def add_message(speaker: str, content: str, role: str):
        # 存盘历史（传给模型的）
        if role != "event":
            if role == "god":
                msg_obj = SystemMessage(content=content)
            else:
                msg_obj = AIMessage(content=content, name=speaker)
            GameState.shared_history.append(msg_obj)

        # 存盘展示历史（传给前端的）
        GameState.display_messages.append({
            "speaker": speaker,
            "content": content,
            "role": role,
        })
