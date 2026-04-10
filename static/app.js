document.addEventListener("DOMContentLoaded", async () => {
    // Elements
    const chatBox = document.getElementById("chatBox");
    const placeholderMsg = document.getElementById("placeholderMsg");
    const playersList = document.getElementById("playersList");
    const startBtn = document.getElementById("startBtn");
    const stopBtn = document.getElementById("stopBtn");
    const injectBtn = document.getElementById("injectBtn");
    const topicInput = document.getElementById("topicInput");
    const eventInput = document.getElementById("eventInput");

    // Colors
    const PLAYER_COLORS = {
        "裁判": "#f1c40f",
        "系统": "#e74c3c"
    };
    const AVAILABLE_COLORS = ["#ff79c6", "#8be9fd", "#50fa7b", "#bd93f9", "#ffb86c", "#ff5555", "#f1fa8c"];
    let colorIndex = 0;

    const getColor = (name) => {
        if (PLAYER_COLORS[name]) return PLAYER_COLORS[name];
        PLAYER_COLORS[name] = AVAILABLE_COLORS[colorIndex % AVAILABLE_COLORS.length];
        colorIndex++;
        return PLAYER_COLORS[name];
    };

    let config = null;
    let eventSource = null;
    let currentBubble = null;
    let currentCursor = null;
    let currentText = "";

    // Load config to show players
    try {
        const res = await fetch("/config");
        config = await res.json();
        
        config.players.forEach(p => {
            const li = document.createElement("li");
            const color = getColor(p.name);
            li.innerHTML = `<span style="color: ${color}">${p.avatar} ${p.name}</span> - ${p.occupation}`;
            playersList.appendChild(li);
        });
    } catch (e) {
        console.error("Failed to load config", e);
    }

    // Determine Avatar
    const getAvatar = (name) => {
        if (name === "裁判") return "⚖️";
        if (name === "系统") return "⚡";
        if (config) {
            const p = config.players.find(x => x.name === name);
            if (p) return p.avatar;
        }
        return "🤖";
    };

    // Scroll to bottom
    const scrollToBottom = () => {
        chatBox.scrollTop = chatBox.scrollHeight;
    };

    // Create a new chat bubble
    const createBubble = (speaker, role, initialText = "") => {
        if (placeholderMsg) placeholderMsg.style.display = 'none';

        const color = getColor(speaker);
        const avatar = getAvatar(speaker);

        const msgDiv = document.createElement('div');
        msgDiv.className = 'message';

        // Avatar
        const avDiv = document.createElement('div');
        avDiv.className = 'avatar';
        avDiv.textContent = avatar;

        // Content
        const contDiv = document.createElement('div');
        contDiv.className = 'msg-content';

        const nameSpan = document.createElement('span');
        nameSpan.className = 'speaker-name';
        nameSpan.style.color = color;
        nameSpan.textContent = `[${speaker}]`;
        if (role === 'god') nameSpan.textContent += ' 📢';

        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'bubble';
        bubbleDiv.textContent = initialText;

        contDiv.appendChild(nameSpan);
        contDiv.appendChild(bubbleDiv);

        msgDiv.appendChild(avDiv);
        msgDiv.appendChild(contDiv);

        chatBox.appendChild(msgDiv);
        scrollToBottom();

        return bubbleDiv;
    };

    // Setup SSE Connection
    const connectSSE = () => {
        if (eventSource) eventSource.close();
        
        eventSource = new EventSource("/stream");
        
        eventSource.addEventListener("init", (e) => {
            const history = JSON.parse(e.data);
            chatBox.innerHTML = '';
            if (history.length === 0) {
                if (placeholderMsg) {
                    chatBox.appendChild(placeholderMsg);
                    placeholderMsg.style.display = 'block';
                }
            } else {
                history.forEach(msg => {
                    createBubble(msg.speaker, msg.role, msg.content);
                });
            }
        });

        eventSource.addEventListener("message_start", (e) => {
            const data = JSON.parse(e.data);
            currentBubble = createBubble(data.speaker, data.role);
            currentText = "";
            
            // Show typing indicator
            currentCursor = document.createElement('span');
            currentCursor.className = 'typing-indicator';
            currentCursor.textContent = '正在输入中...';
            currentBubble.appendChild(currentCursor);
        });

        // Token stream listener disabled - waiting for full message at end

        eventSource.addEventListener("message_end", (e) => {
            if (!currentBubble) return;
            const data = JSON.parse(e.data);
            
            // Remove cursor
            if (currentCursor) {
                currentBubble.removeChild(currentCursor);
                currentCursor = null;
            }
            
            // Replace with clean text (no @ mentions)
            if (data.clean_text) {
                currentBubble.textContent = data.clean_text;
            }
            
            currentBubble = null;
            currentText = "";
            scrollToBottom();
        });

        eventSource.addEventListener("error", (e) => {
            console.error("SSE Error:", e);
        });
    };

    // Control buttons
    startBtn.addEventListener('click', async () => {
        const topic = topicInput.value.trim();
        if (!topic) {
            alert("请先输入一个话题！");
            return;
        }
        
        // Clear chat box for new game
        chatBox.innerHTML = '';
        currentBubble = null;
        
        await fetch("/start", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ topic })
        });
    });

    stopBtn.addEventListener('click', async () => {
        await fetch("/stop", { method: "POST" });
        if (currentCursor && currentBubble) {
            currentBubble.removeChild(currentCursor);
            currentCursor = null;
        }
    });

    // Start SSE connection
    connectSSE();
});
