"""
Agent Quality Validator
Integration with Enhanced Testing System for Agent Factory

Provides automated agent validation using:
- LangWatch testing patterns
- UltraMCP Scenario-CoD integration
- Real-time quality assessment
- Comprehensive agent certification
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import asdict
import httpx

from enhanced_testing_system import (
    EnhancedAgentTester,
    TestScenario,
    AgentTestResult,
    TestResult,
    TestCriteria,
    AgentTestType,
    PREDEFINED_SCENARIOS
)

from comprehensive_test_scenarios import (
    get_scenarios_for_agent_type,
    get_comprehensive_test_suite,
    get_quick_validation_scenarios,
    ALL_TEST_SCENARIOS,
    PERFORMANCE_BENCHMARKS
)


class AgentQualityValidator:
    """Main validator for agent quality using enhanced testing"""
    
    def __init__(self):
        self.tester = EnhancedAgentTester()
        self.validation_history = []
    
    async def validate_generated_agent(self, agent_id: str, agent_config: Dict[str, Any], 
                                     agent_type: str) -> Dict[str, Any]:
        """Validate a newly generated agent"""
        print(f"🔍 Starting quality validation for agent {agent_id}")
        
        try:
            # Select appropriate test scenarios based on agent type
            scenarios = self._select_test_scenarios(agent_type, agent_config)
            
            # Run comprehensive testing
            test_results = await self.tester.run_comprehensive_test(
                agent_id, agent_config, scenarios
            )
            
            # Generate validation report
            validation_report = self._generate_validation_report(agent_id, test_results)
            
            # Store validation history
            self.validation_history.append({
                "agent_id": agent_id,
                "timestamp": datetime.now().isoformat(),
                "validation_report": validation_report,
                "test_results": [asdict(result) for result in test_results]
            })
            
            print(f"✅ Validation completed for agent {agent_id}")
            return validation_report
            
        except Exception as e:
            error_report = {
                "agent_id": agent_id,
                "status": "validation_failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "overall_score": 0.0,
                "certification": "failed",
                "recommendations": ["Fix critical errors before deployment"]
            }
            
            print(f"❌ Validation failed for agent {agent_id}: {e}")
            return error_report
    
    def _select_test_scenarios(self, agent_type: str, agent_config: Dict[str, Any]) -> List[TestScenario]:
        """Select appropriate test scenarios based on agent type using comprehensive scenarios"""
        
        # Get comprehensive scenarios for the agent type
        scenarios = get_scenarios_for_agent_type(agent_type)
        
        # Add basic predefined scenarios as fallback
        if "customer-support" in agent_type.lower():
            scenarios.append(PREDEFINED_SCENARIOS["customer_support"])
            
            # Add additional customer support scenarios
            scenarios.append(TestScenario(
                name="customer_support_escalation",
                description="Angry customer with complex technical issue requiring escalation",
                scenario_type=AgentTestType.CONVERSATION,
                criteria=[
                    TestCriteria("emotion_handling", "Handles angry customer emotions", 1.5, 0.8),
                    TestCriteria("technical_accuracy", "Provides accurate technical info", 1.2, 0.8),
                    TestCriteria("escalation_timing", "Escalates at appropriate time", 1.0, 0.85),
                    TestCriteria("documentation", "Properly documents the issue", 0.8, 0.75)
                ],
                context={"customer_emotion": "angry", "issue_complexity": "high", "priority": "urgent"},
                expected_capabilities=["escalate_to_human", "create_ticket", "sentiment_analysis"],
                conversation_turns=6
            ))
        
        elif "research" in agent_type.lower():
            scenarios.append(PREDEFINED_SCENARIOS["research_analyst"])
            
            # Add research-specific scenario
            scenarios.append(TestScenario(
                name="research_data_analysis",
                description="Client provides raw data and requests analysis and insights",
                scenario_type=AgentTestType.QUALITY,
                criteria=[
                    TestCriteria("data_interpretation", "Correctly interprets provided data", 1.5, 0.85),
                    TestCriteria("insight_generation", "Generates valuable insights", 1.2, 0.8),
                    TestCriteria("statistical_accuracy", "Uses statistics correctly", 1.0, 0.85),
                    TestCriteria("visualization_suggestions", "Suggests appropriate visualizations", 0.8, 0.7)
                ],
                context={"data_type": "sales", "analysis_depth": "comprehensive"},
                expected_capabilities=["data_analysis", "statistical_modeling", "insight_generation"],
                conversation_turns=8
            ))
        
        elif "code" in agent_type.lower():
            scenarios.append(PREDEFINED_SCENARIOS["code_reviewer"])
            
            # Add code-specific scenario
            scenarios.append(TestScenario(
                name="code_security_audit",
                description="Security audit of critical application code",
                scenario_type=AgentTestType.TECHNICAL,
                criteria=[
                    TestCriteria("vulnerability_detection", "Identifies all vulnerabilities", 2.0, 0.9),
                    TestCriteria("severity_assessment", "Correctly assesses severity", 1.5, 0.85),
                    TestCriteria("fix_recommendations", "Provides actionable fixes", 1.2, 0.8),
                    TestCriteria("compliance_check", "Checks security compliance", 1.0, 0.8)
                ],
                context={"security_level": "critical", "compliance": "SOC2"},
                expected_capabilities=["security_scanning", "compliance_check", "vulnerability_assessment"],
                conversation_turns=5
            ))
        
        # Universal agent testing scenario
        scenarios.append(TestScenario(
            name="universal_capability_test",
            description="General capability and reliability test for any agent type",
            scenario_type=AgentTestType.FUNCTIONAL,
            criteria=[
                TestCriteria("response_coherence", "Responses are coherent and relevant", 1.0, 0.8),
                TestCriteria("task_completion", "Completes assigned tasks", 1.2, 0.8),
                TestCriteria("error_handling", "Handles errors gracefully", 1.0, 0.75),
                TestCriteria("context_maintenance", "Maintains conversation context", 0.8, 0.75),
                TestCriteria("resource_efficiency", "Uses resources efficiently", 0.6, 0.7)
            ],
            context={"test_type": "universal", "difficulty": "medium"},
            expected_capabilities=agent_config.get("capabilities", []),
            conversation_turns=7
        ))
        
        return scenarios
    
    def _generate_validation_report(self, agent_id: str, test_results: List[AgentTestResult]) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        
        total_tests = len(test_results)
        passed_tests = len([r for r in test_results if r.result == TestResult.PASS])
        failed_tests = len([r for r in test_results if r.result == TestResult.FAIL])
        partial_tests = len([r for r in test_results if r.result == TestResult.PARTIAL])
        
        # Calculate overall score
        overall_score = sum(result.score for result in test_results) / total_tests if total_tests > 0 else 0.0
        
        # Determine certification level
        certification = self._determine_certification(overall_score, test_results)
        
        # Extract key insights
        strengths, weaknesses, recommendations = self._analyze_test_results(test_results)
        
        # Generate summary
        report = {
            "agent_id": agent_id,
            "validation_timestamp": datetime.now().isoformat(),
            "status": "validation_completed",
            "overall_score": round(overall_score, 3),
            "certification": certification,
            "test_summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "partial": partial_tests,
                "pass_rate": round(passed_tests / total_tests, 3) if total_tests > 0 else 0.0
            },
            "detailed_scores": {
                result.scenario.name: {
                    "score": round(result.score, 3),
                    "result": result.result.value,
                    "criteria_scores": {k: round(v, 3) for k, v in result.criteria_scores.items()},
                    "execution_time": round(result.execution_time, 2)
                }
                for result in test_results
            },
            "quality_assessment": {
                "strengths": strengths,
                "weaknesses": weaknesses,
                "recommendations": recommendations
            },
            "deployment_readiness": {
                "ready_for_production": overall_score >= 0.8 and failed_tests == 0,
                "ready_for_testing": overall_score >= 0.6,
                "requires_improvement": overall_score < 0.6,
                "critical_issues": failed_tests > 0
            },
            "conversation_analytics": self._analyze_conversations(test_results),
            "performance_metrics": self._calculate_performance_metrics(test_results)
        }
        
        return report
    
    def _determine_certification(self, overall_score: float, test_results: List[AgentTestResult]) -> str:
        """Determine agent certification level"""
        failed_tests = len([r for r in test_results if r.result == TestResult.FAIL])
        
        if failed_tests > 0:
            return "failed"
        elif overall_score >= 0.9:
            return "excellent"
        elif overall_score >= 0.8:
            return "good"
        elif overall_score >= 0.7:
            return "acceptable"
        elif overall_score >= 0.6:
            return "needs_improvement"
        else:
            return "failed"
    
    def _analyze_test_results(self, test_results: List[AgentTestResult]) -> tuple:
        """Analyze test results to extract insights"""
        
        strengths = []
        weaknesses = []
        recommendations = []
        
        # Analyze criteria performance across all tests
        all_criteria_scores = {}
        for result in test_results:
            for criterion, score in result.criteria_scores.items():
                if criterion not in all_criteria_scores:
                    all_criteria_scores[criterion] = []
                all_criteria_scores[criterion].append(score)
        
        # Identify strengths (consistently high scores)
        for criterion, scores in all_criteria_scores.items():
            avg_score = sum(scores) / len(scores)
            if avg_score >= 0.8:
                strengths.append(f"Strong {criterion.replace('_', ' ')} (avg: {avg_score:.2f})")
        
        # Identify weaknesses (consistently low scores)
        for criterion, scores in all_criteria_scores.items():
            avg_score = sum(scores) / len(scores)
            if avg_score < 0.6:
                weaknesses.append(f"Weak {criterion.replace('_', ' ')} (avg: {avg_score:.2f})")
        
        # Generate recommendations
        if not strengths:
            recommendations.append("Consider retraining or adjusting agent configuration")
        
        for weakness in weaknesses:
            if "response" in weakness:
                recommendations.append("Improve response quality through better prompting or model tuning")
            elif "technical" in weakness:
                recommendations.append("Enhance technical knowledge base and capabilities")
            elif "conversation" in weakness:
                recommendations.append("Improve conversation flow and context management")
        
        # Check for failed tests
        failed_results = [r for r in test_results if r.result == TestResult.FAIL]
        if failed_results:
            recommendations.append(f"Address {len(failed_results)} failed test scenarios before deployment")
        
        # Performance recommendations
        avg_execution_time = sum(r.execution_time for r in test_results) / len(test_results)
        if avg_execution_time > 60:
            recommendations.append("Optimize response time - current average exceeds 60 seconds")
        
        return strengths, weaknesses, recommendations
    
    def _analyze_conversations(self, test_results: List[AgentTestResult]) -> Dict[str, Any]:
        """Analyze conversation patterns across tests"""
        
        total_turns = sum(len(result.conversation_log) for result in test_results)
        total_conversations = len(test_results)
        
        return {
            "total_conversation_turns": total_turns,
            "average_turns_per_test": round(total_turns / total_conversations, 1) if total_conversations > 0 else 0,
            "conversation_completion_rate": len([r for r in test_results if len(r.conversation_log) >= 5]) / total_conversations if total_conversations > 0 else 0,
            "response_consistency": self._calculate_response_consistency(test_results)
        }
    
    def _calculate_performance_metrics(self, test_results: List[AgentTestResult]) -> Dict[str, Any]:
        """Calculate performance metrics"""
        
        execution_times = [r.execution_time for r in test_results if r.execution_time > 0]
        
        return {
            "average_execution_time": round(sum(execution_times) / len(execution_times), 2) if execution_times else 0,
            "fastest_test": round(min(execution_times), 2) if execution_times else 0,
            "slowest_test": round(max(execution_times), 2) if execution_times else 0,
            "total_test_time": round(sum(execution_times), 2) if execution_times else 0
        }
    
    def _calculate_response_consistency(self, test_results: List[AgentTestResult]) -> float:
        """Calculate response consistency score"""
        try:
            # Simple heuristic: variance in scores across similar criteria
            all_scores = []
            for result in test_results:
                all_scores.extend(result.criteria_scores.values())
            
            if len(all_scores) < 2:
                return 1.0
            
            # Calculate coefficient of variation (lower = more consistent)
            mean_score = sum(all_scores) / len(all_scores)
            variance = sum((score - mean_score) ** 2 for score in all_scores) / len(all_scores)
            std_dev = variance ** 0.5
            
            cv = std_dev / mean_score if mean_score > 0 else 1.0
            
            # Convert to consistency score (0-1, higher = more consistent)
            consistency = max(0.0, 1.0 - cv)
            return round(consistency, 3)
            
        except Exception:
            return 0.5  # Default moderate consistency
    
    async def run_continuous_monitoring(self, agent_id: str, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run continuous monitoring for deployed agents"""
        print(f"🔄 Starting continuous monitoring for agent {agent_id}")
        
        # Run lightweight monitoring scenarios
        monitoring_scenario = TestScenario(
            name="continuous_monitoring",
            description="Lightweight monitoring check for deployed agent",
            scenario_type=AgentTestType.FUNCTIONAL,
            criteria=[
                TestCriteria("availability", "Agent responds to requests", 1.0, 0.95),
                TestCriteria("response_quality", "Maintains response quality", 1.0, 0.8),
                TestCriteria("performance", "Maintains performance standards", 0.8, 0.8)
            ],
            context={"monitoring": True, "lightweight": True},
            expected_capabilities=agent_config.get("capabilities", []),
            conversation_turns=3
        )
        
        test_results = await self.tester.run_comprehensive_test(
            agent_id, agent_config, [monitoring_scenario]
        )
        
        return {
            "agent_id": agent_id,
            "monitoring_timestamp": datetime.now().isoformat(),
            "status": "healthy" if test_results[0].result == TestResult.PASS else "degraded",
            "monitoring_score": test_results[0].score,
            "issues_detected": test_results[0].result != TestResult.PASS,
            "recommended_actions": ["Continue monitoring"] if test_results[0].result == TestResult.PASS else ["Investigate performance issues"]
        }


# Integration helper functions
async def validate_agent_before_deployment(agent_id: str, agent_config: Dict[str, Any], agent_type: str) -> bool:
    """Quick validation check before deployment"""
    validator = AgentQualityValidator()
    report = await validator.validate_generated_agent(agent_id, agent_config, agent_type)
    
    return (
        report.get("certification") in ["excellent", "good", "acceptable"] and
        report.get("deployment_readiness", {}).get("ready_for_testing", False)
    )


async def get_agent_quality_score(agent_id: str, agent_config: Dict[str, Any], agent_type: str) -> float:
    """Get quick quality score for agent"""
    validator = AgentQualityValidator()
    report = await validator.validate_generated_agent(agent_id, agent_config, agent_type)
    
    return report.get("overall_score", 0.0)