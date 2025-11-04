// Configuration
let config = {
    serverUrl: 'http://localhost:8001',  // agent-http está en puerto 8001
    connectionType: 'http'
};

let ws = null;

// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const toggleLogsBtn = document.getElementById('toggleLogs');
const logsPanel = document.getElementById('logsPanel');
const logsContent = document.getElementById('logsContent');
const clearLogsBtn = document.getElementById('clearLogs');
const connectionStatus = document.getElementById('connectionStatus');
const statusText = document.getElementById('statusText');
const configBtn = document.getElementById('configBtn');
const configModal = document.getElementById('configModal');
const closeModal = document.querySelector('.close');
const saveConfigBtn = document.getElementById('saveConfig');
const serverUrlInput = document.getElementById('serverUrl');
const connectionTypeSelect = document.getElementById('connectionType');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadConfig();
    setupEventListeners();
    addLog('Sistema iniciado', 'info');
});

// Event Listeners
function setupEventListeners() {
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    toggleLogsBtn.addEventListener('click', toggleLogs);
    clearLogsBtn.addEventListener('click', clearLogs);
    configBtn.addEventListener('click', openConfigModal);
    closeModal.addEventListener('click', closeConfigModal);
    saveConfigBtn.addEventListener('click', saveConfig);

    window.addEventListener('click', (e) => {
        if (e.target === configModal) {
            closeConfigModal();
        }
    });

    // Auto-resize textarea
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
}

// Configuration Management
function loadConfig() {
    const savedConfig = localStorage.getItem('mcpChatConfig');
    if (savedConfig) {
        config = JSON.parse(savedConfig);
        serverUrlInput.value = config.serverUrl;
        connectionTypeSelect.value = config.connectionType;
    }
    connectToServer();
}

function saveConfig() {
    config.serverUrl = serverUrlInput.value.trim();
    config.connectionType = connectionTypeSelect.value;
    
    localStorage.setItem('mcpChatConfig', JSON.stringify(config));
    addLog(`Configuración guardada: ${config.connectionType.toUpperCase()} - ${config.serverUrl}`, 'success');
    
    closeConfigModal();
    connectToServer();
}

function openConfigModal() {
    configModal.classList.add('active');
}

function closeConfigModal() {
    configModal.classList.remove('active');
}

// Connection Management
function connectToServer() {
    if (config.connectionType === 'websocket') {
        connectWebSocket();
    } else {
        connectHTTP();
    }
}

function connectHTTP() {
    updateConnectionStatus(true, 'HTTP');
    addLog(`Conectado via HTTP a ${config.serverUrl}`, 'success');
}

function connectWebSocket() {
    const wsUrl = config.serverUrl.replace('http://', 'ws://').replace('https://', 'wss://');
    
    try {
        ws = new WebSocket(`${wsUrl}/ws`);
        
        ws.onopen = () => {
            updateConnectionStatus(true, 'WebSocket');
            addLog(`Conectado via WebSocket a ${wsUrl}`, 'success');
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            addLog(`WebSocket recibido: ${JSON.stringify(data)}`, 'info');
            handleServerResponse(data);
        };
        
        ws.onerror = (error) => {
            addLog(`Error WebSocket: ${error.message || 'Error de conexión'}`, 'error');
            updateConnectionStatus(false);
        };
        
        ws.onclose = () => {
            addLog('WebSocket desconectado', 'warning');
            updateConnectionStatus(false);
        };
    } catch (error) {
        addLog(`Error al conectar WebSocket: ${error.message}`, 'error');
        updateConnectionStatus(false);
    }
}

function updateConnectionStatus(connected, type = '') {
    const statusDot = connectionStatus.querySelector('.status-dot');
    if (connected) {
        statusDot.classList.remove('disconnected');
        statusDot.classList.add('connected');
        statusText.textContent = `Conectado (${type})`;
    } else {
        statusDot.classList.remove('connected');
        statusDot.classList.add('disconnected');
        statusText.textContent = 'Desconectado';
    }
}

// Message Handling
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    addMessage(message, 'user');
    messageInput.value = '';
    messageInput.style.height = 'auto';

    addLog(`Usuario: ${message}`, 'info');

    // Show loading
    const loadingId = addMessage('Procesando<span class="loading"></span>', 'bot', true);

    try {
        if (config.connectionType === 'websocket') {
            await sendWebSocketMessage(message);
        } else {
            await sendHTTPMessage(message);
        }
    } catch (error) {
        addLog(`Error al enviar mensaje: ${error.message}`, 'error');
        removeMessage(loadingId);
        addMessage('❌ Error al procesar el mensaje. Por favor, intenta de nuevo.', 'bot');
    }
}

async function sendHTTPMessage(message) {
    addLog(`Enviando petición HTTP a ${config.serverUrl}/process`, 'info');
    
    const response = await fetch(`${config.serverUrl}/process`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ input: message })
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    addLog(`Respuesta HTTP recibida: ${JSON.stringify(data)}`, 'success');
    
    // Remove loading message
    const loadingMsg = document.querySelector('.bot-message:last-child');
    if (loadingMsg && loadingMsg.textContent.includes('Procesando')) {
        loadingMsg.remove();
    }
    
    handleServerResponse(data);
}

function sendWebSocketMessage(message) {
    return new Promise((resolve, reject) => {
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            reject(new Error('WebSocket no está conectado'));
            return;
        }

        try {
            ws.send(JSON.stringify({ message: message }));
            addLog(`Mensaje enviado via WebSocket: ${message}`, 'info');
            resolve();
        } catch (error) {
            reject(error);
        }
    });
}

function handleServerResponse(data) {
    // Remove loading message if exists
    const loadingMsg = document.querySelector('.bot-message:last-child');
    if (loadingMsg && loadingMsg.textContent.includes('Procesando')) {
        loadingMsg.remove();
    }

    let responseText = '';
    
    if (data.result) {
        responseText = data.result;
    } else if (data.response) {
        responseText = data.response;
    } else if (data.error) {
        responseText = `❌ Error: ${data.error}`;
        addLog(`Error del servidor: ${data.error}`, 'error');
    } else {
        responseText = JSON.stringify(data, null, 2);
    }

    addMessage(responseText, 'bot');

    // Log steps if available
    if (data.steps && data.steps.length > 0) {
        addLog(`Procesamiento completado con ${data.steps.length} pasos`, 'success');
        data.steps.forEach((step, index) => {
            if (step.tool_used) {
                addLog(`Paso ${index + 1}: Herramienta '${step.tool_used}' usada`, 'info');
            }
            if (step.tool_input) {
                addLog(`  - Entrada: ${JSON.stringify(step.tool_input)}`, 'info');
            }
            if (step.tool_output) {
                addLog(`  - Salida: ${step.tool_output}`, 'success');
            }
        });
    }

    // Legacy support for single tool usage
    if (data.tool_used) {
        addLog(`Herramienta utilizada: ${data.tool_used}`, 'success');
    }
    if (data.tool_input) {
        addLog(`Parámetros: ${JSON.stringify(data.tool_input)}`, 'info');
    }
}

function addMessage(text, sender, returnId = false) {
    const messageDiv = document.createElement('div');
    const messageId = `msg-${Date.now()}-${Math.random()}`;
    messageDiv.id = messageId;
    messageDiv.className = `message ${sender}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = `<strong>${sender === 'user' ? 'Tú' : 'Bot'}:</strong> ${text}`;
    
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = new Date().toLocaleTimeString();
    
    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timeDiv);
    chatMessages.appendChild(messageDiv);
    
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return returnId ? messageId : null;
}

function removeMessage(messageId) {
    const message = document.getElementById(messageId);
    if (message) {
        message.remove();
    }
}

// Logs Management
function toggleLogs() {
    logsPanel.classList.toggle('active');
    const isActive = logsPanel.classList.contains('active');
    document.getElementById('toggleText').textContent = isActive ? 'Ocultar Logs' : 'Mostrar Logs';
}

function addLog(message, level = 'info') {
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${level}`;
    
    const time = new Date().toLocaleTimeString();
    const levelText = level.toUpperCase();
    
    logEntry.innerHTML = `
        <span class="log-time">${time}</span>
        <span class="log-level">${levelText}</span>
        <span class="log-message">${message}</span>
    `;
    
    logsContent.appendChild(logEntry);
    logsContent.scrollTop = logsContent.scrollHeight;

    // Keep only last 100 logs
    while (logsContent.children.length > 100) {
        logsContent.removeChild(logsContent.firstChild);
    }
}

function clearLogs() {
    logsContent.innerHTML = '';
    addLog('Logs limpiados', 'info');
}

// Utility Functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Error handling for uncaught errors
window.addEventListener('error', (event) => {
    addLog(`Error global: ${event.error?.message || event.message}`, 'error');
});

window.addEventListener('unhandledrejection', (event) => {
    addLog(`Promise rechazada: ${event.reason}`, 'error');
});
