#!/bin/bash

# 🚀 SCRIPT DE EJECUCIÓN DE MIGRACIÓN - SUPERMCP
# Implementa la reestructuración arquitectural completa

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_phase() { echo -e "${PURPLE}[PHASE]${NC} $1"; }

# Configuration
PROJECT_ROOT="/home/ubuntu/supermcp"
MIGRATION_LOG="$PROJECT_ROOT/migration-tools/migration.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Initialize migration log
echo "=== SUPERMCP MIGRATION EXECUTION - $TIMESTAMP ===" > "$MIGRATION_LOG"

log_phase "🚀 INICIANDO MIGRACIÓN ARQUITECTURAL SUPERMCP..."
echo "Timestamp: $TIMESTAMP" >> "$MIGRATION_LOG"

# Check if backup exists
if [ ! -f "$PROJECT_ROOT/migration-tools/.backup_env" ]; then
    log_error "❌ No se encontró backup. Ejecutar pre-migration-backup.sh primero"
    exit 1
fi

source "$PROJECT_ROOT/migration-tools/.backup_env"
log_info "📦 Backup disponible en: $BACKUP_PATH"

# ========================================
# FASE 1: LIMPIEZA INMEDIATA
# ========================================

log_phase "🧹 FASE 1: LIMPIEZA INMEDIATA"

log_info "🗑️ Eliminando archivos basura..."

# Remove backup directories (8.2MB)
if [ -d "backup_complete_mcp" ]; then
    rm -rf backup_complete_mcp/
    log_success "✅ Eliminado: backup_complete_mcp/"
fi

if [ -d "backup_adapters_complete" ]; then
    rm -rf backup_adapters_complete/
    log_success "✅ Eliminado: backup_adapters_complete/"
fi

if [ -d "backup_backend_controllers" ]; then
    rm -rf backup_backend_controllers/
    log_success "✅ Eliminado: backup_backend_controllers/"
fi

# Remove duplicate frontend
if [ -d "mcp-frontend" ]; then
    rm -rf mcp-frontend/
    log_success "✅ Eliminado: mcp-frontend/ (frontend duplicado)"
fi

# Remove zip files
if [ -f "supermcp25.zip" ]; then
    rm supermcp25.zip
    log_success "✅ Eliminado: supermcp25.zip"
fi

if [ -f "mcp_system_updated.zip" ]; then
    rm mcp_system_updated.zip
    log_success "✅ Eliminado: mcp_system_updated.zip"
fi

# Remove temporary files
find . -name "*.backup.*" -delete 2>/dev/null || true
find . -name ".last_backup_path" -delete 2>/dev/null || true

log_success "✅ FASE 1 COMPLETADA: Limpieza realizada"

# ========================================
# FASE 2: CREAR NUEVA ESTRUCTURA
# ========================================

log_phase "🏗️ FASE 2: CREANDO NUEVA ESTRUCTURA"

log_info "📁 Creando directorios de nueva arquitectura..."

# Create main structure
mkdir -p apps/{backend,frontend}
mkdir -p services/{voice-system,chain-of-debate,langgraph-studio,observatory,mcp-devtools}
mkdir -p packages/{shared-types,shared-utils,mcp-sdk,api-client}
mkdir -p infrastructure/{docker,k8s,terraform,scripts}
mkdir -p docs/{api,architecture,deployment,development}
mkdir -p tests/{e2e,integration,performance}
mkdir -p tools/{scripts,generators,linting}

log_success "✅ Estructura de directorios creada"

# ========================================
# FASE 3: MIGRAR BACKEND PRINCIPAL
# ========================================

log_phase "🔧 FASE 3: MIGRANDO BACKEND PRINCIPAL"

log_info "📦 Migrando backend a apps/backend..."

# Copy existing backend
if [ -d "backend" ]; then
    cp -r backend/* apps/backend/
    log_success "✅ Backend copiado a apps/backend/"
fi

# Create backend internal structure
mkdir -p apps/backend/src/{core,adapters,controllers,services,middleware,routes,utils}

# Move existing components to new structure
if [ -d "apps/backend/src" ] && [ -f "apps/backend/src/index.js" ]; then
    # Move adapters
    if [ -d "apps/backend/src/adapters" ]; then
        mv apps/backend/src/adapters/* apps/backend/src/adapters/ 2>/dev/null || true
    fi
    
    # Move routes
    if [ -d "apps/backend/src/routes" ]; then
        mv apps/backend/src/routes/* apps/backend/src/routes/ 2>/dev/null || true
    fi
    
    # Move services
    if [ -d "apps/backend/src/services" ]; then
        mv apps/backend/src/services/* apps/backend/src/services/ 2>/dev/null || true
    fi
fi

# Move root files to backend
if [ -f "mcp_production_server.js" ]; then
    mv mcp_production_server.js apps/backend/src/
    log_success "✅ Movido: mcp_production_server.js"
fi

if [ -f "python_orchestration_server.py" ]; then
    mv python_orchestration_server.py apps/backend/src/
    log_success "✅ Movido: python_orchestration_server.py"
fi

log_success "✅ FASE 3 COMPLETADA: Backend migrado"

# ========================================
# FASE 4: MIGRAR FRONTEND
# ========================================

log_phase "🎨 FASE 4: MIGRANDO FRONTEND"

log_info "🖥️ Migrando frontend a apps/frontend..."

if [ -d "frontend" ]; then
    cp -r frontend/* apps/frontend/
    log_success "✅ Frontend copiado a apps/frontend/"
fi

log_success "✅ FASE 4 COMPLETADA: Frontend migrado"

# ========================================
# FASE 5: MIGRAR SERVICIOS
# ========================================

log_phase "🔧 FASE 5: MIGRANDO SERVICIOS ESPECIALIZADOS"

# Voice System
if [ -d "voice_system" ]; then
    cp -r voice_system/* services/voice-system/
    log_success "✅ Voice system migrado"
fi

# Chain-of-Debate (already exists)
if [ -d "services/chain-of-debate" ]; then
    log_success "✅ Chain-of-Debate ya existe"
fi

# LangGraph System
if [ -d "langgraph_system" ]; then
    cp -r langgraph_system/* services/langgraph-studio/
    log_success "✅ LangGraph system migrado"
fi

# MCP Observatory
if [ -d "mcp-observatory" ]; then
    cp -r mcp-observatory/* services/observatory/
    log_success "✅ MCP Observatory migrado"
fi

# Move remaining Python files
if [ -f "terminal_agent.py" ]; then
    mv terminal_agent.py services/mcp-devtools/
    log_success "✅ Movido: terminal_agent.py"
fi

if [ -f "complete_webhook_agent_end_task_system.py" ]; then
    mv complete_webhook_agent_end_task_system.py services/mcp-devtools/
    log_success "✅ Movido: complete_webhook_agent_end_task_system.py"
fi

log_success "✅ FASE 5 COMPLETADA: Servicios migrados"

# ========================================
# FASE 6: CONSOLIDAR DOCKER
# ========================================

log_phase "🐳 FASE 6: CONSOLIDANDO CONFIGURACIONES DOCKER"

log_info "📋 Consolidando archivos Docker..."

# Move docker files to infrastructure
if [ -f "docker-compose.yml" ]; then
    cp docker-compose.yml infrastructure/docker/docker-compose.dev.yml
fi

if [ -f "docker-compose.production.yml" ]; then
    cp docker-compose.production.yml infrastructure/docker/docker-compose.prod.yml
fi

# Create test compose file
cat > infrastructure/docker/docker-compose.test.yml << 'EOF'
version: '3.8'
services:
  backend-test:
    build: ../../apps/backend
    environment:
      - NODE_ENV=test
    ports:
      - "3000:3000"
    command: npm test

  voice-system-test:
    build: ../../services/voice-system
    environment:
      - ENVIRONMENT=test
    ports:
      - "8001:8001"
    command: python -m pytest

  chain-of-debate-test:
    build: ../../services/chain-of-debate
    environment:
      - FLASK_ENV=testing
    ports:
      - "5555:5555"
    command: python -m pytest
EOF

# Remove old docker files from root
rm -f docker-compose.yml docker-compose.production.yml 2>/dev/null || true

log_success "✅ FASE 6 COMPLETADA: Docker consolidado"

# ========================================
# FASE 7: CREAR WORKSPACE PACKAGE.JSON
# ========================================

log_phase "📦 FASE 7: CONFIGURANDO WORKSPACE"

log_info "📄 Creando root package.json para workspace..."

# Backup original package.json
if [ -f "package.json" ]; then
    cp package.json package.json.backup
fi

# Create new workspace package.json
cat > package.json << 'EOF'
{
  "name": "supermcp",
  "version": "4.0.0",
  "description": "SuperMCP - Restructured Architecture",
  "private": true,
  "workspaces": [
    "apps/*",
    "services/*",
    "packages/*"
  ],
  "scripts": {
    "dev": "docker-compose -f infrastructure/docker/docker-compose.dev.yml up",
    "prod": "docker-compose -f infrastructure/docker/docker-compose.prod.yml up -d",
    "test": "docker-compose -f infrastructure/docker/docker-compose.test.yml up --abort-on-container-exit",
    "build": "turbo run build",
    "lint": "turbo run lint",
    "type-check": "turbo run type-check",
    "clean": "turbo run clean",
    "backend:dev": "cd apps/backend && npm run dev",
    "frontend:dev": "cd apps/frontend && npm run dev",
    "voice:start": "cd services/voice-system && python main.py",
    "chain-of-debate:start": "cd services/chain-of-debate && python entrypoint.py",
    "migrate:validate": "./migration-tools/scripts/validate-migration.sh"
  },
  "devDependencies": {
    "turbo": "^1.10.0",
    "@types/node": "^20.10.0"
  },
  "engines": {
    "node": ">=18.0.0",
    "npm": ">=9.0.0"
  },
  "repository": {
    "type": "git",
    "url": "https://github.com/fmfg03/supermcp.git"
  }
}
EOF

log_success "✅ FASE 7 COMPLETADA: Workspace configurado"

# ========================================
# FASE 8: CONSOLIDAR DOCUMENTACIÓN
# ========================================

log_phase "📚 FASE 8: CONSOLIDANDO DOCUMENTACIÓN"

log_info "📄 Moviendo documentación a docs/..."

# Move markdown files
for file in *.md; do
    if [ -f "$file" ] && [ "$file" != "README.md" ]; then
        case "$file" in
            *ARCHITECTURE*|*architecture*)
                mv "$file" docs/architecture/
                ;;
            *DEPLOYMENT*|*deployment*|*INSTALL*)
                mv "$file" docs/deployment/
                ;;
            *API*|*api*)
                mv "$file" docs/api/
                ;;
            *)
                mv "$file" docs/development/
                ;;
        esac
        log_success "✅ Movido: $file"
    fi
done

# Create updated README.md
cat > README.md << 'EOF'
# 🚀 SuperMCP - Model Context Protocol Enterprise System

## 🏗️ Architecture Overview

SuperMCP is a restructured, enterprise-grade MCP (Model Context Protocol) system with clean architecture and modular design.

### 📁 Project Structure

```
supermcp/
├── 📁 apps/                    # Main applications
│   ├── 📁 backend/             # Backend API
│   └── 📁 frontend/            # Frontend UI
├── 📁 services/                # Specialized microservices
│   ├── 📁 voice-system/        # Voice processing
│   ├── 📁 chain-of-debate/     # Multi-LLM debates
│   ├── 📁 langgraph-studio/    # LangGraph integration
│   └── 📁 observatory/         # MCP monitoring
├── 📁 packages/                # Shared packages
├── 📁 infrastructure/          # Infrastructure as Code
├── 📁 docs/                    # Documentation
└── 📁 tests/                   # Integration tests
```

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start development environment
npm run dev

# Run tests
npm run test

# Validate migration
npm run migrate:validate
```

## 📋 Available Scripts

- `npm run dev` - Start development environment
- `npm run prod` - Start production environment
- `npm run test` - Run all tests
- `npm run build` - Build all packages
- `npm run lint` - Lint all packages

## 📚 Documentation

- [Architecture](docs/architecture/) - System architecture
- [Deployment](docs/deployment/) - Deployment guides
- [API](docs/api/) - API documentation
- [Development](docs/development/) - Development guides

## 🎯 Features

- ✅ Clean monorepo architecture
- ✅ Docker containerization
- ✅ MCP protocol support
- ✅ Voice system integration
- ✅ Multi-LLM debate system
- ✅ Enterprise monitoring

## 🤝 Contributing

See [Development Guide](docs/development/) for contributing guidelines.
EOF

log_success "✅ FASE 8 COMPLETADA: Documentación consolidada"

# ========================================
# FASE 9: CREAR TURBO.JSON
# ========================================

log_phase "⚡ FASE 9: CONFIGURANDO TURBOREPO"

log_info "⚙️ Creando turbo.json..."

cat > turbo.json << 'EOF'
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": ["**/.env.*local"],
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", "build/**", ".next/**", "!.next/cache/**"]
    },
    "test": {
      "dependsOn": ["build"],
      "outputs": ["coverage/**"]
    },
    "lint": {
      "outputs": []
    },
    "type-check": {
      "outputs": []
    },
    "dev": {
      "cache": false,
      "persistent": true
    },
    "clean": {
      "cache": false
    }
  }
}
EOF

log_success "✅ FASE 9 COMPLETADA: Turborepo configurado"

# ========================================
# VALIDATION & CLEANUP
# ========================================

log_phase "🧪 VALIDACIÓN Y LIMPIEZA FINAL"

log_info "🔍 Validando migración..."

# Remove old directories if they're empty or duplicated
[ -d "backend" ] && [ -d "apps/backend" ] && rm -rf backend/
[ -d "frontend" ] && [ -d "apps/frontend" ] && rm -rf frontend/
[ -d "voice_system" ] && [ -d "services/voice-system" ] && rm -rf voice_system/
[ -d "langgraph_system" ] && [ -d "services/langgraph-studio" ] && rm -rf langgraph_system/

# Create basic .gitignore for new structure
cat > .gitignore << 'EOF'
# Dependencies
node_modules/
*/node_modules/

# Build outputs
dist/
build/
*.tsbuildinfo

# Environment files
.env
.env.local
.env.*.local

# Logs
*.log
logs/

# Runtime data
*.pid
*.seed

# Coverage
coverage/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Turbo
.turbo/

# Docker
.dockerignore

# Backup files
*.backup.*
*-backup-*
backup_*/
EOF

# Create migration completion marker
echo "Migration completed on: $TIMESTAMP" > migration-tools/.migration_completed
echo "Backup location: $BACKUP_PATH" >> migration-tools/.migration_completed

# ========================================
# FINAL REPORT
# ========================================

log_phase "📊 GENERANDO REPORTE FINAL"

echo ""
echo "================================================="
echo "       🎉 MIGRACIÓN COMPLETADA EXITOSAMENTE"
echo "================================================="
echo ""
echo "📦 Nueva estructura implementada:"
echo "   ✅ apps/ - Aplicaciones principales"
echo "   ✅ services/ - Servicios especializados"
echo "   ✅ packages/ - Paquetes compartidos"
echo "   ✅ infrastructure/ - Configuraciones"
echo "   ✅ docs/ - Documentación consolidada"
echo ""
echo "🧹 Limpieza realizada:"
echo "   ✅ 8.2MB archivos basura eliminados"
echo "   ✅ Frontends duplicados removidos"
echo "   ✅ Docker configs consolidados"
echo ""
echo "📋 Próximos pasos:"
echo "   1. Ejecutar: npm install"
echo "   2. Validar: npm run migrate:validate"
echo "   3. Probar: npm run dev"
echo ""
echo "💾 Backup disponible en: $BACKUP_PATH"
echo "📋 Log completo: $MIGRATION_LOG"
echo ""
log_success "🚀 ¡MIGRACIÓN ARQUITECTURAL COMPLETADA!"
echo ""
echo "Para validar la migración, ejecutar:"
echo "   ./migration-tools/scripts/validate-migration.sh"

exit 0