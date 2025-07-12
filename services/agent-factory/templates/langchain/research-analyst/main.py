"""
{{ agent_name }} - LangChain Research Analyst Agent
Generated from UltraMCP Agent Factory with LangChain framework
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import structlog

# LangChain imports
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import Tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.llms import Ollama

logger = structlog.get_logger(__name__)

app = FastAPI(
    title="{{ agent_name }}",
    description="LangChain Research Analyst Agent with UltraMCP integration",
    version="1.0.0"
)

# Configuration
ULTRAMCP_COD_URL = "{{ ultramcp_cod_url }}"
ULTRAMCP_LOCAL_MODELS_URL = "{{ ultramcp_local_models_url }}"
AGENT_ID = "{{ agent_id }}"


class ResearchRequest(BaseModel):
    topic: str
    depth: str = "standard"  # basic, standard, deep
    sources: Optional[List[str]] = None
    format: str = "report"  # report, summary, bullets
    use_cod: bool = False


class ResearchResponse(BaseModel):
    report: str
    sources: List[str]
    confidence: float
    research_id: str
    agent_id: str
    cod_analysis: Optional[Dict[str, Any]] = None


# Initialize LangChain components
def create_research_tools():
    """Create LangChain tools for research"""
    
    async def web_search_tool(query: str) -> str:
        """Search the web for information"""
        try:
            # Use UltraMCP local models for web search analysis
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{ULTRAMCP_LOCAL_MODELS_URL}/generate",
                    json={
                        "prompt": f"Provide comprehensive research information about: {query}",
                        "task_type": "research",
                        "max_tokens": 500
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("content", "No information found")
        except Exception as e:
            logger.error("Web search failed", error=str(e))
        
        return f"Unable to search for: {query}"
    
    async def document_analysis_tool(content: str) -> str:
        """Analyze document content"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{ULTRAMCP_LOCAL_MODELS_URL}/generate",
                    json={
                        "prompt": f"Analyze this document content and extract key insights: {content[:1000]}",
                        "task_type": "reasoning",
                        "max_tokens": 400
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("content", "Unable to analyze document")
        except Exception as e:
            logger.error("Document analysis failed", error=str(e))
        
        return "Document analysis unavailable"
    
    async def data_synthesis_tool(data_points: str) -> str:
        """Synthesize multiple data points"""
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    f"{ULTRAMCP_LOCAL_MODELS_URL}/generate",
                    json={
                        "prompt": f"Synthesize these research findings into coherent insights: {data_points}",
                        "task_type": "reasoning",
                        "max_tokens": 600
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("content", "Unable to synthesize data")
        except Exception as e:
            logger.error("Data synthesis failed", error=str(e))
        
        return "Data synthesis unavailable"
    
    return [
        Tool(
            name="web_search",
            description="Search for information on the web about a specific topic",
            func=web_search_tool
        ),
        Tool(
            name="document_analysis", 
            description="Analyze document content and extract key insights",
            func=document_analysis_tool
        ),
        Tool(
            name="data_synthesis",
            description="Synthesize multiple data points into coherent insights",
            func=data_synthesis_tool
        )
    ]


# Initialize LangChain agent
def create_research_agent():
    """Create LangChain research agent"""
    try:
        # Use local Ollama model
        llm = Ollama(
            model="qwen2.5:14b",
            base_url="http://{{ ultramcp_local_models_url.replace('http://', '').split(':')[0] }}:11434"
        )
        
        tools = create_research_tools()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a professional research analyst. Your job is to:
            1. Gather comprehensive information on the given topic
            2. Analyze and synthesize the information 
            3. Provide well-structured, evidence-based reports
            4. Cite sources and verify information accuracy
            
            Use the available tools to research thoroughly. Always provide citations and confidence levels."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        agent = create_openai_tools_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        
        return agent_executor
    
    except Exception as e:
        logger.error("Failed to create LangChain agent", error=str(e))
        return None


# Global agent instance
research_agent = create_research_agent()


@app.get("/")
async def root():
    return {
        "agent": "{{ agent_name }}",
        "type": "research_analyst",
        "framework": "langchain",
        "capabilities": {{ capabilities }},
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check with LangChain and UltraMCP services"""
    try:
        # Check UltraMCP services
        async with httpx.AsyncClient(timeout=5.0) as client:
            models_healthy = False
            try:
                response = await client.get(f"{ULTRAMCP_LOCAL_MODELS_URL}/models")
                models_healthy = response.status_code == 200
            except:
                pass
            
            cod_healthy = False
            try:
                response = await client.get(f"{ULTRAMCP_COD_URL}/health")
                cod_healthy = response.status_code == 200
            except:
                pass
        
        # Check LangChain agent
        agent_healthy = research_agent is not None
        
        return {
            "status": "healthy",
            "agent_id": AGENT_ID,
            "timestamp": datetime.now(),
            "framework": "langchain",
            "ultramcp_services": {
                "local_models": "healthy" if models_healthy else "unhealthy",
                "cod_service": "healthy" if cod_healthy else "unhealthy"
            },
            "langchain_agent": "healthy" if agent_healthy else "unhealthy"
        }
    
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {"status": "unhealthy", "error": str(e)}


@app.post("/research", response_model=ResearchResponse)
async def conduct_research(request: ResearchRequest):
    """Conduct research using LangChain agent"""
    try:
        research_id = str(uuid.uuid4())
        
        if not research_agent:
            raise HTTPException(status_code=503, detail="Research agent not available")
        
        # Prepare research query
        query = f"""Conduct {request.depth} research on: {request.topic}
        
        Requirements:
        - Provide comprehensive analysis
        - Include sources and citations  
        - Format as {request.format}
        - Confidence level assessment
        """
        
        # Add source constraints if provided
        if request.sources:
            query += f"\nFocus on these sources: {', '.join(request.sources)}"
        
        # Execute research using LangChain agent
        logger.info("Starting research", topic=request.topic, depth=request.depth)
        
        result = await asyncio.to_thread(
            research_agent.invoke,
            {"input": query, "chat_history": []}
        )
        
        report = result.get("output", "Research completed but no output generated")
        
        # Extract sources (simplified extraction)
        sources = extract_sources_from_report(report)
        
        # Calculate confidence based on report quality
        confidence = calculate_research_confidence(report, sources)
        
        # Optional: Use Chain-of-Debate for complex topics
        cod_analysis = None
        if request.use_cod:
            cod_analysis = await conduct_cod_analysis(request.topic, report)
        
        logger.info(
            "Research completed",
            research_id=research_id,
            topic=request.topic,
            confidence=confidence,
            sources_count=len(sources)
        )
        
        return ResearchResponse(
            report=report,
            sources=sources,
            confidence=confidence,
            research_id=research_id,
            agent_id=AGENT_ID,
            cod_analysis=cod_analysis
        )
    
    except Exception as e:
        logger.error("Research failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")


@app.post("/cod-research")
async def enhanced_cod_research(request: ResearchRequest):
    """Use Chain-of-Debate for enhanced research analysis"""
    try:
        # First conduct standard research
        standard_research = await conduct_research(request)
        
        # Then use CoD for multi-perspective analysis
        cod_analysis = await conduct_cod_analysis(
            request.topic, 
            standard_research.report
        )
        
        return {
            "standard_research": standard_research,
            "cod_analysis": cod_analysis,
            "enhanced_insights": extract_cod_insights(cod_analysis)
        }
    
    except Exception as e:
        logger.error("CoD research failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"CoD research failed: {str(e)}")


# Helper functions

async def conduct_cod_analysis(topic: str, initial_report: str) -> Optional[Dict[str, Any]]:
    """Use UltraMCP Chain-of-Debate for research analysis"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            cod_request = {
                "task_id": f"research_analysis_{uuid.uuid4()}",
                "topic": f"Research analysis on: {topic}",
                "participants": ["research_advocate", "research_skeptic", "research_moderator"],
                "context": {
                    "initial_report": initial_report,
                    "research_topic": topic
                }
            }
            
            response = await client.post(
                f"{ULTRAMCP_COD_URL}/debate",
                json=cod_request
            )
            
            if response.status_code == 200:
                return response.json()
    
    except Exception as e:
        logger.error("CoD analysis failed", error=str(e))
    
    return None


def extract_sources_from_report(report: str) -> List[str]:
    """Extract sources from research report"""
    # Simple source extraction (would be more sophisticated in production)
    sources = []
    
    # Look for common source indicators
    import re
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, report)
    sources.extend(urls)
    
    # Look for citation patterns
    citation_patterns = [
        r'\[(\d+)\]',  # [1], [2], etc.
        r'\(([^)]+\d{4}[^)]*)\)',  # (Author 2023)
    ]
    
    for pattern in citation_patterns:
        citations = re.findall(pattern, report)
        sources.extend(citations)
    
    return list(set(sources))  # Remove duplicates


def calculate_research_confidence(report: str, sources: List[str]) -> float:
    """Calculate confidence score for research"""
    confidence = 0.5  # Base confidence
    
    # Higher confidence for longer reports
    if len(report) > 500:
        confidence += 0.2
    
    # Higher confidence for more sources
    source_bonus = min(0.3, len(sources) * 0.05)
    confidence += source_bonus
    
    # Higher confidence for structured content
    if any(keyword in report.lower() for keyword in ["conclusion", "analysis", "findings"]):
        confidence += 0.1
    
    return max(0.0, min(1.0, confidence))


def extract_cod_insights(cod_analysis: Optional[Dict[str, Any]]) -> List[str]:
    """Extract key insights from CoD analysis"""
    if not cod_analysis:
        return []
    
    insights = []
    
    # Extract consensus points
    consensus = cod_analysis.get("consensus", "")
    if consensus:
        insights.append(f"Consensus: {consensus}")
    
    # Extract key arguments
    arguments = cod_analysis.get("arguments", [])
    for arg in arguments[:3]:  # Top 3 arguments
        if isinstance(arg, dict) and "content" in arg:
            insights.append(f"Key point: {arg['content'][:100]}...")
    
    return insights


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port={{ deployment.port }})