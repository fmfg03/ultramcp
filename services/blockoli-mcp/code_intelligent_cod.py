#!/usr/bin/env python3
"""
Code-Intelligent Chain of Debate Protocol
Enhanced CoD with Blockoli semantic code understanding
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, asdict
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blockoli_client import BlockoliCodeContext, BlockoliAPIError
from cod_protocol.enhanced_orchestrator import EnhancedCoDOrchestrator, ParticipantConfig, DebateMode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodeIntelligenceMode(Enum):
    """Code intelligence modes for debates"""
    BASIC = "basic"
    DEEP_ANALYSIS = "deep_analysis"
    ARCHITECTURE_FOCUSED = "architecture_focused"
    SECURITY_FOCUSED = "security_focused"
    PATTERN_ANALYSIS = "pattern_analysis"
    REFACTORING_FOCUSED = "refactoring_focused"

@dataclass
class CodeIntelligentTask:
    """Enhanced task with code intelligence context"""
    task_id: str
    topic: str
    project_name: str
    code_query: Optional[str] = None
    intelligence_mode: CodeIntelligenceMode = CodeIntelligenceMode.BASIC
    context_depth: str = "medium"
    code_context: Optional[Dict] = None
    patterns_focus: Optional[List[str]] = None
    security_focus: bool = False
    architecture_focus: bool = False

class CodeIntelligentCoDOrchestrator(EnhancedCoDOrchestrator):
    """Enhanced CoD Orchestrator with Blockoli code intelligence"""
    
    def __init__(self, config: Dict = None, blockoli_endpoint: str = "http://localhost:8080"):
        super().__init__(config)
        self.blockoli_endpoint = blockoli_endpoint
        self.blockoli_client = None
        
    async def initialize_code_intelligence(self):
        """Initialize Blockoli client"""
        try:
            self.blockoli_client = BlockoliCodeContext(self.blockoli_endpoint)
            await self.blockoli_client.__aenter__()
            
            # Health check
            health = await self.blockoli_client.health_check()
            if not health.get('healthy', False):
                logger.warning("Blockoli service may not be fully healthy")
                
        except Exception as e:
            logger.error(f"Failed to initialize Blockoli client: {e}")
            raise
    
    async def cleanup_code_intelligence(self):
        """Cleanup Blockoli client"""
        if self.blockoli_client:
            await self.blockoli_client.__aexit__(None, None, None)
    
    async def run_code_intelligent_debate(
        self, 
        task: Union[CodeIntelligentTask, Dict],
        participants: List[ParticipantConfig] = None
    ) -> Dict:
        """Run CoD session with full code intelligence context"""
        
        # Convert dict to CodeIntelligentTask if needed
        if isinstance(task, dict):
            task = CodeIntelligentTask(**task)
        
        # Initialize code intelligence
        await self.initialize_code_intelligence()
        
        try:
            # 1. Gather code context
            code_context = await self.gather_code_context(task)
            task.code_context = code_context
            
            # 2. Enhance task with code intelligence
            enhanced_task_content = await self.create_code_intelligent_task_content(task)
            
            # 3. Select appropriate participants based on intelligence mode
            if not participants:
                participants = self.get_code_intelligent_participants(task.intelligence_mode)
            
            # 4. Run enhanced debate
            debate_result = await self.run_enhanced_debate_with_context(
                enhanced_task_content, 
                participants,
                task
            )
            
            # 5. Post-process results with code intelligence insights
            final_result = await self.post_process_code_intelligent_results(
                debate_result, 
                task
            )
            
            return final_result
            
        finally:
            await self.cleanup_code_intelligence()
    
    async def gather_code_context(self, task: CodeIntelligentTask) -> Dict:
        """Gather comprehensive code context using Blockoli"""
        
        try:
            # Determine code query
            code_query = task.code_query or self.extract_code_query_from_topic(task.topic)
            
            # Get code context based on intelligence mode
            if task.intelligence_mode == CodeIntelligenceMode.DEEP_ANALYSIS:
                context = await self.blockoli_client.get_code_context(
                    code_query, 
                    task.project_name,
                    context_depth="deep",
                    limit=20
                )
            elif task.intelligence_mode == CodeIntelligenceMode.ARCHITECTURE_FOCUSED:
                context = await self.gather_architecture_context(code_query, task.project_name)
            elif task.intelligence_mode == CodeIntelligenceMode.SECURITY_FOCUSED:
                context = await self.gather_security_context(code_query, task.project_name)
            elif task.intelligence_mode == CodeIntelligenceMode.PATTERN_ANALYSIS:
                context = await self.gather_pattern_context(code_query, task.project_name, task.patterns_focus)
            else:
                context = await self.blockoli_client.get_code_context(
                    code_query, 
                    task.project_name,
                    limit=15
                )
            
            return context
            
        except BlockoliAPIError as e:
            logger.error(f"Failed to gather code context: {e}")
            return {'error': str(e), 'context_available': False}
        except Exception as e:
            logger.error(f"Unexpected error gathering code context: {e}")
            return {'error': f'Unexpected error: {e}', 'context_available': False}
    
    async def gather_architecture_context(self, query: str, project_name: str) -> Dict:
        """Gather architecture-focused code context"""
        
        # Search for architectural patterns
        architecture_queries = [
            f"{query} architecture",
            f"{query} design pattern",
            f"class {query}",
            f"interface {query}",
            f"{query} service",
            f"{query} controller",
            f"{query} adapter"
        ]
        
        all_contexts = []
        for arch_query in architecture_queries:
            try:
                context = await self.blockoli_client.get_code_context(
                    arch_query, 
                    project_name,
                    limit=10
                )
                if context.get('similar_code_blocks'):
                    all_contexts.extend(context['similar_code_blocks'])
            except Exception as e:
                logger.warning(f"Failed to get architecture context for '{arch_query}': {e}")
        
        # Analyze architectural patterns
        architecture_analysis = await self.blockoli_client.extract_architecture_insights(
            all_contexts, 
            []
        )
        
        return {
            'query': query,
            'project': project_name,
            'context_type': 'architecture_focused',
            'similar_code_blocks': all_contexts,
            'architecture_analysis': architecture_analysis,
            'total_matches': len(all_contexts)
        }
    
    async def gather_security_context(self, query: str, project_name: str) -> Dict:
        """Gather security-focused code context"""
        
        # Security-focused queries
        security_queries = [
            f"{query} security",
            f"{query} authentication",
            f"{query} authorization", 
            f"{query} validation",
            f"{query} encrypt",
            f"{query} hash",
            f"{query} token",
            f"{query} password"
        ]
        
        security_contexts = []
        for sec_query in security_queries:
            try:
                context = await self.blockoli_client.get_code_context(
                    sec_query,
                    project_name,
                    limit=8
                )
                if context.get('similar_code_blocks'):
                    security_contexts.extend(context['similar_code_blocks'])
            except Exception as e:
                logger.warning(f"Failed to get security context for '{sec_query}': {e}")
        
        return {
            'query': query,
            'project': project_name,
            'context_type': 'security_focused',
            'similar_code_blocks': security_contexts,
            'security_patterns': await self.analyze_security_patterns(security_contexts),
            'total_matches': len(security_contexts)
        }
    
    async def gather_pattern_context(self, query: str, project_name: str, patterns_focus: List[str] = None) -> Dict:
        """Gather pattern-focused code context"""
        
        if not patterns_focus:
            patterns_focus = ['async', 'class', 'function', 'import', 'error_handling']
        
        pattern_contexts = {}
        for pattern in patterns_focus:
            try:
                pattern_query = f"{query} {pattern}"
                context = await self.blockoli_client.get_code_context(
                    pattern_query,
                    project_name,
                    limit=10
                )
                if context.get('similar_code_blocks'):
                    pattern_contexts[pattern] = context['similar_code_blocks']
            except Exception as e:
                logger.warning(f"Failed to get pattern context for '{pattern}': {e}")
        
        all_blocks = []
        for blocks in pattern_contexts.values():
            all_blocks.extend(blocks)
        
        return {
            'query': query,
            'project': project_name,
            'context_type': 'pattern_focused',
            'patterns_analyzed': list(pattern_contexts.keys()),
            'pattern_contexts': pattern_contexts,
            'similar_code_blocks': all_blocks,
            'total_matches': len(all_blocks)
        }
    
    async def create_code_intelligent_task_content(self, task: CodeIntelligentTask) -> Dict:
        """Create enhanced task content with code intelligence"""
        
        code_context = task.code_context or {}
        
        # Format code context for AI consumption
        context_summary = self.format_code_context_for_ai(code_context)
        
        # Create enhanced task content
        enhanced_content = f"""
Code-Intelligent Analysis Request

Topic: {task.topic}
Project: {task.project_name}
Intelligence Mode: {task.intelligence_mode.value}
Context Depth: {task.context_depth}

=== CODE CONTEXT ANALYSIS ===
{context_summary}

=== SPECIFIC FOCUS AREAS ===
"""
        
        # Add mode-specific focus areas
        if task.intelligence_mode == CodeIntelligenceMode.ARCHITECTURE_FOCUSED:
            enhanced_content += """
Architecture Analysis Required:
- Analyze current architectural patterns in the codebase
- Identify coupling and cohesion issues
- Suggest architectural improvements
- Consider scalability and maintainability implications
"""
        elif task.intelligence_mode == CodeIntelligenceMode.SECURITY_FOCUSED:
            enhanced_content += """
Security Analysis Required:
- Identify potential security vulnerabilities in the code
- Analyze authentication and authorization patterns
- Review input validation and sanitization
- Assess encryption and data protection measures
"""
        elif task.intelligence_mode == CodeIntelligenceMode.PATTERN_ANALYSIS:
            enhanced_content += """
Pattern Analysis Required:
- Identify recurring code patterns and anti-patterns
- Analyze consistency across the codebase
- Suggest pattern improvements and standardization
- Evaluate pattern implementation quality
"""
        elif task.intelligence_mode == CodeIntelligenceMode.REFACTORING_FOCUSED:
            enhanced_content += """
Refactoring Analysis Required:
- Identify code smells and technical debt
- Suggest refactoring opportunities
- Analyze impact of proposed changes
- Provide step-by-step refactoring plan
"""
        
        enhanced_content += f"""

=== DEBATE INSTRUCTIONS ===
Please provide analysis considering the actual codebase context above.
Base your recommendations on the specific code patterns, architecture, and 
implementation details found in the project.

Each participant should:
1. Reference specific code examples from the context
2. Consider the current implementation patterns
3. Propose concrete, actionable improvements
4. Assess the impact on existing code
"""
        
        return {
            'task_id': task.task_id,
            'content': enhanced_content,
            'code_context': code_context,
            'intelligence_mode': task.intelligence_mode.value,
            'project_name': task.project_name,
            'timestamp': datetime.now().isoformat()
        }
    
    def format_code_context_for_ai(self, code_context: Dict) -> str:
        """Format code context for AI consumption"""
        
        if not code_context or code_context.get('error'):
            return "❌ Code context unavailable - proceeding with general analysis"
        
        formatted = ""
        
        # Similar code blocks
        similar_blocks = code_context.get('similar_code_blocks', [])
        if similar_blocks:
            formatted += f"📋 Found {len(similar_blocks)} relevant code blocks:\n"
            for i, block in enumerate(similar_blocks[:5]):  # Limit to top 5
                file_path = block.get('file_path', 'unknown')
                language = block.get('language', 'unknown')
                formatted += f"  {i+1}. {file_path} ({language})\n"
            
            if len(similar_blocks) > 5:
                formatted += f"  ... and {len(similar_blocks) - 5} more blocks\n"
        
        # Code patterns
        patterns = code_context.get('code_patterns', {})
        if patterns.get('patterns_by_language'):
            formatted += f"\n🔍 Code Patterns Identified:\n"
            for lang_pattern in patterns['patterns_by_language']:
                language = lang_pattern.get('language', 'unknown')
                common_patterns = lang_pattern.get('common_patterns', [])
                if common_patterns:
                    formatted += f"  {language}: {', '.join(common_patterns)}\n"
        
        # Architecture insights
        arch_insights = code_context.get('architecture_insights', {})
        if arch_insights.get('architectural_insights'):
            formatted += f"\n🏗️ Architecture Insights:\n"
            for insight in arch_insights['architectural_insights']:
                pattern = insight.get('pattern', 'Unknown')
                description = insight.get('description', 'No description')
                confidence = insight.get('confidence', 0)
                formatted += f"  • {pattern}: {description} (confidence: {confidence:.1f})\n"
        
        # File analysis
        total_files = arch_insights.get('files_analyzed', 0)
        if total_files > 0:
            coupling = arch_insights.get('coupling_analysis', {}).get('estimated_coupling', 'unknown')
            formatted += f"\n📊 Codebase Analysis:\n"
            formatted += f"  • Files analyzed: {total_files}\n"
            formatted += f"  • Estimated coupling: {coupling}\n"
        
        return formatted
    
    def get_code_intelligent_participants(self, intelligence_mode: CodeIntelligenceMode) -> List[ParticipantConfig]:
        """Get appropriate participants based on intelligence mode"""
        
        base_participants = [
            ParticipantConfig(
                name="Code_Architect",
                role="Senior Software Architect",
                model="local:qwen2.5:14b",
                expertise=["architecture", "design_patterns", "code_quality"],
                perspective="Focus on architectural decisions and long-term maintainability"
            ),
            ParticipantConfig(
                name="Senior_Developer", 
                role="Senior Developer",
                model="local:deepseek-coder:6.7b",
                expertise=["implementation", "best_practices", "performance"],
                perspective="Focus on practical implementation and code quality"
            )
        ]
        
        # Add mode-specific participants
        if intelligence_mode == CodeIntelligenceMode.SECURITY_FOCUSED:
            base_participants.append(ParticipantConfig(
                name="Security_Expert",
                role="Security Engineer",
                model="local:llama3.1:8b",
                expertise=["security", "vulnerabilities", "compliance"],
                perspective="Focus on security implications and threat modeling"
            ))
        
        elif intelligence_mode == CodeIntelligenceMode.ARCHITECTURE_FOCUSED:
            base_participants.append(ParticipantConfig(
                name="Systems_Designer",
                role="Systems Design Engineer", 
                model="local:qwen2.5:14b",
                expertise=["system_design", "scalability", "distributed_systems"],
                perspective="Focus on system architecture and scalability"
            ))
        
        elif intelligence_mode == CodeIntelligenceMode.PATTERN_ANALYSIS:
            base_participants.append(ParticipantConfig(
                name="Code_Reviewer",
                role="Code Quality Specialist",
                model="local:deepseek-coder:6.7b", 
                expertise=["code_review", "patterns", "refactoring"],
                perspective="Focus on code patterns and quality improvements"
            ))
        
        # Add DeepClaude for meta-cognitive analysis
        base_participants.append(ParticipantConfig(
            name="Meta_Analyst",
            role="Meta-Cognitive Analyst",
            model="deepclaude",
            expertise=["meta_analysis", "reasoning", "synthesis"],
            perspective="Provide meta-cognitive analysis and synthesis of technical discussions"
        ))
        
        return base_participants
    
    async def run_enhanced_debate_with_context(
        self, 
        enhanced_task: Dict, 
        participants: List[ParticipantConfig],
        original_task: CodeIntelligentTask
    ) -> Dict:
        """Run the enhanced debate with code context"""
        
        # Use the parent class method but with enhanced task
        result = await super().run_cod_session(
            enhanced_task,
            mode=DebateMode.CODE_INTELLIGENT,
            participants=participants
        )
        
        # Add code intelligence metadata
        result['code_intelligence_metadata'] = {
            'intelligence_mode': original_task.intelligence_mode.value,
            'project_name': original_task.project_name,
            'code_context_available': original_task.code_context is not None,
            'context_blocks_analyzed': len(original_task.code_context.get('similar_code_blocks', [])) if original_task.code_context else 0,
            'patterns_identified': len(original_task.code_context.get('code_patterns', {}).get('patterns_by_language', [])) if original_task.code_context else 0
        }
        
        return result
    
    async def post_process_code_intelligent_results(
        self, 
        debate_result: Dict, 
        task: CodeIntelligentTask
    ) -> Dict:
        """Post-process debate results with code intelligence insights"""
        
        # Extract actionable insights from the debate
        insights = self.extract_actionable_insights(debate_result, task)
        
        # Generate implementation recommendations
        recommendations = self.generate_implementation_recommendations(debate_result, task)
        
        # Create final enhanced result
        enhanced_result = {
            **debate_result,
            'code_intelligence_analysis': {
                'task_summary': {
                    'topic': task.topic,
                    'project': task.project_name,
                    'intelligence_mode': task.intelligence_mode.value,
                    'context_depth': task.context_depth
                },
                'code_context_summary': self.summarize_code_context(task.code_context),
                'actionable_insights': insights,
                'implementation_recommendations': recommendations,
                'next_steps': self.generate_next_steps(insights, recommendations)
            }
        }
        
        return enhanced_result
    
    def extract_actionable_insights(self, debate_result: Dict, task: CodeIntelligentTask) -> List[Dict]:
        """Extract actionable insights from debate results"""
        
        insights = []
        
        # Analyze debate content for actionable items
        for round_result in debate_result.get('debate_rounds', []):
            for participant_response in round_result.get('responses', []):
                content = participant_response.get('content', '')
                
                # Simple keyword-based extraction (can be enhanced with NLP)
                if any(keyword in content.lower() for keyword in ['should', 'recommend', 'suggest', 'implement']):
                    insights.append({
                        'participant': participant_response.get('participant'),
                        'insight': content[:200] + '...' if len(content) > 200 else content,
                        'confidence': participant_response.get('confidence', 0.5),
                        'category': self.categorize_insight(content, task.intelligence_mode)
                    })
        
        return insights
    
    def generate_implementation_recommendations(self, debate_result: Dict, task: CodeIntelligentTask) -> List[Dict]:
        """Generate concrete implementation recommendations"""
        
        recommendations = []
        
        # Based on intelligence mode, generate specific recommendations
        if task.intelligence_mode == CodeIntelligenceMode.REFACTORING_FOCUSED:
            recommendations.append({
                'type': 'refactoring',
                'priority': 'high',
                'description': 'Create refactoring plan based on identified code smells',
                'implementation_steps': [
                    'Identify code smells in the analyzed files',
                    'Prioritize refactoring tasks by impact and complexity',
                    'Create unit tests for code to be refactored',
                    'Implement refactoring in small, incremental steps',
                    'Validate changes with comprehensive testing'
                ]
            })
        
        elif task.intelligence_mode == CodeIntelligenceMode.ARCHITECTURE_FOCUSED:
            recommendations.append({
                'type': 'architecture',
                'priority': 'medium',
                'description': 'Improve architectural structure based on analysis',
                'implementation_steps': [
                    'Document current architecture patterns',
                    'Identify coupling and cohesion issues',
                    'Design improved architecture with better separation of concerns',
                    'Plan migration strategy for architectural changes',
                    'Implement changes incrementally with proper testing'
                ]
            })
        
        elif task.intelligence_mode == CodeIntelligenceMode.SECURITY_FOCUSED:
            recommendations.append({
                'type': 'security',
                'priority': 'high',
                'description': 'Address security vulnerabilities and improve security posture',
                'implementation_steps': [
                    'Audit identified security-sensitive code sections',
                    'Implement additional input validation and sanitization',
                    'Review and strengthen authentication/authorization mechanisms',
                    'Add security testing to CI/CD pipeline',
                    'Conduct security code review with security team'
                ]
            })
        
        return recommendations
    
    def categorize_insight(self, content: str, intelligence_mode: CodeIntelligenceMode) -> str:
        """Categorize insight based on content and intelligence mode"""
        
        content_lower = content.lower()
        
        if intelligence_mode == CodeIntelligenceMode.SECURITY_FOCUSED:
            if any(keyword in content_lower for keyword in ['vulnerability', 'security', 'authentication']):
                return 'security'
            elif any(keyword in content_lower for keyword in ['validate', 'sanitize', 'input']):
                return 'validation'
        
        elif intelligence_mode == CodeIntelligenceMode.ARCHITECTURE_FOCUSED:
            if any(keyword in content_lower for keyword in ['pattern', 'design', 'architecture']):
                return 'architecture'
            elif any(keyword in content_lower for keyword in ['coupling', 'cohesion', 'dependency']):
                return 'coupling'
        
        elif intelligence_mode == CodeIntelligenceMode.REFACTORING_FOCUSED:
            if any(keyword in content_lower for keyword in ['refactor', 'improve', 'clean']):
                return 'refactoring'
            elif any(keyword in content_lower for keyword in ['test', 'testing', 'coverage']):
                return 'testing'
        
        return 'general'
    
    def summarize_code_context(self, code_context: Dict) -> Dict:
        """Summarize code context for final report"""
        
        if not code_context:
            return {'available': False}
        
        return {
            'available': True,
            'blocks_analyzed': len(code_context.get('similar_code_blocks', [])),
            'patterns_found': len(code_context.get('code_patterns', {}).get('patterns_by_language', [])),
            'architecture_insights': len(code_context.get('architecture_insights', {}).get('architectural_insights', [])),
            'files_involved': code_context.get('architecture_insights', {}).get('files_analyzed', 0)
        }
    
    def generate_next_steps(self, insights: List[Dict], recommendations: List[Dict]) -> List[str]:
        """Generate next steps based on insights and recommendations"""
        
        next_steps = []
        
        # Prioritize high-priority recommendations
        high_priority_recs = [r for r in recommendations if r.get('priority') == 'high']
        
        if high_priority_recs:
            next_steps.append(f"Address {len(high_priority_recs)} high-priority recommendations")
        
        # Add specific next steps based on insights
        if len(insights) > 0:
            next_steps.append("Review and validate participant insights")
            next_steps.append("Create implementation plan for suggested changes")
        
        # Add general next steps
        next_steps.extend([
            "Update project documentation with findings",
            "Schedule follow-up review after implementation",
            "Consider running additional code intelligence analysis"
        ])
        
        return next_steps
    
    def extract_code_query_from_topic(self, topic: str) -> str:
        """Extract code-relevant query from topic"""
        
        # Simple extraction - can be enhanced with NLP
        topic_lower = topic.lower()
        
        # Common code-related terms
        code_terms = [
            'authentication', 'auth', 'login', 'user', 'database', 'api', 
            'service', 'controller', 'model', 'class', 'function', 'method',
            'payment', 'security', 'encryption', 'validation', 'error', 'exception'
        ]
        
        for term in code_terms:
            if term in topic_lower:
                return term
        
        # Fallback: use first few words
        words = topic.split()[:3]
        return ' '.join(words)
    
    async def analyze_security_patterns(self, security_contexts: List[Dict]) -> Dict:
        """Analyze security patterns in code contexts"""
        
        security_patterns = {
            'authentication_patterns': [],
            'validation_patterns': [],
            'encryption_patterns': [],
            'authorization_patterns': []
        }
        
        for context in security_contexts:
            content = context.get('content', '').lower()
            
            if any(term in content for term in ['login', 'authenticate', 'signin']):
                security_patterns['authentication_patterns'].append(context)
            
            if any(term in content for term in ['validate', 'sanitize', 'filter']):
                security_patterns['validation_patterns'].append(context)
            
            if any(term in content for term in ['encrypt', 'decrypt', 'hash', 'crypto']):
                security_patterns['encryption_patterns'].append(context)
            
            if any(term in content for term in ['authorize', 'permission', 'role', 'access']):
                security_patterns['authorization_patterns'].append(context)
        
        return security_patterns


# Utility functions for easy integration

async def run_code_intelligent_debate(
    topic: str,
    project_name: str,
    intelligence_mode: str = "basic",
    code_query: str = None,
    blockoli_endpoint: str = "http://localhost:8080"
) -> Dict:
    """Quick utility function to run code-intelligent debate"""
    
    orchestrator = CodeIntelligentCoDOrchestrator(blockoli_endpoint=blockoli_endpoint)
    
    task = CodeIntelligentTask(
        task_id=f"code_debate_{int(datetime.now().timestamp())}",
        topic=topic,
        project_name=project_name,
        code_query=code_query,
        intelligence_mode=CodeIntelligenceMode(intelligence_mode)
    )
    
    return await orchestrator.run_code_intelligent_debate(task)

async def quick_architecture_analysis(
    topic: str,
    project_name: str,
    blockoli_endpoint: str = "http://localhost:8080"
) -> Dict:
    """Quick architecture analysis using code intelligence"""
    
    return await run_code_intelligent_debate(
        topic=topic,
        project_name=project_name,
        intelligence_mode="architecture_focused",
        blockoli_endpoint=blockoli_endpoint
    )

async def quick_security_analysis(
    topic: str,
    project_name: str,
    blockoli_endpoint: str = "http://localhost:8080"
) -> Dict:
    """Quick security analysis using code intelligence"""
    
    return await run_code_intelligent_debate(
        topic=topic,
        project_name=project_name,
        intelligence_mode="security_focused",
        blockoli_endpoint=blockoli_endpoint
    )


if __name__ == "__main__":
    # CLI interface
    import argparse
    
    async def main():
        parser = argparse.ArgumentParser(description='Code-Intelligent Chain of Debate')
        parser.add_argument('--topic', required=True, help='Debate topic')
        parser.add_argument('--project', required=True, help='Project name')
        parser.add_argument('--mode', default='basic', help='Intelligence mode')
        parser.add_argument('--query', help='Specific code query')
        parser.add_argument('--endpoint', default='http://localhost:8080', help='Blockoli endpoint')
        parser.add_argument('--output', help='Output file for results')
        
        args = parser.parse_args()
        
        try:
            result = await run_code_intelligent_debate(
                topic=args.topic,
                project_name=args.project,
                intelligence_mode=args.mode,
                code_query=args.query,
                blockoli_endpoint=args.endpoint
            )
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(result, f, indent=2)
                print(f"Results saved to {args.output}")
            else:
                print(json.dumps(result, indent=2))
                
        except Exception as e:
            logger.error(f"Code-intelligent debate failed: {e}")
            print(f"Error: {e}")
    
    asyncio.run(main())