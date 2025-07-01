#!/bin/bash

# 🧹 SCRIPT DE LIMPIEZA DE ARCHIVOS PYTHON EN ROOT
# Elimina duplicados y reorganiza archivos Python del directorio raíz

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

PROJECT_ROOT="/home/ubuntu/supermcp"
CLEANUP_LOG="$PROJECT_ROOT/migration-tools/python-cleanup.log"

log_info "🧹 INICIANDO LIMPIEZA DE ARCHIVOS PYTHON..."

# Initialize cleanup log
echo "=== PYTHON FILES CLEANUP - $(date) ===" > "$CLEANUP_LOG"

cd "$PROJECT_ROOT"

# 1. ELIMINAR DUPLICADOS EXACTOS
log_info "🔍 Eliminando duplicados exactos..."

# Files that exist in both root and orchestrator_executor_system (keep in orchestrator_executor_system)
DUPLICATES_IN_ORCHESTRATOR=(
    "api_validation_middleware.py"
    "manus_webhook_receiver.py" 
    "mcp_payload_schemas.py"
    "mcp_system_testing_suite.py"
    "sam_manus_notification_protocol.py"
)

for file in "${DUPLICATES_IN_ORCHESTRATOR[@]}"; do
    if [ -f "$file" ] && [ -f "orchestrator_executor_system/$file" ]; then
        rm "$file"
        log_success "✅ Eliminado duplicado: $file (conservado en orchestrator_executor_system/)"
        echo "DELETED: $file (duplicate in orchestrator_executor_system/)" >> "$CLEANUP_LOG"
    fi
done

# Files that exist in both root and backend (keep in backend)
DUPLICATES_IN_BACKEND=(
    "sam_memory_analyzer.py"
    "mcp_orchestration_server.py"
)

for file in "${DUPLICATES_IN_BACKEND[@]}"; do
    if [ -f "$file" ] && [ -f "apps/backend/$file" ]; then
        rm "$file"
        log_success "✅ Eliminado duplicado: $file (conservado en apps/backend/)"
        echo "DELETED: $file (duplicate in apps/backend/)" >> "$CLEANUP_LOG"
    fi
done

# 2. MOVER ARCHIVOS A UBICACIONES APROPIADAS
log_info "📦 Moviendo archivos a ubicaciones apropiadas..."

# Files that should go to services/mcp-devtools/
DEVTOOLS_FILES=(
    "supermcp_a2a_adapters.py"
    "mcp_active_webhook_monitoring.py"
    "mcp_enterprise_testing_suite.py"
    "mcp_task_validation_offline_system.py"
)

for file in "${DEVTOOLS_FILES[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" "services/mcp-devtools/"
        log_success "✅ Movido: $file → services/mcp-devtools/"
        echo "MOVED: $file → services/mcp-devtools/" >> "$CLEANUP_LOG"
    fi
done

# Files that should go to apps/backend/
BACKEND_FILES=(
    "sam_advanced_error_handling.py"
    "sam_agent_role_management.py"
    "sam_enterprise_authentication_security.py"
    "sam_persistent_context_management.py"
)

for file in "${BACKEND_FILES[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" "apps/backend/"
        log_success "✅ Movido: $file → apps/backend/"
        echo "MOVED: $file → apps/backend/" >> "$CLEANUP_LOG"
    fi
done

# Files that should go to infrastructure/scripts/
INFRASTRUCTURE_FILES=(
    "mcp_secrets_management.py"
    "mcp_logs_dashboard_system.py"
)

for file in "${INFRASTRUCTURE_FILES[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" "infrastructure/scripts/"
        log_success "✅ Movido: $file → infrastructure/scripts/"
        echo "MOVED: $file → infrastructure/scripts/" >> "$CLEANUP_LOG"
    fi
done

# 3. VERIFICAR ARCHIVOS RESTANTES
log_info "🔍 Verificando archivos Python restantes en root..."

REMAINING_PY_FILES=$(find . -maxdepth 1 -name "*.py" -type f | wc -l)

if [ "$REMAINING_PY_FILES" -gt 0 ]; then
    log_warning "⚠️ Archivos Python restantes en root:"
    find . -maxdepth 1 -name "*.py" -type f
    echo "REMAINING FILES IN ROOT:" >> "$CLEANUP_LOG"
    find . -maxdepth 1 -name "*.py" -type f >> "$CLEANUP_LOG"
else
    log_success "✅ No hay archivos Python restantes en root"
    echo "NO REMAINING PYTHON FILES IN ROOT" >> "$CLEANUP_LOG"
fi

# 4. GENERAR REPORTE FINAL
echo ""
echo "================================================="
echo "       🧹 REPORTE DE LIMPIEZA PYTHON"
echo "================================================="
echo ""
echo "📊 Archivos procesados:"
echo "   ✅ ${#DUPLICATES_IN_ORCHESTRATOR[@]} duplicados eliminados (orchestrator_executor_system)"
echo "   ✅ ${#DUPLICATES_IN_BACKEND[@]} duplicados eliminados (backend)"
echo "   ✅ ${#DEVTOOLS_FILES[@]} archivos movidos a services/mcp-devtools/"
echo "   ✅ ${#BACKEND_FILES[@]} archivos movidos a apps/backend/"
echo "   ✅ ${#INFRASTRUCTURE_FILES[@]} archivos movidos a infrastructure/scripts/"
echo ""
echo "📂 Nueva estructura:"
echo "   🔹 orchestrator_executor_system/ - Sistema orchestrator-executor"
echo "   🔹 apps/backend/ - Componentes del backend"
echo "   🔹 services/mcp-devtools/ - Herramientas de desarrollo MCP"
echo "   🔹 infrastructure/scripts/ - Scripts de infraestructura"
echo ""
echo "📋 Archivos Python restantes en root: $REMAINING_PY_FILES"
echo "📋 Log completo: $CLEANUP_LOG"
echo ""

if [ "$REMAINING_PY_FILES" -eq 0 ]; then
    log_success "🎉 ¡LIMPIEZA PYTHON COMPLETADA EXITOSAMENTE!"
    echo "✅ Todos los archivos Python han sido organizados apropiadamente"
else
    log_warning "⚠️ LIMPIEZA PARCIALMENTE COMPLETADA"
    echo "❗ Revisar archivos restantes en root para determinar ubicación apropiada"
fi

exit 0