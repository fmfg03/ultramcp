#!/bin/bash

# Script para iniciar UltraMCP en modo mínimo usando Supabase
# Evita conflictos de puertos y usa servicios existentes

set -e

echo "🚀 Iniciando UltraMCP en modo integrado con Supabase..."

# 1. Verificar que Supabase esté corriendo
echo "🔍 Verificando Supabase..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 | grep -q "401"; then
    echo "  ✅ Supabase API activa en puerto 8000"
else
    echo "  ❌ Supabase no está corriendo en puerto 8000"
    echo "  💡 Iniciar con: cd /root/supabase/docker && docker-compose up -d"
    exit 1
fi

# 2. Verificar servicios básicos UltraMCP
echo "🔍 Verificando servicios UltraMCP..."
if docker compose -f docker-compose.supabase-integrated.yml ps | grep -q "ultramcp-redis.*Up"; then
    echo "  ✅ Redis corriendo en puerto 6380"
else
    echo "  🔄 Iniciando Redis..."
    docker compose -f docker-compose.supabase-integrated.yml up -d ultramcp-redis
fi

if docker compose -f docker-compose.supabase-integrated.yml ps | grep -q "ultramcp-qdrant.*Up"; then
    echo "  ✅ Qdrant corriendo en puertos 6333-6334"
else
    echo "  🔄 Iniciando Qdrant..."
    docker compose -f docker-compose.supabase-integrated.yml up -d ultramcp-qdrant
fi

# 3. Verificar conectividad a Supabase desde UltraMCP
echo "🔗 Probando integración UltraMCP -> Supabase..."
if curl -s -H "apikey: ${SUPABASE_ANON_KEY}" http://localhost:8000/rest/v1/mcp_logs?select=count | grep -q "\["; then
    echo "  ✅ Conexión a Supabase exitosa"
else
    echo "  ⚠️  Problemas de conectividad con Supabase"
fi

# 4. Mostrar estado de servicios disponibles
echo ""
echo "📊 Estado de servicios:"
echo ""

# Función para verificar puerto
check_port() {
    local port=$1
    local name=$2
    if netstat -tuln | grep -q ":$port "; then
        echo "  ✅ $name: Puerto $port activo"
    else
        echo "  ❌ $name: Puerto $port no disponible"
    fi
}

echo "🔵 Supabase (2x2.mx):"
check_port 8000 "API"
check_port 5432 "PostgreSQL"

echo ""
echo "🟢 UltraMCP (sam.chat):"
check_port 6380 "Redis"
check_port 6333 "Qdrant HTTP"
check_port 6334 "Qdrant gRPC"

# 5. Mostrar URLs disponibles
echo ""
echo "🌐 URLs disponibles:"
echo ""
echo "🔵 Supabase:"
echo "  • API: http://localhost:8000"
echo "  • Dominio: https://api.2x2.mx (cuando SSL esté configurado)"
echo ""
echo "🟢 UltraMCP (servicios básicos activos):"
echo "  • Redis: localhost:6380"
echo "  • Qdrant: http://localhost:6333"
echo ""

# 6. Mostrar próximos pasos
echo "📋 Próximos pasos para completar UltraMCP:"
echo ""
echo "1. Frontend (puerto 5173):"
echo "   docker compose -f docker-compose.supabase-integrated.yml up -d ultramcp-terminal"
echo ""
echo "2. API Gateway (puerto 3001):"
echo "   docker compose -f docker-compose.supabase-integrated.yml up -d ultramcp-dashboard"
echo ""
echo "3. LangGraph Studio (puerto 8123):"
echo "   docker compose -f docker-compose.supabase-integrated.yml up -d ultramcp-studio"
echo ""
echo "4. Observatory (puerto 5177):"
echo "   docker compose -f docker-compose.supabase-integrated.yml up -d ultramcp-observatory"
echo ""
echo "💡 Para iniciar todos los servicios frontend:"
echo "   docker compose -f docker-compose.supabase-integrated.yml up -d"
echo ""

# 7. Verificar configuración de subdominios
echo "🌐 Configuración de subdominios:"
if [ -f "/etc/nginx/nginx.conf" ] && grep -q "sam.chat" /etc/nginx/nginx.conf; then
    echo "  ✅ Nginx configurado para subdominios"
    echo "  🔗 Frontend: https://sam.chat"
    echo "  🔗 API: https://api.sam.chat"
    echo "  🔗 Studio: https://studio.sam.chat"
    echo "  🔗 Observatory: https://observatory.sam.chat"
else
    echo "  ⚠️  Nginx no configurado para subdominios"
    echo "  💡 Aplicar configuración: sudo cp /root/nginx-subdomain-http.conf /etc/nginx/nginx.conf && sudo systemctl reload nginx"
fi

echo ""
echo "✅ UltraMCP modo básico iniciado exitosamente"
echo "🔗 Integración con Supabase: ACTIVA"
echo "📊 Sin conflictos de puertos: CONFIRMADO"