#!/bin/bash
# Pre-Deployment Verification Script
# Verifica que todo esté listo para deployment

echo "🔍 MCP ENTERPRISE PRE-DEPLOYMENT CHECK"
echo "======================================"

cd /root/supermcp

# Verificar estructura de archivos críticos
echo "📁 Verificando archivos críticos..."

critical_files=(
    "sam_memory_analyzer.py"
    "mcp_orchestration_server.py" 
    "complete_webhook_agent_end_task_system.py"
    "mcp_payload_schemas.py"
    "sam_manus_notification_protocol.py"
    "manus_webhook_receiver.py"
    "api_validation_middleware.py"
    "mcp_system_testing_suite.py"
    "sam_agent_role_management.py"
    "sam_advanced_error_handling.py"
    "sam_persistent_context_management.py"
    "sam_enterprise_authentication_security.py"
    "mcp_active_webhook_monitoring.py"
    "mcp_logs_dashboard_system.py"
    "mcp_task_validation_offline_system.py"
)

missing_files=0
for file in "${critical_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file - MISSING"
        missing_files=$((missing_files + 1))
    fi
done

if [ $missing_files -eq 0 ]; then
    echo "✅ Todos los archivos críticos presentes"
else
    echo "❌ $missing_files archivos faltantes"
    exit 1
fi

# Verificar variables de entorno
echo ""
echo "🔧 Verificando configuración..."

if [ -f ".env" ]; then
    echo "✅ .env file exists"
    
    # Verificar variables críticas
    source .env
    
    required_vars=(
        "SUPABASE_URL"
        "SUPABASE_SERVICE_ROLE_KEY"
        "NODE_ENV"
        "PORT"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -n "${!var}" ]; then
            echo "✅ $var configured"
        else
            echo "❌ $var missing"
        fi
    done
else
    echo "❌ .env file missing"
fi

# Test de conectividad básica
echo ""
echo "🌐 Testing connectivity..."

if command -v curl &> /dev/null; then
    if curl -s --connect-timeout 5 "$SUPABASE_URL" > /dev/null; then
        echo "✅ Supabase reachable"
    else
        echo "⚠️ Supabase connection issue"
    fi
else
    echo "⚠️ curl not available"
fi

# Verificar puertos disponibles
echo ""
echo "🔌 Checking ports..."

ports=(3000 5174 8125 8126 8127 3003)
for port in "${ports[@]}"; do
    if netstat -tuln 2>/dev/null | grep ":$port " > /dev/null; then
        echo "⚠️ Port $port occupied"
    else
        echo "✅ Port $port available"
    fi
done

# Test de imports Python
echo ""
echo "🐍 Testing Python imports..."

python3 -c "
import sys
import importlib

modules = [
    'asyncio',
    'aiohttp', 
    'flask',
    'requests',
    'supabase',
    'openai',
    'numpy',
    'sqlite3',
    'json',
    'uuid',
    'datetime',
    'logging'
]

failed = 0
for module in modules:
    try:
        importlib.import_module(module)
        print(f'✅ {module}')
    except ImportError as e:
        print(f'❌ {module} - {e}')
        failed += 1

if failed == 0:
    print('✅ All Python dependencies available')
else:
    print(f'❌ {failed} Python dependencies missing')
    sys.exit(1)
"

echo ""
echo "✅ PRE-DEPLOYMENT CHECK COMPLETED"
echo "Ready for deployment!"
