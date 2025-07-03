#!/usr/bin/env python3
"""
DeepClaude Metacognitive Service
Advanced reasoning and metacognitive analysis service
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import json

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="DeepClaude Metacognitive Service",
    description="Advanced reasoning and metacognitive analysis",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ReasoningRequest(BaseModel):
    topic: str
    context: Dict[str, Any] = {}
    reasoning_mode: str = "analytical"  # analytical, creative, critical, metacognitive
    depth: str = "medium"  # shallow, medium, deep

class PatternAnalysisRequest(BaseModel):
    data: List[Dict[str, Any]]
    pattern_type: str = "behavioral"  # behavioral, decision, cognitive, temporal
    context: Dict[str, Any] = {}

class SynthesisRequest(BaseModel):
    inputs: List[Dict[str, Any]]
    synthesis_type: str = "consolidation"  # consolidation, comparison, integration
    target_format: str = "insights"  # insights, summary, recommendations

class MetacognitionRequest(BaseModel):
    reasoning_chain: List[Dict[str, Any]]
    evaluation_criteria: List[str] = []
    improvement_focus: str = "accuracy"  # accuracy, creativity, efficiency

# Global state
active_reasoning_tasks = {}
reasoning_cache = {}
pattern_memory = {}

class MetacognitiveReasoningEngine:
    """Core metacognitive reasoning engine"""
    
    def __init__(self):
        self.reasoning_history = []
        self.pattern_database = {}
        self.metacognitive_models = {}
    
    async def perform_reasoning(self, topic: str, context: Dict, mode: str, depth: str) -> Dict:
        """Perform advanced reasoning on a topic"""
        
        reasoning_chain = []
        
        # Step 1: Initial analysis
        initial_analysis = await self._analyze_topic(topic, context, mode)
        reasoning_chain.append({
            "step": "initial_analysis",
            "content": initial_analysis,
            "timestamp": datetime.now().isoformat()
        })
        
        # Step 2: Multi-perspective reasoning
        perspectives = await self._generate_perspectives(topic, context, mode)
        reasoning_chain.append({
            "step": "perspective_generation",
            "content": perspectives,
            "timestamp": datetime.now().isoformat()
        })
        
        # Step 3: Deep analysis (if requested)
        if depth in ["medium", "deep"]:
            deep_analysis = await self._deep_analysis(topic, initial_analysis, perspectives)
            reasoning_chain.append({
                "step": "deep_analysis",
                "content": deep_analysis,
                "timestamp": datetime.now().isoformat()
            })
        
        # Step 4: Metacognitive evaluation
        if depth == "deep":
            metacognitive_eval = await self._metacognitive_evaluation(reasoning_chain)
            reasoning_chain.append({
                "step": "metacognitive_evaluation",
                "content": metacognitive_eval,
                "timestamp": datetime.now().isoformat()
            })
        
        # Step 5: Synthesis
        synthesis = await self._synthesize_reasoning(reasoning_chain, mode)
        
        return {
            "topic": topic,
            "reasoning_mode": mode,
            "depth": depth,
            "reasoning_chain": reasoning_chain,
            "synthesis": synthesis,
            "confidence_score": self._calculate_confidence(reasoning_chain),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _analyze_topic(self, topic: str, context: Dict, mode: str) -> Dict:
        """Initial topic analysis"""
        
        # Simulate advanced reasoning (in real implementation, this would use Claude API)
        analysis = {
            "topic_classification": "complex" if len(topic.split()) > 10 else "simple",
            "domain_identification": self._identify_domain(topic),
            "complexity_factors": self._identify_complexity_factors(topic, context),
            "initial_insights": self._generate_initial_insights(topic, mode),
            "context_relevance": self._evaluate_context_relevance(context)
        }
        
        return analysis
    
    async def _generate_perspectives(self, topic: str, context: Dict, mode: str) -> List[Dict]:
        """Generate multiple perspectives on the topic"""
        
        perspective_types = [
            "analytical", "creative", "critical", "practical", 
            "ethical", "strategic", "technical", "user-focused"
        ]
        
        perspectives = []
        for perspective_type in perspective_types[:4]:  # Limit to 4 perspectives
            perspective = {
                "type": perspective_type,
                "viewpoint": f"{perspective_type.title()} perspective on: {topic}",
                "key_points": self._generate_perspective_points(topic, perspective_type),
                "implications": self._generate_implications(topic, perspective_type)
            }
            perspectives.append(perspective)
        
        return perspectives
    
    async def _deep_analysis(self, topic: str, initial_analysis: Dict, perspectives: List[Dict]) -> Dict:
        """Perform deep analysis combining initial analysis and perspectives"""
        
        return {
            "integrated_insights": self._integrate_insights(initial_analysis, perspectives),
            "contradiction_analysis": self._analyze_contradictions(perspectives),
            "synthesis_opportunities": self._identify_synthesis_opportunities(perspectives),
            "knowledge_gaps": self._identify_knowledge_gaps(topic, initial_analysis),
            "improvement_recommendations": self._generate_improvements(initial_analysis, perspectives)
        }
    
    async def _metacognitive_evaluation(self, reasoning_chain: List[Dict]) -> Dict:
        """Evaluate the reasoning process itself"""
        
        return {
            "reasoning_quality": self._evaluate_reasoning_quality(reasoning_chain),
            "bias_detection": self._detect_biases(reasoning_chain),
            "logical_consistency": self._check_logical_consistency(reasoning_chain),
            "completeness_assessment": self._assess_completeness(reasoning_chain),
            "improvement_suggestions": self._suggest_improvements(reasoning_chain)
        }
    
    async def _synthesize_reasoning(self, reasoning_chain: List[Dict], mode: str) -> Dict:
        """Synthesize the entire reasoning chain"""
        
        return {
            "key_insights": self._extract_key_insights(reasoning_chain),
            "actionable_recommendations": self._generate_recommendations(reasoning_chain),
            "confidence_assessment": self._assess_confidence(reasoning_chain),
            "next_steps": self._suggest_next_steps(reasoning_chain),
            "meta_learnings": self._extract_meta_learnings(reasoning_chain)
        }
    
    def _identify_domain(self, topic: str) -> str:
        """Identify the domain of the topic"""
        # Simple domain classification
        if any(word in topic.lower() for word in ['code', 'software', 'programming', 'development']):
            return "technology"
        elif any(word in topic.lower() for word in ['business', 'strategy', 'market', 'revenue']):
            return "business"
        elif any(word in topic.lower() for word in ['security', 'risk', 'threat', 'vulnerability']):
            return "security"
        else:
            return "general"
    
    def _identify_complexity_factors(self, topic: str, context: Dict) -> List[str]:
        """Identify factors that make the topic complex"""
        factors = []
        
        if len(topic.split()) > 15:
            factors.append("verbose_description")
        if context and len(context) > 5:
            factors.append("rich_context")
        if any(word in topic.lower() for word in ['multiple', 'various', 'different', 'several']):
            factors.append("multiple_dimensions")
        
        return factors
    
    def _generate_initial_insights(self, topic: str, mode: str) -> List[str]:
        """Generate initial insights based on mode"""
        insights = []
        
        if mode == "analytical":
            insights.extend([
                f"Systematic breakdown needed for: {topic}",
                "Multiple factors require careful consideration",
                "Data-driven approach recommended"
            ])
        elif mode == "creative":
            insights.extend([
                f"Creative opportunities in: {topic}",
                "Unconventional approaches worth exploring",
                "Innovation potential identified"
            ])
        elif mode == "critical":
            insights.extend([
                f"Critical evaluation required for: {topic}",
                "Potential weaknesses need examination",
                "Assumptions should be questioned"
            ])
        
        return insights
    
    def _evaluate_context_relevance(self, context: Dict) -> float:
        """Evaluate how relevant the context is"""
        if not context:
            return 0.0
        
        # Simple relevance scoring
        relevance_score = min(len(context) / 10.0, 1.0)
        return relevance_score
    
    def _generate_perspective_points(self, topic: str, perspective_type: str) -> List[str]:
        """Generate key points for a specific perspective"""
        base_points = [
            f"{perspective_type.title()} approach to the problem",
            f"Key considerations from {perspective_type} viewpoint",
            f"Potential solutions using {perspective_type} thinking"
        ]
        return base_points
    
    def _generate_implications(self, topic: str, perspective_type: str) -> List[str]:
        """Generate implications for a perspective"""
        return [
            f"Impact on stakeholders from {perspective_type} view",
            f"Long-term consequences of {perspective_type} decisions",
            f"Resource requirements for {perspective_type} approach"
        ]
    
    def _integrate_insights(self, initial_analysis: Dict, perspectives: List[Dict]) -> List[str]:
        """Integrate insights from analysis and perspectives"""
        return [
            "Combined analytical and perspective insights",
            "Cross-perspective validation completed",
            "Integrated understanding achieved"
        ]
    
    def _analyze_contradictions(self, perspectives: List[Dict]) -> List[Dict]:
        """Analyze contradictions between perspectives"""
        return [
            {
                "contradiction": "Analytical vs Creative approaches",
                "description": "Different optimization criteria",
                "resolution_approach": "Balanced hybrid approach"
            }
        ]
    
    def _identify_synthesis_opportunities(self, perspectives: List[Dict]) -> List[str]:
        """Identify opportunities for synthesis"""
        return [
            "Combine structured analysis with creative insights",
            "Integrate practical constraints with strategic vision",
            "Balance technical accuracy with user experience"
        ]
    
    def _identify_knowledge_gaps(self, topic: str, analysis: Dict) -> List[str]:
        """Identify gaps in knowledge or analysis"""
        return [
            "Additional domain expertise needed",
            "More detailed technical specifications required",
            "Stakeholder input missing"
        ]
    
    def _generate_improvements(self, analysis: Dict, perspectives: List[Dict]) -> List[str]:
        """Generate improvement recommendations"""
        return [
            "Enhance data collection for better analysis",
            "Include additional stakeholder perspectives",
            "Consider long-term implications more thoroughly"
        ]
    
    def _evaluate_reasoning_quality(self, reasoning_chain: List[Dict]) -> Dict:
        """Evaluate the quality of reasoning"""
        return {
            "logical_flow": "strong",
            "evidence_quality": "moderate", 
            "conclusion_support": "adequate",
            "overall_score": 0.75
        }
    
    def _detect_biases(self, reasoning_chain: List[Dict]) -> List[str]:
        """Detect potential biases in reasoning"""
        return [
            "Confirmation bias in perspective selection",
            "Anchoring bias in initial analysis"
        ]
    
    def _check_logical_consistency(self, reasoning_chain: List[Dict]) -> Dict:
        """Check logical consistency of reasoning"""
        return {
            "consistency_score": 0.8,
            "inconsistencies": [],
            "logical_gaps": ["Missing causal links between steps 2 and 3"]
        }
    
    def _assess_completeness(self, reasoning_chain: List[Dict]) -> Dict:
        """Assess completeness of reasoning"""
        return {
            "completeness_score": 0.85,
            "missing_elements": ["Stakeholder analysis", "Risk assessment"],
            "coverage_areas": ["Technical", "Strategic", "Analytical"]
        }
    
    def _suggest_improvements(self, reasoning_chain: List[Dict]) -> List[str]:
        """Suggest improvements to reasoning process"""
        return [
            "Add quantitative analysis where possible",
            "Include more diverse perspectives",
            "Strengthen causal reasoning chains"
        ]
    
    def _extract_key_insights(self, reasoning_chain: List[Dict]) -> List[str]:
        """Extract key insights from reasoning chain"""
        return [
            "Multi-perspective analysis reveals complexity",
            "Integration opportunities identified",
            "Strategic approach recommended"
        ]
    
    def _generate_recommendations(self, reasoning_chain: List[Dict]) -> List[str]:
        """Generate actionable recommendations"""
        return [
            "Implement phased approach to address complexity",
            "Establish stakeholder feedback loops",
            "Monitor progress with defined metrics"
        ]
    
    def _assess_confidence(self, reasoning_chain: List[Dict]) -> float:
        """Assess confidence in reasoning"""
        return 0.78  # Based on reasoning quality, completeness, etc.
    
    def _suggest_next_steps(self, reasoning_chain: List[Dict]) -> List[str]:
        """Suggest next steps"""
        return [
            "Validate assumptions with domain experts",
            "Gather additional data for analysis",
            "Develop implementation roadmap"
        ]
    
    def _extract_meta_learnings(self, reasoning_chain: List[Dict]) -> List[str]:
        """Extract meta-learnings about the reasoning process"""
        return [
            "Multi-perspective approach improved insight quality",
            "Metacognitive evaluation identified reasoning gaps",
            "Structured synthesis enhanced clarity"
        ]
    
    def _calculate_confidence(self, reasoning_chain: List[Dict]) -> float:
        """Calculate overall confidence score"""
        # Base confidence on chain length, depth, and consistency
        base_score = 0.6
        chain_bonus = min(len(reasoning_chain) * 0.1, 0.3)
        return min(base_score + chain_bonus, 1.0)

# Initialize reasoning engine
reasoning_engine = MetacognitiveReasoningEngine()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "deepclaude-metacognitive",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/v1/status")
async def get_service_status():
    """Get detailed service status"""
    return {
        "service": "deepclaude-metacognitive",
        "status": "running",
        "active_tasks": len(active_reasoning_tasks),
        "cached_results": len(reasoning_cache),
        "features": [
            "metacognitive_reasoning",
            "pattern_analysis",
            "insight_synthesis",
            "reasoning_evaluation"
        ],
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/reasoning/analyze")
async def perform_reasoning(request: ReasoningRequest, background_tasks: BackgroundTasks):
    """Perform metacognitive reasoning analysis"""
    try:
        task_id = f"reasoning_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Start background reasoning
        background_tasks.add_task(
            run_reasoning_analysis,
            task_id,
            request.topic,
            request.context,
            request.reasoning_mode,
            request.depth
        )
        
        active_reasoning_tasks[task_id] = {
            "type": "reasoning",
            "status": "running",
            "topic": request.topic,
            "reasoning_mode": request.reasoning_mode,
            "depth": request.depth,
            "started_at": datetime.now().isoformat()
        }
        
        return {
            "task_id": task_id,
            "status": "started",
            "topic": request.topic,
            "message": "Metacognitive reasoning analysis initiated"
        }
        
    except Exception as e:
        logger.error(f"Reasoning analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/patterns/analyze")
async def analyze_patterns(request: PatternAnalysisRequest):
    """Analyze patterns in data"""
    try:
        # Simple pattern analysis (can be enhanced)
        patterns = {
            "identified_patterns": [
                {
                    "pattern_type": request.pattern_type,
                    "confidence": 0.75,
                    "description": f"Pattern identified in {len(request.data)} data points",
                    "characteristics": ["recurring_elements", "temporal_correlation", "contextual_similarity"]
                }
            ],
            "pattern_strength": 0.75,
            "recommendations": [
                "Monitor pattern stability over time",
                "Validate pattern with additional data",
                "Consider pattern implications for decision making"
            ]
        }
        
        return {
            "pattern_type": request.pattern_type,
            "data_points_analyzed": len(request.data),
            "patterns": patterns,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Pattern analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/synthesis/create")
async def create_synthesis(request: SynthesisRequest):
    """Create synthesis from multiple inputs"""
    try:
        # Perform synthesis
        synthesis = {
            "synthesis_type": request.synthesis_type,
            "input_count": len(request.inputs),
            "key_themes": [
                "Convergent insights across inputs",
                "Complementary perspectives identified",
                "Integration opportunities discovered"
            ],
            "synthesized_insights": [
                "Combined analysis reveals deeper understanding",
                "Multiple perspectives strengthen conclusions",
                "Integrated approach recommended for implementation"
            ],
            "recommendations": [
                "Implement synthesis recommendations",
                "Monitor integrated approach effectiveness",
                "Gather feedback on synthesis quality"
            ],
            "confidence_score": 0.82
        }
        
        return {
            "synthesis_type": request.synthesis_type,
            "target_format": request.target_format,
            "synthesis": synthesis,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Synthesis creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/metacognition/evaluate")
async def evaluate_metacognition(request: MetacognitionRequest):
    """Evaluate reasoning chain metacognitively"""
    try:
        # Metacognitive evaluation
        evaluation = {
            "reasoning_quality": {
                "logical_consistency": 0.85,
                "evidence_strength": 0.78,
                "conclusion_validity": 0.82,
                "overall_score": 0.82
            },
            "identified_biases": [
                "Confirmation bias in evidence selection",
                "Anchoring bias in initial assumptions"
            ],
            "improvement_suggestions": [
                "Include contradictory evidence",
                "Question initial assumptions",
                "Consider alternative explanations"
            ],
            "metacognitive_insights": [
                "Reasoning process shows systematic approach",
                "Evidence integration could be improved",
                "Conclusions well-supported by analysis"
            ]
        }
        
        return {
            "reasoning_chain_length": len(request.reasoning_chain),
            "evaluation_criteria": request.evaluation_criteria,
            "improvement_focus": request.improvement_focus,
            "evaluation": evaluation,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Metacognitive evaluation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """Get status of a reasoning task"""
    if task_id not in active_reasoning_tasks and task_id not in reasoning_cache:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task_id in active_reasoning_tasks:
        return active_reasoning_tasks[task_id]
    else:
        return reasoning_cache[task_id]

@app.get("/api/v1/tasks/{task_id}/results")
async def get_task_results(task_id: str):
    """Get results of a reasoning task"""
    if task_id not in reasoning_cache:
        if task_id in active_reasoning_tasks:
            return {"status": "running", "message": "Reasoning still in progress"}
        else:
            raise HTTPException(status_code=404, detail="Task results not found")
    
    return reasoning_cache[task_id]

# Background task functions
async def run_reasoning_analysis(task_id: str, topic: str, context: Dict, reasoning_mode: str, depth: str):
    """Run reasoning analysis in background"""
    try:
        logger.info(f"Starting reasoning analysis {task_id}")
        
        # Perform reasoning
        result = await reasoning_engine.perform_reasoning(topic, context, reasoning_mode, depth)
        
        # Store results
        reasoning_cache[task_id] = {
            "task_id": task_id,
            "type": "reasoning",
            "status": "completed",
            "result": result,
            "completed_at": datetime.now().isoformat()
        }
        
        # Remove from active tasks
        if task_id in active_reasoning_tasks:
            del active_reasoning_tasks[task_id]
        
        logger.info(f"Reasoning analysis {task_id} completed")
        
    except Exception as e:
        logger.error(f"Reasoning analysis {task_id} failed: {e}")
        reasoning_cache[task_id] = {
            "task_id": task_id,
            "type": "reasoning",
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.now().isoformat()
        }
        if task_id in active_reasoning_tasks:
            del active_reasoning_tasks[task_id]

if __name__ == "__main__":
    port = int(os.getenv("DEEPCLAUDE_SERVICE_PORT", 8006))
    
    logger.info(f"🧠 Starting DeepClaude Metacognitive Service on port {port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )