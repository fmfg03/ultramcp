#!/usr/bin/env python3
"""
UltraMCP Agent Factory CLI
Command-line interface for creating and managing AI agents
"""

import asyncio
import json
import sys
import time
from typing import Dict, Any, Optional
import click
import httpx
import yaml
from pathlib import Path

# Configuration
AGENT_FACTORY_URL = "http://localhost:8014"
TIMEOUT = 60


class AgentFactoryCLI:
    """CLI for UltraMCP Agent Factory"""
    
    def __init__(self):
        self.base_url = AGENT_FACTORY_URL
    
    async def create_agent(self, agent_type: str, framework: str = "ultramcp", 
                          name: Optional[str] = None, deploy: bool = False, 
                          test: bool = True, customization: Optional[Dict] = None):
        """Create a new agent from template"""
        
        request_data = {
            "agent_type": agent_type,
            "framework": framework,
            "deploy_immediately": deploy,
            "run_tests": test
        }
        
        if name:
            request_data["name"] = name
        
        if customization:
            request_data["customization"] = customization
        
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await client.post(
                    f"{self.base_url}/agents/create",
                    json=request_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    agent_id = result["agent_id"]
                    
                    click.echo(f"✅ Agent creation started")
                    click.echo(f"Agent ID: {agent_id}")
                    click.echo(f"Agent Name: {result['agent_name']}")
                    click.echo(f"Estimated completion: {result['estimated_completion']}")
                    
                    # Wait for completion if deploy or test requested
                    if deploy or test:
                        click.echo("\n🔄 Monitoring agent creation...")
                        await self.wait_for_agent_ready(agent_id)
                    
                    return agent_id
                else:
                    click.echo(f"❌ Agent creation failed: {response.text}")
                    return None
        
        except Exception as e:
            click.echo(f"❌ Error creating agent: {str(e)}")
            return None
    
    async def wait_for_agent_ready(self, agent_id: str):
        """Wait for agent to be ready"""
        max_attempts = 30
        attempt = 0
        
        while attempt < max_attempts:
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.get(f"{self.base_url}/agents/{agent_id}")
                    
                    if response.status_code == 200:
                        agent_data = response.json()
                        status = agent_data["status"]
                        
                        if status == "ready":
                            click.echo("✅ Agent is ready!")
                            return True
                        elif status == "deployed":
                            click.echo("🚀 Agent is deployed!")
                            return True
                        elif status == "failed":
                            click.echo("❌ Agent creation failed!")
                            return False
                        else:
                            click.echo(f"⏳ Status: {status}")
                
                await asyncio.sleep(5)
                attempt += 1
            
            except Exception as e:
                click.echo(f"⚠️  Error checking status: {str(e)}")
                await asyncio.sleep(5)
                attempt += 1
        
        click.echo("⏰ Timeout waiting for agent completion")
        return False
    
    async def list_agents(self):
        """List all created agents"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/agents")
                
                if response.status_code == 200:
                    data = response.json()
                    agents = data["agents"]
                    
                    if not agents:
                        click.echo("No agents found")
                        return
                    
                    click.echo(f"\n📋 Found {len(agents)} agents:")
                    click.echo("-" * 80)
                    
                    for agent in agents:
                        status_icon = {
                            "ready": "✅",
                            "deployed": "🚀", 
                            "generating": "🔄",
                            "failed": "❌"
                        }.get(agent["status"], "❓")
                        
                        click.echo(f"{status_icon} {agent['name']} ({agent['agent_id'][:8]})")
                        click.echo(f"   Type: {agent['type']} | Framework: {agent['framework']}")
                        click.echo(f"   Status: {agent['status']} | Created: {agent['created_at']}")
                        click.echo()
                else:
                    click.echo(f"❌ Failed to list agents: {response.text}")
        
        except Exception as e:
            click.echo(f"❌ Error listing agents: {str(e)}")
    
    async def list_templates(self):
        """List all available templates"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/templates")
                
                if response.status_code == 200:
                    data = response.json()
                    templates = data["templates"]
                    
                    click.echo(f"\n📚 Available Templates ({data['total_templates']} total):")
                    click.echo("=" * 60)
                    
                    for framework, framework_templates in templates.items():
                        click.echo(f"\n🔧 {framework.upper()} Framework:")
                        
                        for template in framework_templates:
                            click.echo(f"  📄 {template['name']}")
                            click.echo(f"     Type: {template['type']}")
                            click.echo(f"     Description: {template['description']}")
                            click.echo(f"     Capabilities: {', '.join(template['capabilities'][:3])}...")
                            click.echo()
                else:
                    click.echo(f"❌ Failed to list templates: {response.text}")
        
        except Exception as e:
            click.echo(f"❌ Error listing templates: {str(e)}")
    
    async def deploy_agent(self, agent_id: str):
        """Deploy an agent"""
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await client.post(f"{self.base_url}/agents/{agent_id}/deploy")
                
                if response.status_code == 200:
                    click.echo("🚀 Agent deployment started")
                    await self.wait_for_agent_ready(agent_id)
                else:
                    click.echo(f"❌ Deployment failed: {response.text}")
        
        except Exception as e:
            click.echo(f"❌ Error deploying agent: {str(e)}")
    
    async def test_agent(self, agent_id: str):
        """Test an agent"""
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await client.post(f"{self.base_url}/agents/{agent_id}/test")
                
                if response.status_code == 200:
                    click.echo("🧪 Agent testing started")
                    click.echo("Tests are running in the background...")
                else:
                    click.echo(f"❌ Testing failed: {response.text}")
        
        except Exception as e:
            click.echo(f"❌ Error testing agent: {str(e)}")
    
    async def get_agent_status(self, agent_id: str):
        """Get agent status"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/agents/{agent_id}")
                
                if response.status_code == 200:
                    agent = response.json()
                    
                    click.echo(f"\n📊 Agent Status: {agent['name']}")
                    click.echo("-" * 40)
                    click.echo(f"ID: {agent['agent_id']}")
                    click.echo(f"Type: {agent['type']}")
                    click.echo(f"Framework: {agent['framework']}")
                    click.echo(f"Status: {agent['status']}")
                    click.echo(f"Deployed: {'Yes' if agent['deployed'] else 'No'}")
                    click.echo(f"Created: {agent['created_at']}")
                    
                    if agent.get('test_results'):
                        click.echo(f"\n🧪 Test Results:")
                        click.echo(f"Status: {agent['test_results'].get('status', 'Unknown')}")
                else:
                    click.echo(f"❌ Failed to get agent status: {response.text}")
        
        except Exception as e:
            click.echo(f"❌ Error getting agent status: {str(e)}")
    
    async def check_health(self):
        """Check Agent Factory service health"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/health")
                
                if response.status_code == 200:
                    health = response.json()
                    
                    click.echo("🏥 Agent Factory Health Check")
                    click.echo("-" * 30)
                    click.echo(f"Status: {health['status']}")
                    click.echo(f"Active Agents: {health['active_agents']}")
                    click.echo(f"Generation Tasks: {health['generation_tasks']}")
                    click.echo(f"Templates Available: {health['templates_available']}")
                    
                    click.echo("\n🔗 UltraMCP Services:")
                    services = health.get('ultramcp_services', {})
                    for service, status in services.items():
                        icon = "✅" if status == "healthy" else "❌"
                        click.echo(f"  {icon} {service}: {status}")
                else:
                    click.echo(f"❌ Health check failed: {response.text}")
        
        except Exception as e:
            click.echo(f"❌ Error checking health: {str(e)}")


# CLI Commands

@click.group()
def cli():
    """UltraMCP Agent Factory CLI - Create and manage AI agents"""
    pass


@cli.command()
@click.argument('agent_type')
@click.option('--framework', '-f', default='ultramcp', 
              help='Framework to use (ultramcp, langchain, crewai, autogen)')
@click.option('--name', '-n', help='Custom name for the agent')
@click.option('--deploy', '-d', is_flag=True, help='Deploy agent immediately')
@click.option('--test', '-t', is_flag=True, default=True, help='Run tests (default: true)')
@click.option('--config', '-c', help='Custom configuration file (YAML)')
def create(agent_type, framework, name, deploy, test, config):
    """Create a new agent from template
    
    Examples:
        agent-factory create customer-support
        agent-factory create research-analyst --framework langchain
        agent-factory create code-reviewer --deploy --name my-reviewer
    """
    
    customization = None
    if config and Path(config).exists():
        with open(config, 'r') as f:
            customization = yaml.safe_load(f)
    
    factory = AgentFactoryCLI()
    asyncio.run(factory.create_agent(agent_type, framework, name, deploy, test, customization))


@cli.command()
def list():
    """List all created agents"""
    factory = AgentFactoryCLI()
    asyncio.run(factory.list_agents())


@cli.command()
def templates():
    """List all available agent templates"""
    factory = AgentFactoryCLI()
    asyncio.run(factory.list_templates())


@cli.command()
@click.argument('agent_id')
def deploy(agent_id):
    """Deploy an agent to production"""
    factory = AgentFactoryCLI()
    asyncio.run(factory.deploy_agent(agent_id))


@cli.command()
@click.argument('agent_id')
def test(agent_id):
    """Run tests on an agent"""
    factory = AgentFactoryCLI()
    asyncio.run(factory.test_agent(agent_id))


@cli.command()
@click.argument('agent_id')
def status(agent_id):
    """Get agent status and details"""
    factory = AgentFactoryCLI()
    asyncio.run(factory.get_agent_status(agent_id))


@cli.command()
def health():
    """Check Agent Factory service health"""
    factory = AgentFactoryCLI()
    asyncio.run(factory.check_health())


@cli.command()
def frameworks():
    """List supported frameworks and their capabilities"""
    factory = AgentFactoryCLI()
    
    async def show_frameworks():
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{AGENT_FACTORY_URL}/frameworks")
                
                if response.status_code == 200:
                    data = response.json()
                    frameworks = data["frameworks"]
                    
                    click.echo("🔧 Supported Frameworks:")
                    click.echo("=" * 50)
                    
                    for name, info in frameworks.items():
                        click.echo(f"\n📦 {name.upper()}")
                        click.echo(f"Description: {info['description']}")
                        click.echo(f"Capabilities: {', '.join(info['capabilities'])}")
                        click.echo(f"Use Cases: {', '.join(info['use_cases'])}")
                else:
                    click.echo(f"❌ Failed to get frameworks: {response.text}")
        
        except Exception as e:
            click.echo(f"❌ Error getting frameworks: {str(e)}")
    
    asyncio.run(show_frameworks())


if __name__ == '__main__':
    cli()