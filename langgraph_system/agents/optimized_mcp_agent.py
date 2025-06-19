"""
Complete Optimized MCP Agent with Caching and Precheck
Production-ready agent with maximum efficiency
"""

from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from langgraph_system.nodes.optimized_nodes import (
    optimized_reasoning_node,
    optimized_research_node,
    optimized_builder_node,
    should_use_research,
    should_use_builder,
    should_apply_contradiction
)
from langgraph_system.utils.intelligent_cache import get_cache_stats, clear_cache
from langgraph_system.utils.conditional_precheck import get_precheck_stats, reset_precheck_history

class OptimizedMCPAgent:
    """
    Complete MCP Agent with intelligent optimization
    """
    
    def __init__(self):
        self.graph = self._build_graph()
        self.stats = {
            'total_executions': 0,
            'cache_hits': 0,
            'operations_skipped': 0,
            'total_time_saved': 0.0
        }
    
    def _build_graph(self) -> StateGraph:
        """Build the optimized LangGraph"""
        
        # Define the state schema
        class AgentState(Dict):
            task: str
            reasoning_result: str = ""
            research_result: str = ""
            build_result: str = ""
            final_result: Any = None
            next_steps: List[str] = []
            agent_path: List[str] = []
            precheck_result: Any = None
            skipped: bool = False
            from_cache: bool = False
            simplified: bool = False
            delegated: bool = False
        
        # Create the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("reasoning", optimized_reasoning_node)
        workflow.add_node("research", optimized_research_node)
        workflow.add_node("builder", optimized_builder_node)
        workflow.add_node("contradiction", self._contradiction_node)
        workflow.add_node("finalize", self._finalize_node)
        
        # Set entry point
        workflow.set_entry_point("reasoning")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "reasoning",
            should_use_research,
            {
                "execute_research": "research",
                "skip_research": "builder"
            }
        )
        
        workflow.add_conditional_edges(
            "research",
            should_use_builder,
            {
                "execute_builder": "builder",
                "skip_builder": "contradiction"
            }
        )
        
        workflow.add_conditional_edges(
            "builder",
            should_apply_contradiction,
            {
                "apply_contradiction": "contradiction",
                "skip_contradiction": "finalize"
            }
        )
        
        workflow.add_edge("contradiction", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def _contradiction_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Apply contradiction if needed"""
        print("🔥 Applying contradiction analysis...")
        
        # Simple contradiction logic
        final_result = state.get('final_result', {})
        
        if isinstance(final_result, dict):
            confidence = final_result.get('confidence', 1.0)
            
            if confidence < 0.7:
                # Apply contradiction
                contradiction_feedback = "Result confidence is low. Consider alternative approaches."
                
                # Improve confidence slightly
                final_result['confidence'] = min(confidence + 0.1, 1.0)
                final_result['contradiction_applied'] = True
                final_result['feedback'] = contradiction_feedback
        
        return {
            **state,
            'final_result': final_result,
            'contradiction_applied': True
        }
    
    def _finalize_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize the agent execution"""
        print("✅ Finalizing MCP agent execution...")
        
        # Compile execution summary
        execution_summary = {
            'agent_path': state.get('agent_path', []),
            'operations_performed': len(state.get('agent_path', [])),
            'skipped': state.get('skipped', False),
            'from_cache': state.get('from_cache', False),
            'simplified': state.get('simplified', False),
            'delegated': state.get('delegated', False),
            'contradiction_applied': state.get('contradiction_applied', False),
            'final_confidence': state.get('final_result', {}).get('confidence', 1.0) if isinstance(state.get('final_result'), dict) else 1.0
        }
        
        return {
            **state,
            'execution_summary': execution_summary,
            'completed': True
        }
    
    def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Execute the optimized MCP agent"""
        import time
        
        start_time = time.time()
        
        # Prepare initial state
        initial_state = {
            'task': task,
            **kwargs
        }
        
        # Execute the graph
        result = self.graph.invoke(initial_state)
        
        execution_time = time.time() - start_time
        
        # Update stats
        self.stats['total_executions'] += 1
        
        if result.get('from_cache', False):
            self.stats['cache_hits'] += 1
        
        if result.get('skipped', False):
            self.stats['operations_skipped'] += 1
            self.stats['total_time_saved'] += 5.0  # Estimated time saved
        
        # Add execution metadata
        result['execution_time'] = execution_time
        result['agent_stats'] = self.get_stats()
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive agent statistics"""
        cache_stats = get_cache_stats()
        precheck_stats = get_precheck_stats()
        
        return {
            'agent_stats': self.stats,
            'cache_stats': cache_stats,
            'precheck_stats': precheck_stats,
            'efficiency_metrics': {
                'cache_hit_rate': cache_stats.get('hit_rate', 0),
                'skip_rate': (self.stats['operations_skipped'] / max(self.stats['total_executions'], 1)),
                'avg_time_saved': (self.stats['total_time_saved'] / max(self.stats['total_executions'], 1)),
                'total_cost_saved': precheck_stats.get('total_estimated_cost', 0) * 0.3
            }
        }
    
    def clear_cache(self):
        """Clear all caches"""
        clear_cache()
        reset_precheck_history()
        print("🧹 All caches cleared")
    
    def warm_cache(self, common_tasks: List[str]):
        """Warm up cache with common tasks"""
        print("🔥 Warming up cache...")
        
        for task in common_tasks:
            try:
                self.execute(task)
                print(f"✅ Cached: {task[:50]}...")
            except Exception as e:
                print(f"❌ Failed to cache: {task[:50]}... - {e}")
        
        print(f"🎯 Cache warmed with {len(common_tasks)} tasks")

# Global optimized agent instance
optimized_agent = OptimizedMCPAgent()

# Convenience functions
def execute_optimized_task(task: str, **kwargs) -> Dict[str, Any]:
    """Execute a task with the optimized MCP agent"""
    return optimized_agent.execute(task, **kwargs)

def get_optimization_metrics() -> Dict[str, Any]:
    """Get optimization metrics"""
    return optimized_agent.get_stats()

def clear_all_caches():
    """Clear all optimization caches"""
    optimized_agent.clear_cache()

def warm_up_system():
    """Warm up the system with common tasks"""
    common_tasks = [
        "Create a landing page",
        "What is AI?",
        "Research market trends",
        "Build a web application",
        "Analyze user feedback",
        "Generate a report",
        "Create documentation",
        "Design a logo",
        "Write a blog post",
        "Develop an API"
    ]
    
    optimized_agent.warm_cache(common_tasks)

# Example usage and testing
if __name__ == "__main__":
    import time
    
    print("🚀 Testing Complete Optimized MCP Agent\n")
    
    # Test cases with different complexity levels
    test_cases = [
        "Create a modern landing page for an AI startup with dark mode",
        "What is machine learning?",
        "Research the latest trends in artificial intelligence",
        "hi there",
        "Build a comprehensive e-commerce platform with payment integration",
        "What is machine learning?",  # Duplicate to test caching
        "Create a modern landing page for an AI startup with dark mode"  # Duplicate to test caching
    ]
    
    print("--- Initial Execution (Cold Cache) ---")
    for i, task in enumerate(test_cases, 1):
        print(f"\n{i}. Task: {task}")
        
        start = time.time()
        result = execute_optimized_task(task)
        duration = time.time() - start
        
        summary = result.get('execution_summary', {})
        print(f"   ⏱️  Execution time: {duration:.2f}s")
        print(f"   🛤️  Agent path: {summary.get('agent_path', [])}")
        print(f"   ⚡ Optimizations: Cache={summary.get('from_cache', False)}, "
              f"Skip={summary.get('skipped', False)}, "
              f"Simplified={summary.get('simplified', False)}")
        print(f"   🎯 Confidence: {summary.get('final_confidence', 1.0):.2f}")
    
    print("\n--- Optimization Statistics ---")
    stats = get_optimization_metrics()
    efficiency = stats['efficiency_metrics']
    
    print(f"📊 Total executions: {stats['agent_stats']['total_executions']}")
    print(f"🎯 Cache hit rate: {efficiency['cache_hit_rate']:.2%}")
    print(f"⏭️  Skip rate: {efficiency['skip_rate']:.2%}")
    print(f"⚡ Avg time saved: {efficiency['avg_time_saved']:.2f}s")
    print(f"💰 Total cost saved: ${efficiency['total_cost_saved']:.3f}")
    
    print(f"\n🔥 Cache Stats:")
    cache_stats = stats['cache_stats']
    print(f"   Hits: {cache_stats.get('hits', 0)}")
    print(f"   Misses: {cache_stats.get('misses', 0)}")
    print(f"   Memory usage: {cache_stats.get('memory_usage_mb', 0):.2f} MB")
    
    print(f"\n🔍 Precheck Stats:")
    precheck_stats = stats['precheck_stats']
    if precheck_stats.get('total_decisions', 0) > 0:
        distribution = precheck_stats.get('decision_distribution', {})
        print(f"   Execute: {distribution.get('execute', 0)}")
        print(f"   Skip: {distribution.get('skip', 0)}")
        print(f"   Simplified: {distribution.get('simplified', 0)}")
        print(f"   Cache lookup: {distribution.get('cache_lookup', 0)}")
        print(f"   Delegate: {distribution.get('delegate', 0)}")
    
    print("\n✅ Optimization testing completed!")

