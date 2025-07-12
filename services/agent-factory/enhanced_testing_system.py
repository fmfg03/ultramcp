"""
UltraMCP Enhanced Agent Testing System
Integration of LangWatch patterns with Scenario-CoD Protocol

Combines:
- LangWatch's multi-agent testing architecture
- UltraMCP's Chain-of-Debate Protocol
- Scenario framework's conversation engineering
- Real-time agent quality assessment
"""

import asyncio
import pytest
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import httpx
from pydantic import BaseModel

# UltraMCP Service URLs
ULTRAMCP_COD_URL = "http://ultramcp-cod-service:8001"
ULTRAMCP_LOCAL_MODELS_URL = "http://ultramcp-local-models-orchestrator:8012"
ULTRAMCP_SCENARIO_URL = "http://ultramcp-scenario-testing:8013"


class TestResult(Enum):
    """Test result states"""
    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"
    PENDING = "pending"


class AgentTestType(Enum):
    """Types of agent tests"""
    FUNCTIONAL = "functional"
    CONVERSATION = "conversation"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    DEBATE = "debate"
    SCENARIO = "scenario"
    TECHNICAL = "technical"
    RESEARCH = "research"
    CREATIVE = "creative"
    BUSINESS = "business"


@dataclass
class TestCriteria:
    """Testing criteria following LangWatch patterns"""
    name: str
    description: str
    weight: float = 1.0
    threshold: float = 0.75
    required: bool = True


@dataclass
class TestScenario:
    """Enhanced test scenario with UltraMCP integration"""
    name: str
    description: str
    scenario_type: AgentTestType
    criteria: List[TestCriteria]
    context: Dict[str, Any]
    expected_capabilities: List[str]
    debate_topics: Optional[List[str]] = None
    conversation_turns: int = 10
    timeout_seconds: int = 300


@dataclass
class AgentTestResult:
    """Comprehensive test result"""
    test_id: str
    agent_id: str
    scenario: TestScenario
    result: TestResult
    score: float
    criteria_scores: Dict[str, float]
    conversation_log: List[Dict[str, Any]]
    debate_consensus: Optional[Dict[str, Any]]
    execution_time: float
    timestamp: datetime
    error_details: Optional[str] = None


class UltraMCPAgentAdapter:
    """Adapter for testing UltraMCP agents with LangWatch patterns"""
    
    def __init__(self, agent_id: str, agent_config: Dict[str, Any]):
        self.agent_id = agent_id
        self.agent_config = agent_config
        self.conversation_history = []
    
    async def call(self, input_message: str, context: Dict[str, Any] = None) -> str:
        """Call agent with conversation context"""
        try:
            # Add to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": input_message,
                "timestamp": datetime.now().isoformat()
            })
            
            # Determine model based on agent config
            model_config = self.agent_config.get("models", {})
            primary_model = model_config.get("primary", "local:qwen2.5:14b")
            
            # Call local models orchestrator
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{ULTRAMCP_LOCAL_MODELS_URL}/generate",
                    json={
                        "prompt": input_message,
                        "model": primary_model,
                        "context": context or {},
                        "conversation_history": self.conversation_history[-5:],  # Last 5 turns
                        "agent_config": self.agent_config
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    agent_response = result.get("response", "")
                    
                    # Add to conversation history
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": agent_response,
                        "timestamp": datetime.now().isoformat(),
                        "model": primary_model
                    })
                    
                    return agent_response
                else:
                    raise Exception(f"Agent call failed: {response.text}")
                    
        except Exception as e:
            error_msg = f"Agent adapter error: {str(e)}"
            self.conversation_history.append({
                "role": "error",
                "content": error_msg,
                "timestamp": datetime.now().isoformat()
            })
            return error_msg


class UserSimulatorAgent:
    """User simulator following LangWatch patterns with UltraMCP enhancement"""
    
    def __init__(self, scenario: TestScenario):
        self.scenario = scenario
        self.conversation_state = {}
        self.turn_count = 0
    
    async def generate_user_input(self, conversation_history: List[Dict[str, Any]]) -> str:
        """Generate realistic user input based on scenario"""
        try:
            # Use local models for user simulation
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{ULTRAMCP_LOCAL_MODELS_URL}/generate",
                    json={
                        "prompt": self._build_user_simulation_prompt(conversation_history),
                        "model": "local:llama3.1:8b",
                        "task_type": "user_simulation",
                        "max_tokens": 150
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "I need help with this issue.")
                else:
                    return "I need help with this issue."
                    
        except Exception as e:
            return f"Test user input for {self.scenario.name}"
    
    def _build_user_simulation_prompt(self, conversation_history: List[Dict[str, Any]]) -> str:
        """Build prompt for user simulation"""
        return f"""
You are simulating a user in this scenario: {self.scenario.description}

Context: {json.dumps(self.scenario.context, indent=2)}

Conversation so far:
{json.dumps(conversation_history[-3:], indent=2)}

Turn {self.turn_count + 1} of {self.scenario.conversation_turns}

Generate a realistic user response that:
1. Stays in character for this scenario
2. Tests the agent's capabilities
3. Progresses the conversation naturally
4. Challenges the agent appropriately

User response:"""


class JudgeAgent:
    """Enhanced judge agent combining LangWatch patterns with CoD Protocol"""
    
    def __init__(self, criteria: List[TestCriteria], use_cod_protocol: bool = True):
        self.criteria = criteria
        self.use_cod_protocol = use_cod_protocol
        self.evaluation_history = []
    
    async def evaluate_turn(self, conversation_turn: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, float]:
        """Evaluate a single conversation turn"""
        try:
            if self.use_cod_protocol:
                return await self._evaluate_with_cod(conversation_turn, context)
            else:
                return await self._evaluate_direct(conversation_turn, context)
                
        except Exception as e:
            print(f"Judge evaluation error: {e}")
            return {criterion.name: 0.5 for criterion in self.criteria}
    
    async def _evaluate_with_cod(self, conversation_turn: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, float]:
        """Evaluate using Chain-of-Debate Protocol for enhanced accuracy"""
        try:
            # Build debate topic for this evaluation
            debate_topic = f"""
Evaluate this agent conversation turn against quality criteria:

Conversation Turn:
{json.dumps(conversation_turn, indent=2)}

Context: {json.dumps(context, indent=2)}

Criteria to evaluate:
{json.dumps([asdict(c) for c in self.criteria], indent=2)}

Debate Question: How well does this agent response meet each criterion? 
Provide scores from 0.0 to 1.0 for each criterion with detailed reasoning.
"""

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{ULTRAMCP_COD_URL}/debate",
                    json={
                        "topic": debate_topic,
                        "participants": ["local:qwen2.5:14b", "local:llama3.1:8b", "local:deepseek-coder:6.7b"],
                        "rounds": 2,
                        "mode": "quality_assessment",
                        "context": context
                    }
                )
                
                if response.status_code == 200:
                    debate_result = response.json()
                    consensus = debate_result.get("consensus", {})
                    
                    # Extract scores from consensus
                    scores = {}
                    for criterion in self.criteria:
                        score = self._extract_score_from_consensus(consensus, criterion.name)
                        scores[criterion.name] = max(0.0, min(1.0, score))
                    
                    return scores
                else:
                    return await self._evaluate_direct(conversation_turn, context)
                    
        except Exception as e:
            print(f"CoD evaluation error: {e}")
            return await self._evaluate_direct(conversation_turn, context)
    
    async def _evaluate_direct(self, conversation_turn: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, float]:
        """Direct evaluation without CoD Protocol"""
        try:
            evaluation_prompt = f"""
Evaluate this agent conversation turn against the criteria:

Turn: {json.dumps(conversation_turn, indent=2)}
Context: {json.dumps(context, indent=2)}

Criteria:
{json.dumps([asdict(c) for c in self.criteria], indent=2)}

Provide a JSON response with scores (0.0-1.0) for each criterion:
{{"criterion_name": score, ...}}
"""

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{ULTRAMCP_LOCAL_MODELS_URL}/generate",
                    json={
                        "prompt": evaluation_prompt,
                        "model": "local:qwen2.5:14b",
                        "task_type": "evaluation",
                        "max_tokens": 500
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    evaluation_text = result.get("response", "{}")
                    
                    try:
                        scores = json.loads(evaluation_text)
                        return {criterion.name: scores.get(criterion.name, 0.5) for criterion in self.criteria}
                    except:
                        return {criterion.name: 0.5 for criterion in self.criteria}
                else:
                    return {criterion.name: 0.5 for criterion in self.criteria}
                    
        except Exception as e:
            print(f"Direct evaluation error: {e}")
            return {criterion.name: 0.5 for criterion in self.criteria}
    
    def _extract_score_from_consensus(self, consensus: Dict[str, Any], criterion_name: str) -> float:
        """Extract numerical score from CoD consensus"""
        try:
            consensus_text = consensus.get("summary", "").lower()
            
            # Look for score patterns in consensus
            import re
            
            # Pattern 1: "criterion_name: 0.8" or "criterion_name score: 0.8"
            pattern1 = rf"{criterion_name.lower()}[:\s]*(\d*\.?\d+)"
            match1 = re.search(pattern1, consensus_text)
            if match1:
                return float(match1.group(1))
            
            # Pattern 2: General score extraction
            score_patterns = [r"(\d\.\d+)", r"(\d+)%", r"score[:\s]*(\d*\.?\d+)"]
            for pattern in score_patterns:
                matches = re.findall(pattern, consensus_text)
                if matches:
                    score = float(matches[0])
                    return score / 100 if score > 1 else score
            
            return 0.5  # Default score
            
        except Exception:
            return 0.5


class EnhancedAgentTester:
    """Main testing orchestrator combining LangWatch + UltraMCP approaches"""
    
    def __init__(self):
        self.test_results = []
        self.active_tests = {}
    
    async def run_comprehensive_test(self, agent_id: str, agent_config: Dict[str, Any], 
                                   test_scenarios: List[TestScenario]) -> List[AgentTestResult]:
        """Run comprehensive agent testing with multiple scenarios"""
        results = []
        
        for scenario in test_scenarios:
            print(f"🧪 Running scenario: {scenario.name}")
            
            try:
                result = await self._run_single_scenario(agent_id, agent_config, scenario)
                results.append(result)
                self.test_results.append(result)
                
                print(f"✅ Scenario '{scenario.name}' completed - Score: {result.score:.2f}")
                
            except Exception as e:
                print(f"❌ Scenario '{scenario.name}' failed: {e}")
                
                # Create failed result
                failed_result = AgentTestResult(
                    test_id=str(uuid.uuid4()),
                    agent_id=agent_id,
                    scenario=scenario,
                    result=TestResult.FAIL,
                    score=0.0,
                    criteria_scores={},
                    conversation_log=[],
                    debate_consensus=None,
                    execution_time=0.0,
                    timestamp=datetime.now(),
                    error_details=str(e)
                )
                results.append(failed_result)
                self.test_results.append(failed_result)
        
        return results
    
    async def _run_single_scenario(self, agent_id: str, agent_config: Dict[str, Any], 
                                 scenario: TestScenario) -> AgentTestResult:
        """Run a single test scenario"""
        start_time = asyncio.get_event_loop().time()
        test_id = str(uuid.uuid4())
        
        # Initialize agents
        agent = UltraMCPAgentAdapter(agent_id, agent_config)
        user_simulator = UserSimulatorAgent(scenario)
        judge = JudgeAgent(scenario.criteria, use_cod_protocol=True)
        
        # Track conversation
        conversation_log = []
        criteria_scores_per_turn = []
        
        # Run conversation turns
        for turn in range(scenario.conversation_turns):
            try:
                # Generate user input
                user_input = await user_simulator.generate_user_input(conversation_log)
                
                # Get agent response
                agent_response = await agent.call(user_input, scenario.context)
                
                # Log turn
                turn_data = {
                    "turn": turn + 1,
                    "user_input": user_input,
                    "agent_response": agent_response,
                    "timestamp": datetime.now().isoformat()
                }
                conversation_log.append(turn_data)
                
                # Judge evaluation
                turn_scores = await judge.evaluate_turn(turn_data, scenario.context)
                criteria_scores_per_turn.append(turn_scores)
                
                user_simulator.turn_count = turn + 1
                
            except Exception as e:
                print(f"Turn {turn + 1} failed: {e}")
                break
        
        # Calculate final scores
        final_scores = self._calculate_final_scores(criteria_scores_per_turn, scenario.criteria)
        overall_score = self._calculate_overall_score(final_scores, scenario.criteria)
        
        # Determine result
        result_status = TestResult.PASS if overall_score >= 0.75 else TestResult.FAIL
        if 0.5 <= overall_score < 0.75:
            result_status = TestResult.PARTIAL
        
        # Optional: Run debate consensus for final evaluation
        debate_consensus = None
        if scenario.debate_topics:
            debate_consensus = await self._run_debate_evaluation(agent_id, scenario, conversation_log)
        
        execution_time = asyncio.get_event_loop().time() - start_time
        
        return AgentTestResult(
            test_id=test_id,
            agent_id=agent_id,
            scenario=scenario,
            result=result_status,
            score=overall_score,
            criteria_scores=final_scores,
            conversation_log=conversation_log,
            debate_consensus=debate_consensus,
            execution_time=execution_time,
            timestamp=datetime.now()
        )
    
    def _calculate_final_scores(self, scores_per_turn: List[Dict[str, float]], 
                              criteria: List[TestCriteria]) -> Dict[str, float]:
        """Calculate final scores across all turns"""
        final_scores = {}
        
        for criterion in criteria:
            scores = [turn_scores.get(criterion.name, 0.0) for turn_scores in scores_per_turn]
            if scores:
                # Use weighted average with more weight on later turns
                weights = [i + 1 for i in range(len(scores))]
                weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
                total_weight = sum(weights)
                final_scores[criterion.name] = weighted_sum / total_weight if total_weight > 0 else 0.0
            else:
                final_scores[criterion.name] = 0.0
        
        return final_scores
    
    def _calculate_overall_score(self, final_scores: Dict[str, float], 
                               criteria: List[TestCriteria]) -> float:
        """Calculate weighted overall score"""
        total_weight = sum(criterion.weight for criterion in criteria)
        if total_weight == 0:
            return 0.0
        
        weighted_sum = sum(
            final_scores.get(criterion.name, 0.0) * criterion.weight 
            for criterion in criteria
        )
        
        return weighted_sum / total_weight
    
    async def _run_debate_evaluation(self, agent_id: str, scenario: TestScenario, 
                                   conversation_log: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run Chain-of-Debate Protocol for final agent evaluation"""
        try:
            debate_topic = f"""
Final evaluation of agent {agent_id} in scenario: {scenario.name}

Scenario Description: {scenario.description}

Full Conversation:
{json.dumps(conversation_log, indent=2)}

Debate Question: Based on this complete conversation, how well did the agent perform?
Consider: effectiveness, accuracy, user experience, goal achievement, and overall quality.

Provide a consensus evaluation with specific strengths, weaknesses, and recommendations.
"""

            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    f"{ULTRAMCP_COD_URL}/debate",
                    json={
                        "topic": debate_topic,
                        "participants": ["local:qwen2.5:14b", "local:llama3.1:8b", "local:deepseek-coder:6.7b"],
                        "rounds": 3,
                        "mode": "agent_evaluation",
                        "context": {"agent_id": agent_id, "scenario": scenario.name}
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": "Debate evaluation failed"}
                    
        except Exception as e:
            return {"error": f"Debate evaluation error: {str(e)}"}


# Pytest Integration Decorators (LangWatch Pattern)
def agent_test(scenario_name: str):
    """Decorator for agent tests following LangWatch patterns"""
    def decorator(func):
        func._agent_test = True
        func._scenario_name = scenario_name
        return pytest.mark.asyncio(func)
    return decorator


def concurrent_agent_test(group: str):
    """Decorator for concurrent agent testing"""
    def decorator(func):
        func._concurrent_group = group
        return pytest.mark.asyncio_concurrent(group=group)(func)
    return decorator


# Test Configuration
class TestConfig:
    """Global test configuration"""
    DEFAULT_MODEL = "local:qwen2.5:14b"
    DEBUG_MODE = False
    TIMEOUT_SECONDS = 300
    MIN_CONVERSATION_TURNS = 5
    MAX_CONVERSATION_TURNS = 15
    QUALITY_THRESHOLD = 0.75


# Predefined Test Scenarios
PREDEFINED_SCENARIOS = {
    "customer_support": TestScenario(
        name="customer_support_basic",
        description="Customer with a product inquiry and potential complaint",
        scenario_type=AgentTestType.CONVERSATION,
        criteria=[
            TestCriteria("response_helpfulness", "Agent provides helpful responses", 1.0, 0.8),
            TestCriteria("query_understanding", "Agent understands customer queries", 1.0, 0.75),
            TestCriteria("escalation_appropriateness", "Agent escalates when needed", 0.8, 0.7),
            TestCriteria("solution_accuracy", "Agent provides accurate solutions", 1.2, 0.8),
            TestCriteria("conversation_flow", "Natural conversation progression", 0.8, 0.7)
        ],
        context={"customer_tier": "premium", "product": "software", "issue_complexity": "medium"},
        expected_capabilities=["query_knowledge_base", "escalate_to_human", "create_ticket"],
        debate_topics=["customer_satisfaction", "solution_effectiveness"],
        conversation_turns=8
    ),
    
    "research_analyst": TestScenario(
        name="research_analyst_market",
        description="Client requesting market research and analysis",
        scenario_type=AgentTestType.QUALITY,
        criteria=[
            TestCriteria("research_depth", "Provides comprehensive research", 1.2, 0.8),
            TestCriteria("source_credibility", "Uses credible sources", 1.0, 0.85),
            TestCriteria("analysis_quality", "High-quality analysis and insights", 1.2, 0.8),
            TestCriteria("presentation_clarity", "Clear presentation of findings", 0.8, 0.75),
            TestCriteria("recommendation_actionability", "Actionable recommendations", 1.0, 0.8)
        ],
        context={"industry": "technology", "market": "AI tools", "timeframe": "quarterly"},
        expected_capabilities=["web_research", "data_analysis", "report_generation"],
        debate_topics=["research_methodology", "market_insights_accuracy"],
        conversation_turns=10
    ),
    
    "code_reviewer": TestScenario(
        name="code_reviewer_security",
        description="Developer submitting code for security review",
        scenario_type=AgentTestType.TECHNICAL,
        criteria=[
            TestCriteria("security_issue_detection", "Identifies security vulnerabilities", 1.5, 0.9),
            TestCriteria("code_quality_assessment", "Evaluates code quality", 1.0, 0.8),
            TestCriteria("improvement_suggestions", "Provides actionable improvements", 1.0, 0.75),
            TestCriteria("explanation_clarity", "Clear explanations of issues", 0.8, 0.75),
            TestCriteria("best_practices_adherence", "Recommends best practices", 1.0, 0.8)
        ],
        context={"language": "python", "framework": "fastapi", "security_focus": "high"},
        expected_capabilities=["static_analysis", "security_scanning", "best_practices"],
        debate_topics=["security_assessment", "code_quality_standards"],
        conversation_turns=6
    )
}