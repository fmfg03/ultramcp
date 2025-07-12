"""
Enhanced Judge System for Chain-of-Debate Quality Assessment
Specialized judges for evaluating debate quality, argument structure, and logical consistency
"""

import asyncio
import httpx
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import structlog

# Import from scenario framework
import sys
sys.path.append('/root/scenario/python')
import scenario
from scenario.agent_adapter import AgentAdapter, AgentRole
from scenario.types import AgentInput, AgentReturnTypes, ScenarioResult

logger = structlog.get_logger(__name__)


class JudgmentCriteria(Enum):
    """Different aspects of debate quality to evaluate"""
    LOGICAL_CONSISTENCY = "logical_consistency"
    ARGUMENT_STRUCTURE = "argument_structure"
    EVIDENCE_QUALITY = "evidence_quality"
    RESPONSE_RELEVANCE = "response_relevance"
    FALLACY_DETECTION = "fallacy_detection"
    CONSENSUS_BUILDING = "consensus_building"
    ETHICAL_REASONING = "ethical_reasoning"


@dataclass
class ArgumentAnalysis:
    """Analysis of individual arguments"""
    has_claim: bool
    has_evidence: bool
    has_warrant: bool
    logical_structure_score: float  # 0.0 to 1.0
    evidence_quality_score: float  # 0.0 to 1.0
    detected_fallacies: List[str]
    citation_count: int


@dataclass
class DebateQualityMetrics:
    """Comprehensive debate quality assessment"""
    overall_score: float  # 0.0 to 1.0
    individual_scores: Dict[JudgmentCriteria, float]
    argument_analyses: List[ArgumentAnalysis]
    consensus_progression: float  # -1.0 (diverging) to 1.0 (converging)
    turn_quality_progression: List[float]
    detected_issues: List[str]
    recommendations: List[str]


class CoDJudgeAgent(AgentAdapter):
    """Enhanced judge for Chain-of-Debate quality assessment"""
    
    role = AgentRole.JUDGE
    
    def __init__(
        self,
        criteria: List[JudgmentCriteria] = None,
        local_models_url: str = "http://localhost:8012",
        strict_mode: bool = False,
        quality_threshold: float = 0.7
    ):
        self.criteria = criteria or list(JudgmentCriteria)
        self.local_models_url = local_models_url
        self.strict_mode = strict_mode
        self.quality_threshold = quality_threshold
        
        logger.info(
            "Initialized CoD judge",
            criteria_count=len(self.criteria),
            strict_mode=strict_mode,
            threshold=quality_threshold
        )
    
    async def call(self, input: AgentInput) -> AgentReturnTypes:
        """Comprehensive debate quality evaluation"""
        try:
            messages = input.messages
            
            # Perform multi-dimensional analysis
            quality_metrics = await self.analyze_debate_quality(messages)
            
            # Generate structured result
            result = ScenarioResult(
                success=quality_metrics.overall_score >= self.quality_threshold,
                reason=self.generate_judgment_reason(quality_metrics),
                metadata={
                    "cod_quality_metrics": quality_metrics.__dict__,
                    "judge_criteria": [c.value for c in self.criteria],
                    "evaluation_timestamp": asyncio.get_event_loop().time()
                }
            )
            
            logger.info(
                "Debate evaluation completed",
                overall_score=quality_metrics.overall_score,
                success=result.success,
                issues_count=len(quality_metrics.detected_issues)
            )
            
            return result
            
        except Exception as e:
            logger.error("Judge evaluation failed", error=str(e))
            return ScenarioResult(
                success=False,
                reason=f"Evaluation error: {str(e)}",
                metadata={"error": str(e)}
            )
    
    async def analyze_debate_quality(self, messages: List[Any]) -> DebateQualityMetrics:
        """Perform comprehensive debate quality analysis"""
        
        # Extract argument messages (excluding user/system messages)
        argument_messages = [
            msg for msg in messages 
            if hasattr(msg, 'role') and msg.role == 'assistant'
        ]
        
        if not argument_messages:
            return DebateQualityMetrics(
                overall_score=0.0,
                individual_scores={},
                argument_analyses=[],
                consensus_progression=0.0,
                turn_quality_progression=[],
                detected_issues=["No arguments found"],
                recommendations=["Ensure agents provide substantial arguments"]
            )
        
        # Analyze individual arguments
        argument_analyses = []
        for msg in argument_messages:
            analysis = await self.analyze_argument(msg.content)
            argument_analyses.append(analysis)
        
        # Calculate criterion-specific scores
        individual_scores = {}
        for criterion in self.criteria:
            score = await self.evaluate_criterion(criterion, argument_messages, argument_analyses)
            individual_scores[criterion] = score
        
        # Calculate consensus progression
        consensus_progression = self.calculate_consensus_progression(argument_messages)
        
        # Calculate turn quality progression
        turn_quality_progression = [
            (analysis.logical_structure_score + analysis.evidence_quality_score) / 2
            for analysis in argument_analyses
        ]
        
        # Detect issues and generate recommendations
        detected_issues = self.detect_quality_issues(argument_analyses, individual_scores)
        recommendations = self.generate_recommendations(detected_issues, individual_scores)
        
        # Calculate overall score
        overall_score = sum(individual_scores.values()) / len(individual_scores) if individual_scores else 0.0
        
        return DebateQualityMetrics(
            overall_score=overall_score,
            individual_scores=individual_scores,
            argument_analyses=argument_analyses,
            consensus_progression=consensus_progression,
            turn_quality_progression=turn_quality_progression,
            detected_issues=detected_issues,
            recommendations=recommendations
        )
    
    async def analyze_argument(self, argument_text: str) -> ArgumentAnalysis:
        """Analyze individual argument structure and quality"""
        
        # Basic structure detection
        has_claim = self.detect_claim(argument_text)
        has_evidence = self.detect_evidence(argument_text)
        has_warrant = self.detect_warrant(argument_text)
        
        # Count citations
        citation_count = self.count_citations(argument_text)
        
        # Detect logical fallacies
        detected_fallacies = await self.detect_fallacies(argument_text)
        
        # Score logical structure
        logical_structure_score = self.score_logical_structure(
            has_claim, has_evidence, has_warrant, len(detected_fallacies)
        )
        
        # Score evidence quality
        evidence_quality_score = self.score_evidence_quality(
            has_evidence, citation_count, argument_text
        )
        
        return ArgumentAnalysis(
            has_claim=has_claim,
            has_evidence=has_evidence,
            has_warrant=has_warrant,
            logical_structure_score=logical_structure_score,
            evidence_quality_score=evidence_quality_score,
            detected_fallacies=detected_fallacies,
            citation_count=citation_count
        )
    
    def detect_claim(self, text: str) -> bool:
        """Detect if argument contains a clear claim"""
        claim_indicators = [
            r"I believe", r"I argue", r"I contend", r"I propose",
            r"It is clear that", r"Evidence shows", r"Studies indicate",
            r"Therefore", r"Thus", r"Consequently", r"In conclusion"
        ]
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in claim_indicators)
    
    def detect_evidence(self, text: str) -> bool:
        """Detect if argument contains supporting evidence"""
        evidence_indicators = [
            r"according to", r"research shows", r"studies indicate",
            r"data reveals", r"statistics show", r"evidence suggests",
            r"for example", r"for instance", r"specifically",
            r"\d+%", r"\d+\.\d+%", r"study", r"research"
        ]
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in evidence_indicators)
    
    def detect_warrant(self, text: str) -> bool:
        """Detect reasoning that connects evidence to claim"""
        warrant_indicators = [
            r"because", r"since", r"given that", r"this shows",
            r"this proves", r"this demonstrates", r"this indicates",
            r"the reason", r"due to", r"as a result"
        ]
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in warrant_indicators)
    
    def count_citations(self, text: str) -> int:
        """Count citation-like patterns in text"""
        citation_patterns = [
            r"\(\d{4}\)",  # (2023)
            r"\d{4}",      # 2023
            r"et al\.",    # et al.
            r"http[s]?://", # URLs
            r"www\.",      # www.
            r"doi:",       # DOI
        ]
        count = 0
        for pattern in citation_patterns:
            count += len(re.findall(pattern, text, re.IGNORECASE))
        return count
    
    async def detect_fallacies(self, text: str) -> List[str]:
        """Detect common logical fallacies using AI analysis"""
        try:
            fallacy_detection_prompt = f"""
Analyze the following argument for logical fallacies. Return only the names of detected fallacies, one per line:

Argument: {text[:500]}...

Common fallacies to check for:
- Ad hominem (attacking the person, not the argument)
- Straw man (misrepresenting opponent's position)
- False dichotomy (only two options when more exist)
- Appeal to authority (inappropriate authority)
- Slippery slope (unfounded chain of consequences)
- Circular reasoning (conclusion restates premise)
- Appeal to emotion (emotions instead of logic)
- Hasty generalization (insufficient evidence for broad claim)

Return only fallacy names if detected, or "None" if no fallacies found.
"""
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self.local_models_url}/generate",
                    json={
                        "prompt": fallacy_detection_prompt,
                        "task_type": "reasoning",
                        "max_tokens": 100
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                content = result.get("content", "").strip()
                
                if content.lower() == "none":
                    return []
                
                # Parse fallacy names
                fallacies = [
                    line.strip() for line in content.split('\n')
                    if line.strip() and not line.strip().lower().startswith('none')
                ]
                return fallacies[:3]  # Limit to top 3 fallacies
                
        except Exception as e:
            logger.warning("Fallacy detection failed", error=str(e))
            return []
    
    def score_logical_structure(self, has_claim: bool, has_evidence: bool, has_warrant: bool, fallacy_count: int) -> float:
        """Score the logical structure of an argument"""
        base_score = 0.0
        
        if has_claim:
            base_score += 0.4
        if has_evidence:
            base_score += 0.4
        if has_warrant:
            base_score += 0.2
        
        # Penalize fallacies
        fallacy_penalty = min(0.3, fallacy_count * 0.1)
        
        return max(0.0, base_score - fallacy_penalty)
    
    def score_evidence_quality(self, has_evidence: bool, citation_count: int, text: str) -> float:
        """Score the quality of evidence provided"""
        if not has_evidence:
            return 0.0
        
        base_score = 0.5  # Base score for having evidence
        
        # Bonus for citations
        citation_bonus = min(0.3, citation_count * 0.1)
        
        # Bonus for specific details
        specificity_bonus = 0.2 if any(char.isdigit() for char in text) else 0.0
        
        return min(1.0, base_score + citation_bonus + specificity_bonus)
    
    async def evaluate_criterion(self, criterion: JudgmentCriteria, messages: List[Any], analyses: List[ArgumentAnalysis]) -> float:
        """Evaluate specific judgment criterion"""
        
        if criterion == JudgmentCriteria.LOGICAL_CONSISTENCY:
            # Average logical structure scores
            scores = [analysis.logical_structure_score for analysis in analyses]
            return sum(scores) / len(scores) if scores else 0.0
        
        elif criterion == JudgmentCriteria.ARGUMENT_STRUCTURE:
            # Check if arguments have proper structure (claim + evidence + warrant)
            structured_count = sum(
                1 for analysis in analyses
                if analysis.has_claim and analysis.has_evidence
            )
            return structured_count / len(analyses) if analyses else 0.0
        
        elif criterion == JudgmentCriteria.EVIDENCE_QUALITY:
            # Average evidence quality scores
            scores = [analysis.evidence_quality_score for analysis in analyses]
            return sum(scores) / len(scores) if scores else 0.0
        
        elif criterion == JudgmentCriteria.FALLACY_DETECTION:
            # Penalize arguments with fallacies
            total_fallacies = sum(len(analysis.detected_fallacies) for analysis in analyses)
            return max(0.0, 1.0 - (total_fallacies * 0.2))
        
        elif criterion == JudgmentCriteria.RESPONSE_RELEVANCE:
            # Use AI to assess relevance (simplified for now)
            return await self.assess_response_relevance(messages)
        
        elif criterion == JudgmentCriteria.CONSENSUS_BUILDING:
            # Check if debate is progressing toward consensus
            return max(0.0, self.calculate_consensus_progression(messages))
        
        else:
            # Default scoring for other criteria
            return 0.5
    
    async def assess_response_relevance(self, messages: List[Any]) -> float:
        """Assess how well responses address previous arguments"""
        if len(messages) < 2:
            return 1.0  # Can't assess relevance with fewer than 2 messages
        
        try:
            # Take last few messages for analysis
            recent_messages = messages[-4:] if len(messages) > 4 else messages
            
            relevance_prompt = f"""
Assess how well the responses in this debate address and engage with previous arguments on a scale of 0.0 to 1.0:

Messages:
{chr(10).join([f"{msg.role}: {msg.content[:150]}..." for msg in recent_messages if hasattr(msg, 'role')])}

Criteria:
- Do responses directly address previous points?
- Are counterarguments acknowledged?
- Is there meaningful engagement with opposing views?

Return only a number between 0.0 and 1.0.
"""
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.local_models_url}/generate",
                    json={
                        "prompt": relevance_prompt,
                        "task_type": "reasoning",
                        "max_tokens": 10
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                content = result.get("content", "0.5").strip()
                
                # Extract numeric score
                import re
                match = re.search(r'0\.\d+|1\.0|0|1', content)
                if match:
                    return float(match.group())
                return 0.5
                
        except Exception as e:
            logger.warning("Relevance assessment failed", error=str(e))
            return 0.5
    
    def calculate_consensus_progression(self, messages: List[Any]) -> float:
        """Calculate if debate is progressing toward consensus"""
        if len(messages) < 3:
            return 0.0
        
        # Simple heuristic: look for consensus language in later messages
        consensus_indicators = [
            "I agree", "you're right", "good point", "I concede",
            "that's true", "I see your point", "common ground",
            "both sides", "compromise", "middle ground"
        ]
        
        early_messages = messages[:len(messages)//2]
        later_messages = messages[len(messages)//2:]
        
        early_consensus = sum(
            1 for msg in early_messages
            if hasattr(msg, 'content') and any(
                indicator in msg.content.lower()
                for indicator in consensus_indicators
            )
        )
        
        later_consensus = sum(
            1 for msg in later_messages
            if hasattr(msg, 'content') and any(
                indicator in msg.content.lower()
                for indicator in consensus_indicators
            )
        )
        
        if len(later_messages) == 0:
            return 0.0
        
        # Return positive if consensus increases over time
        early_rate = early_consensus / len(early_messages) if early_messages else 0
        later_rate = later_consensus / len(later_messages) if later_messages else 0
        
        return later_rate - early_rate
    
    def detect_quality_issues(self, analyses: List[ArgumentAnalysis], scores: Dict[JudgmentCriteria, float]) -> List[str]:
        """Detect specific quality issues in the debate"""
        issues = []
        
        # Check for lack of evidence
        evidence_rate = sum(1 for a in analyses if a.has_evidence) / len(analyses) if analyses else 0
        if evidence_rate < 0.5:
            issues.append("Low evidence rate - many arguments lack supporting evidence")
        
        # Check for high fallacy rate
        total_fallacies = sum(len(a.detected_fallacies) for a in analyses)
        if total_fallacies > len(analyses) * 0.5:
            issues.append("High logical fallacy rate detected")
        
        # Check for poor structure
        if scores.get(JudgmentCriteria.ARGUMENT_STRUCTURE, 1.0) < 0.4:
            issues.append("Arguments lack proper structure (claim-evidence-warrant)")
        
        # Check for poor relevance
        if scores.get(JudgmentCriteria.RESPONSE_RELEVANCE, 1.0) < 0.4:
            issues.append("Responses poorly address previous arguments")
        
        return issues
    
    def generate_recommendations(self, issues: List[str], scores: Dict[JudgmentCriteria, float]) -> List[str]:
        """Generate improvement recommendations based on detected issues"""
        recommendations = []
        
        if "Low evidence rate" in " ".join(issues):
            recommendations.append("Require agents to provide specific evidence and citations")
        
        if "High logical fallacy rate" in " ".join(issues):
            recommendations.append("Implement fallacy detection and prevention training")
        
        if "lack proper structure" in " ".join(issues):
            recommendations.append("Train agents on claim-evidence-warrant argument structure")
        
        if "poorly address previous arguments" in " ".join(issues):
            recommendations.append("Improve context awareness and response relevance")
        
        # General recommendations based on low scores
        for criterion, score in scores.items():
            if score < 0.5:
                recommendations.append(f"Focus on improving {criterion.value.replace('_', ' ')}")
        
        return recommendations
    
    def generate_judgment_reason(self, metrics: DebateQualityMetrics) -> str:
        """Generate human-readable judgment reason"""
        score = metrics.overall_score
        
        if score >= 0.8:
            quality = "excellent"
        elif score >= 0.6:
            quality = "good"
        elif score >= 0.4:
            quality = "fair"
        else:
            quality = "poor"
        
        reason = f"Debate quality assessed as {quality} (score: {score:.2f}). "
        
        if metrics.detected_issues:
            reason += f"Issues detected: {', '.join(metrics.detected_issues[:2])}. "
        
        if metrics.recommendations:
            reason += f"Key recommendation: {metrics.recommendations[0]}"
        
        return reason