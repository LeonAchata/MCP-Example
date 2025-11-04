# Frontend - MCP Chatbot

Frontend simple para interactuar con el sistema de agentes MCP.

## 🏗️ Arquitectura del Sistema

```
┌─────────────────┐
│   Frontend      │ (HTML/CSS/JS - Este archivo)
│  localhost:8080 │
└────────┬────────┘
         │ HTTP REST
         ↓
┌─────────────────┐
│  Agent HTTP     │ (FastAPI + LangGraph + Bedrock)
│  localhost:8001 │ 
└────────┬────────┘
         │ HTTP REST (MCP Protocol)
         ↓
┌─────────────────┐
│  MCP Server     │ (MCP Toolbox - Herramientas)
│  localhost:8000 │
└─────────────────┘
         │
    ┌────┴────┐
    ↓         ↓
[Calculator] [Text Tools]
```

**Flujo de comunicación:**
1. **Frontend → Agent** (puerto 8001): Envía mensaje del usuario
2. **Agent → MCP Server** (puerto 8000): Solicita herramientas vía HTTP REST
3. **MCP Server**: Ejecuta las herramientas localmente
4. **MCP Server → Agent**: Devuelve resultados
5. **Agent → Frontend**: Devuelve respuesta procesada

## 🚀 Inicio Rápido

### Opción 1: Abrir directamente en el navegador

1. Navega a la carpeta `frontend`
2. Abre `index.html` en tu navegador web favorito

### Opción 2: Usar un servidor local

```bash
# Con Python
cd frontend
python -m http.server 8080

# Con Node.js (si tienes http-server instalado)
cd frontend
npx http-server -p 8080

# Luego abre: http://localhost:8080
```

## ⚙️ Configuración

1. Haz clic en el botón **⚙️ Configuración** en la esquina inferior derecha
2. Configura los siguientes parámetros:
   - **URL del Servidor**: `http://localhost:8001` (por defecto)
   - **Tipo de Conexión**: 
     - `HTTP` - Para el agent-http (puerto 8001)
     - `WebSocket` - Para el agent-websocket (puerto 8002)
3. Haz clic en **Guardar y Conectar**

## 💬 Uso

### Comandos de Ejemplo

**Calculadora:**
- "calcula 5 + 3"
- "cuánto es 10 * 25"
- "divide 100 entre 4"
- "raíz cuadrada de 16"

**Manipulación de Texto:**
- "convierte 'hola mundo' a mayúsculas"
- "pon en minúsculas 'HOLA MUNDO'"
- "capitaliza 'hola mundo'"
- "invierte el texto 'hola'"
- "cuenta las palabras en 'este es un texto de prueba'"

### Panel de Logs

- Haz clic en **📊 Mostrar Logs** para ver el panel de logs
- Los logs muestran toda la actividad del sistema:
  - 🔵 INFO: Información general
  - 🟢 SUCCESS: Operaciones exitosas
  - 🟡 WARNING: Advertencias
  - 🔴 ERROR: Errores
- Usa el botón **Limpiar** para vaciar los logs

## 🔧 Estructura de Archivos

```
frontend/
├── index.html      # Estructura HTML principal
├── styles.css      # Estilos y diseño
├── app.js          # Lógica de la aplicación
└── README.md       # Este archivo
```

## 🌐 Endpoints del Backend

### Puertos Disponibles:
- **8000**: MCP Server (Toolbox) - NO acceder directamente
- **8001**: Agent HTTP - Usar este para HTTP
- **8002**: Agent WebSocket - Usar este para WebSocket

### Agent HTTP (puerto 8001)

- `GET /` - Información del servicio
- `GET /health` - Estado de salud
- `POST /process` - Procesar mensaje
  ```json
  {
    "input": "tu mensaje aquí"
  }
  ```

### Agent WebSocket (puerto 8002)

- `GET /` - Información del servicio
- `GET /health` - Estado de salud
- `WS /ws` - Conexión WebSocket

## 🎨 Características

- ✅ Interfaz conversacional intuitiva
- ✅ Soporte HTTP y WebSocket
- ✅ Panel de logs detallado y filtrable
- ✅ Indicador de estado de conexión
- ✅ Configuración persistente (localStorage)
- ✅ Diseño responsive
- ✅ Animaciones suaves
- ✅ Manejo de errores robusto

## 🐛 Solución de Problemas

### Error: "Failed to fetch"

**Causa**: El servidor no está corriendo o hay problemas de CORS.

**Solución**:
1. Asegúrate de que el servidor backend esté corriendo:
   ```bash
   docker-compose up agent-http
   ```
2. Verifica que la URL en la configuración sea correcta
3. Verifica que CORS esté habilitado en el backend

### El WebSocket no se conecta

**Causa**: El agent-websocket no está corriendo o la URL es incorrecta.

**Solución**:
1. Verifica que el servicio esté corriendo:
   ```bash
   docker-compose up agent-websocket
   ```
2. La URL debe ser `http://localhost:8002` (sin `/ws` al final)

### "No puedo ver las herramientas MCP"

**Causa**: Los servicios no están conectados correctamente.

**Solución**:
1. Verifica que todos los servicios estén corriendo:
   ```bash
   docker-compose ps
   ```
2. El orden correcto es: `mcp-server` → `agent-http` → `frontend`
3. Verifica los logs:
   ```bash
   docker-compose logs agent-http
   ```

### Los logs no aparecen

**Solución**: Haz clic en el botón "📊 Mostrar Logs" en la parte superior derecha

## � Reiniciar Agentes Después de Cambios en el Código

Cuando hagas cambios en el código de los agentes (Python), necesitas reiniciar los contenedores para que los cambios se apliquen. Aquí están los comandos en orden:

### PowerShell (Windows)

```powershell
# 1. Detener y eliminar contenedores, redes, y volúmenes
docker-compose down

# 2. Eliminar contenedores antiguos por si acaso
docker stop agent-http agent-websocket mcp-server
docker rm agent-http agent-websocket mcp-server

# 3. Reconstruir las imágenes (esto recompila el código)
docker-compose build --no-cache

# 4. Iniciar los servicios en modo detached (background)
docker-compose up -d

# 5. Esperar a que los servicios estén listos (opcional pero recomendado)
Start-Sleep -Seconds 10

# 6. Verificar que los servicios estén corriendo
docker-compose ps

# 7. Ver los logs en tiempo real (Ctrl+C para salir)
docker-compose logs -f
```

### Bash (Linux/Mac)

```bash
# 1. Detener y eliminar contenedores
docker-compose down

# 2. Eliminar contenedores antiguos
docker stop agent-http agent-websocket mcp-server
docker rm agent-http agent-websocket mcp-server

# 3. Reconstruir sin cache
docker-compose build --no-cache

# 4. Iniciar servicios
docker-compose up -d

# 5. Esperar 10 segundos
sleep 10

# 6. Verificar estado
docker-compose ps

# 7. Ver logs
docker-compose logs -f
```

### Reinicio Rápido (Sin Reconstruir)

Si solo hiciste cambios menores y sabes que el contenedor tiene el código correcto:

```powershell
# PowerShell
docker-compose restart
Start-Sleep -Seconds 5
docker-compose ps
```

```bash
# Bash
docker-compose restart
sleep 5
docker-compose ps
```

### Reiniciar Solo un Servicio Específico

```powershell
# PowerShell - Solo reconstruir agent-http
docker-compose stop agent
docker-compose build --no-cache agent
docker-compose up -d agent
Start-Sleep -Seconds 5
docker-compose logs agent --tail=20
```

```bash
# Bash - Solo reconstruir agent-http
docker-compose stop agent
docker-compose build --no-cache agent
docker-compose up -d agent
sleep 5
docker-compose logs agent --tail=20
```

### Script Completo de Reinicio (PowerShell)

Guarda esto como `restart-agents.ps1`:

```powershell
Write-Host "🔄 Deteniendo servicios..." -ForegroundColor Yellow
docker-compose down

Write-Host "🧹 Limpiando contenedores antiguos..." -ForegroundColor Yellow
docker stop agent-http agent-websocket mcp-server 2>$null
docker rm agent-http agent-websocket mcp-server 2>$null

Write-Host "🏗️ Reconstruyendo imágenes..." -ForegroundColor Cyan
docker-compose build --no-cache

Write-Host "🚀 Iniciando servicios..." -ForegroundColor Green
docker-compose up -d

Write-Host "⏳ Esperando a que los servicios inicien..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "✅ Estado de los servicios:" -ForegroundColor Green
docker-compose ps

Write-Host "`n📊 Logs recientes:" -ForegroundColor Cyan
docker-compose logs --tail=5

Write-Host "`n✅ Servicios reiniciados correctamente!" -ForegroundColor Green
Write-Host "💡 Para ver logs en tiempo real: docker-compose logs -f" -ForegroundColor Blue
```

Ejecuta con: `.\restart-agents.ps1`

### Script Completo de Reinicio (Bash)

Guarda esto como `restart-agents.sh`:

```bash
#!/bin/bash

echo "🔄 Deteniendo servicios..."
docker-compose down

echo "🧹 Limpiando contenedores antiguos..."
docker stop agent-http agent-websocket mcp-server 2>/dev/null
docker rm agent-http agent-websocket mcp-server 2>/dev/null

echo "🏗️ Reconstruyendo imágenes..."
docker-compose build --no-cache

echo "🚀 Iniciando servicios..."
docker-compose up -d

echo "⏳ Esperando a que los servicios inicien..."
sleep 10

echo "✅ Estado de los servicios:"
docker-compose ps

echo -e "\n📊 Logs recientes:"
docker-compose logs --tail=5

echo -e "\n✅ Servicios reiniciados correctamente!"
echo "💡 Para ver logs en tiempo real: docker-compose logs -f"
```

Ejecuta con: `chmod +x restart-agents.sh && ./restart-agents.sh`

### Verificar que los Cambios se Aplicaron

```powershell
# Verificar el contenido de un archivo dentro del contenedor
docker exec agent-http cat /app/src/main.py | Select-String -Pattern "CORS"

# Ver la fecha de creación de la imagen
docker images | Select-String "mcp-example"

# Verificar que el servicio responda correctamente
curl.exe -X POST http://localhost:8001/process -H "Content-Type: application/json" -d '{\"input\": \"suma 2 mas 3\"}'
```

### Comandos Útiles Adicionales

```powershell
# Ver logs de un servicio específico
docker-compose logs agent -f

# Ver logs de los últimos 50 líneas
docker-compose logs agent --tail=50

# Entrar al contenedor (debugging)
docker exec -it agent-http /bin/bash

# Ver uso de recursos
docker stats agent-http agent-websocket mcp-server

# Limpiar todo (imágenes, contenedores, volúmenes, etc.)
docker system prune -a --volumes
```

## �📝 Notas

- La configuración se guarda automáticamente en el localStorage del navegador
- Los logs se mantienen en memoria y se pierden al recargar la página
- Se mantienen máximo 100 entradas de logs
- El frontend es completamente estático y no requiere compilación

## 🔒 Consideraciones de Producción

Si vas a desplegar en producción:

1. **CORS**: Configura CORS específicamente para tu dominio en el backend
2. **HTTPS**: Usa HTTPS para conexiones seguras
3. **WebSocket Seguro**: Usa `wss://` en lugar de `ws://`
4. **Validación**: Agrega validación adicional de entrada
5. **Rate Limiting**: Implementa límites de tasa en el backend
