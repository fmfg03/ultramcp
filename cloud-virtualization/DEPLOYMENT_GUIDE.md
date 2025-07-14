# UltraMCP Cloud Virtualization - Deployment Guide

Complete guide for deploying UltraMCP services across multiple cloud providers and virtualization technologies.

## 🎯 Quick Start

### Option 1: AWS Deployment
```bash
# Navigate to AWS Terraform directory
cd terraform/aws

# Initialize Terraform
terraform init

# Create terraform.tfvars
cat > terraform.tfvars << EOF
aws_region         = "us-east-1"
environment        = "production"
supabase_url       = "https://your-project.supabase.co"
supabase_anon_key  = "your-anon-key"
public_key         = "ssh-rsa YOUR_PUBLIC_KEY"
min_size           = 2
max_size           = 10
desired_capacity   = 3
EOF

# Deploy infrastructure
terraform plan
terraform apply
```

### Option 2: Google Cloud Deployment
```bash
# Navigate to GCP Terraform directory
cd terraform/gcp

# Initialize Terraform
terraform init

# Create terraform.tfvars
cat > terraform.tfvars << EOF
project_id         = "your-gcp-project"
region             = "europe-west1"
environment        = "production"
supabase_url       = "https://your-project.supabase.co"
supabase_anon_key  = "your-anon-key"
domain_name        = "ultramcp.yourdomain.com"
enable_ssl         = true
min_size           = 2
max_size           = 10
EOF

# Deploy infrastructure
terraform plan
terraform apply
```

### Option 3: Docker Swarm Deployment
```bash
# Initialize Docker Swarm (if not already done)
docker swarm init

# Deploy UltraMCP stack
cd scripts
./deploy-swarm.sh init
```

### Option 4: Local Sandbox Development
```bash
# Initialize LXD environment
cd sandbox
./lxd-manager.sh init

# Create sandbox for specific service
./lxd-manager.sh create chain-of-debate 4 4GiB 20GiB
```

## 🏗️ Architecture Overview

### Multi-Provider Cloud Infrastructure

```
┌─────────────────────────────────────────────────────────────────┐
│                    UltraMCP Cloud Architecture                   │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │    AWS      │  │    GCP      │  │   Azure     │  │  Local  │ │
│  │             │  │             │  │             │  │         │ │
│  │ • Auto      │  │ • Global    │  │ • Hybrid    │  │ • LXD   │ │
│  │   Scaling   │  │   LB        │  │   Cloud     │  │ • Docker│ │
│  │ • ALB       │  │ • Cloud     │  │ • VM Scale  │  │ • Swarm │ │
│  │ • CloudWatch│  │   SQL       │  │   Sets      │  │         │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────────────┘
              │                │                │                │
              └────────────────┼────────────────┼────────────────┘
                               │                │
                    ┌─────────────────────────────────┐
                    │      Supabase Control Plane    │
                    │  • PostgreSQL Database         │
                    │  • Edge Functions               │
                    │  • Real-time Subscriptions     │
                    │  • Authentication & Storage    │
                    └─────────────────────────────────┘
```

### Service Distribution Strategy

#### Production Deployment
```yaml
Primary Region (AWS us-east-1):
  - Chain-of-Debate Service (3 replicas)
  - Control Tower (2 replicas)
  - Backend API Gateway (3 replicas)
  - WebUI (2 replicas)

Secondary Region (GCP europe-west1):
  - Claude Memory Service (2 replicas)
  - Blockoli Intelligence (2 replicas)
  - VoyageAI Integration (1 replica)

Edge Locations (Azure/Local):
  - Voice System (2 replicas)
  - Security Scanner (2 replicas)
  - Development Sandboxes
```

## 📋 Prerequisites

### Required Software
- **Terraform** >= 1.0
- **Docker** >= 20.10
- **Docker Compose** >= 2.0
- **LXD** >= 5.0 (for local sandboxes)
- **Cloud Provider CLI Tools**
  - AWS CLI v2
  - Google Cloud SDK
  - Azure CLI

### Required Accounts & Credentials
1. **Supabase Project**
   - Project URL
   - Anonymous Key
   - Service Role Key

2. **Cloud Provider Accounts**
   - AWS Account with appropriate IAM permissions
   - Google Cloud Project with billing enabled
   - Azure Subscription (optional)

3. **API Keys** (optional but recommended)
   - OpenAI API Key
   - Anthropic Claude API Key

## 🚀 Detailed Deployment Instructions

### AWS Deployment

#### 1. Prepare AWS Environment
```bash
# Configure AWS CLI
aws configure

# Verify permissions
aws sts get-caller-identity

# Create S3 bucket for Terraform state (optional)
aws s3 mb s3://ultramcp-terraform-state-$(date +%s)
```

#### 2. Deploy Infrastructure
```bash
cd terraform/aws

# Initialize Terraform with remote state (optional)
cat > backend.tf << EOF
terraform {
  backend "s3" {
    bucket = "ultramcp-terraform-state-YOUR_SUFFIX"
    key    = "aws/terraform.tfstate"
    region = "us-east-1"
  }
}
EOF

terraform init

# Create variables file
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# Plan and apply
terraform plan -out=plan.out
terraform apply plan.out
```

#### 3. Verify Deployment
```bash
# Get load balancer DNS name
terraform output load_balancer_dns

# Check instance health
aws elbv2 describe-target-health --target-group-arn $(terraform output -raw target_group_arn)

# View CloudWatch logs
aws logs describe-log-groups --log-group-name-prefix ultramcp
```

### Google Cloud Deployment

#### 1. Prepare GCP Environment
```bash
# Install Google Cloud SDK and authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable compute.googleapis.com
gcloud services enable container.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable logging.googleapis.com
gcloud services enable monitoring.googleapis.com
```

#### 2. Deploy Infrastructure
```bash
cd terraform/gcp

# Initialize Terraform
terraform init

# Create service account for Terraform
gcloud iam service-accounts create terraform-ultramcp
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:terraform-ultramcp@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/editor"

# Download service account key
gcloud iam service-accounts keys create terraform-key.json \
  --iam-account=terraform-ultramcp@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="terraform-key.json"

# Create variables file
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# Deploy
terraform plan -out=plan.out
terraform apply plan.out
```

#### 3. Verify Deployment
```bash
# Get load balancer IP
terraform output load_balancer_ip

# Check instance group health
gcloud compute instance-groups managed describe ultramcp-igm-production --zone=europe-west1-b

# View logs
gcloud logging read "resource.type=gce_instance AND labels.project_id=YOUR_PROJECT_ID"
```

### Docker Swarm Deployment

#### 1. Initialize Swarm Cluster
```bash
# On manager node
docker swarm init --advertise-addr YOUR_MANAGER_IP

# Add worker nodes (run on each worker)
docker swarm join --token SWMTKN-1-... YOUR_MANAGER_IP:2377

# Label nodes for service placement
docker node update --label-add postgres=true MANAGER_NODE
docker node update --label-add redis=true WORKER_NODE_1
docker node update --label-add monitoring=true WORKER_NODE_2
```

#### 2. Deploy UltraMCP Stack
```bash
cd scripts

# Set environment variables
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="your-anon-key"
export WEBUI_DOMAIN="ultramcp.yourdomain.com"
export API_DOMAIN="api.ultramcp.yourdomain.com"

# Deploy complete stack
./deploy-swarm.sh init
```

#### 3. Monitor Deployment
```bash
# Check service status
docker stack services ultramcp

# View service logs
docker service logs -f ultramcp_chain-of-debate

# Scale services
./deploy-swarm.sh scale chain-of-debate 5

# Update services
./deploy-swarm.sh update webui ultramcp/webui:v2.0
```

### Local Sandbox Development

#### 1. Install and Configure LXD
```bash
# Install LXD (Ubuntu/Debian)
sudo snap install lxd

# Initialize LXD
sudo lxd init

# Add user to lxd group
sudo usermod -a -G lxd $USER
newgrp lxd
```

#### 2. Initialize UltraMCP Environment
```bash
cd sandbox

# Initialize LXD environment for UltraMCP
./lxd-manager.sh init
```

#### 3. Create Service Sandboxes
```bash
# Create Chain-of-Debate sandbox
./lxd-manager.sh create chain-of-debate 4 4GiB 20GiB

# Create Security scanner sandbox
./lxd-manager.sh create asterisk-security 2 2GiB 15GiB

# Create Code intelligence sandbox
./lxd-manager.sh create blockoli-intelligence 4 6GiB 25GiB

# Create Memory service sandbox
./lxd-manager.sh create claude-memory 4 6GiB 30GiB
```

#### 4. Manage Sandboxes
```bash
# List all sandboxes
./lxd-manager.sh list

# Get detailed info
./lxd-manager.sh info ultramcp-chain-of-debate-sandbox

# Execute commands
./lxd-manager.sh exec ultramcp-chain-of-debate-sandbox "docker ps"

# View logs
./lxd-manager.sh logs ultramcp-chain-of-debate-sandbox

# Stop/start sandbox
./lxd-manager.sh stop ultramcp-chain-of-debate-sandbox
./lxd-manager.sh start ultramcp-chain-of-debate-sandbox
```

## 🔧 Configuration

### Environment Variables

#### Core Configuration
```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Database Configuration
POSTGRES_URL=postgresql://user:password@host:5432/database
REDIS_URL=redis://username:password@host:6379

# API Keys (optional)
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=claude-your-anthropic-key
```

#### Service-Specific Configuration
```bash
# Chain-of-Debate Service
DEBATE_TIMEOUT=300
MAX_PARTICIPANTS=5
LOCAL_LLM_ENABLED=true
CHAIN_OF_DEBATE_PORT=8001

# Security Service
SECURITY_SCAN_ENABLED=true
VULNERABILITY_DB_UPDATE=daily
COMPLIANCE_FRAMEWORKS=SOC2,HIPAA,GDPR
ASTERISK_SECURITY_PORT=8002

# Code Intelligence
CODE_ANALYSIS_ENABLED=true
PATTERN_RECOGNITION=true
SEMANTIC_SEARCH=true
BLOCKOLI_INTELLIGENCE_PORT=8003

# Memory Service
MEMORY_PERSISTENCE=true
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_DIMENSIONS=384
MEMORY_SERVICE_PORT=8007
```

### SSL/TLS Configuration

#### Traefik with Let's Encrypt (Docker Swarm)
```bash
# Set domain names
export WEBUI_DOMAIN="ultramcp.yourdomain.com"
export API_DOMAIN="api.ultramcp.yourdomain.com"
export ACME_EMAIL="admin@yourdomain.com"

# Deploy with SSL
./deploy-swarm.sh init
```

#### Google Cloud SSL (GCP)
```bash
# Enable SSL in terraform.tfvars
enable_ssl = true
domain_name = "ultramcp.yourdomain.com"

# Apply changes
terraform apply
```

#### AWS Certificate Manager (AWS)
```bash
# Request certificate
aws acm request-certificate \
    --domain-name ultramcp.yourdomain.com \
    --domain-name "*.ultramcp.yourdomain.com" \
    --validation-method DNS

# Update ALB listener to use HTTPS
# (This requires manual configuration or additional Terraform resources)
```

## 📊 Monitoring and Observability

### Built-in Monitoring

#### CloudWatch (AWS)
- **Metrics**: CPU, Memory, Disk, Network usage
- **Logs**: Application logs, system logs
- **Alarms**: Auto-scaling triggers, health alerts
- **Dashboard**: Custom CloudWatch dashboard

#### Google Cloud Operations (GCP)
- **Cloud Monitoring**: Resource and application metrics
- **Cloud Logging**: Centralized log management
- **Cloud Trace**: Application performance insights
- **Error Reporting**: Real-time error tracking

#### Prometheus + Grafana (Docker Swarm)
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **AlertManager**: Alert routing and management
- **Service Discovery**: Automatic target discovery

### Health Checks and Alerts

#### Service Health Endpoints
```bash
# Check individual services
curl http://localhost:8001/health  # Chain-of-Debate
curl http://localhost:8002/health  # Security
curl http://localhost:8003/health  # Code Intelligence
curl http://localhost:8007/health  # Memory Service
curl http://localhost:3000/health  # API Gateway
```

#### Aggregate Health Status
```bash
# Docker Swarm
curl http://grafana.ultramcp.local/api/health

# AWS
aws elbv2 describe-target-health --target-group-arn $(terraform output -raw target_group_arn)

# GCP
gcloud compute instance-groups managed describe ultramcp-igm-production --zone=YOUR_ZONE
```

## 🔐 Security Configuration

### Network Security

#### AWS Security Groups
```hcl
# Web traffic
ingress {
  from_port   = 80
  to_port     = 80
  protocol    = "tcp"
  cidr_blocks = ["0.0.0.0/0"]
}

ingress {
  from_port   = 443
  to_port     = 443
  protocol    = "tcp"
  cidr_blocks = ["0.0.0.0/0"]
}

# UltraMCP services (internal only)
ingress {
  from_port       = 8001
  to_port         = 8013
  protocol        = "tcp"
  security_groups = [aws_security_group.ultramcp_web_sg.id]
}
```

#### GCP Firewall Rules
```bash
# Create firewall rules
gcloud compute firewall-rules create ultramcp-web \
    --allow tcp:80,tcp:443,tcp:3000,tcp:3001 \
    --source-ranges 0.0.0.0/0 \
    --target-tags ultramcp-web

gcloud compute firewall-rules create ultramcp-internal \
    --allow tcp:8001-8013 \
    --source-tags ultramcp-web \
    --target-tags ultramcp-app
```

### Access Control

#### IAM Roles and Policies
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "cloudwatch:PutMetricData"
      ],
      "Resource": "*"
    }
  ]
}
```

#### Service Account Configuration
```bash
# GCP Service Account
gcloud iam service-accounts create ultramcp-service \
    --display-name="UltraMCP Service Account"

gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:ultramcp-service@PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/logging.logWriter"
```

## 🔄 Backup and Disaster Recovery

### Database Backup

#### Automated Backups
```bash
# AWS RDS automated backups (configured in Terraform)
backup_retention_period = 7
backup_window          = "03:00-04:00"
maintenance_window     = "sun:04:00-sun:05:00"

# GCP Cloud SQL automated backups
backup_configuration {
  enabled                        = true
  start_time                     = "03:00"
  point_in_time_recovery_enabled = true
  backup_retention_settings {
    retained_backups = 30
  }
}
```

#### Manual Backup Scripts
```bash
# Create backup script
cat > backup-database.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/ultramcp/backups"

# PostgreSQL backup
pg_dump $POSTGRES_URL > $BACKUP_DIR/ultramcp_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/ultramcp_$DATE.sql

# Upload to cloud storage
aws s3 cp $BACKUP_DIR/ultramcp_$DATE.sql.gz s3://ultramcp-backups/
EOF

chmod +x backup-database.sh
```

### Application Data Backup

#### Docker Volumes
```bash
# Create volume backup
docker run --rm \
  -v ultramcp_postgres-data:/source:ro \
  -v /backup:/backup \
  alpine tar czf /backup/postgres_data_$(date +%Y%m%d).tar.gz -C /source .

# Restore volume
docker run --rm \
  -v ultramcp_postgres-data:/target \
  -v /backup:/backup \
  alpine tar xzf /backup/postgres_data_YYYYMMDD.tar.gz -C /target
```

#### LXD Container Snapshots
```bash
# Create snapshot
lxc snapshot ultramcp-chain-of-debate-sandbox backup-$(date +%Y%m%d)

# List snapshots
lxc info ultramcp-chain-of-debate-sandbox

# Restore from snapshot
lxc restore ultramcp-chain-of-debate-sandbox backup-YYYYMMDD
```

### Multi-Region Failover

#### DNS-based Failover
```bash
# Route 53 health checks (AWS)
resource "aws_route53_health_check" "primary" {
  fqdn              = aws_lb.ultramcp_alb.dns_name
  port              = 443
  type              = "HTTPS"
  resource_path     = "/health"
  failure_threshold = "3"
  request_interval  = "30"
}

# Failover routing
resource "aws_route53_record" "primary" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "ultramcp.yourdomain.com"
  type    = "A"
  
  set_identifier = "primary"
  failover_routing_policy {
    type = "PRIMARY"
  }
  
  health_check_id = aws_route53_health_check.primary.id
  
  alias {
    name                   = aws_lb.ultramcp_alb.dns_name
    zone_id                = aws_lb.ultramcp_alb.zone_id
    evaluate_target_health = true
  }
}
```

## 🧪 Testing and Validation

### Infrastructure Testing

#### Terraform Validation
```bash
# Validate configuration
terraform validate

# Format code
terraform fmt

# Security scanning
tflint
checkov -f main.tf
```

#### Deployment Testing
```bash
# Health check script
cat > test-deployment.sh << 'EOF'
#!/bin/bash
set -e

ENDPOINTS=(
  "http://localhost:3000/health"
  "http://localhost:3001/health"
  "http://localhost:8001/health"
  "http://localhost:8002/health"
  "http://localhost:8003/health"
  "http://localhost:8007/health"
)

for endpoint in "${ENDPOINTS[@]}"; do
  echo "Testing $endpoint..."
  curl -f -s "$endpoint" || exit 1
  echo "✓ $endpoint is healthy"
done

echo "All services are healthy!"
EOF

chmod +x test-deployment.sh
./test-deployment.sh
```

### Load Testing

#### Apache Bench
```bash
# Test API Gateway
ab -n 1000 -c 10 http://localhost:3000/health

# Test specific service
ab -n 500 -c 5 http://localhost:8001/health
```

#### Kubernetes Load Testing
```bash
# Deploy load testing pod
kubectl run load-test --image=busybox --rm -it --restart=Never -- \
  sh -c "while true; do wget -qO- http://ultramcp-api:3000/health; done"
```

## 🚨 Troubleshooting

### Common Issues

#### Service Not Starting
```bash
# Check service logs
docker service logs ultramcp_chain-of-debate

# Check container status
docker ps -a

# Inspect service configuration
docker service inspect ultramcp_chain-of-debate
```

#### Network Connectivity Issues
```bash
# Test internal connectivity
docker exec -it $(docker ps -q -f name=ultramcp_chain-of-debate) curl http://postgres:5432

# Check network configuration
docker network ls
docker network inspect ultramcp-overlay
```

#### Performance Issues
```bash
# Check resource usage
docker stats

# View system metrics
htop
iostat 1

# Check service health
curl http://localhost:3000/metrics
```

### Debug Commands

#### Container Debugging
```bash
# Access container shell
docker exec -it ultramcp_chain-of-debate bash

# View environment variables
docker exec ultramcp_chain-of-debate env

# Check mounted volumes
docker exec ultramcp_chain-of-debate df -h
```

#### LXD Container Debugging
```bash
# Access container
lxc exec ultramcp-chain-of-debate-sandbox bash

# View container logs
lxc info ultramcp-chain-of-debate-sandbox --show-log

# Check resource usage
lxc exec ultramcp-chain-of-debate-sandbox -- htop
```

## 📚 Additional Resources

### Documentation Links
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Terraform Google Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Docker Swarm Documentation](https://docs.docker.com/engine/swarm/)
- [LXD Documentation](https://linuxcontainers.org/lxd/docs/master/)
- [Supabase Documentation](https://supabase.com/docs)

### Community and Support
- **GitHub Repository**: https://github.com/your-org/ultramcp
- **Documentation**: https://docs.ultramcp.com
- **Discord Community**: https://discord.gg/ultramcp
- **Support Email**: support@ultramcp.com

### Training and Certification
- **UltraMCP Cloud Certification**: Learn advanced deployment strategies
- **DevOps Best Practices**: Infrastructure as Code and CI/CD
- **Security Compliance**: SOC2, HIPAA, and GDPR implementation

---

## 🎉 Conclusion

This deployment guide provides comprehensive instructions for deploying UltraMCP across multiple cloud providers and virtualization technologies. Choose the deployment option that best fits your requirements:

- **AWS**: For enterprise-scale, high-availability deployments
- **GCP**: For global scale with advanced ML/AI capabilities  
- **Docker Swarm**: For on-premises or hybrid deployments
- **Local Sandboxes**: For development and testing

Each deployment option includes monitoring, security, backup, and disaster recovery configurations to ensure production-ready operations.

For additional support or custom deployment scenarios, please refer to the community resources or contact our support team.