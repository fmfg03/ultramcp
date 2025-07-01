"""
Conditional Precheck Node for LangGraph
Intelligent filtering before expensive operations
"""

import time
import re
from typing import Dict, Any, Optional, List, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
import hashlib

class ConfidenceLevel(Enum):
    """Confidence levels for precheck decisions"""
    VERY_LOW = 0.1
    LOW = 0.3
    MEDIUM = 0.5
    HIGH = 0.7
    VERY_HIGH = 0.9

class PrecheckDecision(Enum):
    """Precheck decision types"""
    EXECUTE = "execute"
    SKIP = "skip"
    CACHE_LOOKUP = "cache_lookup"
    SIMPLIFIED = "simplified"
    DELEGATE = "delegate"

@dataclass
class PrecheckResult:
    """Result of precheck analysis"""
    decision: PrecheckDecision
    confidence: float
    reasoning: str
    estimated_cost: float
    estimated_time: float
    alternative_path: Optional[str] = None
    metadata: Dict[str, Any] = None

class ConditionalPrechecker:
    """
    Intelligent precheck system for LangGraph nodes
    Analyzes inputs to determine if expensive operations are worthwhile
    """
    
    def __init__(self):
        self.patterns = self._load_patterns()
        self.cost_thresholds = self._load_cost_thresholds()
        self.entity_cache = {}
        self.decision_history = []
        
    def _load_patterns(self) -> Dict[str, Any]:
        """Load patterns for different types of analysis"""
        return {
            'simple_queries': [
                r'^(what|who|when|where|how)\s+is\s+\w+\??$',
                r'^(yes|no)\s*\??$',
                r'^(true|false)\s*\??$',
                r'^\d+\s*[\+\-\*\/]\s*\d+\s*\??$'
            ],
            'complex_queries': [
                r'analyze.*complex.*system',
                r'create.*comprehensive.*plan',
                r'develop.*full.*application',
                r'research.*multiple.*sources'
            ],
            'cached_patterns': [
                r'what.*current.*weather',
                r'latest.*news.*about',
                r'stock.*price.*for',
                r'definition.*of.*\w+'
            ],
            'high_confidence_skip': [
                r'^(hi|hello|hey)\s*$',
                r'^(thanks?|thank\s+you)\s*$',
                r'^(bye|goodbye)\s*$',
                r'^\s*$'  # Empty input
            ]
        }
    
    def _load_cost_thresholds(self) -> Dict[str, float]:
        """Load cost thresholds for different operations"""
        return {
            'reasoning_cost_threshold': 0.1,  # Skip if estimated cost > threshold
            'time_threshold': 30.0,  # Skip if estimated time > 30 seconds
            'confidence_threshold': 0.7,  # Execute if confidence > threshold
            'cache_hit_threshold': 0.8,  # Use cache if similarity > threshold
            'simplification_threshold': 0.6  # Use simplified version if appropriate
        }
    
    def precheck_reasoning(self, state: Dict[str, Any]) -> PrecheckResult:
        """
        Precheck for reasoning operations
        """
        task = state.get('task', state.get('query', state.get('question', '')))
        context = state.get('context', {})
        
        # Quick pattern matching
        pattern_result = self._check_patterns(task)
        if pattern_result:
            return pattern_result
        
        # Complexity analysis
        complexity = self._analyze_complexity(task, context)
        
        # Entity analysis
        entities = self._extract_entities(task)
        entity_confidence = self._analyze_entities(entities)
        
        # Cost estimation
        estimated_cost = self._estimate_reasoning_cost(task, complexity)
        estimated_time = self._estimate_reasoning_time(task, complexity)
        
        # Decision logic
        decision = self._make_reasoning_decision(
            complexity, entity_confidence, estimated_cost, estimated_time
        )
        
        return PrecheckResult(
            decision=decision.decision,
            confidence=decision.confidence,
            reasoning=decision.reasoning,
            estimated_cost=estimated_cost,
            estimated_time=estimated_time,
            alternative_path=decision.alternative_path,
            metadata={
                'complexity': complexity,
                'entities': entities,
                'entity_confidence': entity_confidence,
                'patterns_matched': pattern_result.metadata if pattern_result else {}
            }
        )
    
    def precheck_research(self, state: Dict[str, Any]) -> PrecheckResult:
        """
        Precheck for research operations
        """
        query = state.get('query', state.get('question', ''))
        research_type = state.get('research_type', 'general')
        
        # Check if query is research-worthy
        if len(query.strip()) < 10:
            return PrecheckResult(
                decision=PrecheckDecision.SKIP,
                confidence=0.9,
                reasoning="Query too short for meaningful research",
                estimated_cost=0.0,
                estimated_time=0.0
            )
        
        # Check for cached research
        cache_similarity = self._check_research_cache(query)
        if cache_similarity > self.cost_thresholds['cache_hit_threshold']:
            return PrecheckResult(
                decision=PrecheckDecision.CACHE_LOOKUP,
                confidence=cache_similarity,
                reasoning=f"Similar research found in cache (similarity: {cache_similarity:.2f})",
                estimated_cost=0.01,
                estimated_time=0.5
            )
        
        # Analyze research complexity
        complexity = self._analyze_research_complexity(query, research_type)
        estimated_cost = self._estimate_research_cost(query, research_type, complexity)
        estimated_time = self._estimate_research_time(query, research_type, complexity)
        
        # Check if research is worth the cost
        if estimated_cost > self.cost_thresholds['reasoning_cost_threshold'] * 5:  # Research is more expensive
            return PrecheckResult(
                decision=PrecheckDecision.SIMPLIFIED,
                confidence=0.6,
                reasoning=f"Research too expensive (${estimated_cost:.2f}), using simplified approach",
                estimated_cost=estimated_cost * 0.3,
                estimated_time=estimated_time * 0.3,
                alternative_path="simplified_research"
            )
        
        return PrecheckResult(
            decision=PrecheckDecision.EXECUTE,
            confidence=0.8,
            reasoning="Research query is valuable and cost-effective",
            estimated_cost=estimated_cost,
            estimated_time=estimated_time
        )
    
    def precheck_building(self, state: Dict[str, Any]) -> PrecheckResult:
        """
        Precheck for building/creation operations
        """
        task = state.get('task', '')
        requirements = state.get('requirements', [])
        project_type = state.get('project_type', 'unknown')
        
        # Analyze build complexity
        complexity = self._analyze_build_complexity(task, requirements, project_type)
        
        # Check for existing templates
        template_match = self._check_template_availability(task, project_type)
        if template_match:
            return PrecheckResult(
                decision=PrecheckDecision.SIMPLIFIED,
                confidence=0.85,
                reasoning=f"Template available: {template_match}",
                estimated_cost=0.05,
                estimated_time=5.0,
                alternative_path="template_based"
            )
        
        # Estimate resources needed
        estimated_cost = self._estimate_build_cost(complexity, project_type)
        estimated_time = self._estimate_build_time(complexity, project_type)
        
        # Check if build is feasible
        if estimated_time > 300:  # 5 minutes
            return PrecheckResult(
                decision=PrecheckDecision.DELEGATE,
                confidence=0.7,
                reasoning="Build too complex for single operation, should be delegated",
                estimated_cost=estimated_cost,
                estimated_time=estimated_time,
                alternative_path="multi_step_build"
            )
        
        return PrecheckResult(
            decision=PrecheckDecision.EXECUTE,
            confidence=0.8,
            reasoning="Build is feasible and worthwhile",
            estimated_cost=estimated_cost,
            estimated_time=estimated_time
        )
    
    def _check_patterns(self, text: str) -> Optional[PrecheckResult]:
        """Check text against known patterns"""
        text_lower = text.lower().strip()
        
        # Check for high-confidence skip patterns
        for pattern in self.patterns['high_confidence_skip']:
            if re.match(pattern, text_lower):
                return PrecheckResult(
                    decision=PrecheckDecision.SKIP,
                    confidence=0.95,
                    reasoning=f"Matched skip pattern: {pattern}",
                    estimated_cost=0.0,
                    estimated_time=0.0,
                    metadata={'pattern': pattern}
                )
        
        # Check for simple queries
        for pattern in self.patterns['simple_queries']:
            if re.match(pattern, text_lower):
                return PrecheckResult(
                    decision=PrecheckDecision.SIMPLIFIED,
                    confidence=0.8,
                    reasoning=f"Simple query detected: {pattern}",
                    estimated_cost=0.02,
                    estimated_time=2.0,
                    alternative_path="simple_lookup",
                    metadata={'pattern': pattern}
                )
        
        # Check for cached patterns
        for pattern in self.patterns['cached_patterns']:
            if re.search(pattern, text_lower):
                return PrecheckResult(
                    decision=PrecheckDecision.CACHE_LOOKUP,
                    confidence=0.85,
                    reasoning=f"Cacheable pattern detected: {pattern}",
                    estimated_cost=0.01,
                    estimated_time=0.5,
                    metadata={'pattern': pattern}
                )
        
        return None
    
    def _analyze_complexity(self, text: str, context: Dict[str, Any]) -> float:
        """Analyze complexity of a task/query"""
        complexity_score = 0.0
        
        # Length-based complexity
        complexity_score += min(len(text) / 1000, 0.3)
        
        # Keyword-based complexity
        complex_keywords = [
            'analyze', 'comprehensive', 'detailed', 'complex', 'multiple',
            'integrate', 'optimize', 'advanced', 'sophisticated', 'elaborate'
        ]
        
        for keyword in complex_keywords:
            if keyword in text.lower():
                complexity_score += 0.1
        
        # Context complexity
        if context:
            complexity_score += min(len(context) / 10, 0.2)
        
        # Multi-step indicators
        if any(word in text.lower() for word in ['first', 'then', 'next', 'finally', 'step']):
            complexity_score += 0.2
        
        return min(complexity_score, 1.0)
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract entities from text"""
        # Simple entity extraction (in production, use NER)
        entities = []
        
        # Extract capitalized words (potential proper nouns)
        words = re.findall(r'\b[A-Z][a-z]+\b', text)
        entities.extend(words)
        
        # Extract quoted strings
        quoted = re.findall(r'"([^"]*)"', text)
        entities.extend(quoted)
        
        # Extract URLs
        urls = re.findall(r'https?://[^\s]+', text)
        entities.extend(urls)
        
        return list(set(entities))
    
    def _analyze_entities(self, entities: List[str]) -> float:
        """Analyze confidence based on entities"""
        if not entities:
            return 0.5
        
        confidence = 0.0
        
        for entity in entities:
            # Check if entity is in cache
            if entity in self.entity_cache:
                confidence += 0.2
            else:
                # Unknown entity reduces confidence
                confidence -= 0.1
        
        return max(0.1, min(confidence / len(entities) + 0.5, 1.0))
    
    def _estimate_reasoning_cost(self, task: str, complexity: float) -> float:
        """Estimate cost of reasoning operation"""
        base_cost = 0.02  # Base cost in dollars
        complexity_multiplier = 1 + complexity * 2
        length_multiplier = 1 + len(task) / 10000
        
        return base_cost * complexity_multiplier * length_multiplier
    
    def _estimate_reasoning_time(self, task: str, complexity: float) -> float:
        """Estimate time for reasoning operation"""
        base_time = 3.0  # Base time in seconds
        complexity_multiplier = 1 + complexity * 3
        length_multiplier = 1 + len(task) / 5000
        
        return base_time * complexity_multiplier * length_multiplier
    
    def _check_research_cache(self, query: str) -> float:
        """Check similarity with cached research"""
        # Simple similarity check (in production, use embeddings)
        query_hash = hashlib.md5(query.lower().encode()).hexdigest()
        
        # Simulate cache lookup
        if query_hash in self.entity_cache:
            return 0.9
        
        # Check for similar queries (simplified)
        for cached_query in self.entity_cache.keys():
            if len(set(query.lower().split()) & set(cached_query.split())) > 2:
                return 0.7
        
        return 0.0
    
    def _analyze_research_complexity(self, query: str, research_type: str) -> float:
        """Analyze research complexity"""
        complexity = 0.0
        
        # Type-based complexity
        type_complexity = {
            'academic': 0.8,
            'technical': 0.7,
            'news': 0.3,
            'general': 0.5
        }
        complexity += type_complexity.get(research_type, 0.5)
        
        # Query complexity
        if len(query.split()) > 10:
            complexity += 0.2
        
        if any(word in query.lower() for word in ['compare', 'analyze', 'evaluate']):
            complexity += 0.3
        
        return min(complexity, 1.0)
    
    def _estimate_research_cost(self, query: str, research_type: str, complexity: float) -> float:
        """Estimate research cost"""
        base_cost = 0.05
        type_multiplier = {'academic': 2.0, 'technical': 1.5, 'news': 1.0, 'general': 1.2}
        
        return base_cost * type_multiplier.get(research_type, 1.0) * (1 + complexity)
    
    def _estimate_research_time(self, query: str, research_type: str, complexity: float) -> float:
        """Estimate research time"""
        base_time = 10.0
        type_multiplier = {'academic': 3.0, 'technical': 2.0, 'news': 1.0, 'general': 1.5}
        
        return base_time * type_multiplier.get(research_type, 1.0) * (1 + complexity)
    
    def _analyze_build_complexity(self, task: str, requirements: List[str], project_type: str) -> float:
        """Analyze build complexity"""
        complexity = 0.0
        
        # Project type complexity
        type_complexity = {
            'web': 0.6,
            'mobile': 0.8,
            'desktop': 0.7,
            'api': 0.5,
            'document': 0.3
        }
        complexity += type_complexity.get(project_type, 0.5)
        
        # Requirements complexity
        complexity += min(len(requirements) / 10, 0.3)
        
        # Task complexity
        if any(word in task.lower() for word in ['full', 'complete', 'comprehensive']):
            complexity += 0.2
        
        return min(complexity, 1.0)
    
    def _check_template_availability(self, task: str, project_type: str) -> Optional[str]:
        """Check if templates are available"""
        templates = {
            'web': ['landing_page', 'blog', 'portfolio', 'ecommerce'],
            'mobile': ['todo_app', 'weather_app', 'chat_app'],
            'document': ['report', 'proposal', 'manual']
        }
        
        project_templates = templates.get(project_type, [])
        
        for template in project_templates:
            if template.replace('_', ' ') in task.lower():
                return template
        
        return None
    
    def _estimate_build_cost(self, complexity: float, project_type: str) -> float:
        """Estimate build cost"""
        base_cost = 0.1
        type_multiplier = {'web': 1.0, 'mobile': 1.5, 'desktop': 1.3, 'api': 0.8, 'document': 0.5}
        
        return base_cost * type_multiplier.get(project_type, 1.0) * (1 + complexity * 2)
    
    def _estimate_build_time(self, complexity: float, project_type: str) -> float:
        """Estimate build time"""
        base_time = 30.0
        type_multiplier = {'web': 1.0, 'mobile': 2.0, 'desktop': 1.5, 'api': 0.8, 'document': 0.5}
        
        return base_time * type_multiplier.get(project_type, 1.0) * (1 + complexity * 3)
    
    def _make_reasoning_decision(self, complexity: float, entity_confidence: float, 
                               estimated_cost: float, estimated_time: float) -> PrecheckResult:
        """Make final decision for reasoning operations"""
        
        # High complexity + low confidence = skip or simplify
        if complexity > 0.8 and entity_confidence < 0.3:
            return PrecheckResult(
                decision=PrecheckDecision.SKIP,
                confidence=0.8,
                reasoning="High complexity with low entity confidence",
                estimated_cost=0.0,
                estimated_time=0.0
            )
        
        # High cost = simplify
        if estimated_cost > self.cost_thresholds['reasoning_cost_threshold']:
            return PrecheckResult(
                decision=PrecheckDecision.SIMPLIFIED,
                confidence=0.7,
                reasoning=f"Cost too high (${estimated_cost:.3f}), using simplified approach",
                estimated_cost=estimated_cost * 0.5,
                estimated_time=estimated_time * 0.5,
                alternative_path="simplified_reasoning"
            )
        
        # High time = delegate
        if estimated_time > self.cost_thresholds['time_threshold']:
            return PrecheckResult(
                decision=PrecheckDecision.DELEGATE,
                confidence=0.6,
                reasoning=f"Time too long ({estimated_time:.1f}s), should delegate",
                estimated_cost=estimated_cost,
                estimated_time=estimated_time,
                alternative_path="multi_step_reasoning"
            )
        
        # Default: execute
        return PrecheckResult(
            decision=PrecheckDecision.EXECUTE,
            confidence=0.8,
            reasoning="Task is suitable for direct execution",
            estimated_cost=estimated_cost,
            estimated_time=estimated_time
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get precheck statistics"""
        if not self.decision_history:
            return {'total_decisions': 0}
        
        decisions = [d.decision for d in self.decision_history]
        decision_counts = {d.value: decisions.count(d) for d in PrecheckDecision}
        
        return {
            'total_decisions': len(self.decision_history),
            'decision_distribution': decision_counts,
            'avg_confidence': sum(d.confidence for d in self.decision_history) / len(self.decision_history),
            'total_estimated_cost': sum(d.estimated_cost for d in self.decision_history),
            'total_estimated_time': sum(d.estimated_time for d in self.decision_history)
        }

# Global precheck instance
_global_prechecker = ConditionalPrechecker()

def precheck_node(node_type: str = 'reasoning'):
    """
    Decorator for adding precheck to LangGraph nodes
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(state: Dict[str, Any], *args, **kwargs) -> Dict[str, Any]:
            # Perform precheck
            if node_type == 'reasoning':
                precheck_result = _global_prechecker.precheck_reasoning(state)
            elif node_type == 'research':
                precheck_result = _global_prechecker.precheck_research(state)
            elif node_type == 'building':
                precheck_result = _global_prechecker.precheck_building(state)
            else:
                # Default to reasoning precheck
                precheck_result = _global_prechecker.precheck_reasoning(state)
            
            # Add precheck result to state
            state['precheck_result'] = precheck_result
            
            # Record decision
            _global_prechecker.decision_history.append(precheck_result)
            
            # Act on decision
            if precheck_result.decision == PrecheckDecision.SKIP:
                print(f"⏭️ SKIPPING {func.__name__}: {precheck_result.reasoning}")
                return {
                    **state,
                    'result': f"Skipped: {precheck_result.reasoning}",
                    'skipped': True
                }
            
            elif precheck_result.decision == PrecheckDecision.CACHE_LOOKUP:
                print(f"🎯 CACHE LOOKUP for {func.__name__}: {precheck_result.reasoning}")
                # In a real implementation, this would do cache lookup
                return {
                    **state,
                    'result': f"Cache lookup: {precheck_result.reasoning}",
                    'from_cache': True
                }
            
            elif precheck_result.decision == PrecheckDecision.SIMPLIFIED:
                print(f"⚡ SIMPLIFIED {func.__name__}: {precheck_result.reasoning}")
                # Execute simplified version
                state['simplified'] = True
                return func(state, *args, **kwargs)
            
            elif precheck_result.decision == PrecheckDecision.DELEGATE:
                print(f"🔄 DELEGATING {func.__name__}: {precheck_result.reasoning}")
                return {
                    **state,
                    'result': f"Delegated: {precheck_result.reasoning}",
                    'delegated': True,
                    'alternative_path': precheck_result.alternative_path
                }
            
            else:  # EXECUTE
                print(f"✅ EXECUTING {func.__name__}: {precheck_result.reasoning}")
                return func(state, *args, **kwargs)
        
        return wrapper
    return decorator

# Utility functions
def get_precheck_stats() -> Dict[str, Any]:
    """Get precheck statistics"""
    return _global_prechecker.get_stats()

def reset_precheck_history():
    """Reset precheck decision history"""
    _global_prechecker.decision_history.clear()

# Example usage
if __name__ == "__main__":
    # Example precheck usage
    @precheck_node('reasoning')
    def reasoning_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Example reasoning node with precheck"""
        task = state.get('task', '')
        
        if state.get('simplified', False):
            result = f"Simple analysis of: {task}"
        else:
            result = f"Comprehensive analysis of: {task}"
        
        return {
            **state,
            'reasoning_result': result
        }
    
    # Test different scenarios
    test_cases = [
        {'task': 'hi'},  # Should skip
        {'task': 'what is AI?'},  # Should simplify
        {'task': 'Create a comprehensive analysis of the global economic impact of artificial intelligence on developing nations'},  # Should delegate
        {'task': 'Analyze the user feedback'},  # Should execute
    ]
    
    for i, test_state in enumerate(test_cases):
        print(f"\n--- Test Case {i+1} ---")
        result = reasoning_node(test_state)
        print(f"Result: {result.get('result', result.get('reasoning_result', 'No result'))}")
    
    print(f"\nPrecheck Stats: {get_precheck_stats()}")

