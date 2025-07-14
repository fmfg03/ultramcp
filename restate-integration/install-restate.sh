#!/bin/bash
# UltraMCP Restate Integration - Local Installation
# Install and configure Restate for durable agent orchestration

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESTATE_VERSION="1.0.1"
RESTATE_PORT="8080"
RESTATE_ADMIN_PORT="9070"
RESTATE_INGRESS_PORT="8081"

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

# Check system requirements
check_requirements() {
    log_info "Checking system requirements for Restate..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is required but not installed"
        exit 1
    fi
    
    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is required but not installed"
        exit 1
    fi
    
    # Check available ports
    local ports=("$RESTATE_PORT" "$RESTATE_ADMIN_PORT" "$RESTATE_INGRESS_PORT")
    for port in "${ports[@]}"; do
        if netstat -ln | grep ":$port " &> /dev/null; then
            log_warning "Port $port is already in use"
        fi
    done
    
    log_success "System requirements check completed"
}

# Create Restate directory structure
setup_directories() {
    log_info "Setting up Restate directory structure..."
    
    mkdir -p "$SCRIPT_DIR"/{config,data,logs,services,examples}
    mkdir -p "$SCRIPT_DIR"/data/{restate,postgres}
    mkdir -p "$SCRIPT_DIR"/services/{typescript,rust}
    
    log_success "Directory structure created"
}

# Create Restate Docker Compose configuration
create_docker_compose() {
    log_info "Creating Restate Docker Compose configuration..."
    
    cat > "$SCRIPT_DIR/docker-compose.yml" << EOF
version: '3.8'

services:
  # Restate Server
  restate:
    image: restatedev/restate:${RESTATE_VERSION}
    container_name: ultramcp-restate
    restart: unless-stopped
    ports:
      - "${RESTATE_PORT}:8080"           # Ingress endpoint
      - "${RESTATE_ADMIN_PORT}:9070"     # Admin API
      - "${RESTATE_INGRESS_PORT}:8081"   # Meta service
    environment:
      - RESTATE_ROCKSDB__PATH=/restate-data
      - RESTATE_SERVER__BIND_ADDRESS=0.0.0.0:8080
      - RESTATE_ADMIN__BIND_ADDRESS=0.0.0.0:9070
      - RESTATE_META__BIND_ADDRESS=0.0.0.0:8081
      - RUST_LOG=info
    volumes:
      - ./data/restate:/restate-data
      - ./logs:/var/log/restate
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9070/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    networks:
      - restate-network

  # PostgreSQL for additional persistence (optional)
  postgres:
    image: postgres:15-alpine
    container_name: ultramcp-restate-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_DB=restate
      - POSTGRES_USER=restate
      - POSTGRES_PASSWORD=restate_secure_password
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
      - ./config/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    ports:
      - "5433:5432"  # Different port to avoid conflicts
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U restate -d restate"]
      interval: 30s
      timeout: 10s
      retries: 5
    networks:
      - restate-network

  # Restate CLI for management
  restate-cli:
    image: restatedev/restate:${RESTATE_VERSION}
    container_name: ultramcp-restate-cli
    entrypoint: ["sleep", "infinity"]
    volumes:
      - ./services:/services
      - ./examples:/examples
    networks:
      - restate-network
    depends_on:
      - restate

  # Jaeger for distributed tracing (optional)
  jaeger:
    image: jaegertracing/all-in-one:1.50
    container_name: ultramcp-jaeger
    restart: unless-stopped
    ports:
      - "16686:16686"  # Jaeger UI
      - "14268:14268"  # Jaeger collector
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    networks:
      - restate-network

networks:
  restate-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.30.0.0/16

volumes:
  restate-data:
    driver: local
  postgres-data:
    driver: local
EOF

    log_success "Docker Compose configuration created"
}

# Create Restate configuration
create_restate_config() {
    log_info "Creating Restate configuration files..."
    
    # Restate server configuration
    cat > "$SCRIPT_DIR/config/restate.toml" << EOF
[server]
bind_address = "0.0.0.0:8080"

[admin]
bind_address = "0.0.0.0:9070"

[meta]
bind_address = "0.0.0.0:8081"

[rocksdb]
path = "/restate-data"

[tracing]
endpoint = "http://jaeger:14268/api/traces"
service_name = "ultramcp-restate"

[log]
format = "json"
level = "info"
EOF

    # PostgreSQL initialization
    cat > "$SCRIPT_DIR/config/init.sql" << EOF
-- UltraMCP Restate Database Schema
-- Additional tables for UltraMCP-specific metadata

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Agent execution history
CREATE TABLE agent_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id VARCHAR(255) NOT NULL,
    agent_name VARCHAR(100) NOT NULL,
    execution_status VARCHAR(50) NOT NULL,
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    duration_ms INTEGER
);

-- Workflow metadata
CREATE TABLE workflow_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id VARCHAR(255) UNIQUE NOT NULL,
    workflow_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_by VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Agent registry
CREATE TABLE agent_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_name VARCHAR(100) UNIQUE NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    endpoint_url VARCHAR(500) NOT NULL,
    health_check_url VARCHAR(500),
    capabilities JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    registered_at TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_agent_executions_workflow_id ON agent_executions(workflow_id);
CREATE INDEX idx_agent_executions_agent_name ON agent_executions(agent_name);
CREATE INDEX idx_workflow_metadata_status ON workflow_metadata(status);
CREATE INDEX idx_agent_registry_active ON agent_registry(is_active);

-- Insert initial UltraMCP agents
INSERT INTO agent_registry (agent_name, agent_type, endpoint_url, health_check_url, capabilities) VALUES
('chain-of-debate', 'orchestrator', 'http://ultramcp-cod:8001', 'http://ultramcp-cod:8001/health', '{"multi_llm": true, "debate": true}'),
('asterisk-security', 'scanner', 'http://ultramcp-security:8002', 'http://ultramcp-security:8002/health', '{"vulnerability_scan": true, "compliance": true}'),
('blockoli-intelligence', 'analyzer', 'http://ultramcp-blockoli:8003', 'http://ultramcp-blockoli:8003/health', '{"code_analysis": true, "patterns": true}'),
('voice-system', 'interface', 'http://ultramcp-voice:8004', 'http://ultramcp-voice:8004/health', '{"voice_processing": true, "transcription": true}'),
('deepclaude-engine', 'reasoning', 'http://ultramcp-deepclaude:8005', 'http://ultramcp-deepclaude:8005/health', '{"metacognitive": true, "analysis": true}'),
('control-tower', 'orchestrator', 'http://ultramcp-control:8006', 'http://ultramcp-control:8006/health', '{"coordination": true, "monitoring": true}'),
('claude-memory', 'memory', 'http://ultramcp-memory:8007', 'http://ultramcp-memory:8007/health', '{"semantic_search": true, "code_intelligence": true}'),
('sam-mcp', 'agent', 'http://ultramcp-sam:8008', 'http://ultramcp-sam:8008/health', '{"autonomous": true, "langgraph": true}');
EOF

    log_success "Configuration files created"
}

# Create management scripts
create_management_scripts() {
    log_info "Creating management scripts..."
    
    # Main management script
    cat > "$SCRIPT_DIR/manage-restate.sh" << 'EOF'
#!/bin/bash
# UltraMCP Restate Management Script

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"

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

case "${1:-help}" in
    "start")
        log_info "Starting Restate services..."
        docker-compose -f "$COMPOSE_FILE" up -d
        log_success "Restate services started"
        ;;
    "stop")
        log_info "Stopping Restate services..."
        docker-compose -f "$COMPOSE_FILE" down
        log_success "Restate services stopped"
        ;;
    "restart")
        log_info "Restarting Restate services..."
        docker-compose -f "$COMPOSE_FILE" down
        docker-compose -f "$COMPOSE_FILE" up -d
        log_success "Restate services restarted"
        ;;
    "status")
        docker-compose -f "$COMPOSE_FILE" ps
        ;;
    "logs")
        service="${2:-restate}"
        docker-compose -f "$COMPOSE_FILE" logs -f "$service"
        ;;
    "health")
        log_info "Checking Restate health..."
        
        # Check Restate server
        if curl -s -f http://localhost:9070/health >/dev/null; then
            log_success "✓ Restate server is healthy"
        else
            log_error "✗ Restate server is unhealthy"
        fi
        
        # Check PostgreSQL
        if docker exec ultramcp-restate-postgres pg_isready -U restate >/dev/null 2>&1; then
            log_success "✓ PostgreSQL is healthy"
        else
            log_error "✗ PostgreSQL is unhealthy"
        fi
        ;;
    "cli")
        log_info "Opening Restate CLI..."
        docker exec -it ultramcp-restate-cli bash
        ;;
    "register")
        service_url="${2:-}"
        if [[ -z "$service_url" ]]; then
            log_error "Service URL required. Usage: $0 register <service_url>"
            exit 1
        fi
        
        log_info "Registering service: $service_url"
        curl -X POST http://localhost:9070/deployments \
            -H "Content-Type: application/json" \
            -d "{\"uri\": \"$service_url\"}"
        log_success "Service registered"
        ;;
    "services")
        log_info "Listing registered services..."
        curl -s http://localhost:9070/deployments | jq '.'
        ;;
    "workflows")
        log_info "Listing active workflows..."
        curl -s http://localhost:9070/services | jq '.'
        ;;
    "cancel")
        workflow_id="${2:-}"
        if [[ -z "$workflow_id" ]]; then
            log_error "Workflow ID required. Usage: $0 cancel <workflow_id>"
            exit 1
        fi
        
        log_info "Cancelling workflow: $workflow_id"
        curl -X DELETE "http://localhost:9070/services/WorkflowService/instances/$workflow_id"
        log_success "Workflow cancelled"
        ;;
    "dashboard")
        log_info "Restate Dashboard URLs:"
        echo ""
        echo "🔧 Restate Admin API:    http://localhost:9070"
        echo "🌐 Restate Ingress:     http://localhost:8080"
        echo "📊 Jaeger Tracing:      http://localhost:16686"
        echo "🗄️ PostgreSQL:          localhost:5433 (restate/restate_secure_password)"
        echo ""
        echo "📝 API Examples:"
        echo "  List services:    curl http://localhost:9070/services"
        echo "  List deployments: curl http://localhost:9070/deployments"
        echo "  Health check:     curl http://localhost:9070/health"
        ;;
    "help"|*)
        echo "UltraMCP Restate Management"
        echo ""
        echo "Usage: $0 <command> [options]"
        echo ""
        echo "Commands:"
        echo "  start                    Start Restate services"
        echo "  stop                     Stop Restate services"
        echo "  restart                  Restart Restate services"
        echo "  status                   Show service status"
        echo "  logs [service]           Show logs"
        echo "  health                   Check service health"
        echo "  cli                      Open Restate CLI"
        echo "  register <url>           Register a service"
        echo "  services                 List registered services"
        echo "  workflows                List active workflows"
        echo "  cancel <workflow_id>     Cancel a workflow"
        echo "  dashboard                Show dashboard URLs"
        echo "  help                     Show this help"
        ;;
esac
EOF

    chmod +x "$SCRIPT_DIR/manage-restate.sh"
    
    # Create symlink for global access
    sudo ln -sf "$SCRIPT_DIR/manage-restate.sh" /usr/local/bin/ultramcp-restate
    
    log_success "Management scripts created"
}

# Create example UltraMCP Restate service
create_example_service() {
    log_info "Creating example UltraMCP Restate service..."
    
    # TypeScript example
    mkdir -p "$SCRIPT_DIR/examples/typescript"
    
    cat > "$SCRIPT_DIR/examples/typescript/package.json" << EOF
{
  "name": "ultramcp-restate-examples",
  "version": "1.0.0",
  "description": "UltraMCP Restate Integration Examples",
  "main": "index.js",
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "ts-node src/index.ts"
  },
  "dependencies": {
    "@restatedev/restate-sdk": "^1.0.1",
    "axios": "^1.6.0",
    "uuid": "^9.0.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/uuid": "^9.0.0",
    "typescript": "^5.0.0",
    "ts-node": "^10.9.0"
  }
}
EOF

    mkdir -p "$SCRIPT_DIR/examples/typescript/src"
    
    cat > "$SCRIPT_DIR/examples/typescript/src/index.ts" << 'EOF'
import { endpoint, workflow, ctx } from "@restatedev/restate-sdk";
import axios from "axios";
import { v4 as uuidv4 } from "uuid";

// UltraMCP Agent Workflow Example
// Demonstrates durable orchestration of UltraMCP agents

interface AgentRequest {
  task: string;
  context: any;
  priority: "high" | "medium" | "low";
}

interface AgentResponse {
  success: boolean;
  result: any;
  error?: string;
  duration: number;
}

// UltraMCP Multi-Agent Workflow
const ultramcpWorkflow = workflow("ultramcp-workflow", async (ctx, input: {
  task: string;
  agents: string[];
  context: any;
}) => {
  const workflowId = uuidv4();
  const startTime = Date.now();

  ctx.console.log(`Starting UltraMCP workflow: ${workflowId}`);
  ctx.console.log(`Task: ${input.task}`);
  ctx.console.log(`Agents: ${input.agents.join(", ")}`);

  // Store workflow metadata
  await ctx.sideEffect(async () => {
    return {
      workflowId,
      task: input.task,
      agents: input.agents,
      startTime,
      status: "started"
    };
  });

  const results: { [agent: string]: AgentResponse } = {};

  // Sequential execution of agents
  for (const agentName of input.agents) {
    try {
      ctx.console.log(`Executing agent: ${agentName}`);
      
      // Call agent with durable execution
      const agentResult = await ctx.sideEffect(async () => {
        const agentStartTime = Date.now();
        
        try {
          const response = await axios.post(`http://ultramcp-${agentName}:8001/execute`, {
            task: input.task,
            context: input.context,
            workflowId
          }, {
            timeout: 30000
          });

          return {
            success: true,
            result: response.data,
            duration: Date.now() - agentStartTime
          };
        } catch (error: any) {
          return {
            success: false,
            result: null,
            error: error.message,
            duration: Date.now() - agentStartTime
          };
        }
      });

      results[agentName] = agentResult;

      // If agent fails and it's critical, decide whether to continue
      if (!agentResult.success && input.agents.length === 1) {
        throw new Error(`Critical agent ${agentName} failed: ${agentResult.error}`);
      }

      // Add delay between agents if needed
      if (input.agents.indexOf(agentName) < input.agents.length - 1) {
        await ctx.sleep(1000); // 1 second delay
      }

    } catch (error: any) {
      ctx.console.error(`Agent ${agentName} execution failed:`, error);
      results[agentName] = {
        success: false,
        result: null,
        error: error.message,
        duration: 0
      };
    }
  }

  // Final workflow result
  const finalResult = {
    workflowId,
    task: input.task,
    agents: input.agents,
    results,
    totalDuration: Date.now() - startTime,
    success: Object.values(results).some(r => r.success),
    completedAt: new Date().toISOString()
  };

  ctx.console.log(`Workflow ${workflowId} completed:`, finalResult);
  return finalResult;
});

// Chain of Debate specific workflow
const chainOfDebateWorkflow = workflow("chain-of-debate", async (ctx, input: {
  topic: string;
  participants: string[];
  rounds: number;
}) => {
  const debateId = uuidv4();
  ctx.console.log(`Starting Chain of Debate: ${debateId}`);

  const debateResults = [];

  for (let round = 1; round <= input.rounds; round++) {
    ctx.console.log(`Round ${round}/${input.rounds}`);

    // Parallel execution of participants in each round
    const roundPromises = input.participants.map(async (participant) => {
      return await ctx.sideEffect(async () => {
        const response = await axios.post(`http://ultramcp-cod:8001/debate`, {
          topic: input.topic,
          participant,
          round,
          debateId,
          previousRounds: debateResults
        });
        return response.data;
      });
    });

    // Wait for all participants to complete the round
    const roundResults = await Promise.all(roundPromises);
    debateResults.push({
      round,
      timestamp: new Date().toISOString(),
      results: roundResults
    });

    // Delay between rounds
    if (round < input.rounds) {
      await ctx.sleep(2000);
    }
  }

  // Synthesize final result
  const synthesis = await ctx.sideEffect(async () => {
    const response = await axios.post(`http://ultramcp-cod:8001/synthesize`, {
      topic: input.topic,
      debateResults,
      debateId
    });
    return response.data;
  });

  return {
    debateId,
    topic: input.topic,
    participants: input.participants,
    rounds: input.rounds,
    results: debateResults,
    synthesis,
    completedAt: new Date().toISOString()
  };
});

// Code Analysis workflow
const codeAnalysisWorkflow = workflow("code-analysis", async (ctx, input: {
  repository: string;
  branch: string;
  analysisType: "security" | "quality" | "patterns" | "all";
}) => {
  const analysisId = uuidv4();
  ctx.console.log(`Starting code analysis: ${analysisId}`);

  // Step 1: Clone and prepare repository
  const repoData = await ctx.sideEffect(async () => {
    const response = await axios.post(`http://ultramcp-blockoli:8003/clone`, {
      repository: input.repository,
      branch: input.branch,
      analysisId
    });
    return response.data;
  });

  if (!repoData.success) {
    throw new Error(`Failed to clone repository: ${repoData.error}`);
  }

  const analysisResults: any = {};

  // Step 2: Security analysis (if requested)
  if (input.analysisType === "security" || input.analysisType === "all") {
    ctx.console.log("Running security analysis...");
    analysisResults.security = await ctx.sideEffect(async () => {
      const response = await axios.post(`http://ultramcp-security:8002/analyze`, {
        repositoryPath: repoData.path,
        analysisId,
        type: "security"
      });
      return response.data;
    });
  }

  // Step 3: Code quality analysis
  if (input.analysisType === "quality" || input.analysisType === "all") {
    ctx.console.log("Running quality analysis...");
    analysisResults.quality = await ctx.sideEffect(async () => {
      const response = await axios.post(`http://ultramcp-blockoli:8003/analyze`, {
        repositoryPath: repoData.path,
        analysisId,
        type: "quality"
      });
      return response.data;
    });
  }

  // Step 4: Pattern analysis
  if (input.analysisType === "patterns" || input.analysisType === "all") {
    ctx.console.log("Running pattern analysis...");
    analysisResults.patterns = await ctx.sideEffect(async () => {
      const response = await axios.post(`http://ultramcp-blockoli:8003/analyze`, {
        repositoryPath: repoData.path,
        analysisId,
        type: "patterns"
      });
      return response.data;
    });
  }

  // Step 5: Generate comprehensive report
  const report = await ctx.sideEffect(async () => {
    const response = await axios.post(`http://ultramcp-control:8006/generate-report`, {
      analysisId,
      repository: input.repository,
      branch: input.branch,
      results: analysisResults
    });
    return response.data;
  });

  return {
    analysisId,
    repository: input.repository,
    branch: input.branch,
    analysisType: input.analysisType,
    results: analysisResults,
    report,
    completedAt: new Date().toISOString()
  };
});

// Create the Restate endpoint
endpoint()
  .bind(ultramcpWorkflow)
  .bind(chainOfDebateWorkflow)
  .bind(codeAnalysisWorkflow)
  .listen(9080);

console.log("UltraMCP Restate service listening on port 9080");
EOF

    cat > "$SCRIPT_DIR/examples/typescript/tsconfig.json" << EOF
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
EOF

    cat > "$SCRIPT_DIR/examples/typescript/Dockerfile" << EOF
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build TypeScript
RUN npm run build

# Expose port
EXPOSE 9080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:9080/health || exit 1

# Start the service
CMD ["npm", "start"]
EOF

    log_success "Example service created"
}

# Start Restate services
start_restate() {
    log_info "Starting Restate services..."
    
    cd "$SCRIPT_DIR"
    docker-compose up -d
    
    log_info "Waiting for services to start..."
    sleep 30
    
    # Health check
    if curl -s -f http://localhost:9070/health >/dev/null; then
        log_success "Restate is running and healthy!"
        
        echo ""
        echo "🎉 Restate Installation Complete!"
        echo ""
        echo "📊 Dashboard URLs:"
        echo "  Restate Admin API:    http://localhost:9070"
        echo "  Restate Ingress:      http://localhost:8080"
        echo "  Jaeger Tracing:       http://localhost:16686"
        echo ""
        echo "🛠️ Management Commands:"
        echo "  ultramcp-restate status    # Check service status"
        echo "  ultramcp-restate health    # Health check"
        echo "  ultramcp-restate dashboard # Show all URLs"
        echo ""
        echo "📝 Next Steps:"
        echo "1. Register UltraMCP services: ultramcp-restate register <service_url>"
        echo "2. Deploy example workflows: cd examples/typescript && npm install && npm run dev"
        echo "3. Integrate with existing UltraMCP services"
        
    else
        log_error "Restate failed to start properly"
        echo ""
        echo "Debugging steps:"
        echo "1. Check logs: ultramcp-restate logs"
        echo "2. Check port availability: netstat -ln | grep 8080"
        echo "3. Check Docker: docker ps"
    fi
}

# Main installation function
main() {
    local action="${1:-install}"
    
    case "$action" in
        "install")
            log_info "Starting UltraMCP Restate installation..."
            check_requirements
            setup_directories
            create_docker_compose
            create_restate_config
            create_management_scripts
            create_example_service
            start_restate
            ;;
        "uninstall")
            log_warning "Uninstalling Restate..."
            cd "$SCRIPT_DIR"
            docker-compose down -v
            sudo rm -f /usr/local/bin/ultramcp-restate
            log_success "Restate uninstalled"
            ;;
        "help"|*)
            echo "UltraMCP Restate Installation"
            echo ""
            echo "Usage: $0 <action>"
            echo ""
            echo "Actions:"
            echo "  install     Install and start Restate"
            echo "  uninstall   Remove Restate completely"
            echo "  help        Show this help"
            ;;
    esac
}

# Run main function
main "$@"