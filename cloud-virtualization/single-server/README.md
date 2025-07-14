# UltraMCP Single Server Testing Deployment

Test the complete UltraMCP cloud virtualization platform on a single server before scaling to multi-cloud infrastructure.

## 🎯 Overview

This single-server deployment provides:
- **Complete UltraMCP Stack**: All 9 services + infrastructure
- **Production-like Environment**: Docker containers with proper networking
- **Monitoring & Observability**: Prometheus, Grafana, Traefik dashboard
- **Domain-based Routing**: Local domains for each service
- **Comprehensive Testing**: Automated test suite for validation
- **Easy Management**: Simple commands for deployment and maintenance

## 🖥️ System Requirements

### Minimum Requirements
- **OS**: Ubuntu 20.04+ or Debian 11+
- **CPU**: 4 cores
- **RAM**: 8GB
- **Disk**: 50GB available space
- **Network**: Internet connection for downloads

### Recommended Requirements
- **CPU**: 8+ cores
- **RAM**: 16GB+
- **Disk**: 100GB+ SSD
- **Network**: High-speed internet

## 🚀 Quick Start

### 1. One-Command Installation
```bash
# Download and run the installer
curl -fsSL https://raw.githubusercontent.com/your-org/ultramcp/main/cloud-virtualization/single-server/deploy-single-server.sh -o deploy-single-server.sh
chmod +x deploy-single-server.sh

# Full installation (installs everything but doesn't deploy yet)
./deploy-single-server.sh full
```

### 2. Configure Supabase (Required)
```bash
# Edit the environment file
sudo nano /opt/ultramcp/.env

# Update these lines with your Supabase credentials:
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
```

### 3. Deploy Services
```bash
# After logging out/in and configuring Supabase
./deploy-single-server.sh deploy

# Or use the management command
ultramcp start
```

### 4. Run Tests
```bash
# Download and run the test suite
curl -fsSL https://raw.githubusercontent.com/your-org/ultramcp/main/cloud-virtualization/single-server/test-deployment.sh -o test-deployment.sh
chmod +x test-deployment.sh

# Run comprehensive tests
./test-deployment.sh all

# Or run quick health check
./test-deployment.sh quick
```

## 📋 Step-by-Step Installation

### Step 1: System Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install git (if not already installed)
sudo apt install -y git

# Clone the repository (if needed)
git clone https://github.com/your-org/ultramcp.git
cd ultramcp/cloud-virtualization/single-server
```

### Step 2: Install Dependencies
```bash
# Option A: Full installation
./deploy-single-server.sh install

# Option B: Manual installation
sudo apt install -y curl wget git vim htop jq python3 python3-pip nodejs npm

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER

# Install LXD (for future sandbox testing)
sudo snap install lxd
sudo usermod -a -G lxd $USER

# Log out and back in for group membership
```

### Step 3: Setup Configuration
```bash
# Create directory structure and configurations
./deploy-single-server.sh setup

# The script creates:
# - /opt/ultramcp/docker-compose.yml
# - /opt/ultramcp/.env
# - /opt/ultramcp/config/
# - /opt/ultramcp/manage.sh
```

### Step 4: Configure Supabase
```bash
# Edit environment file
sudo nano /opt/ultramcp/.env

# Required configuration:
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here

# Optional API keys:
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=claude-your-key-here
```

### Step 5: Deploy and Test
```bash
# Deploy all services
./deploy-single-server.sh deploy

# Wait for services to start (2-3 minutes)
sleep 180

# Run comprehensive tests
./test-deployment.sh all

# Check status
ultramcp status
ultramcp health
```

## 🛠️ Management Commands

### Basic Operations
```bash
# Start all services
ultramcp start

# Stop all services
ultramcp stop

# Restart all services
ultramcp restart

# Check service status
ultramcp status

# Health check
ultramcp health

# Show all service URLs
ultramcp urls
```

### Monitoring and Logs
```bash
# View all logs
ultramcp logs

# View specific service logs
ultramcp logs chain-of-debate
ultramcp logs postgres
ultramcp logs traefik

# Follow logs in real-time
docker-compose -f /opt/ultramcp/docker-compose.yml logs -f
```

### Updates and Maintenance
```bash
# Update all services
ultramcp update

# Update specific service
ultramcp update webui

# Create backup
ultramcp backup

# View resource usage
docker stats
```

## 🌐 Service URLs

After deployment, access services via these URLs:

### Main Interfaces
- **WebUI**: http://ultramcp.local
- **API Gateway**: http://api.ultramcp.local

### UltraMCP Services
- **Chain-of-Debate**: http://cod.ultramcp.local
- **Security Scanner**: http://security.ultramcp.local
- **Code Intelligence**: http://blockoli.ultramcp.local
- **Voice System**: http://voice.ultramcp.local
- **DeepClaude Engine**: http://deepclaude.ultramcp.local
- **Control Tower**: http://control.ultramcp.local
- **Claude Memory**: http://memory.ultramcp.local
- **Sam MCP**: http://sam.ultramcp.local

### Monitoring & Administration
- **Grafana**: http://grafana.ultramcp.local (admin/ultramcp2024)
- **Prometheus**: http://prometheus.ultramcp.local
- **Traefik Dashboard**: http://traefik.ultramcp.local

> **Note**: The deployment script automatically adds these domains to your `/etc/hosts` file.

## 🧪 Testing Suite

### Comprehensive Test Categories

#### Infrastructure Tests
```bash
./test-deployment.sh infrastructure
```
- Docker container health
- Database connectivity (PostgreSQL, Redis, Qdrant)
- Network configuration
- Storage volumes

#### Service Tests
```bash
./test-deployment.sh services
```
- All 9 UltraMCP services health
- HTTP endpoint responses
- JSON API health checks
- Container resource usage

#### Integration Tests
```bash
./test-deployment.sh integration
```
- Service-to-service communication
- Database schema validation
- API Gateway routing
- Cache functionality

#### Security Tests
```bash
./test-deployment.sh security
```
- Port exposure validation
- File permissions
- Container security
- Network isolation

#### Performance Tests
```bash
./test-deployment.sh performance
```
- Response time measurements
- Resource utilization
- Memory and CPU usage
- Concurrent request handling

### Quick Test Options
```bash
# Essential health check (fastest)
./test-deployment.sh quick

# Domain routing only
./test-deployment.sh domains

# Resource usage only
./test-deployment.sh resources

# Monitoring setup only
./test-deployment.sh monitoring
```

## 📊 Monitoring and Observability

### Grafana Dashboards
Access Grafana at http://grafana.ultramcp.local
- **Username**: admin
- **Password**: ultramcp2024

**Pre-configured dashboards**:
- UltraMCP Services Overview
- Infrastructure Metrics
- Container Resource Usage
- API Response Times

### Prometheus Metrics
Access Prometheus at http://prometheus.ultramcp.local

**Key metrics collected**:
- Service health and uptime
- HTTP request rates and latency
- Container CPU and memory usage
- Database connection pools
- Redis cache hit rates

### Log Management
```bash
# Centralized logging location
ls -la /opt/ultramcp/logs/

# Real-time log monitoring
tail -f /opt/ultramcp/logs/*.log

# Service-specific logs
docker logs ultramcp-cod
docker logs ultramcp-postgres
```

## 🔧 Troubleshooting

### Common Issues

#### Services Not Starting
```bash
# Check Docker daemon
sudo systemctl status docker

# Check available resources
free -h
df -h

# View service logs
ultramcp logs [service-name]

# Restart specific service
docker-compose -f /opt/ultramcp/docker-compose.yml restart [service]
```

#### Domain Resolution Issues
```bash
# Check hosts file
cat /etc/hosts | grep ultramcp

# Manually add entries if missing
echo "127.0.0.1 ultramcp.local" | sudo tee -a /etc/hosts
echo "127.0.0.1 api.ultramcp.local" | sudo tee -a /etc/hosts

# Test DNS resolution
nslookup ultramcp.local
```

#### Performance Issues
```bash
# Check resource usage
htop
docker stats

# Check disk space
df -h

# Check memory usage
free -h

# Optimize if needed
docker system prune -f
```

#### Database Connection Issues
```bash
# Check PostgreSQL
docker exec ultramcp-postgres pg_isready

# Check Redis
docker exec ultramcp-redis redis-cli ping

# Reset databases if needed
docker-compose -f /opt/ultramcp/docker-compose.yml down
docker volume prune -f
ultramcp start
```

### Debug Commands
```bash
# Container inspection
docker inspect ultramcp-[service]

# Network inspection
docker network ls
docker network inspect ultramcp_ultramcp

# Volume inspection
docker volume ls
docker volume inspect ultramcp_postgres-data

# System information
docker system info
docker system df
```

## 🔄 Backup and Recovery

### Automated Backup
```bash
# Create full backup
ultramcp backup

# Backup location
ls -la /opt/ultramcp/backups/
```

### Manual Backup
```bash
# Database backup
docker exec ultramcp-postgres pg_dump -U postgres ultramcp > backup.sql

# Volume backup
docker run --rm -v ultramcp_postgres-data:/source:ro -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /source .

# Configuration backup
cp -r /opt/ultramcp/config/ ~/ultramcp-config-backup/
cp /opt/ultramcp/.env ~/ultramcp-env-backup
```

### Recovery
```bash
# Stop services
ultramcp stop

# Restore volume
docker run --rm -v ultramcp_postgres-data:/target -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /target

# Restore database
docker exec -i ultramcp-postgres psql -U postgres ultramcp < backup.sql

# Start services
ultramcp start
```

## 🚀 Next Steps

### Scale to Multi-Cloud
Once single-server testing is complete:

1. **AWS Deployment**
   ```bash
   cd ../terraform/aws
   terraform init
   terraform apply
   ```

2. **GCP Deployment**
   ```bash
   cd ../terraform/gcp
   terraform init
   terraform apply
   ```

3. **Docker Swarm Cluster**
   ```bash
   cd ../scripts
   ./deploy-swarm.sh init
   ```

### Development Workflow
```bash
# Use LXD sandboxes for development
cd ../sandbox
./lxd-manager.sh init
./lxd-manager.sh create chain-of-debate

# Test individual services
./lxd-manager.sh logs ultramcp-chain-of-debate-sandbox
```

### CI/CD Integration
```bash
# Add testing to CI pipeline
./test-deployment.sh all > test-results.txt

# Automated deployment verification
if ./test-deployment.sh quick; then
    echo "Deployment successful"
    exit 0
else
    echo "Deployment failed"
    exit 1
fi
```

## 📚 Additional Resources

### Documentation
- [UltraMCP Architecture Overview](../README.md)
- [Complete Deployment Guide](../DEPLOYMENT_GUIDE.md)
- [Multi-Cloud Infrastructure](../terraform/)
- [Container Orchestration](../docker-compose.swarm.yml)

### Support
- **Issues**: Create issues for bugs or feature requests
- **Discussions**: Join community discussions
- **Documentation**: Contribute to documentation improvements

---

## 🎉 Success Criteria

Your single-server deployment is successful when:

✅ All containers are running (`docker ps` shows 15+ containers)  
✅ All health checks pass (`./test-deployment.sh quick`)  
✅ All services respond (`ultramcp health`)  
✅ Domain routing works (can access http://ultramcp.local)  
✅ Monitoring is active (Grafana shows metrics)  
✅ No failed tests (`./test-deployment.sh all`)  

**Ready to scale to multi-cloud infrastructure!** 🚀