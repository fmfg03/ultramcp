"""
demo-support - UltraMCP Customer Support Agent
Generated from UltraMCP Agent Factory with local models integration
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import structlog

logger = structlog.get_logger(__name__)

app = FastAPI(
    title="demo-support",
    description="UltraMCP Customer Support Agent with local models",
    version="1.0.0"
)

# Configuration
ULTRAMCP_COD_URL = "http://ultramcp-cod-service:8001"
ULTRAMCP_LOCAL_MODELS_URL = "http://ultramcp-local-models-orchestrator:8012"
AGENT_ID = "c3b31be4-b6c9-4922-8448-5e1bd7c48d40"


class Priority(Enum):
    LOW = "low"
    NORMAL = "normal" 
    HIGH = "high"
    URGENT = "urgent"


class TicketStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class CustomerQuery(BaseModel):
    message: str
    customer_id: Optional[str] = None
    priority: Priority = Priority.NORMAL
    category: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class SupportResponse(BaseModel):
    response: str
    agent_id: str
    confidence: float
    escalation_needed: bool
    suggested_actions: List[str]
    ticket_id: Optional[str] = None
    sentiment: Optional[str] = None


class SupportTicket(BaseModel):
    ticket_id: str
    customer_id: str
    message: str
    priority: Priority
    status: TicketStatus
    created_at: datetime
    agent_response: Optional[str] = None


# In-memory storage (would be database in production)
tickets_db = {}
conversation_history = {}


@app.get("/")
async def root():
    return {
        "agent": "demo-support",
        "type": "customer_support",
        "framework": "ultramcp",
        "capabilities": ['query_knowledge_base', 'escalate_to_human', 'create_ticket', 'cod_consultation', 'sentiment_analysis', 'solution_recommendation'],
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check with UltraMCP services connectivity"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Check local models
            models_healthy = False
            try:
                response = await client.get(f"{ULTRAMCP_LOCAL_MODELS_URL}/models")
                models_healthy = response.status_code == 200
            except:
                pass
            
            # Check CoD service if needed
            cod_healthy = False
            try:
                response = await client.get(f"{ULTRAMCP_COD_URL}/health")
                cod_healthy = response.status_code == 200
            except:
                pass
        
        return {
            "status": "healthy",
            "agent_id": AGENT_ID,
            "timestamp": datetime.now(),
            "ultramcp_services": {
                "local_models": "healthy" if models_healthy else "unhealthy",
                "cod_service": "healthy" if cod_healthy else "unhealthy"
            },
            "active_conversations": len(conversation_history),
            "open_tickets": len([t for t in tickets_db.values() if t.status == TicketStatus.OPEN])
        }
    
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {"status": "unhealthy", "error": str(e)}


@app.post("/chat", response_model=SupportResponse)
async def handle_customer_query(query: CustomerQuery):
    """Handle customer support query with UltraMCP local models"""
    try:
        conversation_id = query.customer_id or str(uuid.uuid4())
        
        # Analyze sentiment first
        sentiment = await analyze_sentiment(query.message)
        
        # Check if escalation is needed based on keywords
        escalation_keywords = ["manager", "supervisor", "escalate", "lawsuit", "cancel", "angry"]
        escalation_needed = any(keyword in query.message.lower() for keyword in escalation_keywords)
        escalation_needed = escalation_needed or query.priority in [Priority.HIGH, Priority.URGENT]
        
        # Generate response using local models
        response_text = await generate_support_response(query, sentiment, conversation_id)
        
        # Extract suggested actions
        suggested_actions = await extract_suggested_actions(query.message, response_text)
        
        # Create ticket if needed
        ticket_id = None
        if escalation_needed or query.priority in [Priority.HIGH, Priority.URGENT]:
            ticket_id = await create_support_ticket(query, response_text)
        
        # Store conversation history
        if conversation_id not in conversation_history:
            conversation_history[conversation_id] = []
        
        conversation_history[conversation_id].append({
            "timestamp": datetime.now(),
            "customer_message": query.message,
            "agent_response": response_text,
            "sentiment": sentiment,
            "escalation_needed": escalation_needed
        })
        
        # Calculate confidence based on response quality
        confidence = await calculate_response_confidence(query.message, response_text)
        
        logger.info(
            "Customer query processed",
            customer_id=query.customer_id,
            sentiment=sentiment,
            escalation_needed=escalation_needed,
            confidence=confidence
        )
        
        return SupportResponse(
            response=response_text,
            agent_id=AGENT_ID,
            confidence=confidence,
            escalation_needed=escalation_needed,
            suggested_actions=suggested_actions,
            ticket_id=ticket_id,
            sentiment=sentiment
        )
    
    except Exception as e:
        logger.error("Error processing customer query", error=str(e))
        
        # Fallback response
        return SupportResponse(
            response="I apologize, but I'm experiencing technical difficulties. Let me connect you with a human agent right away.",
            agent_id=AGENT_ID,
            confidence=0.0,
            escalation_needed=True,
            suggested_actions=["escalate_to_human"],
            sentiment="neutral"
        )


@app.get("/tickets")
async def list_tickets():
    """List all support tickets"""
    return {
        "tickets": [ticket.__dict__ for ticket in tickets_db.values()],
        "total": len(tickets_db),
        "by_status": {
            status.value: len([t for t in tickets_db.values() if t.status == status])
            for status in TicketStatus
        }
    }


@app.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str):
    """Get specific support ticket"""
    if ticket_id not in tickets_db:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return tickets_db[ticket_id].__dict__


@app.post("/consultation")
async def cod_consultation(query: CustomerQuery):
    """Use Chain-of-Debate for complex customer issues"""
    try:
        # Use CoD for complex decision making
        async with httpx.AsyncClient(timeout=30.0) as client:
            cod_request = {
                "task_id": f"customer_consultation_{uuid.uuid4()}",
                "topic": f"Customer support decision for: {query.message[:100]}",
                "participants": ["support_agent_pro", "support_agent_con", "moderator"],
                "context": {
                    "customer_query": query.message,
                    "priority": query.priority.value,
                    "customer_id": query.customer_id
                }
            }
            
            response = await client.post(
                f"{ULTRAMCP_COD_URL}/debate",
                json=cod_request
            )
            
            if response.status_code == 200:
                debate_result = response.json()
                return {
                    "consultation_result": debate_result,
                    "recommendation": debate_result.get("consensus", "Unable to reach consensus"),
                    "agent_id": AGENT_ID
                }
            else:
                return {"error": "CoD consultation unavailable", "fallback": True}
    
    except Exception as e:
        logger.error("CoD consultation failed", error=str(e))
        return {"error": str(e), "fallback": True}


# Helper functions

async def analyze_sentiment(message: str) -> str:
    """Analyze customer sentiment using local models"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{ULTRAMCP_LOCAL_MODELS_URL}/generate",
                json={
                    "prompt": f"Analyze the sentiment of this customer message (positive/negative/neutral): {message}",
                    "task_type": "sentiment_analysis",
                    "max_tokens": 50
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("content", "neutral").lower()
                
                if "positive" in content:
                    return "positive"
                elif "negative" in content:
                    return "negative"
                else:
                    return "neutral"
    except:
        pass
    
    return "neutral"


async def generate_support_response(query: CustomerQuery, sentiment: str, conversation_id: str) -> str:
    """Generate customer support response using local models"""
    try:
        # Build context from conversation history
        context = ""
        if conversation_id in conversation_history:
            recent_history = conversation_history[conversation_id][-3:]  # Last 3 exchanges
            context = "Previous conversation context:\n"
            for entry in recent_history:
                context += f"Customer: {entry['customer_message'][:100]}\n"
                context += f"Agent: {entry['agent_response'][:100]}\n"
        
        support_prompt = f"""You are a professional customer support agent. 

Customer sentiment: {sentiment}
Priority: {query.priority.value}
{context}

Customer message: {query.message}

Provide a helpful, empathetic, and professional response. Be concise but thorough. If you cannot resolve the issue, offer to escalate or create a ticket.

Response:"""
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{ULTRAMCP_LOCAL_MODELS_URL}/generate",
                json={
                    "prompt": support_prompt,
                    "task_type": "customer_support",
                    "max_tokens": 300
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("content", "I apologize, but I need to connect you with a human agent.")
    
    except Exception as e:
        logger.error("Response generation failed", error=str(e))
    
    return "Thank you for contacting us. I'm experiencing some technical difficulties, but I'd be happy to help you. Could you please rephrase your question?"


async def extract_suggested_actions(customer_message: str, agent_response: str) -> List[str]:
    """Extract suggested actions from the conversation"""
    actions = []
    
    # Rule-based action extraction
    if any(word in customer_message.lower() for word in ["refund", "return", "money back"]):
        actions.append("process_refund")
    
    if any(word in customer_message.lower() for word in ["technical", "not working", "error", "bug"]):
        actions.append("technical_support")
    
    if any(word in customer_message.lower() for word in ["billing", "charge", "payment", "invoice"]):
        actions.append("billing_inquiry")
    
    if any(word in agent_response.lower() for word in ["escalate", "manager", "supervisor"]):
        actions.append("escalate_to_human")
    
    if any(word in agent_response.lower() for word in ["ticket", "case", "follow up"]):
        actions.append("create_ticket")
    
    return actions if actions else ["general_inquiry"]


async def create_support_ticket(query: CustomerQuery, response: str) -> str:
    """Create a support ticket"""
    ticket_id = f"TICKET_{uuid.uuid4().hex[:8].upper()}"
    
    ticket = SupportTicket(
        ticket_id=ticket_id,
        customer_id=query.customer_id or "anonymous",
        message=query.message,
        priority=query.priority,
        status=TicketStatus.OPEN,
        created_at=datetime.now(),
        agent_response=response
    )
    
    tickets_db[ticket_id] = ticket
    
    logger.info("Support ticket created", ticket_id=ticket_id, priority=query.priority.value)
    
    return ticket_id


async def calculate_response_confidence(customer_message: str, agent_response: str) -> float:
    """Calculate confidence score for the response"""
    try:
        # Simple heuristic-based confidence calculation
        confidence = 0.5  # Base confidence
        
        # Higher confidence for longer, more detailed responses
        if len(agent_response) > 100:
            confidence += 0.2
        
        # Higher confidence if response addresses specific keywords from customer
        customer_words = set(customer_message.lower().split())
        response_words = set(agent_response.lower().split())
        overlap = len(customer_words.intersection(response_words))
        
        if overlap > 3:
            confidence += 0.2
        
        # Lower confidence for generic responses
        generic_phrases = ["thank you", "i apologize", "technical difficulties"]
        if any(phrase in agent_response.lower() for phrase in generic_phrases):
            confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))
    
    except:
        return 0.5


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8015)