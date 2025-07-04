# 🚀 UltraMCP Supreme Stack - Complete Deployment Guide

## Overview

This guide covers deploying the complete UltraMCP Supreme Stack with all 7 integrated microservices. The system supports development, staging, and production deployments with zero loose components.

## 🎯 Deployment Options

### 1. Development Deployment (Recommended for local development)
- Full integration with hot reload
- All 7 services with development optimizations
- Local model support with API fallback

### 2. Hybrid Production Deployment (Recommended for production)
- Optimized Docker stack with all services
- Production-ready configuration
- Complete monitoring and health checks

### 3. Enterprise Deployment
- Kubernetes orchestration
- Advanced monitoring and observability
- High availability and auto-scaling

## 📋 Prerequisites

### System Requirements

**Minimum Requirements:**
- CPU: 4 cores (8 cores recommended)
- RAM: 8GB (16GB recommended for local models)
- Storage: 50GB (100GB recommended)
- Network: Broadband internet connection

**Software Requirements:**
```bash
# Required
Docker 20.10+
Docker Compose 2.0+
Node.js 18+
Python 3.8+
Git 2.0+

# Optional (for local models)
Ollama latest version
NVIDIA drivers (for GPU acceleration)

# Optional (for production)
Kubernetes 1.24+
Helm 3.0+
Nginx or Traefik
```

### Port Requirements

**Default Ports:**
- `3001` - Backend API Gateway
- `8001` - Chain-of-Debate Service
- `8002` - Asterisk Security Service  
- `8003` - Blockoli Code Intelligence
- `8004` - Voice System HTTP
- `8005` - Voice System WebSocket
- `8006` - DeepClaude Reasoning Engine
- `8007` - Control Tower HTTP
- `8008` - Control Tower WebSocket
- `5432` - PostgreSQL Database
- `6379` - Redis Cache
- `11434` - Ollama (local models)

## 🔧 Environment Setup

### 1. Clone and Configure

```bash
# Clone repository
git clone https://github.com/fmfg03/ultramcp.git
cd ultramcp

# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

### 2. Environment Configuration

#### Required Configuration
```bash
# Database Configuration
DATABASE_URL=postgresql://ultramcp:your-secure-password@ultramcp-postgres:5432/ultramcp
POSTGRES_PASSWORD=your-secure-password
REDIS_URL=redis://:redis_secure@ultramcp-redis:6379/0
REDIS_PASSWORD=your-redis-password

# Service URLs (auto-configured in Docker)
COD_SERVICE_URL=http://ultramcp-cod-service:8001
ASTERISK_SERVICE_URL=http://ultramcp-asterisk-mcp:8002
BLOCKOLI_SERVICE_URL=http://ultramcp-blockoli:8003
VOICE_SERVICE_URL=http://ultramcp-voice:8004
DEEPCLAUDE_SERVICE_URL=http://ultramcp-deepclaude:8006
CONTROL_TOWER_URL=http://ultramcp-control-tower:8007
```

#### Optional API Keys (for enhanced features)
```bash
# AI API Keys (optional - local models work without these)
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=claude-your-key
GOOGLE_API_KEY=your-google-key

# External Integrations
GITHUB_TOKEN=ghp-your-github-token
NOTION_TOKEN=secret_your-notion-token
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# Monitoring (optional)
LANGWATCH_API_KEY=lw-your-langwatch-key
SENTRY_DSN=your-sentry-dsn
```

#### Service-Specific Configuration
```bash
# Security Service
ASTERISK_SECURITY_LEVEL=strict
ASTERISK_COMPLIANCE_FRAMEWORKS=SOC2,HIPAA,GDPR
ASTERISK_SCAN_MAX_DEPTH=10

# Code Intelligence
BLOCKOLI_SEMANTIC_SEARCH_ENABLED=true
BLOCKOLI_MAX_PROJECT_SIZE=10GB
BLOCKOLI_INDEX_PATH=/app/code_indexes

# Voice System
VOICE_AI_ENABLED=true
VOICE_MAX_SESSION_DURATION=3600
VOICE_AUDIO_FORMAT=wav
VOICE_SAMPLE_RATE=16000

# DeepClaude Engine
DEEPCLAUDE_REASONING_DEPTH=deep
DEEPCLAUDE_METACOGNITIVE_MODE=enabled
DEEPCLAUDE_MAX_REASONING_TIME=300

# Control Tower
CONTROL_TOWER_WEBSOCKET_ENABLED=true
CONTROL_TOWER_MAX_ORCHESTRATIONS=10
CONTROL_TOWER_HEALTH_CHECK_INTERVAL=30
```

## 🐳 Docker Deployment

### Development Deployment

```bash
# Quick setup and verification
make setup

# Verify integration before starting
make verify-integration

# Start development environment
make docker-dev

# Check all services are running
make status

# Test integration
make health-check
```

### Production Deployment

```bash
# Start optimized hybrid production stack
make docker-hybrid

# Verify complete integration
make verify-integration

# Check system health
make health-check

# Test API Gateway routing
curl http://localhost:3001/api/health

# Test cross-service communication
make test-cross-services
```

### Manual Docker Compose

```bash
# Production deployment with all services
docker-compose -f docker-compose.hybrid.yml up -d

# Check all containers are running
docker ps

# View logs
docker-compose -f docker-compose.hybrid.yml logs -f

# Stop all services
docker-compose -f docker-compose.hybrid.yml down
```

## ☸️ Kubernetes Deployment

### Namespace Setup

```bash
# Create namespace
kubectl create namespace ultramcp

# Set default namespace
kubectl config set-context --current --namespace=ultramcp
```

### ConfigMap and Secrets

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ultramcp-config
  namespace: ultramcp
data:
  COD_SERVICE_URL: "http://cod-service:8001"
  ASTERISK_SERVICE_URL: "http://asterisk-service:8002"
  BLOCKOLI_SERVICE_URL: "http://blockoli-service:8003"
  VOICE_SERVICE_URL: "http://voice-service:8004"
  DEEPCLAUDE_SERVICE_URL: "http://deepclaude-service:8006"
  CONTROL_TOWER_URL: "http://control-tower:8007"
  
---
apiVersion: v1
kind: Secret
metadata:
  name: ultramcp-secrets
  namespace: ultramcp
type: Opaque
stringData:
  POSTGRES_PASSWORD: "your-secure-password"
  REDIS_PASSWORD: "your-redis-password"
  OPENAI_API_KEY: "sk-your-openai-key"
  ANTHROPIC_API_KEY: "claude-your-key"
```

### Database Deployment

```yaml
# k8s/postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: ultramcp
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          value: "ultramcp"
        - name: POSTGRES_USER
          value: "ultramcp"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: ultramcp-secrets
              key: POSTGRES_PASSWORD
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
        - name: init-script
          mountPath: /docker-entrypoint-initdb.d
      volumes:
      - name: init-script
        configMap:
          name: postgres-init
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 20Gi

---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: ultramcp
spec:
  ports:
  - port: 5432
  selector:
    app: postgres
```

### Service Deployments

```yaml
# k8s/cod-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cod-service
  namespace: ultramcp
spec:
  replicas: 2
  selector:
    matchLabels:
      app: cod-service
  template:
    metadata:
      labels:
        app: cod-service
    spec:
      containers:
      - name: cod-service
        image: ultramcp/cod-service:latest
        ports:
        - containerPort: 8001
        env:
        - name: COD_SERVICE_PORT
          value: "8001"
        - name: POSTGRES_URL
          value: "postgresql://ultramcp:$(POSTGRES_PASSWORD)@postgres:5432/ultramcp"
        - name: REDIS_URL
          value: "redis://:$(REDIS_PASSWORD)@redis:6379/0"
        envFrom:
        - configMapRef:
            name: ultramcp-config
        - secretRef:
            name: ultramcp-secrets
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: cod-service
  namespace: ultramcp
spec:
  ports:
  - port: 8001
    targetPort: 8001
  selector:
    app: cod-service
```

### Complete Kubernetes Deployment

```bash
# Apply all configurations
kubectl apply -f k8s/

# Check deployment status
kubectl get pods
kubectl get services

# View logs
kubectl logs -f deployment/cod-service
kubectl logs -f deployment/asterisk-service

# Port forward for testing
kubectl port-forward service/api-gateway 3001:3001

# Scale services
kubectl scale deployment cod-service --replicas=3
kubectl scale deployment blockoli-service --replicas=2
```

## 🔐 SSL/TLS Configuration

### Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/ultramcp
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/certificate.pem;
    ssl_certificate_key /path/to/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

    # API Gateway
    location /api/ {
        proxy_pass http://localhost:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://localhost:8008;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Traefik Configuration (Kubernetes)

```yaml
# k8s/traefik-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ultramcp-ingress
  namespace: ultramcp
  annotations:
    traefik.ingress.kubernetes.io/router.tls: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - yourdomain.com
    secretName: ultramcp-tls
  rules:
  - host: yourdomain.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-gateway
            port:
              number: 3001
      - path: /ws
        pathType: Prefix
        backend:
          service:
            name: control-tower
            port:
              number: 8008
```

## 📊 Monitoring and Observability

### Prometheus Configuration

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ultramcp-services'
    static_configs:
      - targets: 
        - 'localhost:3001'  # API Gateway
        - 'localhost:8001'  # CoD Service
        - 'localhost:8002'  # Security Service
        - 'localhost:8003'  # Blockoli Service
        - 'localhost:8004'  # Voice Service
        - 'localhost:8006'  # DeepClaude Service
        - 'localhost:8007'  # Control Tower

  - job_name: 'infrastructure'
    static_configs:
      - targets:
        - 'localhost:5432'  # PostgreSQL
        - 'localhost:6379'  # Redis
```

### Grafana Dashboards

```json
{
  "dashboard": {
    "title": "UltraMCP Supreme Stack",
    "panels": [
      {
        "title": "Service Health Overview",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job='ultramcp-services'}",
            "legendFormat": "{{instance}}"
          }
        ]
      },
      {
        "title": "API Gateway Response Times",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Cross-Service Communication",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{job='ultramcp-services'}[5m])",
            "legendFormat": "{{service}}"
          }
        ]
      }
    ]
  }
}
```

### Health Check Automation

```bash
#!/bin/bash
# monitoring/health-check.sh

# Function to check service health
check_service_health() {
    local service_name=$1
    local service_url=$2
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$service_url/health")
    
    if [ "$response" = "200" ]; then
        echo "✅ $service_name: Healthy"
        return 0
    else
        echo "❌ $service_name: Unhealthy (HTTP $response)"
        return 1
    fi
}

# Check all services
services=(
    "API Gateway:http://localhost:3001/api/health"
    "CoD Service:http://localhost:8001/health"
    "Security Service:http://localhost:8002/health"
    "Blockoli Service:http://localhost:8003/health"
    "Voice Service:http://localhost:8004/health"
    "DeepClaude Service:http://localhost:8006/health"
    "Control Tower:http://localhost:8007/health"
)

failed_services=0

for service in "${services[@]}"; do
    name=$(echo "$service" | cut -d: -f1)
    url=$(echo "$service" | cut -d: -f2-)
    
    if ! check_service_health "$name" "$url"; then
        ((failed_services++))
    fi
done

if [ $failed_services -eq 0 ]; then
    echo "🎉 All services healthy!"
    exit 0
else
    echo "⚠️  $failed_services services failed health check"
    exit 1
fi
```

## 🔄 Backup and Recovery

### Database Backup

```bash
#!/bin/bash
# backup/postgres-backup.sh

BACKUP_DIR="/backups/postgres"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/ultramcp_backup_$TIMESTAMP.sql"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Create database backup
docker exec ultramcp-postgres pg_dump -U ultramcp ultramcp > "$BACKUP_FILE"

# Compress backup
gzip "$BACKUP_FILE"

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete

echo "✅ Database backup completed: $BACKUP_FILE.gz"
```

### Service Data Backup

```bash
#!/bin/bash
# backup/service-data-backup.sh

BACKUP_DIR="/backups/services"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup service data directories
tar -czf "$BACKUP_DIR/data_backup_$TIMESTAMP.tar.gz" \
    data/ \
    logs/ \
    config/

# Backup Docker volumes
docker run --rm -v ultramcp_postgres_data:/source -v "$BACKUP_DIR":/backup alpine \
    tar -czf "/backup/postgres_volume_$TIMESTAMP.tar.gz" -C /source .

docker run --rm -v ultramcp_redis_data:/source -v "$BACKUP_DIR":/backup alpine \
    tar -czf "/backup/redis_volume_$TIMESTAMP.tar.gz" -C /source .

echo "✅ Service data backup completed"
```

### Disaster Recovery

```bash
#!/bin/bash
# recovery/disaster-recovery.sh

# Stop all services
make docker-down

# Restore database from backup
LATEST_DB_BACKUP=$(ls -t /backups/postgres/*.sql.gz | head -1)
gunzip -c "$LATEST_DB_BACKUP" | docker exec -i ultramcp-postgres psql -U ultramcp ultramcp

# Restore service data
LATEST_DATA_BACKUP=$(ls -t /backups/services/data_backup_*.tar.gz | head -1)
tar -xzf "$LATEST_DATA_BACKUP"

# Restore Docker volumes
LATEST_POSTGRES_VOLUME=$(ls -t /backups/services/postgres_volume_*.tar.gz | head -1)
docker run --rm -v ultramcp_postgres_data:/target -v /backups/services:/backup alpine \
    tar -xzf "/backup/$(basename $LATEST_POSTGRES_VOLUME)" -C /target

# Start services
make docker-hybrid

# Verify recovery
make verify-integration

echo "✅ Disaster recovery completed"
```

## 🚀 Production Optimization

### Performance Tuning

```bash
# docker-compose.prod.yml optimizations
version: '3.8'

services:
  ultramcp-postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_SHARED_BUFFERS: "256MB"
      POSTGRES_EFFECTIVE_CACHE_SIZE: "1GB"
      POSTGRES_MAX_CONNECTIONS: "200"
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  ultramcp-redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G

  ultramcp-cod-service:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 1G
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
```

### Load Balancing

```nginx
# nginx/load-balancer.conf
upstream cod_service {
    least_conn;
    server ultramcp-cod-service-1:8001 max_fails=3 fail_timeout=30s;
    server ultramcp-cod-service-2:8001 max_fails=3 fail_timeout=30s;
    server ultramcp-cod-service-3:8001 max_fails=3 fail_timeout=30s;
}

upstream blockoli_service {
    least_conn;
    server ultramcp-blockoli-1:8003 max_fails=3 fail_timeout=30s;
    server ultramcp-blockoli-2:8003 max_fails=3 fail_timeout=30s;
}

server {
    location /api/cod/ {
        proxy_pass http://cod_service;
    }
    
    location /api/blockoli/ {
        proxy_pass http://blockoli_service;
    }
}
```

## 📋 Deployment Checklist

### Pre-Deployment

- [ ] Environment configuration completed
- [ ] SSL certificates obtained and configured
- [ ] Database initialization scripts prepared
- [ ] Backup strategy implemented
- [ ] Monitoring tools configured
- [ ] Load testing completed
- [ ] Security scan passed
- [ ] Integration verification passed

### Deployment

- [ ] Services deployed in correct order
- [ ] Database schema applied
- [ ] Environment variables set
- [ ] Health checks passing
- [ ] API Gateway routing verified
- [ ] Cross-service communication tested
- [ ] WebSocket connections functional
- [ ] Monitoring dashboards accessible

### Post-Deployment

- [ ] All services responding correctly
- [ ] Integration verification passed
- [ ] Performance metrics within acceptable ranges
- [ ] Backup procedures verified
- [ ] Monitoring alerts configured
- [ ] Documentation updated
- [ ] Team notified of deployment completion

## 🚨 Troubleshooting

### Common Deployment Issues

**Service Won't Start**
```bash
# Check logs
docker logs ultramcp-service-name

# Check resource usage
docker stats

# Verify environment variables
docker exec ultramcp-service-name env
```

**Database Connection Issues**
```bash
# Test database connectivity
docker exec ultramcp-postgres psql -U ultramcp -d ultramcp -c "SELECT 1;"

# Check network connectivity
docker exec ultramcp-service-name ping ultramcp-postgres
```

**API Gateway Routing Issues**
```bash
# Test routing
curl -v http://localhost:3001/api/health

# Check proxy configuration
docker exec ultramcp-terminal cat /app/src/index.js | grep createProxyMiddleware
```

**Integration Verification Failures**
```bash
# Run detailed verification
make verify-integration

# Check specific integration points
make test-cross-services
make test-api-gateway
make websocket-status
```

## 📞 Support and Maintenance

### Regular Maintenance Tasks

```bash
# Weekly maintenance
make health-check
make verify-integration
make backup
make update-local-models

# Monthly maintenance
make security-audit
make performance-review
make log-rotation
make dependency-updates

# Quarterly maintenance
make disaster-recovery-test
make security-penetration-test
make capacity-planning-review
```

### Support Resources

- **Integration Verification**: `make verify-integration`
- **Health Monitoring**: `make health-check`
- **Log Analysis**: `make logs-search QUERY="error"`
- **Performance Metrics**: `make performance-metrics`
- **API Documentation**: [docs/api/README.md](api/README.md)
- **Claude Code Guide**: [CLAUDE.md](../CLAUDE.md)

---

For additional deployment scenarios and advanced configurations, consult the [Complete API Documentation](api/README.md) and [Integration Verification Guide](integration-verification.md).