"""
Content Templates para Chain-of-Debate SuperMCP

Sistema de plantillas especializadas para diferentes tipos de contenido empresarial,
con prompts optimizados, estructuras de respuesta, y criterios de calidad específicos
para cada dominio de negocio.

Dominios Soportados:
- Proposals: Business proposals, RFP responses, project proposals
- Content: Marketing content, blog posts, social media, copywriting  
- Contracts: Legal agreements, terms of service, compliance documents
- Strategy: Business strategy, market analysis, competitive intelligence
- Technical: System design, architecture, code review, technical specs
- Financial: Financial analysis, budgets, ROI calculations, forecasts

Características:
- Templates dinámicos basados en contexto
- Criterios de calidad específicos por dominio
- Structured output formats
- Industry best practices integradas
- Compliance-aware templates
- Multi-language support preparado

Beneficios Empresariales:
- Consistencia en deliverables
- Reduced time-to-market 
- Enhanced quality assurance
- Compliance automation
- Brand voice consistency
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import re

logger = logging.getLogger(__name__)

class ContentDomain(Enum):
    """Dominios de contenido soportados"""
    PROPOSAL = "proposal"
    CONTENT = "content"
    CONTRACT = "contract"
    STRATEGY = "strategy"
    TECHNICAL = "technical"
    FINANCIAL = "financial"
    MARKETING = "marketing"
    LEGAL = "legal"

class ContentComplexity(Enum):
    """Niveles de complejidad"""
    SIMPLE = "simple"
    INTERMEDIATE = "intermediate"
    COMPLEX = "complex"
    ENTERPRISE = "enterprise"

class OutputFormat(Enum):
    """Formatos de salida"""
    STRUCTURED_TEXT = "structured_text"
    MARKDOWN = "markdown"
    JSON = "json"
    EXECUTIVE_SUMMARY = "executive_summary"
    DETAILED_REPORT = "detailed_report"

@dataclass
class ContentRequirements:
    """Requerimientos específicos de contenido"""
    domain: ContentDomain
    complexity: ContentComplexity
    output_format: OutputFormat
    word_count_target: Optional[int] = None
    tone: str = "professional"
    audience: str = "business"
    compliance_requirements: List[str] = None
    brand_guidelines: Dict[str, Any] = None
    industry_context: str = None
    
    def __post_init__(self):
        if self.compliance_requirements is None:
            self.compliance_requirements = []
        if self.brand_guidelines is None:
            self.brand_guidelines = {}

@dataclass
class ContentTemplate:
    """Template de contenido estructurado"""
    template_id: str
    domain: ContentDomain
    name: str
    description: str
    system_prompt: str
    user_prompt_template: str
    output_structure: Dict[str, Any]
    quality_criteria: List[str]
    success_metrics: List[str]
    example_inputs: List[str]
    estimated_completion_time: int  # minutes
    complexity_level: ContentComplexity
    
class ContentTemplateEngine:
    """
    Motor de templates para generación de contenido especializado
    """
    
    def __init__(self):
        self.templates = {}
        self.template_usage_stats = {}
        self.quality_benchmarks = {}
        
        # Cargar templates por defecto
        self._load_default_templates()
        
        logger.info("📄 Content Template Engine initialized")
    
    def _load_default_templates(self):
        """Cargar templates por defecto para cada dominio"""
        
        # PROPOSAL TEMPLATES
        self.templates["business_proposal"] = ContentTemplate(
            template_id="business_proposal",
            domain=ContentDomain.PROPOSAL,
            name="Business Proposal Template",
            description="Comprehensive business proposal with executive summary, solution details, and pricing",
            system_prompt="""You are an expert business proposal writer with 15+ years of experience in B2B sales and business development. You create compelling, professional proposals that win deals and clearly communicate value propositions. Your proposals are structured, persuasive, and focus on solving client problems while demonstrating clear ROI.""",
            user_prompt_template="""
Create a comprehensive business proposal for the following request:

**CLIENT REQUEST:**
{input_content}

**ADDITIONAL CONTEXT:**
- Industry: {industry_context}
- Budget Range: {budget_range}
- Timeline: {timeline}
- Key Decision Makers: {decision_makers}

**PROPOSAL REQUIREMENTS:**
Your proposal must include:

1. **Executive Summary** (150-200 words)
   - Problem statement and proposed solution
   - Key benefits and value proposition
   - Investment summary and ROI highlights

2. **Understanding of Requirements** (300-400 words)
   - Detailed analysis of client needs
   - Current state assessment
   - Desired future state vision

3. **Proposed Solution** (400-500 words)
   - Technical approach and methodology
   - Implementation phases and timeline
   - Resource allocation and team structure
   - Technology stack and tools

4. **Value Proposition & Benefits** (300-400 words)
   - Quantifiable business benefits
   - ROI calculations and payback period
   - Risk mitigation and competitive advantages
   - Success metrics and KPIs

5. **Investment & Pricing** (200-300 words)
   - Detailed cost breakdown
   - Payment terms and milestones
   - Optional add-ons and future enhancements

6. **Implementation Timeline** (200-250 words)
   - Project phases with deliverables
   - Critical milestones and dependencies
   - Communication and reporting schedule

7. **Team & Credentials** (250-300 words)
   - Key team members and expertise
   - Relevant case studies and references
   - Company credentials and certifications

8. **Next Steps** (100-150 words)
   - Immediate action items
   - Decision timeline
   - Contact information

**TONE:** Professional, confident, client-focused
**FORMAT:** Clear sections with bullet points and structured layout
**GOAL:** Win the business by demonstrating clear value and expertise
""",
            output_structure={
                "executive_summary": "string",
                "requirements_understanding": "string", 
                "proposed_solution": "string",
                "value_proposition": "string",
                "investment_pricing": "string",
                "implementation_timeline": "string",
                "team_credentials": "string",
                "next_steps": "string",
                "appendices": "optional_string"
            },
            quality_criteria=[
                "Clear value proposition articulated",
                "Specific, quantifiable benefits mentioned",
                "Professional tone throughout",
                "All required sections included",
                "Logical flow and structure",
                "Client-specific customization evident",
                "Call-to-action present"
            ],
            success_metrics=[
                "Client engagement rate",
                "Proposal-to-contract conversion",
                "Time to close",
                "Deal size vs. projected"
            ],
            example_inputs=[
                "We need a digital transformation solution for our manufacturing company",
                "Looking for a marketing automation platform implementation",
                "Require cybersecurity assessment and implementation services"
            ],
            estimated_completion_time=15,
            complexity_level=ContentComplexity.COMPLEX
        )
        
        # CONTENT TEMPLATES
        self.templates["marketing_content"] = ContentTemplate(
            template_id="marketing_content",
            domain=ContentDomain.CONTENT,
            name="Marketing Content Template",
            description="Engaging marketing content including blog posts, social media, and promotional copy",
            system_prompt="""You are a world-class marketing copywriter and content strategist with expertise in creating compelling, conversion-focused content across all digital channels. You understand consumer psychology, brand voice, SEO best practices, and how to create content that drives engagement and action. Your content is always on-brand, audience-appropriate, and optimized for the intended platform.""",
            user_prompt_template="""
Create compelling marketing content for the following request:

**CONTENT REQUEST:**
{input_content}

**BRAND CONTEXT:**
- Brand Voice: {brand_voice}
- Target Audience: {target_audience}
- Content Type: {content_type}
- Platform/Channel: {platform}
- Campaign Objective: {campaign_objective}

**CONTENT REQUIREMENTS:**

1. **Primary Content Piece** (400-600 words)
   - Attention-grabbing headline/title
   - Engaging opening that hooks the reader
   - Clear value proposition and benefits
   - Compelling call-to-action
   - SEO-optimized (include relevant keywords naturally)

2. **Supporting Elements:**
   - **Social Media Snippets** (3-5 variations, platform-specific)
   - **Email Subject Lines** (5 options with different approaches)
   - **Meta Description** (150-160 characters, SEO-optimized)
   - **Key Hashtags** (relevant and trending)

3. **Content Strategy Notes** (200-300 words)
   - Target audience insights
   - Content positioning rationale
   - Distribution recommendations
   - Performance prediction and success metrics

**TONE:** {tone}
**BRAND VOICE:** Consistent with brand guidelines
**GOAL:** Drive {campaign_objective} while maintaining brand authenticity

**OPTIMIZATION REQUIREMENTS:**
- Mobile-first writing (short paragraphs, scannable)
- Include emotional triggers and urgency when appropriate
- Clear benefit statements over feature lists
- Social proof elements where relevant
- Strong, action-oriented CTAs
""",
            output_structure={
                "primary_content": "string",
                "headline_options": "array",
                "social_media_snippets": "array", 
                "email_subject_lines": "array",
                "meta_description": "string",
                "hashtags": "array",
                "strategy_notes": "string",
                "cta_variations": "array"
            },
            quality_criteria=[
                "Compelling, benefit-focused headline",
                "Clear value proposition",
                "Strong call-to-action",
                "Brand voice consistency",
                "Audience-appropriate tone",
                "SEO optimization evident",
                "Mobile-friendly formatting"
            ],
            success_metrics=[
                "Engagement rate",
                "Click-through rate", 
                "Conversion rate",
                "Social shares",
                "Time on page"
            ],
            example_inputs=[
                "Blog post about the benefits of cloud migration for small businesses",
                "Social media campaign for new product launch in healthcare",
                "Email newsletter content for B2B software company"
            ],
            estimated_completion_time=8,
            complexity_level=ContentComplexity.INTERMEDIATE
        )
        
        # CONTRACT TEMPLATES
        self.templates["legal_contract"] = ContentTemplate(
            template_id="legal_contract",
            domain=ContentDomain.CONTRACT,
            name="Legal Contract Template",
            description="Professional legal contracts and agreements with compliance considerations",
            system_prompt="""You are a seasoned business attorney and contract specialist with expertise in commercial law, compliance, and risk management. You create legally sound, comprehensive contracts that protect business interests while being fair and enforceable. Your contracts are clear, unambiguous, and include all necessary legal protections and compliance requirements.""",
            user_prompt_template="""
Draft a comprehensive legal contract/agreement for the following situation:

**CONTRACT REQUEST:**
{input_content}

**LEGAL CONTEXT:**
- Jurisdiction: {jurisdiction}
- Contract Type: {contract_type}
- Industry: {industry_context}
- Regulatory Requirements: {regulatory_requirements}
- Risk Level: {risk_level}

**CONTRACT REQUIREMENTS:**

1. **Contract Header & Parties** (200-300 words)
   - Full legal names and addresses of all parties
   - Contract title and effective date
   - Recitals and background context
   - Definition of key terms

2. **Scope of Work/Services** (400-500 words)
   - Detailed description of deliverables
   - Performance standards and specifications
   - Timeline and milestones
   - Acceptance criteria

3. **Financial Terms** (300-400 words)
   - Payment amounts and schedule
   - Expense reimbursement terms
   - Late payment penalties
   - Invoice and payment procedures

4. **Legal Protections** (500-600 words)
   - Intellectual property ownership
   - Confidentiality and non-disclosure
   - Limitation of liability
   - Indemnification clauses
   - Force majeure provisions

5. **Compliance & Regulatory** (300-400 words)
   - Industry-specific compliance requirements
   - Data protection and privacy (GDPR, CCPA)
   - Regulatory reporting obligations
   - Audit and inspection rights

6. **Term & Termination** (300-400 words)
   - Contract duration and renewal
   - Termination conditions and procedures
   - Survival of obligations post-termination
   - Return of materials and data

7. **Dispute Resolution** (200-300 words)
   - Governing law and jurisdiction
   - Dispute resolution procedures (mediation/arbitration)
   - Legal fees and costs
   - Notice requirements

8. **Miscellaneous Provisions** (200-300 words)
   - Amendment procedures
   - Assignment restrictions
   - Severability clause
   - Entire agreement clause
   - Signature requirements

**TONE:** Formal, precise, legally protective
**FORMAT:** Standard legal contract format with numbered sections
**GOAL:** Create enforceable contract that protects all parties

**LEGAL REQUIREMENTS:**
- Comply with {jurisdiction} law
- Include all standard legal protections
- Address industry-specific risks
- Ensure enforceability and clarity
""",
            output_structure={
                "contract_header": "string",
                "scope_of_work": "string",
                "financial_terms": "string", 
                "legal_protections": "string",
                "compliance_regulatory": "string",
                "term_termination": "string",
                "dispute_resolution": "string",
                "miscellaneous_provisions": "string",
                "signature_block": "string"
            },
            quality_criteria=[
                "All parties clearly identified",
                "Scope of work unambiguous",
                "Payment terms crystal clear",
                "Appropriate legal protections included",
                "Compliance requirements addressed",
                "Termination procedures defined",
                "Dispute resolution mechanism specified",
                "Professional legal language"
            ],
            success_metrics=[
                "Contract execution rate",
                "Dispute frequency",
                "Compliance audit results",
                "Amendment requests"
            ],
            example_inputs=[
                "Software development agreement for custom enterprise application",
                "Marketing services contract for digital agency engagement",
                "Data processing agreement for GDPR compliance"
            ],
            estimated_completion_time=20,
            complexity_level=ContentComplexity.ENTERPRISE
        )
        
        # STRATEGY TEMPLATES  
        self.templates["business_strategy"] = ContentTemplate(
            template_id="business_strategy",
            domain=ContentDomain.STRATEGY,
            name="Business Strategy Template",
            description="Comprehensive business strategy analysis and recommendations",
            system_prompt="""You are a senior strategy consultant from a top-tier consulting firm with expertise in business strategy, market analysis, and competitive intelligence. You create insightful, data-driven strategic recommendations that help companies achieve sustainable competitive advantage. Your analyses are thorough, actionable, and grounded in business fundamentals.""",
            user_prompt_template="""
Develop a comprehensive business strategy analysis and recommendations for:

**STRATEGIC CHALLENGE:**
{input_content}

**BUSINESS CONTEXT:**
- Industry: {industry_context}
- Company Size: {company_size}
- Market Position: {market_position}
- Geographic Scope: {geographic_scope}
- Time Horizon: {time_horizon}

**STRATEGY REQUIREMENTS:**

1. **Situation Analysis** (400-500 words)
   - Current market position assessment
   - Internal capabilities and resources
   - External market trends and dynamics
   - Key challenges and opportunities
   - SWOT analysis summary

2. **Market & Competitive Analysis** (500-600 words)
   - Market size, growth, and segmentation
   - Competitive landscape mapping
   - Competitor strengths and weaknesses
   - Market gaps and white space opportunities
   - Customer needs and buying behavior

3. **Strategic Options** (600-700 words)
   - 3-5 strategic alternatives considered
   - Pros and cons of each option
   - Resource requirements and capabilities needed
   - Risk assessment for each option
   - Timeline and complexity considerations

4. **Recommended Strategy** (500-600 words)
   - Primary strategic recommendation with rationale
   - Supporting strategic initiatives
   - Competitive positioning and differentiation
   - Value proposition and go-to-market approach
   - Success factors and key dependencies

5. **Implementation Roadmap** (400-500 words)
   - Phase-gate implementation plan
   - Resource allocation and investment requirements
   - Quick wins and long-term initiatives
   - Critical milestones and decision points
   - Risk mitigation strategies

6. **Financial Projections** (300-400 words)
   - Revenue and profit impact projections
   - Investment requirements and payback period
   - Scenario analysis (best/base/worst case)
   - Key financial metrics and KPIs

7. **Success Metrics & Monitoring** (200-300 words)
   - Leading and lagging indicators
   - Performance dashboard recommendations
   - Review and adjustment mechanisms
   - Governance and accountability structure

**TONE:** Analytical, confident, business-focused
**FORMAT:** Executive consulting report style
**GOAL:** Provide actionable strategic guidance for business growth
""",
            output_structure={
                "situation_analysis": "string",
                "market_competitive_analysis": "string",
                "strategic_options": "string",
                "recommended_strategy": "string", 
                "implementation_roadmap": "string",
                "financial_projections": "string",
                "success_metrics": "string",
                "executive_summary": "string"
            },
            quality_criteria=[
                "Thorough situation analysis",
                "Data-driven insights",
                "Multiple strategic options considered", 
                "Clear recommendation with rationale",
                "Actionable implementation plan",
                "Realistic financial projections",
                "Measurable success metrics"
            ],
            success_metrics=[
                "Strategy adoption rate",
                "Implementation progress",
                "Financial performance vs. projections",
                "Market share changes"
            ],
            example_inputs=[
                "Digital transformation strategy for traditional retailer",
                "Market expansion strategy for SaaS company",
                "Competitive response strategy to new market entrant"
            ],
            estimated_completion_time=25,
            complexity_level=ContentComplexity.ENTERPRISE
        )
        
        # TECHNICAL TEMPLATES
        self.templates["technical_specification"] = ContentTemplate(
            template_id="technical_specification",
            domain=ContentDomain.TECHNICAL,
            name="Technical Specification Template", 
            description="Detailed technical specifications and system design documents",
            system_prompt="""You are a senior technical architect and systems engineer with deep expertise in software development, system design, and technology architecture. You create comprehensive, technically accurate specifications that enable successful system development and implementation. Your specifications are detailed, unambiguous, and follow industry best practices.""",
            user_prompt_template="""
Create a comprehensive technical specification for the following system/component:

**TECHNICAL REQUEST:**
{input_content}

**TECHNICAL CONTEXT:**
- Technology Stack: {technology_stack}
- Scale Requirements: {scale_requirements}
- Performance Requirements: {performance_requirements}
- Security Requirements: {security_requirements}
- Integration Requirements: {integration_requirements}

**SPECIFICATION REQUIREMENTS:**

1. **System Overview** (300-400 words)
   - High-level system description and purpose
   - Key functional requirements
   - Non-functional requirements (performance, scalability, security)
   - System boundaries and scope
   - Key assumptions and constraints

2. **Architecture Design** (500-600 words)
   - System architecture diagram description
   - Component breakdown and responsibilities
   - Data flow and interaction patterns
   - Technology stack rationale
   - Scalability and performance considerations

3. **API Specifications** (400-500 words)
   - Endpoint definitions and descriptions
   - Request/response schemas and examples
   - Authentication and authorization mechanisms
   - Error handling and status codes
   - Rate limiting and throttling policies

4. **Database Design** (400-500 words)
   - Entity relationship model
   - Table schemas with constraints
   - Index strategies for performance
   - Data consistency and integrity requirements
   - Backup and recovery procedures

5. **Security Specifications** (400-500 words)
   - Authentication and authorization framework
   - Data encryption requirements (at rest and in transit)
   - Security controls and access policies
   - Vulnerability assessment and monitoring
   - Compliance requirements (SOC2, GDPR, etc.)

6. **Development Guidelines** (300-400 words)
   - Coding standards and conventions
   - Testing requirements (unit, integration, performance)
   - Code review and quality gates
   - Development workflow and CI/CD pipeline
   - Documentation standards

7. **Deployment & Operations** (300-400 words)
   - Infrastructure requirements and specifications
   - Deployment procedures and environments
   - Monitoring and alerting requirements
   - Backup and disaster recovery procedures
   - Performance tuning and optimization guidelines

8. **Testing Strategy** (300-400 words)
   - Test cases and scenarios
   - Performance benchmarks and load testing
   - Security testing requirements
   - User acceptance testing criteria
   - Test automation strategy

**TONE:** Technical, precise, comprehensive
**FORMAT:** Technical documentation standard with code examples
**GOAL:** Enable successful system development and implementation
""",
            output_structure={
                "system_overview": "string",
                "architecture_design": "string",
                "api_specifications": "string",
                "database_design": "string",
                "security_specifications": "string", 
                "development_guidelines": "string",
                "deployment_operations": "string",
                "testing_strategy": "string",
                "appendices": "optional_string"
            },
            quality_criteria=[
                "Clear system requirements defined",
                "Comprehensive architecture described",
                "API specifications are complete",
                "Security requirements addressed",
                "Testing strategy included",
                "Implementation guidelines provided",
                "Technical accuracy and feasibility"
            ],
            success_metrics=[
                "Development velocity",
                "Bug rate in production",
                "System performance vs. requirements",
                "Security audit results"
            ],
            example_inputs=[
                "Microservices architecture for e-commerce platform",
                "API gateway design for enterprise integration",
                "Real-time analytics system for IoT data processing"
            ],
            estimated_completion_time=30,
            complexity_level=ContentComplexity.COMPLEX
        )
        
        # FINANCIAL TEMPLATES
        self.templates["financial_analysis"] = ContentTemplate(
            template_id="financial_analysis",
            domain=ContentDomain.FINANCIAL,
            name="Financial Analysis Template",
            description="Comprehensive financial analysis and business case development",
            system_prompt="""You are a senior financial analyst and investment professional with expertise in financial modeling, valuation, and business case development. You create thorough, accurate financial analyses that support sound business decision-making. Your analyses are data-driven, conservative in assumptions, and clearly present financial risks and opportunities.""",
            user_prompt_template="""
Prepare a comprehensive financial analysis for the following business scenario:

**FINANCIAL ANALYSIS REQUEST:**
{input_content}

**FINANCIAL CONTEXT:**
- Company Size: {company_size}
- Industry: {industry_context}
- Analysis Period: {analysis_period}
- Currency: {currency}
- Risk Profile: {risk_profile}

**ANALYSIS REQUIREMENTS:**

1. **Executive Summary** (200-300 words)
   - Investment/project overview
   - Key financial highlights
   - Recommendation summary
   - Risk assessment overview

2. **Financial Model & Assumptions** (400-500 words)
   - Revenue projections and growth assumptions
   - Cost structure analysis and drivers
   - Capital expenditure requirements
   - Working capital considerations
   - Key modeling assumptions and rationale

3. **Investment Analysis** (400-500 words)
   - Total investment requirements
   - Funding sources and structure
   - Cash flow projections (5-year)
   - Break-even analysis
   - Sensitivity analysis on key variables

4. **Return Analysis** (300-400 words)
   - NPV calculation with discount rate rationale
   - IRR analysis and hurdle rate comparison
   - Payback period (simple and discounted)
   - Return on investment metrics
   - Value creation analysis

5. **Risk Assessment** (400-500 words)
   - Key risk factors identification
   - Scenario analysis (best/base/worst case)
   - Risk mitigation strategies
   - Contingency planning requirements
   - Probability-weighted outcomes

6. **Competitive & Market Analysis** (300-400 words)
   - Market size and growth projections
   - Competitive positioning impact
   - Market share assumptions
   - Pricing strategy and elasticity
   - Industry benchmark comparisons

7. **Implementation Timeline** (200-300 words)
   - Project phases and milestones
   - Cash flow timing
   - Resource allocation schedule
   - Critical success factors
   - Key decision points

8. **Recommendation & Next Steps** (200-300 words)
   - Investment recommendation with rationale
   - Implementation priorities
   - Monitoring and review requirements
   - Success metrics and KPIs

**TONE:** Analytical, objective, financially rigorous
**FORMAT:** Professional financial report with supporting calculations
**GOAL:** Enable informed financial decision-making
""",
            output_structure={
                "executive_summary": "string",
                "financial_model_assumptions": "string",
                "investment_analysis": "string",
                "return_analysis": "string",
                "risk_assessment": "string",
                "competitive_market_analysis": "string",
                "implementation_timeline": "string",
                "recommendation_next_steps": "string",
                "financial_appendices": "optional_string"
            },
            quality_criteria=[
                "Comprehensive financial model",
                "Realistic assumptions documented",
                "Multiple valuation methods used",
                "Thorough risk analysis",
                "Scenario modeling included",
                "Clear investment recommendation",
                "Professional financial formatting"
            ],
            success_metrics=[
                "Forecast accuracy",
                "Investment performance vs. projections",
                "Risk materialization rate",
                "Stakeholder decision adoption"
            ],
            example_inputs=[
                "ROI analysis for ERP system implementation",
                "Business case for market expansion investment",
                "Financial evaluation of merger and acquisition opportunity"
            ],
            estimated_completion_time=35,
            complexity_level=ContentComplexity.ENTERPRISE
        )
        
        logger.info(f"📚 Loaded {len(self.templates)} content templates")
    
    def get_template(self, domain: ContentDomain, complexity: ContentComplexity = None) -> Optional[ContentTemplate]:
        """Obtener template apropiado para dominio y complejidad"""
        
        # Mapeo de dominios a template IDs
        domain_mapping = {
            ContentDomain.PROPOSAL: "business_proposal",
            ContentDomain.CONTENT: "marketing_content",
            ContentDomain.CONTRACT: "legal_contract",
            ContentDomain.STRATEGY: "business_strategy",
            ContentDomain.TECHNICAL: "technical_specification",
            ContentDomain.FINANCIAL: "financial_analysis",
            ContentDomain.MARKETING: "marketing_content",
            ContentDomain.LEGAL: "legal_contract"
        }
        
        template_id = domain_mapping.get(domain)
        if template_id and template_id in self.templates:
            template = self.templates[template_id]
            
            # Verificar si complexity match es apropiado
            if complexity and template.complexity_level != complexity:
                logger.warning(f"Template complexity mismatch: requested {complexity}, available {template.complexity_level}")
            
            return template
        
        return None
    
    def generate_content_prompt(
        self,
        domain: ContentDomain,
        input_content: str,
        context: Dict[str, Any] = None,
        requirements: ContentRequirements = None
    ) -> Dict[str, str]:
        """Generar prompt especializado para el contenido"""
        
        template = self.get_template(domain, requirements.complexity if requirements else None)
        
        if not template:
            # Fallback a prompt genérico
            return self._generate_generic_prompt(domain, input_content, context)
        
        # Preparar contexto para el template
        template_context = self._prepare_template_context(context or {}, requirements)
        
        # Formatear user prompt
        try:
            formatted_user_prompt = template.user_prompt_template.format(
                input_content=input_content,
                **template_context
            )
        except KeyError as e:
            logger.warning(f"Template formatting error: {e}, using partial context")
            # Intentar con contexto parcial
            safe_context = {k: v for k, v in template_context.items() if f"{{{k}}}" in template.user_prompt_template}
            formatted_user_prompt = template.user_prompt_template.format(
                input_content=input_content,
                **safe_context
            )
        
        # Actualizar estadísticas de uso
        self._update_template_usage_stats(template.template_id)
        
        return {
            "system_prompt": template.system_prompt,
            "user_prompt": formatted_user_prompt,
            "template_id": template.template_id,
            "expected_structure": json.dumps(template.output_structure, indent=2),
            "quality_criteria": template.quality_criteria,
            "estimated_time": template.estimated_completion_time
        }
    
    def _prepare_template_context(
        self, 
        context: Dict[str, Any], 
        requirements: Optional[ContentRequirements]
    ) -> Dict[str, str]:
        """Preparar contexto para formateo de template"""
        
        # Valores por defecto
        default_context = {
            "industry_context": "general business",
            "budget_range": "to be discussed",
            "timeline": "standard timeline",
            "decision_makers": "key stakeholders",
            "brand_voice": "professional and trustworthy",
            "target_audience": "business professionals",
            "content_type": "standard content",
            "platform": "multiple channels",
            "campaign_objective": "engagement and conversion",
            "tone": "professional",
            "jurisdiction": "applicable jurisdiction",
            "contract_type": "standard agreement",
            "regulatory_requirements": "standard compliance",
            "risk_level": "moderate",
            "company_size": "medium enterprise",
            "market_position": "established player",
            "geographic_scope": "regional",
            "time_horizon": "3-5 years",
            "technology_stack": "modern technology stack",
            "scale_requirements": "enterprise scale",
            "performance_requirements": "high performance",
            "security_requirements": "enterprise security",
            "integration_requirements": "standard integrations",
            "analysis_period": "5 years",
            "currency": "USD",
            "risk_profile": "moderate risk"
        }
        
        # Combinar con contexto proporcionado
        template_context = {**default_context, **context}
        
        # Aplicar requirements si están disponibles
        if requirements:
            template_context.update({
                "tone": requirements.tone,
                "audience": requirements.audience,
                "industry_context": requirements.industry_context or template_context["industry_context"]
            })
            
            # Agregar compliance requirements
            if requirements.compliance_requirements:
                template_context["regulatory_requirements"] = ", ".join(requirements.compliance_requirements)
        
        return template_context
    
    def _generate_generic_prompt(
        self,
        domain: ContentDomain,
        input_content: str,
        context: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generar prompt genérico cuando no hay template específico"""
        
        domain_guidance = {
            ContentDomain.PROPOSAL: "Create a professional business proposal that clearly articulates value proposition, scope, timeline, and investment.",
            ContentDomain.CONTENT: "Create engaging, on-brand content that resonates with the target audience and drives desired actions.",
            ContentDomain.CONTRACT: "Draft a comprehensive legal agreement that protects all parties while being fair and enforceable.",
            ContentDomain.STRATEGY: "Develop strategic analysis and recommendations based on thorough market and competitive assessment.",
            ContentDomain.TECHNICAL: "Create detailed technical specifications that enable successful system development and implementation.",
            ContentDomain.FINANCIAL: "Prepare thorough financial analysis with realistic projections and comprehensive risk assessment.",
            ContentDomain.MARKETING: "Create compelling marketing content that drives engagement and conversion.",
            ContentDomain.LEGAL: "Draft legally sound documentation that ensures compliance and protects business interests."
        }
        
        system_prompt = f"""You are an expert {domain.value} specialist with extensive experience in creating high-quality, professional content. {domain_guidance.get(domain, 'Create professional, high-quality content that meets business standards.')}"""
        
        user_prompt = f"""
Please create comprehensive {domain.value} content for the following request:

{input_content}

Context: {json.dumps(context, indent=2)}

Ensure the content is:
- Professional and well-structured
- Appropriate for business use
- Complete and actionable
- Tailored to the specific requirements
"""
        
        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "template_id": f"generic_{domain.value}",
            "expected_structure": "unstructured",
            "quality_criteria": ["Professional tone", "Complete content", "Business appropriate"],
            "estimated_time": 10
        }
    
    def _update_template_usage_stats(self, template_id: str):
        """Actualizar estadísticas de uso de templates"""
        
        if template_id not in self.template_usage_stats:
            self.template_usage_stats[template_id] = {
                "usage_count": 0,
                "first_used": datetime.now(),
                "last_used": datetime.now(),
                "avg_quality_score": 0.0,
                "total_quality_scores": 0
            }
        
        stats = self.template_usage_stats[template_id]
        stats["usage_count"] += 1
        stats["last_used"] = datetime.now()
    
    def evaluate_content_quality(
        self,
        domain: ContentDomain,
        generated_content: str,
        template_id: str = None
    ) -> Dict[str, Any]:
        """Evaluar calidad del contenido generado"""
        
        template = self.templates.get(template_id) if template_id else self.get_template(domain)
        
        if not template:
            return self._generic_quality_evaluation(generated_content)
        
        quality_score = 0.0
        criteria_scores = {}
        
        # Evaluar cada criterio de calidad
        for criterion in template.quality_criteria:
            score = self._evaluate_quality_criterion(generated_content, criterion)
            criteria_scores[criterion] = score
            quality_score += score
        
        # Promedio de scores
        if template.quality_criteria:
            quality_score /= len(template.quality_criteria)
        
        # Evaluaciones adicionales
        length_score = self._evaluate_content_length(generated_content, template.domain)
        structure_score = self._evaluate_content_structure(generated_content, template.output_structure)
        
        final_score = (quality_score * 0.6 + length_score * 0.2 + structure_score * 0.2)
        
        # Actualizar estadísticas del template
        if template_id and template_id in self.template_usage_stats:
            stats = self.template_usage_stats[template_id]
            stats["total_quality_scores"] += final_score
            stats["avg_quality_score"] = stats["total_quality_scores"] / stats["usage_count"]
        
        return {
            "overall_score": final_score,
            "criteria_scores": criteria_scores,
            "length_score": length_score,
            "structure_score": structure_score,
            "quality_level": self._get_quality_level(final_score),
            "improvement_suggestions": self._generate_improvement_suggestions(criteria_scores, template)
        }
    
    def _evaluate_quality_criterion(self, content: str, criterion: str) -> float:
        """Evaluar un criterio específico de calidad"""
        
        # Mappings de criterios a patrones de evaluación
        criterion_evaluators = {
            "clear value proposition": lambda c: 0.8 if any(word in c.lower() for word in ["benefit", "value", "advantage", "roi"]) else 0.4,
            "professional tone": lambda c: 0.9 if not any(word in c.lower() for word in ["awesome", "cool", "super"]) else 0.3,
            "all required sections included": lambda c: min(1.0, len(c.split('\n\n')) / 5),
            "compelling headline": lambda c: 0.8 if len(c.split('\n')[0]) > 20 and ":" not in c.split('\n')[0] else 0.4,
            "strong call-to-action": lambda c: 0.8 if any(word in c.lower() for word in ["contact", "call", "visit", "download", "sign up"]) else 0.3,
            "technical accuracy": lambda c: 0.7,  # Placeholder - requeriría validación técnica real
            "comprehensive analysis": lambda c: 0.8 if len(c.split()) > 500 else 0.5
        }
        
        # Buscar evaluador que match el criterio
        for pattern, evaluator in criterion_evaluators.items():
            if pattern.lower() in criterion.lower():
                return evaluator(content)
        
        # Evaluación genérica basada en palabras clave del criterio
        criterion_words = criterion.lower().split()
        matches = sum(1 for word in criterion_words if word in content.lower())
        return min(1.0, matches / len(criterion_words))
    
    def _evaluate_content_length(self, content: str, domain: ContentDomain) -> float:
        """Evaluar apropiada longitud del contenido"""
        
        word_count = len(content.split())
        
        # Targets de longitud por dominio
        length_targets = {
            ContentDomain.PROPOSAL: (1500, 3000),
            ContentDomain.CONTENT: (500, 1200),
            ContentDomain.CONTRACT: (1000, 2500),
            ContentDomain.STRATEGY: (1200, 2500),
            ContentDomain.TECHNICAL: (1500, 3500),
            ContentDomain.FINANCIAL: (1200, 2800)
        }
        
        min_words, max_words = length_targets.get(domain, (500, 1500))
        
        if min_words <= word_count <= max_words:
            return 1.0
        elif word_count < min_words:
            return max(0.3, word_count / min_words)
        else:
            return max(0.5, max_words / word_count)
    
    def _evaluate_content_structure(self, content: str, expected_structure: Dict[str, Any]) -> float:
        """Evaluar estructura del contenido"""
        
        if expected_structure == "unstructured":
            return 0.8  # Score neutral para contenido no estructurado
        
        # Contar secciones y headers
        lines = content.split('\n')
        headers = [line for line in lines if line.strip().startswith('#') or line.strip().endswith(':')]
        
        expected_sections = len(expected_structure)
        found_sections = len(headers)
        
        # Score basado en cantidad de secciones encontradas vs esperadas
        if expected_sections > 0:
            section_score = min(1.0, found_sections / expected_sections)
        else:
            section_score = 0.8
        
        # Bonus por estructura clara (párrafos, bullets, etc.)
        paragraph_count = len([line for line in lines if line.strip() and not line.startswith(' ')])
        bullet_count = len([line for line in lines if line.strip().startswith(('-', '*', '•'))])
        
        structure_bonus = min(0.2, (paragraph_count + bullet_count) / 50)
        
        return min(1.0, section_score + structure_bonus)
    
    def _generic_quality_evaluation(self, content: str) -> Dict[str, Any]:
        """Evaluación genérica de calidad"""
        
        word_count = len(content.split())
        line_count = len(content.split('\n'))
        
        # Scores básicos
        length_score = 0.8 if 200 <= word_count <= 2000 else 0.5
        structure_score = 0.8 if line_count > 5 else 0.5
        
        return {
            "overall_score": (length_score + structure_score) / 2,
            "criteria_scores": {"length": length_score, "structure": structure_score},
            "quality_level": "acceptable",
            "improvement_suggestions": ["Consider adding more detailed sections", "Improve content structure"]
        }
    
    def _get_quality_level(self, score: float) -> str:
        """Convertir score numérico a nivel de calidad"""
        
        if score >= 0.9:
            return "excellent"
        elif score >= 0.8:
            return "good"
        elif score >= 0.7:
            return "acceptable"
        elif score >= 0.6:
            return "needs_improvement"
        else:
            return "poor"
    
    def _generate_improvement_suggestions(
        self,
        criteria_scores: Dict[str, float],
        template: ContentTemplate
    ) -> List[str]:
        """Generar sugerencias de mejora basadas en scores de criterios"""
        
        suggestions = []
        
        for criterion, score in criteria_scores.items():
            if score < 0.7:
                if "value proposition" in criterion:
                    suggestions.append("Strengthen the value proposition with more specific benefits and ROI")
                elif "professional tone" in criterion:
                    suggestions.append("Use more formal, business-appropriate language")
                elif "sections" in criterion:
                    suggestions.append("Ensure all required sections are included and properly structured")
                elif "call-to-action" in criterion:
                    suggestions.append("Add stronger, more specific calls-to-action")
                elif "technical" in criterion:
                    suggestions.append("Verify technical accuracy and add more technical detail")
                else:
                    suggestions.append(f"Improve: {criterion}")
        
        # Sugerencias generales basadas en el dominio
        domain_suggestions = {
            ContentDomain.PROPOSAL: "Consider adding more quantified benefits and competitive differentiators",
            ContentDomain.CONTENT: "Enhance engagement with storytelling and emotional appeals",
            ContentDomain.CONTRACT: "Ensure all legal protections and compliance requirements are addressed",
            ContentDomain.STRATEGY: "Add more data-driven insights and scenario analysis",
            ContentDomain.TECHNICAL: "Include more implementation details and technical specifications",
            ContentDomain.FINANCIAL: "Provide more comprehensive risk analysis and scenario modeling"
        }
        
        if template.domain in domain_suggestions:
            suggestions.append(domain_suggestions[template.domain])
        
        return suggestions[:5]  # Limitar a top 5 sugerencias
    
    def get_template_analytics(self) -> Dict[str, Any]:
        """Obtener analytics de uso de templates"""
        
        return {
            "total_templates": len(self.templates),
            "template_usage_stats": self.template_usage_stats,
            "most_used_templates": sorted(
                self.template_usage_stats.items(),
                key=lambda x: x[1]["usage_count"],
                reverse=True
            )[:5],
            "highest_quality_templates": sorted(
                self.template_usage_stats.items(),
                key=lambda x: x[1]["avg_quality_score"],
                reverse=True
            )[:5] if self.template_usage_stats else [],
            "domain_distribution": {
                domain.value: len([t for t in self.templates.values() if t.domain == domain])
                for domain in ContentDomain
            }
        }
    
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """Obtener lista de templates disponibles"""
        
        return [
            {
                "template_id": template.template_id,
                "name": template.name,
                "domain": template.domain.value,
                "description": template.description,
                "complexity": template.complexity_level.value,
                "estimated_time": template.estimated_completion_time,
                "usage_count": self.template_usage_stats.get(template.template_id, {}).get("usage_count", 0),
                "avg_quality": self.template_usage_stats.get(template.template_id, {}).get("avg_quality_score", 0.0)
            }
            for template in self.templates.values()
        ]