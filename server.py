import json
import os
import re
from pathlib import Path
from queue import Queue, Empty
from typing import Any

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

from cyberchat.game.orchestrator import get_orchestrator
from cyberchat.game.state import GameState

load_dotenv()

app = FastAPI(title="CyberChat Server")

# Serve static files
static_dir = Path(__file__).parent / "static"
if not static_dir.exists():
    static_dir.mkdir()
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

def load_config():
    with open(Path(__file__).parent / "config.json", encoding="utf-8") as f:
        return json.load(f)

# A simple global queue to manage server-sent events for all connected clients.
# In a real app we'd handle multi-client pub-sub. For this demo, a simple queue or just broadcasting from GameState works.
subs = []

def broadcast(event_type: str, data: Any):
    msg = f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
    for q in subs:
        q.put(msg)

def strip_at(text: str) -> str:
    return re.sub(r'@\s*\S+', '', text).strip()

# Run the game loop in a background thread
import threading
import time

class GameRunner:
    def __init__(self):
        self.running = False
        self.thread = None

    def start(self, topic: str):
        if self.running:
            self.stop()
            # Wait for the old thread to exit cleanly
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=1.0)
        
        # Reset GameState
        GameState.is_running = True
        GameState.topic = topic
        GameState.round_idx = 0
        GameState.shared_history = []
        GameState.display_messages = []
        GameState.topic_announced = False
        GameState.next_speaker_name = None

        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        GameState.is_running = False

    def _run_loop(self):
        try:
            orch = get_orchestrator(load_config())
            
            # Broadcast topic
            announcement = orch.god.broadcast_topic(GameState.topic)
            GameState.topic_announced = True
            
            # Send message to clients
            broadcast("message_start", {"speaker": "裁判", "role": "god"})
            time.sleep(1.0) # mock thinking time
            broadcast("message_end", {"speaker": "裁判", "role": "god", "clean_text": announcement})
            GameState.add_message("裁判", announcement, role="god")

            while self.running:
                is_first = (GameState.round_idx == 0)

                if is_first:
                    speaker = orch.first_speaker()
                    god_notice = orch.god_first_announce(speaker.name)
                    
                    broadcast("message_start", {"speaker": "裁判", "role": "god"})
                    time.sleep(0.5)
                    broadcast("message_end", {"speaker": "裁判", "role": "god", "clean_text": god_notice})
                    GameState.add_message("裁判", god_notice, role="god")
                    speaker_input = god_notice
                else:
                    speaker = orch.current_speaker()
                    if not GameState.shared_history:
                        speaker_input = ""
                    else:
                        speaker_input = GameState.shared_history[-1].content
                
                broadcast("message_start", {"speaker": speaker.name, "role": "player"})
                
                full_text = ""
                # Call LangChain stream_response
                for token in speaker.stream_response(GameState.shared_history, speaker_input):
                    if not self.running:
                        break
                    full_text += token
                    # 取消流式推送，前端等待全部获取
                    # broadcast("token", {"token": token})

                if not self.running:
                    break

                # Parse @ mentions before adding to history
                next_name = orch.parse_next_speaker(full_text, speaker.name)
                clean_text = strip_at(full_text)
                
                # Signal frontend the full text is done, and send clean text to replace
                broadcast("message_end", {"speaker": speaker.name, "role": "player", "clean_text": clean_text})

                GameState.add_message(speaker.name, clean_text, role="player")
                GameState.next_speaker_name = next_name
                GameState.round_idx += 1
                
                time.sleep(0.5)

        except Exception as e:
            print(f"Game error: {e}")
            broadcast("error", {"msg": str(e)})
            self.running = False

runner = GameRunner()

@app.get("/")
def read_root():
    runner.stop()
    GameState.topic = ""
    GameState.round_idx = 0
    GameState.shared_history = []
    GameState.display_messages = []
    GameState.topic_announced = False
    GameState.next_speaker_name = None
    with open(static_dir / "index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/stream")
def sse_stream(request: Request):
    q = Queue()
    subs.append(q)
    
    # Use async_generator explicitly
    return StreamingResponse(async_generator(request, q), media_type="text/event-stream")

async def async_generator(request: Request, q: Queue):
    yield f"event: init\ndata: {json.dumps(GameState.display_messages, ensure_ascii=False)}\n\n"
    import asyncio
    while True:
        if await request.is_disconnected():
            subs.remove(q)
            break
        try:
            # Non-blocking get for asyncio
            msg = await asyncio.to_thread(q.get, timeout=0.5)
            yield msg
        except Empty:
            continue

class StartReq(BaseModel):
    topic: str

@app.post("/start")
def start_game(req: StartReq):
    runner.start(req.topic)
    return {"status": "ok"}

@app.post("/stop")
def stop_game():
    runner.stop()
    return {"status": "ok"}

@app.get("/config")
def get_config():
    return load_config()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8501, reload=True)
