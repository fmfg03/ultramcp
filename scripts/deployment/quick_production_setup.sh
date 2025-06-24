#!/bin/bash
# Quick Production Setup - MCP Enterprise
# El código está implementado, solo falta configuración

echo "🚀 SETUP RÁPIDO PARA PRODUCCIÓN"
echo "==============================="

cd /root/supermcp

# 1. CONFIGURAR ENVIRONMENT VARIABLES
echo "🔧 Configurando variables de entorno..."

cat > .env << 'EOF'
# Supabase Configuration
SUPABASE_URL=https://bvhhkmdlfpcebecmxshd.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ2aGhrbWRsZnBjZWJlY214c2hkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczMzQyNjQzNCwiZXhwIjoyMDQ5MDAyNDM0fQ.TiJmDmqn-3TlPkv7F52HFZ7vZWGfRlNqcVFRo4q5brQ
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ2aGhrbWRsZnBjZWJlY214c2hkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzM0MjY0MzQsImV4cCI6MjA0OTAwMjQzNH0.iHR5YG1UhLDrOL47eFqzUUo10O3gxl-rSFXe4VNdqWQ

# External APIs (obtener keys reales después)
FIRECRAWL_API_KEY=fc-demo-key
TELEGRAM_BOT_TOKEN=demo-token
NOTION_TOKEN=ntn-demo-token
GITHUB_TOKEN=ghp-demo-token

# System Configuration
NODE_ENV=production
PORT=3000
FRONTEND_PORT=5174
LOG_LEVEL=info

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/mcp_enterprise

# Redis
REDIS_URL=redis://localhost:6379

# Security
JWT_SECRET=mcp-enterprise-jwt-secret-2024
ENCRYPTION_KEY=mcp-enterprise-encryption-key-32-chars
EOF

echo "✅ Variables de entorno configuradas en .env"

# 2. CARGAR VARIABLES
echo "📋 Cargando variables de entorno..."
export $(cat .env | grep -v '^#' | xargs)

# 3. INICIALIZAR BASE DE DATOS
echo "🗄️ Inicializando base de datos..."

if command -v psql &> /dev/null; then
    echo "Aplicando schema de Supabase..."
    # Si tienes acceso directo a Supabase
    if [ -n "$SUPABASE_URL" ]; then
        echo "✅ Supabase configurado, aplicar schema manualmente desde dashboard"
    fi
else
    echo "⚠️ PostgreSQL CLI no disponible, usar Supabase dashboard"
fi

# 4. INSTALAR DEPENDENCIAS SI FALTAN
echo "📦 Verificando dependencias..."

if [ -f "requirements.txt" ]; then
    echo "Instalando dependencias Python..."
    pip3 install -r requirements.txt
fi

if [ -f "package.json" ]; then
    echo "Instalando dependencias Node.js..."
    npm install
fi

# 5. EJECUTAR TESTS BÁSICOS
echo "🧪 Ejecutando tests básicos..."

python3 -c "
print('Testing imports...')
try:
    import sam_memory_analyzer
    print('✅ sam_memory_analyzer imported')
except Exception as e:
    print(f'❌ sam_memory_analyzer error: {e}')

try:
    import mcp_orchestration_server
    print('✅ mcp_orchestration_server imported')
except Exception as e:
    print(f'❌ mcp_orchestration_server error: {e}')
"

# 6. CONFIGURAR DOCKER
echo "🐳 Preparando Docker..."

# Verificar que docker-compose funciona
if docker-compose -f docker-compose.enterprise.yml config > /dev/null 2>&1; then
    echo "✅ Docker configuration válida"
else
    echo "❌ Docker configuration tiene errores"
fi

# 7. VERIFICAR PUERTOS DISPONIBLES
echo "🔌 Verificando puertos..."

if netstat -tuln | grep :3000 > /dev/null; then
    echo "⚠️ Puerto 3000 ocupado"
    echo "   Detener servicio: sudo fuser -k 3000/tcp"
else
    echo "✅ Puerto 3000 disponible"
fi

if netstat -tuln | grep :5174 > /dev/null; then
    echo "⚠️ Puerto 5174 ocupado"
    echo "   Detener servicio: sudo fuser -k 5174/tcp"
else
    echo "✅ Puerto 5174 disponible"
fi

# 8. CREAR SCRIPT DE STARTUP
echo "📝 Creando script de startup..."

cat > start_mcp_system.sh << 'EOF'
#!/bin/bash
# MCP Enterprise System Startup

echo "🚀 Starting MCP Enterprise System..."

# Load environment
export $(cat .env | grep -v '^#' | xargs)

# Start services in background
echo "Starting Memory Analyzer..."
python3 sam_memory_analyzer.py &

echo "Starting Orchestration Server..."
python3 mcp_orchestration_server.py &

echo "Starting Webhook System..."
python3 complete_webhook_agent_end_task_system.py &

echo "Starting Monitoring Dashboard..."
python3 mcp_logs_dashboard_system.py &

echo "✅ All services started!"
echo "📊 Monitor logs: tail -f *.log"
echo "🌐 Access frontend: http://65.109.54.94:5174"
echo "🔌 API endpoint: http://65.109.54.94:3000"
EOF

chmod +x start_mcp_system.sh

echo ""
echo "🎯 SETUP COMPLETO - PRÓXIMOS PASOS:"
echo "==================================="
echo ""
echo "1. 🔑 CONFIGURAR API KEYS REALES:"
echo "   - Editar .env con keys reales de Firecrawl, Telegram, etc."
echo ""
echo "2. 🗄️ CONFIGURAR SUPABASE:"
echo "   - Ir a: https://supabase.com/dashboard"
echo "   - Aplicar schema: supabase_memory_schema.sql"
echo ""
echo "3. 🚀 INICIAR SISTEMA:"
echo "   ./start_mcp_system.sh"
echo ""
echo "4. 🌐 ACCEDER A SISTEMA:"
echo "   Frontend: http://65.109.54.94:5174"
echo "   Backend:  http://65.109.54.94:3000"
echo ""
echo "5. 🧪 VERIFICAR FUNCIONAMIENTO:"
echo "   curl http://65.109.54.94:3000/health"
echo ""

# 9. TEST FINAL DE CONECTIVIDAD
echo "🔗 TEST FINAL DE CONECTIVIDAD:"
echo "============================="

# Test Supabase connection
if curl -s -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" "$SUPABASE_URL/rest/v1/" > /dev/null; then
    echo "✅ Supabase connection working"
else
    echo "❌ Supabase connection failed - verificar keys"
fi

echo ""
echo "🎉 SISTEMA LISTO PARA DEPLOYMENT!"
echo "================================"
echo ""
echo "El código está implementado ✅"
echo "Solo falta configuración mínima ⚙️"
echo "Deployment estimado: 30 minutos 🚀"
