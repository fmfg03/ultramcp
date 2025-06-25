#!/bin/bash

echo "🚀 Deploying SUPERmcp A2A Agents..."

# Verificar que el servidor A2A central esté funcionando
echo "📡 Checking A2A Central Server..."
if ! curl -s http://localhost:8200/health > /dev/null; then
    echo "❌ A2A Central Server not running. Starting it..."
    python3 supermcp_a2a_server.py &
    sleep 5
fi

echo "✅ A2A Central Server is running"

# Instalar dependencias si no están instaladas
echo "📦 Installing dependencies..."
pip3 install aiohttp asyncio > /dev/null 2>&1

# Iniciar agentes A2A en background
echo "🤖 Starting A2A Agents..."

# Manus Agent (Puerto 8210)
echo "  🧠 Starting Manus Orchestrator Agent on port 8210..."
python3 -c "
import asyncio
import sys
sys.path.append('/home/ubuntu')
from supermcp_a2a_adapters import ManusA2AAgent
from aiohttp import web

async def start_manus():
    agent = ManusA2AAgent()
    await agent.register_with_a2a_server()
    runner = web.AppRunner(agent.app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8210)
    await site.start()
    print('Manus Agent started on port 8210')
    while True:
        await asyncio.sleep(30)
        await agent.send_heartbeat(0.1)

asyncio.run(start_manus())
" &

sleep 2

# SAM Agent (Puerto 8211)
echo "  🔧 Starting SAM Executor Agent on port 8211..."
python3 -c "
import asyncio
import sys
sys.path.append('/home/ubuntu')
from supermcp_a2a_adapters import SAMA2AAgent
from aiohttp import web

async def start_sam():
    agent = SAMA2AAgent()
    await agent.register_with_a2a_server()
    runner = web.AppRunner(agent.app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8211)
    await site.start()
    print('SAM Agent started on port 8211')
    while True:
        await asyncio.sleep(30)
        await agent.send_heartbeat(0.1)

asyncio.run(start_sam())
" &

sleep 2

# Memory Agent (Puerto 8212)
echo "  🧠 Starting Memory Analyzer Agent on port 8212..."
python3 -c "
import asyncio
import sys
sys.path.append('/home/ubuntu')
from supermcp_a2a_adapters import MemoryA2AAgent
from aiohttp import web

async def start_memory():
    agent = MemoryA2AAgent()
    await agent.register_with_a2a_server()
    runner = web.AppRunner(agent.app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8212)
    await site.start()
    print('Memory Agent started on port 8212')
    while True:
        await asyncio.sleep(30)
        await agent.send_heartbeat(0.1)

asyncio.run(start_memory())
" &

echo "⏳ Waiting for agents to start..."
sleep 10

echo "🔍 Verifying agent deployment..."

# Verificar cada agente
echo "  📡 Checking Manus Agent (8210)..."
if curl -s http://localhost:8210/health > /dev/null; then
    echo "  ✅ Manus Agent is running"
else
    echo "  ❌ Manus Agent failed to start"
fi

echo "  📡 Checking SAM Agent (8211)..."
if curl -s http://localhost:8211/health > /dev/null; then
    echo "  ✅ SAM Agent is running"
else
    echo "  ❌ SAM Agent failed to start"
fi

echo "  📡 Checking Memory Agent (8212)..."
if curl -s http://localhost:8212/health > /dev/null; then
    echo "  ✅ Memory Agent is running"
else
    echo "  ❌ Memory Agent failed to start"
fi

echo "📊 Checking A2A Registry..."
curl -s http://localhost:8200/agents

echo ""
echo "🎉 A2A Agent deployment completed!"
echo "📍 Agent Endpoints:"
echo "  🧠 Manus Orchestrator: http://localhost:8210"
echo "  🔧 SAM Executor: http://localhost:8211"
echo "  💾 Memory Analyzer: http://localhost:8212"
echo "  📡 A2A Central Server: http://localhost:8200"
