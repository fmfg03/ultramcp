# Security & Control Implementation

## 🔐 **Sistema de Seguridad Completo Implementado**

He implementado un sistema de seguridad y control robusto para el sistema MCP que incluye todas las características solicitadas y más.

---

## 🛡️ **Componentes de Seguridad**

### **1. SecurityMiddleware (`backend/src/middleware/securityMiddleware.js`)**

#### **🚦 Rate Limiting Inteligente:**
- **General API**: 100 req/15min (prod) / 1000 req/15min (dev)
- **MCP Endpoints**: 50 req/10min (prod) / 500 req/10min (dev)
- **Studio Endpoints**: 200 req/15min (prod) / 2000 req/15min (dev)
- **Auth Endpoints**: 5 req/5min (prod) / 50 req/5min (dev)

#### **🔑 Autenticación Multi-Nivel:**
```javascript
// IP-based authentication
app.use('/mcp', securityManager.ipAuthMiddleware());

// Token-based authentication
app.use('/analytics', securityManager.tokenAuthMiddleware());

// Studio-specific authentication
app.use('/studio', securityManager.studioAuthMiddleware());

// MCP API key authentication
app.use('/mcp', securityManager.mcpAuthMiddleware());
```

#### **🛡️ Características de Seguridad:**
- **Input Sanitization**: Limpieza automática de XSS y injection
- **Security Headers**: Helmet.js con configuración robusta
- **Audit Logging**: Log de todos los eventos de seguridad
- **IP Whitelisting**: Control de acceso por IP
- **JWT Token Management**: Tokens seguros con expiración

### **2. EnvironmentManager (`backend/src/utils/environmentManager.js`)**

#### **🌍 Detección Automática de Entorno:**
```javascript
// Múltiples métodos de detección:
1. NODE_ENV explícito
2. Argumentos de línea de comandos (--prod, --dev, --test)
3. Variables de entorno (PRODUCTION, CI, DEBUG)
4. Análisis de puerto (80/443 = prod, 3000 = dev)
5. Estructura de directorios (/prod, /dev, /test)
6. Análisis de package.json scripts
7. Indicadores del sistema de archivos
```

#### **⚙️ Configuración por Entorno:**
```javascript
// Development
{
  logLevel: 'debug',
  enableDebug: true,
  authRequired: false,
  rateLimitMultiplier: 10
}

// Production
{
  logLevel: 'info',
  enableDebug: false,
  authRequired: true,
  rateLimitMultiplier: 1
}

// Test
{
  logLevel: 'warn',
  enableDebug: false,
  authRequired: false,
  rateLimitMultiplier: 100
}
```

### **3. Archivo .env Completo (`.env.langwatch.example`)**

#### **🔐 Secciones de Configuración:**
- **Environment & Security**: NODE_ENV, JWT_SECRET, STUDIO_SECRET
- **LLM & AI Services**: LANGWATCH_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY
- **Research Services**: PERPLEXITY_API_KEY, SERPER_API_KEY
- **Database**: SUPABASE_URL, DATABASE_URL, REDIS_URL
- **Integrations**: GITHUB_TOKEN, NOTION_API_KEY, TELEGRAM_BOT_TOKEN
- **Attendee**: ATTENDEE_API_KEY, AUDIO_PROCESSING_ENDPOINT
- **Monitoring**: METRICS_ENDPOINT, PROMETHEUS_PORT
- **Deployment**: CLUSTER_MODE, RATE_LIMIT_MAX_REQUESTS

### **4. Servidor Seguro (`backend/src/server-secure.cjs`)**

#### **🚀 Características del Servidor:**
- **Validación de Entorno**: Verificación automática al inicio
- **Middleware de Seguridad**: Stack completo de protección
- **Rutas Protegidas**: Autenticación específica por endpoint
- **Manejo de Errores**: Error handling seguro sin leak de información
- **Graceful Shutdown**: Cierre limpio del servidor

---

## 🔒 **Configuración de Seguridad por Endpoint**

### **📊 `/health` - Sin Autenticación**
```javascript
// Endpoint público para health checks
GET /health
// Respuesta: status, environment, uptime, memory
```

### **🔧 `/env` - Solo Development**
```javascript
// Información de entorno (solo en desarrollo)
GET /env
// Requiere: NODE_ENV=development
```

### **🎯 `/api/*` - Rate Limiting General**
```javascript
// API pública con rate limiting
app.use('/api', rateLimitMiddleware('general'));
```

### **🤖 `/mcp/*` - Seguridad Máxima**
```javascript
// Endpoints MCP con autenticación completa
app.use('/mcp',
  rateLimitMiddleware('mcp'),        // Rate limiting estricto
  mcpAuthMiddleware(),              // API key requerida
  ipAuthMiddleware()                // IP whitelist
);
```

### **🎬 `/studio/*` - Autenticación Studio**
```javascript
// LangGraph Studio con secret
app.use('/studio',
  rateLimitMiddleware('studio'),
  studioAuthMiddleware()            // STUDIO_SECRET requerido
);
```

### **📈 `/analytics/*` - Token JWT**
```javascript
// Analytics con token JWT
app.use('/analytics',
  rateLimitMiddleware('general'),
  tokenAuthMiddleware()             // JWT token requerido
);
```

### **🔑 `/auth/*` - Rate Limiting Extremo**
```javascript
// Autenticación con límites estrictos
app.use('/auth',
  rateLimitMiddleware('auth')       // 5 req/5min en producción
);
```

---

## 🌍 **Control por Entorno**

### **🔧 Development Mode**
```javascript
Features Enabled:
✅ Console logging
✅ Debug routes (/env)
✅ Hot reload
✅ Source maps
✅ Relaxed rate limits (10x)
❌ IP whitelist
❌ Strict authentication
❌ Security headers
```

### **🧪 Test Mode**
```javascript
Features Enabled:
✅ Mock data
✅ Relaxed rate limits (100x)
✅ Fast timeouts
❌ File logging
❌ Authentication
❌ External services
```

### **🚀 Production Mode**
```javascript
Features Enabled:
✅ Strict authentication
✅ IP whitelist
✅ Security headers (Helmet)
✅ File logging
✅ Compression
✅ Rate limiting
✅ Audit logging
❌ Debug routes
❌ Console logging
❌ Source maps
```

---

## 🔑 **Configuración de Keys y Secrets**

### **Variables Requeridas por Entorno:**

#### **Production (REQUIRED):**
```bash
JWT_SECRET=your-super-secret-jwt-key-here
SESSION_SECRET=your-session-secret-here
STUDIO_SECRET=your-studio-secret-here
DATABASE_URL=postgresql://...
```

#### **Recommended (All Environments):**
```bash
LANGWATCH_API_KEY=your-langwatch-key
PERPLEXITY_API_KEY=your-perplexity-key
MCP_API_KEYS=key1,key2,key3
IP_WHITELIST=127.0.0.1,your-ip
```

#### **Optional (Feature-Specific):**
```bash
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GITHUB_TOKEN=your-github-token
NOTION_API_KEY=your-notion-key
TELEGRAM_BOT_TOKEN=your-telegram-token
```

---

## 🚦 **Uso y Testing**

### **Iniciar con Seguridad:**
```bash
# Development (sin autenticación)
NODE_ENV=development npm start

# Production (con autenticación completa)
NODE_ENV=production npm start

# Con variables específicas
STUDIO_SECRET=my-secret MCP_API_KEYS=key1,key2 npm start
```

### **Testing de Endpoints:**
```bash
# Health check (público)
curl http://localhost:3000/health

# Studio (requiere secret en producción)
curl -H "X-Studio-Secret: my-secret" http://localhost:3000/studio

# MCP (requiere API key en producción)
curl -H "X-MCP-Key: key1" http://localhost:3000/mcp/agents

# Analytics (requiere JWT token)
curl -H "Authorization: Bearer jwt-token" http://localhost:3000/analytics
```

### **Generar Token JWT:**
```bash
# Generar token temporal
curl -X POST http://localhost:3000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"purpose": "testing", "duration": "1h"}'
```

---

## 🎯 **Beneficios del Sistema**

### **🔐 Seguridad Robusta:**
- **Multi-layer authentication**: IP, API keys, JWT tokens
- **Rate limiting inteligente**: Previene ataques DDoS
- **Input sanitization**: Protege contra XSS e injection
- **Security headers**: Protección a nivel de navegador

### **🌍 Environment-Aware:**
- **Detección automática**: No requiere configuración manual
- **Configuración adaptativa**: Optimizada para cada entorno
- **Validación de setup**: Verifica configuración al inicio

### **📊 Observabilidad:**
- **Audit logging**: Rastrea todos los eventos de seguridad
- **Metrics integration**: Métricas de seguridad en tiempo real
- **Error handling**: Manejo seguro sin leak de información

### **🚀 Production-Ready:**
- **Graceful shutdown**: Cierre limpio del servidor
- **Health checks**: Monitoreo de salud del sistema
- **Scalability**: Preparado para clustering y load balancing

**El sistema MCP ahora tiene seguridad de nivel enterprise con control granular por entorno y observabilidad completa.** 🎯

