#!/usr/bin/env python3
"""
MiniMax-M1-80k Integration Scripts for UltraMCP
Provides easy interfaces for using MiniMax-M1-80k in UltraMCP workflows
"""

import asyncio
import httpx
import json
from typing import Dict, List, Optional

class MiniMaxClient:
    """Client for interacting with MiniMax-M1-80k through UltraMCP orchestrator"""
    
    def __init__(self, base_url: str = "http://localhost:8012"):
        self.base_url = base_url
        
    async def health_check(self) -> bool:
        """Check if MiniMax service is available"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health")
                data = response.json()
                
                # Check if MiniMax provider is healthy
                minimax_status = data.get("providers", {}).get("minimax", {})
                return minimax_status.get("status") == "healthy"
        except:
            return False
    
    async def start_minimax(self) -> bool:
        """Start MiniMax server if not running"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.base_url}/models/minimax/start")
                return response.status_code == 200
        except:
            return False
    
    async def reasoning_generation(self, prompt: str, **kwargs) -> str:
        """Generate response using MiniMax-M1-80k reasoning capabilities"""
        payload = {
            "prompt": prompt,
            "task_type": "reasoning",
            "use_reasoning": True,
            "temperature": kwargs.get("temperature", 1.0),
            "max_tokens": kwargs.get("max_tokens", 8192)
        }
        
        try:
            async with httpx.AsyncClient(timeout=600.0) as client:
                response = await client.post(f"{self.base_url}/generate/reasoning", json=payload)
                data = response.json()
                return data.get("content", "")
        except Exception as e:
            raise Exception(f"MiniMax generation failed: {e}")
    
    async def mathematical_reasoning(self, problem: str) -> str:
        """Solve mathematical problems using MiniMax-M1-80k"""
        prompt = f"""Solve this mathematical problem step by step, showing all your reasoning:

{problem}

Please provide:
1. Problem analysis
2. Step-by-step solution
3. Verification of the answer
4. Final result"""
        
        return await self.reasoning_generation(prompt, task_type="mathematics")
    
    async def code_analysis(self, code: str, task: str) -> str:
        """Analyze code using MiniMax-M1-80k reasoning"""
        prompt = f"""Analyze the following code for: {task}

```
{code}
```

Please provide:
1. Code structure analysis
2. Potential issues or improvements
3. Best practices recommendations
4. Detailed reasoning for each point"""
        
        return await self.reasoning_generation(prompt, task_type="engineering")
    
    async def complex_decision(self, scenario: str, options: List[str]) -> str:
        """Make complex decisions using MiniMax-M1-80k reasoning"""
        options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
        
        prompt = f"""Analyze this decision scenario and provide reasoned recommendations:

Scenario: {scenario}

Options:
{options_text}

Please provide:
1. Analysis of each option
2. Pros and cons for each choice
3. Risk assessment
4. Recommended decision with detailed reasoning
5. Implementation considerations"""
        
        return await self.reasoning_generation(prompt, task_type="complex-analysis")

# Command-line interface functions
async def main():
    """CLI interface for MiniMax-M1-80k"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python minimax-integration.py <command> [args...]")
        print("Commands:")
        print("  health                    - Check MiniMax status")
        print("  start                     - Start MiniMax server")
        print("  reason <prompt>           - General reasoning")
        print("  math <problem>            - Mathematical reasoning")
        print("  code <file> <task>        - Code analysis")
        print("  decide <scenario> <opt1,opt2,...> - Decision making")
        return
    
    client = MiniMaxClient()
    command = sys.argv[1]
    
    if command == "health":
        is_healthy = await client.health_check()
        print("✅ MiniMax is healthy" if is_healthy else "❌ MiniMax is not available")
    
    elif command == "start":
        success = await client.start_minimax()
        print("✅ MiniMax server started" if success else "❌ Failed to start MiniMax server")
    
    elif command == "reason" and len(sys.argv) > 2:
        prompt = " ".join(sys.argv[2:])
        try:
            result = await client.reasoning_generation(prompt)
            print("🧠 MiniMax-M1-80k Reasoning:")
            print("=" * 50)
            print(result)
        except Exception as e:
            print(f"❌ Error: {e}")
    
    elif command == "math" and len(sys.argv) > 2:
        problem = " ".join(sys.argv[2:])
        try:
            result = await client.mathematical_reasoning(problem)
            print("🔢 Mathematical Reasoning:")
            print("=" * 50)
            print(result)
        except Exception as e:
            print(f"❌ Error: {e}")
    
    elif command == "code" and len(sys.argv) > 3:
        file_path = sys.argv[2]
        task = " ".join(sys.argv[3:])
        try:
            with open(file_path, 'r') as f:
                code = f.read()
            result = await client.code_analysis(code, task)
            print("💻 Code Analysis:")
            print("=" * 50)
            print(result)
        except Exception as e:
            print(f"❌ Error: {e}")
    
    elif command == "decide" and len(sys.argv) > 3:
        scenario = sys.argv[2]
        options = sys.argv[3].split(',')
        try:
            result = await client.complex_decision(scenario, options)
            print("🎯 Decision Analysis:")
            print("=" * 50)
            print(result)
        except Exception as e:
            print(f"❌ Error: {e}")
    
    else:
        print("❌ Invalid command or missing arguments")

if __name__ == "__main__":
    asyncio.run(main())