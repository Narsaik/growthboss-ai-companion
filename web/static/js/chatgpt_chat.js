// GrowthBoss AI Companion - ChatGPT-like Interface
let currentMode = 'rag';
let sessionId = null;
let isTyping = false;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    loadSession();
});

function setupEventListeners() {
    const input = document.getElementById('messageInput');
    
    input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    input.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 200) + 'px';
    });
}

function setMode(mode) {
    currentMode = mode;
    document.getElementById('ragModeBtn').classList.toggle('active', mode === 'rag');
    document.getElementById('councilModeBtn').classList.toggle('active', mode === 'council');
    document.getElementById('modeBadge').textContent = mode === 'rag' ? '📚 Knowledge Base' : '🎯 Marketing Council';
}

function sendSuggestion(text) {
    document.getElementById('messageInput').value = text;
    sendMessage();
}

async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message || isTyping) return;

    // Hide welcome screen
    document.getElementById('welcomeScreen').style.display = 'none';

    // Add user message
    addMessage('user', message);
    input.value = '';
    input.style.height = 'auto';

    // Show typing indicator
    isTyping = true;
    const typingId = addTypingIndicator();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                use_council: currentMode === 'council',
                session_id: sessionId
            })
        });

        const data = await response.json();
        
        // Remove typing indicator
        removeTypingIndicator(typingId);
        
        if (data.session_id) {
            sessionId = data.session_id;
        }

        // Add assistant response
        addMessage('assistant', data.response || 'Sorry, I encountered an error.');
    } catch (error) {
        removeTypingIndicator(typingId);
        addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
    }

    isTyping = false;
}

function addMessage(role, content) {
    const container = document.getElementById('chatContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const avatar = document.createElement('div');
    avatar.className = `avatar ${role}`;
    avatar.textContent = role === 'user' ? 'U' : 'GB';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Format content (simple markdown-like formatting)
    const formatted = formatMessage(content);
    contentDiv.innerHTML = formatted;
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    container.appendChild(messageDiv);
    
    // Scroll to bottom
    container.scrollTop = container.scrollHeight;
}

function formatMessage(text) {
    // Simple formatting - convert markdown-like syntax
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .split('\n')
        .map(line => line.trim() ? `<p>${line}</p>` : '')
        .join('');
}

function addTypingIndicator() {
    const container = document.getElementById('chatContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.id = 'typing-indicator';
    
    const avatar = document.createElement('div');
    avatar.className = 'avatar assistant';
    avatar.textContent = 'GB';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = '<div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>';
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    container.appendChild(messageDiv);
    
    container.scrollTop = container.scrollHeight;
    
    return 'typing-indicator';
}

function removeTypingIndicator(id) {
    const indicator = document.getElementById(id);
    if (indicator) {
        indicator.remove();
    }
}

function loadSession() {
    fetch('/api/session')
        .then(res => res.json())
        .then(data => {
            if (data.session_id) {
                sessionId = data.session_id;
            }
        })
        .catch(err => console.error('Session load error:', err));
}





