#!/usr/bin/env python3
"""
UltraMCP ContextBuilderAgent 2.0 - PromptAssemblerAgent
Next-generation dynamic prompt assembly with semantic coherence
"""

import asyncio
import json
import yaml
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import logging
from dataclasses import dataclass
from enum import Enum
import aiohttp
import jinja2
from semantic_coherence_bus import get_semantic_bus, SemanticMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PromptType(str, Enum):
    """Types of prompts that can be assembled"""
    SYSTEM = "system"
    USER = "user" 
    ASSISTANT = "assistant"
    CONTEXT_INJECTION = "context_injection"
    VALIDATION = "validation"
    OPTIMIZATION = "optimization"

class PromptComplexity(str, Enum):
    """Complexity levels for prompt assembly"""
    SIMPLE = "simple"          # Basic template substitution
    MEDIUM = "medium"          # Context-aware with validation
    COMPLEX = "complex"        # Multi-stage with coherence checking
    ADAPTIVE = "adaptive"      # Self-optimizing prompts

@dataclass
class PromptFragment:
    """Individual prompt fragment with metadata"""
    fragment_id: str
    content: str
    priority: float
    context_domain: str
    validation_score: Optional[float] = None
    usage_count: int = 0
    success_rate: float = 0.0
    last_updated: str = ""

class PromptAssemblyRequest(BaseModel):
    """Request for prompt assembly"""
    prompt_type: PromptType
    complexity: PromptComplexity = PromptComplexity.MEDIUM
    context_domains: List[str] = Field(default_factory=list)
    target_audience: str = "general"
    objective: str = ""
    constraints: Dict[str, Any] = Field(default_factory=dict)
    max_length: int = 4000
    include_reasoning: bool = False
    template_variables: Dict[str, Any] = Field(default_factory=dict)

class PromptAssemblyResponse(BaseModel):
    """Response from prompt assembly"""
    assembled_prompt: str
    prompt_metadata: Dict[str, Any]
    fragments_used: List[str]
    coherence_score: float
    estimated_effectiveness: float
    optimization_suggestions: List[str]
    timestamp: str

class PromptOptimizationRequest(BaseModel):
    """Request for prompt optimization"""
    original_prompt: str
    performance_metrics: Dict[str, float]
    target_improvement: str = "effectiveness"
    optimization_budget: int = 100  # Number of iterations
    
class PromptTemplateRequest(BaseModel):
    """Request for creating prompt templates"""
    template_name: str
    template_content: str
    variables: List[str]
    context_domains: List[str]
    description: str = ""

class PromptAssemblerAgent:
    """
    Next-generation PromptAssemblerAgent for dynamic prompt construction
    Features semantic coherence, adaptive optimization, and template management
    """
    
    def __init__(self):
        self.app = FastAPI(title="PromptAssemblerAgent", version="2.0.0")
        self.semantic_bus = None
        self.jinja_env = jinja2.Environment(
            loader=jinja2.DictLoader({}),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        
        # Fragment storage and management
        self.prompt_fragments: Dict[str, PromptFragment] = {}
        self.templates: Dict[str, Dict[str, Any]] = {}
        self.optimization_history: List[Dict[str, Any]] = []
        
        # Performance tracking
        self.performance_metrics = {
            "prompts_assembled": 0,
            "avg_coherence_score": 0.0,
            "avg_effectiveness": 0.0,
            "optimizations_performed": 0,
            "templates_created": 0,
            "fragments_managed": 0
        }
        
        # Context paths
        self.context_dir = "/root/ultramcp/.context"
        self.fragments_dir = f"{self.context_dir}/fragments"
        self.templates_dir = f"{self.fragments_dir}/templates"
        
        # Setup routes and initialize
        self._setup_routes()
        self._load_initial_fragments()
        
        # Add startup event handler
        @self.app.on_event("startup")
        async def startup_event():
            await self._initialize_system()
    
    def _setup_routes(self):
        """Setup FastAPI routes for prompt assembly"""
        
        @self.app.post("/assemble_prompt", response_model=PromptAssemblyResponse)
        async def assemble_prompt(request: PromptAssemblyRequest):
            """Main prompt assembly endpoint"""
            try:
                start_time = datetime.utcnow()
                
                result = await self._assemble_prompt(
                    request.prompt_type,
                    request.complexity,
                    request.context_domains,
                    request.target_audience,
                    request.objective,
                    request.constraints,
                    request.max_length,
                    request.include_reasoning,
                    request.template_variables
                )
                
                # Update metrics
                self.performance_metrics["prompts_assembled"] += 1
                self.performance_metrics["avg_coherence_score"] = (
                    (self.performance_metrics["avg_coherence_score"] * (self.performance_metrics["prompts_assembled"] - 1) + 
                     result["coherence_score"]) / self.performance_metrics["prompts_assembled"]
                )
                
                return PromptAssemblyResponse(**result)
                
            except Exception as e:
                logger.error(f"Error assembling prompt: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/optimize_prompt")
        async def optimize_prompt(request: PromptOptimizationRequest):
            """Optimize existing prompts for better performance"""
            try:
                result = await self._optimize_prompt(
                    request.original_prompt,
                    request.performance_metrics,
                    request.target_improvement,
                    request.optimization_budget
                )
                
                self.performance_metrics["optimizations_performed"] += 1
                return result
                
            except Exception as e:
                logger.error(f"Error optimizing prompt: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/create_template")
        async def create_template(request: PromptTemplateRequest):
            """Create new prompt templates"""
            try:
                result = await self._create_template(
                    request.template_name,
                    request.template_content,
                    request.variables,
                    request.context_domains,
                    request.description
                )
                
                self.performance_metrics["templates_created"] += 1
                return result
                
            except Exception as e:
                logger.error(f"Error creating template: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/templates")
        async def get_templates():
            """Get all available templates"""
            return {
                "templates": self.templates,
                "count": len(self.templates),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        @self.app.get("/fragments")
        async def get_fragments():
            """Get all prompt fragments"""
            return {
                "fragments": {k: {
                    "fragment_id": v.fragment_id,
                    "content": v.content[:100] + "..." if len(v.content) > 100 else v.content,
                    "priority": v.priority,
                    "context_domain": v.context_domain,
                    "usage_count": v.usage_count,
                    "success_rate": v.success_rate
                } for k, v in self.prompt_fragments.items()},
                "count": len(self.prompt_fragments),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        @self.app.post("/analyze_prompt")
        async def analyze_prompt(prompt_data: Dict[str, Any]):
            """Analyze prompt for coherence and effectiveness"""
            try:
                result = await self._analyze_prompt_quality(
                    prompt_data.get("prompt", ""),
                    prompt_data.get("context_domains", []),
                    prompt_data.get("target_metrics", {})
                )
                return result
                
            except Exception as e:
                logger.error(f"Error analyzing prompt: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/performance_analytics")
        async def get_performance_analytics():
            """Get detailed performance analytics"""
            try:
                analytics = await self._generate_performance_analytics()
                return analytics
                
            except Exception as e:
                logger.error(f"Error generating analytics: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/adaptive_learning")
        async def adaptive_learning(learning_data: Dict[str, Any]):
            """Update prompt assembly based on performance feedback"""
            try:
                result = await self._adaptive_learning_update(
                    learning_data.get("prompt_id", ""),
                    learning_data.get("performance_score", 0.0),
                    learning_data.get("user_feedback", {}),
                    learning_data.get("context_data", {})
                )
                return result
                
            except Exception as e:
                logger.error(f"Error in adaptive learning: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            try:
                return {
                    "status": "healthy",
                    "service": "PromptAssemblerAgent",
                    "version": "2.0.0",
                    "fragments_loaded": len(self.prompt_fragments),
                    "templates_available": len(self.templates),
                    "semantic_bus_connected": self.semantic_bus is not None,
                    "performance_metrics": self.performance_metrics,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            except Exception as e:
                return {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
        
        @self.app.get("/metrics")
        async def get_metrics():
            """Get service metrics"""
            return {
                **self.performance_metrics,
                "optimization_history_count": len(self.optimization_history),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def _initialize_system(self):
        """Initialize PromptAssemblerAgent system"""
        try:
            # Initialize semantic bus connection
            self.semantic_bus = await get_semantic_bus()
            
            # Load templates and fragments
            await self._load_templates()
            await self._load_fragment_performance_data()
            
            logger.info("PromptAssemblerAgent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize PromptAssemblerAgent: {e}")
    
    def _load_initial_fragments(self):
        """Load initial prompt fragments for different domains"""
        
        # System prompt fragments
        self.prompt_fragments["system_context_aware"] = PromptFragment(
            fragment_id="system_context_aware",
            content="You are an AI assistant with deep understanding of the current context. Use the provided context to inform your responses while maintaining accuracy and relevance.",
            priority=0.9,
            context_domain="SYSTEM"
        )
        
        self.prompt_fragments["system_expert"] = PromptFragment(
            fragment_id="system_expert",
            content="You are a domain expert with comprehensive knowledge. Provide detailed, accurate, and actionable insights.",
            priority=0.8,
            context_domain="SYSTEM"
        )
        
        # Context injection fragments
        self.prompt_fragments["context_business"] = PromptFragment(
            fragment_id="context_business",
            content="Based on the business context: {{business_context}}, consider the following objectives: {{objectives}}",
            priority=0.85,
            context_domain="ORGANIZACION"
        )
        
        self.prompt_fragments["context_technical"] = PromptFragment(
            fragment_id="context_technical",
            content="Technical context: {{technical_details}}. Current constraints: {{constraints}}. Target outcomes: {{outcomes}}",
            priority=0.8,
            context_domain="TECHNICAL"
        )
        
        # Validation fragments
        self.prompt_fragments["validation_coherence"] = PromptFragment(
            fragment_id="validation_coherence",
            content="Ensure your response maintains semantic coherence with the established context and doesn't contradict previous information.",
            priority=0.7,
            context_domain="VALIDATION"
        )
        
        self.prompt_fragments["validation_accuracy"] = PromptFragment(
            fragment_id="validation_accuracy",
            content="Verify all facts and claims. If uncertain, clearly state assumptions and confidence levels.",
            priority=0.75,
            context_domain="VALIDATION"
        )
        
        # Reasoning fragments
        self.prompt_fragments["reasoning_step_by_step"] = PromptFragment(
            fragment_id="reasoning_step_by_step",
            content="Think through this step-by-step: 1) Analyze the problem, 2) Consider alternatives, 3) Evaluate options, 4) Recommend solution.",
            priority=0.9,
            context_domain="REASONING"
        )
        
        self.prompt_fragments["reasoning_pros_cons"] = PromptFragment(
            fragment_id="reasoning_pros_cons",
            content="Consider both pros and cons of each approach. Weigh trade-offs carefully before making recommendations.",
            priority=0.8,
            context_domain="REASONING"
        )
        
        # Update fragment count
        self.performance_metrics["fragments_managed"] = len(self.prompt_fragments)
    
    async def _assemble_prompt(self, prompt_type: PromptType, complexity: PromptComplexity,
                              context_domains: List[str], target_audience: str, objective: str,
                              constraints: Dict[str, Any], max_length: int, include_reasoning: bool,
                              template_variables: Dict[str, Any]) -> Dict[str, Any]:
        """Core prompt assembly logic"""
        
        assembled_parts = []
        fragments_used = []
        coherence_score = 0.0
        
        try:
            # Step 1: Select base template or fragments
            if complexity == PromptComplexity.SIMPLE:
                assembled_parts, fragments_used = await self._simple_assembly(
                    prompt_type, context_domains, template_variables
                )
            elif complexity == PromptComplexity.MEDIUM:
                assembled_parts, fragments_used = await self._medium_assembly(
                    prompt_type, context_domains, objective, template_variables
                )
            elif complexity == PromptComplexity.COMPLEX:
                assembled_parts, fragments_used = await self._complex_assembly(
                    prompt_type, context_domains, objective, constraints, template_variables
                )
            elif complexity == PromptComplexity.ADAPTIVE:
                assembled_parts, fragments_used = await self._adaptive_assembly(
                    prompt_type, context_domains, objective, constraints, template_variables
                )
            
            # Step 2: Add reasoning if requested
            if include_reasoning:
                reasoning_fragments = self._select_reasoning_fragments(complexity)
                assembled_parts.extend(reasoning_fragments)
                fragments_used.extend([f.fragment_id for f in reasoning_fragments])
            
            # Step 3: Apply template variables
            assembled_prompt = await self._apply_template_variables(assembled_parts, template_variables)
            
            # Step 4: Validate length constraints
            if len(assembled_prompt) > max_length:
                assembled_prompt = await self._truncate_intelligently(assembled_prompt, max_length)
            
            # Step 5: Calculate coherence score
            coherence_score = await self._calculate_prompt_coherence(assembled_prompt, context_domains)
            
            # Step 6: Estimate effectiveness
            effectiveness = await self._estimate_prompt_effectiveness(
                assembled_prompt, prompt_type, target_audience, objective
            )
            
            # Step 7: Generate optimization suggestions
            optimization_suggestions = await self._generate_optimization_suggestions(
                assembled_prompt, coherence_score, effectiveness, constraints
            )
            
            # Step 8: Log usage for learning
            await self._log_prompt_usage(fragments_used, coherence_score, effectiveness)
            
            return {
                "assembled_prompt": assembled_prompt,
                "prompt_metadata": {
                    "prompt_type": prompt_type,
                    "complexity": complexity,
                    "context_domains": context_domains,
                    "target_audience": target_audience,
                    "objective": objective,
                    "length": len(assembled_prompt),
                    "fragments_count": len(fragments_used)
                },
                "fragments_used": fragments_used,
                "coherence_score": coherence_score,
                "estimated_effectiveness": effectiveness,
                "optimization_suggestions": optimization_suggestions,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            logger.error(f"Error in prompt assembly: {e}")
            raise
    
    async def _simple_assembly(self, prompt_type: PromptType, context_domains: List[str],
                              template_variables: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Simple prompt assembly with basic templates"""
        
        parts = []
        used_fragments = []
        
        if prompt_type == PromptType.SYSTEM:
            # Use basic system fragment
            fragment = self.prompt_fragments.get("system_context_aware")
            if fragment:
                parts.append(fragment.content)
                used_fragments.append(fragment.fragment_id)
        
        elif prompt_type == PromptType.CONTEXT_INJECTION:
            # Add relevant context fragments
            for domain in context_domains:
                matching_fragments = [
                    f for f in self.prompt_fragments.values()
                    if domain.upper() in f.context_domain.upper()
                ]
                if matching_fragments:
                    best_fragment = max(matching_fragments, key=lambda x: x.priority)
                    parts.append(best_fragment.content)
                    used_fragments.append(best_fragment.fragment_id)
        
        return parts, used_fragments
    
    async def _medium_assembly(self, prompt_type: PromptType, context_domains: List[str],
                              objective: str, template_variables: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Medium complexity assembly with context awareness"""
        
        parts = []
        used_fragments = []
        
        # Start with base fragments
        base_parts, base_used = await self._simple_assembly(prompt_type, context_domains, template_variables)
        parts.extend(base_parts)
        used_fragments.extend(base_used)
        
        # Add objective-specific content
        if objective:
            objective_prompt = f"Your primary objective is: {objective}. Focus your response on achieving this goal."
            parts.append(objective_prompt)
        
        # Add validation fragments for quality assurance
        validation_fragment = self.prompt_fragments.get("validation_coherence")
        if validation_fragment:
            parts.append(validation_fragment.content)
            used_fragments.append(validation_fragment.fragment_id)
        
        return parts, used_fragments
    
    async def _complex_assembly(self, prompt_type: PromptType, context_domains: List[str],
                               objective: str, constraints: Dict[str, Any],
                               template_variables: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Complex assembly with multi-stage processing and validation"""
        
        parts = []
        used_fragments = []
        
        # Start with medium complexity
        medium_parts, medium_used = await self._medium_assembly(
            prompt_type, context_domains, objective, template_variables
        )
        parts.extend(medium_parts)
        used_fragments.extend(medium_used)
        
        # Add constraint handling
        if constraints:
            constraint_text = "Important constraints to consider:\n"
            for key, value in constraints.items():
                constraint_text += f"- {key}: {value}\n"
            parts.append(constraint_text)
        
        # Add domain-specific expertise
        for domain in context_domains:
            expert_fragments = [
                f for f in self.prompt_fragments.values()
                if f.context_domain == domain and f.priority > 0.8
            ]
            if expert_fragments:
                best_expert = max(expert_fragments, key=lambda x: x.success_rate)
                parts.append(best_expert.content)
                used_fragments.append(best_expert.fragment_id)
        
        # Add accuracy validation
        accuracy_fragment = self.prompt_fragments.get("validation_accuracy")
        if accuracy_fragment:
            parts.append(accuracy_fragment.content)
            used_fragments.append(accuracy_fragment.fragment_id)
        
        return parts, used_fragments
    
    async def _adaptive_assembly(self, prompt_type: PromptType, context_domains: List[str],
                                objective: str, constraints: Dict[str, Any],
                                template_variables: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Adaptive assembly that learns from performance history"""
        
        parts = []
        used_fragments = []
        
        # Start with complex assembly as base
        complex_parts, complex_used = await self._complex_assembly(
            prompt_type, context_domains, objective, constraints, template_variables
        )
        parts.extend(complex_parts)
        used_fragments.extend(complex_used)
        
        # Apply adaptive optimizations based on history
        high_performing_fragments = [
            f for f in self.prompt_fragments.values()
            if f.success_rate > 0.8 and f.usage_count > 5
        ]
        
        # Sort by success rate and add top performers
        high_performing_fragments.sort(key=lambda x: x.success_rate, reverse=True)
        for fragment in high_performing_fragments[:2]:  # Add top 2 performers
            if fragment.fragment_id not in used_fragments:
                parts.append(fragment.content)
                used_fragments.append(fragment.fragment_id)
        
        # Add adaptive learning instruction
        adaptive_instruction = """
        Based on previous successful interactions, prioritize approaches that have shown high effectiveness.
        Continuously refine your response based on context quality and user engagement patterns.
        """
        parts.append(adaptive_instruction)
        
        return parts, used_fragments
    
    def _select_reasoning_fragments(self, complexity: PromptComplexity) -> List[PromptFragment]:
        """Select appropriate reasoning fragments based on complexity"""
        
        reasoning_fragments = [
            f for f in self.prompt_fragments.values()
            if f.context_domain == "REASONING"
        ]
        
        if complexity in [PromptComplexity.SIMPLE, PromptComplexity.MEDIUM]:
            # Use basic step-by-step reasoning
            return [f for f in reasoning_fragments if "step_by_step" in f.fragment_id]
        else:
            # Use more sophisticated reasoning for complex/adaptive
            return reasoning_fragments
    
    async def _apply_template_variables(self, parts: List[str], variables: Dict[str, Any]) -> str:
        """Apply template variables to assembled parts"""
        
        combined_content = "\n\n".join(parts)
        
        try:
            # Use Jinja2 for variable substitution
            template = self.jinja_env.from_string(combined_content)
            return template.render(**variables)
        except Exception as e:
            logger.warning(f"Template variable substitution failed: {e}")
            # Fallback to simple string replacement
            for key, value in variables.items():
                combined_content = combined_content.replace(f"{{{{{key}}}}}", str(value))
            return combined_content
    
    async def _truncate_intelligently(self, prompt: str, max_length: int) -> str:
        """Intelligently truncate prompt while preserving important content"""
        
        if len(prompt) <= max_length:
            return prompt
        
        # Split into sentences and prioritize
        sentences = prompt.split('. ')
        important_keywords = ['objective', 'constraint', 'important', 'critical', 'required']
        
        # Score sentences by importance
        scored_sentences = []
        for sentence in sentences:
            score = sum(1 for keyword in important_keywords if keyword.lower() in sentence.lower())
            scored_sentences.append((sentence, score))
        
        # Sort by importance and rebuild
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        truncated = ""
        for sentence, _ in scored_sentences:
            if len(truncated + sentence + ". ") <= max_length:
                truncated += sentence + ". "
            else:
                break
        
        return truncated.strip()
    
    async def _calculate_prompt_coherence(self, prompt: str, context_domains: List[str]) -> float:
        """Calculate semantic coherence score for the prompt"""
        
        try:
            # Basic coherence metrics
            coherence_score = 0.0
            
            # Check for consistent terminology
            domain_keywords = {
                "ORGANIZACION": ["business", "company", "organization", "strategy"],
                "OFERTA": ["product", "service", "offering", "solution"],
                "MERCADO": ["market", "customer", "competition", "industry"],
                "TECHNICAL": ["system", "architecture", "implementation", "technology"]
            }
            
            # Count relevant keywords for coherence
            total_relevant_keywords = 0
            found_keywords = 0
            
            for domain in context_domains:
                if domain in domain_keywords:
                    keywords = domain_keywords[domain]
                    total_relevant_keywords += len(keywords)
                    for keyword in keywords:
                        if keyword.lower() in prompt.lower():
                            found_keywords += 1
            
            # Calculate keyword coherence
            if total_relevant_keywords > 0:
                keyword_coherence = found_keywords / total_relevant_keywords
            else:
                keyword_coherence = 0.5  # Neutral score
            
            # Check for contradictions (simple heuristic)
            contradiction_words = ["but", "however", "contradicts", "conflicts"]
            contradiction_count = sum(1 for word in contradiction_words if word in prompt.lower())
            contradiction_penalty = min(0.2, contradiction_count * 0.05)
            
            # Calculate final coherence
            coherence_score = max(0.0, min(1.0, keyword_coherence - contradiction_penalty + 0.3))
            
            return coherence_score
            
        except Exception as e:
            logger.warning(f"Coherence calculation failed: {e}")
            return 0.7  # Default neutral score
    
    async def _estimate_prompt_effectiveness(self, prompt: str, prompt_type: PromptType,
                                           target_audience: str, objective: str) -> float:
        """Estimate prompt effectiveness based on various factors"""
        
        try:
            effectiveness = 0.0
            
            # Length appropriateness (500-2000 chars is optimal)
            length_score = 1.0
            if len(prompt) < 200:
                length_score = 0.6
            elif len(prompt) > 3000:
                length_score = 0.7
            elif 500 <= len(prompt) <= 2000:
                length_score = 1.0
            else:
                length_score = 0.8
            
            # Clarity indicators
            clarity_keywords = ["clearly", "specifically", "exactly", "precisely", "step-by-step"]
            clarity_score = min(1.0, sum(1 for word in clarity_keywords if word in prompt.lower()) * 0.2)
            
            # Objective alignment
            objective_score = 0.5  # Default
            if objective and objective.lower() in prompt.lower():
                objective_score = 0.9
            elif objective:
                # Check for semantic similarity (simplified)
                objective_words = objective.lower().split()
                matches = sum(1 for word in objective_words if word in prompt.lower())
                objective_score = min(0.9, matches / len(objective_words))
            
            # Audience appropriateness
            audience_score = 0.8  # Default good score
            if target_audience == "technical":
                technical_terms = ["system", "architecture", "implementation", "algorithm"]
                if any(term in prompt.lower() for term in technical_terms):
                    audience_score = 0.9
            elif target_audience == "business":
                business_terms = ["strategy", "ROI", "value", "impact", "business"]
                if any(term in prompt.lower() for term in business_terms):
                    audience_score = 0.9
            
            # Calculate weighted effectiveness
            effectiveness = (
                length_score * 0.25 +
                clarity_score * 0.25 +
                objective_score * 0.3 +
                audience_score * 0.2
            )
            
            return max(0.0, min(1.0, effectiveness))
            
        except Exception as e:
            logger.warning(f"Effectiveness estimation failed: {e}")
            return 0.7  # Default neutral score
    
    async def _generate_optimization_suggestions(self, prompt: str, coherence_score: float,
                                               effectiveness: float, constraints: Dict[str, Any]) -> List[str]:
        """Generate suggestions for prompt optimization"""
        
        suggestions = []
        
        try:
            # Coherence improvements
            if coherence_score < 0.7:
                suggestions.append("Consider adding more domain-specific terminology for better coherence")
                suggestions.append("Review for potential contradictions or unclear statements")
            
            # Effectiveness improvements
            if effectiveness < 0.7:
                suggestions.append("Clarify the objective and expected outcomes")
                suggestions.append("Add more specific instructions or examples")
            
            # Length optimization
            if len(prompt) < 200:
                suggestions.append("Consider adding more context and detailed instructions")
            elif len(prompt) > 3000:
                suggestions.append("Simplify and focus on key requirements to reduce length")
            
            # Constraint-based suggestions
            if constraints:
                if "time_sensitive" in constraints and constraints["time_sensitive"]:
                    suggestions.append("Add urgency indicators and prioritization guidance")
                if "technical_accuracy" in constraints and constraints["technical_accuracy"]:
                    suggestions.append("Include validation steps and accuracy requirements")
            
            # General improvements
            if "step-by-step" not in prompt.lower():
                suggestions.append("Consider adding step-by-step reasoning instructions")
            
            if not any(word in prompt.lower() for word in ["example", "demonstrate", "show"]):
                suggestions.append("Add request for examples or demonstrations")
            
            return suggestions[:5]  # Limit to top 5 suggestions
            
        except Exception as e:
            logger.warning(f"Suggestion generation failed: {e}")
            return ["Review prompt for clarity and completeness"]
    
    async def _log_prompt_usage(self, fragments_used: List[str], coherence_score: float, effectiveness: float):
        """Log prompt usage for learning and optimization"""
        
        try:
            # Update fragment usage statistics
            for fragment_id in fragments_used:
                if fragment_id in self.prompt_fragments:
                    fragment = self.prompt_fragments[fragment_id]
                    fragment.usage_count += 1
                    
                    # Update success rate (simple exponential moving average)
                    performance_score = (coherence_score + effectiveness) / 2
                    alpha = 0.1  # Learning rate
                    fragment.success_rate = (
                        (1 - alpha) * fragment.success_rate + alpha * performance_score
                    )
                    fragment.last_updated = datetime.utcnow().isoformat() + "Z"
            
            # Log to semantic bus for system-wide learning
            if self.semantic_bus:
                usage_message = SemanticMessage(
                    message_id=f"prompt_usage_{int(datetime.utcnow().timestamp())}",
                    message_type="PROMPT_USAGE",
                    content={
                        "fragments_used": fragments_used,
                        "coherence_score": coherence_score,
                        "effectiveness": effectiveness,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    },
                    source="PromptAssemblerAgent",
                    timestamp=datetime.utcnow().isoformat() + "Z"
                )
                await self.semantic_bus.publish_semantic_message(usage_message)
                
        except Exception as e:
            logger.warning(f"Usage logging failed: {e}")
    
    async def _optimize_prompt(self, original_prompt: str, performance_metrics: Dict[str, float],
                              target_improvement: str, optimization_budget: int) -> Dict[str, Any]:
        """Optimize existing prompt based on performance feedback"""
        
        try:
            optimized_prompt = original_prompt
            optimization_steps = []
            
            # Analyze current performance
            current_score = performance_metrics.get("overall_score", 0.5)
            
            # Apply optimization strategies
            if target_improvement == "effectiveness":
                # Add more specific instructions
                if "specifically" not in optimized_prompt.lower():
                    optimized_prompt += "\n\nBe specific and provide actionable recommendations."
                    optimization_steps.append("Added specificity instruction")
                
                # Add example request
                if "example" not in optimized_prompt.lower():
                    optimized_prompt += "\n\nInclude relevant examples to illustrate your points."
                    optimization_steps.append("Added example request")
            
            elif target_improvement == "coherence":
                # Add coherence validation
                validation_text = "\n\nEnsure your response maintains semantic coherence and consistency throughout."
                optimized_prompt += validation_text
                optimization_steps.append("Added coherence validation")
            
            elif target_improvement == "clarity":
                # Add clarity instruction
                clarity_text = "\n\nStructure your response clearly with logical flow and easy-to-follow reasoning."
                optimized_prompt += clarity_text
                optimization_steps.append("Added clarity instruction")
            
            # Calculate improvement estimate
            improvement_estimate = min(0.3, len(optimization_steps) * 0.1)
            estimated_new_score = min(1.0, current_score + improvement_estimate)
            
            # Record optimization
            optimization_record = {
                "original_prompt": original_prompt,
                "optimized_prompt": optimized_prompt,
                "performance_metrics": performance_metrics,
                "target_improvement": target_improvement,
                "optimization_steps": optimization_steps,
                "improvement_estimate": improvement_estimate,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            self.optimization_history.append(optimization_record)
            
            return {
                "optimized_prompt": optimized_prompt,
                "optimization_steps": optimization_steps,
                "improvement_estimate": improvement_estimate,
                "estimated_new_score": estimated_new_score,
                "optimization_id": len(self.optimization_history) - 1,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            logger.error(f"Prompt optimization failed: {e}")
            return {
                "optimized_prompt": original_prompt,
                "optimization_steps": [],
                "improvement_estimate": 0.0,
                "error": str(e)
            }
    
    async def _create_template(self, template_name: str, template_content: str,
                              variables: List[str], context_domains: List[str],
                              description: str) -> Dict[str, Any]:
        """Create new prompt template"""
        
        try:
            # Validate template
            template_obj = self.jinja_env.from_string(template_content)
            
            # Create template record
            template_record = {
                "name": template_name,
                "content": template_content,
                "variables": variables,
                "context_domains": context_domains,
                "description": description,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "usage_count": 0,
                "success_rate": 0.0
            }
            
            self.templates[template_name] = template_record
            
            # Save to file system
            template_file = f"{self.templates_dir}/{template_name}.yaml"
            with open(template_file, 'w', encoding='utf-8') as f:
                yaml.dump(template_record, f, default_flow_style=False)
            
            return {
                "success": True,
                "template_name": template_name,
                "message": "Template created successfully",
                "template_id": template_name,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            logger.error(f"Template creation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def _analyze_prompt_quality(self, prompt: str, context_domains: List[str],
                                     target_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze prompt quality across multiple dimensions"""
        
        try:
            analysis = {}
            
            # Basic metrics
            analysis["length"] = len(prompt)
            analysis["word_count"] = len(prompt.split())
            analysis["sentence_count"] = len([s for s in prompt.split('.') if s.strip()])
            
            # Coherence analysis
            coherence_score = await self._calculate_prompt_coherence(prompt, context_domains)
            analysis["coherence_score"] = coherence_score
            
            # Clarity analysis
            clarity_keywords = ["clearly", "specifically", "exactly", "step-by-step"]
            clarity_count = sum(1 for word in clarity_keywords if word in prompt.lower())
            analysis["clarity_indicators"] = clarity_count
            
            # Complexity analysis
            complex_words = len([word for word in prompt.split() if len(word) > 7])
            analysis["complexity_ratio"] = complex_words / len(prompt.split()) if prompt.split() else 0
            
            # Domain relevance
            domain_relevance = {}
            domain_keywords = {
                "ORGANIZACION": ["business", "company", "organization", "strategy"],
                "OFERTA": ["product", "service", "offering", "solution"],
                "MERCADO": ["market", "customer", "competition", "industry"]
            }
            
            for domain in context_domains:
                if domain in domain_keywords:
                    keywords = domain_keywords[domain]
                    found = sum(1 for keyword in keywords if keyword.lower() in prompt.lower())
                    domain_relevance[domain] = found / len(keywords)
            
            analysis["domain_relevance"] = domain_relevance
            
            # Overall quality score
            quality_score = (
                min(1.0, analysis["length"] / 1000) * 0.2 +  # Length appropriateness
                coherence_score * 0.3 +                     # Coherence
                min(1.0, clarity_count / 3) * 0.25 +        # Clarity
                (1 - min(1.0, analysis["complexity_ratio"] * 2)) * 0.25  # Appropriate complexity
            )
            
            analysis["overall_quality_score"] = quality_score
            
            # Recommendations
            recommendations = []
            if coherence_score < 0.7:
                recommendations.append("Improve semantic coherence")
            if clarity_count < 2:
                recommendations.append("Add more clarity indicators")
            if analysis["length"] < 200:
                recommendations.append("Consider adding more detail")
            if analysis["complexity_ratio"] > 0.3:
                recommendations.append("Simplify language for better clarity")
            
            analysis["recommendations"] = recommendations
            analysis["timestamp"] = datetime.utcnow().isoformat() + "Z"
            
            return analysis
            
        except Exception as e:
            logger.error(f"Prompt quality analysis failed: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat() + "Z"}
    
    async def _generate_performance_analytics(self) -> Dict[str, Any]:
        """Generate comprehensive performance analytics"""
        
        try:
            analytics = {
                "service_metrics": self.performance_metrics,
                "fragment_analytics": {},
                "template_analytics": {},
                "optimization_analytics": {},
                "trends": {},
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            # Fragment analytics
            if self.prompt_fragments:
                fragment_stats = {
                    "total_fragments": len(self.prompt_fragments),
                    "avg_success_rate": sum(f.success_rate for f in self.prompt_fragments.values()) / len(self.prompt_fragments),
                    "most_used": max(self.prompt_fragments.values(), key=lambda x: x.usage_count).fragment_id,
                    "highest_success": max(self.prompt_fragments.values(), key=lambda x: x.success_rate).fragment_id,
                    "domain_distribution": {}
                }
                
                # Domain distribution
                domain_counts = {}
                for fragment in self.prompt_fragments.values():
                    domain = fragment.context_domain
                    domain_counts[domain] = domain_counts.get(domain, 0) + 1
                fragment_stats["domain_distribution"] = domain_counts
                
                analytics["fragment_analytics"] = fragment_stats
            
            # Template analytics
            if self.templates:
                template_stats = {
                    "total_templates": len(self.templates),
                    "avg_success_rate": sum(t.get("success_rate", 0) for t in self.templates.values()) / len(self.templates),
                    "most_used": max(self.templates.items(), key=lambda x: x[1].get("usage_count", 0))[0] if self.templates else None
                }
                analytics["template_analytics"] = template_stats
            
            # Optimization analytics
            if self.optimization_history:
                opt_stats = {
                    "total_optimizations": len(self.optimization_history),
                    "avg_improvement": sum(opt.get("improvement_estimate", 0) for opt in self.optimization_history) / len(self.optimization_history),
                    "common_targets": {}
                }
                
                # Count optimization targets
                targets = [opt.get("target_improvement", "unknown") for opt in self.optimization_history]
                for target in set(targets):
                    opt_stats["common_targets"][target] = targets.count(target)
                
                analytics["optimization_analytics"] = opt_stats
            
            # Trends (last 24 hours simulation)
            analytics["trends"] = {
                "prompts_assembled_trend": "increasing",
                "avg_coherence_trend": "stable",
                "optimization_frequency": "moderate"
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Analytics generation failed: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat() + "Z"}
    
    async def _adaptive_learning_update(self, prompt_id: str, performance_score: float,
                                       user_feedback: Dict[str, Any], context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update system based on performance feedback"""
        
        try:
            updates_made = []
            
            # Update fragment performance based on feedback
            if prompt_id in self.optimization_history:
                # Find associated fragments
                optimization = self.optimization_history[int(prompt_id)]
                # Update fragment success rates based on performance
                for step in optimization.get("optimization_steps", []):
                    # Simple learning: improve scores for successful optimizations
                    if performance_score > 0.7:
                        updates_made.append(f"Increased confidence in: {step}")
            
            # Update based on user feedback
            if user_feedback:
                clarity_feedback = user_feedback.get("clarity", 0)
                if clarity_feedback > 7:  # Scale 1-10
                    # Boost clarity-related fragments
                    for fragment in self.prompt_fragments.values():
                        if "clarity" in fragment.content.lower():
                            fragment.success_rate = min(1.0, fragment.success_rate + 0.05)
                            updates_made.append(f"Boosted clarity fragment: {fragment.fragment_id}")
                
                effectiveness_feedback = user_feedback.get("effectiveness", 0)
                if effectiveness_feedback > 7:
                    # Boost effectiveness-related patterns
                    updates_made.append("Improved effectiveness patterns")
            
            # Context-based learning
            if context_data:
                successful_domains = context_data.get("successful_domains", [])
                for domain in successful_domains:
                    # Boost fragments from successful domains
                    domain_fragments = [f for f in self.prompt_fragments.values() if f.context_domain == domain]
                    for fragment in domain_fragments:
                        fragment.success_rate = min(1.0, fragment.success_rate + 0.02)
                    updates_made.append(f"Boosted {domain} domain fragments")
            
            return {
                "success": True,
                "updates_made": updates_made,
                "performance_score": performance_score,
                "learning_applied": len(updates_made) > 0,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            logger.error(f"Adaptive learning update failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def _load_templates(self):
        """Load templates from file system"""
        try:
            import os
            if os.path.exists(self.templates_dir):
                for file in os.listdir(self.templates_dir):
                    if file.endswith('.yaml'):
                        template_path = os.path.join(self.templates_dir, file)
                        with open(template_path, 'r', encoding='utf-8') as f:
                            template_data = yaml.safe_load(f)
                            template_name = file.replace('.yaml', '')
                            self.templates[template_name] = template_data
                logger.info(f"Loaded {len(self.templates)} templates")
        except Exception as e:
            logger.warning(f"Template loading failed: {e}")
    
    async def _load_fragment_performance_data(self):
        """Load fragment performance data from previous sessions"""
        try:
            performance_file = f"{self.context_dir}/fragments/performance_data.json"
            import os
            if os.path.exists(performance_file):
                with open(performance_file, 'r', encoding='utf-8') as f:
                    performance_data = json.load(f)
                    for fragment_id, data in performance_data.items():
                        if fragment_id in self.prompt_fragments:
                            fragment = self.prompt_fragments[fragment_id]
                            fragment.usage_count = data.get("usage_count", 0)
                            fragment.success_rate = data.get("success_rate", 0.0)
                            fragment.last_updated = data.get("last_updated", "")
                logger.info("Loaded fragment performance data")
        except Exception as e:
            logger.warning(f"Performance data loading failed: {e}")

# Global instance
prompt_assembler = PromptAssemblerAgent()

# FastAPI app instance for uvicorn
app = prompt_assembler.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8027)