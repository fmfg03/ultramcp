#!/bin/bash

# 🔍 DIAGNÓSTICO ESPECÍFICO FRONTEND→BACKEND COMMUNICATION
# El endpoint funciona con curl pero el frontend no se conecta

echo "🔍 DIAGNÓSTICO FRONTEND→BACKEND COMMUNICATION"
echo "============================================="

cd /root/supermcp

# 1. Verificar configuración del frontend
echo "📱 1. VERIFICANDO CONFIGURACIÓN DEL FRONTEND"
echo "============================================="

if [ -d "frontend" ]; then
    cd frontend
    
    echo "🔍 Buscando configuración de API en el frontend:"
    
    # Buscar variables de entorno del frontend
    echo "📄 Variables de entorno (.env):"
    if [ -f ".env" ]; then
        cat .env | grep -E "API|BACKEND|URL|PORT" || echo "  No hay variables de API"
    elif [ -f ".env.local" ]; then
        cat .env.local | grep -E "API|BACKEND|URL|PORT" || echo "  No hay variables de API"
    else
        echo "  No existe archivo .env"
    fi
    
    echo ""
    echo "🔍 Buscando URLs hardcodeadas en código JavaScript:"
    # Buscar en archivos JS/TS del frontend
    grep -r -n "localhost:3000\|127.0.0.1:3000\|:3000\|api/tools" src/ . 2>/dev/null | head -10 || echo "  No se encontraron URLs hardcodeadas"
    
    echo ""
    echo "🔍 Verificando configuración de Vite proxy:"
    if [ -f "vite.config.js" ]; then
        echo "📄 vite.config.js:"
        cat vite.config.js
    elif [ -f "vite.config.ts" ]; then
        echo "📄 vite.config.ts:"
        cat vite.config.ts
    else
        echo "  No se encontró configuración Vite"
    fi
    
    cd /root/supermcp
else
    echo "❌ Directorio frontend no encontrado"
fi

# 2. Simular exactamente la petición que hace el frontend
echo ""
echo "🧪 2. SIMULANDO PETICIÓN EXACTA DEL FRONTEND"
echo "==========================================="

# Test con diferentes combinaciones que podría usar el frontend
test_frontend_request() {
    local base_url=$1
    local description=$2
    
    echo "🔍 Testing: $description ($base_url)"
    
    # Test básico
    response=$(curl -s -w "%{http_code}" -o /tmp/test_response --max-time 5 \
        -H "Origin: http://localhost:5173" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json" \
        "$base_url/api/tools")
    
    if [ "$response" = "200" ]; then
        echo "  ✅ HTTP 200 - Success"
        echo "  📄 Response: $(cat /tmp/test_response | head -1)"
    elif [ "$response" = "000" ]; then
        echo "  ❌ No response (connection failed)"
    else
        echo "  ❌ HTTP $response"
        echo "  📄 Error: $(cat /tmp/test_response)"
    fi
    echo ""
}

# Probar diferentes URLs que podría estar usando el frontend
test_frontend_request "http://localhost:3000" "localhost:3000"
test_frontend_request "http://127.0.0.1:3000" "127.0.0.1:3000"
test_frontend_request "http://65.109.54.94:3000" "IP pública:3000"

# 3. Verificar logs del backend en tiempo real
echo "📝 3. VERIFICANDO LOGS BACKEND EN TIEMPO REAL"
echo "=============================================="

echo "🔍 Logs recientes del backend:"
tail -20 mcp_backend_fixed.log 2>/dev/null || tail -20 mcp_backend_new.log 2>/dev/null || echo "No hay logs disponibles"

# 4. Test de CORS específico
echo ""
echo "🛡️ 4. TEST DE CORS ESPECÍFICO"
echo "============================="

echo "🔍 Test OPTIONS preflight request:"
curl -s -X OPTIONS \
    -H "Origin: http://localhost:5173" \
    -H "Access-Control-Request-Method: GET" \
    -H "Access-Control-Request-Headers: content-type" \
    -v "http://localhost:3000/api/tools" 2>&1 | grep -E "(HTTP|Access-Control|Origin)"

# 5. Verificar si el frontend puede conectarse al backend
echo ""
echo "🔗 5. TEST DE CONECTIVIDAD BÁSICA"
echo "================================="

echo "🔍 Test si frontend puede conectarse a backend:"
# Simular desde el mismo contexto que el frontend
curl -s -H "Origin: http://localhost:5173" "http://localhost:3000/health" || echo "❌ No puede conectarse a backend"

# 6. Verificar console del frontend
echo ""
echo "🌐 6. VERIFICAR CONSOLE DEL FRONTEND"
echo "==================================="

echo "💡 Para verificar errores JavaScript:"
echo "  1. Abre http://65.109.54.94:5173 en el navegador"
echo "  2. Presiona F12 para abrir Developer Tools"
echo "  3. Ve a la pestaña 'Console'"
echo "  4. Busca errores en rojo relacionados con:"
echo "     - Failed to fetch"
echo "     - CORS error"
echo "     - Network error"
echo "     - 404 Not Found"
echo "     - Connection refused"

# 7. Test desde el servidor hacia el frontend
echo ""
echo "🔄 7. TEST CONEXIÓN INVERSA"
echo "==========================="

echo "🔍 Test si backend puede 'ver' al frontend:"
curl -s -I "http://localhost:5173" | head -3 || echo "❌ Backend no puede ver frontend"

# 8. Diagnóstico de red
echo ""
echo "🌐 8. DIAGNÓSTICO DE RED"
echo "======================="

echo "🔍 Puertos escuchando en todas las interfaces:"
netstat -tlnp | grep -E ":(3000|5173)" | head -5

echo ""
echo "🔍 Reglas de firewall (si existen):"
iptables -L INPUT | grep -E "(3000|5173|REJECT|DROP)" 2>/dev/null | head -3 || echo "  No hay reglas restrictivas aparentes"

# 9. Generar comando para test manual
echo ""
echo "🧪 9. COMANDO PARA TEST MANUAL"
echo "=============================="

echo "📋 Ejecuta este comando manualmente para simular al frontend:"
echo "curl -v -H 'Origin: http://localhost:5173' 'http://localhost:3000/api/tools'"

echo ""
echo "📋 Ejecuta este comando desde el frontend (en browser console):"
echo "fetch('http://localhost:3000/api/tools')"
echo "  .then(response => response.json())"
echo "  .then(data => console.log(data))"
echo "  .catch(error => console.error('Error:', error));"

# 10. Buscar código específico del error en frontend
echo ""
echo "🔍 10. BUSCAR CÓDIGO DE ERROR EN FRONTEND"
echo "========================================="

if [ -d "frontend" ]; then
    echo "🔍 Buscando texto 'Failed to load tools from backend' en código:"
    find frontend/ -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" | xargs grep -l "Failed to load tools" 2>/dev/null | head -3
    
    echo ""
    echo "🔍 Buscando función que carga herramientas MCP:"
    find frontend/ -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" | xargs grep -l -i "mcp\|tools\|api" 2>/dev/null | head -3
fi

echo ""
echo "🎯 RESUMEN DEL DIAGNÓSTICO"
echo "========================="
echo "📝 Ejecutar y revisar todos los resultados arriba"
echo "🌐 Revisar console del navegador (F12)"
echo "🔍 El problema está en la comunicación específica frontend→backend"

rm -f /tmp/test_response
