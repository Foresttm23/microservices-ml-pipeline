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
let lastActivity = Date.now();
const INACTIVITY_LIMIT = 10 * 60 * 1000; // 10 minutes


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

function logToClean(data, role = 'assistant') {
    const emptyState = cleanOutput.querySelector('.empty-state');
    if (emptyState) emptyState.remove();

    if (typeof data !== 'object' || data === null) {
        if (typeof data === 'string') {
            data = {output: data};
        } else {
            return;
        }
    }

    const outputText = data.output || data.result || data.message || data.output_text || data.text || data.content;
    const status = data.status || data.state || 'COMPLETED';
    const timestamp = data.completed_at || data.created_at || new Date().toISOString();

    if (!outputText && role !== 'user') return;

    const msgDiv = document.createElement('div');
    msgDiv.className = `clean-message ${role}`;

    let metaHtml = `<div class="clean-metadata">
        <span class="role-tag">${role.toUpperCase()}</span>
        <span><strong>Status:</strong> ${status}</span>
        <span><strong>Time:</strong> ${new Date(timestamp).toLocaleString()}</span>
    </div>`;

    let contentHtml = `<div class="clean-content">${outputText || "..."}</div>`;

    msgDiv.innerHTML = metaHtml + contentHtml;
    cleanOutput.appendChild(msgDiv);
    cleanOutput.scrollTop = cleanOutput.scrollHeight;
}

// Chat Helpers
function createChat() {
    const id = Date.now().toString();
    chats.unshift({
        id,
        interactionId: null,
        title: `Chat ${chats.length + 1}`,
        cleanHtml: '<div class="empty-state">Waiting for results...</div>',
        rawHtml: '<div class="terminal-line"><span class="prompt">></span> Ready...</div>'
    });
    switchChat(id);
    renderChatList();
}

async function switchChat(id) {
    if (currentChatId) {
        const oldChat = chats.find(c => c.id === currentChatId);
        if (oldChat) {
            oldChat.cleanHtml = cleanOutput.innerHTML;
            oldChat.rawHtml = terminal.innerHTML;
        }
    }

    currentChatId = id;
    const newChat = chats.find(c => c.id === currentChatId);
    if (!newChat) return;

    if (newChat.interactionId && !newChat.loaded) {
        cleanOutput.innerHTML = '';
        terminal.innerHTML = '';
        logToTerminal('Loading history...');
        const data = await apiRequest('GET', `/chats/${newChat.interactionId}/messages`);
        cleanOutput.innerHTML = '';
        terminal.innerHTML = '';
        if (data && data.items) {
            data.items.forEach(msg => {
                logToTerminal(`Prompt: ${msg.message}`);
                logToClean({
                    message: msg.message,
                    created_at: msg.created_at,
                    state: msg.state
                }, 'user');

                if (msg.responses) {
                    msg.responses.forEach(resp => {
                        const payload = {
                            status: msg.state,
                            completed_at: resp.created_at,
                            output: resp.content
                        };
                        logToClean(payload, 'assistant');
                        logToTerminal(payload, 'success');
                    });
                }
            });
            newChat.loaded = true;
            newChat.cleanHtml = cleanOutput.innerHTML || '<div class="empty-state">Waiting for results...</div>';
            newChat.rawHtml = terminal.innerHTML || '<div class="terminal-line"><span class="prompt">></span> Ready...</div>';
        }
    }

    cleanOutput.innerHTML = newChat.cleanHtml || '<div class="empty-state">Waiting for results...</div>';
    terminal.innerHTML = newChat.rawHtml || '<div class="terminal-line"><span class="prompt">></span> Ready...</div>';

    renderChatList();
}

async function loadChats() {
    const data = await apiRequest('GET', '/chats', null, true);
    if (data && data.items && data.items.length > 0) {
        chats = data.items.map((q) => ({
            id: q.interaction_id,
            interactionId: q.interaction_id,
            title: q.message.substring(0, 20) + (q.message.length > 20 ? '...' : ''),
            cleanHtml: '',
            rawHtml: '',
            loaded: false
        }));
        switchChat(chats[0].id);
    } else {
        chats = [];
        createChat();
    }
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
            loadChats(); // Load history when authenticated
        } catch (e) {
            statusText.textContent = 'Invalid Token';
            statusDot.classList.remove('active');
        }
    } else {
        statusText.textContent = 'Not Authenticated';
        statusDot.classList.remove('active');
        connectWebSocket('anonymous'); // Connect as anonymous if needed
        chats = [];
        createChat(); // Blank chat for anonymous
    }
}

// API Wrapper
async function apiRequest(method, endpoint, body = null, silent = false) {
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
        if (!silent) {
            logToClean(data);
        }
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
    }, true);

    if (data && data.access_token) {
        localStorage.setItem(TOKEN_KEY, data.access_token);
        if (data.refresh_token) {
            localStorage.setItem(REFRESH_KEY, data.refresh_token);
        }
        logToClean({
            message: "Token refreshed successfully. Session extended.",
            status: "SUCCESS"
        }, 'assistant');
        updateStatus();
    } else {
        logToClean({
            message: "Failed to refresh token. Please login again.",
            status: "ERROR"
        }, 'assistant');
    }
});

document.getElementById('btnLogout').addEventListener('click', async () => {
    const refreshToken = localStorage.getItem(REFRESH_KEY);
    if (refreshToken) {
        await apiRequest('POST', '/auth/logout', {refresh_token: refreshToken});
    }
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(SESSION_KEY);
    localStorage.setItem(SESSION_KEY, crypto.randomUUID());

    // Clear frontend memory
    chats = [];
    currentChatId = null;
    terminal.innerHTML = '<div class="terminal-line"><span class="prompt">></span> Ready...</div>';
    cleanOutput.innerHTML = '<div class="empty-state">Waiting for results...</div>';

    updateStatus();
});

document.getElementById('btnMe').addEventListener('click', async () => {
    const data = await apiRequest('GET', '/auth/me', null, true);
    if (data) {
        logToClean({
            message: `User Profile:\nEmail: ${data.email}\nID: ${data.id}\nCreated: ${new Date(data.created_at).toLocaleString()}`,
            status: "AUTHENTICATED"
        }, 'assistant');
    }
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

// Activity Monitoring
function resetInactivityTimer() {
    lastActivity = Date.now();
}

window.addEventListener('mousedown', resetInactivityTimer);
window.addEventListener('keypress', resetInactivityTimer);
window.addEventListener('scroll', resetInactivityTimer);
window.addEventListener('touchstart', resetInactivityTimer);

setInterval(() => {
    if (Date.now() - lastActivity > INACTIVITY_LIMIT) {
        const token = localStorage.getItem(TOKEN_KEY);
        if (token) {
            console.log('Inactivity detected, reloading chats...');
            logToTerminal('Inactivity detected, refreshing chat list...');
            loadChats();
            resetInactivityTimer();
        }
    }
}, 60000); // Check every minute

// Initial Setup
updateStatus();

