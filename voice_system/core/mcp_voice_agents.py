# mcp_voice_agents.py - Sin LangWatch
import asyncio
from typing import Dict, Optional, List
from voice_manager_cpu_optimized import CPUOptimizedVoiceManager
from voice_types import *

class MCPVoiceAgent:
    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type
        self.voice_manager = CPUOptimizedVoiceManager()
        print(f"✅ Voice agent initialized: {agent_type.value}")

    async def handle_customer_service_call(
        self,
        audio_input: bytes,
        user_id: str,
        language: Language = Language.SPANISH_MX
    ) -> AudioResponse:
        """Complete customer service call handling with premium OpenAI voice"""
        
        print(f"📞 Processing customer service call for {user_id}")
        
        # 1. Speech to Text
        transcript = await self.voice_manager.transcribe_audio(audio_input, language)
        
        if not transcript:
            # Handle empty transcript
            if language == Language.SPANISH_MX:
                response_text = "Disculpa, no pude escuchar bien tu mensaje. ¿Podrías repetirlo por favor?"
            else:
                response_text = "Sorry, I couldn't hear your message clearly. Could you please repeat it?"
        else:
            # 2. Get customer context
            customer_context = await self._get_customer_context(user_id)
            
            # 3. Process query
            response_text = await self._process_customer_query(
                transcript, customer_context, language
            )
        
        # 4. Generate voice response
        audio_response = await self.voice_manager.generate_speech(
            text=response_text,
            agent_type=AgentType.CUSTOMER_SERVICE,
            language=language
        )
        
        # 5. Save interaction
        await self._save_customer_interaction(user_id, transcript, response_text)
        
        print(f"✅ Customer service call completed: {audio_response.duration_ms}ms, cost: ${audio_response.cost:.4f}")
        return audio_response

    async def handle_sales_call(
        self,
        audio_input: bytes,
        prospect_id: str,
        language: Language = Language.SPANISH_MX
    ) -> AudioResponse:
        """Sales call with premium persuasive voice"""
        
        print(f"💼 Processing sales call for {prospect_id}")
        
        transcript = await self.voice_manager.transcribe_audio(audio_input, language)
        
        if not transcript:
            if language == Language.SPANISH_MX:
                response_text = "¡Hola! Me da mucho gusto poder hablar contigo. ¿En qué puedo ayudarte hoy?"
            else:
                response_text = "Hello! I'm excited to speak with you today. How can I help you?"
        else:
            sales_context = await self._get_sales_context(prospect_id)
            response_text = await self._process_sales_query(
                transcript, sales_context, language
            )
        
        audio_response = await self.voice_manager.generate_speech(
            text=response_text,
            agent_type=AgentType.SALES,
            language=language
        )
        
        await self._save_sales_interaction(prospect_id, transcript, response_text)
        
        print(f"✅ Sales call completed: {audio_response.duration_ms}ms, cost: ${audio_response.cost:.4f}")
        return audio_response

    async def handle_internal_rag_query(
        self,
        audio_input: bytes,
        employee_id: str,
        language: Language = Language.SPANISH_MX
    ) -> AudioResponse:
        """Internal RAG with standard voice"""
        
        print(f"🔍 Processing internal RAG query for {employee_id}")
        
        transcript = await self.voice_manager.transcribe_audio(audio_input, language)
        
        if not transcript:
            if language == Language.SPANISH_MX:
                response_text = "No pude procesar tu consulta. Intenta de nuevo."
            else:
                response_text = "I couldn't process your query. Please try again."
        else:
            rag_results = await self._search_internal_documents(transcript, language)
            response_text = await self._generate_rag_response(transcript, rag_results, language)
        
        audio_response = await self.voice_manager.generate_speech(
            text=response_text,
            agent_type=AgentType.RAG_ASSISTANT,
            language=language
        )
        
        print(f"✅ RAG query completed: {audio_response.duration_ms}ms, cost: ${audio_response.cost:.4f}")
        return audio_response

    # Integration methods
    async def _get_customer_context(self, user_id: str) -> Dict:
        return {
            "user_id": user_id, 
            "history": [], 
            "preferences": {"language": "spanish"},
            "tier": "premium"
        }

    async def _process_customer_query(self, transcript: str, context: Dict, language: Language) -> str:
        if language == Language.SPANISH_MX:
            return f"""Entiendo perfectamente tu consulta sobre '{transcript}'. 
            Como tu asistente personal, estoy aquí para brindarte el mejor servicio posible. 
            He revisado tu información y puedo ayudarte de inmediato. 
            ¿Hay algo específico en lo que te gustaría que me enfoque?"""
        else:
            return f"""I completely understand your inquiry about '{transcript}'. 
            As your personal assistant, I'm here to provide you with the best possible service. 
            I've reviewed your information and can help you right away. 
            Is there something specific you'd like me to focus on?"""

    async def _process_sales_query(self, transcript: str, context: Dict, language: Language) -> str:
        if language == Language.SPANISH_MX:
            return f"""¡Excelente pregunta sobre '{transcript}'! 
            Me emociona poder compartir contigo exactamente lo que necesitas. 
            Nuestro producto está diseñado específicamente para resolver este tipo de situaciones. 
            Déjame explicarte los 3 beneficios principales que vas a obtener inmediatamente..."""
        else:
            return f"""Excellent question about '{transcript}'! 
            I'm excited to share with you exactly what you need. 
            Our product is specifically designed to solve this type of situation. 
            Let me explain the 3 main benefits you'll get immediately..."""

    async def _generate_rag_response(self, query: str, results: List, language: Language) -> str:
        if not results:
            if language == Language.SPANISH_MX:
                return f"No encontré información específica sobre '{query}' en los documentos internos. ¿Podrías ser más específico?"
            else:
                return f"I didn't find specific information about '{query}' in the internal documents. Could you be more specific?"
        
        if language == Language.SPANISH_MX:
            return f"""Según los documentos internos más recientes sobre '{query}': 
            He encontrado {len(results)} documentos relevantes. 
            Los puntos clave son: Primero, los datos indican que... 
            Segundo, las mejores prácticas sugieren... 
            ¿Te gustaría que profundice en algún aspecto específico?"""
        else:
            return f"""According to the most recent internal documents about '{query}': 
            I found {len(results)} relevant documents. 
            The key points are: First, the data indicates that... 
            Second, best practices suggest... 
            Would you like me to dive deeper into any specific aspect?"""

    async def _search_internal_documents(self, query: str, language: Language) -> List:
        return [
            {"doc": "policy_handbook.pdf", "score": 0.92, "snippet": "Employee guidelines..."},
            {"doc": "technical_specs.md", "score": 0.87, "snippet": "System requirements..."},
            {"doc": "faq_internal.pdf", "score": 0.82, "snippet": "Common questions..."}
        ]

    async def _get_sales_context(self, prospect_id: str) -> Dict:
        return {
            "prospect_id": prospect_id, 
            "stage": "qualification",
            "pain_points": ["efficiency", "cost"],
            "budget": "enterprise",
            "timeline": "Q2"
        }

    async def _save_customer_interaction(self, user_id: str, transcript: str, response: str):
        print(f"💾 Saving customer interaction for {user_id}: '{transcript[:50]}...'")

    async def _save_sales_interaction(self, prospect_id: str, transcript: str, response: str):
        print(f"💾 Saving sales interaction for {prospect_id}: '{transcript[:50]}...'")
