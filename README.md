# 🤖 LangGraph Multi-Agent System + MCP + LLM Gateway

Intelligent multi-agent system with **Model Context Protocol (MCP)**, **centralized LLM Gateway**, and support for multiple AI providers (AWS Bedrock, OpenAI, Google Gemini).

## 📋 Description

This project implements a microservices architecture for AI agents that:
- 🧠 **Centralized LLM Gateway**: Unified management of multiple LLM providers
- 🔧 **MCP Toolbox**: Tool server using Model Context Protocol over HTTP
- 🤖 **Multiple Agents**: HTTP REST and WebSocket for different integration types
- 📊 **LangGraph**: Advanced workflow orchestration
- 🐳 **Containerized**: Everything in Docker for easy deployment
- ☁️ **Production Ready**: Ready for Kubernetes/AWS EKS

### 🎯 Key Features

- ✅ **Dynamic model selection**: Switch between Bedrock, OpenAI, and Gemini from prompt
- ✅ **Intelligent caching**: Cached responses with configurable TTL
- ✅ **Real-time metrics**: Cost, token, and latency tracking
- ✅ **Tool handling**: Tool execution through MCP
- ✅ **Streaming**: WebSocket support for real-time responses
- ✅ **Health checks**: Health monitoring for all services

## 🏗️ Architecture

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
    │  • Real-time streaming│    │  • REST API           │
    │  • Multiple clients   │    │  • Request/Response   │
    │  • FastAPI + WS       │    │  • FastAPI            │
    │  • LangGraph          │    │  • LangGraph          │
    └───────────┬───────────┘    └───────────┬───────────┘
                │                            │
                │      MCP Protocol          │
                ├────────────┬───────────────┤
                │            │               │
                ▼            ▼               │
    ┌──────────────────┐  ┌─────────────────▼──────┐
    │  LLM Gateway     │  │   MCP Toolbox          │
    │  Port: 8003      │  │   Port: 8000           │
    │                  │  │                        │
    │  3 Providers:    │  │   Tools:               │
    │  • Bedrock Nova  │  │   • add                │
    │  • OpenAI GPT-4o │  │   • multiply           │
    │  • Gemini Flash  │  │   • uppercase          │
    │                  │  │   • count_words        │
    │  Features:       │  └────────────────────────┘
    │  • Cache (TTL)   │
    │  • Metrics       │
    │  • Cost tracking │
    └──────────────────┘
                
        Docker Network (mcp-network)
```

## 🔧 Components

### 1. 🧠 LLM Gateway (Port 8003)
**Centralized LLM management server**

- **Purpose**: Abstracts and unifies access to multiple AI providers
- **Supported providers**:
  - AWS Bedrock Nova Pro (`bedrock-nova-pro`)
  - OpenAI GPT-4o (`gpt-4o`)
  - Google Gemini 1.5 Flash (`gemini-pro`)
- **Features**:
  - 💰 **Cost calculation**: Estimates costs per request
  - 🚀 **TTL Cache**: Reduces external API calls
  - 📊 **Metrics**: Requests, tokens, latency, hit rate
  - 🔌 **Registry pattern**: Easy to add new LLMs
  - 🔐 **Centralized credentials**: Agents don't need API keys

**Endpoints**:
- `GET /mcp/llm/list` - List available models
- `POST /mcp/llm/generate` - Generate response with selected model
- `GET /metrics` - Get gateway metrics
- `POST /cache/clear` - Clear cache

### 2. 🛠️ MCP Toolbox (Port 8000)
**Tool server with Model Context Protocol**

- **Protocol**: MCP over HTTP REST
- **4 Tools**:
  - `add(a, b)` - Add two numbers
  - `multiply(a, b)` - Multiply two numbers
  - `uppercase(text)` - Convert text to uppercase
  - `count_words(text)` - Count words in text

**Endpoints**:
- `GET /mcp/tools/list` - List available tools
- `POST /mcp/tools/call` - Execute a tool

### 3. 🤖 Agent HTTP (Port 8001)
**Agent with REST API**

- **Framework**: FastAPI + LangGraph
- **Type**: Traditional request/response
- **Use**: Synchronous integrations, external APIs
- **Features**:
  - Model selection per request
  - Automatic model detection from prompt
  - Execution step tracking

**Endpoint**:
```bash
POST /process
{
  "input": "use gemini, how much is 5 + 3",
  "model": "gemini-pro"  # Optional
}
```

### 4. 🔌 Agent WebSocket (Port 8002)
**Agent with real-time communication**

- **Framework**: FastAPI WebSocket + LangGraph
- **Type**: Bidirectional streaming
- **Use**: Conversational interfaces, dashboards
- **Features**:
  - Multiple concurrent clients
  - Execution step streaming
  - Real-time notifications

**Connection**:
```javascript
ws://localhost:8002/ws/{connection_id}
```

## 📁 Project Structure

```
MCP-Example/
├── llm-gateway/                     # 🧠 LLM Gateway (NEW)
│   ├── src/
│   │   ├── models/                 # LLM implementations
│   │   │   ├── base.py            # Abstract class
│   │   │   ├── bedrock.py         # AWS Bedrock
│   │   │   ├── openai.py          # OpenAI GPT-4
│   │   │   └── gemini.py          # Google Gemini
│   │   ├── cache.py               # TTL cache system
│   │   ├── metrics.py             # Metrics and tracking
│   │   ├── registry.py            # LLM registry
│   │   ├── config.py              # Configuration
│   │   └── server.py              # FastAPI MCP server
│   ├── Dockerfile
│   └── requirements.txt
│
├── agents/                          # System agents
│   ├── agent-http/                  # REST API Agent
│   │   ├── src/
│   │   │   ├── graph/              # LangGraph workflow
│   │   │   │   ├── nodes.py        # Graph nodes
│   │   │   │   ├── state.py        # Agent state
│   │   │   │   └── workflow.py     # Workflow definition
│   │   │   ├── llm_client/         # LLM Gateway client (NEW)
│   │   │   ├── mcp_client/         # MCP Toolbox client
│   │   │   ├── api/                # FastAPI routes
│   │   │   ├── config.py           # Configuration
│   │   │   └── main.py             # Entry point
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   └── agent-websocket/             # WebSocket Agent
│       ├── src/
│       │   ├── graph/              # LangGraph workflow
│       │   ├── llm_client/         # LLM Gateway client (NEW)
│       │   ├── mcp_client/         # MCP Toolbox client
│       │   ├── websocket/          # WebSocket handlers
│       │   ├── config.py           # Configuration
│       │   └── main.py             # Entry point
│       ├── Dockerfile
│       └── requirements.txt
│
├── mcp-server/                      # MCP Toolbox Server
│   ├── src/
│   │   ├── tools/                  # 4 tools
│   │   │   ├── calculator.py
│   │   │   └── text_tools.py
│   │   ├── server.py               # HTTP MCP server
│   │   └── config.py               # Configuration
│   ├── Dockerfile
│   └── requirements.txt
│
├── k8s/                             # Kubernetes manifests
│   ├── namespace.yaml
│   ├── llm-gateway-*.yaml          # LLM Gateway deployment
│   ├── mcp-toolbox-*.yaml
│   ├── agent-*.yaml
│   ├── websocket-agent-*.yaml
│   └── ingress.yaml
│
├── docs/                            # Documentation
│   ├── DEPLOYMENT_EKS.md           # AWS EKS guide
│   └── WEBSOCKET_AGENT.md          # WebSocket docs
│
├── docker-compose.yml               # Docker orchestration
├── test-websocket.html              # WebSocket HTML client
├── .env                             # Environment variables (DO NOT COMMIT)
└── README.md
```

## 🚀 Installation and Usage

### Prerequisites

- Docker and Docker Compose installed
- **Credentials for at least one of:**
  - AWS (for Bedrock Nova Pro)
  - OpenAI (for GPT-4o)
  - Google Cloud (for Gemini)

### Configuration

1. **Clone the repository**

```bash
git clone https://github.com/LeonAchata/MCP-Server-Prueba.git
cd MCP-Example
```

2. **Configure environment variables**

Create `.env` file in project root:

```bash
# LLM Gateway Configuration
HOST=0.0.0.0
PORT=8003
LOG_LEVEL=INFO

# Cache Configuration
CACHE_ENABLED=true
CACHE_TTL=3600
CACHE_MAX_SIZE=1000

# AWS Bedrock Credentials (Optional)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
BEDROCK_MODEL_ID=us.amazon.nova-pro-v1:0

# OpenAI Credentials (Optional)
OPENAI_API_KEY=sk-proj-...
OPENAI_DEFAULT_MODEL=gpt-4o

# Google Gemini Credentials (Optional)
GOOGLE_API_KEY=AIzaSy...
GEMINI_DEFAULT_MODEL=gemini-1.5-flash

# MCP Configuration
MCP_SERVER_URL=http://toolbox:8000
LLM_GATEWAY_URL=http://llm-gateway:8003
```

**⚠️ Important notes:**
- Configure at least one LLM provider (Bedrock, OpenAI or Gemini)
- If using AWS, ensure you have Bedrock Nova Pro access in your region
- For OpenAI, you need credits in your account
- For Gemini, enable the API in Google Cloud Console

### Execution

**Build and start all containers:**

```bash
docker-compose up --build -d
```

The system will start 4 services:
- 🧠 **LLM Gateway** at `http://localhost:8003`
- 🔧 **MCP Toolbox** at `http://localhost:8000` (internal)
- 📡 **Agent HTTP** at `http://localhost:8001`
- 🔌 **Agent WebSocket** at `http://localhost:8002`

**View logs in real-time:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f llm-gateway
docker-compose logs -f agent-http
```

**Check service status:**
```bash
docker-compose ps
```

**Stop the system:**
```bash
docker-compose down
```

**Rebuild a specific service:**
```bash
docker-compose build llm-gateway
docker-compose up -d llm-gateway
```

## 📡 API Reference

### 🧠 LLM Gateway (Port 8003)

#### GET /health
Check gateway status:
```bash
curl http://localhost:8003/health
```

#### GET /mcp/llm/list
List all available models:
```bash
curl -X GET http://localhost:8003/mcp/llm/list
```

Response:
```json
{
  "llms": [
    {
      "name": "bedrock-nova-pro",
      "provider": "aws",
      "description": "AWS Bedrock Nova Pro - Advanced reasoning model"
    },
    {
      "name": "gpt-4o",
      "provider": "openai",
      "description": "OpenAI GPT-4o - Most capable model"
    },
    {
      "name": "gemini-pro",
      "provider": "google",
      "description": "Google Gemini - Advanced multimodal AI model (using gemini-1.5-flash)"
    }
  ]
}
```

#### POST /mcp/llm/generate
Generate response with specified model:
```bash
curl -X POST http://localhost:8003/mcp/llm/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-pro",
    "messages": [
      {"role": "user", "content": "Explain quantum computing"}
    ],
    "temperature": 0.7,
    "max_tokens": 2000
  }'
```

#### GET /metrics
Get gateway metrics:
```bash
curl http://localhost:8003/metrics
```

Response:
```json
{
  "total_requests": 42,
  "total_tokens": 15234,
  "total_cost_usd": 0.0523,
  "average_latency_ms": 1234.5,
  "cache_hit_rate": 0.35,
  "requests_by_model": {
    "bedrock-nova-pro": 20,
    "gpt-4o": 12,
    "gemini-pro": 10
  }
}
```

#### POST /cache/clear
Clear cache:
```bash
curl -X POST http://localhost:8003/cache/clear
```

### 🔧 MCP Toolbox (Port 8000)

#### GET /health
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "service": "mcp-toolbox",
  "tools_count": 4,
  "protocol": "MCP over HTTP REST"
}
```

#### POST /mcp/tools/list
List all available tools:
```bash
curl -X POST http://localhost:8000/mcp/tools/list
```

#### POST /mcp/tools/call
Execute a tool:
```bash
curl -X POST http://localhost:8000/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "add", "arguments": {"a": 5, "b": 3}}'
```

### 🤖 Agent HTTP - REST API (Port 8001)

#### GET /health
Check agent status:

```bash
curl http://localhost:8001/health
```

Response:
```json
{
  "status": "healthy",
  "mcp_connected": true,
  "bedrock_available": true
}
```

#### POST /process
Process a query using the agent with LangGraph.

**Basic syntax:**
```bash
curl -X POST http://localhost:8001/process \
  -H "Content-Type: application/json" \
  -d '{
    "input": "How much is 5 + 3?",
    "model": "bedrock-nova-pro"
  }'
```

**Example 1: Addition with Bedrock (default)**
```bash
curl -X POST http://localhost:8001/process \
  -H "Content-Type: application/json" \
  -d '{"input": "How much is 5 + 3?"}'
```

**Example 2: With Gemini (specified)**
```bash
curl -X POST http://localhost:8001/process \
  -H "Content-Type: application/json" \
  -d '{"input": "Multiply 7 by 8", "model": "gemini-pro"}'
```

**Example 3: Automatic model detection**
```bash
curl -X POST http://localhost:8001/process \
  -H "Content-Type: application/json" \
  -d '{"input": "use gemini, convert HELLO to uppercase"}'
```

**Example 4: Complex operations**
```bash
curl -X POST http://localhost:8001/process \
  -H "Content-Type: application/json" \
  -d '{"input": "Multiply 25 by 8, then convert the result to uppercase text"}'
```

**With PowerShell:**
```powershell
$body = @{
    input = "use gemini, how much is 10 + 5"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8001/process" `
  -Method POST `
  -Body $body `
  -ContentType "application/json"
```

Response:
```json
{
  "result": "The sum of 5 and 3 is 8",
  "steps": [
    {
      "node": "process_input",
      "timestamp": "2024-11-03T19:00:00",
      "input": "How much is 5 + 3?",
      "model_selected": "bedrock-nova-pro"
    },
    {
      "node": "llm",
      "timestamp": "2024-11-03T19:00:01",
      "model": "bedrock-nova-pro",
      "has_tool_calls": true
    },
    {
      "node": "tool_execution",
      "timestamp": "2024-11-03T19:00:01",
      "tools": [
        {"name": "add", "args": {"a": 5, "b": 3}, "result": "8"}
      ]
    },
    {
      "node": "llm",
      "timestamp": "2024-11-03T19:00:02",
      "model": "bedrock-nova-pro",
      "has_tool_calls": false
    },
    {"node": "final_answer", "timestamp": "2024-11-03T19:00:02"}
  ]
}
```

**Available models:**
- `bedrock-nova-pro` - AWS Bedrock Nova Pro (default)
- `gpt-4o` - OpenAI GPT-4o
- `gemini-pro` - Google Gemini 1.5 Flash

**Automatic detection:**
The agent can detect the model from the prompt with keywords:
- "use openai", "use gpt", "with gpt-4" → OpenAI
- "use gemini", "use google", "with gemini" → Gemini
- "use bedrock", "use nova", "with aws" → Bedrock

---

### 🔌 Agent WebSocket - Real-time Streaming (Port 8002)

#### GET /health
Check WebSocket agent status:

```bash
curl http://localhost:8002/health
```

Response:
```json
{
  "status": "healthy",
  "service": "websocket-agent",
  "mcp_connected": true,
  "mcp_tools": 4,
  "active_connections": 0
}
```

#### WebSocket /ws/{connection_id}
WebSocket connection for real-time communication with response streaming.

**Using the HTML client:**
1. Open `test-websocket.html` in your browser
2. Connection establishes automatically
3. Type messages like:
   - "Add 10 and 5"
   - "use gemini, multiply 25 by 8"
   - "Convert HELLO to uppercase"

**Message with specific model:**
```javascript
{
  "type": "message",
  "content": "Add 100 and 50",
  "model": "gemini-pro"  // Optional
}
```

**Using JavaScript:**
```javascript
const connectionId = 'user-' + Date.now();
const ws = new WebSocket(`ws://localhost:8002/ws/${connectionId}`);

ws.onopen = () => {
    console.log('Connected');
    
    // Send message with specific model
    ws.send(JSON.stringify({
        type: 'message',
        content: 'use gemini, add 100 and 50',
        model: 'gemini-pro'  // Optional, also detects from text
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
    
    switch(data.type) {
        case 'connected':
            console.log('✅ Connected:', data.message);
            break;
        case 'start':
            console.log('🚀', data.message);
            break;
        case 'step':
            console.log(`⚙️ ${data.node}:`, data.message);
            if (data.model) {
                console.log('  🧠 Model:', data.model);
            }
            break;
        case 'tool_call':
            console.log('🔧 Calling:', data.tool, data.args);
            break;
        case 'tool_result':
            console.log('✅ Result:', data.tool, '→', data.result);
            break;
        case 'response':
            console.log('🤖 Response:', data.content);
            break;
        case 'complete':
            console.log('✓ Completed in', data.steps, 'steps');
            break;
        case 'error':
            console.error('❌ Error:', data.message);
            break;
    }
};

ws.onerror = (error) => console.error('Error:', error);
ws.onclose = () => console.log('Disconnected');
```

**Using wscat (Node.js):**
```bash
npm install -g wscat
wscat -c ws://localhost:8002/ws/test-client

# Send message
> {"type":"message","content":"use gemini, add 10 and 5"}

# You'll receive real-time streaming:
< {"type":"start","message":"Processing..."}
< {"type":"step","node":"process_input","model":"gemini-pro"}
< {"type":"step","node":"llm","model":"gemini-pro","message":"Querying LLM..."}
< {"type":"tool_call","tool":"add","args":{"a":10,"b":5}}
< {"type":"tool_result","tool":"add","result":"15"}
< {"type":"response","content":"The sum of 10 and 5 is 15"}
< {"type":"complete","steps":5}
```

**Using Python:**
```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8002/ws/test-123"
    async with websockets.connect(uri) as websocket:
        # Send message
        await websocket.send(json.dumps({
            "type": "message",
            "content": "Add 10 and 5"
        }))
        
        # Receive streaming responses
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            print(f"{data['type']}: {data}")
            
            if data['type'] == 'complete':
                break

asyncio.run(test_websocket())
```

## 🛠️ Available Tools

The MCP Server exposes 4 tools that Claude can use:

| Tool | Description | Parameters |
|------|-------------|------------|
| `add` | Add two numbers | `a: float, b: float` |
| `multiply` | Multiply two numbers | `a: float, b: float` |
| `uppercase` | Convert text to uppercase | `text: string` |
| `count_words` | Count words in text | `text: string` |

## 💡 Complete Usage Examples

### 🧠 LLM Model Selection

**Default model (Bedrock):**
```bash
curl -X POST http://localhost:8001/process \
  -H "Content-Type: application/json" \
  -d '{"input": "Add 10 and 5"}'
```

**Explicitly specifying model:**
```bash
# With Gemini
curl -X POST http://localhost:8001/process \
  -H "Content-Type: application/json" \
  -d '{"input": "Multiply 7 by 8", "model": "gemini-pro"}'

# With OpenAI (if you have credits)
curl -X POST http://localhost:8001/process \
  -H "Content-Type: application/json" \
  -d '{"input": "Count words in: hello world", "model": "gpt-4o"}'
```

**Automatic detection from prompt:**
```bash
# Detects Gemini
curl -X POST http://localhost:8001/process \
  -H "Content-Type: application/json" \
  -d '{"input": "use gemini, how much is 15 + 25"}'

# Detects OpenAI
curl -X POST http://localhost:8001/process \
  -H "Content-Type: application/json" \
  -d '{"input": "with gpt-4, convert HELLO to uppercase"}'

# Detects Bedrock
curl -X POST http://localhost:8001/process \
  -H "Content-Type: application/json" \
  -d '{"input": "use bedrock, multiply 3 by 9"}'
```

### 📡 HTTP REST Agent

**Basic math:**
```bash
curl -X POST http://localhost:8001/process \
  -H "Content-Type: application/json" \
  -d '{"input": "Calculate 10 multiplied by 5"}'
```

**Text processing:**
```bash
curl -X POST http://localhost:8001/process \
  -H "Content-Type: application/json" \
  -d '{"input": "Convert hello world to uppercase"}'
```

**Tool combination:**
```bash
curl -X POST http://localhost:8001/process \
  -H "Content-Type: application/json" \
  -d '{"input": "Add 4 and 6, then multiply the result by 2"}'
```

**With PowerShell:**
```powershell
# Addition with Bedrock
$body = '{"input":"Add 100 and 50"}'
Invoke-WebRequest -Uri "http://localhost:8001/process" -Method POST -Body $body -ContentType "application/json"

# Multiplication with Gemini
$body = '{"input":"use gemini, multiply 25 by 8"}'
Invoke-WebRequest -Uri "http://localhost:8001/process" -Method POST -Body $body -ContentType "application/json"

# Text
$body = '{"input":"Convert HELLO WORLD to uppercase and count the words"}'
Invoke-WebRequest -Uri "http://localhost:8001/process" -Method POST -Body $body -ContentType "application/json"
```

### 🔌 WebSocket Agent

**Using the HTML client (Recommended):**
1. Open `test-websocket.html` in your browser
2. You'll see a nice interface with connection status
3. Type in the input and press Enter or click "Send"
4. Watch real-time streaming of each step
5. Steps will show the model used (in the `model` field)

**Example messages:**
- "Add 10 and 5"
- "use gemini, multiply 7 by 8"
- "with gpt-4, convert HELLO to uppercase"
- "use bedrock, count words in: the sky is blue"

**Testing from command line:**
```bash
# Install wscat
npm install -g wscat

# Connect
wscat -c ws://localhost:8002/ws/test-123

# Try different commands:
> {"type":"message","content":"Add 10 and 5"}
> {"type":"message","content":"use gemini, multiply 100 by 2"}
> {"type":"message","content":"Convert python to uppercase","model":"gemini-pro"}
> {"type":"message","content":"Count words in: MCP is awesome"}
```

### 🧪 Check LLM Gateway Metrics

```bash
# View current metrics
curl http://localhost:8003/metrics

# Clear cache
curl -X POST http://localhost:8003/cache/clear

# List available models
curl http://localhost:8003/mcp/llm/list
```

## 🔍 Logs and Debugging

**View all logs in real-time:**
```bash
docker-compose logs -f
```

**View specific service logs:**
```bash
docker-compose logs -f llm-gateway
docker-compose logs -f agent-http
docker-compose logs -f agent-websocket
docker-compose logs -f toolbox
```

**View last 50 lines:**
```bash
docker-compose logs --tail 50 agent-http
```

**Search for errors in PowerShell:**
```powershell
docker-compose logs agent-http | Select-String -Pattern "error|Error|ERROR"
```

**Logs show:**
- ✅ LLM Gateway initialization with 3 providers
- ✅ MCP client ↔ servers connection
- ✅ Tool discovery (4 tools)
- ✅ Model selection (Bedrock/OpenAI/Gemini)
- ✅ LLM calls with cache hit/miss
- ✅ Tool execution via MCP
- ✅ Cost and token metrics
- ✅ Active WebSocket connections
- ✅ Real-time message streaming

## 🛑 Stop the System

```bash
docker-compose down
```

## 🔧 Development

### Rebuild after changes

```bash
docker-compose up --build
```

### View specific service logs

```bash
docker-compose logs -f agent
docker-compose logs -f mcp-server
```

## 📚 Technologies

- **Python 3.11** - Runtime
- **FastAPI** - Web framework for REST and WebSocket
- **LangGraph** - Workflow orchestration with graphs
- **LangChain** - LLM framework
- **Amazon Bedrock** - Nova Pro (LLM model)
- **MCP (Model Context Protocol)** - Tool protocol over HTTP REST
- **WebSocket** - Bidirectional real-time communication
- **Docker & Docker Compose** - Containerization and orchestration
- **httpx** - Async HTTP client
- **boto3** - AWS SDK for Bedrock

## 📝 Important Notes

- **Microservices architecture**: 4 independent containers (LLM Gateway, Toolbox, Agent HTTP, Agent WebSocket)
- **Centralized LLM Gateway**: Single point to manage multiple AI providers
- **Secure credentials**: Only LLM Gateway has API keys, agents don't need them
- **Intelligent cache**: Reduces costs and improves latency with configurable TTL
- **MCP over HTTP REST**: Real MCP protocol with HTTP transport for K8s compatibility
- **Dynamic model selection**: Switch between Bedrock/OpenAI/Gemini per request or from prompt
- **Real-time metrics**: Cost, token, latency, and cache hit rate tracking
- **Kubernetes ready**: Works perfectly in EKS with service discovery
- **WebSocket vs HTTP**: WebSocket for interactive UIs, HTTP for integrations
- **Centralized architecture**: Both agents share the same Toolbox and LLM Gateway
- Containers automatically restart if they fail
- If your `AWS_SECRET_ACCESS_KEY` has `/`, regenerate credentials (causes signature errors)

## 🎯 Use Cases

### When to use Agent HTTP (REST):
- ✅ Integrations with other services/APIs
- ✅ Public REST APIs
- ✅ Webhooks
- ✅ Batch automations
- ✅ Systems that need caching
- ✅ Simple request/response

### When to use Agent WebSocket:
- ✅ Interactive chatbots
- ✅ Real-time chat applications
- ✅ Dashboards that need live updates
- ✅ Streaming of long responses
- ✅ Push notifications
- ✅ See agent's "thinking" step by step

### When to use each LLM:
- **Bedrock Nova Pro** (`bedrock-nova-pro`):
  - ✅ Complex reasoning
  - ✅ Long context (300K tokens)
  - ✅ Medium cost
  - ✅ Best for deep analysis

- **OpenAI GPT-4o** (`gpt-4o`):
  - ✅ Most capable and versatile
  - ✅ Best at following instructions
  - ✅ Higher cost
  - ✅ Requires active credits

- **Gemini 1.5 Flash** (`gemini-pro`):
  - ✅ Faster
  - ✅ Lower cost
  - ✅ Good for simple tasks
  - ✅ Excellent for production

## 🏢 Deployment to AWS/EKS

This project is **production ready** for AWS EKS. See complete guide at [`docs/DEPLOYMENT_EKS.md`](./docs/DEPLOYMENT_EKS.md)

**Deployment summary:**

1. **Create ECR repositories** for the 4 images (llm-gateway, toolbox, agent-http, agent-websocket)
2. **Push Docker images** to ECR
3. **Create EKS cluster** (or use existing)
4. **Configure Secrets Manager** with credentials (AWS, OpenAI, Gemini)
5. **Apply K8s manifests**:
   ```bash
   kubectl apply -f k8s/namespace.yaml
   kubectl apply -f k8s/llm-gateway-deployment.yaml
   kubectl apply -f k8s/llm-gateway-service.yaml
   kubectl apply -f k8s/mcp-toolbox-deployment.yaml
   kubectl apply -f k8s/mcp-toolbox-service.yaml
   kubectl apply -f k8s/agent-deployment.yaml
   kubectl apply -f k8s/agent-service.yaml
   kubectl apply -f k8s/websocket-agent-deployment.yaml
   kubectl apply -f k8s/websocket-agent-service.yaml
   kubectl apply -f k8s/ingress.yaml
   ```

**Service Discovery in Kubernetes:**
```yaml
# Agents connect via internal DNS:
LLM_GATEWAY_URL: "http://llm-gateway.mcp-system.svc.cluster.local:8003"
MCP_SERVER_URL: "http://mcp-toolbox.mcp-system.svc.cluster.local:8000"
```

**Architecture in EKS:**
```
Internet → ALB Ingress → {
    /api/http → Agent HTTP Service → Agent HTTP Pods
    /api/ws   → WebSocket Agent Service → WebSocket Agent Pods
}

Agent HTTP Pods ────┬──→ LLM Gateway Service → LLM Gateway Pods → {Bedrock, OpenAI, Gemini}
                    │
WebSocket Agent ────┤
                    │
                    └──→ MCP Toolbox Service → MCP Toolbox Pods
```

## 📖 Additional Documentation

- [`docs/DEPLOYMENT_EKS.md`](./docs/DEPLOYMENT_EKS.md) - Complete AWS EKS deployment guide
- [`docs/WEBSOCKET_AGENT.md`](./docs/WEBSOCKET_AGENT.md) - WebSocket Agent documentation
- [`test-websocket.html`](./test-websocket.html) - Interactive test client
- [`k8s/`](./k8s/) - Ready-to-use Kubernetes manifests

## 🚀 Quick Start

```bash
# 1. Clone repo
git clone https://github.com/LeonAchata/MCP-Server-Prueba.git
cd MCP-Example

# 2. Configure credentials (at least one provider)
nano .env
# Add credentials for AWS Bedrock, OpenAI or Google Gemini

# 3. Start services
docker-compose up -d

# 4. Verify everything is running
docker-compose ps
docker-compose logs -f

# 5. Test HTTP Agent
curl -X POST http://localhost:8001/process \
  -H "Content-Type: application/json" \
  -d '{"input":"Add 10 and 5"}'

# 6. Test with different models
curl -X POST http://localhost:8001/process \
  -H "Content-Type: application/json" \
  -d '{"input":"use gemini, multiply 7 by 8"}'

# 7. Test WebSocket Agent
# Open test-websocket.html in your browser

# 8. View gateway metrics
curl http://localhost:8003/metrics
```

## 🔧 Troubleshooting

### Error: "LLM Gateway error (404): LLM 'xxx' not found"
- Verify the model name is correct: `bedrock-nova-pro`, `gpt-4o`, or `gemini-pro`
- Check logs: `docker-compose logs llm-gateway --tail=50`

### Error: OpenAI "insufficient_quota"
- You don't have credits in your OpenAI account
- Solution: Use Bedrock or Gemini, or add credits to OpenAI

### Error: Gemini "model not found"
- Verify that `GEMINI_DEFAULT_MODEL=gemini-1.5-flash` in your `.env`
- Ensure you have Gemini API enabled in Google Cloud

### Error: "RuntimeError: Event loop is closed"
- Already fixed in current version
- If persists, verify you're using `async/await` correctly

### Containers won't start
```bash
# View detailed logs
docker-compose logs

# Rebuild everything from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 🤝 Contributions

Contributions are welcome! If you find a bug or have an improvement:

1. Fork the repository
2. Create a branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This is a personal learning project. Free to use for educational purposes.

## 👨‍💻 Author

**Leon Achata**
- GitHub: [@LeonAchata](https://github.com/LeonAchata)
- Project: [MCP-Server-Prueba](https://github.com/LeonAchata/MCP-Server-Prueba)
---

**Happy coding! 🚀**

*Multi-Agent System with MCP Protocol + LLM Gateway - Production Ready*
