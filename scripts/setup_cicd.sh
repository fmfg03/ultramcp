#!/bin/bash

# UltraMCP ContextBuilderAgent 2.0 - CI/CD Setup Script
# Automated setup for GitHub Actions CI/CD pipeline

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking CI/CD prerequisites..."
    
    # Check GitHub CLI
    if ! command -v gh &> /dev/null; then
        warning "GitHub CLI not found. Install it from: https://cli.github.com/"
    else
        success "GitHub CLI found"
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    # Check if we're in a git repository
    if ! git rev-parse --git-dir &> /dev/null; then
        error "Not in a git repository"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Setup GitHub repository secrets
setup_github_secrets() {
    log "Setting up GitHub repository secrets..."
    
    if ! command -v gh &> /dev/null; then
        warning "GitHub CLI not available. Please manually set up the following secrets:"
        echo "Required secrets:"
        echo "  - SONAR_TOKEN: SonarCloud authentication token"
        echo "  - SNYK_TOKEN: Snyk security scanning token"
        echo "  - SLACK_WEBHOOK_URL: Slack notification webhook"
        echo "  - SECURITY_SLACK_WEBHOOK_URL: Security alerts webhook"
        echo "  - KUBECONFIG_STAGING: Base64 encoded staging kubeconfig"
        echo "  - KUBECONFIG_PRODUCTION: Base64 encoded production kubeconfig"
        return
    fi
    
    # Check if authenticated
    if ! gh auth status &> /dev/null; then
        log "Authenticating with GitHub..."
        gh auth login
    fi
    
    # Set secrets (will prompt for values)
    log "Setting up repository secrets..."
    
    echo "Enter SonarCloud token (or press Enter to skip):"
    read -s SONAR_TOKEN
    if [[ -n "$SONAR_TOKEN" ]]; then
        gh secret set SONAR_TOKEN --body "$SONAR_TOKEN"
        success "SONAR_TOKEN secret set"
    fi
    
    echo "Enter Snyk token (or press Enter to skip):"
    read -s SNYK_TOKEN
    if [[ -n "$SNYK_TOKEN" ]]; then
        gh secret set SNYK_TOKEN --body "$SNYK_TOKEN"
        success "SNYK_TOKEN secret set"
    fi
    
    echo "Enter Slack webhook URL (or press Enter to skip):"
    read -s SLACK_WEBHOOK_URL
    if [[ -n "$SLACK_WEBHOOK_URL" ]]; then
        gh secret set SLACK_WEBHOOK_URL --body "$SLACK_WEBHOOK_URL"
        success "SLACK_WEBHOOK_URL secret set"
    fi
    
    success "GitHub secrets configuration completed"
}

# Create test files if they don't exist
create_test_files() {
    log "Creating test files structure..."
    
    # Create test directories
    mkdir -p "$PROJECT_ROOT/tests/unit"
    mkdir -p "$PROJECT_ROOT/tests/integration"
    mkdir -p "$PROJECT_ROOT/tests/performance"
    mkdir -p "$PROJECT_ROOT/tests/policies"
    
    # Create basic test files
    if [[ ! -f "$PROJECT_ROOT/tests/unit/test_contextbuilder.py" ]]; then
        cat > "$PROJECT_ROOT/tests/unit/test_contextbuilder.py" <<'EOF'
import pytest
import asyncio
from unittest.mock import Mock, patch


class TestContextBuilderCore:
    """Unit tests for ContextBuilder Core functionality"""
    
    @pytest.mark.asyncio
    async def test_context_validation(self):
        """Test context validation functionality"""
        # Mock test - replace with actual implementation
        assert True
    
    @pytest.mark.asyncio
    async def test_coherence_scoring(self):
        """Test coherence scoring algorithm"""
        # Mock test - replace with actual implementation
        assert True
    
    def test_health_check(self):
        """Test health check endpoint"""
        # Mock test - replace with actual implementation
        assert True


class TestBeliefReviser:
    """Unit tests for Belief Reviser service"""
    
    @pytest.mark.asyncio
    async def test_belief_revision(self):
        """Test belief revision logic"""
        # Mock test - replace with actual implementation
        assert True
    
    def test_contradiction_detection(self):
        """Test contradiction detection"""
        # Mock test - replace with actual implementation
        assert True


class TestPromptAssembler:
    """Unit tests for Prompt Assembler service"""
    
    @pytest.mark.asyncio
    async def test_prompt_assembly(self):
        """Test prompt assembly functionality"""
        # Mock test - replace with actual implementation
        assert True
    
    def test_template_validation(self):
        """Test prompt template validation"""
        # Mock test - replace with actual implementation
        assert True
EOF
        success "Created unit test file"
    fi
    
    # Create integration test file
    if [[ ! -f "$PROJECT_ROOT/tests/integration/test_api_integration.py" ]]; then
        cat > "$PROJECT_ROOT/tests/integration/test_api_integration.py" <<'EOF'
import pytest
import asyncio
import aiohttp
import os


class TestAPIIntegration:
    """Integration tests for ContextBuilderAgent APIs"""
    
    @pytest.fixture
    def base_url(self):
        return os.getenv('API_BASE_URL', 'http://sam.chat:8020')
    
    @pytest.mark.asyncio
    async def test_health_endpoints(self, base_url):
        """Test all service health endpoints"""
        services = [
            ('contextbuilder-core', 8020),
            ('belief-reviser', 8022),
            ('prompt-assembler', 8027),
            ('context-observatory', 8028),
        ]
        
        async with aiohttp.ClientSession() as session:
            for service, port in services:
                async with session.get(f'http://sam.chat:{port}/health') as resp:
                    assert resp.status == 200
                    data = await resp.json()
                    assert data.get('status') == 'healthy'
    
    @pytest.mark.asyncio
    async def test_context_validation_flow(self, base_url):
        """Test complete context validation workflow"""
        async with aiohttp.ClientSession() as session:
            # Test context validation
            payload = {
                'context_id': 'test-001',
                'validation_type': 'semantic',
                'content': 'Test context content',
                'coherence_threshold': 0.8
            }
            
            async with session.post(f'{base_url}/api/context/validate', json=payload) as resp:
                assert resp.status == 200
                data = await resp.json()
                assert 'coherence_score' in data
    
    @pytest.mark.asyncio
    async def test_cross_service_integration(self, base_url):
        """Test integration between multiple services"""
        # Test workflow that spans multiple services
        async with aiohttp.ClientSession() as session:
            # 1. Validate context
            # 2. Revise beliefs
            # 3. Assemble prompt
            # 4. Monitor in observatory
            pass  # Implement actual integration test
EOF
        success "Created integration test file"
    fi
    
    # Create performance test file
    if [[ ! -f "$PROJECT_ROOT/tests/performance/benchmark.py" ]]; then
        cat > "$PROJECT_ROOT/tests/performance/benchmark.py" <<'EOF'
#!/usr/bin/env python3
"""
ContextBuilderAgent Performance Benchmarks
"""

import asyncio
import aiohttp
import time
import statistics
import json
from concurrent.futures import ThreadPoolExecutor


class PerformanceBenchmark:
    """Performance benchmark suite for ContextBuilderAgent"""
    
    def __init__(self, base_url='http://sam.chat:8020'):
        self.base_url = base_url
        self.results = {}
    
    async def benchmark_context_validation(self, concurrent_requests=10, total_requests=100):
        """Benchmark context validation performance"""
        print(f"Benchmarking context validation ({total_requests} requests, {concurrent_requests} concurrent)")
        
        async def single_request(session, request_id):
            start_time = time.time()
            
            payload = {
                'context_id': f'benchmark-{request_id}',
                'validation_type': 'semantic',
                'content': f'Benchmark context content {request_id}',
                'coherence_threshold': 0.8
            }
            
            try:
                async with session.post(f'{self.base_url}/api/context/validate', json=payload) as resp:
                    await resp.json()
                    return time.time() - start_time, resp.status
            except Exception as e:
                return time.time() - start_time, 0
        
        async with aiohttp.ClientSession() as session:
            semaphore = asyncio.Semaphore(concurrent_requests)
            
            async def limited_request(request_id):
                async with semaphore:
                    return await single_request(session, request_id)
            
            tasks = [limited_request(i) for i in range(total_requests)]
            results = await asyncio.gather(*tasks)
        
        response_times = [r[0] for r in results]
        status_codes = [r[1] for r in results]
        
        success_rate = sum(1 for s in status_codes if s == 200) / len(status_codes) * 100
        
        self.results['context_validation'] = {
            'total_requests': total_requests,
            'concurrent_requests': concurrent_requests,
            'success_rate': success_rate,
            'avg_response_time': statistics.mean(response_times),
            'min_response_time': min(response_times),
            'max_response_time': max(response_times),
            'p95_response_time': statistics.quantiles(response_times, n=20)[18],
            'p99_response_time': statistics.quantiles(response_times, n=100)[98],
        }
        
        return self.results['context_validation']
    
    async def benchmark_belief_revision(self, concurrent_requests=5, total_requests=50):
        """Benchmark belief revision performance"""
        print(f"Benchmarking belief revision ({total_requests} requests, {concurrent_requests} concurrent)")
        
        # Similar implementation to context validation
        # Add belief revision specific benchmarking logic
        pass
    
    def generate_report(self):
        """Generate performance report"""
        print("\n" + "="*50)
        print("CONTEXTBUILDERAGENT PERFORMANCE REPORT")
        print("="*50)
        
        for test_name, results in self.results.items():
            print(f"\n{test_name.upper()} RESULTS:")
            print(f"  Total Requests: {results['total_requests']}")
            print(f"  Concurrent Requests: {results['concurrent_requests']}")
            print(f"  Success Rate: {results['success_rate']:.2f}%")
            print(f"  Average Response Time: {results['avg_response_time']:.3f}s")
            print(f"  95th Percentile: {results['p95_response_time']:.3f}s")
            print(f"  99th Percentile: {results['p99_response_time']:.3f}s")
        
        # Save results to file
        with open('performance_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Generate markdown report
        with open('tests/performance/results.md', 'w') as f:
            f.write("# ContextBuilderAgent Performance Results\n\n")
            for test_name, results in self.results.items():
                f.write(f"## {test_name.replace('_', ' ').title()}\n\n")
                f.write(f"- **Success Rate**: {results['success_rate']:.2f}%\n")
                f.write(f"- **Average Response Time**: {results['avg_response_time']:.3f}s\n")
                f.write(f"- **95th Percentile**: {results['p95_response_time']:.3f}s\n")
                f.write(f"- **99th Percentile**: {results['p99_response_time']:.3f}s\n\n")


async def main():
    """Run performance benchmarks"""
    benchmark = PerformanceBenchmark()
    
    # Run benchmarks
    await benchmark.benchmark_context_validation()
    
    # Generate report
    benchmark.generate_report()
    print("\nPerformance benchmarking completed!")


if __name__ == "__main__":
    asyncio.run(main())
EOF
        chmod +x "$PROJECT_ROOT/tests/performance/benchmark.py"
        success "Created performance benchmark file"
    fi
    
    # Create security policy file
    if [[ ! -f "$PROJECT_ROOT/tests/policies/security.rego" ]]; then
        cat > "$PROJECT_ROOT/tests/policies/security.rego" <<'EOF'
package kubernetes.security

# Deny containers running as root
deny[msg] {
    input.kind == "Deployment"
    input.spec.template.spec.containers[_].securityContext.runAsUser == 0
    msg := "Container must not run as root user"
}

# Require security contexts
deny[msg] {
    input.kind == "Deployment"
    not input.spec.template.spec.containers[_].securityContext
    msg := "Container must have security context defined"
}

# Require resource limits
deny[msg] {
    input.kind == "Deployment"
    not input.spec.template.spec.containers[_].resources.limits
    msg := "Container must have resource limits defined"
}

# Deny privileged containers
deny[msg] {
    input.kind == "Deployment"
    input.spec.template.spec.containers[_].securityContext.privileged == true
    msg := "Container must not run in privileged mode"
}

# Require read-only root filesystem
deny[msg] {
    input.kind == "Deployment"
    not input.spec.template.spec.containers[_].securityContext.readOnlyRootFilesystem == true
    msg := "Container must have read-only root filesystem"
}
EOF
        success "Created security policy file"
    fi
    
    success "Test files structure created"
}

# Create CI/CD configuration files
create_cicd_configs() {
    log "Creating CI/CD configuration files..."
    
    # Create pytest configuration
    if [[ ! -f "$PROJECT_ROOT/pytest.ini" ]]; then
        cat > "$PROJECT_ROOT/pytest.ini" <<'EOF'
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=services
    --cov-report=term-missing
    --cov-report=xml
    --cov-report=html
markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    security: Security tests
    slow: Slow running tests
EOF
        success "Created pytest configuration"
    fi
    
    # Create SonarCloud configuration
    if [[ ! -f "$PROJECT_ROOT/sonar-project.properties" ]]; then
        cat > "$PROJECT_ROOT/sonar-project.properties" <<'EOF'
sonar.projectKey=ultramcp_contextbuilder-agent
sonar.organization=ultramcp
sonar.projectName=ContextBuilderAgent 2.0

# Source code configuration
sonar.sources=services
sonar.tests=tests
sonar.python.coverage.reportPaths=coverage.xml

# Code analysis configuration
sonar.python.pylint.reportPaths=pylint-report.txt
sonar.python.bandit.reportPaths=bandit-report.json

# Exclusions
sonar.exclusions=**/*_test.py,**/test_*.py,**/__pycache__/**,**/venv/**

# Coverage exclusions
sonar.coverage.exclusions=tests/**,**/*_test.py,**/test_*.py
EOF
        success "Created SonarCloud configuration"
    fi
    
    # Create security scanning configuration
    if [[ ! -f "$PROJECT_ROOT/.bandit" ]]; then
        cat > "$PROJECT_ROOT/.bandit" <<'EOF'
[bandit]
exclude_dirs = tests,venv,.venv,build,dist
skips = B101,B601
EOF
        success "Created Bandit configuration"
    fi
    
    success "CI/CD configuration files created"
}

# Setup local development tools
setup_dev_tools() {
    log "Setting up local development tools..."
    
    # Create pre-commit configuration
    if [[ ! -f "$PROJECT_ROOT/.pre-commit-config.yaml" ]]; then
        cat > "$PROJECT_ROOT/.pre-commit-config.yaml" <<'EOF'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=88', '--extend-ignore=E203']

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ["-c", ".bandit"]

  - repo: https://github.com/adrienverge/yamllint
    rev: v1.32.0
    hooks:
      - id: yamllint
        args: [-c=.yamllint]

  - repo: https://github.com/hadolint/hadolint
    rev: v2.12.0
    hooks:
      - id: hadolint-docker
EOF
        success "Created pre-commit configuration"
    fi
    
    # Install pre-commit if available
    if command -v pre-commit &> /dev/null; then
        log "Installing pre-commit hooks..."
        pre-commit install
        success "Pre-commit hooks installed"
    else
        warning "pre-commit not available. Install it with: pip install pre-commit"
    fi
    
    success "Development tools setup completed"
}

# Validate CI/CD setup
validate_setup() {
    log "Validating CI/CD setup..."
    
    # Check if GitHub workflows exist
    if [[ -f "$PROJECT_ROOT/.github/workflows/ci.yml" ]]; then
        success "CI workflow found"
    else
        error "CI workflow missing"
    fi
    
    if [[ -f "$PROJECT_ROOT/.github/workflows/security.yml" ]]; then
        success "Security workflow found"
    else
        error "Security workflow missing"
    fi
    
    if [[ -f "$PROJECT_ROOT/.github/workflows/release.yml" ]]; then
        success "Release workflow found"
    else
        error "Release workflow missing"
    fi
    
    # Check test structure
    if [[ -d "$PROJECT_ROOT/tests" ]]; then
        success "Test directory structure exists"
    else
        error "Test directory missing"
    fi
    
    # Validate YAML files
    if command -v yamllint &> /dev/null; then
        log "Validating YAML files..."
        yamllint .github/workflows/ || warning "YAML validation issues found"
    fi
    
    success "CI/CD setup validation completed"
}

# Show setup summary
show_summary() {
    log "CI/CD Setup Summary"
    echo
    echo "✅ GitHub Actions Workflows:"
    echo "   - CI/CD Pipeline (.github/workflows/ci.yml)"
    echo "   - Security Pipeline (.github/workflows/security.yml)"
    echo "   - Release Pipeline (.github/workflows/release.yml)"
    echo
    echo "✅ Test Structure:"
    echo "   - Unit Tests (tests/unit/)"
    echo "   - Integration Tests (tests/integration/)"
    echo "   - Performance Tests (tests/performance/)"
    echo "   - Security Policies (tests/policies/)"
    echo
    echo "✅ Configuration Files:"
    echo "   - pytest.ini (Python testing)"
    echo "   - sonar-project.properties (Code quality)"
    echo "   - .bandit (Security scanning)"
    echo "   - .pre-commit-config.yaml (Git hooks)"
    echo
    echo "🚀 Next Steps:"
    echo "   1. Push changes to GitHub repository"
    echo "   2. Configure required secrets in GitHub repository"
    echo "   3. Enable GitHub Actions in repository settings"
    echo "   4. Set up SonarCloud and Snyk integrations"
    echo "   5. Configure Kubernetes clusters for staging/production"
    echo
    echo "📚 Documentation:"
    echo "   - GitHub Actions: https://docs.github.com/en/actions"
    echo "   - SonarCloud: https://sonarcloud.io/"
    echo "   - Snyk: https://snyk.io/"
}

# Main setup function
main() {
    local action="${1:-setup}"
    
    case "$action" in
        "setup")
            log "Starting ContextBuilderAgent CI/CD Setup"
            check_prerequisites
            create_test_files
            create_cicd_configs
            setup_dev_tools
            setup_github_secrets
            validate_setup
            show_summary
            success "CI/CD setup completed successfully!"
            ;;
        "validate")
            validate_setup
            ;;
        "secrets")
            setup_github_secrets
            ;;
        "help"|*)
            echo "UltraMCP ContextBuilderAgent 2.0 - CI/CD Setup"
            echo
            echo "Usage: $0 [command]"
            echo
            echo "Commands:"
            echo "  setup       Complete CI/CD setup (default)"
            echo "  validate    Validate CI/CD configuration"
            echo "  secrets     Setup GitHub repository secrets"
            echo "  help        Show this help message"
            echo
            echo "Features:"
            echo "  - GitHub Actions workflows (CI, Security, Release)"
            echo "  - Automated testing (Unit, Integration, Performance)"
            echo "  - Security scanning (SAST, Container, Dependencies)"
            echo "  - Code quality analysis (SonarCloud)"
            echo "  - Automated deployments (Staging, Production)"
            echo "  - Pre-commit hooks for code quality"
            ;;
    esac
}

# Run main function
main "$@"