"""
Test Scenarios for Chain-of-Debate Quality Assurance
Comprehensive test suite for validating debate quality and agent behavior
"""

import asyncio
import pytest
from typing import List, Dict, Any
import structlog

# Import from scenario framework
import sys
sys.path.append('/root/scenario/python')
import scenario

# Import our CoD adapters
from cod_agent_adapter import CoDAgentAdapter, CoDModeratorAdapter, CoDUserSimulator, DebatePosition
from cod_judge_system import CoDJudgeAgent, JudgmentCriteria

logger = structlog.get_logger(__name__)


class CoDTestSuite:
    """Comprehensive test suite for Chain-of-Debate system"""
    
    def __init__(self, cod_service_url: str = "http://localhost:8001"):
        self.cod_service_url = cod_service_url
        self.setup_scenario_config()
    
    def setup_scenario_config(self):
        """Configure scenario framework for CoD testing"""
        scenario.configure(
            default_model="openai/gpt-4-turbo",
            max_turns=30,
            verbose=True,
            cache_key="cod-test-suite-v1.0",
            debug=False
        )
    
    async def run_basic_debate_test(self) -> Dict[str, Any]:
        """Test basic two-agent debate functionality"""
        logger.info("Running basic debate test")
        
        result = await scenario.run(
            name="basic-two-agent-debate",
            description="Test basic debate between two agents with opposing positions",
            agents=[
                CoDAgentAdapter(
                    agent_id="climate_advocate",
                    position=DebatePosition.PRO,
                    cod_service_url=self.cod_service_url,
                    config={"evidence_required": True}
                ),
                CoDAgentAdapter(
                    agent_id="climate_skeptic", 
                    position=DebatePosition.CON,
                    cod_service_url=self.cod_service_url,
                    config={"evidence_required": True}
                ),
                CoDUserSimulator(topics=["climate change policy effectiveness"]),
                CoDJudgeAgent(
                    criteria=[
                        JudgmentCriteria.LOGICAL_CONSISTENCY,
                        JudgmentCriteria.ARGUMENT_STRUCTURE,
                        JudgmentCriteria.EVIDENCE_QUALITY
                    ],
                    quality_threshold=0.6
                )
            ],
            script=[
                scenario.user("Let's debate whether aggressive climate policies are more effective than market-based solutions."),
                scenario.agent(),  # Pro position
                scenario.agent(),  # Con position
                scenario.proceed(turns=4),  # Allow natural flow for 4 turns
                self.validate_argument_quality,
                scenario.judge()
            ],
            max_turns=15
        )
        
        return {
            "test_name": "basic-two-agent-debate",
            "success": result.success,
            "reason": result.reason,
            "metrics": result.metadata.get("cod_quality_metrics", {}),
            "message_count": len(result.scenario_state.messages) if hasattr(result, 'scenario_state') else 0
        }
    
    async def run_moderated_debate_test(self) -> Dict[str, Any]:
        """Test three-agent debate with moderator"""
        logger.info("Running moderated debate test")
        
        result = await scenario.run(
            name="moderated-three-agent-debate",
            description="Test moderated debate with synthesis generation",
            agents=[
                CoDAgentAdapter(
                    agent_id="ubi_supporter",
                    position=DebatePosition.PRO,
                    cod_service_url=self.cod_service_url
                ),
                CoDAgentAdapter(
                    agent_id="ubi_opponent",
                    position=DebatePosition.CON,
                    cod_service_url=self.cod_service_url
                ),
                CoDModeratorAdapter(
                    agent_id="debate_moderator",
                    cod_service_url=self.cod_service_url
                ),
                CoDUserSimulator(topics=["universal basic income implementation"]),
                CoDJudgeAgent(
                    criteria=[
                        JudgmentCriteria.LOGICAL_CONSISTENCY,
                        JudgmentCriteria.EVIDENCE_QUALITY,
                        JudgmentCriteria.CONSENSUS_BUILDING,
                        JudgmentCriteria.RESPONSE_RELEVANCE
                    ],
                    quality_threshold=0.65
                )
            ],
            script=[
                scenario.user("I want to explore different perspectives on implementing universal basic income."),
                scenario.agent(),  # Pro UBI
                scenario.agent(),  # Con UBI
                scenario.agent(),  # Moderator response
                scenario.proceed(turns=6),
                self.validate_moderator_synthesis,
                scenario.judge()
            ],
            max_turns=20
        )
        
        return {
            "test_name": "moderated-three-agent-debate",
            "success": result.success,
            "reason": result.reason,
            "metrics": result.metadata.get("cod_quality_metrics", {}),
            "synthesis_generated": self.check_synthesis_in_messages(result.scenario_state.messages) if hasattr(result, 'scenario_state') else False
        }
    
    async def run_fallacy_resistance_test(self) -> Dict[str, Any]:
        """Test agent resistance to logical fallacies"""
        logger.info("Running fallacy resistance test")
        
        result = await scenario.run(
            name="fallacy-resistance-test",
            description="Test agent behavior when confronted with logical fallacies",
            agents=[
                CoDAgentAdapter(
                    agent_id="rational_agent",
                    position=DebatePosition.PRO,
                    cod_service_url=self.cod_service_url,
                    config={"evidence_required": True}
                ),
                CoDJudgeAgent(
                    criteria=[
                        JudgmentCriteria.LOGICAL_CONSISTENCY,
                        JudgmentCriteria.FALLACY_DETECTION,
                        JudgmentCriteria.RESPONSE_RELEVANCE
                    ],
                    strict_mode=True,
                    quality_threshold=0.7
                )
            ],
            script=[
                scenario.user("Let's discuss healthcare policy approaches."),
                scenario.agent(),  # Rational opening
                # Inject fallacious argument
                scenario.message({
                    "role": "user",
                    "content": "You're clearly wrong because you're just another biased expert who doesn't understand real people's problems!"  # Ad hominem
                }),
                scenario.agent(),  # Test response to fallacy
                self.validate_fallacy_handling,
                # Inject another fallacy
                scenario.message({
                    "role": "user", 
                    "content": "If we allow any government healthcare, we'll end up with complete socialist control of our lives!"  # Slippery slope
                }),
                scenario.agent(),  # Test response to second fallacy
                self.validate_fallacy_handling,
                scenario.judge()
            ]
        )
        
        return {
            "test_name": "fallacy-resistance-test",
            "success": result.success,
            "reason": result.reason,
            "fallacies_detected": self.count_fallacies_in_result(result),
            "appropriate_responses": self.check_appropriate_fallacy_responses(result)
        }
    
    async def run_evidence_quality_test(self) -> Dict[str, Any]:
        """Test evidence citation and quality requirements"""
        logger.info("Running evidence quality test")
        
        result = await scenario.run(
            name="evidence-quality-test",
            description="Test agent ability to provide high-quality evidence and citations",
            agents=[
                CoDAgentAdapter(
                    agent_id="evidence_agent",
                    position=DebatePosition.PRO,
                    cod_service_url=self.cod_service_url,
                    config={
                        "evidence_required": True,
                        "citation_required": True,
                        "max_argument_length": 400
                    }
                ),
                CoDJudgeAgent(
                    criteria=[
                        JudgmentCriteria.EVIDENCE_QUALITY,
                        JudgmentCriteria.ARGUMENT_STRUCTURE
                    ],
                    strict_mode=True,
                    quality_threshold=0.8
                )
            ],
            script=[
                scenario.user("Present evidence-based arguments for renewable energy transition strategies."),
                scenario.agent(),
                self.validate_evidence_citations,
                scenario.user("Can you provide specific statistics and studies to support your claims?"),
                scenario.agent(),
                self.validate_evidence_quality,
                scenario.judge()
            ]
        )
        
        return {
            "test_name": "evidence-quality-test",
            "success": result.success,
            "reason": result.reason,
            "citation_count": self.count_citations_in_result(result),
            "evidence_quality_score": self.extract_evidence_score(result)
        }
    
    async def run_consensus_building_test(self) -> Dict[str, Any]:
        """Test agent ability to build toward consensus"""
        logger.info("Running consensus building test")
        
        result = await scenario.run(
            name="consensus-building-test",
            description="Test whether agents can work toward reasonable compromise",
            agents=[
                CoDAgentAdapter(
                    agent_id="progressive_agent",
                    position=DebatePosition.PRO,
                    cod_service_url=self.cod_service_url
                ),
                CoDAgentAdapter(
                    agent_id="conservative_agent",
                    position=DebatePosition.CON,
                    cod_service_url=self.cod_service_url
                ),
                CoDModeratorAdapter(
                    agent_id="consensus_moderator",
                    cod_service_url=self.cod_service_url
                ),
                CoDJudgeAgent(
                    criteria=[
                        JudgmentCriteria.CONSENSUS_BUILDING,
                        JudgmentCriteria.RESPONSE_RELEVANCE
                    ],
                    quality_threshold=0.6
                )
            ],
            script=[
                scenario.user("Let's find common ground on artificial intelligence regulation approaches."),
                scenario.agent(),  # Progressive position
                scenario.agent(),  # Conservative position
                scenario.user("Can you both identify areas where you might agree?"),
                scenario.agent(),  # Progressive response
                scenario.agent(),  # Conservative response
                scenario.agent(),  # Moderator synthesis
                self.validate_consensus_progression,
                scenario.judge()
            ]
        )
        
        return {
            "test_name": "consensus-building-test",
            "success": result.success,
            "reason": result.reason,
            "consensus_score": self.extract_consensus_score(result),
            "common_ground_identified": self.check_common_ground(result)
        }
    
    async def run_local_models_test(self) -> Dict[str, Any]:
        """Test debate quality using only local models"""
        logger.info("Running local models test")
        
        result = await scenario.run(
            name="local-models-debate-test",
            description="Test debate quality using local models only",
            agents=[
                CoDAgentAdapter(
                    agent_id="local_agent_1",
                    position=DebatePosition.PRO,
                    cod_service_url="http://localhost:8012",  # Use local models directly
                    config={"use_local_only": True}
                ),
                CoDAgentAdapter(
                    agent_id="local_agent_2",
                    position=DebatePosition.CON,
                    cod_service_url="http://localhost:8012",
                    config={"use_local_only": True}
                ),
                CoDJudgeAgent(
                    criteria=[
                        JudgmentCriteria.LOGICAL_CONSISTENCY,
                        JudgmentCriteria.ARGUMENT_STRUCTURE
                    ],
                    quality_threshold=0.5  # Lower threshold for local models
                )
            ],
            script=[
                scenario.user("Debate the effectiveness of different machine learning approaches."),
                scenario.agent(),
                scenario.agent(),
                scenario.proceed(turns=3),
                scenario.judge()
            ]
        )
        
        return {
            "test_name": "local-models-debate-test",
            "success": result.success,
            "reason": result.reason,
            "local_model_performance": "functional" if result.success else "needs_improvement"
        }
    
    # Validation functions
    
    def validate_argument_quality(self, state) -> None:
        """Validate that arguments meet quality standards"""
        recent_messages = state.get_recent_messages(2)
        
        for msg in recent_messages:
            if hasattr(msg, 'role') and msg.role == 'assistant':
                content = msg.content.lower()
                
                # Check for minimum argument length
                if len(content) < 50:
                    raise AssertionError(f"Argument too short: {len(content)} characters")
                
                # Check for some form of reasoning
                reasoning_indicators = ['because', 'since', 'therefore', 'however', 'although']
                if not any(indicator in content for indicator in reasoning_indicators):
                    raise AssertionError("Argument lacks clear reasoning structure")
    
    def validate_moderator_synthesis(self, state) -> None:
        """Validate that moderator provides meaningful synthesis"""
        recent_messages = state.get_recent_messages(1)
        
        if recent_messages:
            msg = recent_messages[0]
            if hasattr(msg, 'content'):
                content = msg.content.lower()
                synthesis_indicators = ['synthesis', 'common ground', 'both sides', 'compromise', 'balance']
                
                if not any(indicator in content for indicator in synthesis_indicators):
                    raise AssertionError("Moderator response lacks synthesis elements")
    
    def validate_evidence_citations(self, state) -> None:
        """Validate that arguments include proper citations"""
        recent_messages = state.get_recent_messages(1)
        
        if recent_messages:
            msg = recent_messages[0]
            if hasattr(msg, 'content'):
                content = msg.content
                
                # Look for citation patterns
                import re
                citation_patterns = [r'\(\d{4}\)', r'http', r'study', r'research', r'according to']
                citations_found = sum(1 for pattern in citation_patterns if re.search(pattern, content, re.IGNORECASE))
                
                if citations_found == 0:
                    raise AssertionError("No citations or evidence sources found in argument")
    
    def validate_evidence_quality(self, state) -> None:
        """Validate quality of evidence provided"""
        recent_messages = state.get_recent_messages(1)
        
        if recent_messages:
            msg = recent_messages[0]
            if hasattr(msg, 'content'):
                content = msg.content
                
                # Check for specific details (numbers, percentages, specific studies)
                import re
                has_numbers = bool(re.search(r'\d+%|\d+\.\d+', content))
                has_specifics = any(word in content.lower() for word in ['study', 'research', 'data', 'statistics'])
                
                if not (has_numbers or has_specifics):
                    raise AssertionError("Evidence lacks specific details or quantitative support")
    
    def validate_fallacy_handling(self, state) -> None:
        """Validate appropriate response to logical fallacies"""
        recent_messages = state.get_recent_messages(1)
        
        if recent_messages:
            msg = recent_messages[0]
            if hasattr(msg, 'content'):
                content = msg.content.lower()
                
                # Check if agent addresses the fallacy appropriately
                fallacy_responses = [
                    'focus on the argument', 'address the point', 'evidence', 'facts',
                    'logical', 'reasoning', 'let\'s discuss', 'relevant'
                ]
                
                appropriate_response = any(response in content for response in fallacy_responses)
                personal_attack = any(attack in content for attack in ['you are', 'you\'re wrong', 'stupid', 'biased'])
                
                if not appropriate_response or personal_attack:
                    raise AssertionError("Agent did not handle logical fallacy appropriately")
    
    def validate_consensus_progression(self, state) -> None:
        """Validate that debate is progressing toward consensus"""
        messages = state.messages
        
        if len(messages) >= 4:
            later_messages = messages[-2:]
            consensus_language = ['agree', 'common ground', 'compromise', 'both right', 'middle ground']
            
            consensus_found = any(
                any(term in msg.content.lower() for term in consensus_language)
                for msg in later_messages if hasattr(msg, 'content')
            )
            
            if not consensus_found:
                raise AssertionError("No evidence of consensus building in recent messages")
    
    # Helper methods for result analysis
    
    def check_synthesis_in_messages(self, messages: List[Any]) -> bool:
        """Check if moderator synthesis was generated"""
        for msg in messages:
            if hasattr(msg, 'content') and 'synthesis' in msg.content.lower():
                return True
        return False
    
    def count_fallacies_in_result(self, result) -> int:
        """Count detected fallacies in result"""
        if hasattr(result, 'metadata') and 'cod_quality_metrics' in result.metadata:
            metrics = result.metadata['cod_quality_metrics']
            if 'argument_analyses' in metrics:
                return sum(len(analysis.get('detected_fallacies', [])) for analysis in metrics['argument_analyses'])
        return 0
    
    def check_appropriate_fallacy_responses(self, result) -> bool:
        """Check if agent responses to fallacies were appropriate"""
        # Simplified check - look for rational responses in messages
        if hasattr(result, 'scenario_state'):
            for msg in result.scenario_state.messages:
                if hasattr(msg, 'content') and 'evidence' in msg.content.lower():
                    return True
        return False
    
    def count_citations_in_result(self, result) -> int:
        """Count citations found in debate"""
        citation_count = 0
        if hasattr(result, 'scenario_state'):
            for msg in result.scenario_state.messages:
                if hasattr(msg, 'content'):
                    import re
                    citation_count += len(re.findall(r'\(\d{4}\)|http|study|research', msg.content, re.IGNORECASE))
        return citation_count
    
    def extract_evidence_score(self, result) -> float:
        """Extract evidence quality score from result"""
        if hasattr(result, 'metadata') and 'cod_quality_metrics' in result.metadata:
            metrics = result.metadata['cod_quality_metrics']
            individual_scores = metrics.get('individual_scores', {})
            return individual_scores.get('evidence_quality', 0.0)
        return 0.0
    
    def extract_consensus_score(self, result) -> float:
        """Extract consensus building score from result"""
        if hasattr(result, 'metadata') and 'cod_quality_metrics' in result.metadata:
            metrics = result.metadata['cod_quality_metrics']
            return metrics.get('consensus_progression', 0.0)
        return 0.0
    
    def check_common_ground(self, result) -> bool:
        """Check if common ground was identified"""
        if hasattr(result, 'scenario_state'):
            for msg in result.scenario_state.messages:
                if hasattr(msg, 'content'):
                    content = msg.content.lower()
                    if any(term in content for term in ['common ground', 'agree', 'compromise']):
                        return True
        return False


# Test runner functions

@pytest.mark.asyncio
async def test_basic_debate():
    """Run basic debate test"""
    suite = CoDTestSuite()
    result = await suite.run_basic_debate_test()
    assert result["success"], f"Basic debate test failed: {result['reason']}"
    assert result["message_count"] > 0, "No messages generated in debate"

@pytest.mark.asyncio  
async def test_moderated_debate():
    """Run moderated debate test"""
    suite = CoDTestSuite()
    result = await suite.run_moderated_debate_test()
    assert result["success"], f"Moderated debate test failed: {result['reason']}"
    
@pytest.mark.asyncio
async def test_fallacy_resistance():
    """Run fallacy resistance test"""
    suite = CoDTestSuite()
    result = await suite.run_fallacy_resistance_test()
    assert result["success"], f"Fallacy resistance test failed: {result['reason']}"

@pytest.mark.asyncio
async def test_evidence_quality():
    """Run evidence quality test"""
    suite = CoDTestSuite()
    result = await suite.run_evidence_quality_test()
    assert result["success"], f"Evidence quality test failed: {result['reason']}"
    assert result["citation_count"] > 0, "No citations found in evidence-based debate"

@pytest.mark.asyncio
async def test_consensus_building():
    """Run consensus building test"""
    suite = CoDTestSuite()
    result = await suite.run_consensus_building_test()
    assert result["success"], f"Consensus building test failed: {result['reason']}"

@pytest.mark.asyncio
async def test_local_models():
    """Run local models test"""
    suite = CoDTestSuite()
    result = await suite.run_local_models_test()
    assert result["success"], f"Local models test failed: {result['reason']}"


async def run_comprehensive_test_suite():
    """Run all tests and generate comprehensive report"""
    suite = CoDTestSuite()
    
    tests = [
        ("Basic Debate", suite.run_basic_debate_test),
        ("Moderated Debate", suite.run_moderated_debate_test),
        ("Fallacy Resistance", suite.run_fallacy_resistance_test),
        ("Evidence Quality", suite.run_evidence_quality_test),
        ("Consensus Building", suite.run_consensus_building_test),
        ("Local Models", suite.run_local_models_test)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            logger.info(f"Running {test_name} test")
            result = await test_func()
            results[test_name] = result
            logger.info(f"{test_name} test completed", success=result["success"])
        except Exception as e:
            logger.error(f"{test_name} test failed with exception", error=str(e))
            results[test_name] = {
                "test_name": test_name.lower().replace(" ", "_"),
                "success": False,
                "reason": f"Exception: {str(e)}",
                "error": str(e)
            }
    
    # Generate summary report
    successful_tests = sum(1 for result in results.values() if result["success"])
    total_tests = len(results)
    
    print(f"\n{'='*60}")
    print(f"CHAIN-OF-DEBATE TEST SUITE RESULTS")
    print(f"{'='*60}")
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {total_tests - successful_tests}")
    print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
    print(f"{'='*60}")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{status} {test_name}")
        if not result["success"]:
            print(f"     Reason: {result['reason']}")
    
    print(f"{'='*60}")
    
    return results


if __name__ == "__main__":
    # Run comprehensive test suite
    asyncio.run(run_comprehensive_test_suite())