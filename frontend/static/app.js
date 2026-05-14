const TOKEN_KEY = "access_token";
const REFRESH_KEY = "refresh_token";
const SESSION_KEY = "session_id";

// Initialize Session ID
if (!localStorage.getItem(SESSION_KEY)) {
    localStorage.setItem(SESSION_KEY, crypto.randomUUID());
}

const GATEWAY_URL = window.CONFIG.GATEWAY_URL;
const GATEWAY_WS_URL = window.CONFIG.GATEWAY_WS_URL;

let ws = null;
let chats = [];
let currentChatId = null;

// DOM Elements
const terminal = document.getElementById('terminal');
const statusDot = document.getElementById('statusIndicator');
const statusText = document.getElementById('statusText');
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');
const pipelineIdInput = document.getElementById('pipelineId');
const promptInput = document.getElementById('prompt');
const cleanOutput = document.getElementById('cleanOutput');

// Tabs Logic
const tabBtns = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.terminal-body');

tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        tabBtns.forEach(b => b.classList.remove('active'));
        tabContents.forEach(c => c.classList.remove('active'));

        btn.classList.add('active');
        document.getElementById(btn.dataset.target).classList.add('active');
    });
});

// Terminal Logger
function logToTerminal(message, type = 'info') {
    const line = document.createElement('div');
    line.className = `terminal-line ${type}`;

    let text = message;
    if (typeof message === 'object') {
        text = JSON.stringify(message, null, 2);
    }

    line.innerHTML = `<span class="prompt">></span> <pre style="display:inline; margin:0; font-family:inherit;">${text}</pre>`;
    terminal.appendChild(line);
    terminal.scrollTop = terminal.scrollHeight;
}

function logToClean(data) {
    const emptyState = cleanOutput.querySelector('.empty-state');
    if (emptyState) emptyState.remove();

    if (typeof data !== 'object' || data === null) {
        return;
    }

    const outputText = data.output || data.result || data.message || data.output_text || data.text;
    const status = data.status || data.state || (data.access_token ? 'SUCCESS' : 'COMPLETED');
    const timestamp = data.completed_at || data.created_at || new Date().toISOString();

    if (!outputText && !data.status && !data.access_token) return;

    const msgDiv = document.createElement('div');
    msgDiv.className = 'clean-message';

    let metaHtml = `<div class="clean-metadata">
        <span><strong>Status:</strong> ${status}</span>
        <span><strong>Time:</strong> ${new Date(timestamp).toLocaleString()}</span>
    </div>`;

    let contentHtml = `<div class="clean-content">${outputText || JSON.stringify({
        status: data.status,
        message: "No output"
    }, null, 2)}</div>`;

    msgDiv.innerHTML = metaHtml + contentHtml;
    cleanOutput.appendChild(msgDiv);
    cleanOutput.scrollTop = cleanOutput.scrollHeight;
}

// Chat Helpers
function createChat() {
    const id = Date.now().toString();
    chats.push({
        id,
        interactionId: null,
        title: `Chat ${chats.length + 1}`,
        cleanHtml: '<div class="empty-state">Waiting for results...</div>',
        rawHtml: '<div class="terminal-line"><span class="prompt">></span> Ready...</div>'
    });
    switchChat(id);
    renderChatList();
}

function switchChat(id) {
    if (currentChatId) {
        const oldChat = chats.find(c => c.id === currentChatId);
        if (oldChat) {
            oldChat.cleanHtml = cleanOutput.innerHTML;
            oldChat.rawHtml = terminal.innerHTML;
        }
    }

    currentChatId = id;
    const newChat = chats.find(c => c.id === currentChatId);
    if (newChat) {
        cleanOutput.innerHTML = newChat.cleanHtml;
        terminal.innerHTML = newChat.rawHtml;
    }
    renderChatList();
}

function renderChatList() {
    const chatList = document.getElementById('chatList');
    chatList.innerHTML = '';
    chats.forEach(chat => {
        const li = document.createElement('li');
        li.className = `chat-item ${chat.id === currentChatId ? 'active' : ''}`;
        li.textContent = chat.title;
        li.onclick = () => switchChat(chat.id);
        chatList.appendChild(li);
    });
}

document.getElementById('btnNewChat').addEventListener('click', createChat);

document.getElementById('btnClearTerminal').addEventListener('click', () => {
    terminal.innerHTML = '<div class="terminal-line"><span class="prompt">></span> Ready...</div>';
    cleanOutput.innerHTML = '<div class="empty-state">Waiting for results...</div>';
});

// Auth Helpers
function getAuthHeaders() {
    const token = localStorage.getItem(TOKEN_KEY);
    return token ? {'Authorization': `Bearer ${token}`} : {};
}

function updateStatus() {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            statusText.textContent = payload.sub || 'Authenticated';
            statusDot.classList.add('active');
            connectWebSocket(payload.sub);
        } catch (e) {
            statusText.textContent = 'Invalid Token';
            statusDot.classList.remove('active');
        }
    } else {
        statusText.textContent = 'Not Authenticated';
        statusDot.classList.remove('active');
        connectWebSocket('anonymous'); // Connect as anonymous if needed
    }
}

// API Wrapper
async function apiRequest(method, endpoint, body = null) {
    logToTerminal(`[${method}] ${endpoint}`);
    try {
        const headers = {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
        };

        const options = {method, headers};
        if (body) options.body = JSON.stringify(body);

        const response = await fetch(`${GATEWAY_URL}${endpoint}`, options);
        let data;

        const contentType = response.headers.get("content-type");
        if (contentType && contentType.indexOf("application/json") !== -1) {
            data = await response.json();
        } else {
            data = await response.text();
            try {
                data = JSON.parse(data);
            } catch (e) {
            }
        }

        if (!response.ok) {
            logToTerminal(data, 'error');
            return null;
        }

        logToTerminal(data, 'success');
        logToClean(data);
        return data;
    } catch (error) {
        logToTerminal(`Network Error: ${error.message}`, 'error');
        return null;
    }
}

// Event Listeners - Auth
document.getElementById('btnRegister').addEventListener('click', async () => {
    await apiRequest('POST', '/auth/register', {
        email: emailInput.value,
        password: passwordInput.value
    });
});

document.getElementById('btnLogin').addEventListener('click', async () => {
    const data = await apiRequest('POST', '/auth/login', {
        email: emailInput.value,
        password: passwordInput.value
    });

    if (data && data.access_token) {
        localStorage.setItem(TOKEN_KEY, data.access_token);
        if (data.refresh_token) {
            localStorage.setItem(REFRESH_KEY, data.refresh_token);
        }
        updateStatus();
    }
});

document.getElementById('btnRefresh').addEventListener('click', async () => {
    const refreshToken = localStorage.getItem(REFRESH_KEY);
    if (!refreshToken) {
        logToTerminal('No refresh token available', 'error');
        return;
    }

    const data = await apiRequest('POST', '/auth/refresh', {
        refresh_token: refreshToken
    });

    if (data && data.access_token) {
        localStorage.setItem(TOKEN_KEY, data.access_token);
        if (data.refresh_token) {
            localStorage.setItem(REFRESH_KEY, data.refresh_token);
        }
        updateStatus();
    }
});

document.getElementById('btnLogout').addEventListener('click', async () => {
    const refreshToken = localStorage.getItem(REFRESH_KEY);
    if (refreshToken) {
        await apiRequest('POST', '/auth/logout', {refresh_token: refreshToken});
    }
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
    updateStatus();
});

document.getElementById('btnMe').addEventListener('click', async () => {
    await apiRequest('GET', '/auth/me');
});

// Event Listeners - Pipeline
document.getElementById('btnRun').addEventListener('click', async () => {
    const pipelineId = pipelineIdInput.value || 'default';
    const currentChat = chats.find(c => c.id === currentChatId);

    if (currentChat && promptInput.value) {
        if (currentChat.title.startsWith('Chat ')) {
            currentChat.title = promptInput.value.substring(0, 20) + '...';
            renderChatList();
        }
    }

    await apiRequest('POST', `/pipelines/${pipelineId}/run`, {
        message: promptInput.value,
        client_id: localStorage.getItem(SESSION_KEY),
        interaction_id: currentChat ? currentChat.interactionId : null
    });
});

// WebSocket Connection
function connectWebSocket(userId) {
    if (ws) {
        ws.close();
    }

    const wsUrl = `${GATEWAY_WS_URL}/ws/results/${userId}`;
    logToTerminal(`Connecting WS: ${wsUrl}`);

    ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            logToTerminal(`[WS] Received Result:`, 'success');
            logToTerminal(data, 'success');
            logToClean(data);

            if (data.interaction_id && currentChatId) {
                const currentChat = chats.find(c => c.id === currentChatId);
                if (currentChat) {
                    currentChat.interactionId = data.interaction_id;
                }
            }
        } catch (e) {
            logToTerminal(`[WS] ${event.data}`, 'success');
        }
    };

    ws.onclose = () => {
        logToTerminal('[WS] Disconnected');
    };

    ws.onerror = (error) => {
        logToTerminal(`[WS] Error: ${error}`, 'error');
    };
}

// Initial Setup
updateStatus();
createChat();
