# UltraMCP - Mapeo Completo de Puertos

## 🚀 Servicios Principales UltraMCP

### Core Infrastructure
| Puerto | Servicio | Estado | Descripción | URL |
|--------|----------|--------|-------------|-----|
| **5432** | PostgreSQL | ✅ Activo | Base de datos principal | `localhost:5432` |
| **6379** | Redis | ✅ Activo | Cache y sesiones | `localhost:6379` |

### Servicios AI/ML
| Puerto | Servicio | Estado | Descripción | URL |
|--------|----------|--------|-------------|-----|
| **8001** | CoD Protocol Service | ✅ Activo | Chain-of-Debate AI Orchestration | `http://localhost:8001` |
| **8001/health** | CoD Health | ✅ Activo | Health check endpoint | `http://localhost:8001/health` |
| **8001/docs** | CoD API Docs | ✅ Activo | FastAPI Swagger documentation | `http://localhost:8001/docs` |

### Web Interfaces
| Puerto | Servicio | Estado | Descripción | URL |
|--------|----------|--------|-------------|-----|
| **3000** | Simple Web Dashboard | ✅ Activo | Status dashboard básico | `http://localhost:3000` |
| **5173** | MCP Observatory | ✅ Activo | React dashboard avanzado | `http://localhost:5173` |
| **3002** | PortNote | ✅ Activo | Port mapping tool | `http://localhost:3002` |

### Backend APIs
| Puerto | Servicio | Estado | Descripción | URL |
|--------|----------|--------|-------------|-----|
| **3001** | Backend API Gateway | ❌ Pendiente | Express.js API gateway | `http://localhost:3001` |
| **8012** | Local Models Orchestrator | 📝 Configurado | Multi-model orchestration | `http://localhost:8012` |

### Servicios de Desarrollo
| Puerto | Servicio | Estado | Descripción | URL |
|--------|----------|--------|-------------|-----|
| **5174** | Frontend Dev (Alt) | ⏸️ Disponible | Vite dev server alternativo | `http://localhost:5174` |
| **11434** | Ollama (Host) | ✅ Activo | Local LLM server (host) | `http://localhost:11434` |
| **11435** | Ollama Proxy | 📝 Configurado | Docker proxy to host Ollama | `http://localhost:11435` |

## 🔧 Servicios de Monitoreo y Utilidades

### PortNote System
| Puerto | Servicio | Estado | Descripción | URL |
|--------|----------|--------|-------------|-----|
| **3002** | PortNote Web | ✅ Activo | Interface web de PortNote | `http://localhost:3002` |
| **5433** | PortNote DB | ✅ Activo | PostgreSQL para PortNote | `localhost:5433` |

### Servicios Externos (Supabase Legacy)
| Puerto | Servicio | Estado | Descripción | URL |
|--------|----------|--------|-------------|-----|
| **4000** | Supabase Realtime | ✅ Activo | Realtime subscriptions | `http://localhost:4000` |
| **5001** | Supabase Imgproxy | ✅ Activo | Image processing | `http://localhost:5001` |

## 📊 Puertos de Servicios Planeados

### Microservicios UltraMCP (No iniciados)
| Puerto | Servicio | Estado | Descripción |
|--------|----------|--------|-------------|
| **8002** | Voice System | 📝 Planeado | Sistema de voz AI |
| **8003** | Context Builder | 📝 Planeado | Constructor de contexto |
| **8004** | Blockoli MCP | 📝 Planeado | Code intelligence |
| **8005** | Asterisk Security | 📝 Planeado | Security scanning |
| **8006** | Claude Code Memory | 📝 Planeado | Memory management |
| **8007** | DeepClaude | 📝 Planeado | Metacognitive reasoning |
| **8008** | Control Tower | 📝 Planeado | Service orchestration |
| **8009** | Unified Docs | 📝 Planeado | Documentation service |
| **8010** | Actions MCP | 📝 Planeado | Action execution |

### Puertos de Desarrollo
| Puerto | Servicio | Estado | Descripción |
|--------|----------|--------|-------------|
| **3003** | MCP DevTool | 📝 Disponible | Development tools |
| **3004** | Observatory Alt | 📝 Disponible | Alternative monitoring |
| **9000** | Grafana | 📝 Planeado | Metrics dashboard |
| **9090** | Prometheus | 📝 Planeado | Metrics collection |

## 🔐 Credenciales de Acceso

### PortNote
- **URL**: http://localhost:3002
- **Usuario**: `ultramcp`
- **Contraseña**: `ultramcp_admin_2024`

### Bases de Datos
- **PostgreSQL Principal**: 
  - Host: `localhost:5432`
  - DB: `ultramcp`
  - User: `ultramcp`
  - Pass: `ultramcp_secure_2024`

- **PortNote PostgreSQL**:
  - Host: `localhost:5433`
  - DB: `postgres`
  - User: `postgres`
  - Pass: `postgres`

### Redis
- **Host**: `localhost:6379`
- **Password**: `redis_secure_2024`

## 🌐 Arquitectura de Red

### Red Docker
- **Nombre**: `ultramcp-network`
- **Tipo**: Bridge
- **Servicios conectados**: Todos los servicios UltraMCP

### Servicios Activos Actualmente
```
✅ PostgreSQL (5432)
✅ Redis (6379)  
✅ CoD Protocol Service (8001)
✅ Simple Web Dashboard (3000)
✅ MCP Observatory (5173)
✅ PortNote (3002)
✅ PortNote DB (5433)
```

### Próximos Pasos
1. Iniciar Backend API Gateway (3001)
2. Configurar servicios de microservicios
3. Implementar monitoreo con Grafana/Prometheus
4. Documentar endpoints API completos

## 📊 Modelos Locales Disponibles

### Ollama Models (Host)
| Modelo | Tamaño | Especialidad | Estado |
|--------|--------|--------------|--------|
| **qwen2.5:14b** | 9.0 GB | Razonamiento general | ✅ Activo |
| **qwen2.5-coder:7b** | 4.7 GB | Programación | ✅ Activo |
| **deepseek-coder:6.7b** | 3.8 GB | Code analysis | ✅ Activo |
| **llama3.1:8b** | 4.9 GB | General purpose | ✅ Activo |
| **mistral:7b** | 4.1 GB | Fast responses | ✅ Activo |

### Kimi-K2 (Opcional)
| Modelo | Tamaño | Especialidad | Estado |
|--------|--------|--------------|--------|
| **kimi-k2** | ~25 GB | Long context (128K) | 📝 Configurado |

**Total**: 5 modelos activos + 1 opcional

## 📝 Notas
- Todos los servicios están configurados con health checks
- PortNote nos ayuda a mapear y documentar puertos sistemáticamente
- Modelos locales funcionan completamente offline (cero costo API)
- La arquitectura está preparada para escalabilidad horizontal
- Los servicios legacy de Supabase pueden ser migrados gradualmente