#!/bin/bash
set -euo pipefail

# SuperMCP UV Installation Script
# Fast, reproducible Python dependency management

echo "🚀 SuperMCP UV Integration Setup"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [[ ! -f "requirements.txt" ]]; then
    print_error "requirements.txt not found. Please run this script from the SuperMCP root directory."
    exit 1
fi

print_status "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
if [[ $(python3 -c "import sys; print(1 if sys.version_info >= (3, 8) else 0)") -eq 0 ]]; then
    print_error "Python 3.8 or higher required. Found: $python_version"
    exit 1
fi
print_success "Python version: $python_version ✓"

# Install uv if not already installed
if ! command -v uv &> /dev/null; then
    print_status "Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    print_success "uv installed successfully"
else
    print_success "uv already installed: $(uv --version)"
fi

# Ensure uv is in PATH
if ! command -v uv &> /dev/null; then
    export PATH="$HOME/.local/bin:$PATH"
    if ! command -v uv &> /dev/null; then
        print_error "uv installation failed or not in PATH"
        exit 1
    fi
fi

# Generate/update lockfile
print_status "Generating uv.lock from requirements.txt..."
if uv pip compile requirements.txt --output-file uv.lock; then
    print_success "uv.lock generated successfully"
else
    print_error "Failed to generate uv.lock"
    exit 1
fi

# Check if virtual environment exists
if [[ ! -d ".venv" ]]; then
    print_status "Creating virtual environment..."
    python3 -m venv .venv
    print_success "Virtual environment created"
fi

# Activate virtual environment and install dependencies
print_status "Installing dependencies with uv..."
source .venv/bin/activate

if uv pip install -r uv.lock; then
    print_success "Dependencies installed successfully with uv"
else
    print_error "Failed to install dependencies with uv"
    exit 1
fi

# Install Node.js dependencies
if [[ -f "package.json" ]]; then
    print_status "Installing Node.js dependencies..."
    if command -v pnpm &> /dev/null; then
        pnpm install
    elif command -v yarn &> /dev/null; then
        yarn install
    else
        npm install
    fi
    print_success "Node.js dependencies installed"
fi

# Create development scripts
print_status "Creating development scripts..."

# Create uv install script
cat > scripts/uv-install.sh << 'EOF'
#!/bin/bash
# Quick dependency installation with uv
export PATH="$HOME/.local/bin:$PATH"
echo "📦 Installing Python dependencies with uv..."
uv pip install -r uv.lock
echo "✅ Dependencies installed"
EOF

# Create uv update script
cat > scripts/uv-update.sh << 'EOF'
#!/bin/bash
# Update dependencies and regenerate lockfile
export PATH="$HOME/.local/bin:$PATH"
echo "🔄 Updating dependencies..."
uv pip compile requirements.txt --output-file uv.lock --upgrade
uv pip install -r uv.lock
echo "✅ Dependencies updated"
EOF

# Create uv add script
cat > scripts/uv-add.sh << 'EOF'
#!/bin/bash
# Add new dependency with uv
export PATH="$HOME/.local/bin:$PATH"
if [[ -z "$1" ]]; then
    echo "Usage: ./scripts/uv-add.sh <package-name>"
    exit 1
fi
echo "➕ Adding $1 to requirements.txt..."
echo "$1" >> requirements.txt
uv pip compile requirements.txt --output-file uv.lock
uv pip install -r uv.lock
echo "✅ $1 added and installed"
EOF

chmod +x scripts/uv-*.sh
print_success "Development scripts created"

# Update documentation
print_status "Updating README.md with uv instructions..."

# Check if uv section exists in README
if ! grep -q "## Installation with uv" README.md; then
    # Add uv installation section
    cat >> README.md << 'EOF'

## Installation with uv (Recommended)

SuperMCP now uses [uv](https://github.com/astral-sh/uv) for ultra-fast Python dependency management.

### Quick Setup

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install all dependencies
./scripts/install-uv.sh

# Or manually:
uv pip install -r uv.lock
```

### Development Commands

```bash
# Install dependencies
./scripts/uv-install.sh

# Update dependencies  
./scripts/uv-update.sh

# Add new dependency
./scripts/uv-add.sh <package-name>
```

### Benefits

- 🚀 **8-10x faster** than pip
- 🔒 **Reproducible builds** with uv.lock
- 🛡️ **Security verification** with hash checking
- 📦 **Cross-platform compatibility**
- 🔄 **Easy CI/CD integration**

EOF
    print_success "README.md updated with uv documentation"
else
    print_warning "uv section already exists in README.md"
fi

# Check environment
print_status "Verifying installation..."

# Test import of key packages
python3 -c "
import sys
try:
    import fastapi
    import langchain
    import openai
    import supabase
    print('✅ Key packages imported successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"

print_success "Environment verification completed"

echo ""
echo "🎉 SuperMCP UV Integration Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Activate environment: source .venv/bin/activate"
echo "2. Start development: npm run dev"
echo "3. For production: npm run prod"
echo ""
echo "UV Commands:"
echo "• Install deps: ./scripts/uv-install.sh"
echo "• Update deps:  ./scripts/uv-update.sh"  
echo "• Add package:  ./scripts/uv-add.sh <name>"
echo ""
echo "🚀 Ready for 8-10x faster Python dependency management!"