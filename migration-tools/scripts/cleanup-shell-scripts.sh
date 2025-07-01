#!/bin/bash

# 🧹 SCRIPT DE LIMPIEZA DE SCRIPTS SHELL EN ROOT
# Elimina duplicados y reorganiza scripts shell del directorio raíz

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
CLEANUP_LOG="$PROJECT_ROOT/migration-tools/shell-cleanup.log"

log_info "🧹 INICIANDO LIMPIEZA DE SCRIPTS SHELL..."

# Initialize cleanup log
echo "=== SHELL SCRIPTS CLEANUP - $(date) ===" > "$CLEANUP_LOG"

cd "$PROJECT_ROOT"

# 1. IDENTIFICAR SCRIPTS POR CATEGORÍA Y DESTINO
log_info "🔍 Categorizando scripts shell..."

# Scripts de deployment que van a infrastructure/scripts/
DEPLOYMENT_SCRIPTS=(
    "deploy_mcp_observatory_production.sh"
    "deploy_a2a_agents.sh"
    "setup_ssl_tls.sh"
)

# Scripts de setup/environment que van a tools/scripts/
SETUP_SCRIPTS=(
    "setup_env.sh"
    "sync-from-github.sh"
)

# Scripts de fix/debug que van a tools/scripts/ (históricos)
FIX_SCRIPTS=(
    "add_execute_endpoint.sh"
    "diagnose_frontend_backend.sh"
    "diagnose_mcp_tools.sh"
    "fix_frontend_urls.sh"
    "fix_mcp_tools_endpoints.sh"
    "fix_orchestration_endpoints.sh"
    "fix_ui_and_telegram.sh"
    "fix_vite_proxy.sh"
    "master_fix.sh"
)

# Scripts de start/run que van a scripts/ (directorio existente)
RUN_SCRIPTS=(
    "start_observatory.sh"
)

# 2. CREAR DIRECTORIOS SI NO EXISTEN
mkdir -p infrastructure/scripts
mkdir -p tools/scripts

# 3. MOVER SCRIPTS DE DEPLOYMENT
log_info "📦 Moviendo scripts de deployment..."

for script in "${DEPLOYMENT_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        mv "$script" "infrastructure/scripts/"
        log_success "✅ Movido: $script → infrastructure/scripts/"
        echo "MOVED: $script → infrastructure/scripts/" >> "$CLEANUP_LOG"
    fi
done

# 4. MOVER SCRIPTS DE SETUP
log_info "🔧 Moviendo scripts de setup..."

for script in "${SETUP_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        mv "$script" "tools/scripts/"
        log_success "✅ Movido: $script → tools/scripts/"
        echo "MOVED: $script → tools/scripts/" >> "$CLEANUP_LOG"
    fi
done

# 5. MOVER SCRIPTS DE FIX/DEBUG
log_info "🔧 Moviendo scripts de fix/debug..."

for script in "${FIX_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        mv "$script" "tools/scripts/"
        log_success "✅ Movido: $script → tools/scripts/"
        echo "MOVED: $script → tools/scripts/" >> "$CLEANUP_LOG"
    fi
done

# 6. MOVER SCRIPTS DE RUN
log_info "🚀 Moviendo scripts de ejecución..."

for script in "${RUN_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        mv "$script" "scripts/"
        log_success "✅ Movido: $script → scripts/"
        echo "MOVED: $script → scripts/" >> "$CLEANUP_LOG"
    fi
done

# 7. VERIFICAR DUPLICADOS Y CONFLICTOS
log_info "🔍 Verificando posibles duplicados..."

# Check for similar scripts in scripts/deployment/
if [ -f "infrastructure/scripts/deploy_mcp_observatory_production.sh" ] && [ -f "scripts/deployment/deploy_mcp_enterprise.sh" ]; then
    log_warning "⚠️ Posible conflicto: scripts de deployment similar existen"
    echo "WARNING: Similar deployment scripts exist" >> "$CLEANUP_LOG"
fi

# 8. CREAR README EN CADA DIRECTORIO PARA DOCUMENTAR ORGANIZACIÓN
cat > infrastructure/scripts/README.md << 'EOF'
# Infrastructure Scripts

This directory contains scripts for infrastructure deployment and management:

- `deploy_*.sh` - Deployment scripts for production environments
- `setup_ssl_tls.sh` - SSL/TLS certificate setup

## Usage

These scripts are typically run during deployment or infrastructure setup phases.
EOF

cat > tools/scripts/README.md << 'EOF'
# Development Tools Scripts

This directory contains development and debugging scripts:

## Setup Scripts
- `setup_env.sh` - Environment setup for developers
- `sync-from-github.sh` - Repository synchronization

## Debug/Fix Scripts (Historical)
- `diagnose_*.sh` - Diagnostic scripts
- `fix_*.sh` - Historical fix scripts
- `master_fix.sh` - Master fix script

## Usage

These scripts are for development, debugging, and historical reference.
Most fix scripts are historical and may not be needed in the new architecture.
EOF

# 9. VERIFICAR ARCHIVOS RESTANTES
log_info "🔍 Verificando scripts shell restantes en root..."

REMAINING_SH_FILES=$(find . -maxdepth 1 -name "*.sh" -type f | wc -l)

if [ "$REMAINING_SH_FILES" -gt 0 ]; then
    log_warning "⚠️ Scripts shell restantes en root:"
    find . -maxdepth 1 -name "*.sh" -type f
    echo "REMAINING FILES IN ROOT:" >> "$CLEANUP_LOG"
    find . -maxdepth 1 -name "*.sh" -type f >> "$CLEANUP_LOG"
else
    log_success "✅ No hay scripts shell restantes en root"
    echo "NO REMAINING SHELL SCRIPTS IN ROOT" >> "$CLEANUP_LOG"
fi

# 10. GENERAR REPORTE FINAL
echo ""
echo "================================================="
echo "       🧹 REPORTE DE LIMPIEZA SCRIPTS SHELL"
echo "================================================="
echo ""
echo "📊 Scripts procesados:"
echo "   ✅ ${#DEPLOYMENT_SCRIPTS[@]} scripts movidos a infrastructure/scripts/"
echo "   ✅ ${#SETUP_SCRIPTS[@]} scripts movidos a tools/scripts/"
echo "   ✅ ${#FIX_SCRIPTS[@]} scripts de fix/debug movidos a tools/scripts/"
echo "   ✅ ${#RUN_SCRIPTS[@]} scripts movidos a scripts/"
echo ""
echo "📂 Nueva estructura:"
echo "   🔹 infrastructure/scripts/ - Scripts de deployment e infraestructura"
echo "   🔹 tools/scripts/ - Scripts de desarrollo y debug"
echo "   🔹 scripts/ - Scripts de ejecución del sistema"
echo ""
echo "📋 Scripts shell restantes en root: $REMAINING_SH_FILES"
echo "📋 Log completo: $CLEANUP_LOG"
echo ""

# 11. VERIFICAR PERMISOS DE EJECUCIÓN
log_info "🔐 Verificando permisos de ejecución..."

SCRIPTS_DIRS=("infrastructure/scripts" "tools/scripts" "scripts")
for dir in "${SCRIPTS_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        find "$dir" -name "*.sh" -type f ! -executable -exec chmod +x {} \;
        FIXED_PERMS=$(find "$dir" -name "*.sh" -type f -executable | wc -l)
        log_info "📁 $dir: $FIXED_PERMS scripts con permisos de ejecución"
    fi
done

if [ "$REMAINING_SH_FILES" -eq 0 ]; then
    log_success "🎉 ¡LIMPIEZA SCRIPTS SHELL COMPLETADA EXITOSAMENTE!"
    echo "✅ Todos los scripts shell han sido organizados apropiadamente"
else
    log_warning "⚠️ LIMPIEZA PARCIALMENTE COMPLETADA"
    echo "❗ Revisar scripts restantes en root para determinar ubicación apropiada"
fi

echo ""
echo "📋 RESUMEN FINAL:"
echo "   📁 infrastructure/scripts/ - $(find infrastructure/scripts -name "*.sh" 2>/dev/null | wc -l) scripts"
echo "   📁 tools/scripts/ - $(find tools/scripts -name "*.sh" 2>/dev/null | wc -l) scripts"
echo "   📁 scripts/ - $(find scripts -name "*.sh" 2>/dev/null | wc -l) scripts"
echo "   📁 Root - $REMAINING_SH_FILES scripts"

exit 0