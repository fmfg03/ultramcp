"""
Optimized LangGraph Nodes with Caching and Precheck
Integration of intelligent caching and conditional precheck for maximum efficiency
"""

import time
from typing import Dict, Any, Optional
from langgraph_system.utils.intelligent_cache import cached_node, smart_cache_key, should_skip_cache
from langgraph_system.utils.conditional_precheck import precheck_node, PrecheckDecision

# Optimized Reasoning Node
@precheck_node('reasoning')
@cached_node(ttl=1800, cache_key_fn=smart_cache_key, skip_cache_fn=should_skip_cache)
def optimized_reasoning_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Optimized reasoning node with precheck and caching
    """
    task = state.get('task', state.get('query', ''))
    context = state.get('context', {})
    simplified = state.get('simplified', False)
    
    print(f"🧠 Executing reasoning for: {task[:50]}...")
    
    # Simulate reasoning time based on complexity
    if simplified:
        time.sleep(0.5)  # Fast simplified reasoning
        reasoning_result = f"Quick analysis: {task}"
        confidence = 0.7
    else:
        time.sleep(2.0)  # Full reasoning
        reasoning_result = f"Comprehensive analysis: {task}"
        confidence = 0.9
    
    # Extract key insights
    insights = []
    if 'create' in task.lower():
        insights.append("Creation task detected")
    if 'analyze' in task.lower():
        insights.append("Analysis required")
    if 'research' in task.lower():
        insights.append("Research component needed")
    
    # Determine next steps
    next_steps = []
    if any(word in task.lower() for word in ['research', 'find', 'search']):
        next_steps.append('perplexity_research')
    if any(word in task.lower() for word in ['create', 'build', 'develop']):
        next_steps.append('builder_execution')
    if any(word in task.lower() for word in ['meeting', 'discussion', 'call']):
        next_steps.append('attendee_analysis')
    
    return {
        **state,
        'reasoning_result': reasoning_result,
        'reasoning_confidence': confidence,
        'insights': insights,
        'next_steps': next_steps,
        'reasoning_timestamp': time.time()
    }

# Optimized Research Node
@precheck_node('research')
@cached_node(ttl=3600, cache_key_fn=smart_cache_key)  # Longer cache for research
def optimized_research_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Optimized research node with precheck and caching
    """
    query = state.get('query', state.get('question', ''))
    research_type = state.get('research_type', 'general')
    simplified = state.get('simplified', False)
    
    print(f"🔍 Executing research for: {query[:50]}...")
    
    # Simulate research based on type and complexity
    if simplified:
        time.sleep(1.0)
        research_result = f"Quick search results for: {query}"
        sources = ["Quick source 1", "Quick source 2"]
        confidence = 0.6
    else:
        research_time = {
            'academic': 5.0,
            'technical': 3.0,
            'news': 2.0,
            'general': 2.5
        }
        time.sleep(research_time.get(research_type, 2.5))
        
        research_result = f"Comprehensive research on: {query}"
        sources = [
            f"Academic paper on {query}",
            f"Technical documentation for {query}",
            f"Recent news about {query}",
            f"Expert analysis of {query}"
        ]
        confidence = 0.85
    
    # Extract key findings
    findings = []
    if 'AI' in query or 'artificial intelligence' in query.lower():
        findings.append("AI technology is rapidly evolving")
    if 'market' in query.lower():
        findings.append("Market trends show significant growth")
    if 'technology' in query.lower():
        findings.append("Technology adoption is accelerating")
    
    return {
        **state,
        'research_result': research_result,
        'research_confidence': confidence,
        'sources': sources,
        'findings': findings,
        'research_type': research_type,
        'research_timestamp': time.time()
    }

# Optimized Builder Node
@precheck_node('building')
@cached_node(ttl=1200, cache_key_fn=smart_cache_key)  # Medium cache for builds
def optimized_builder_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Optimized builder node with precheck and caching
    """
    task = state.get('task', '')
    project_type = state.get('project_type', 'web')
    requirements = state.get('requirements', [])
    simplified = state.get('simplified', False)
    
    print(f"🏗️ Executing build for: {task[:50]}...")
    
    # Use template if available
    if state.get('precheck_result', {}).get('alternative_path') == 'template_based':
        time.sleep(1.0)
        build_result = f"Created {project_type} project from template"
        files_created = [f"template_{project_type}.html", "template_styles.css"]
        confidence = 0.8
    elif simplified:
        time.sleep(2.0)
        build_result = f"Basic {project_type} project created"
        files_created = [f"basic_{project_type}.html"]
        confidence = 0.7
    else:
        # Full build
        build_time = {
            'web': 4.0,
            'mobile': 6.0,
            'desktop': 5.0,
            'api': 3.0,
            'document': 2.0
        }
        time.sleep(build_time.get(project_type, 4.0))
        
        build_result = f"Complete {project_type} project created"
        files_created = [
            f"{project_type}_main.html",
            f"{project_type}_styles.css",
            f"{project_type}_script.js",
            f"{project_type}_config.json"
        ]
        confidence = 0.9
    
    # Add features based on requirements
    features = []
    for req in requirements:
        if 'responsive' in req.lower():
            features.append("Responsive design")
        if 'dark mode' in req.lower():
            features.append("Dark mode support")
        if 'api' in req.lower():
            features.append("API integration")
    
    return {
        **state,
        'build_result': build_result,
        'build_confidence': confidence,
        'files_created': files_created,
        'features': features,
        'project_type': project_type,
        'build_timestamp': time.time()
    }

# Optimized Complete MCP Agent
@cached_node(ttl=600, cache_key_fn=smart_cache_key)  # Shorter cache for orchestration
def optimized_complete_mcp_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Optimized complete MCP agent with intelligent routing
    """
    task = state.get('task', '')
    
    print(f"🎯 MCP Agent orchestrating: {task[:50]}...")
    
    # Start with reasoning
    state = optimized_reasoning_node(state)
    
    # Check if we should skip further processing
    if state.get('skipped', False):
        return {
            **state,
            'final_result': state.get('result', 'Task was skipped'),
            'agent_path': ['reasoning_skipped']
        }
    
    agent_path = ['reasoning']
    
    # Execute next steps based on reasoning
    next_steps = state.get('next_steps', [])
    
    if 'perplexity_research' in next_steps:
        # Add research query to state
        state['query'] = task
        state = optimized_research_node(state)
        agent_path.append('research')
    
    if 'builder_execution' in next_steps:
        # Determine project type from task
        if 'web' in task.lower() or 'website' in task.lower():
            state['project_type'] = 'web'
        elif 'app' in task.lower():
            state['project_type'] = 'mobile'
        elif 'api' in task.lower():
            state['project_type'] = 'api'
        elif 'document' in task.lower() or 'report' in task.lower():
            state['project_type'] = 'document'
        
        state = optimized_builder_node(state)
        agent_path.append('builder')
    
    # Compile final result
    final_result = {
        'reasoning': state.get('reasoning_result', ''),
        'research': state.get('research_result', ''),
        'build': state.get('build_result', ''),
        'confidence': min([
            state.get('reasoning_confidence', 1.0),
            state.get('research_confidence', 1.0),
            state.get('build_confidence', 1.0)
        ])
    }
    
    return {
        **state,
        'final_result': final_result,
        'agent_path': agent_path,
        'completion_timestamp': time.time()
    }

# Conditional routing functions
def should_use_research(state: Dict[str, Any]) -> str:
    """Determine if research is needed"""
    next_steps = state.get('next_steps', [])
    precheck_result = state.get('precheck_result')
    
    if precheck_result and precheck_result.decision == PrecheckDecision.SKIP:
        return "skip_research"
    
    if 'perplexity_research' in next_steps:
        return "execute_research"
    
    return "skip_research"

def should_use_builder(state: Dict[str, Any]) -> str:
    """Determine if builder is needed"""
    next_steps = state.get('next_steps', [])
    precheck_result = state.get('precheck_result')
    
    if precheck_result and precheck_result.decision == PrecheckDecision.SKIP:
        return "skip_builder"
    
    if 'builder_execution' in next_steps:
        return "execute_builder"
    
    return "skip_builder"

def should_apply_contradiction(state: Dict[str, Any]) -> str:
    """Determine if contradiction should be applied"""
    final_result = state.get('final_result', {})
    
    if isinstance(final_result, dict):
        confidence = final_result.get('confidence', 1.0)
    else:
        confidence = 0.8  # Default confidence
    
    # Apply contradiction if confidence is low
    if confidence < 0.7:
        return "apply_contradiction"
    
    return "skip_contradiction"

# Performance monitoring
def get_optimization_stats() -> Dict[str, Any]:
    """Get optimization statistics"""
    from langgraph_system.utils.intelligent_cache import get_cache_stats
    from langgraph_system.utils.conditional_precheck import get_precheck_stats
    
    cache_stats = get_cache_stats()
    precheck_stats = get_precheck_stats()
    
    return {
        'cache': cache_stats,
        'precheck': precheck_stats,
        'optimization_summary': {
            'cache_hit_rate': cache_stats.get('hit_rate', 0),
            'operations_skipped': precheck_stats.get('decision_distribution', {}).get('skip', 0),
            'operations_simplified': precheck_stats.get('decision_distribution', {}).get('simplified', 0),
            'total_cost_saved': precheck_stats.get('total_estimated_cost', 0) * 0.3  # Estimated savings
        }
    }

# Example usage and testing
if __name__ == "__main__":
    # Test optimization with different scenarios
    test_cases = [
        {
            'task': 'Create a landing page for an AI startup',
            'description': 'Complex task requiring research and building'
        },
        {
            'task': 'What is machine learning?',
            'description': 'Simple query that should be simplified'
        },
        {
            'task': 'hi',
            'description': 'Greeting that should be skipped'
        },
        {
            'task': 'Create a comprehensive analysis of global AI trends with detailed market research and implementation roadmap',
            'description': 'Very complex task that might be delegated'
        }
    ]
    
    print("🚀 Testing Optimized MCP System\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"--- Test Case {i}: {test_case['description']} ---")
        print(f"Task: {test_case['task']}")
        
        start_time = time.time()
        result = optimized_complete_mcp_agent(test_case)
        execution_time = time.time() - start_time
        
        print(f"Execution time: {execution_time:.2f}s")
        print(f"Agent path: {result.get('agent_path', [])}")
        print(f"Skipped: {result.get('skipped', False)}")
        print(f"From cache: {result.get('from_cache', False)}")
        print()
    
    # Show optimization statistics
    print("📊 Optimization Statistics:")
    stats = get_optimization_stats()
    print(f"Cache hit rate: {stats['optimization_summary']['cache_hit_rate']:.2%}")
    print(f"Operations skipped: {stats['optimization_summary']['operations_skipped']}")
    print(f"Operations simplified: {stats['optimization_summary']['operations_simplified']}")
    print(f"Estimated cost saved: ${stats['optimization_summary']['total_cost_saved']:.3f}")

