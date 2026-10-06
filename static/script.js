document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Menu Toggle
    const mobileToggle = document.getElementById('mobileToggle');
    const navMenu = document.getElementById('navMenu');
    
    if (mobileToggle && navMenu) {
        mobileToggle.addEventListener('click', () => {
            navMenu.classList.toggle('show');
        });
    }

    // 2. Auto-dismiss Toast notifications
    const toasts = document.querySelectorAll('.toast');
    toasts.forEach(toast => {
        const closeBtn = toast.querySelector('.toast-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                toast.style.opacity = '0';
                toast.style.transform = 'translateY(-10px)';
                toast.style.transition = 'all 0.3s ease';
                setTimeout(() => toast.remove(), 300);
            });
        }
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            if (toast && toast.parentElement) {
                toast.style.opacity = '0';
                toast.style.transform = 'translateY(-10px)';
                toast.style.transition = 'all 0.3s ease';
                setTimeout(() => toast.remove(), 300);
            }
        }, 5000);
    });

    // 3. Confirm Delete Actions
    const deleteForms = document.querySelectorAll('.delete-form');
    deleteForms.forEach(form => {
        form.addEventListener('submit', (e) => {
            const studentName = form.dataset.studentName || 'this student';
            const confirmed = confirm(`Are you sure you want to delete ${studentName}? This action cannot be undone.`);
            if (!confirmed) {
                e.preventDefault();
            }
        });
    });

    // 4. Input clear button support / form dynamic feel
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        // Optional quick escape key clear
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                searchInput.value = '';
                searchInput.closest('form').submit();
            }
        });
    }
});

/* ==================================================
   STUDENTHUB AI AGENT INTERACTIVE CHAT ENGINE
   ================================================== */

// Toggle floating chat drawer
function toggleAIChat() {
    const drawer = document.getElementById('aiChatDrawer');
    if (drawer) {
        drawer.classList.toggle('open');
        if (drawer.classList.contains('open')) {
            const input = document.getElementById('drawerChatInput');
            if (input) input.focus();
        }
    }
}

// Markdown Formatter Helper
function formatMarkdown(text) {
    if (!text) return '';
    let formatted = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    
    // Markdown headers
    formatted = formatted.replace(/^### (.*$)/gim, '<strong>$1</strong>');
    formatted = formatted.replace(/^## (.*$)/gim, '<strong>$1</strong>');
    
    // Bold
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Italic
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
    // Inline code
    formatted = formatted.replace(/`(.*?)`/g, '<code style="background:#e0e7ff; color:#3730a3; padding:2px 6px; border-radius:4px;">$1</code>');
    
    // Markdown links [text](url)
    formatted = formatted.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
    
    // Line breaks & lists
    formatted = formatted.replace(/\n\n/g, '<br><br>');
    formatted = formatted.replace(/\n- /g, '<br>• ');
    formatted = formatted.replace(/\n\d+\. /g, '<br>1. ');
    
    return formatted;
}

// Send message from Drawer
async function sendDrawerChatMessage() {
    const input = document.getElementById('drawerChatInput');
    const container = document.getElementById('drawerChatMessageContainer');
    if (!input || !container) return;

    const message = input.value.trim();
    if (!message) return;

    // Append User Message
    const userMsgDiv = document.createElement('div');
    userMsgDiv.className = 'ai-message ai-message-user';
    userMsgDiv.innerHTML = `
        <div class="ai-avatar">You</div>
        <div class="ai-bubble">${formatMarkdown(message)}</div>
    `;
    container.appendChild(userMsgDiv);
    input.value = '';
    container.scrollTop = container.scrollHeight;

    // Append Typing Indicator
    const typingDiv = document.createElement('div');
    typingDiv.className = 'ai-message ai-message-agent';
    typingDiv.id = 'drawerTypingIndicator';
    typingDiv.innerHTML = `
        <div class="ai-avatar">🤖</div>
        <div class="ai-bubble" style="font-style: italic; color: #64748b;">AI Agent is thinking...</div>
    `;
    container.appendChild(typingDiv);
    container.scrollTop = container.scrollHeight;

    try {
        const response = await fetch('/api/ai/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        });
        const data = await response.json();

        // Remove typing indicator
        const typing = document.getElementById('drawerTypingIndicator');
        if (typing) typing.remove();

        // Append Agent Response
        const agentMsgDiv = document.createElement('div');
        agentMsgDiv.className = 'ai-message ai-message-agent';
        agentMsgDiv.innerHTML = `
            <div class="ai-avatar">🤖</div>
            <div class="ai-bubble">${formatMarkdown(data.reply)}</div>
        `;
        container.appendChild(agentMsgDiv);
        container.scrollTop = container.scrollHeight;

    } catch (err) {
        const typing = document.getElementById('drawerTypingIndicator');
        if (typing) typing.remove();

        const errDiv = document.createElement('div');
        errDiv.className = 'ai-message ai-message-agent';
        errDiv.innerHTML = `
            <div class="ai-avatar">🤖</div>
            <div class="ai-bubble" style="color: #ef4444;">Sorry, I encountered an error connecting to the AI agent service.</div>
        `;
        container.appendChild(errDiv);
        container.scrollTop = container.scrollHeight;
    }
}

function handleDrawerKeyPress(e) {
    if (e.key === 'Enter') {
        sendDrawerChatMessage();
    }
}

function sendDrawerQuickPrompt(promptText) {
    const input = document.getElementById('drawerChatInput');
    if (input) {
        input.value = promptText;
        sendDrawerChatMessage();
    }
}

// Send message on dedicated AI Assistant page
async function sendPageChatMessage() {
    const input = document.getElementById('pageChatInput');
    const container = document.getElementById('pageChatMessageContainer');
    if (!input || !container) return;

    const message = input.value.trim();
    if (!message) return;

    // User message
    const userMsgDiv = document.createElement('div');
    userMsgDiv.className = 'ai-message ai-message-user';
    userMsgDiv.innerHTML = `
        <div class="ai-avatar">You</div>
        <div class="ai-bubble">${formatMarkdown(message)}</div>
    `;
    container.appendChild(userMsgDiv);
    input.value = '';
    container.scrollTop = container.scrollHeight;

    // Typing indicator
    const typingDiv = document.createElement('div');
    typingDiv.className = 'ai-message ai-message-agent';
    typingDiv.id = 'pageTypingIndicator';
    typingDiv.innerHTML = `
        <div class="ai-avatar">🤖</div>
        <div class="ai-bubble" style="font-style: italic; color: #64748b;">AI Agent is analyzing database...</div>
    `;
    container.appendChild(typingDiv);
    container.scrollTop = container.scrollHeight;

    try {
        const response = await fetch('/api/ai/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        });
        const data = await response.json();

        const typing = document.getElementById('pageTypingIndicator');
        if (typing) typing.remove();

        const agentMsgDiv = document.createElement('div');
        agentMsgDiv.className = 'ai-message ai-message-agent';
        agentMsgDiv.innerHTML = `
            <div class="ai-avatar">🤖</div>
            <div class="ai-bubble">${formatMarkdown(data.reply)}</div>
        `;
        container.appendChild(agentMsgDiv);
        container.scrollTop = container.scrollHeight;

    } catch (err) {
        const typing = document.getElementById('pageTypingIndicator');
        if (typing) typing.remove();

        const errDiv = document.createElement('div');
        errDiv.className = 'ai-message ai-message-agent';
        errDiv.innerHTML = `
            <div class="ai-avatar">🤖</div>
            <div class="ai-bubble" style="color: #ef4444;">Error communicating with AI agent.</div>
        `;
        container.appendChild(errDiv);
        container.scrollTop = container.scrollHeight;
    }
}

function handlePageChatKeyPress(e) {
    if (e.key === 'Enter') {
        sendPageChatMessage();
    }
}

function sendQuickPrompt(promptText) {
    const drawer = document.getElementById('aiChatDrawer');
    if (drawer && !drawer.classList.contains('open')) {
        toggleAIChat();
        sendDrawerQuickPrompt(promptText);
    } else {
        const input = document.getElementById('pageChatInput') || document.getElementById('drawerChatInput');
        if (input) {
            input.value = promptText;
            if (input.id === 'pageChatInput') {
                sendPageChatMessage();
            } else {
                sendDrawerChatMessage();
            }
        }
    }
}

function clearAIChatHistory() {
    const container = document.getElementById('pageChatMessageContainer');
    if (container) {
        container.innerHTML = `
            <div class="ai-message ai-message-agent">
                <div class="ai-avatar">🤖</div>
                <div class="ai-bubble">Chat history cleared. How can I assist you with StudentHub today?</div>
            </div>
        `;
    }
}

