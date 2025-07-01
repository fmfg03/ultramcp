#!/bin/bash

# 🧹 SCRIPT DE LIMPIEZA DE ARCHIVOS JAVASCRIPT EN ROOT
# Organiza archivos JavaScript del directorio raíz

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
CLEANUP_LOG="$PROJECT_ROOT/migration-tools/javascript-cleanup.log"

log_info "🧹 INICIANDO LIMPIEZA DE ARCHIVOS JAVASCRIPT..."

# Initialize cleanup log
echo "=== JAVASCRIPT FILES CLEANUP - $(date) ===" > "$CLEANUP_LOG"

cd "$PROJECT_ROOT"

# 1. IDENTIFICAR ARCHIVOS POR CATEGORÍA
log_info "🔍 Categorizando archivos JavaScript..."

# Archivos de configuración que DEBEN quedarse en root
CONFIG_FILES=(
    "babel.config.js"
    "eslint.config.js" 
    "jest.config.js"
)

# Archivos de test que van a tests/
TEST_FILES=(
    "test_a2a_integration.js"
)

# Archivos de servidor/rutas que van a apps/backend/src/
BACKEND_FILES=(
    "mcpRoutes.mjs"
    "mcpRoutes_fixed.mjs"
    "mcp_server_fixed.mjs"
    "server.mjs"
)

# 2. VERIFICAR ARCHIVOS DE CONFIGURACIÓN (deben quedarse)
log_info "✅ Verificando archivos de configuración en root..."

for file in "${CONFIG_FILES[@]}"; do
    if [ -f "$file" ]; then
        log_success "✅ Mantenido en root: $file (archivo de configuración)"
        echo "KEPT IN ROOT: $file (config file)" >> "$CLEANUP_LOG"
    fi
done

# 3. MOVER ARCHIVOS DE TEST
log_info "🧪 Moviendo archivos de test..."

for file in "${TEST_FILES[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" "tests/"
        log_success "✅ Movido: $file → tests/"
        echo "MOVED: $file → tests/" >> "$CLEANUP_LOG"
    fi
done

# 4. MOVER ARCHIVOS DE BACKEND
log_info "🔧 Moviendo archivos de backend..."

for file in "${BACKEND_FILES[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" "apps/backend/src/"
        log_success "✅ Movido: $file → apps/backend/src/"
        echo "MOVED: $file → apps/backend/src/" >> "$CLEANUP_LOG"
    fi
done

# 5. VERIFICAR ARCHIVOS RESTANTES
log_info "🔍 Verificando archivos JavaScript restantes en root..."

REMAINING_JS_FILES=$(find . -maxdepth 1 \( -name "*.js" -o -name "*.mjs" -o -name "*.cjs" \) -type f | wc -l)

echo "Archivos JavaScript restantes en root:" >> "$CLEANUP_LOG"
find . -maxdepth 1 \( -name "*.js" -o -name "*.mjs" -o -name "*.cjs" \) -type f >> "$CLEANUP_LOG"

# 6. GENERAR REPORTE FINAL
echo ""
echo "================================================="
echo "       🧹 REPORTE DE LIMPIEZA JAVASCRIPT"
echo "================================================="
echo ""
echo "📊 Archivos procesados:"
echo "   ✅ ${#CONFIG_FILES[@]} archivos de configuración mantenidos en root"
echo "   ✅ ${#TEST_FILES[@]} archivos de test movidos a tests/"
echo "   ✅ ${#BACKEND_FILES[@]} archivos de backend movidos a apps/backend/src/"
echo ""
echo "📂 Organización:"
echo "   🔹 Root - Archivos de configuración del proyecto"
echo "   🔹 tests/ - Archivos de testing"
echo "   🔹 apps/backend/src/ - Archivos de servidor y rutas"
echo ""
echo "📋 Archivos JavaScript restantes en root: $REMAINING_JS_FILES"
echo "📋 Log completo: $CLEANUP_LOG"
echo ""

if [ "$REMAINING_JS_FILES" -le "${#CONFIG_FILES[@]}" ]; then
    log_success "🎉 ¡LIMPIEZA JAVASCRIPT COMPLETADA EXITOSAMENTE!"
    echo "✅ Solo archivos de configuración apropiados permanecen en root"
else
    log_warning "⚠️ VERIFICAR ARCHIVOS RESTANTES"
    echo "❗ Revisar si hay archivos adicionales que necesitan organización"
    echo ""
    echo "Archivos restantes:"
    find . -maxdepth 1 \( -name "*.js" -o -name "*.mjs" -o -name "*.cjs" \) -type f
fi

echo ""
echo "📋 RESUMEN FINAL:"
echo "   📁 Root - $REMAINING_JS_FILES archivos JavaScript (config)"
echo "   📁 tests/ - $(find tests -name "*.js" 2>/dev/null | wc -l) archivos de test"
echo "   📁 apps/backend/src/ - $(find apps/backend/src -name "*.js" -o -name "*.mjs" -o -name "*.cjs" 2>/dev/null | wc -l) archivos de backend"

exit 0