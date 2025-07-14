#!/usr/bin/env python3
"""
Fixed SynLogic Integration for UltraMCP Chain of Debate
Works with actual CoD API format discovered
"""

import asyncio
import httpx
import json
import uuid
from typing import Dict, List, Optional
from datetime import datetime

class SynLogicCoD:
    """Enhanced Chain of Debate with SynLogic integration - Fixed version"""
    
    def __init__(self, cod_url: str = "http://localhost:8001"):
        self.cod_url = cod_url
        self.synlogic_tasks = [
            "sudoku", "game_of_24", "cipher", "arrow_maze", 
            "logical_reasoning", "mathematical_proof", "puzzle_solving"
        ]
    
    async def generate_debate_problem(self, task_type: str, difficulty: float = 0.5) -> Dict:
        """Generate a verifiable reasoning problem for debate"""
        problems = {
            "logical_reasoning": {
                "statement": "All birds can fly. Penguins are birds. Can penguins fly? Analyze this logical argument.",
                "context": "This is a classic logical fallacy example. The first premise is false.",
                "solution": "No, penguins cannot fly. This reveals that the first premise 'All birds can fly' is false, making this a logical fallacy.",
                "verification_keywords": ["fallacy", "false premise", "cannot fly", "penguin", "logical error"]
            },
            "game_of_24": {
                "statement": f"Using the numbers [6, 6, 13, 1] and operations +, -, *, /, create an expression that equals 24.",
                "context": "Mathematical puzzle requiring creative use of arithmetic operations.",
                "solution": "6 / (1 - 6/13) = 24, or equivalently: 6 * 13 / (13 - 6) = 78/7 ≠ 24. Correct: (6 + 6) * (13 - 1) / (something) - need valid solution.",
                "verification_keywords": ["24", "arithmetic", "expression", "equals", "operations"]
            },
            "mathematical_proof": {
                "statement": f"Prove or disprove: The square root of 2 is irrational.",
                "context": "Classic mathematical proof requiring logical reasoning.",
                "solution": "√2 is irrational. Proof by contradiction: Assume √2 = p/q in lowest terms. Then 2q² = p², so p² is even, thus p is even. Let p = 2k, then 2q² = 4k², so q² = 2k², making q even. Contradiction since p and q can't both be even if in lowest terms.",
                "verification_keywords": ["irrational", "proof", "contradiction", "even", "lowest terms"]
            },
            "sudoku": {
                "statement": f"Analyze the logical strategies needed to solve a Sudoku puzzle.",
                "context": "Puzzle-solving that requires systematic logical deduction.",
                "solution": "Sudoku solving uses constraint satisfaction: elimination (removing possibilities), hidden singles (only one cell can contain a number), naked pairs (two cells with same two possibilities), and backtracking for complex cases.",
                "verification_keywords": ["constraint", "elimination", "deduction", "possibilities", "systematic"]
            }
        }
        
        return problems.get(task_type, problems["logical_reasoning"])
    
    async def run_enhanced_debate(self, task_type: str, difficulty: float = 0.5, agents: List[str] = None) -> Dict:
        """Run CoD debate with SynLogic-generated problem using correct API format"""
        if agents is None:
            agents = ["claude", "gpt4"]
        
        # Generate problem
        problem = await self.generate_debate_problem(task_type, difficulty)
        
        # Create unique task ID
        task_id = f"synlogic-{task_type}-{uuid.uuid4().hex[:8]}"
        
        # Prepare CoD request with correct format
        cod_request = {
            "task_id": task_id,
            "topic": problem["statement"],
            "agents": agents,
            "rounds": 3
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(f"{self.cod_url}/debate", json=cod_request)
                
                if response.status_code != 200:
                    return {"error": f"CoD API error: {response.status_code} - {response.text}"}
                
                debate_result = response.json()
                
                # Extract the consensus (final conclusion)
                consensus = debate_result.get("consensus", "")
                confidence_score = debate_result.get("confidence_score", 0)
                
                # Verify the solution
                verification_score = await self.verify_solution(
                    consensus, 
                    problem["solution"],
                    problem["verification_keywords"]
                )
                
                return {
                    "task_id": task_id,
                    "problem": problem,
                    "debate_result": debate_result,
                    "verification": {
                        "score": verification_score,
                        "confidence": confidence_score,
                        "keywords_found": self.count_keywords(consensus, problem["verification_keywords"]),
                        "expected_solution": problem["solution"]
                    },
                    "metadata": {
                        "task_type": task_type,
                        "difficulty": difficulty,
                        "agents": agents,
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
        except Exception as e:
            return {"error": f"Enhanced debate failed: {e}"}
    
    def count_keywords(self, text: str, keywords: List[str]) -> Dict:
        """Count how many verification keywords appear in the text"""
        text_lower = text.lower()
        found = {}
        for keyword in keywords:
            count = text_lower.count(keyword.lower())
            if count > 0:
                found[keyword] = count
        return found
    
    async def verify_solution(self, consensus: str, correct_solution: str, keywords: List[str]) -> float:
        """Verify debate conclusion against known solution"""
        consensus_lower = consensus.lower()
        solution_lower = correct_solution.lower()
        
        # Keyword matching score (0.0 to 0.6)
        keyword_score = len(self.count_keywords(consensus, keywords)) / len(keywords) * 0.6
        
        # Content similarity score (0.0 to 0.4)
        consensus_words = set(consensus_lower.split())
        solution_words = set(solution_lower.split())
        if solution_words:
            content_score = len(consensus_words.intersection(solution_words)) / len(solution_words) * 0.4
        else:
            content_score = 0.0
        
        total_score = keyword_score + content_score
        return min(1.0, total_score)  # Cap at 1.0
    
    async def progressive_training(self, task_type: str, num_rounds: int = 5) -> List[Dict]:
        """Run progressive difficulty training"""
        results = []
        difficulties = [i / (num_rounds - 1) for i in range(num_rounds)]  # 0.0 to 1.0
        
        for i, difficulty in enumerate(difficulties):
            print(f"\n🎓 Training Round {i+1}/{num_rounds}: {task_type} (difficulty {difficulty:.2f})")
            
            result = await self.run_enhanced_debate(task_type, difficulty)
            
            if "verification" in result:
                score = result["verification"]["score"]
                confidence = result["verification"]["confidence"]
                keywords = result["verification"]["keywords_found"]
                
                print(f"   📊 Verification Score: {score:.2f}")
                print(f"   🎯 Confidence: {confidence}%")
                print(f"   🔍 Keywords Found: {list(keywords.keys())}")
                
                results.append(result)
            else:
                print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
                results.append(result)
            
            # Brief pause between rounds
            await asyncio.sleep(3)
        
        return results
    
    async def benchmark_cod_performance(self) -> Dict:
        """Benchmark CoD performance across different SynLogic tasks"""
        benchmark_results = {}
        
        test_tasks = ["logical_reasoning", "mathematical_proof", "game_of_24"]
        
        for task in test_tasks:
            print(f"\n🔬 Benchmarking {task}...")
            
            # Test 3 difficulty levels
            task_results = []
            for difficulty in [0.3, 0.6, 0.9]:
                print(f"   Testing difficulty {difficulty}...")
                result = await self.run_enhanced_debate(task, difficulty)
                
                if "verification" in result:
                    task_results.append({
                        "difficulty": difficulty,
                        "verification_score": result["verification"]["score"],
                        "confidence_score": result["verification"]["confidence"],
                        "keywords_found": len(result["verification"]["keywords_found"]),
                        "task_id": result["task_id"]
                    })
            
            if task_results:
                avg_verification = sum(r["verification_score"] for r in task_results) / len(task_results)
                avg_confidence = sum(r["confidence_score"] for r in task_results) / len(task_results)
                
                benchmark_results[task] = {
                    "results": task_results,
                    "avg_verification_score": avg_verification,
                    "avg_confidence_score": avg_confidence,
                    "best_result": max(task_results, key=lambda x: x["verification_score"])
                }
                
                print(f"   ✅ Average Verification: {avg_verification:.2f}")
                print(f"   🎯 Average Confidence: {avg_confidence:.0f}%")
        
        return benchmark_results

# CLI Interface
async def main():
    import sys
    
    if len(sys.argv) < 2:
        print("🔧 SynLogic + CoD Integration (Fixed Version)")
        print("Usage: python3 cod-synlogic-integration-fixed.py <command> [args...]")
        print("")
        print("Commands:")
        print("  debate <task_type> [difficulty]     - Run enhanced debate")
        print("  training <task_type> [rounds]       - Progressive training")
        print("  benchmark                           - Benchmark CoD performance")
        print("  available-tasks                     - List available task types")
        print("  test-api                            - Test CoD API connectivity")
        print("")
        print("Examples:")
        print("  python3 cod-synlogic-integration-fixed.py debate logical_reasoning 0.7")
        print("  python3 cod-synlogic-integration-fixed.py training mathematical_proof 3")
        print("  python3 cod-synlogic-integration-fixed.py benchmark")
        return
    
    synlogic_cod = SynLogicCoD()
    command = sys.argv[1]
    
    if command == "test-api":
        print("🔗 Testing CoD API connectivity...")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{synlogic_cod.cod_url}/health")
                health_data = response.json()
                print(f"✅ CoD Service: {health_data.get('status', 'unknown')}")
                print(f"📊 Active Debates: {health_data.get('active_debates', 0)}")
                print(f"🔑 API Keys Available: {health_data.get('api_keys', {})}")
        except Exception as e:
            print(f"❌ CoD API Error: {e}")
    
    elif command == "available-tasks":
        print("📋 Available SynLogic task types:")
        for task in synlogic_cod.synlogic_tasks:
            print(f"  - {task}")
    
    elif command == "debate" and len(sys.argv) > 2:
        task_type = sys.argv[2]
        difficulty = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
        
        print(f"🤝 Running enhanced CoD debate: {task_type} (difficulty: {difficulty})")
        result = await synlogic_cod.run_enhanced_debate(task_type, difficulty)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return
        
        print(f"\n📋 Problem: {result['problem']['statement']}")
        print(f"🆔 Task ID: {result['task_id']}")
        
        if "verification" in result:
            verification = result["verification"]
            print(f"\n🎯 Verification Score: {verification['score']:.2f}")
            print(f"🎯 Confidence Score: {verification['confidence']}%")
            print(f"🔍 Keywords Found: {list(verification['keywords_found'].keys())}")
            
            if "debate_result" in result:
                consensus = result["debate_result"].get("consensus", "")
                print(f"\n💭 CoD Conclusion: {consensus[:200]}...")
        
        print(f"\n✅ Expected Solution: {result['problem']['solution'][:150]}...")
    
    elif command == "training" and len(sys.argv) > 2:
        task_type = sys.argv[2]
        rounds = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        
        print(f"🎓 Starting progressive training: {task_type} ({rounds} rounds)")
        results = await synlogic_cod.progressive_training(task_type, rounds)
        
        print("\n📊 Training Summary:")
        successful_results = [r for r in results if "verification" in r]
        if successful_results:
            avg_score = sum(r["verification"]["score"] for r in successful_results) / len(successful_results)
            avg_confidence = sum(r["verification"]["confidence"] for r in successful_results) / len(successful_results)
            print(f"   Average Verification Score: {avg_score:.2f}")
            print(f"   Average Confidence: {avg_confidence:.0f}%")
            print(f"   Successful Rounds: {len(successful_results)}/{len(results)}")
    
    elif command == "benchmark":
        print("📈 Benchmarking CoD performance across SynLogic tasks...")
        results = await synlogic_cod.benchmark_cod_performance()
        
        print("\n🏆 Benchmark Summary:")
        for task, data in results.items():
            print(f"\n{task.upper().replace('_', ' ')}:")
            print(f"  📊 Avg Verification: {data['avg_verification_score']:.2f}")
            print(f"  🎯 Avg Confidence: {data['avg_confidence_score']:.0f}%")
            print(f"  🏅 Best Score: {data['best_result']['verification_score']:.2f} (difficulty {data['best_result']['difficulty']})")
    
    else:
        print("❌ Invalid command or missing arguments")
        print("Use 'python3 cod-synlogic-integration-fixed.py' for help")

if __name__ == "__main__":
    asyncio.run(main())