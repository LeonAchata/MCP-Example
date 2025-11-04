# 🔌 Agregar Agente con WebSocket al MCP Toolbox

## Arquitectura

```
┌─────────────────┐
│   Client/UI     │
│  (Browser/App)  │
└────────┬────────┘
         │ WebSocket
         ▼
┌─────────────────────────────┐
│   WebSocket Agent           │
│   - FastAPI + WebSocket     │
│   - LangGraph Workflow      │
│   - Bedrock Integration     │
└────────┬────────────────────┘
         │ HTTP REST (MCP)
         ▼
┌─────────────────────────────┐
│   MCP Toolbox               │
│   - 4 herramientas          │
│   - add, multiply, etc.     │
└─────────────────────────────┘
         ▲
         │ HTTP REST (MCP)
┌────────┴────────────────────┐
│   HTTP Agent (existente)    │
│   - REST API                │
│   - LangGraph Workflow      │
└─────────────────────────────┘
```

## Ventajas de WebSocket

✅ **Comunicación bidireccional en tiempo real**
✅ **Streaming de respuestas** (ver el agente "pensando")
✅ **Múltiples clientes conectados simultáneamente**
✅ **Notificaciones push** desde el servidor
✅ **Perfecto para chatbots y UI interactivas**

---

## Implementación

### 1. Estructura del Proyecto

```
websocket-agent/
├── Dockerfile
├── requirements.txt
└── src/
    ├── __init__.py
    ├── config.py
    ├── main.py              # FastAPI + WebSocket
    ├── websocket/
    │   ├── __init__.py
    │   ├── connection.py    # ConnectionManager
    │   └── handlers.py      # Message handlers
    ├── graph/               # Mismo que agent (reutilizar)
    │   ├── __init__.py
    │   ├── nodes.py
    │   ├── state.py
    │   └── workflow.py
    └── mcp_client/          # Mismo que agent (reutilizar)
        ├── __init__.py
        └── client.py
```

### 2. Ventajas del Diseño MCP

Como ya tienes **MCP Toolbox centralizado**, el nuevo agente WebSocket:

✅ **Reutiliza el mismo MCP Client** → No duplicas código
✅ **Usa las mismas herramientas** → Consistencia
✅ **Comparte la toolbox** → Los 2 agentes pueden usar add, multiply, etc.
✅ **Escalabilidad** → Puedes agregar N agentes (REST, WebSocket, gRPC, etc.)

### 3. Diferencias entre Agentes

| Característica | HTTP Agent | WebSocket Agent |
|----------------|------------|-----------------|
| Protocolo | HTTP REST | WebSocket |
| Comunicación | Request/Response | Bidireccional |
| Streaming | No | Sí |
| Use case | APIs, integraciones | Chat, UI interactiva |
| Conexión | Stateless | Stateful |
| MCP Toolbox | ✅ HTTP REST | ✅ HTTP REST |

**IMPORTANTE**: Ambos agentes se comunican con el **mismo MCP Toolbox usando HTTP REST**. Solo la comunicación Cliente→Agente cambia (HTTP vs WebSocket).

---

## Código del WebSocket Agent

Ya creé los archivos. Revisa:
- `websocket-agent/src/main.py` - FastAPI con WebSocket endpoint
- `websocket-agent/src/websocket/connection.py` - ConnectionManager
- `websocket-agent/src/websocket/handlers.py` - Lógica de mensajes

### Características incluidas:

✅ **Streaming de pasos del workflow** en tiempo real
✅ **Múltiples clientes simultáneos** (ConnectionManager)
✅ **Mensajes estructurados** (JSON con tipos)
✅ **Manejo de errores** con reconexión automática
✅ **Health check** para Kubernetes
✅ **Reutiliza MCP Client existente** → Mismas herramientas

---

## Protocolo de Mensajes WebSocket

### Cliente → Servidor

```json
{
  "type": "message",
  "content": "Suma 10 y 5"
}
```

### Servidor → Cliente

```json
// 1. Inicio del procesamiento
{
  "type": "start",
  "message": "Procesando tu solicitud..."
}

// 2. Paso del workflow
{
  "type": "step",
  "node": "llm",
  "message": "Consultando a Bedrock..."
}

// 3. Llamada a herramienta MCP
{
  "type": "tool_call",
  "tool": "add",
  "args": {"a": 10, "b": 5}
}

// 4. Resultado de herramienta
{
  "type": "tool_result",
  "tool": "add",
  "result": "15"
}

// 5. Respuesta final
{
  "type": "response",
  "content": "La suma de 10 y 5 es 15."
}

// 6. Completado
{
  "type": "complete",
  "steps": 5
}
```

---

## Despliegue

### Docker Compose (Local)

Actualiza `docker-compose.yml`:

```yaml
services:
  # ... mcp-server y agent existentes ...

  websocket-agent:
    build:
      context: ./websocket-agent
      dockerfile: Dockerfile
    container_name: websocket-agent
    ports:
      - "8002:8000"  # Puerto diferente
    environment:
      - MCP_SERVER_URL=http://mcp-server:8000
      - AWS_REGION=${AWS_REGION}
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - BEDROCK_MODEL_ID=${BEDROCK_MODEL_ID}
      - LOG_LEVEL=DEBUG
    depends_on:
      mcp-server:
        condition: service_healthy
    networks:
      - mcp-network
```

### Kubernetes (EKS)

Ya creé los manifiestos en `k8s/`:
- `websocket-agent-deployment.yaml`
- `websocket-agent-service.yaml`

```bash
kubectl apply -f k8s/websocket-agent-deployment.yaml
kubectl apply -f k8s/websocket-agent-service.yaml
```

---

## Cliente de Prueba (HTML/JavaScript)

```html
<!DOCTYPE html>
<html>
<head>
    <title>MCP WebSocket Agent Test</title>
    <style>
        body { font-family: Arial; padding: 20px; }
        #messages { 
            border: 1px solid #ccc; 
            height: 400px; 
            overflow-y: scroll; 
            padding: 10px; 
            margin-bottom: 10px;
        }
        .message { margin: 5px 0; padding: 5px; }
        .user { background: #e3f2fd; }
        .agent { background: #f3e5f5; }
        .step { background: #fff3e0; font-size: 0.9em; }
        .tool { background: #e8f5e9; font-family: monospace; }
    </style>
</head>
<body>
    <h1>🔌 MCP WebSocket Agent</h1>
    <div id="messages"></div>
    <input type="text" id="input" placeholder="Escribe tu mensaje..." style="width: 80%;">
    <button onclick="sendMessage()">Enviar</button>
    <button onclick="connect()">Conectar</button>
    <button onclick="disconnect()">Desconectar</button>

    <script>
        let ws = null;
        const messages = document.getElementById('messages');
        const input = document.getElementById('input');

        function connect() {
            ws = new WebSocket('ws://localhost:8002/ws');
            
            ws.onopen = () => {
                addMessage('✅ Conectado al agente', 'step');
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                handleMessage(data);
            };
            
            ws.onclose = () => {
                addMessage('❌ Desconectado', 'step');
            };
            
            ws.onerror = (error) => {
                addMessage('⚠️ Error: ' + error, 'step');
            };
        }

        function disconnect() {
            if (ws) ws.close();
        }

        function sendMessage() {
            if (!ws || ws.readyState !== WebSocket.OPEN) {
                alert('No conectado al servidor');
                return;
            }
            
            const message = input.value;
            if (!message) return;
            
            addMessage('👤 ' + message, 'user');
            ws.send(JSON.stringify({
                type: 'message',
                content: message
            }));
            
            input.value = '';
        }

        function handleMessage(data) {
            switch(data.type) {
                case 'start':
                    addMessage('🚀 ' + data.message, 'step');
                    break;
                case 'step':
                    addMessage(`⚙️ ${data.node}: ${data.message}`, 'step');
                    break;
                case 'tool_call':
                    addMessage(`🔧 Llamando ${data.tool}(${JSON.stringify(data.args)})`, 'tool');
                    break;
                case 'tool_result':
                    addMessage(`✅ ${data.tool} → ${data.result}`, 'tool');
                    break;
                case 'response':
                    addMessage('🤖 ' + data.content, 'agent');
                    break;
                case 'complete':
                    addMessage(`✓ Completado (${data.steps} pasos)`, 'step');
                    break;
                case 'error':
                    addMessage('❌ Error: ' + data.message, 'step');
                    break;
            }
        }

        function addMessage(text, className) {
            const div = document.createElement('div');
            div.className = 'message ' + className;
            div.textContent = text;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }

        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });

        // Auto-conectar al cargar
        connect();
    </script>
</body>
</html>
```

Guarda como `test-websocket.html` y ábrelo en tu navegador.

---

## Probar con curl/wscat

```bash
# Instalar wscat
npm install -g wscat

# Conectar
wscat -c ws://localhost:8002/ws

# Enviar mensaje
> {"type":"message","content":"Suma 100 y 50"}

# Verás el streaming en tiempo real
< {"type":"start","message":"Procesando..."}
< {"type":"step","node":"llm","message":"Consultando Bedrock..."}
< {"type":"tool_call","tool":"add","args":{"a":100,"b":50}}
< {"type":"tool_result","tool":"add","result":"150"}
< {"type":"response","content":"La suma es 150"}
< {"type":"complete","steps":5}
```

---

## Comparación: REST vs WebSocket

### Cuándo usar HTTP Agent (REST):
- ✅ Integraciones con otros servicios
- ✅ APIs públicas
- ✅ Webhooks
- ✅ Automatizaciones
- ✅ Caching fácil

### Cuándo usar WebSocket Agent:
- ✅ Chatbots interactivos
- ✅ Aplicaciones de chat
- ✅ Dashboards en tiempo real
- ✅ Streaming de respuestas largas
- ✅ Notificaciones push

### Lo mejor: **¡Usar ambos!**

Ambos comparten el mismo **MCP Toolbox**, así que:
- Mantienes una sola fuente de verdad para herramientas
- Puedes cambiar/agregar tools sin tocar los agentes
- Escalas horizontalmente cada servicio independientemente

---

## 🚀 Próximos Pasos

1. **Levantar WebSocket Agent localmente**:
```bash
cd websocket-agent
docker-compose up -d websocket-agent
```

2. **Probar con el cliente HTML**:
```bash
# Abrir test-websocket.html en el navegador
start test-websocket.html
```

3. **Ver logs en tiempo real**:
```bash
docker-compose logs -f websocket-agent
```

4. **Desplegar en EKS** (cuando esté listo):
```bash
kubectl apply -f k8s/websocket-agent-deployment.yaml
```

---

¿Quieres que cree el código completo del WebSocket Agent ahora? 🚀
