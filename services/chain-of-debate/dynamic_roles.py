"""
Dynamic Role Orchestrator para Chain-of-Debate SuperMCP

Sistema de asignación contextual de roles que analiza el contenido de la tarea
y asigna especialidades específicas a cada modelo LLM basado en:
- Análisis semántico del contenido
- Dominio de la tarea 
- Contexto del cliente
- Complejidad detectada
- Riesgo regulatorio

Roles Especializados:
- CFO Conservative/Growth: Perspectivas financieras
- CTO Pragmatic/Innovative: Enfoque técnico
- CMO Brand/Growth: Estrategia de marketing  
- Legal Compliance/Business: Análisis legal
- Strategy Execution/Vision: Dirección estratégica
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import openai
from datetime import datetime

logger = logging.getLogger(__name__)

class RoleType(Enum):
    """Tipos de roles especializados"""
    CFO_CONSERVATIVE = "cfo_conservative"
    CFO_GROWTH = "cfo_growth"
    CTO_PRAGMATIC = "cto_pragmatic"
    CTO_INNOVATIVE = "cto_innovative"
    CMO_BRAND = "cmo_brand"
    CMO_GROWTH = "cmo_growth"
    LEGAL_COMPLIANCE = "legal_compliance"
    LEGAL_BUSINESS = "legal_business"
    STRATEGY_EXECUTION = "strategy_execution"
    STRATEGY_VISION = "strategy_vision"

class ModelProvider(Enum):
    """Proveedores de modelos LLM"""
    GPT4 = "gpt-4"
    CLAUDE = "claude-3-sonnet"
    GEMINI = "gemini-pro"

@dataclass
class RoleAssignment:
    """Asignación de rol para un modelo específico"""
    model: ModelProvider
    role: RoleType
    context_factors: Dict[str, float]
    assignment_reason: str
    confidence: float

@dataclass
class ContextAnalysis:
    """Análisis contextual de una tarea"""
    domain_indicators: Dict[str, float]
    complexity_score: float
    risk_level: float
    innovation_vs_conservative: float
    financial_impact: float
    technical_complexity: float
    regulatory_risk: float
    brand_sensitivity: float
    
class DynamicRoleOrchestrator:
    """
    Orquestador de roles dinámicos que asigna especialidades contextualmente
    """
    
    def __init__(self):
        self.role_definitions = self._load_role_definitions()
        self.context_keywords = self._load_context_keywords()
        self.assignment_history = []
        
        logger.info("🎭 Dynamic Role Orchestrator initialized")
    
    def assign_roles_by_context(
        self, 
        task_content: str, 
        domain: str,
        client_context: Dict[str, Any] = None
    ) -> Dict[str, RoleAssignment]:
        """
        Asignar roles especializados basados en análisis contextual
        
        Args:
            task_content: Contenido de la tarea a analizar
            domain: Dominio principal (proposal, content, contract, etc.)
            client_context: Contexto adicional del cliente
            
        Returns:
            Diccionario de asignaciones de roles por modelo
        """
        try:
            # Análisis contextual profundo
            context_analysis = self._analyze_task_context(task_content, domain, client_context)
            
            # Asignación optimizada de roles
            role_assignments = self._optimize_role_assignments(context_analysis, domain)
            
            # Log de la asignación
            self._log_assignment(task_content, context_analysis, role_assignments)
            
            logger.info(f"🎯 Roles assigned for {domain}: {[r.role.value for r in role_assignments.values()]}")
            
            return role_assignments
            
        except Exception as e:
            logger.error(f"Role assignment error: {e}")
            return self._get_default_assignments(domain)
    
    def _analyze_task_context(
        self, 
        content: str, 
        domain: str,
        client_context: Dict[str, Any] = None
    ) -> ContextAnalysis:
        """Analizar contexto profundo de la tarea"""
        
        # Análisis de palabras clave por categoría
        domain_scores = {}
        for category, keywords in self.context_keywords.items():
            score = sum(1 for keyword in keywords if keyword.lower() in content.lower())
            domain_scores[category] = score / len(keywords) if keywords else 0
        
        # Análisis de complejidad
        complexity_indicators = [
            len(content.split()) > 500,  # Longitud
            len(re.findall(r'\d+%|\$\d+', content)) > 3,  # Números/métricas
            'implementation' in content.lower(),  # Implementación
            'strategy' in content.lower(),  # Estrategia
            'integration' in content.lower()  # Integración
        ]
        complexity_score = sum(complexity_indicators) / len(complexity_indicators)
        
        # Análisis de riesgo
        risk_keywords = ['compliance', 'regulation', 'legal', 'audit', 'risk', 'security']
        risk_score = sum(1 for keyword in risk_keywords if keyword in content.lower()) / len(risk_keywords)
        
        # Innovation vs Conservative
        innovation_keywords = ['innovation', 'disrupt', 'new', 'cutting-edge', 'breakthrough']
        conservative_keywords = ['proven', 'stable', 'reliable', 'traditional', 'established']
        
        innovation_score = sum(1 for kw in innovation_keywords if kw in content.lower())
        conservative_score = sum(1 for kw in conservative_keywords if kw in content.lower())
        
        innovation_vs_conservative = (innovation_score - conservative_score) / max(innovation_score + conservative_score, 1)
        
        # Impacto financiero
        financial_keywords = ['revenue', 'cost', 'roi', 'budget', 'profit', 'investment']
        financial_impact = sum(1 for kw in financial_keywords if kw in content.lower()) / len(financial_keywords)
        
        # Complejidad técnica
        tech_keywords = ['api', 'architecture', 'development', 'integration', 'system']
        technical_complexity = sum(1 for kw in tech_keywords if kw in content.lower()) / len(tech_keywords)
        
        # Sensibilidad de marca
        brand_keywords = ['brand', 'reputation', 'image', 'customer', 'public']
        brand_sensitivity = sum(1 for kw in brand_keywords if kw in content.lower()) / len(brand_keywords)
        
        return ContextAnalysis(
            domain_indicators=domain_scores,
            complexity_score=complexity_score,
            risk_level=risk_score,
            innovation_vs_conservative=innovation_vs_conservative,
            financial_impact=financial_impact,
            technical_complexity=technical_complexity,
            regulatory_risk=risk_score,
            brand_sensitivity=brand_sensitivity
        )
    
    def _optimize_role_assignments(
        self, 
        context: ContextAnalysis, 
        domain: str
    ) -> Dict[str, RoleAssignment]:
        """Optimizar asignación de roles basado en análisis contextual"""
        
        assignments = {}
        
        # GPT-4: Asignación financiera/estratégica
        if context.financial_impact > 0.3 or domain == 'proposal':
            if context.innovation_vs_conservative > 0:
                gpt4_role = RoleType.CFO_GROWTH
                reason = f"Growth-oriented CFO for innovation focus (score: {context.innovation_vs_conservative:.2f})"
            else:
                gpt4_role = RoleType.CFO_CONSERVATIVE
                reason = f"Conservative CFO for stability focus (risk: {context.risk_level:.2f})"
        else:
            gpt4_role = RoleType.STRATEGY_EXECUTION if context.complexity_score > 0.5 else RoleType.STRATEGY_VISION
            reason = f"Strategic role based on complexity (score: {context.complexity_score:.2f})"
        
        assignments['gpt-4'] = RoleAssignment(
            model=ModelProvider.GPT4,
            role=gpt4_role,
            context_factors={"financial_impact": context.financial_impact, "innovation": context.innovation_vs_conservative},
            assignment_reason=reason,
            confidence=0.8 + (context.financial_impact * 0.2)
        )
        
        # Claude: Asignación técnica/legal
        if context.technical_complexity > 0.4 or domain == 'contract':
            if context.innovation_vs_conservative > 0.2:
                claude_role = RoleType.CTO_INNOVATIVE
                reason = f"Innovative CTO for technical innovation (complexity: {context.technical_complexity:.2f})"
            else:
                claude_role = RoleType.CTO_PRAGMATIC
                reason = f"Pragmatic CTO for reliable implementation (complexity: {context.technical_complexity:.2f})"
        elif context.regulatory_risk > 0.3:
            claude_role = RoleType.LEGAL_COMPLIANCE if context.regulatory_risk > 0.5 else RoleType.LEGAL_BUSINESS
            reason = f"Legal focus due to regulatory risk (risk: {context.regulatory_risk:.2f})"
        else:
            claude_role = RoleType.CTO_PRAGMATIC
            reason = "Default technical analysis role"
        
        assignments['claude'] = RoleAssignment(
            model=ModelProvider.CLAUDE,
            role=claude_role,
            context_factors={"technical_complexity": context.technical_complexity, "regulatory_risk": context.regulatory_risk},
            assignment_reason=reason,
            confidence=0.75 + (context.technical_complexity * 0.25)
        )
        
        # Gemini: Asignación marketing/estratégica
        if context.brand_sensitivity > 0.3 or domain == 'content':
            if 'growth' in domain.lower() or context.financial_impact > 0.4:
                gemini_role = RoleType.CMO_GROWTH
                reason = f"Growth CMO for expansion focus (brand sensitivity: {context.brand_sensitivity:.2f})"
            else:
                gemini_role = RoleType.CMO_BRAND
                reason = f"Brand CMO for reputation management (sensitivity: {context.brand_sensitivity:.2f})"
        else:
            gemini_role = RoleType.STRATEGY_VISION if context.innovation_vs_conservative > 0 else RoleType.STRATEGY_EXECUTION
            reason = f"Strategic vision role (innovation bias: {context.innovation_vs_conservative:.2f})"
        
        assignments['gemini'] = RoleAssignment(
            model=ModelProvider.GEMINI,
            role=gemini_role,
            context_factors={"brand_sensitivity": context.brand_sensitivity, "innovation": context.innovation_vs_conservative},
            assignment_reason=reason,
            confidence=0.7 + (context.brand_sensitivity * 0.3)
        )
        
        return assignments
    
    def get_role_prompt(self, role: RoleType, content: str, context: Dict[str, Any] = None) -> str:
        """
        Generar prompt especializado para un rol específico
        """
        base_context = f"Analyzing the following content from the perspective of {role.value.replace('_', ' ').title()}:\n\n{content}\n\n"
        
        role_prompts = {
            RoleType.CFO_CONSERVATIVE: base_context + """
As a Conservative CFO, focus on:
- Financial risk assessment and mitigation
- Cost-benefit analysis with conservative projections  
- Cash flow impact and working capital considerations
- ROI calculations using conservative metrics
- Compliance with financial regulations
- Sustainable growth over aggressive expansion
- Protection of existing revenue streams

Provide a detailed financial perspective emphasizing stability and risk management.
""",
            
            RoleType.CFO_GROWTH: base_context + """
As a Growth-Oriented CFO, focus on:
- Revenue expansion opportunities and scaling potential
- Investment requirements for aggressive growth
- Market penetration financial modeling
- Competitive advantage from financial perspective
- Capital allocation for maximum growth impact
- KPI tracking for growth initiatives
- Strategic financial partnerships and funding

Provide a growth-focused financial analysis emphasizing expansion and opportunity.
""",
            
            RoleType.CTO_PRAGMATIC: base_context + """
As a Pragmatic CTO, focus on:
- Technical feasibility with current resources
- Implementation timeline and realistic milestones
- System reliability and maintenance considerations
- Security implications and risk mitigation
- Integration with existing technology stack
- Team capacity and skill requirements
- Cost-effective technical solutions

Provide practical technical analysis emphasizing reliability and implementation.
""",
            
            RoleType.CTO_INNOVATIVE: base_context + """
As an Innovative CTO, focus on:
- Cutting-edge technology opportunities
- Scalability and future-proofing architecture
- Competitive technical advantages
- Innovation potential and differentiation
- Emerging technology integration possibilities
- Technical roadmap for disruption
- Investment in transformative capabilities

Provide visionary technical analysis emphasizing innovation and competitive advantage.
""",
            
            RoleType.CMO_BRAND: base_context + """
As a Brand-Focused CMO, focus on:
- Brand consistency and reputation protection
- Customer perception and messaging alignment
- Brand equity impact of proposed initiatives
- Stakeholder communication strategy
- Risk to brand image and mitigation
- Brand positioning and competitive differentiation
- Long-term brand value preservation

Provide brand-centric marketing analysis emphasizing reputation and consistency.
""",
            
            RoleType.CMO_GROWTH: base_context + """
As a Growth-Oriented CMO, focus on:
- Customer acquisition and market expansion
- Growth marketing strategies and channels
- Conversion optimization and funnel improvement
- Market penetration and customer lifetime value
- Competitive market share capture
- Viral and scalable marketing mechanisms
- Data-driven growth experiments

Provide growth-focused marketing analysis emphasizing acquisition and expansion.
""",
            
            RoleType.LEGAL_COMPLIANCE: base_context + """
As a Compliance-Focused Legal Advisor, focus on:
- Regulatory compliance requirements and implications
- Legal risk assessment and mitigation strategies
- Industry-specific regulations and standards
- Data protection and privacy considerations
- Contractual obligations and liabilities
- Audit trail and documentation requirements
- Risk tolerance and legal exposure

Provide comprehensive legal analysis emphasizing compliance and risk management.
""",
            
            RoleType.LEGAL_BUSINESS: base_context + """
As a Business-Oriented Legal Advisor, focus on:
- Legal frameworks that enable business objectives
- Strategic legal positioning and competitive advantage
- Commercial terms optimization
- Intellectual property considerations
- Partnership and collaboration legal structures
- Efficient legal processes that accelerate business
- Balanced risk-taking within legal boundaries

Provide business-enabling legal analysis emphasizing opportunity and strategic advantage.
""",
            
            RoleType.STRATEGY_EXECUTION: base_context + """
As an Execution-Focused Strategist, focus on:
- Implementation roadmap and tactical steps
- Resource allocation and operational requirements
- Timeline management and milestone tracking
- Risk mitigation during execution
- Team coordination and responsibility matrix
- Success metrics and performance indicators
- Continuous monitoring and course correction

Provide execution-oriented strategic analysis emphasizing implementation and delivery.
""",
            
            RoleType.STRATEGY_VISION: base_context + """
As a Visionary Strategist, focus on:
- Long-term strategic implications and opportunities
- Market positioning and competitive advantage
- Future market trends and disruption potential
- Strategic partnerships and ecosystem development
- Innovation opportunities and blue ocean strategies
- Transformation potential and paradigm shifts
- Visionary leadership and change management

Provide forward-looking strategic analysis emphasizing vision and transformation.
"""
        }
        
        return role_prompts.get(role, base_context + "Provide your specialized analysis.")
    
    def _load_role_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Cargar definiciones detalladas de roles"""
        return {
            "cfo_conservative": {
                "description": "Conservative CFO focused on financial stability and risk management",
                "key_competencies": ["financial_risk", "cost_analysis", "cash_flow", "compliance"],
                "decision_bias": "conservative",
                "primary_focus": "stability"
            },
            "cfo_growth": {
                "description": "Growth-oriented CFO focused on expansion and investment opportunities",
                "key_competencies": ["revenue_growth", "investment_analysis", "scaling", "market_expansion"],
                "decision_bias": "aggressive",
                "primary_focus": "growth"
            },
            "cto_pragmatic": {
                "description": "Pragmatic CTO focused on reliable implementation and system stability",
                "key_competencies": ["system_reliability", "implementation", "security", "maintenance"],
                "decision_bias": "practical",
                "primary_focus": "reliability"
            },
            "cto_innovative": {
                "description": "Innovative CTO focused on cutting-edge technology and competitive advantage",
                "key_competencies": ["innovation", "emerging_tech", "scalability", "disruption"],
                "decision_bias": "innovative",
                "primary_focus": "competitive_advantage"
            }
            # ... más definiciones de roles
        }
    
    def _load_context_keywords(self) -> Dict[str, List[str]]:
        """Cargar palabras clave para análisis contextual"""
        return {
            "financial": [
                "revenue", "cost", "profit", "roi", "budget", "investment", "funding",
                "cash flow", "margin", "expense", "financial", "money", "price"
            ],
            "technical": [
                "system", "architecture", "api", "development", "code", "integration",
                "database", "server", "platform", "technology", "software", "hardware"
            ],
            "legal": [
                "compliance", "regulation", "legal", "contract", "agreement", "terms",
                "liability", "risk", "audit", "policy", "gdpr", "privacy"
            ],
            "marketing": [
                "brand", "customer", "market", "campaign", "promotion", "advertising",
                "social media", "content", "engagement", "conversion", "funnel"
            ],
            "strategy": [
                "strategy", "vision", "mission", "goal", "objective", "planning",
                "roadmap", "competitive", "market position", "growth", "expansion"
            ],
            "risk": [
                "risk", "security", "threat", "vulnerability", "protection", "safety",
                "compliance", "audit", "control", "governance", "oversight"
            ],
            "innovation": [
                "innovation", "disrupt", "new", "novel", "cutting-edge", "breakthrough",
                "advanced", "revolutionary", "transform", "modernize", "upgrade"
            ],
            "conservative": [
                "proven", "stable", "reliable", "traditional", "established", "tested",
                "conservative", "safe", "predictable", "consistent", "standard"
            ]
        }
    
    def _get_default_assignments(self, domain: str) -> Dict[str, RoleAssignment]:
        """Asignaciones por defecto en caso de error"""
        default_assignments = {
            'gpt-4': RoleAssignment(
                model=ModelProvider.GPT4,
                role=RoleType.CFO_CONSERVATIVE,
                context_factors={},
                assignment_reason="Default CFO role",
                confidence=0.5
            ),
            'claude': RoleAssignment(
                model=ModelProvider.CLAUDE,
                role=RoleType.CTO_PRAGMATIC,
                context_factors={},
                assignment_reason="Default CTO role",
                confidence=0.5
            ),
            'gemini': RoleAssignment(
                model=ModelProvider.GEMINI,
                role=RoleType.CMO_BRAND,
                context_factors={},
                assignment_reason="Default CMO role",
                confidence=0.5
            )
        }
        
        logger.warning(f"Using default role assignments for domain: {domain}")
        return default_assignments
    
    def _log_assignment(
        self, 
        content: str, 
        analysis: ContextAnalysis, 
        assignments: Dict[str, RoleAssignment]
    ):
        """Log de asignación para análisis posterior"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "content_length": len(content),
            "context_analysis": {
                "complexity_score": analysis.complexity_score,
                "risk_level": analysis.risk_level,
                "innovation_vs_conservative": analysis.innovation_vs_conservative,
                "financial_impact": analysis.financial_impact,
                "technical_complexity": analysis.technical_complexity
            },
            "assignments": {
                model: {
                    "role": assignment.role.value,
                    "confidence": assignment.confidence,
                    "reason": assignment.assignment_reason
                }
                for model, assignment in assignments.items()
            }
        }
        
        self.assignment_history.append(log_entry)
        
        # Mantener solo los últimos 1000 registros
        if len(self.assignment_history) > 1000:
            self.assignment_history = self.assignment_history[-1000:]
    
    def get_assignment_analytics(self) -> Dict[str, Any]:
        """Obtener analytics de asignaciones realizadas"""
        if not self.assignment_history:
            return {"message": "No assignment history available"}
        
        # Análisis de patrones de asignación
        role_frequency = {}
        avg_confidence = {}
        
        for entry in self.assignment_history:
            for model, assignment in entry["assignments"].items():
                role = assignment["role"]
                confidence = assignment["confidence"]
                
                if role not in role_frequency:
                    role_frequency[role] = 0
                    avg_confidence[role] = []
                
                role_frequency[role] += 1
                avg_confidence[role].append(confidence)
        
        # Calcular confianza promedio por rol
        for role in avg_confidence:
            avg_confidence[role] = sum(avg_confidence[role]) / len(avg_confidence[role])
        
        return {
            "total_assignments": len(self.assignment_history),
            "role_frequency": role_frequency,
            "average_confidence_by_role": avg_confidence,
            "most_used_roles": sorted(role_frequency.items(), key=lambda x: x[1], reverse=True)[:5],
            "assignment_patterns": self._analyze_assignment_patterns()
        }
    
    def _analyze_assignment_patterns(self) -> Dict[str, Any]:
        """Analizar patrones en las asignaciones"""
        if len(self.assignment_history) < 10:
            return {"message": "Insufficient data for pattern analysis"}
        
        recent_assignments = self.assignment_history[-50:]  # Últimas 50 asignaciones
        
        # Tendencias de complejidad
        complexity_trend = [entry["context_analysis"]["complexity_score"] for entry in recent_assignments]
        avg_complexity = sum(complexity_trend) / len(complexity_trend)
        
        # Tendencias de innovación vs conservadurismo
        innovation_trend = [entry["context_analysis"]["innovation_vs_conservative"] for entry in recent_assignments]
        avg_innovation = sum(innovation_trend) / len(innovation_trend)
        
        return {
            "average_complexity": avg_complexity,
            "average_innovation_bias": avg_innovation,
            "complexity_trend": "increasing" if complexity_trend[-10:] > complexity_trend[:10] else "stable",
            "innovation_trend": "increasing" if innovation_trend[-10:] > innovation_trend[:10] else "stable"
        }