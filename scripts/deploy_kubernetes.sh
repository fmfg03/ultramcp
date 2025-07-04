#!/bin/bash

# UltraMCP ContextBuilderAgent 2.0 - Kubernetes Deployment Script
# Production-ready Kubernetes deployment automation

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
K8S_DIR="$PROJECT_ROOT/k8s"
NAMESPACE="contextbuilder"

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
    log "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not installed"
        exit 1
    fi
    
    # Check kustomize
    if ! command -v kustomize &> /dev/null; then
        warning "kustomize not found, using kubectl kustomize"
    fi
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check cluster resources
    local nodes=$(kubectl get nodes --no-headers | wc -l)
    log "Connected to cluster with $nodes nodes"
    
    success "Prerequisites check passed"
}

# Create namespace
create_namespace() {
    log "Creating namespace..."
    
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log "Namespace $NAMESPACE already exists"
    else
        kubectl apply -f "$K8S_DIR/namespace.yaml"
        success "Namespace $NAMESPACE created"
    fi
}

# Deploy storage
deploy_storage() {
    log "Deploying storage components..."
    
    # Create directories on nodes (for hostPath volumes)
    log "Creating storage directories..."
    kubectl get nodes -o name | while read node; do
        node_name=$(echo $node | cut -d'/' -f2)
        log "Creating directories on node: $node_name"
        
        # This assumes you have SSH access to nodes or are using local cluster
        # For production, use proper storage classes and CSI drivers
        kubectl debug node/$node_name -it --image=busybox -- /bin/sh -c "
            mkdir -p /host/data/contextbuilder/postgres
            mkdir -p /host/data/contextbuilder/redis
            mkdir -p /host/data/contextbuilder/prometheus
            mkdir -p /host/data/contextbuilder/grafana
            mkdir -p /host/data/contextbuilder/context
            chmod 755 /host/data/contextbuilder/*
        " 2>/dev/null || warning "Could not create directories on $node_name"
    done
    
    # Apply storage configurations
    kubectl apply -f "$K8S_DIR/storage/"
    
    # Wait for PVs to be available
    log "Waiting for Persistent Volumes to be available..."
    kubectl wait --for=condition=Available pv --all --timeout=60s
    
    success "Storage deployed"
}

# Deploy secrets and configmaps
deploy_configs() {
    log "Deploying secrets and configuration..."
    
    kubectl apply -f "$K8S_DIR/secrets/"
    kubectl apply -f "$K8S_DIR/configmaps/"
    
    success "Secrets and configuration deployed"
}

# Deploy databases
deploy_databases() {
    log "Deploying database services..."
    
    # Apply database services
    kubectl apply -f "$K8S_DIR/services/database-services.yaml"
    
    # Apply database deployments
    kubectl apply -f "$K8S_DIR/deployments/database-deployments.yaml"
    
    # Wait for databases to be ready
    log "Waiting for databases to be ready..."
    kubectl wait --for=condition=available deployment/postgres -n "$NAMESPACE" --timeout=300s
    kubectl wait --for=condition=available deployment/redis -n "$NAMESPACE" --timeout=300s
    kubectl wait --for=condition=available deployment/pgbouncer -n "$NAMESPACE" --timeout=300s
    
    success "Database services deployed"
}

# Deploy ContextBuilderAgent services
deploy_contextbuilder() {
    log "Deploying ContextBuilderAgent services..."
    
    # Apply ContextBuilder services
    kubectl apply -f "$K8S_DIR/services/contextbuilder-services.yaml"
    
    # Apply ContextBuilder deployments
    kubectl apply -f "$K8S_DIR/deployments/contextbuilder-deployments.yaml"
    
    # Wait for core services to be ready
    log "Waiting for ContextBuilderAgent services to be ready..."
    local services=(
        "contextbuilder-core"
        "belief-reviser"
        "contradiction-resolver"
        "utility-predictor"
        "context-drift-detector"
        "prompt-assembler"
        "context-observatory"
        "deterministic-debug"
        "context-memory-tuner"
    )
    
    for service in "${services[@]}"; do
        log "Waiting for $service to be ready..."
        kubectl wait --for=condition=available deployment/$service -n "$NAMESPACE" --timeout=300s
    done
    
    success "ContextBuilderAgent services deployed"
}

# Deploy monitoring
deploy_monitoring() {
    log "Deploying monitoring stack..."
    
    # Apply monitoring services
    kubectl apply -f "$K8S_DIR/services/monitoring-services.yaml"
    
    # Apply monitoring deployments
    kubectl apply -f "$K8S_DIR/deployments/monitoring-deployments.yaml"
    
    # Wait for monitoring services to be ready
    log "Waiting for monitoring services to be ready..."
    kubectl wait --for=condition=available deployment/prometheus -n "$NAMESPACE" --timeout=300s
    kubectl wait --for=condition=available deployment/grafana -n "$NAMESPACE" --timeout=300s
    kubectl wait --for=condition=available deployment/alertmanager -n "$NAMESPACE" --timeout=300s
    kubectl wait --for=condition=available deployment/metrics-collector -n "$NAMESPACE" --timeout=300s
    
    # Wait for DaemonSet
    kubectl rollout status daemonset/node-exporter -n "$NAMESPACE" --timeout=300s
    
    success "Monitoring stack deployed"
}

# Deploy ingress
deploy_ingress() {
    log "Deploying ingress configuration..."
    
    # Check if ingress controller is available
    if ! kubectl get ingressclass nginx &> /dev/null; then
        warning "Nginx ingress controller not found. Installing..."
        kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml
        
        # Wait for ingress controller to be ready
        log "Waiting for ingress controller to be ready..."
        kubectl wait --namespace ingress-nginx \
            --for=condition=ready pod \
            --selector=app.kubernetes.io/component=controller \
            --timeout=300s
    fi
    
    # Apply ingress configuration
    kubectl apply -f "$K8S_DIR/ingress/"
    
    success "Ingress deployed"
}

# Verify deployment
verify_deployment() {
    log "Verifying deployment..."
    
    # Check all pods are running
    log "Checking pod status..."
    kubectl get pods -n "$NAMESPACE" -o wide
    
    # Check services
    log "Checking services..."
    kubectl get services -n "$NAMESPACE"
    
    # Check ingress
    log "Checking ingress..."
    kubectl get ingress -n "$NAMESPACE"
    
    # Test service health
    log "Testing service health..."
    local healthy_services=0
    local total_services=0
    
    # Get all service endpoints
    kubectl get endpoints -n "$NAMESPACE" --no-headers | while read line; do
        service_name=$(echo $line | awk '{print $1}')
        endpoints=$(echo $line | awk '{print $2}')
        
        if [[ "$endpoints" != "<none>" ]]; then
            ((healthy_services++))
        fi
        ((total_services++))
    done
    
    log "Service health check completed"
    
    # Show cluster resources
    log "Cluster resource usage:"
    kubectl top nodes 2>/dev/null || log "Metrics server not available"
    kubectl top pods -n "$NAMESPACE" 2>/dev/null || log "Pod metrics not available"
    
    success "Deployment verification completed"
}

# Scale deployment
scale_deployment() {
    local component="${1:-all}"
    local replicas="${2:-1}"
    
    log "Scaling $component to $replicas replicas..."
    
    case "$component" in
        "core")
            kubectl scale deployment contextbuilder-core -n "$NAMESPACE" --replicas="$replicas"
            ;;
        "prompt")
            kubectl scale deployment prompt-assembler -n "$NAMESPACE" --replicas="$replicas"
            ;;
        "observatory")
            kubectl scale deployment context-observatory -n "$NAMESPACE" --replicas="$replicas"
            ;;
        "monitoring")
            kubectl scale deployment prometheus -n "$NAMESPACE" --replicas="$replicas"
            kubectl scale deployment grafana -n "$NAMESPACE" --replicas="$replicas"
            ;;
        "all")
            # Scale all services
            local services=(
                "contextbuilder-core"
                "belief-reviser"
                "contradiction-resolver"
                "utility-predictor"
                "context-drift-detector"
                "prompt-assembler"
                "context-observatory"
                "context-memory-tuner"
            )
            
            for service in "${services[@]}"; do
                kubectl scale deployment "$service" -n "$NAMESPACE" --replicas="$replicas"
            done
            ;;
        *)
            kubectl scale deployment "$component" -n "$NAMESPACE" --replicas="$replicas"
            ;;
    esac
    
    success "Scaling completed"
}

# Show status
show_status() {
    log "ContextBuilderAgent 2.0 - Kubernetes Status"
    echo
    
    # Namespace info
    kubectl get namespace "$NAMESPACE" -o wide
    echo
    
    # Pod status
    echo "=== Pod Status ==="
    kubectl get pods -n "$NAMESPACE" -o wide
    echo
    
    # Service status
    echo "=== Service Status ==="
    kubectl get services -n "$NAMESPACE" -o wide
    echo
    
    # Ingress status
    echo "=== Ingress Status ==="
    kubectl get ingress -n "$NAMESPACE" -o wide
    echo
    
    # Persistent Volumes
    echo "=== Storage Status ==="
    kubectl get pv,pvc -n "$NAMESPACE"
    echo
    
    # Resource usage
    echo "=== Resource Usage ==="
    kubectl top pods -n "$NAMESPACE" 2>/dev/null || echo "Metrics not available"
    
    # Access information
    echo
    log "Access Information:"
    echo "API Endpoints:"
    kubectl get ingress -n "$NAMESPACE" -o jsonpath='{range .items[*]}{.spec.rules[*].host}{"\n"}{end}' | sort | uniq | while read host; do
        if [[ -n "$host" ]]; then
            echo "  https://$host"
        fi
    done
    
    echo
    echo "Port Forwards (for local access):"
    echo "  kubectl port-forward svc/grafana 3000:3000 -n $NAMESPACE"
    echo "  kubectl port-forward svc/prometheus 9090:9090 -n $NAMESPACE"
    echo "  kubectl port-forward svc/contextbuilder-core 8020:8020 -n $NAMESPACE"
}

# Cleanup deployment
cleanup() {
    log "Cleaning up ContextBuilderAgent deployment..."
    
    read -p "Are you sure you want to delete the entire ContextBuilderAgent deployment? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Delete resources in reverse order
        kubectl delete -f "$K8S_DIR/ingress/" --ignore-not-found=true
        kubectl delete -f "$K8S_DIR/deployments/" --ignore-not-found=true
        kubectl delete -f "$K8S_DIR/services/" --ignore-not-found=true
        kubectl delete -f "$K8S_DIR/configmaps/" --ignore-not-found=true
        kubectl delete -f "$K8S_DIR/secrets/" --ignore-not-found=true
        kubectl delete -f "$K8S_DIR/storage/" --ignore-not-found=true
        kubectl delete namespace "$NAMESPACE" --ignore-not-found=true
        
        success "Cleanup completed"
    else
        log "Cleanup cancelled"
    fi
}

# Main deployment function
main() {
    local action="${1:-deploy}"
    
    case "$action" in
        "deploy")
            log "Starting ContextBuilderAgent 2.0 Kubernetes Deployment"
            check_prerequisites
            create_namespace
            deploy_storage
            deploy_configs
            deploy_databases
            deploy_contextbuilder
            deploy_monitoring
            deploy_ingress
            verify_deployment
            show_status
            success "Deployment completed successfully!"
            ;;
        "status")
            show_status
            ;;
        "verify")
            verify_deployment
            ;;
        "scale")
            scale_deployment "${2:-all}" "${3:-1}"
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|*)
            echo "UltraMCP ContextBuilderAgent 2.0 - Kubernetes Deployment"
            echo
            echo "Usage: $0 [command] [options]"
            echo
            echo "Commands:"
            echo "  deploy              Complete deployment (default)"
            echo "  status              Show deployment status"
            echo "  verify              Verify deployment health"
            echo "  scale [component] [replicas]  Scale components"
            echo "  cleanup             Delete entire deployment"
            echo "  help                Show this help message"
            echo
            echo "Scale components:"
            echo "  core                ContextBuilder Core"
            echo "  prompt              Prompt Assembler"
            echo "  observatory         Context Observatory"
            echo "  monitoring          Monitoring stack"
            echo "  all                 All services (default)"
            echo
            echo "Examples:"
            echo "  $0 deploy           Deploy complete platform"
            echo "  $0 scale core 5     Scale core service to 5 replicas"
            echo "  $0 scale all 3      Scale all services to 3 replicas"
            echo "  $0 status           Show current status"
            echo "  $0 cleanup          Remove deployment"
            ;;
    esac
}

# Run main function
main "$@"