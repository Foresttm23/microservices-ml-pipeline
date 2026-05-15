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
let historyAbortController = null;
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

// Toast Notifications
function showToast(title, message, type = 'info') {
    console.log(`[Toast] ${type.toUpperCase()}: ${title} - ${message}`);

    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icons = {
        success: '✓',
        error: '✕',
        info: 'ℹ',
        warning: '⚠'
    };

    toast.innerHTML = `
        <div class="toast-icon">${icons[type] || icons.info}</div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
    `;

    container.appendChild(toast);

    // Auto remove
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => {
            if (toast.parentNode === container) {
                container.removeChild(toast);
            }
            if (container.childNodes.length === 0) {
                container.remove();
            }
        }, 300);
    }, 5000);
}

function handleApiError(response, data) {
    const status = response.status;
    let title = "Error";
    let message = "An unexpected error occurred.";

    const errorMap = {
        400: "Invalid request. Please check your input.",
        401: "Session expired or unauthorized. Please login.",
        403: "You don't have permission to perform this action.",
        404: "The requested resource was not found.",
        422: "Validation error. Please check your email and password format.",
        429: "Too many requests. Please wait a moment before trying again.",
        500: "Internal server error. Our team is looking into it.",
        502: "Service temporarily unavailable. Try again in a moment.",
        503: "The service is under heavy load. Please wait.",
        504: "The request timed out. Please try again."
    };

    if (errorMap[status]) {
        message = errorMap[status];
    }

    // Specific logic for 422 (often used for auth errors in this repo)
    if (status === 422) {
        title = "Auth Error";
        message = "Invalid email or password format.";
    } else if (status === 401) {
        title = "Authentication Required";
    }

    // If backend provided a specific detail message, we can log it to terminal but show generic toast
    const detail = data && (data.detail || data.message || (typeof data === 'string' ? data : null));
    if (detail) {
        console.error(`API Error [${status}]:`, detail);
        // If it's a validation error with list of errors
        if (Array.isArray(detail)) {
            const firstErr = detail[0];
            if (firstErr && firstErr.msg) {
                message = firstErr.msg;
            }
        } else if (typeof detail === 'string' && detail.length < 100) {
            // If it's a short string, we can show it directly
            message = detail;
        }
    }

    showToast(title, message, 'error');
}

// Chat Helpers
function createChat() {
    const id = Date.now().toString();
    const interactionId = crypto.randomUUID();
    chats.unshift({
        id,
        interactionId,
        title: `Chat ${chats.length + 1}`,
        cleanHtml: '<div class="empty-state">Waiting for results...</div>',
        rawHtml: '<div class="terminal-line"><span class="prompt">></span> Ready...</div>',
        loaded: true // It's a new chat, nothing to load
    });
    switchChat(id);
    renderChatList();
}

async function switchChat(id) {
    if (currentChatId === id) return;

    // Save current chat state before switching
    if (currentChatId) {
        const oldChat = chats.find(c => c.id === currentChatId);
        // Only save if it's not in loading state to avoid saving empty/clearing DOM
        if (oldChat && !oldChat.loading) {
            oldChat.cleanHtml = cleanOutput.innerHTML;
            oldChat.rawHtml = terminal.innerHTML;
        }
    }

    // Cancel any pending history requests
    if (historyAbortController) {
        historyAbortController.abort();
    }

    currentChatId = id;
    const newChat = chats.find(c => c.id === currentChatId);
    if (!newChat) return;

    // If chat needs loading, fetch it
    if (newChat.interactionId && !newChat.loaded) {
        newChat.loading = true;
        cleanOutput.innerHTML = '<div class="empty-state">Loading history...</div>';
        terminal.innerHTML = '<div class="terminal-line"><span class="prompt">></span> Loading history...</div>';

        historyAbortController = new AbortController();
        try {
            const data = await apiRequest('GET', `/chats/${newChat.interactionId}/messages`, null, false, historyAbortController.signal);

            // Re-verify that we are still on the same chat after async call
            if (currentChatId !== id) return;

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
            }
        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('History load aborted for chat:', id);
                return;
            }
            logToTerminal(`Failed to load history: ${error.message}`, 'error');
        } finally {
            newChat.loading = false;
            // Only update saved HTML if we successfully loaded (or if it was already loaded)
            if (newChat.loaded) {
                newChat.cleanHtml = cleanOutput.innerHTML;
                newChat.rawHtml = terminal.innerHTML;
            }
        }
    }

    // Restore DOM from saved state
    if (currentChatId === id) {
        cleanOutput.innerHTML = newChat.cleanHtml || '<div class="empty-state">Waiting for results...</div>';
        terminal.innerHTML = newChat.rawHtml || '<div class="terminal-line"><span class="prompt">></span> Ready...</div>';
    }

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
            showToast("Session Error", "Your session token is invalid. Please login again.", "warning");
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
async function apiRequest(method, endpoint, body = null, silent = false, signal = null) {
    logToTerminal(`[${method}] ${endpoint}`);
    try {
        const headers = {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
        };

        const options = {method, headers, signal};
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
            handleApiError(response, data);
            return null;
        }

        logToTerminal(data, 'success');
        if (!silent) {
            logToClean(data);
        }
        return data;
    } catch (error) {
        logToTerminal(`Network Error: ${error.message}`, 'error');
        showToast("Network Error", "Unable to connect to the server. Please check your internet connection.", "error");
        return null;
    }
}

// Event Listeners - Auth
document.getElementById('btnRegister').addEventListener('click', async () => {
    const data = await apiRequest('POST', '/auth/register', {
        email: emailInput.value,
        password: passwordInput.value
    });
    if (data) {
        showToast("Success", "Account created successfully. You can now login.", "success");
    }
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
        showToast("Welcome", "Login successful! Your session is now active.", "success");
        updateStatus();
    }
});

document.getElementById('btnRefresh').addEventListener('click', async () => {
    const refreshToken = localStorage.getItem(REFRESH_KEY);
    if (!refreshToken) {
        logToTerminal('No refresh token available', 'error');
        showToast("Session Expired", "No refresh token found. Please login again.", "warning");
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
        showToast("Refreshed", "Your session has been successfully extended.", "success");
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
    showToast("Logged Out", "You have been safely logged out.", "info");
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

    const data = await apiRequest('POST', `/pipelines/${pipelineId}/run`, {
        message: promptInput.value,
        client_id: localStorage.getItem(SESSION_KEY),
        interaction_id: currentChat ? currentChat.interactionId : null
    });

    if (data) {
        showToast("Task Sent", "Your request has been submitted and is being processed.", "success");
        promptInput.value = ''; // Clear input on success
    }
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

            const currentChat = chats.find(c => c.id === currentChatId);

            // Strictly check that the message belongs to the current chat
            if (currentChat && currentChat.interactionId === data.interaction_id) {
                logToClean(data);
            } else if (data.interaction_id) {
                // Background update for the corresponding chat
                const targetChat = chats.find(c => c.interactionId === data.interaction_id);
                if (targetChat) {
                    targetChat.loaded = false; // Mark as stale so it re-fetches history next time
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
        showToast("Connection Error", "The real-time updates channel encountered an error.", "warning");
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

