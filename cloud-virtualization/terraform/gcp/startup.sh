#!/bin/bash
# UltraMCP GCP Instance Startup Script
# Auto-configure UltraMCP services on Google Cloud Platform instances

set -euo pipefail

# Configuration from Terraform
SUPABASE_URL="${supabase_url}"
SUPABASE_KEY="${supabase_key}"
ENVIRONMENT="${environment}"
NODE_ROLE="${node_role}"
DOCKER_COMPOSE_URL="${docker_compose_url}"
PROJECT_ID="${project_id}"

# System variables
HOSTNAME=$(hostname)
INSTANCE_ID=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/id" -H "Metadata-Flavor: Google")
ZONE=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/zone" -H "Metadata-Flavor: Google" | cut -d/ -f4)
REGION=$(echo $ZONE | cut -d- -f1-2)
EXTERNAL_IP=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip" -H "Metadata-Flavor: Google" 2>/dev/null || echo "none")
INTERNAL_IP=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/ip" -H "Metadata-Flavor: Google")

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a /var/log/ultramcp-startup.log
}

log "Starting UltraMCP GCP instance setup for $HOSTNAME (ID: $INSTANCE_ID)"
log "Zone: $ZONE, Region: $REGION, Internal IP: $INTERNAL_IP"

# Update system packages
log "Updating system packages..."
apt-get update -y
apt-get upgrade -y

# Install essential packages
log "Installing essential packages..."
apt-get install -y \
    curl \
    wget \
    git \
    htop \
    vim \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    jq \
    python3 \
    python3-pip \
    nodejs \
    npm

# Install Docker
log "Installing Docker..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start and enable Docker
systemctl start docker
systemctl enable docker

# Add ubuntu user to docker group
usermod -aG docker ubuntu

# Install Docker Compose (standalone)
log "Installing Docker Compose..."
DOCKER_COMPOSE_VERSION="2.24.0"
curl -L "https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# Install Google Cloud SDK
log "Installing Google Cloud SDK..."
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
apt-get update -y
apt-get install -y google-cloud-sdk

# Install monitoring agent
log "Installing monitoring agents..."
curl -sSO https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh
bash add-google-cloud-ops-agent-repo.sh --also-install

# Configure Google Cloud Ops Agent
cat > /etc/google-cloud-ops-agent/config.yaml << 'EOF'
logging:
  receivers:
    ultramcp_logs:
      type: files
      include_paths:
        - /var/log/ultramcp-*.log
        - /opt/ultramcp/logs/*.log
      exclude_paths:
        - /var/log/ultramcp-startup.log
  service:
    pipelines:
      default_pipeline:
        receivers: [ultramcp_logs]

metrics:
  receivers:
    ultramcp_metrics:
      type: prometheus
      config:
        scrape_configs:
          - job_name: 'ultramcp-services'
            scrape_interval: 30s
            static_configs:
              - targets: ['localhost:3000', 'localhost:8001', 'localhost:8002']
  service:
    pipelines:
      default_pipeline:
        receivers: [ultramcp_metrics]
EOF

# Restart ops agent
systemctl restart google-cloud-ops-agent

# Create UltraMCP directory structure
log "Setting up UltraMCP directory structure..."
mkdir -p /opt/ultramcp/{config,data,logs,backups}
chown -R ubuntu:ubuntu /opt/ultramcp

# Download UltraMCP configuration
log "Downloading UltraMCP configuration..."
cd /opt/ultramcp

# Download docker-compose file
wget -O docker-compose.yml "$DOCKER_COMPOSE_URL"

# Create environment file
cat > .env << EOF
# UltraMCP GCP Configuration
ENVIRONMENT=$ENVIRONMENT
NODE_ROLE=$NODE_ROLE
INSTANCE_ID=$INSTANCE_ID
ZONE=$ZONE
REGION=$REGION
INTERNAL_IP=$INTERNAL_IP
EXTERNAL_IP=$EXTERNAL_IP

# Supabase Configuration
SUPABASE_URL=$SUPABASE_URL
SUPABASE_ANON_KEY=$SUPABASE_KEY
SUPABASE_SERVICE_ROLE_KEY=$SUPABASE_KEY

# GCP Configuration
PROJECT_ID=$PROJECT_ID
GCP_REGION=$REGION
GCP_ZONE=$ZONE

# Database Configuration
POSTGRES_URL=postgresql://postgres:ultramcp_password@postgres:5432/ultramcp
REDIS_URL=redis://redis:6379

# UltraMCP Services Configuration
CHAIN_OF_DEBATE_PORT=8001
ASTERISK_SECURITY_PORT=8002
BLOCKOLI_INTELLIGENCE_PORT=8003
VOICE_SYSTEM_PORT=8004
DEEPCLAUDE_ENGINE_PORT=8005
CONTROL_TOWER_PORT=8006
MEMORY_SERVICE_PORT=8007
SAM_MCP_PORT=8008
BACKEND_API_PORT=3000
WEBUI_PORT=3001

# Monitoring
ENABLE_MONITORING=true
LOG_LEVEL=info
METRICS_ENABLED=true

# Security
SECURITY_SCAN_ENABLED=true
COMPLIANCE_CHECKS=true

# Performance
AUTO_SCALING_ENABLED=true
RESOURCE_LIMITS_ENABLED=true
EOF

# Set permissions
chown ubuntu:ubuntu .env
chmod 600 .env

# Download UltraMCP source code
log "Downloading UltraMCP source code..."
git clone https://github.com/your-org/ultramcp.git source
chown -R ubuntu:ubuntu source

# Install Python dependencies
log "Installing Python dependencies..."
pip3 install supabase python-dotenv requests psutil

# Create health check script
log "Creating health check script..."
cat > /opt/ultramcp/health-check.py << 'EOF'
#!/usr/bin/env python3
import requests
import json
import time
import os
from supabase import create_client
from datetime import datetime

def check_services():
    services = {
        'backend-api': 'http://localhost:3000/health',
        'webui': 'http://localhost:3001/health',
        'chain-of-debate': 'http://localhost:8001/health',
        'asterisk-security': 'http://localhost:8002/health',
        'blockoli-intelligence': 'http://localhost:8003/health',
        'voice-system': 'http://localhost:8004/health',
        'deepclaude-engine': 'http://localhost:8005/health',
        'control-tower': 'http://localhost:8006/health',
        'memory-service': 'http://localhost:8007/health',
        'sam-mcp': 'http://localhost:8008/health'
    }
    
    results = {}
    for service, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            results[service] = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_time': response.elapsed.total_seconds(),
                'status_code': response.status_code
            }
        except Exception as e:
            results[service] = {
                'status': 'error',
                'error': str(e)
            }
    
    return results

def report_to_supabase(health_data):
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        instance_id = os.getenv('INSTANCE_ID')
        
        if not all([supabase_url, supabase_key, instance_id]):
            return False
            
        supabase = create_client(supabase_url, supabase_key)
        
        # Update instance status
        result = supabase.table('cloud_instances').update({
            'status': 'running' if all(s['status'] == 'healthy' for s in health_data.values()) else 'degraded',
            'metadata': {
                'health_check': health_data,
                'last_check': datetime.utcnow().isoformat(),
                'zone': os.getenv('ZONE'),
                'region': os.getenv('REGION')
            },
            'updated_at': datetime.utcnow().isoformat()
        }).eq('instance_id', instance_id).execute()
        
        return True
    except Exception as e:
        print(f"Error reporting to Supabase: {e}")
        return False

if __name__ == '__main__':
    health_data = check_services()
    print(json.dumps(health_data, indent=2))
    
    # Report to Supabase
    report_to_supabase(health_data)
    
    # Log to file
    with open('/var/log/ultramcp-health.log', 'a') as f:
        f.write(f"{datetime.utcnow().isoformat()} {json.dumps(health_data)}\n")
EOF

chmod +x /opt/ultramcp/health-check.py

# Create systemd service for health checks
log "Creating health check service..."
cat > /etc/systemd/system/ultramcp-health.service << 'EOF'
[Unit]
Description=UltraMCP Health Check Service
After=docker.service

[Service]
Type=oneshot
User=ubuntu
WorkingDirectory=/opt/ultramcp
Environment=PYTHONPATH=/opt/ultramcp
EnvironmentFile=/opt/ultramcp/.env
ExecStart=/opt/ultramcp/health-check.py
StandardOutput=journal
StandardError=journal
EOF

cat > /etc/systemd/system/ultramcp-health.timer << 'EOF'
[Unit]
Description=Run UltraMCP health check every 2 minutes
Requires=ultramcp-health.service

[Timer]
OnBootSec=300
OnUnitActiveSec=120
Unit=ultramcp-health.service

[Install]
WantedBy=timers.target
EOF

# Create UltraMCP startup service
log "Creating UltraMCP startup service..."
cat > /etc/systemd/system/ultramcp.service << 'EOF'
[Unit]
Description=UltraMCP Services
After=docker.service
Requires=docker.service

[Service]
Type=forking
Restart=always
RestartSec=10
User=ubuntu
WorkingDirectory=/opt/ultramcp
EnvironmentFile=/opt/ultramcp/.env
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=300
TimeoutStopSec=120

[Install]
WantedBy=multi-user.target
EOF

# Enable and start services
systemctl daemon-reload
systemctl enable ultramcp.service
systemctl enable ultramcp-health.timer

# Register instance with Supabase
log "Registering instance with Supabase..."
python3 << EOF
import requests
import json
import os

try:
    supabase_url = "$SUPABASE_URL"
    supabase_key = "$SUPABASE_KEY"
    
    # Register instance
    instance_data = {
        "name": "$HOSTNAME",
        "type": "vm",
        "provider": "gcp",
        "region": "$REGION",
        "instance_id": "$INSTANCE_ID",
        "status": "initializing",
        "specs": {
            "cpu": 2,
            "memory": 7680,
            "disk": 50
        },
        "metadata": {
            "zone": "$ZONE",
            "internal_ip": "$INTERNAL_IP",
            "external_ip": "$EXTERNAL_IP",
            "machine_type": "e2-standard-2",
            "project_id": "$PROJECT_ID",
            "startup_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
        }
    }
    
    response = requests.post(
        f"{supabase_url}/rest/v1/cloud_instances",
        headers={
            "apikey": supabase_key,
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        },
        json=instance_data
    )
    
    if response.status_code in [200, 201]:
        print("Successfully registered with Supabase")
    else:
        print(f"Failed to register with Supabase: {response.status_code} - {response.text}")
        
except Exception as e:
    print(f"Error registering with Supabase: {e}")
EOF

# Start UltraMCP services
log "Starting UltraMCP services..."
cd /opt/ultramcp
systemctl start ultramcp.service

# Wait for services to start
sleep 30

# Start health monitoring
systemctl start ultramcp-health.timer

# Configure logrotate for UltraMCP logs
log "Configuring log rotation..."
cat > /etc/logrotate.d/ultramcp << 'EOF'
/var/log/ultramcp-*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 ubuntu ubuntu
    postrotate
        systemctl reload google-cloud-ops-agent
    endscript
}

/opt/ultramcp/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 ubuntu ubuntu
}
EOF

# Create performance monitoring script
log "Setting up performance monitoring..."
cat > /opt/ultramcp/monitor-performance.py << 'EOF'
#!/usr/bin/env python3
import psutil
import json
import time
import os
from datetime import datetime
from supabase import create_client

def collect_metrics():
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    network = psutil.net_io_counters()
    
    return {
        'timestamp': datetime.utcnow().isoformat(),
        'cpu_usage': cpu_percent,
        'memory_usage': memory.percent,
        'disk_usage': (disk.used / disk.total) * 100,
        'network_in': network.bytes_recv,
        'network_out': network.bytes_sent,
        'memory_available': memory.available,
        'disk_free': disk.free,
        'load_average': os.getloadavg()[0]
    }

def send_metrics_to_supabase(metrics):
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        instance_id = os.getenv('INSTANCE_ID')
        
        if not all([supabase_url, supabase_key, instance_id]):
            return False
            
        supabase = create_client(supabase_url, supabase_key)
        
        # Send metrics
        result = supabase.table('resource_metrics').insert({
            'instance_id': instance_id,
            'cpu_usage': metrics['cpu_usage'],
            'memory_usage': metrics['memory_usage'],
            'disk_usage': metrics['disk_usage'],
            'network_in': metrics['network_in'],
            'network_out': metrics['network_out'],
            'timestamp': metrics['timestamp']
        }).execute()
        
        return True
    except Exception as e:
        print(f"Error sending metrics: {e}")
        return False

if __name__ == '__main__':
    metrics = collect_metrics()
    print(json.dumps(metrics, indent=2))
    send_metrics_to_supabase(metrics)
EOF

chmod +x /opt/ultramcp/monitor-performance.py

# Create performance monitoring timer
cat > /etc/systemd/system/ultramcp-metrics.service << 'EOF'
[Unit]
Description=UltraMCP Performance Metrics Collection
After=ultramcp.service

[Service]
Type=oneshot
User=ubuntu
WorkingDirectory=/opt/ultramcp
Environment=PYTHONPATH=/opt/ultramcp
EnvironmentFile=/opt/ultramcp/.env
ExecStart=/opt/ultramcp/monitor-performance.py
StandardOutput=journal
StandardError=journal
EOF

cat > /etc/systemd/system/ultramcp-metrics.timer << 'EOF'
[Unit]
Description=Collect UltraMCP metrics every 5 minutes
Requires=ultramcp-metrics.service

[Timer]
OnBootSec=600
OnUnitActiveSec=300
Unit=ultramcp-metrics.service

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable ultramcp-metrics.timer
systemctl start ultramcp-metrics.timer

# Configure firewall (using ufw for simplicity)
log "Configuring firewall..."
ufw --force enable
ufw default deny incoming
ufw default allow outgoing

# Allow SSH
ufw allow 22/tcp

# Allow UltraMCP services
ufw allow 3000:3001/tcp  # WebUI and API
ufw allow 8001:8008/tcp  # UltraMCP services

# Allow HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Final status check
log "Performing final status check..."
sleep 10
systemctl status ultramcp.service --no-pager
systemctl status ultramcp-health.timer --no-pager
systemctl status ultramcp-metrics.timer --no-pager

# Update instance status to running
python3 << EOF
import requests
import json

try:
    supabase_url = "$SUPABASE_URL"
    supabase_key = "$SUPABASE_KEY"
    instance_id = "$INSTANCE_ID"
    
    response = requests.patch(
        f"{supabase_url}/rest/v1/cloud_instances?instance_id=eq.{instance_id}",
        headers={
            "apikey": supabase_key,
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        },
        json={
            "status": "running",
            "metadata": {
                "startup_completed": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
                "services_started": True,
                "health_monitoring": True,
                "metrics_collection": True
            }
        }
    )
    
    if response.status_code in [200, 204]:
        print("Successfully updated instance status to running")
    else:
        print(f"Failed to update status: {response.status_code}")
        
except Exception as e:
    print(f"Error updating status: {e}")
EOF

log "UltraMCP GCP instance setup completed successfully!"
log "Instance $HOSTNAME is ready for service"
log "Health monitoring and metrics collection are active"
log "All UltraMCP services should be accessible within 5 minutes"

# Create a completion marker
touch /opt/ultramcp/startup-complete
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > /opt/ultramcp/startup-timestamp

log "Startup script execution finished at $(date)"