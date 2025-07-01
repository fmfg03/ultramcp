#!/bin/bash

# 🔍 DIAGNÓSTICO HERRAMIENTAS MCP - FRONTEND TO BACKEND
# Script para diagnosticar el problema "Failed to load tools from backend"

echo "🔍 DIAGNÓSTICO: Failed to load tools from backend"
echo "================================================"

cd /root/supermcp

# 1. Verificar endpoints del backend que el frontend puede estar intentando usar
echo "🔍 1. VERIFICANDO ENDPOINTS DEL BACKEND..."
echo ""

endpoints=(
    "/api/tools"
    "/tools" 
    "/api/adapters"
    "/adapters"
    "/api/mcp/tools"
    "/mcp/tools"
    "/api/broker/tools"
    "/health"
    "/status"
    "/api/status"
)

for endpoint in "${endpoints[@]}"; do
    echo "Testing $endpoint:"
    response=$(curl -s -w "%{http_code}" -o /tmp/response --max-time 3 "http://localhost:3000$endpoint")
    
    if [ "$response" = "200" ]; then
        echo "  ✅ $endpoint: HTTP 200"
        echo "  📄 Response: $(cat /tmp/response | head -1)"
    elif [ "$response" = "404" ]; then
        echo "  ❌ $endpoint: HTTP 404 (Not Found)"
    elif [ "$response" = "000" ]; then
        echo "  ❌ $endpoint: No response (timeout/error)"
    else
        echo "  ⚠️  $endpoint: HTTP $response"
        echo "  📄 Response: $(cat /tmp/response | head -1)"
    fi
    echo ""
done

rm -f /tmp/response

# 2. Verificar configuración CORS del backend
echo "🔍 2. VERIFICANDO CONFIGURACIÓN CORS..."
echo ""

# Test CORS desde frontend hacia backend
echo "Testing CORS desde frontend (5173) hacia backend (3000):"
response=$(curl -s -H "Origin: http://localhost:5173" -H "Access-Control-Request-Method: GET" -H "Access-Control-Request-Headers: content-type" -X OPTIONS "http://localhost:3000/api/tools")

if [ -n "$response" ]; then
    echo "  📄 CORS Response: $response"
else
    echo "  ⚠️  No CORS response"
fi

# 3. Verificar logs del backend para errores específicos
echo ""
echo "🔍 3. VERIFICANDO LOGS BACKEND RECIENTES..."
echo ""

if [ -f "mcp_backend.log" ]; then
    echo "📄 Últimas líneas del log backend:"
    tail -20 mcp_backend.log
else
    echo "⚠️  No se encontró mcp_backend.log"
fi

# 4. Buscar configuración del frontend que especifica la URL del backend
echo ""
echo "🔍 4. VERIFICANDO CONFIGURACIÓN FRONTEND..."
echo ""

# Buscar archivos de configuración del frontend
if [ -d "frontend" ]; then
    cd frontend
    
    echo "📂 Buscando configuración de API en frontend..."
    
    # Buscar URLs de API en archivos JS/TS
    echo "🔍 URLs de API encontradas:"
    grep -r -n "localhost:3000\|127.0.0.1:3000\|api/tools\|/tools" src/ . 2>/dev/null | head -10 || echo "  No se encontraron URLs de API explícitas"
    
    echo ""
    echo "🔍 Variables de entorno frontend:"
    if [ -f ".env" ]; then
        grep -E "API|BACKEND|URL" .env 2>/dev/null || echo "  No hay variables de API en .env"
    else
        echo "  No existe archivo .env en frontend"
    fi
    
    echo ""
    echo "🔍 Configuración Vite:"
    if [ -f "vite.config.js" ]; then
        grep -A 10 -B 2 "proxy\|server" vite.config.js 2>/dev/null || echo "  No hay configuración de proxy en vite.config.js"
    elif [ -f "vite.config.ts" ]; then
        grep -A 10 -B 2 "proxy\|server" vite.config.ts 2>/dev/null || echo "  No hay configuración de proxy en vite.config.ts"
    else
        echo "  No se encontró vite.config"
    fi
    
    cd /root/supermcp
fi

# 5. Verificar archivo específico del backend que maneja las rutas
echo ""
echo "🔍 5. VERIFICANDO RUTAS DEL BACKEND..."
echo ""

# Buscar archivos de rutas en el backend
echo "📂 Archivos de rutas encontrados:"
find backend/ -name "*route*" -o -name "*controller*" -o -name "*endpoint*" 2>/dev/null | head -10

echo ""
echo "🔍 Rutas registradas en backend:"

# Buscar definiciones de rutas en archivos del backend
if [ -f "backend/mcp-secure-server.cjs" ]; then
    echo "📄 Rutas en mcp-secure-server.cjs:"
    grep -n "app\.\|router\.\|\.get\|\.post" backend/mcp-secure-server.cjs | head -10
fi

# Buscar en otros archivos de servidor
for file in backend/src/server.cjs backend/server.cjs; do
    if [ -f "$file" ]; then
        echo "📄 Rutas en $file:"
        grep -n "app\.\|router\.\|\.get\|\.post" "$file" | head -5
    fi
done

# 6. Test específico de comunicación frontend -> backend
echo ""
echo "🔍 6. TEST ESPECÍFICO DE COMUNICACIÓN..."
echo ""

# Simular la llamada que hace el frontend
echo "🧪 Simulando llamada del frontend al backend:"

# Test con diferentes métodos y headers que podría usar el frontend
for method in "GET" "POST"; do
    echo "  Testing $method /api/tools:"
    response=$(curl -s -w "%{http_code}" -o /tmp/test_response -X $method \
        -H "Content-Type: application/json" \
        -H "Origin: http://localhost:5173" \
        --max-time 3 "http://localhost:3000/api/tools")
    
    echo "    Status: $response"
    if [ -f "/tmp/test_response" ]; then
        echo "    Response: $(cat /tmp/test_response | head -1)"
    fi
    echo ""
done

# 7. Verificar si hay adaptadores MCP registrados
echo "🔍 7. VERIFICANDO ADAPTADORES MCP..."
echo ""

# Buscar archivos de configuración de adaptadores
echo "📂 Configuración de adaptadores:"
for config_file in "config/adapter_config.json" "backend/config/adapter_config.json" "adapters.json" "backend/adapters.json"; do
    if [ -f "$config_file" ]; then
        echo "✅ Encontrado: $config_file"
        echo "📄 Contenido (primeras líneas):"
        head -10 "$config_file" | grep -E "name|type|url" || echo "    (Estructura no reconocida)"
        echo ""
    fi
done

if ! ls config/adapter_config.json backend/config/adapter_config.json adapters.json backend/adapters.json 2>/dev/null; then
    echo "⚠️  No se encontraron archivos de configuración de adaptadores"
fi

# 8. Resumen del diagnóstico
echo ""
echo "🎯 RESUMEN DEL DIAGNÓSTICO"
echo "=========================="

echo "📊 Problemas identificados:"

# Verificar si encontramos el endpoint correcto
if grep -q "HTTP 200" /tmp/diagnostic_log 2>/dev/null; then
    echo "  ✅ Backend responde en algunos endpoints"
else
    echo "  ❌ Backend no responde en endpoints esperados"
fi

# Verificar si hay configuración de adaptadores
if ls config/adapter_config.json backend/config/adapter_config.json 2>/dev/null >/dev/null; then
    echo "  ✅ Configuración de adaptadores encontrada"
else
    echo "  ⚠️  Configuración de adaptadores no encontrada"
fi

echo ""
echo "💡 PRÓXIMOS PASOS SUGERIDOS:"
echo "  1. Verificar si el endpoint /api/tools existe y está configurado"
echo "  2. Revisar logs del backend para errores específicos"
echo "  3. Verificar que los adaptadores MCP estén registrados"
echo "  4. Confirmar configuración CORS del backend"
echo "  5. Verificar URL del backend en configuración del frontend"

echo ""
echo "📝 Para resolver, ejecutar el script de fix correspondiente"

# Cleanup
rm -f /tmp/test_response /tmp/response
