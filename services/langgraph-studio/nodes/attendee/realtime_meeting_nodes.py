"""
Real-time Meeting Analysis Nodes for LangGraph
Processes attendee transcriptions in real-time with context awareness
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MeetingState:
    """State object for meeting analysis workflow"""
    session_id: str
    mode: str  # 'ears-only' or 'ears-and-mouth'
    transcript_chunk: Dict[str, Any]
    meeting_context: Dict[str, Any]
    detected_actions: List[Dict[str, Any]]
    classifications: List[Dict[str, Any]]
    pending_interventions: List[Dict[str, Any]]
    context_analysis: Dict[str, Any]
    should_intervene: bool
    intervention_message: Optional[str]
    mcp_payloads: List[Dict[str, Any]]
    execution_results: List[Dict[str, Any]]
    error: Optional[str]

def create_meeting_state(session_id: str, mode: str = 'ears-only') -> MeetingState:
    """Create initial meeting state"""
    return MeetingState(
        session_id=session_id,
        mode=mode,
        transcript_chunk={},
        meeting_context={},
        detected_actions=[],
        classifications=[],
        pending_interventions=[],
        context_analysis={},
        should_intervene=False,
        intervention_message=None,
        mcp_payloads=[],
        execution_results=[],
        error=None
    )

async def realtime_transcription_ingestion(state: MeetingState) -> MeetingState:
    """
    Node: Ingest and validate real-time transcription chunks
    """
    logger.info(f"Processing transcription for session {state.session_id}")
    
    try:
        # Validate transcript chunk
        if not state.transcript_chunk:
            state.error = "No transcript chunk provided"
            return state
            
        required_fields = ['timestamp', 'speaker', 'utterance']
        if not all(field in state.transcript_chunk for field in required_fields):
            state.error = f"Missing required fields: {required_fields}"
            return state
        
        # Enrich transcript with metadata
        state.transcript_chunk['processed_at'] = datetime.now().isoformat()
        state.transcript_chunk['session_id'] = state.session_id
        
        # Basic text preprocessing
        utterance = state.transcript_chunk['utterance'].strip()
        if len(utterance) < 5:  # Skip very short utterances
            logger.info("Skipping short utterance")
            return state
            
        state.transcript_chunk['utterance'] = utterance
        state.transcript_chunk['word_count'] = len(utterance.split())
        
        logger.info(f"Processed utterance from {state.transcript_chunk['speaker']}: {utterance[:50]}...")
        
    except Exception as e:
        logger.error(f"Error in transcription ingestion: {str(e)}")
        state.error = f"Transcription ingestion failed: {str(e)}"
    
    return state

async def realtime_action_extraction(state: MeetingState) -> MeetingState:
    """
    Node: Extract actions from transcript using JavaScript extractors
    """
    logger.info("Extracting actions from transcript")
    
    try:
        # Import and use the JavaScript action extractor
        # In production, this would call the Node.js extractors via subprocess or API
        
        # Simulate action extraction for now
        utterance = state.transcript_chunk['utterance'].lower()
        
        # Simple pattern matching (would be replaced by full extractor)
        action_patterns = [
            ('hay que', 'task'),
            ('necesitamos', 'task'), 
            ('vamos a', 'task'),
            ('se acordó', 'decision'),
            ('decidimos', 'decision'),
            ('reunión', 'calendar'),
            ('agendar', 'calendar'),
            ('recordar', 'reminder'),
            ('seguimiento', 'followup')
        ]
        
        detected_actions = []
        for pattern, action_type in action_patterns:
            if pattern in utterance:
                action = {
                    'id': f"action_{datetime.now().timestamp()}_{hash(utterance) % 10000}",
                    'source': 'attendee',
                    'timestamp': state.transcript_chunk['timestamp'],
                    'speaker': state.transcript_chunk['speaker'],
                    'originalText': state.transcript_chunk['utterance'],
                    'extractedAction': utterance,
                    'confidence': 0.8,  # Would be calculated by real extractor
                    'type': action_type,
                    'entities': {},
                    'pattern_matched': pattern
                }
                detected_actions.append(action)
                logger.info(f"Detected {action_type} action: {pattern}")
        
        state.detected_actions = detected_actions
        
        if not detected_actions:
            logger.info("No actions detected in this utterance")
        
    except Exception as e:
        logger.error(f"Error in action extraction: {str(e)}")
        state.error = f"Action extraction failed: {str(e)}"
    
    return state

async def context_awareness_analysis(state: MeetingState) -> MeetingState:
    """
    Node: Analyze meeting context and historical information
    """
    logger.info("Analyzing meeting context")
    
    try:
        context_analysis = {
            'meeting_phase': 'discussion',  # Default
            'participant_count': len(state.meeting_context.get('participants', [])),
            'session_duration': 0,
            'action_count': len(state.detected_actions),
            'speaker_activity': {},
            'topic_continuity': False,
            'urgency_indicators': [],
            'project_references': [],
            'decision_points': []
        }
        
        # Analyze speaker activity
        if state.transcript_chunk.get('speaker'):
            speaker = state.transcript_chunk['speaker']
            context_analysis['current_speaker'] = speaker
            
        # Detect meeting phase based on content
        utterance = state.transcript_chunk['utterance'].lower()
        if any(word in utterance for word in ['comenzamos', 'empezamos', 'start']):
            context_analysis['meeting_phase'] = 'opening'
        elif any(word in utterance for word in ['decidir', 'acordar', 'decide']):
            context_analysis['meeting_phase'] = 'decision'
        elif any(word in utterance for word in ['planificar', 'organizar', 'plan']):
            context_analysis['meeting_phase'] = 'planning'
        elif any(word in utterance for word in ['terminamos', 'concluir', 'finish']):
            context_analysis['meeting_phase'] = 'closing'
            
        # Detect urgency indicators
        urgency_words = ['urgente', 'asap', 'crítico', 'ya', 'ahora', 'urgent', 'critical']
        for word in urgency_words:
            if word in utterance:
                context_analysis['urgency_indicators'].append(word)
                
        # Extract project references
        import re
        project_pattern = r'proyecto\s+([a-zA-Z\s]+)'
        project_matches = re.findall(project_pattern, utterance, re.IGNORECASE)
        context_analysis['project_references'] = project_matches
        
        # Check for decision points
        decision_words = ['acordamos', 'decidimos', 'se estableció', 'confirmamos']
        if any(word in utterance for word in decision_words):
            context_analysis['decision_points'].append({
                'timestamp': state.transcript_chunk['timestamp'],
                'speaker': state.transcript_chunk['speaker'],
                'decision': utterance
            })
            
        state.context_analysis = context_analysis
        logger.info(f"Context analysis: phase={context_analysis['meeting_phase']}, urgency={len(context_analysis['urgency_indicators'])}")
        
    except Exception as e:
        logger.error(f"Error in context analysis: {str(e)}")
        state.error = f"Context analysis failed: {str(e)}"
    
    return state

async def intelligent_classification(state: MeetingState) -> MeetingState:
    """
    Node: Classify actions and determine intervention needs
    """
    logger.info("Classifying actions and determining interventions")
    
    try:
        classifications = []
        
        for action in state.detected_actions:
            # Simulate classification using the ClassificationEngine
            classification = {
                'action': action,
                'type': action['type'],
                'confidence': action['confidence'],
                'urgency': 'medium',
                'suggestedAgent': f"{action['type']}BuilderAgent",
                'interventionNeeded': False,
                'interventionType': None,
                'interventionMessage': None,
                'contextAnalysis': state.context_analysis,
                'recommendations': []
            }
            
            # Determine if intervention is needed
            utterance = action['extractedAction'].lower()
            
            # Check for missing assignee
            if action['type'] == 'task' and not action['entities'].get('assignee'):
                if any(word in utterance for word in ['hay que', 'necesitamos', 'alguien']):
                    classification['interventionNeeded'] = True
                    classification['interventionType'] = 'missing_assignee'
                    classification['interventionMessage'] = "¿Quién se encarga de esta tarea?"
                    classification['urgency'] = 'high'
            
            # Check for unclear deadline
            if action['type'] in ['task', 'calendar'] and not action['entities'].get('dueDate'):
                if any(word in utterance for word in ['pronto', 'rápido', 'soon']):
                    classification['interventionNeeded'] = True
                    classification['interventionType'] = 'unclear_deadline'
                    classification['interventionMessage'] = "¿Cuándo necesitamos esto listo?"
                    
            # Check for vague references
            if any(word in utterance for word in ['esto', 'eso', 'that', 'it']):
                classification['interventionNeeded'] = True
                classification['interventionType'] = 'missing_details'
                classification['interventionMessage'] = "¿Podrías especificar más detalles sobre esto?"
            
            # Adjust confidence based on context
            if state.context_analysis.get('urgency_indicators'):
                classification['urgency'] = 'high'
                classification['confidence'] = min(classification['confidence'] + 0.1, 1.0)
            
            # Generate recommendations
            recommendations = [
                {
                    'type': 'action',
                    'priority': 'high',
                    'message': f"Crear {action['type']} usando {classification['suggestedAgent']}",
                    'mcpCall': {
                        'agent': classification['suggestedAgent'],
                        'action': 'create',
                        'payload': {
                            'type': action['type'],
                            'title': action['extractedAction'],
                            'context': {
                                'source': 'meeting',
                                'speaker': action['speaker'],
                                'timestamp': action['timestamp']
                            }
                        }
                    }
                }
            ]
            
            if classification['interventionNeeded']:
                recommendations.append({
                    'type': 'intervention',
                    'priority': 'high',
                    'message': classification['interventionMessage'],
                    'mcpCall': {
                        'agent': 'meetingAssistantAgent',
                        'action': 'intervene',
                        'payload': {
                            'type': classification['interventionType'],
                            'message': classification['interventionMessage'],
                            'mode': state.mode
                        }
                    }
                })
            
            classification['recommendations'] = recommendations
            classifications.append(classification)
            
        state.classifications = classifications
        
        # Determine if any intervention should be triggered
        interventions_needed = [c for c in classifications if c['interventionNeeded']]
        if interventions_needed and state.mode == 'ears-and-mouth':
            # Select highest priority intervention
            best_intervention = max(interventions_needed, 
                                  key=lambda x: (x['urgency'] == 'high', x['confidence']))
            state.should_intervene = True
            state.intervention_message = best_intervention['interventionMessage']
            
        logger.info(f"Classified {len(classifications)} actions, {len(interventions_needed)} need intervention")
        
    except Exception as e:
        logger.error(f"Error in classification: {str(e)}")
        state.error = f"Classification failed: {str(e)}"
    
    return state

async def mcp_payload_generation(state: MeetingState) -> MeetingState:
    """
    Node: Generate MCP payloads for agent execution
    """
    logger.info("Generating MCP payloads")
    
    try:
        mcp_payloads = []
        
        for classification in state.classifications:
            action = classification['action']
            
            # Generate base payload
            payload = {
                'type': action['type'],
                'title': action['extractedAction'],
                'assignee': action['entities'].get('assignee'),
                'dueDate': action['entities'].get('dueDate'),
                'priority': action['entities'].get('priority', 'medium'),
                'context': {
                    'source': 'meeting',
                    'speaker': action['speaker'],
                    'timestamp': action['timestamp'],
                    'meetingPhase': state.context_analysis.get('meeting_phase'),
                    'sessionId': state.session_id,
                    'originalText': action['originalText']
                },
                'metadata': {
                    'extractionConfidence': action['confidence'],
                    'classificationConfidence': classification['confidence'],
                    'interventionTriggered': classification['interventionNeeded'],
                    'aiGenerated': True,
                    'mode': state.mode
                }
            }
            
            # Add context-specific information
            if state.context_analysis.get('project_references'):
                payload['context']['projects'] = state.context_analysis['project_references']
                
            if state.context_analysis.get('urgency_indicators'):
                payload['priority'] = 'high'
                payload['context']['urgencyIndicators'] = state.context_analysis['urgency_indicators']
            
            mcp_payload = {
                'agent': classification['suggestedAgent'],
                'action': 'create',
                'payload': payload,
                'classification': classification
            }
            
            mcp_payloads.append(mcp_payload)
            
        state.mcp_payloads = mcp_payloads
        logger.info(f"Generated {len(mcp_payloads)} MCP payloads")
        
    except Exception as e:
        logger.error(f"Error generating MCP payloads: {str(e)}")
        state.error = f"MCP payload generation failed: {str(e)}"
    
    return state

async def meeting_memory_update(state: MeetingState) -> MeetingState:
    """
    Node: Update meeting memory and context for future reference
    """
    logger.info("Updating meeting memory")
    
    try:
        # Update meeting context with new information
        if not state.meeting_context:
            state.meeting_context = {
                'sessionId': state.session_id,
                'startTime': datetime.now().isoformat(),
                'participants': [],
                'previousActions': [],
                'interventionHistory': [],
                'contextHistory': []
            }
        
        # Add current actions to history
        state.meeting_context['previousActions'].extend(state.detected_actions)
        
        # Add intervention history
        if state.should_intervene:
            intervention_record = {
                'timestamp': datetime.now().isoformat(),
                'type': state.classifications[0]['interventionType'] if state.classifications else 'unknown',
                'message': state.intervention_message,
                'mode': state.mode,
                'triggered': True
            }
            state.meeting_context['interventionHistory'].append(intervention_record)
        
        # Add context analysis to history
        context_record = {
            'timestamp': datetime.now().isoformat(),
            'phase': state.context_analysis.get('meeting_phase'),
            'speaker': state.transcript_chunk.get('speaker'),
            'actionCount': len(state.detected_actions),
            'urgencyLevel': len(state.context_analysis.get('urgency_indicators', []))
        }
        state.meeting_context['contextHistory'].append(context_record)
        
        # Keep only recent history (last 50 items)
        state.meeting_context['previousActions'] = state.meeting_context['previousActions'][-50:]
        state.meeting_context['interventionHistory'] = state.meeting_context['interventionHistory'][-20:]
        state.meeting_context['contextHistory'] = state.meeting_context['contextHistory'][-30:]
        
        logger.info("Meeting memory updated successfully")
        
    except Exception as e:
        logger.error(f"Error updating meeting memory: {str(e)}")
        state.error = f"Memory update failed: {str(e)}"
    
    return state

# Create the LangGraph workflow
def create_realtime_meeting_graph():
    """Create the LangGraph workflow for real-time meeting analysis"""
    
    workflow = StateGraph(MeetingState)
    
    # Add nodes
    workflow.add_node("ingest", realtime_transcription_ingestion)
    workflow.add_node("extract", realtime_action_extraction)
    workflow.add_node("context", context_awareness_analysis)
    workflow.add_node("classify", intelligent_classification)
    workflow.add_node("generate", mcp_payload_generation)
    workflow.add_node("memory", meeting_memory_update)
    
    # Define the flow
    workflow.set_entry_point("ingest")
    workflow.add_edge("ingest", "extract")
    workflow.add_edge("extract", "context")
    workflow.add_edge("context", "classify")
    workflow.add_edge("classify", "generate")
    workflow.add_edge("generate", "memory")
    workflow.add_edge("memory", END)
    
    return workflow.compile()

# Utility functions for integration
async def process_transcript_chunk(session_id: str, mode: str, transcript_chunk: Dict[str, Any], 
                                 meeting_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Process a single transcript chunk through the real-time analysis pipeline
    """
    try:
        # Create initial state
        state = create_meeting_state(session_id, mode)
        state.transcript_chunk = transcript_chunk
        state.meeting_context = meeting_context or {}
        
        # Run the workflow
        graph = create_realtime_meeting_graph()
        result = await graph.ainvoke(state)
        
        # Return processed result
        return {
            'success': True,
            'sessionId': session_id,
            'detectedActions': result.detected_actions,
            'classifications': result.classifications,
            'shouldIntervene': result.should_intervene,
            'interventionMessage': result.intervention_message,
            'mcpPayloads': result.mcp_payloads,
            'contextAnalysis': result.context_analysis,
            'updatedContext': result.meeting_context,
            'error': result.error
        }
        
    except Exception as e:
        logger.error(f"Error processing transcript chunk: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'sessionId': session_id
        }

# Export the main components
__all__ = [
    'MeetingState',
    'create_meeting_state',
    'create_realtime_meeting_graph',
    'process_transcript_chunk',
    'realtime_transcription_ingestion',
    'realtime_action_extraction',
    'context_awareness_analysis',
    'intelligent_classification',
    'mcp_payload_generation',
    'meeting_memory_update'
]

