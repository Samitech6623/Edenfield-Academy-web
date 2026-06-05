/**
 * chat_room.js
 * Handles real-time communication for the EdenField Chat System
 */

(function() {
    const {
        receiver,
        requestUser
    } = window.chatConfig;

    // Safety check: If no receiver is selected, don't initialize
    if (!receiver) return;

    /* ---------- 1. UI Elements ---------- */
    const chatBox = document.getElementById("chat-messages");
    const messageInput = document.getElementById("messageInput");
    const sendForm = document.getElementById("sendForm");
    const chatMenu = document.getElementById("chatMenu");
    const toggleMenu = document.getElementById("toggleMenu");
    const newChatSelect = document.getElementById("new-chat-select");

    /* ---------- 2. WebSocket Initialization ---------- */
    // Use secure protocol if the site is on HTTPS
    const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    const socketUrl = `${protocol}${window.location.host}/ws/chat/${receiver}/`;
    const socket = new WebSocket(socketUrl);

    socket.onopen = () => {
        console.log("WebSocket connected to EdenField Server");
        // We do NOT clear the chatBox here because the Consumer 
        // will push the last 50 messages immediately.
    };

    socket.onclose = (e) => {
        console.error("WebSocket closed unexpectedly. Refresh to reconnect.");
    };

    /* ---------- 3. Message Handling ---------- */
    socket.onmessage = (e) => {
        const data = JSON.parse(e.data);

        // Handle typing notifications
        if (data.type === "typing_status") {
            handleTypingUI(data);
            return;
        }

        // Handle actual messages (History or Live)
        renderMessage(data);
    };

    function renderMessage(data) {
        const isMe = data.sender === requestUser;
        const messageDiv = document.createElement("div");
        messageDiv.className = `message ${isMe ? "sent" : "received"}`;
        
        // Match the keys provided by our AsyncWebsocketConsumer: id, sender, body, timestamp, status
        messageDiv.innerHTML = `
            <strong>${isMe ? "You" : data.sender}</strong>
            <div>
                ${data.body}
                ${isMe ? `<span class="tick ${data.status === 'read' ? 'read' : 'sent'}">✔✔</span>` : ""}
            </div>
            <small>${data.timestamp}</small>
        `;
        
        chatBox.appendChild(messageDiv);
        
        // Auto-scroll to bottom
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    /* ---------- 4. Sending Messages ---------- */
    sendForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const msg = messageInput.value.trim();
        
        if (!msg) return;

        // Send to consumer
        socket.send(JSON.stringify({
            "message": msg
        }));

        messageInput.value = "";
        sendTypingStatus(false);
    });

    /* ---------- 5. Typing Indicator Logic ---------- */
    let typingTimer;
    messageInput.addEventListener("input", () => {
        sendTypingStatus(true);
        clearTimeout(typingTimer);
        typingTimer = setTimeout(() => sendTypingStatus(false), 2000);
    });

    function sendTypingStatus(isTyping) {
        if (socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                "type": "typing",
                "is_typing": isTyping
            }));
        }
    }

    function handleTypingUI(data) {
        let indicator = document.getElementById("typing-indicator");
        
        // Only show if the OTHER person is typing
        if (data.is_typing && data.username !== requestUser) {
            if (!indicator) {
                indicator = document.createElement("div");
                indicator.id = "typing-indicator";
                indicator.className = "typing-text"; // Add this to your CSS
                indicator.style.fontStyle = "italic";
                indicator.style.fontSize = "0.85rem";
                indicator.style.color = "#888";
                indicator.style.padding = "5px 10px";
                indicator.innerText = `${data.username} is typing...`;
                chatBox.appendChild(indicator);
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        } else if (indicator) {
            indicator.remove();
        }
    }

    /* ---------- 6. Navigation & Menu Helpers ---------- */
    // Chat Menu Toggle
    if (chatMenu && toggleMenu) {
        chatMenu.addEventListener("click", (e) => {
            e.stopPropagation();
            toggleMenu.classList.toggle("active");
        });

        document.addEventListener("click", () => {
            toggleMenu.classList.remove("active");
        });
    }

    // Dropdown for new chats
    if (newChatSelect) {
        newChatSelect.addEventListener("change", function() {
            const username = this.value;
            if (username) {
                // Uses the base URL variable defined in the HTML template
                window.location.href = `${window.chatBaseUrl}${username}/`;
            }
        });
    }

})();