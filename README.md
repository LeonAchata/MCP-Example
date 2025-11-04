# 🤖 LangGraph Multi-Agent System + MCP Server with Bedrock

Sistema de aprendizaje sobre **Model Context Protocol (MCP)** usando LangGraph + Amazon Bedrock con **múltiples agentes** (HTTP REST y WebSocket).

## 📋 Descripción

Este proyecto implementa un sistema multi-agente inteligente que:
- Usa **LangGraph** para orquestar el flujo de trabajo
- Se conecta a **Amazon Bedrock Nova Pro** como LLM
- Comunica con un **MCP Toolbox Server centralizado** que expone 4 herramientas
- **2 Agentes diferentes**:
  - **Agent HTTP**: API REST tradicional para integraciones
  - **Agent WebSocket**: Comunicación en tiempo real con streaming
- Todo containerizado con **Docker** para fácil deployment
- **MCP sobre HTTP REST** - Protocolo MCP real con transporte HTTP
- **Listo para producción en AWS EKS**

## 🏗️ Arquitectura

```
                    ┌─────────────────────┐
                    │   Browser/Client    │
                    └──────────┬──────────┘
                               │
                ┌──────────────┴──────────────┐
                │ WebSocket                   │ HTTP REST
                ▼                             ▼
    ┌───────────────────────┐    ┌───────────────────────┐
    │  Agent WebSocket      │    │  Agent HTTP           │
    │  Port: 8002           │    │  Port: 8001           │
    │  • Streaming real-time│    │  • REST API           │
    │  • Múltiples clientes │    │  • Request/Response   │
    │  • FastAPI + WS       │    │  • FastAPI            │
    │  • LangGraph          │    │  • LangGraph          │
    │  • Bedrock Nova Pro   │    │  • Bedrock Nova Pro   │
    └───────────┬───────────┘    └───────────┬───────────┘
                │                            │
                │      HTTP REST (MCP)       │
                │                            │
                └──────────┬─────────────────┘
                           ▼
                ┌──────────────────────┐
                │   MCP Toolbox        │
                │   Port: 8000         │
                │                      │
                │   4 Tools:           │
                │   • add              │
                │   • multiply         │
                │   • uppercase        │
                │   • count_words      │
                └──────────────────────┘
                
        Docker Network (mcp-network)
```

## 🎯 MCP Protocol

Este proyecto implementa el **Model Context Protocol (MCP)** sobre HTTP REST:

- ✅ **Estructura MCP real**: Herramientas con schemas JSON
- ✅ **Endpoints MCP**: `/mcp/tools/list` y `/mcp/tools/call`
- ✅ **Formato de respuesta MCP**: Content con type y text
- ✅ **Compatible con Kubernetes**: Service discovery por DNS
- ✅ **Listo para producción**: Health checks, logs, errores

**Ventajas sobre stdio/SSE:**
- 🚀 Funciona perfecto en Docker y Kubernetes
- 🔍 Fácil de debuggear con curl/Postman
- 📊 Compatible con load balancers y service mesh
- ⚡ Más rápido y confiable en producción

## 📁 Estructura del Proyecto

```
MCP-Server-Prueba/
├── agents/                          # Agentes del sistema
│   ├── agent-http/                  # Agent REST API
│   │   ├── src/
│   │   │   ├── graph/              # LangGraph workflow
│   │   │   ├── mcp_client/         # Cliente MCP
│   │   │   ├── api/                # FastAPI routes
│   │   │   ├── config.py           # Configuración
│   │   │   └── main.py             # Entry point
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   └── agent-websocket/             # Agent WebSocket (NUEVO)
│       ├── src/
│       │   ├── graph/              # LangGraph workflow
│       │   ├── mcp_client/         # Cliente MCP (compartido)
│       │   ├── websocket/          # WebSocket handlers
│       │   ├── config.py           # Configuración
│       │   └── main.py             # Entry point
│       ├── Dockerfile
│       └── requirements.txt
│
├── mcp-server/                      # Servidor MCP Toolbox
│   ├── src/
│   │   ├── tools/                  # 4 herramientas
│   │   ├── server.py               # MCP server HTTP
│   │   └── config.py               # Configuración
│   ├── Dockerfile
│   └── requirements.txt
│
├── k8s/                             # Manifiestos Kubernetes
│   ├── namespace.yaml
│   ├── mcp-toolbox-*.yaml
│   ├── agent-deployment.yaml
│   ├── agent-service.yaml
│   ├── websocket-agent-*.yaml
│   └── ingress.yaml
│
├── docker-compose.yml               # Orquestación Docker
├── test-websocket.html              # Cliente HTML WebSocket
├── .env                             # Variables de entorno (NO SUBIR)
├── .env.example                     # Template
├── DEPLOYMENT_EKS.md                # Guía de despliegue AWS
├── WEBSOCKET_AGENT.md               # Documentación WebSocket
└── README.md
```

## 🚀 Instalación y Uso

### Prerrequisitos

- Docker y Docker Compose instalados
- Credenciales de AWS con acceso a Bedrock
- Claude 3.5 habilitado en tu cuenta AWS

### Configuración

1. **Clona el repositorio**

```bash
git clone <tu-repo>
cd JLR
```

2. **Configura las variables de entorno**

Copia el archivo de ejemplo y edita con tus credenciales:

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales de AWS:

```bash
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=tu_access_key
AWS_SECRET_ACCESS_KEY=tu_secret_key
BEDROCK_MODEL_ID=us.amazon.nova-pro-v1:0
MCP_SERVER_URL=http://mcp-server:8000
LOG_LEVEL=DEBUG
```

**⚠️ Importante:** Asegúrate de que tu `AWS_SECRET_ACCESS_KEY` no contenga el carácter `/` ya que causa problemas con la firma de AWS. Si tu clave tiene `/`, regenera tus credenciales en AWS IAM Console y elige "Código local" como caso de uso.

### Ejecución

**Construir e iniciar los contenedores:**

```bash
docker-compose up --build -d
```

El sistema iniciará 3 servicios:
- 🔧 **MCP Toolbox** en `http://localhost:8000` (interno)
- 📡 **Agent HTTP** en `http://localhost:8001`
- 🔌 **Agent WebSocket** en `http://localhost:8002`

**Ver logs:**
```bash
docker-compose logs -f
```

**Verificar estado:**
```bash
docker-compose ps
```

## 📡 Endpoints

### MCP Toolbox Server (Port 8000)

#### GET /health
```bash
curl http://localhost:8000/health
```

Respuesta:
```json
{
  "status": "healthy",
  "service": "mcp-toolbox",
  "tools_count": 4,
  "protocol": "MCP over HTTP REST"
}
```

#### POST /mcp/tools/list
Lista todas las herramientas disponibles en formato MCP:
```bash
curl -X POST http://localhost:8000/mcp/tools/list
```

#### POST /mcp/tools/call
Ejecuta una herramienta:
```bash
curl -X POST http://localhost:8000/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "add", "arguments": {"a": 5, "b": 3}}'
```

### Agent HTTP - REST API (Port 8001)

#### GET /health

Verifica el estado del agente HTTP:

```bash
curl http://localhost:8001/health
```

Respuesta:
```json
{
  "status": "healthy",
  "service": "agent",
  "mcp_connected": true,
  "bedrock_available": true,
  "bedrock_model": "us.amazon.nova-pro-v1:0"
}
```

#### POST /process

Procesa una query en lenguaje natural usando HTTP REST:

**Ejemplo 1: Suma de números**
```bash
curl -X POST http://localhost:8001/process \
  -H "Content-Type: application/json" \
  -d '{"input": "¿Cuánto es 5 + 3?"}'
```

**Ejemplo 2: Con PowerShell**
```powershell
$body = @{input="Suma 10 y 5"} | ConvertTo-Json
Invoke-WebRequest -Uri "http://localhost:8001/process" `
  -Method POST `
  -Body $body `
  -ContentType "application/json"
```

**Ejemplo 3: Operaciones complejas**
```bash
curl -X POST http://localhost:8001/process \
  -H "Content-Type: application/json" \
  -d '{"input": "Multiplica 25 por 8 y luego convierte el resultado a texto en mayúsculas"}'
```

Respuesta:
```json
{
  "result": "La suma de 5 y 3 es 8",
  "steps": [
    {"node": "process_input", "timestamp": "2024-11-03T19:00:00", "input": "¿Cuánto es 5 + 3?"},
    {"node": "llm", "timestamp": "2024-11-03T19:00:01", "has_tool_calls": true},
    {
      "node": "tool_execution", 
      "timestamp": "2024-11-03T19:00:01",
      "tools": [
        {"name": "add", "args": {"a": 5, "b": 3}, "result": "8"}
      ]
    },
    {"node": "llm", "timestamp": "2024-11-03T19:00:02", "has_tool_calls": false},
    {"node": "final_answer", "timestamp": "2024-11-03T19:00:02"}
  ]
}
```

---

### Agent WebSocket - Real-time Streaming (Port 8002)

#### GET /health

Verifica el estado del agente WebSocket:

```bash
curl http://localhost:8002/health
```

Respuesta:
```json
{
  "status": "healthy",
  "service": "websocket-agent",
  "mcp_connected": true,
  "mcp_tools": 4,
  "bedrock_available": true,
  "bedrock_model": "us.amazon.nova-pro-v1:0",
  "active_connections": 0
}
```

#### WebSocket /ws

Conexión WebSocket para comunicación en tiempo real con streaming de respuestas.

**Usando el cliente HTML:**
1. Abre `test-websocket.html` en tu navegador
2. La conexión se establece automáticamente
3. Escribe mensajes como:
   - "Suma 10 y 5"
   - "Multiplica 25 por 8"
   - "Convierte HOLA a mayúsculas"

**Usando JavaScript:**
```javascript
const ws = new WebSocket('ws://localhost:8002/ws');

ws.onopen = () => {
    console.log('Conectado');
    
    // Enviar mensaje
    ws.send(JSON.stringify({
        type: 'message',
        content: 'Suma 100 y 50'
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Recibido:', data);
    
    switch(data.type) {
        case 'connected':
            console.log('✅ Conectado:', data.message);
            break;
        case 'start':
            console.log('🚀', data.message);
            break;
        case 'step':
            console.log(`⚙️ ${data.node}:`, data.message);
            break;
        case 'tool_call':
            console.log('🔧 Llamando:', data.tool, data.args);
            break;
        case 'tool_result':
            console.log('✅ Resultado:', data.tool, '→', data.result);
            break;
        case 'response':
            console.log('🤖 Respuesta:', data.content);
            break;
        case 'complete':
            console.log('✓ Completado en', data.steps, 'pasos');
            break;
        case 'error':
            console.error('❌ Error:', data.message);
            break;
    }
};

ws.onerror = (error) => console.error('Error:', error);
ws.onclose = () => console.log('Desconectado');
```

**Usando wscat (Node.js):**
```bash
npm install -g wscat
wscat -c ws://localhost:8002/ws

# Enviar mensaje
> {"type":"message","content":"Suma 10 y 5"}

# Recibirás streaming en tiempo real:
< {"type":"start","message":"Procesando..."}
< {"type":"step","node":"llm","message":"Consultando Bedrock..."}
< {"type":"tool_call","tool":"add","args":{"a":10,"b":5}}
< {"type":"tool_result","tool":"add","result":"15"}
< {"type":"response","content":"La suma de 10 y 5 es 15"}
< {"type":"complete","steps":5}
```

**Usando Python:**
```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8002/ws"
    async with websockets.connect(uri) as websocket:
        # Enviar mensaje
        await websocket.send(json.dumps({
            "type": "message",
            "content": "Suma 10 y 5"
        }))
        
        # Recibir respuestas en streaming
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            print(f"{data['type']}: {data}")
            
            if data['type'] == 'complete':
                break

asyncio.run(test_websocket())
```

## 🛠️ Herramientas Disponibles

El MCP Server expone 4 herramientas que Claude puede usar:

| Herramienta | Descripción | Parámetros |
|-------------|-------------|------------|
| `add` | Suma dos números | `a: float, b: float` |
| `multiply` | Multiplica dos números | `a: float, b: float` |
| `uppercase` | Convierte texto a mayúsculas | `text: string` |
| `count_words` | Cuenta palabras en un texto | `text: string` |

## 💡 Ejemplos de Uso

### 📡 HTTP REST Agent

**Matemáticas básicas:**
```bash
curl -X POST http://localhost:8001/process \
  -H "Content-Type: application/json" \
  -d '{"input": "Calcula 10 multiplicado por 5"}'
```

**Procesamiento de texto:**
```bash
curl -X POST http://localhost:8001/process \
  -H "Content-Type: application/json" \
  -d '{"input": "Convierte hello world a mayúsculas"}'
```

**Combinación de herramientas:**
```bash
curl -X POST http://localhost:8001/process \
  -H "Content-Type: application/json" \
  -d '{"input": "Suma 4 y 6, luego multiplica el resultado por 2"}'
```

**Con PowerShell:**
```powershell
# Suma
$body = '{"input":"Suma 100 y 50"}'
Invoke-WebRequest -Uri "http://localhost:8001/process" -Method POST -Body $body -ContentType "application/json"

# Multiplicación
$body = '{"input":"Multiplica 25 por 8"}'
Invoke-WebRequest -Uri "http://localhost:8001/process" -Method POST -Body $body -ContentType "application/json"

# Texto
$body = '{"input":"Convierte HOLA MUNDO a mayúsculas y cuenta las palabras"}'
Invoke-WebRequest -Uri "http://localhost:8001/process" -Method POST -Body $body -ContentType "application/json"
```

### 🔌 WebSocket Agent

**Usando el cliente HTML (Recomendado):**
1. Abre el archivo `test-websocket.html` en tu navegador
2. Verás una interfaz bonita con el estado de conexión
3. Escribe en el input y presiona Enter o clic en "Enviar"
4. Observa el streaming en tiempo real de cada paso

**Pruebas desde línea de comandos:**
```bash
# Instalar wscat
npm install -g wscat

# Conectar
wscat -c ws://localhost:8002/ws

# Probar diferentes comandos:
> {"type":"message","content":"Suma 10 y 5"}
> {"type":"message","content":"Multiplica 100 por 2"}
> {"type":"message","content":"Convierte python a mayúsculas"}
> {"type":"message","content":"Cuenta las palabras en: El MCP es genial"}
```

## 🔍 Logs y Debugging

**Ver todos los logs en tiempo real:**
```bash
docker-compose logs -f
```

**Ver logs de un servicio específico:**
```bash
docker-compose logs -f agent-http
docker-compose logs -f agent-websocket
docker-compose logs -f mcp-server
```

**Ver últimas 50 líneas:**
```bash
docker-compose logs --tail 50 agent-http
```

**Buscar errores:**
```bash
docker-compose logs agent-websocket | Select-String -Pattern "error|Error"
```

**Los logs muestran:**
- ✅ Conexión MCP client ↔ server
- ✅ Discovery de herramientas (4 tools)
- ✅ Llamadas a Bedrock Nova Pro
- ✅ Ejecución de herramientas via MCP
- ✅ Resultados de cada paso
- ✅ Conexiones WebSocket activas
- ✅ Streaming de mensajes en tiempo real

## 🛑 Detener el Sistema

```bash
docker-compose down
```

## 🔧 Desarrollo

### Reconstruir después de cambios

```bash
docker-compose up --build
```

### Ver logs de un servicio específico

```bash
docker-compose logs -f agent
docker-compose logs -f mcp-server
```

## 📚 Tecnologías

- **Python 3.11** - Runtime
- **FastAPI** - Framework web para REST y WebSocket
- **LangGraph** - Orquestación de workflows con grafos
- **LangChain** - Framework para LLM
- **Amazon Bedrock** - Nova Pro (modelo LLM)
- **MCP (Model Context Protocol)** - Protocolo de herramientas sobre HTTP REST
- **WebSocket** - Comunicación bidireccional en tiempo real
- **Docker & Docker Compose** - Containerización y orquestación
- **httpx** - Cliente HTTP asíncrono
- **boto3** - SDK de AWS para Bedrock

## ⚠️ Notas Importantes

- **NO subir el archivo `.env`** a GitHub (ya está en `.gitignore`)
- Las credenciales de AWS son sensibles - manéjalas con cuidado
- **MCP sobre HTTP REST**: Usa el protocolo MCP real pero con transporte HTTP en lugar de stdio/SSE
- **Listo para Kubernetes**: Funciona perfecto en EKS con service discovery
- Los contenedores se reinician automáticamente si fallan
- **WebSocket vs HTTP**: Usa WebSocket para UIs interactivas, HTTP para integraciones
- **Ambos agentes comparten el mismo MCP Toolbox** - Arquitectura centralizada
- Si `AWS_SECRET_ACCESS_KEY` tiene `/`, regenera las credenciales (causa errores de firma)

## 🎯 Casos de Uso

### Cuándo usar Agent HTTP (REST):
- ✅ Integraciones con otros servicios
- ✅ APIs públicas
- ✅ Webhooks
- ✅ Automatizaciones batch
- ✅ Sistemas que necesitan caching
- ✅ Request/response simple

### Cuándo usar Agent WebSocket:
- ✅ Chatbots interactivos
- ✅ Aplicaciones de chat en tiempo real
- ✅ Dashboards que necesitan updates live
- ✅ Streaming de respuestas largas
- ✅ Notificaciones push
- ✅ Ver el "pensamiento" del agente paso a paso

## 🏢 Deployment a AWS/EKS

Este proyecto está **listo para producción** en AWS EKS. Ver guía completa en [`DEPLOYMENT_EKS.md`](./DEPLOYMENT_EKS.md)

**Resumen de deployment:**

1. **Crear repositorios ECR** para las 3 imágenes
2. **Push imágenes Docker** a ECR
3. **Crear cluster EKS** (o usar existente)
4. **Configurar Secrets Manager** con credenciales AWS
5. **Aplicar manifiestos K8s**:
   ```bash
   kubectl apply -f k8s/namespace.yaml
   kubectl apply -f k8s/mcp-toolbox-deployment.yaml
   kubectl apply -f k8s/mcp-toolbox-service.yaml
   kubectl apply -f k8s/agent-deployment.yaml
   kubectl apply -f k8s/agent-service.yaml
   kubectl apply -f k8s/websocket-agent-deployment.yaml
   kubectl apply -f k8s/websocket-agent-service.yaml
   kubectl apply -f k8s/ingress.yaml
   ```

**Service Discovery en Kubernetes:**
```yaml
# Los agents se conectan al toolbox via DNS interno:
MCP_SERVER_URL: "http://mcp-toolbox.mcp-system.svc.cluster.local:8000"
```

**Arquitectura en EKS:**
```
Internet → ALB Ingress → {
    /api/http → Agent HTTP Service → Agent HTTP Pods
    /api/ws   → WebSocket Agent Service → WebSocket Agent Pods
}

Agent HTTP Pods ────┐
                    ├──→ MCP Toolbox Service → MCP Toolbox Pods
WebSocket Agent ────┘
```

## 📖 Documentación Adicional

- [`DEPLOYMENT_EKS.md`](./DEPLOYMENT_EKS.md) - Guía completa de despliegue en AWS EKS
- [`WEBSOCKET_AGENT.md`](./WEBSOCKET_AGENT.md) - Documentación del Agent WebSocket
- [`test-websocket.html`](./test-websocket.html) - Cliente de prueba interactivo
- [`k8s/`](./k8s/) - Manifiestos de Kubernetes listos para usar

## 🚀 Quick Start

```bash
# 1. Clonar repo
git clone <tu-repo>
cd MCP-Server-Prueba

# 2. Configurar credenciales
cp .env.example .env
# Editar .env con tus credenciales AWS

# 3. Levantar servicios
docker-compose up -d

# 4. Probar HTTP Agent
curl -X POST http://localhost:8001/process \
  -H "Content-Type: application/json" \
  -d '{"input":"Suma 10 y 5"}'

# 5. Probar WebSocket Agent
# Abre test-websocket.html en tu navegador
```

## 📝 Licencia

Este es un proyecto de aprendizaje personal.

## Autor:

Leon Achata

---

**Happy coding! 🚀**

*Sistema Multi-Agent con MCP Protocol - Listo para producción en AWS EKS*
