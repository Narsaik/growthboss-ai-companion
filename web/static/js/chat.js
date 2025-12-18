// GrowthBoss AI Companion - Chat Interface

let currentMode = 'rag'; // 'rag' or 'council'
let sessionId = null;
let isTyping = false;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    checkHealth();
    setupEventListeners();
    loadSession();
});

// Setup event listeners
function setupEventListeners() {
    const input = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendButton');
    
    // Send on Enter (Shift+Enter for new line)
    input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Auto-resize textarea
    input.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 150) + 'px';
    });
}

// Check API health
async function checkHealth() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        
        const statusIndicator = document.getElementById('statusIndicator');
        const statusDot = statusIndicator.querySelector('.status-dot');
        const statusText = statusIndicator.querySelector('.status-text');
        
        if (data.status === 'healthy') {
            statusDot.style.background = '#10b981';
            statusText.textContent = 'Connected';
        } else {
            statusDot.style.background = '#ef4444';
            statusText.textContent = 'Error';
        }
    } catch (error) {
        console.error('Health check failed:', error);
        const statusIndicator = document.getElementById('statusIndicator');
        const statusDot = statusIndicator.querySelector('.status-dot');
        const statusText = statusIndicator.querySelector('.status-text');
        statusDot.style.background = '#ef4444';
        statusText.textContent = 'Disconnected';
    }
}

// Load session
async function loadSession() {
    try {
        const response = await fetch('/api/session');
        const data = await response.json();
        sessionId = data.session_id;
    } catch (error) {
        console.error('Failed to load session:', error);
    }
}

// Set mode
function setMode(mode) {
    currentMode = mode;
    
    const ragBtn = document.getElementById('ragModeBtn');
    const councilBtn = document.getElementById('councilModeBtn');
    
    if (mode === 'rag') {
        ragBtn.classList.add('active');
        councilBtn.classList.remove('active');
    } else {
        councilBtn.classList.add('active');
        ragBtn.classList.remove('active');
    }
}

// Toggle council mode
function toggleCouncilMode() {
    if (currentMode === 'council') {
        setMode('rag');
    } else {
        setMode('council');
    }
}

// Set quick question
function setQuickQuestion(question) {
    document.getElementById('messageInput').value = question;
    document.getElementById('messageInput').focus();
    sendMessage();
}

// Send message
async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message || isTyping) return;
    
    // Hide welcome section
    const welcomeSection = document.getElementById('welcomeSection');
    welcomeSection.style.display = 'none';
    
    // Show messages container
    const messagesContainer = document.getElementById('messagesContainer');
    messagesContainer.classList.add('active');
    
    // Add user message
    addMessage('user', message);
    
    // Clear input
    input.value = '';
    input.style.height = 'auto';
    
    // Show typing indicator
    showTypingIndicator();
    
    // Disable input
    isTyping = true;
    input.disabled = true;
    document.getElementById('sendButton').disabled = true;
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                use_council: currentMode === 'council'
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Remove typing indicator
            hideTypingIndicator();
            
            // Add assistant response
            addMessage('assistant', data.response, currentMode === 'council' ? 'council' : 'rag');
            
            // Update session ID if provided
            if (data.session_id) {
                sessionId = data.session_id;
            }
        } else {
            throw new Error(data.error || 'Failed to get response');
        }
    } catch (error) {
        console.error('Error sending message:', error);
        hideTypingIndicator();
        addMessage('assistant', `Sorry, I encountered an error: ${error.message}. Please try again.`, 'rag');
    } finally {
        // Re-enable input
        isTyping = false;
        input.disabled = false;
        document.getElementById('sendButton').disabled = false;
        input.focus();
        
        // Scroll to bottom
        scrollToBottom();
    }
}

// Add message to chat
function addMessage(role, content, mode = 'rag') {
    const messagesContainer = document.getElementById('messagesContainer');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    // Format message content (simple markdown-like formatting)
    const formattedContent = formatMessage(content);
    messageContent.innerHTML = formattedContent;
    
    // Add metadata
    const messageMeta = document.createElement('div');
    messageMeta.className = 'message-meta';
    
    const timestamp = new Date().toLocaleTimeString();
    const modeBadge = document.createElement('span');
    modeBadge.className = `mode-badge ${mode}`;
    modeBadge.textContent = mode === 'council' ? '🎯 Marketing Council' : '📚 Knowledge Base';
    
    messageMeta.appendChild(modeBadge);
    messageMeta.appendChild(document.createTextNode(` • ${timestamp}`));
    
    messageDiv.appendChild(messageContent);
    messageDiv.appendChild(messageMeta);
    
    messagesContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    scrollToBottom();
}

// Format message content (basic markdown)
function formatMessage(text) {
    // Escape HTML
    let html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    
    // Bold (**text**)
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Italic (*text*)
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Code blocks (```code```)
    html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    
    // Inline code (`code`)
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
    
    // Bullet points
    html = html.replace(/^[\*\-]\s+(.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    
    // Numbered lists
    html = html.replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>');
    
    // Line breaks
    html = html.replace(/\n\n/g, '</p><p>');
    html = html.replace(/\n/g, '<br>');
    
    // Wrap in paragraphs
    if (!html.startsWith('<')) {
        html = '<p>' + html + '</p>';
    }
    
    return html;
}

// Show typing indicator
function showTypingIndicator() {
    const messagesContainer = document.getElementById('messagesContainer');
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message assistant';
    typingDiv.id = 'typingIndicator';
    
    const typingContent = document.createElement('div');
    typingContent.className = 'typing-indicator';
    typingContent.innerHTML = '<span></span><span></span><span></span>';
    
    typingDiv.appendChild(typingContent);
    messagesContainer.appendChild(typingDiv);
    
    scrollToBottom();
}

// Hide typing indicator
function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Scroll to bottom
function scrollToBottom() {
    const messagesContainer = document.getElementById('messagesContainer');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

