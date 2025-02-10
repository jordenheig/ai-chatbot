class ChatInterface {
    constructor() {
        this.currentSession = null;
        this.messageQueue = [];
        this.isProcessing = false;

        // Initialize elements
        this.chatList = document.getElementById('chatList');
        this.chatMessages = document.getElementById('chatMessages');
        this.messageForm = document.getElementById('messageForm');
        this.uploadForm = document.getElementById('uploadForm');
        this.newChatButton = document.getElementById('newChat');

        // Bind event listeners
        this.messageForm.addEventListener('submit', this.handleMessageSubmit.bind(this));
        this.uploadForm.addEventListener('submit', this.handleFileUpload.bind(this));
        this.newChatButton.addEventListener('click', this.createNewChat.bind(this));

        // Load initial chat sessions
        this.loadChatSessions();
    }

    async loadChatSessions() {
        try {
            const response = await fetch('/api/v1/chat/sessions');
            const sessions = await response.json();
            this.renderChatList(sessions);
        } catch (error) {
            console.error('Error loading chat sessions:', error);
        }
    }

    renderChatList(sessions) {
        this.chatList.innerHTML = sessions.map(session => `
            <div class="p-2 hover:bg-gray-100 cursor-pointer" 
                 onclick="chat.switchSession(${session.id})">
                <div class="font-medium">${session.title}</div>
                <div class="text-sm text-gray-500">
                    ${new Date(session.created_at).toLocaleString()}
                </div>
            </div>
        `).join('');
    }

    async createNewChat() {
        try {
            const response = await fetch('/api/v1/chat/sessions', {
                method: 'POST'
            });
            const session = await response.json();
            this.switchSession(session.id);
            this.loadChatSessions();
        } catch (error) {
            console.error('Error creating new chat:', error);
        }
    }

    async switchSession(sessionId) {
        this.currentSession = sessionId;
        this.chatMessages.innerHTML = '';
        
        try {
            const response = await fetch(`/api/v1/chat/sessions/${sessionId}/messages`);
            const messages = await response.json();
            messages.forEach(msg => this.addMessage(msg.role, msg.content));
        } catch (error) {
            console.error('Error loading messages:', error);
        }
    }

    async handleMessageSubmit(event) {
        event.preventDefault();
        if (!this.currentSession) {
            await this.createNewChat();
        }

        const messageInput = this.messageForm.querySelector('#message');
        const message = messageInput.value.trim();
        if (!message) return;

        // Add user message to chat
        this.addMessage('user', message);
        messageInput.value = '';

        try {
            // Send message to server
            const response = await fetch('/api/v1/chat/messages', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.currentSession
                })
            });

            // Handle streaming response
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let assistantMessage = '';

            while (true) {
                const {value, done} = await reader.read();
                if (done) break;
                
                const text = decoder.decode(value);
                assistantMessage += text;
                this.updateAssistantMessage(assistantMessage);
            }
        } catch (error) {
            console.error('Error sending message:', error);
        }
    }

    async handleFileUpload(event) {
        event.preventDefault();
        const formData = new FormData(this.uploadForm);
        
        try {
            const response = await fetch('/api/v1/documents/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            this.pollDocumentStatus(result.document_id);
        } catch (error) {
            console.error('Error uploading file:', error);
        }
    }

    async pollDocumentStatus(documentId) {
        const statusElement = document.createElement('div');
        statusElement.className = 'text-sm text-gray-500 mt-2';
        this.uploadForm.appendChild(statusElement);

        while (true) {
            try {
                const response = await fetch(`/api/v1/documents/status/${documentId}`);
                const status = await response.json();
                
                statusElement.textContent = `Processing status: ${status.status}`;
                
                if (status.status === 'completed' || status.status === 'failed') {
                    break;
                }
                
                await new Promise(resolve => setTimeout(resolve, 2000));
            } catch (error) {
                console.error('Error polling status:', error);
                break;
            }
        }
    }

    addMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `p-3 rounded-lg mb-2 ${
            role === 'user' ? 'bg-blue-100 ml-auto' : 'bg-gray-100'
        }`;
        messageDiv.style.maxWidth = '80%';
        messageDiv.textContent = content;
        this.chatMessages.appendChild(messageDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    updateAssistantMessage(content) {
        const lastMessage = this.chatMessages.lastElementChild;
        if (lastMessage && !lastMessage.classList.contains('bg-blue-100')) {
            lastMessage.textContent = content;
        } else {
            this.addMessage('assistant', content);
        }
    }
}

// Initialize chat interface
const chat = new ChatInterface(); 