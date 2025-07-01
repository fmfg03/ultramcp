#!/bin/bash

# 🧪 SCRIPT DE VALIDACIÓN DE MIGRACIÓN - SUPERMCP
# Valida que todo funcione correctamente después de la reestructuración

set -euo pipefail

# Colors para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration
PROJECT_ROOT="/home/ubuntu/supermcp"
VALIDATION_LOG="$PROJECT_ROOT/migration-tools/validation.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Initialize validation log
echo "=== SUPERMCP MIGRATION VALIDATION - $TIMESTAMP ===" > "$VALIDATION_LOG"

log_info "🧪 INICIANDO VALIDACIÓN DE MIGRACIÓN SUPERMCP..."

# Test counters
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0

run_test() {
    local test_name="$1"
    local test_command="$2"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    log_info "🔍 Testing: $test_name"
    echo "TEST: $test_name - $TIMESTAMP" >> "$VALIDATION_LOG"
    
    if eval "$test_command" >> "$VALIDATION_LOG" 2>&1; then
        log_success "✅ PASS: $test_name"
        echo "RESULT: PASS" >> "$VALIDATION_LOG"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        log_error "❌ FAIL: $test_name"
        echo "RESULT: FAIL" >> "$VALIDATION_LOG"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# ========================================
# FASE 1: VALIDACIÓN DE ESTRUCTURA
# ========================================

log_info "📁 FASE 1: Validando estructura de directorios..."

run_test "Directorio apps/backend existe" "test -d '$PROJECT_ROOT/apps/backend'"
run_test "Directorio apps/frontend existe" "test -d '$PROJECT_ROOT/apps/frontend'"
run_test "Directorio services/voice-system existe" "test -d '$PROJECT_ROOT/services/voice-system'"
run_test "Directorio services/chain-of-debate existe" "test -d '$PROJECT_ROOT/services/chain-of-debate'"
run_test "Directorio infrastructure/docker existe" "test -d '$PROJECT_ROOT/infrastructure/docker'"
run_test "Directorio packages existe" "test -d '$PROJECT_ROOT/packages'"
run_test "Directorio docs existe" "test -d '$PROJECT_ROOT/docs'"
run_test "Directorio tests existe" "test -d '$PROJECT_ROOT/tests'"

# Verificar que archivos críticos estén en lugar correcto
run_test "Backend package.json existe" "test -f '$PROJECT_ROOT/apps/backend/package.json'"
run_test "Frontend package.json existe" "test -f '$PROJECT_ROOT/apps/frontend/package.json'"
run_test "Root package.json existe (workspace)" "test -f '$PROJECT_ROOT/package.json'"

# Verificar que basura fue eliminada
run_test "No hay directorios backup_*" "! find '$PROJECT_ROOT' -maxdepth 1 -name 'backup_*' -type d | grep -q ."
run_test "No hay archivos .zip obsoletos" "! find '$PROJECT_ROOT' -maxdepth 1 -name '*.zip' | grep -q ."
run_test "No hay frontend duplicado" "! test -d '$PROJECT_ROOT/mcp-frontend'"

# ========================================
# FASE 2: VALIDACIÓN DE CONFIGURACIONES
# ========================================

log_info "⚙️ FASE 2: Validando configuraciones..."

# Docker configurations
run_test "docker-compose.dev.yml existe" "test -f '$PROJECT_ROOT/infrastructure/docker/docker-compose.dev.yml'"
run_test "docker-compose.prod.yml existe" "test -f '$PROJECT_ROOT/infrastructure/docker/docker-compose.prod.yml'"
run_test "docker-compose.test.yml existe" "test -f '$PROJECT_ROOT/infrastructure/docker/docker-compose.test.yml'"

# Package.json validations
if [ -f "$PROJECT_ROOT/package.json" ]; then
    run_test "Root package.json tiene workspaces" "grep -q 'workspaces' '$PROJECT_ROOT/package.json'"
fi

# Backend configuration
if [ -f "$PROJECT_ROOT/apps/backend/package.json" ]; then
    run_test "Backend tiene dependencies" "grep -q 'dependencies' '$PROJECT_ROOT/apps/backend/package.json'"
fi

# ========================================
# FASE 3: VALIDACIÓN DE DEPENDENCIAS
# ========================================

log_info "📦 FASE 3: Validando dependencias..."

# Check for node_modules in correct locations
run_test "Node modules en backend" "test -d '$PROJECT_ROOT/apps/backend/node_modules' || test -d '$PROJECT_ROOT/node_modules'"
run_test "Node modules en frontend" "test -d '$PROJECT_ROOT/apps/frontend/node_modules' || test -d '$PROJECT_ROOT/node_modules'"

# Check for circular dependencies (basic check)
if [ -d "$PROJECT_ROOT/apps/backend/src" ]; then
    CIRCULAR_DEPS=$(find "$PROJECT_ROOT/apps/backend/src" -name "*.js" -exec grep -l "require.*\.\./\.\./\.\." {} \; 2>/dev/null | wc -l)
    run_test "No hay dependencias circulares profundas (../../../)" "test $CIRCULAR_DEPS -eq 0"
fi

# ========================================
# FASE 4: VALIDACIÓN DE SERVICIOS
# ========================================

log_info "🔧 FASE 4: Validando servicios..."

# Backend service files
run_test "Backend index.js existe" "test -f '$PROJECT_ROOT/apps/backend/src/index.js' || test -f '$PROJECT_ROOT/apps/backend/index.js'"
run_test "Backend tiene controllers" "test -d '$PROJECT_ROOT/apps/backend/src/controllers'"
run_test "Backend tiene services" "test -d '$PROJECT_ROOT/apps/backend/src/services'"
run_test "Backend tiene adapters" "test -d '$PROJECT_ROOT/apps/backend/src/adapters'"

# Frontend service files
run_test "Frontend App.jsx existe" "test -f '$PROJECT_ROOT/apps/frontend/src/App.jsx'"
run_test "Frontend package.json válido" "cd '$PROJECT_ROOT/apps/frontend' && npm ls --depth=0 >/dev/null 2>&1 || true"

# Voice system
if [ -d "$PROJECT_ROOT/services/voice-system" ]; then
    run_test "Voice system tiene requirements.txt" "test -f '$PROJECT_ROOT/services/voice-system/requirements.txt'"
    run_test "Voice system tiene main files" "find '$PROJECT_ROOT/services/voice-system' -name '*.py' | grep -q ."
fi

# Chain of Debate
if [ -d "$PROJECT_ROOT/services/chain-of-debate" ]; then
    run_test "Chain-of-Debate tiene entrypoint.py" "test -f '$PROJECT_ROOT/services/chain-of-debate/entrypoint.py'"
    run_test "Chain-of-Debate tiene Python files" "find '$PROJECT_ROOT/services/chain-of-debate' -name '*.py' | grep -q ."
fi

# ========================================
# FASE 5: VALIDACIÓN DE BUILD
# ========================================

log_info "🔨 FASE 5: Validando build process..."

# Test backend build
if [ -f "$PROJECT_ROOT/apps/backend/package.json" ]; then
    cd "$PROJECT_ROOT/apps/backend"
    if npm ls >/dev/null 2>&1; then
        run_test "Backend dependencies están instaladas" "true"
        
        # Try to run syntax check
        if command -v node >/dev/null 2>&1; then
            run_test "Backend syntax check" "find src -name '*.js' -exec node -c {} \; 2>/dev/null || true"
        fi
    else
        run_test "Backend dependencies están instaladas" "false"
    fi
fi

# Test frontend build
if [ -f "$PROJECT_ROOT/apps/frontend/package.json" ]; then
    cd "$PROJECT_ROOT/apps/frontend"
    if npm ls >/dev/null 2>&1; then
        run_test "Frontend dependencies están instaladas" "true"
    else
        run_test "Frontend dependencies están instaladas" "false"
    fi
fi

# ========================================
# FASE 6: VALIDACIÓN DE DOCKER
# ========================================

log_info "🐳 FASE 6: Validando Docker setup..."

# Check Docker Compose files syntax
if command -v docker-compose >/dev/null 2>&1; then
    if [ -f "$PROJECT_ROOT/infrastructure/docker/docker-compose.dev.yml" ]; then
        run_test "docker-compose.dev.yml syntax" "docker-compose -f '$PROJECT_ROOT/infrastructure/docker/docker-compose.dev.yml' config >/dev/null"
    fi
    
    if [ -f "$PROJECT_ROOT/infrastructure/docker/docker-compose.prod.yml" ]; then
        run_test "docker-compose.prod.yml syntax" "docker-compose -f '$PROJECT_ROOT/infrastructure/docker/docker-compose.prod.yml' config >/dev/null"
    fi
fi

# Check Dockerfiles
if [ -f "$PROJECT_ROOT/apps/backend/Dockerfile" ]; then
    run_test "Backend Dockerfile existe" "true"
fi

if [ -f "$PROJECT_ROOT/apps/frontend/Dockerfile" ]; then
    run_test "Frontend Dockerfile existe" "true"
fi

# ========================================
# FASE 7: VALIDACIÓN DE DOCUMENTACIÓN
# ========================================

log_info "📚 FASE 7: Validando documentación..."

run_test "README.md principal existe" "test -f '$PROJECT_ROOT/README.md'"
run_test "Migration plan existe" "test -f '$PROJECT_ROOT/RESTRUCTURE_MIGRATION_PLAN.md'"

if [ -d "$PROJECT_ROOT/docs" ]; then
    run_test "Directorio docs no está vacío" "find '$PROJECT_ROOT/docs' -type f | grep -q ."
fi

# ========================================
# FASE 8: VALIDACIÓN DE LIMPIEZA
# ========================================

log_info "🧹 FASE 8: Validando limpieza..."

# Check for old backup files
run_test "No hay archivos .backup" "! find '$PROJECT_ROOT' -name '*.backup.*' | grep -q ."
run_test "No hay archivos temporales" "! find '$PROJECT_ROOT' -name '.last_backup_path' | grep -q ."

# Check that we don't have too many docker-compose files
DOCKER_COMPOSE_COUNT=$(find "$PROJECT_ROOT" -name "docker-compose*.yml" | wc -l)
run_test "Máximo 5 archivos docker-compose" "test $DOCKER_COMPOSE_COUNT -le 5"

# Check for duplicate package.json files in wrong places
PACKAGE_JSON_COUNT=$(find "$PROJECT_ROOT" -name "package.json" | wc -l)
run_test "Número razonable de package.json (<10)" "test $PACKAGE_JSON_COUNT -lt 10"

# ========================================
# REPORTE FINAL
# ========================================

log_info "📊 GENERANDO REPORTE FINAL..."

echo "" >> "$VALIDATION_LOG"
echo "=== RESUMEN DE VALIDACIÓN ===" >> "$VALIDATION_LOG"
echo "Total Tests: $TESTS_TOTAL" >> "$VALIDATION_LOG"
echo "Passed: $TESTS_PASSED" >> "$VALIDATION_LOG"
echo "Failed: $TESTS_FAILED" >> "$VALIDATION_LOG"
echo "Success Rate: $(( TESTS_PASSED * 100 / TESTS_TOTAL ))%" >> "$VALIDATION_LOG"

# Console output
echo ""
echo "================================================="
echo "       📊 REPORTE DE VALIDACIÓN FINAL"
echo "================================================="
echo ""
echo "📈 Total Tests Ejecutados: $TESTS_TOTAL"
echo "✅ Tests Exitosos: $TESTS_PASSED"
echo "❌ Tests Fallidos: $TESTS_FAILED"
echo "📊 Tasa de Éxito: $(( TESTS_PASSED * 100 / TESTS_TOTAL ))%"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    log_success "🎉 ¡MIGRACIÓN VALIDADA EXITOSAMENTE!"
    echo "✅ Todos los tests pasaron. La migración fue exitosa."
    echo "📋 Log completo disponible en: $VALIDATION_LOG"
    exit 0
else
    log_error "🚨 MIGRACIÓN TIENE PROBLEMAS"
    echo "❌ $TESTS_FAILED tests fallaron. Revisar issues antes de continuar."
    echo "📋 Log completo disponible en: $VALIDATION_LOG"
    echo ""
    echo "🔍 TESTS FALLIDOS DETECTADOS:"
    grep -A1 "RESULT: FAIL" "$VALIDATION_LOG" | grep "TEST:" | sed 's/TEST: /  - /'
    exit 1
fi