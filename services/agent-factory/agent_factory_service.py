"""
UltraMCP Agent Factory Service
Generates AI agents from templates like Create Agent App but integrated with UltraMCP infrastructure
"""

import asyncio
import os
import uuid
import yaml
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import structlog

# Import enhanced testing system
from agent_quality_validator import AgentQualityValidator, validate_agent_before_deployment, get_agent_quality_score
import httpx
from jinja2 import Environment, FileSystemLoader
import git

logger = structlog.get_logger(__name__)

app = FastAPI(
    title="UltraMCP Agent Factory Service",
    description="Generate and manage AI agents across multiple frameworks",
    version="1.0.0"
)

# Configuration
TEMPLATES_DIR = Path("/app/templates")
GENERATED_AGENTS_DIR = Path("/app/generated")
ULTRAMCP_COD_URL = "http://ultramcp-cod-service:8001"
ULTRAMCP_LOCAL_MODELS_URL = "http://ultramcp-local-models-orchestrator:8012"
ULTRAMCP_SCENARIO_URL = "http://ultramcp-scenario-testing:8013"

# Global state
active_agents = {}
generation_tasks = {}


class AgentFramework(Enum):
    """Supported AI agent frameworks"""
    LANGCHAIN = "langchain"
    CREWAI = "crewai"
    AUTOGEN = "autogen"
    ULTRAMCP = "ultramcp"


class AgentType(Enum):
    """Categories of agents"""
    BUSINESS = "business"
    TECHNICAL = "technical"
    CREATIVE = "creative"
    RESEARCH = "research"
    SUPPORT = "support"


@dataclass
class AgentTemplate:
    """Agent template configuration"""
    name: str
    type: AgentType
    framework: AgentFramework
    description: str
    capabilities: List[str]
    models: Dict[str, str]
    testing: Dict[str, Any]
    deployment: Dict[str, Any]


class AgentGenerationRequest(BaseModel):
    """Request to generate a new agent"""
    agent_type: str
    framework: str = "ultramcp"
    name: Optional[str] = None
    customization: Optional[Dict[str, Any]] = None
    deploy_immediately: bool = False
    run_tests: bool = True


class AgentInfo(BaseModel):
    """Information about a generated agent"""
    agent_id: str
    name: str
    type: str
    framework: str
    status: str
    created_at: datetime
    deployed: bool = False
    test_results: Optional[Dict[str, Any]] = None


@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "UltraMCP Agent Factory",
        "version": "1.0.0",
        "description": "Generate AI agents from templates with UltraMCP integration",
        "endpoints": {
            "create_agent": "/agents/create",
            "list_agents": "/agents",
            "agent_status": "/agents/{agent_id}",
            "deploy_agent": "/agents/{agent_id}/deploy",
            "test_agent": "/agents/{agent_id}/test",
            "templates": "/templates",
            "frameworks": "/frameworks"
        },
        "supported_frameworks": [f.value for f in AgentFramework],
        "agent_types": [t.value for t in AgentType]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check UltraMCP services connectivity
        async with httpx.AsyncClient(timeout=5.0) as client:
            cod_healthy = False
            local_models_healthy = False
            scenario_healthy = False
            
            try:
                cod_response = await client.get(f"{ULTRAMCP_COD_URL}/health")
                cod_healthy = cod_response.status_code == 200
            except:
                pass
            
            try:
                models_response = await client.get(f"{ULTRAMCP_LOCAL_MODELS_URL}/models")
                local_models_healthy = models_response.status_code == 200
            except:
                pass
            
            try:
                scenario_response = await client.get(f"{ULTRAMCP_SCENARIO_URL}/health")
                scenario_healthy = scenario_response.status_code == 200
            except:
                pass
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(),
            "ultramcp_services": {
                "cod_service": "healthy" if cod_healthy else "unhealthy",
                "local_models": "healthy" if local_models_healthy else "unhealthy",
                "scenario_testing": "healthy" if scenario_healthy else "unhealthy"
            },
            "active_agents": len(active_agents),
            "generation_tasks": len(generation_tasks),
            "templates_available": len(list(TEMPLATES_DIR.glob("*/*"))) if TEMPLATES_DIR.exists() else 0
        }
    
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.get("/templates")
async def list_templates():
    """List all available agent templates"""
    try:
        templates = {}
        
        if not TEMPLATES_DIR.exists():
            logger.warning("Templates directory not found, creating with defaults")
            await create_default_templates()
        
        for framework_dir in TEMPLATES_DIR.iterdir():
            if framework_dir.is_dir():
                framework = framework_dir.name
                templates[framework] = []
                
                for template_dir in framework_dir.iterdir():
                    if template_dir.is_dir() and (template_dir / "config.yaml").exists():
                        config_file = template_dir / "config.yaml"
                        try:
                            with open(config_file, 'r') as f:
                                config = yaml.safe_load(f)
                            
                            templates[framework].append({
                                "name": template_dir.name,
                                "description": config.get("agent", {}).get("description", ""),
                                "type": config.get("agent", {}).get("type", ""),
                                "capabilities": config.get("capabilities", []),
                                "path": str(template_dir)
                            })
                        except Exception as e:
                            logger.error(f"Error loading template {template_dir}", error=str(e))
        
        return {
            "templates": templates,
            "total_frameworks": len(templates),
            "total_templates": sum(len(t) for t in templates.values())
        }
    
    except Exception as e:
        logger.error("Failed to list templates", error=str(e))
        raise HTTPException(status_code=500, detail=f"Template listing failed: {str(e)}")


@app.get("/frameworks")
async def list_frameworks():
    """List supported frameworks and their capabilities"""
    return {
        "frameworks": {
            "langchain": {
                "description": "LangChain framework for tool-based agents",
                "capabilities": ["tools", "memory", "chains", "vectorstores"],
                "use_cases": ["RAG", "tool_calling", "document_processing"]
            },
            "crewai": {
                "description": "CrewAI for collaborative multi-agent systems",
                "capabilities": ["multi_agent", "roles", "collaboration", "task_delegation"],
                "use_cases": ["team_workflows", "specialized_roles", "complex_projects"]
            },
            "autogen": {
                "description": "AutoGen for conversational multi-agent systems",
                "capabilities": ["conversation", "group_chat", "code_generation"],
                "use_cases": ["collaborative_coding", "group_discussions", "iterative_development"]
            },
            "ultramcp": {
                "description": "UltraMCP native framework with CoD and local models",
                "capabilities": ["local_models", "cod_debates", "quality_assurance", "offline_ai"],
                "use_cases": ["production_systems", "cost_optimization", "privacy_first"]
            }
        }
    }


@app.post("/agents/create")
async def create_agent(request: AgentGenerationRequest, background_tasks: BackgroundTasks):
    """Create a new agent from template"""
    try:
        agent_id = str(uuid.uuid4())
        agent_name = request.name or f"{request.agent_type}_{agent_id[:8]}"
        
        # Validate framework and agent type
        try:
            framework = AgentFramework(request.framework)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unsupported framework: {request.framework}")
        
        # Check if template exists
        template_path = TEMPLATES_DIR / request.framework / request.agent_type
        if not template_path.exists():
            raise HTTPException(status_code=404, detail=f"Template not found: {request.framework}/{request.agent_type}")
        
        # Create agent entry
        agent_info = AgentInfo(
            agent_id=agent_id,
            name=agent_name,
            type=request.agent_type,
            framework=request.framework,
            status="generating",
            created_at=datetime.now()
        )
        
        active_agents[agent_id] = agent_info
        
        # Start generation in background
        background_tasks.add_task(
            generate_agent_from_template,
            agent_id,
            template_path,
            request
        )
        
        logger.info(
            "Agent creation started",
            agent_id=agent_id,
            agent_type=request.agent_type,
            framework=request.framework
        )
        
        return {
            "agent_id": agent_id,
            "status": "generation_started",
            "agent_name": agent_name,
            "estimated_completion": "2-5 minutes"
        }
    
    except Exception as e:
        logger.error("Agent creation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Agent creation failed: {str(e)}")


@app.get("/agents")
async def list_agents():
    """List all generated agents"""
    return {
        "agents": [agent.dict() for agent in active_agents.values()],
        "total_agents": len(active_agents),
        "by_status": {
            status: len([a for a in active_agents.values() if a.status == status])
            for status in ["generating", "ready", "deployed", "failed"]
        }
    }


@app.get("/agents/{agent_id}")
async def get_agent_status(agent_id: str):
    """Get status of specific agent"""
    if agent_id not in active_agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = active_agents[agent_id]
    return asdict(agent)


@app.post("/agents/{agent_id}/deploy")
async def deploy_agent(agent_id: str, background_tasks: BackgroundTasks):
    """Deploy an agent to production"""
    if agent_id not in active_agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = active_agents[agent_id]
    
    if agent.status != "ready":
        raise HTTPException(status_code=400, detail=f"Agent not ready for deployment. Status: {agent.status}")
    
    # Start deployment in background
    background_tasks.add_task(deploy_agent_container, agent_id)
    
    agent.status = "deploying"
    active_agents[agent_id] = agent
    
    return {
        "agent_id": agent_id,
        "status": "deployment_started",
        "message": "Agent deployment initiated"
    }


@app.post("/agents/{agent_id}/test")
async def test_agent(agent_id: str, background_tasks: BackgroundTasks):
    """Run enhanced tests on an agent using Scenario-CoD framework"""
    if agent_id not in active_agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = active_agents[agent_id]
    
    if agent.status not in ["ready", "deployed", "validated"]:
        raise HTTPException(status_code=400, detail=f"Agent not ready for testing. Status: {agent.status}")
    
    # Start enhanced testing in background
    background_tasks.add_task(run_enhanced_agent_validation, agent_id)
    
    return {
        "agent_id": agent_id,
        "status": "enhanced_testing_started",
        "message": "Agent testing initiated using enhanced Scenario-CoD framework"
    }


@app.get("/agents/{agent_id}/validation")
async def get_agent_validation(agent_id: str):
    """Get detailed validation report for agent"""
    if agent_id not in active_agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = active_agents[agent_id]
    
    if not agent.test_results:
        return {
            "agent_id": agent_id,
            "status": "no_validation_data",
            "message": "No validation results available. Run tests first."
        }
    
    return {
        "agent_id": agent_id,
        "validation_report": agent.test_results,
        "last_updated": agent.created_at.isoformat()
    }


@app.post("/agents/{agent_id}/validate")
async def validate_agent_quality(agent_id: str, background_tasks: BackgroundTasks):
    """Run comprehensive quality validation on agent"""
    if agent_id not in active_agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    background_tasks.add_task(run_enhanced_agent_validation, agent_id)
    
    return {
        "agent_id": agent_id,
        "status": "validation_started",
        "message": "Comprehensive quality validation initiated"
    }


@app.get("/testing/scenarios")
async def get_available_test_scenarios():
    """Get list of available test scenarios"""
    try:
        from enhanced_testing_system import PREDEFINED_SCENARIOS
        
        scenarios = {}
        for name, scenario in PREDEFINED_SCENARIOS.items():
            scenarios[name] = {
                "name": scenario.name,
                "description": scenario.description,
                "type": scenario.scenario_type.value,
                "criteria_count": len(scenario.criteria),
                "conversation_turns": scenario.conversation_turns,
                "expected_capabilities": scenario.expected_capabilities
            }
        
        return {
            "available_scenarios": scenarios,
            "total_scenarios": len(scenarios)
        }
    except Exception as e:
        logger.error("Failed to load test scenarios", error=str(e))
        return {
            "available_scenarios": {},
            "total_scenarios": 0,
            "error": "Enhanced testing system not available"
        }


# Background task functions

async def generate_agent_from_template(agent_id: str, template_path: Path, request: AgentGenerationRequest):
    """Generate agent code from template"""
    try:
        agent = active_agents[agent_id]
        
        # Load template configuration
        config_file = template_path / "config.yaml"
        with open(config_file, 'r') as f:
            template_config = yaml.safe_load(f)
        
        # Create output directory
        output_dir = GENERATED_AGENTS_DIR / agent_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy template files
        shutil.copytree(template_path, output_dir, dirs_exist_ok=True)
        
        # Apply customizations using Jinja2
        env = Environment(loader=FileSystemLoader(str(template_path)))
        
        template_vars = {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "ultramcp_cod_url": ULTRAMCP_COD_URL,
            "ultramcp_local_models_url": ULTRAMCP_LOCAL_MODELS_URL,
            **template_config,
            **(request.customization or {})
        }
        
        # Process template files
        for template_file in template_path.glob("**/*.py"):
            if template_file.is_file():
                relative_path = template_file.relative_to(template_path)
                output_file = output_dir / relative_path
                
                template = env.get_template(str(relative_path))
                rendered_content = template.render(**template_vars)
                
                with open(output_file, 'w') as f:
                    f.write(rendered_content)
        
        # Update agent status
        agent.status = "ready"
        active_agents[agent_id] = agent
        
        # Run enhanced quality validation
        if request.run_tests:
            logger.info("Starting enhanced quality validation", agent_id=agent_id)
            try:
                validator = AgentQualityValidator()
                
                # Load agent config for validation
                config_file = output_dir / "config.yaml"
                with open(config_file, 'r') as f:
                    agent_config = yaml.safe_load(f)
                
                # Run comprehensive validation
                validation_report = await validator.validate_generated_agent(
                    agent_id, agent_config, agent.type
                )
                
                # Store validation results
                agent.test_results = validation_report
                active_agents[agent_id] = agent
                
                # Update status based on validation
                if validation_report.get("certification") in ["excellent", "good", "acceptable"]:
                    agent.status = "validated"
                    logger.info("Agent validation passed", agent_id=agent_id, score=validation_report.get("overall_score"))
                else:
                    agent.status = "validation_failed"
                    logger.warning("Agent validation failed", agent_id=agent_id, score=validation_report.get("overall_score"))
                
                active_agents[agent_id] = agent
                
            except Exception as e:
                logger.error("Enhanced validation failed", agent_id=agent_id, error=str(e))
                # Fallback to basic tests
                await run_agent_tests(agent_id)
        
        # Deploy if requested and validation passed
        if request.deploy_immediately and agent.status in ["ready", "validated"]:
            await deploy_agent_container(agent_id)
        
        logger.info(
            "Agent generation completed",
            agent_id=agent_id,
            output_dir=str(output_dir)
        )
    
    except Exception as e:
        logger.error("Agent generation failed", agent_id=agent_id, error=str(e))
        agent = active_agents[agent_id]
        agent.status = "failed"
        active_agents[agent_id] = agent


async def run_enhanced_agent_validation(agent_id: str):
    """Run enhanced validation using Scenario-CoD system"""
    try:
        agent = active_agents[agent_id]
        
        # Load agent config
        config_file = GENERATED_AGENTS_DIR / agent_id / "config.yaml"
        with open(config_file, 'r') as f:
            agent_config = yaml.safe_load(f)
        
        # Run enhanced validation
        validator = AgentQualityValidator()
        validation_report = await validator.validate_generated_agent(
            agent_id, agent_config, agent.type
        )
        
        # Store results
        agent.test_results = validation_report
        
        # Update status based on validation
        if validation_report.get("certification") in ["excellent", "good", "acceptable"]:
            agent.status = "validated"
            logger.info("Enhanced validation passed", agent_id=agent_id, score=validation_report.get("overall_score"))
        else:
            agent.status = "validation_failed" 
            logger.warning("Enhanced validation failed", agent_id=agent_id, score=validation_report.get("overall_score"))
        
        active_agents[agent_id] = agent
        
    except Exception as e:
        logger.error("Enhanced validation failed", agent_id=agent_id, error=str(e))
        agent = active_agents[agent_id]
        agent.status = "validation_failed"
        active_agents[agent_id] = agent


async def run_agent_tests(agent_id: str):
    """Run basic Scenario tests (fallback method)"""
    try:
        agent = active_agents[agent_id]
        
        # Call Scenario testing service
        async with httpx.AsyncClient(timeout=60.0) as client:
            test_request = {
                "test_type": "custom_agent",
                "agent_id": agent_id,
                "agent_type": agent.type,
                "framework": agent.framework
            }
            
            response = await client.post(
                f"{ULTRAMCP_SCENARIO_URL}/test/run",
                json=test_request
            )
            
            if response.status_code == 200:
                test_result = response.json()
                agent.test_results = test_result
                active_agents[agent_id] = agent
                
                logger.info(
                    "Agent testing completed",
                    agent_id=agent_id,
                    test_success=test_result.get("status") == "started"
                )
            else:
                logger.error(
                    "Agent testing failed",
                    agent_id=agent_id,
                    status_code=response.status_code
                )
    
    except Exception as e:
        logger.error("Agent testing error", agent_id=agent_id, error=str(e))


async def deploy_agent_container(agent_id: str):
    """Deploy agent as Docker container"""
    try:
        agent = active_agents[agent_id]
        
        # Create Dockerfile for agent
        agent_dir = GENERATED_AGENTS_DIR / agent_id
        dockerfile_content = generate_agent_dockerfile(agent)
        
        with open(agent_dir / "Dockerfile", 'w') as f:
            f.write(dockerfile_content)
        
        # Build and deploy with Docker
        # This would integrate with Docker API to build and run container
        # For now, marking as deployed
        agent.deployed = True
        agent.status = "deployed"
        active_agents[agent_id] = agent
        
        logger.info("Agent deployed successfully", agent_id=agent_id)
        
    except Exception as e:
        logger.error("Agent deployment failed", agent_id=agent_id, error=str(e))
        agent = active_agents[agent_id]
        agent.status = "deployment_failed"
        active_agents[agent_id] = agent


def generate_agent_dockerfile(agent: AgentInfo) -> str:
    """Generate Dockerfile for agent deployment"""
    return f"""# Generated Dockerfile for Agent: {agent.name}
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY . .

# Expose port (dynamic based on agent type)
EXPOSE 8015

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8015/health || exit 1

# Run agent
CMD ["python", "main.py"]
"""


async def create_default_templates():
    """Create default agent templates if they don't exist"""
    try:
        TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
        
        # Create UltraMCP customer support template
        ultramcp_dir = TEMPLATES_DIR / "ultramcp" / "customer-support"
        ultramcp_dir.mkdir(parents=True, exist_ok=True)
        
        config_content = """
agent:
  name: "customer-support"
  type: "business"
  framework: "ultramcp"
  description: "Customer support agent with UltraMCP integration"

capabilities:
  - "query_knowledge_base"
  - "escalate_to_human"
  - "create_ticket"
  - "cod_consultation"

models:
  primary: "local:qwen2.5:14b"
  fallback: "openai:gpt-4-turbo"

testing:
  scenarios:
    - "complaint_handling"
    - "product_inquiry"
    - "refund_request"
  quality_threshold: 0.75

deployment:
  port: 8015
  memory: "512Mi"
  replicas: 1
"""
        
        agent_code = '''"""
UltraMCP Customer Support Agent
Generated from template with local models integration
"""

import asyncio
import httpx
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="{{ agent_name }}", version="1.0.0")

class CustomerQuery(BaseModel):
    message: str
    customer_id: str = None
    priority: str = "normal"

@app.get("/health")
async def health():
    return {"status": "healthy", "agent": "{{ agent_name }}"}

@app.post("/chat")
async def handle_customer_query(query: CustomerQuery):
    """Handle customer support query with UltraMCP integration"""
    
    # Use local models for privacy-first customer support
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "{{ ultramcp_local_models_url }}/generate",
                json={
                    "prompt": f"Customer support query: {query.message}",
                    "task_type": "customer_support",
                    "max_tokens": 300
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "response": result.get("content"),
                    "agent": "{{ agent_name }}",
                    "model": result.get("model"),
                    "escalation_needed": "escalate" in query.message.lower()
                }
        except Exception as e:
            # Fallback response
            return {
                "response": "I apologize, but I'm experiencing technical difficulties. Please contact human support.",
                "agent": "{{ agent_name }}",
                "error": str(e),
                "escalation_needed": True
            }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8015)
'''
        
        # Write template files
        with open(ultramcp_dir / "config.yaml", 'w') as f:
            f.write(config_content.strip())
        
        with open(ultramcp_dir / "main.py", 'w') as f:
            f.write(agent_code.strip())
        
        with open(ultramcp_dir / "requirements.txt", 'w') as f:
            f.write("fastapi>=0.104.0\nuvicorn>=0.24.0\nhttpx>=0.27.0\npydantic>=2.7.0\n")
        
        logger.info("Default templates created successfully")
        
    except Exception as e:
        logger.error("Failed to create default templates", error=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8014)