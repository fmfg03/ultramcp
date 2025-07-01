#!/bin/bash

# 💾 SCRIPT DE BACKUP PRE-MIGRACIÓN - SUPERMCP
# Crea backup completo antes de la reestructuración arquitectural

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

# Configuration
PROJECT_ROOT="/home/ubuntu/supermcp"
BACKUP_DIR="/home/ubuntu/supermcp-backups"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
BACKUP_NAME="supermcp-pre-migration-$TIMESTAMP"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

log_info "💾 INICIANDO BACKUP PRE-MIGRACIÓN SUPERMCP..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Check available space
AVAILABLE_SPACE=$(df "$BACKUP_DIR" | awk 'NR==2{printf "%.1f", $4/1024/1024}')
PROJECT_SIZE=$(du -sm "$PROJECT_ROOT" | cut -f1)

log_info "📊 Espacio disponible: ${AVAILABLE_SPACE}GB"
log_info "📊 Tamaño del proyecto: ${PROJECT_SIZE}MB"

if (( $(echo "$AVAILABLE_SPACE < 1.0" | bc -l) )); then
    log_error "❌ Espacio insuficiente para backup. Se requiere al menos 1GB libre."
    exit 1
fi

# Create backup with progress
log_info "📦 Creando backup completo en: $BACKUP_PATH"

# Copy with progress and excluding unnecessary files
rsync -av \
    --progress \
    --exclude='node_modules' \
    --exclude='.git' \
    --exclude='*.log' \
    --exclude='*.tmp' \
    --exclude='.DS_Store' \
    --exclude='coverage' \
    --exclude='dist' \
    --exclude='build' \
    "$PROJECT_ROOT/" "$BACKUP_PATH/"

if [ $? -eq 0 ]; then
    log_success "✅ Backup completado exitosamente"
else
    log_error "❌ Error durante el backup"
    exit 1
fi

# Create backup manifest
MANIFEST_FILE="$BACKUP_PATH/BACKUP_MANIFEST.md"
cat > "$MANIFEST_FILE" << EOF
# 💾 BACKUP MANIFEST - SUPERMCP PRE-MIGRATION

## Información del Backup
- **Timestamp:** $TIMESTAMP
- **Backup Name:** $BACKUP_NAME
- **Source:** $PROJECT_ROOT
- **Destination:** $BACKUP_PATH
- **Purpose:** Pre-migration backup before architectural restructure

## Contenido del Backup
$(find "$BACKUP_PATH" -type f | wc -l) archivos totales
$(du -sh "$BACKUP_PATH" | cut -f1) tamaño total

## Estructura Principal
\`\`\`
$(tree -L 2 "$BACKUP_PATH" 2>/dev/null || find "$BACKUP_PATH" -maxdepth 2 -type d | head -20)
\`\`\`

## Archivos Críticos Incluidos
- ✅ Backend completo (/backend/)
- ✅ Frontend(s) (/frontend/, /mcp-*)
- ✅ Servicios (/services/, /voice_system/, /langgraph_system/)
- ✅ Configuraciones (docker-compose*, package.json, etc.)
- ✅ Documentación (*.md)
- ✅ Scripts (/scripts/)

## Archivos Excluidos
- ❌ node_modules (se pueden regenerar con npm install)
- ❌ .git (demasiado grande, usar Git para historial)
- ❌ Logs y archivos temporales
- ❌ Coverage reports
- ❌ Build artifacts

## Instrucciones de Restore
Para restaurar este backup:
\`\`\`bash
# Backup current state (opcional)
mv $PROJECT_ROOT ${PROJECT_ROOT}-broken-$(date +%Y%m%d)

# Restore from backup
cp -r $BACKUP_PATH $PROJECT_ROOT

# Reinstall dependencies
cd $PROJECT_ROOT
npm install
cd backend && npm install
cd ../frontend && npm install
\`\`\`

## Validación del Backup
- Backup Size: $(du -sh "$BACKUP_PATH" | cut -f1)
- File Count: $(find "$BACKUP_PATH" -type f | wc -l)
- Creation Time: $(date)

**⚠️ IMPORTANTE:** Este backup NO incluye node_modules. Después del restore, ejecutar npm install en todos los directorios.
EOF

# Verify backup integrity
log_info "🔍 Verificando integridad del backup..."

# Check critical files exist
CRITICAL_FILES=(
    "package.json"
    "backend/package.json"
    "backend/src/index.js"
    "frontend/package.json"
    "docker-compose.yml"
)

MISSING_FILES=0
for file in "${CRITICAL_FILES[@]}"; do
    if [ ! -f "$BACKUP_PATH/$file" ]; then
        log_warning "⚠️ Archivo crítico faltante en backup: $file"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done

# Create restore script
RESTORE_SCRIPT="$BACKUP_PATH/restore-backup.sh"
cat > "$RESTORE_SCRIPT" << 'EOF'
#!/bin/bash
# 🔄 SCRIPT DE RESTORE AUTOMÁTICO

set -euo pipefail

BACKUP_DIR="$(dirname "$0")"
TARGET_DIR="/home/ubuntu/supermcp"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

echo "🔄 INICIANDO RESTORE DEL BACKUP..."
echo "📁 Backup Source: $BACKUP_DIR"
echo "📁 Target: $TARGET_DIR"

# Backup current state if exists
if [ -d "$TARGET_DIR" ]; then
    echo "💾 Backing up current state..."
    mv "$TARGET_DIR" "${TARGET_DIR}-backup-before-restore-$TIMESTAMP"
fi

# Restore from backup
echo "📦 Restoring files..."
cp -r "$BACKUP_DIR" "$TARGET_DIR"

# Remove backup manifest and restore script from restored directory
rm -f "$TARGET_DIR/BACKUP_MANIFEST.md"
rm -f "$TARGET_DIR/restore-backup.sh"

echo "📦 Installing dependencies..."
cd "$TARGET_DIR"

# Install root dependencies if package.json exists
if [ -f "package.json" ]; then
    npm install
fi

# Install backend dependencies
if [ -f "backend/package.json" ]; then
    cd backend && npm install && cd ..
fi

# Install frontend dependencies
if [ -f "frontend/package.json" ]; then
    cd frontend && npm install && cd ..
fi

echo "✅ RESTORE COMPLETADO EXITOSAMENTE"
echo "📋 El proyecto ha sido restaurado a: $TARGET_DIR"
EOF

chmod +x "$RESTORE_SCRIPT"

# Create backup summary
BACKUP_SIZE=$(du -sh "$BACKUP_PATH" | cut -f1)
FILE_COUNT=$(find "$BACKUP_PATH" -type f | wc -l)

# Generate final report
echo ""
echo "================================================="
echo "       💾 REPORTE DE BACKUP COMPLETADO"
echo "================================================="
echo ""
echo "📦 Backup Name: $BACKUP_NAME"
echo "📁 Backup Path: $BACKUP_PATH"
echo "📊 Backup Size: $BACKUP_SIZE"
echo "📄 File Count: $FILE_COUNT"
echo "⚠️ Missing Critical Files: $MISSING_FILES"
echo ""

if [ $MISSING_FILES -eq 0 ]; then
    log_success "✅ BACKUP COMPLETO Y VERIFICADO"
    echo "📋 Manifest: $MANIFEST_FILE"
    echo "🔄 Restore Script: $RESTORE_SCRIPT"
    echo ""
    echo "🎯 LISTO PARA MIGRACIÓN"
    echo "   Para continuar con la migración ejecuta:"
    echo "   ./migration-tools/scripts/execute-migration.sh"
else
    log_warning "⚠️ BACKUP COMPLETADO CON ADVERTENCIAS"
    echo "❌ $MISSING_FILES archivos críticos faltantes"
    echo "📋 Revisar manifest para detalles: $MANIFEST_FILE"
fi

# Save backup info to migration tools
echo "$BACKUP_PATH" > "$PROJECT_ROOT/migration-tools/.last_backup_path"
echo "BACKUP_PATH=\"$BACKUP_PATH\"" > "$PROJECT_ROOT/migration-tools/.backup_env"

log_info "📝 Información de backup guardada para scripts de migración"

exit 0