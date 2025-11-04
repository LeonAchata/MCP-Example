// Configuration
let config = {
    serverUrl: 'ws://localhost:8002/ws',
    autoReconnect: true
};

let ws = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY = 3000;

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
const autoReconnectInput = document.getElementById('autoReconnect');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadConfig();
    setupEventListeners();
    addLog('Sistema iniciado', 'info');
    document.getElementById('initialTime').textContent = new Date().toLocaleTimeString();
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
    const savedConfig = localStorage.getItem('mcpWebSocketConfig');
    if (savedConfig) {
        config = JSON.parse(savedConfig);
        serverUrlInput.value = config.serverUrl;
        autoReconnectInput.checked = config.autoReconnect;
    }
    connectWebSocket();
}

function saveConfig() {
    config.serverUrl = serverUrlInput.value.trim();
    config.autoReconnect = autoReconnectInput.checked;
    
    localStorage.setItem('mcpWebSocketConfig', JSON.stringify(config));
    addLog(`Configuración guardada: ${config.serverUrl}`, 'success');
    
    closeConfigModal();
    
    // Reconectar con la nueva configuración
    if (ws) {
        ws.close();
    }
    reconnectAttempts = 0;
    connectWebSocket();
}

function openConfigModal() {
    configModal.classList.add('active');
}

function closeConfigModal() {
    configModal.classList.remove('active');
}

// WebSocket Connection Management
function connectWebSocket() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        addLog('Ya existe una conexión WebSocket activa', 'warning');
        return;
    }

    try {
        addLog(`Conectando a ${config.serverUrl}...`, 'info');
        updateConnectionStatus(false, 'Conectando...');
        
        ws = new WebSocket(config.serverUrl);
        
        ws.onopen = () => {
            reconnectAttempts = 0;
            updateConnectionStatus(true);
            addLog(`✅ Conectado a ${config.serverUrl}`, 'success');
        };
        
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleServerMessage(data);
            } catch (error) {
                addLog(`Error al parsear mensaje: ${error.message}`, 'error');
            }
        };
        
        ws.onerror = (error) => {
            addLog(`Error WebSocket: ${error.message || 'Error de conexión'}`, 'error');
        };
        
        ws.onclose = (event) => {
            updateConnectionStatus(false);
            addLog(`WebSocket cerrado (código: ${event.code})`, 'warning');
            
            // Auto-reconectar si está habilitado
            if (config.autoReconnect && reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                reconnectAttempts++;
                addLog(`Intentando reconectar (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})...`, 'info');
                setTimeout(() => connectWebSocket(), RECONNECT_DELAY);
            } else if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
                addLog('Máximo de intentos de reconexión alcanzado', 'error');
            }
        };
    } catch (error) {
        addLog(`Error al crear WebSocket: ${error.message}`, 'error');
        updateConnectionStatus(false);
    }
}

function updateConnectionStatus(connected, customText = '') {
    const statusDot = connectionStatus.querySelector('.status-dot');
    if (connected) {
        statusDot.classList.remove('disconnected');
        statusDot.classList.add('connected');
        statusText.textContent = 'Conectado (WebSocket)';
        sendButton.disabled = false;
    } else {
        statusDot.classList.remove('connected');
        statusDot.classList.add('disconnected');
        statusText.textContent = customText || 'Desconectado';
        sendButton.disabled = true;
    }
}

// Message Handling
function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    if (!ws || ws.readyState !== WebSocket.OPEN) {
        addLog('WebSocket no está conectado', 'error');
        addMessage('❌ No estás conectado al servidor. Verifica la configuración.', 'bot');
        return;
    }

    addMessage(message, 'user');
    messageInput.value = '';
    messageInput.style.height = 'auto';

    addLog(`👤 Usuario: ${message}`, 'info');

    try {
        ws.send(JSON.stringify({ 
            type: "message",
            content: message 
        }));
        addLog(`📤 Mensaje enviado via WebSocket`, 'info');
    } catch (error) {
        addLog(`Error al enviar mensaje: ${error.message}`, 'error');
        addMessage('❌ Error al enviar el mensaje. Intenta de nuevo.', 'bot');
    }
}

function handleServerMessage(data) {
    addLog(`📥 Mensaje recibido: ${JSON.stringify(data)}`, 'info');

    // Manejar diferentes tipos de mensajes
    if (data.type === 'connected') {
        handleConnectedMessage(data);
    } else if (data.type === 'start') {
        addLog(`🚀 ${data.message}`, 'info');
    } else if (data.type === 'processing') {
        addLog(`🚀 ${data.message}`, 'info');
    } else if (data.type === 'step') {
        handleStepMessage(data);
    } else if (data.type === 'result' || data.result) {
        handleResultMessage(data);
    } else if (data.type === 'error' || data.error) {
        handleErrorMessage(data);
    } else {
        addLog(`Mensaje no reconocido: ${JSON.stringify(data)}`, 'warning');
    }
}

function handleConnectedMessage(data) {
    const mcpTools = data.mcp_tools || 'desconocido';
    const model = data.bedrock_model || 'desconocido';
    addLog(`✅ ${data.message}`, 'success');
    addLog(`📊 Herramientas MCP disponibles: ${mcpTools}`, 'info');
    addLog(`🤖 Modelo Bedrock: ${model}`, 'info');
}

function handleStepMessage(data) {
    const step = data.step || data.node || 'desconocido';
    const timestamp = data.timestamp || new Date().toLocaleTimeString();
    
    addLog(`⚙️ ${step}: ${data.message || 'Procesando...'}`, 'info');
    
    // Si hay herramientas ejecutadas
    if (data.tools && Array.isArray(data.tools)) {
        data.tools.forEach(tool => {
            addLog(`🔧 Llamando ${tool.name}`, 'info');
            if (tool.args) {
                addLog(`   Parámetros: ${JSON.stringify(tool.args)}`, 'info');
            }
            if (tool.result !== undefined) {
                addLog(`   ✅ ${tool.name} → ${tool.result}`, 'success');
            } else if (tool.error) {
                addLog(`   ❌ Error: ${tool.error}`, 'error');
            }
        });
    }
}

function handleResultMessage(data) {
    const result = data.result || data.message || 'Resultado recibido';
    addMessage(result, 'bot');
    addLog(`✅ Respuesta final recibida`, 'success');
    
    // Log pasos si existen
    if (data.steps && data.steps.length > 0) {
        addLog(`Procesamiento completado con ${data.steps.length} pasos`, 'info');
    }
}

function handleErrorMessage(data) {
    const errorMsg = data.error || data.message || 'Error desconocido';
    addMessage(`❌ Error: ${errorMsg}`, 'bot');
    addLog(`❌ Error: ${errorMsg}`, 'error');
}

function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = `<strong>${sender === 'user' ? 'Tú' : 'Bot'}:</strong> ${escapeHtml(text)}`;
    
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = new Date().toLocaleTimeString();
    
    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timeDiv);
    chatMessages.appendChild(messageDiv);
    
    chatMessages.scrollTop = chatMessages.scrollHeight;
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
        <span class="log-message">${escapeHtml(message)}</span>
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

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (ws) {
        ws.close();
    }
});
