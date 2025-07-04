/**
 * DebateVisualization Component - Adapted for UltraMCP Frontend
 * 
 * Real-time visual interface for UltraMCP Chain-of-Debate Protocol
 * Features: Participant circles, message flow, decision timeline, confidence metrics
 */

import React, { useState, useEffect, useRef } from 'react';
import { 
  Play,
  Pause,
  RotateCcw,
  AlertTriangle,
  CheckCircle2,
  Users,
  Activity,
  Brain, 
  MessageSquare, 
  Clock, 
  Target, 
  TrendingUp, 
  Shield, 
  DollarSign
} from 'lucide-react';

// =============================================================================
// PARTICIPANT CIRCLE COMPONENT
// =============================================================================

const ParticipantCircle = ({ participants, activeParticipant }) => {
  const radius = 120;
  const centerX = 150;
  const centerY = 150;

  const getParticipantPosition = (index, total) => {
    const angle = (index * 2 * Math.PI) / total - Math.PI / 2;
    return {
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle)
    };
  };

  return (
    <div className="bg-white rounded-lg border shadow-sm p-4 h-80">
      <div className="flex items-center gap-2 mb-4">
        <Users className="h-4 w-4" />
        <h3 className="text-sm font-semibold">Debate Participants</h3>
      </div>
      
      <div className="relative w-[300px] h-[300px] mx-auto">
        <svg width="300" height="300" className="absolute inset-0">
          {/* Connection lines */}
          {participants.map((participant, index) => {
            const pos = getParticipantPosition(index, participants.length);
            return (
              <g key={`line-${participant.id}`}>
                <line
                  x1={centerX}
                  y1={centerY}
                  x2={pos.x}
                  y2={pos.y}
                  stroke="#e2e8f0"
                  strokeWidth="1"
                  strokeDasharray="4,4"
                />
              </g>
            );
          })}
          
          {/* Center topic circle */}
          <circle
            cx={centerX}
            cy={centerY}
            r="20"
            fill="#3b82f6"
            className="opacity-20"
          />
          <text
            x={centerX}
            y={centerY}
            textAnchor="middle"
            dominantBaseline="middle"
            className="text-xs font-semibold fill-current"
          >
            Topic
          </text>
        </svg>

        {/* Participant nodes */}
        {participants.map((participant, index) => {
          const pos = getParticipantPosition(index, participants.length);
          const isActive = activeParticipant === participant.id;
          
          return (
            <div
              key={participant.id}
              className={`absolute transition-all duration-300 ${isActive ? 'scale-110' : 'scale-100'}`}
              style={{ 
                left: pos.x - 25, 
                top: pos.y - 25,
                width: 50,
                height: 50
              }}
              title={`${participant.name} (${participant.model}) - ${participant.role}`}
            >
              <div 
                className={`w-12 h-12 rounded-full border-3 flex items-center justify-center text-xs font-bold text-white relative ${
                  participant.type === 'local' ? 'bg-green-500' : 'bg-blue-500'
                } ${isActive ? 'ring-4 ring-yellow-400 ring-opacity-50' : ''}`}
                style={{ borderColor: participant.color }}
              >
                {participant.type === 'local' ? '🤖' : '🌐'}
                
                {/* Status indicator */}
                <div className={`absolute -top-1 -right-1 w-3 h-3 rounded-full ${
                  participant.status === 'active' ? 'bg-green-400' :
                  participant.status === 'thinking' ? 'bg-yellow-400' :
                  participant.status === 'responding' ? 'bg-blue-400' : 'bg-gray-400'
                }`} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// =============================================================================
// MESSAGE STREAM COMPONENT
// =============================================================================

const MessageStream = ({ messages, participants }) => {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const getParticipant = (id) => participants.find(p => p.id === id);

  return (
    <div className="bg-white rounded-lg border shadow-sm p-4 h-96">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <MessageSquare className="h-4 w-4" />
          <h3 className="text-sm font-semibold">Debate Stream</h3>
        </div>
        <span className="text-xs bg-gray-100 px-2 py-1 rounded">
          {messages.length} messages
        </span>
      </div>
      
      <div className="h-80 overflow-y-auto" ref={scrollRef}>
        <div className="space-y-4">
          {messages.map((message) => {
            const participant = getParticipant(message.participantId);
            if (!participant) return null;

            return (
              <div
                key={message.id}
                className="border rounded-lg p-3 space-y-2 transition-all duration-300 hover:shadow-sm"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div 
                      className="w-6 h-6 rounded-full flex items-center justify-center text-xs text-white"
                      style={{ backgroundColor: participant.color }}
                    >
                      {participant.type === 'local' ? '🤖' : '🌐'}
                    </div>
                    <span className="font-semibold text-sm">{participant.name}</span>
                    <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                      Round {message.round}
                    </span>
                  </div>
                  
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <span>{message.timestamp.toLocaleTimeString()}</span>
                    <span className={`px-2 py-1 rounded text-white ${
                      message.confidence > 0.8 ? 'bg-green-500' : 
                      message.confidence > 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}>
                      {(message.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
                
                <div className="text-sm text-gray-700">
                  {message.content}
                </div>
                
                {message.keyPoints && message.keyPoints.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {message.keyPoints.map((point, index) => (
                      <span key={index} className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                        {point}
                      </span>
                    ))}
                  </div>
                )}
                
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>{message.wordCount} words</span>
                  <span className={`px-2 py-1 rounded ${
                    message.sentiment === 'positive' ? 'bg-green-100 text-green-800' :
                    message.sentiment === 'negative' ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'
                  }`}>
                    {message.sentiment}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

// =============================================================================
// DECISION TIMELINE COMPONENT
// =============================================================================

const DecisionTimeline = ({ decisions }) => {
  return (
    <div className="bg-white rounded-lg border shadow-sm p-4 h-64">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Target className="h-4 w-4" />
          <h3 className="text-sm font-semibold">Decision Points</h3>
        </div>
        <span className="text-xs bg-gray-100 px-2 py-1 rounded">
          {decisions.filter(d => d.status === 'consensus').length} consensus
        </span>
      </div>
      
      <div className="h-48 overflow-y-auto">
        <div className="space-y-3">
          {decisions.map((decision, index) => (
            <div
              key={decision.id}
              className="flex items-start gap-3 border-l-2 border-gray-200 pl-3 transition-all duration-300"
            >
              <div className={`w-2 h-2 rounded-full mt-1 ${
                decision.status === 'consensus' ? 'bg-green-500' :
                decision.status === 'conflict' ? 'bg-red-500' : 'bg-yellow-500'
              }`} />
              
              <div className="flex-1 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{decision.description}</span>
                  <span className={`text-xs px-2 py-1 rounded ${
                    decision.status === 'consensus' ? 'bg-green-100 text-green-800' :
                    decision.status === 'conflict' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {decision.status}
                  </span>
                </div>
                
                <div className="text-xs text-gray-500">
                  {decision.timestamp.toLocaleTimeString()} • 
                  Confidence: {(decision.confidence * 100).toFixed(0)}%
                </div>
                
                <div className="text-xs space-y-1">
                  <div className="text-green-600">
                    Supporting: {decision.supportingParticipants.length}
                  </div>
                  <div className="text-red-600">
                    Opposing: {decision.opposingParticipants.length}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// =============================================================================
// METRICS DASHBOARD COMPONENT
// =============================================================================

const MetricsDashboard = ({ session }) => {
  return (
    <div className="grid grid-cols-2 gap-4">
      {/* Confidence Meter */}
      <div className="bg-white rounded-lg border shadow-sm p-4">
        <div className="flex items-center gap-2 mb-2">
          <TrendingUp className="h-4 w-4" />
          <h4 className="text-sm font-semibold">Overall Confidence</h4>
        </div>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-2xl font-bold">
              {(session.overallConfidence * 100).toFixed(1)}%
            </span>
            <span className={`text-xs px-2 py-1 rounded ${
              session.overallConfidence > 0.8 ? 'bg-green-100 text-green-800' : 
              session.overallConfidence > 0.6 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
            }`}>
              {session.overallConfidence > 0.8 ? 'High' : session.overallConfidence > 0.6 ? 'Medium' : 'Low'}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${session.overallConfidence * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* Privacy Score */}
      <div className="bg-white rounded-lg border shadow-sm p-4">
        <div className="flex items-center gap-2 mb-2">
          <Shield className="h-4 w-4" />
          <h4 className="text-sm font-semibold">Privacy Score</h4>
        </div>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-2xl font-bold text-blue-600">
              {session.privacyScore.toFixed(0)}%
            </span>
            <span className="text-xs bg-gray-100 px-2 py-1 rounded">
              {session.privacyScore === 100 ? 'Local Only' : 'Hybrid'}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${session.privacyScore}%` }}
            />
          </div>
        </div>
      </div>

      {/* Cost Breakdown */}
      <div className="bg-white rounded-lg border shadow-sm p-4">
        <div className="flex items-center gap-2 mb-2">
          <DollarSign className="h-4 w-4" />
          <h4 className="text-sm font-semibold">Cost Breakdown</h4>
        </div>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-500">Local</span>
            <span className="font-semibold text-green-600">
              ${session.costBreakdown.local.toFixed(4)}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-500">API</span>
            <span className="font-semibold text-blue-600">
              ${session.costBreakdown.api.toFixed(4)}
            </span>
          </div>
          <hr className="my-2" />
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold">Total</span>
            <span className="font-bold">
              ${session.costBreakdown.total.toFixed(4)}
            </span>
          </div>
        </div>
      </div>

      {/* Progress */}
      <div className="bg-white rounded-lg border shadow-sm p-4">
        <div className="flex items-center gap-2 mb-2">
          <Activity className="h-4 w-4" />
          <h4 className="text-sm font-semibold">Progress</h4>
        </div>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-500">Round</span>
            <span className="font-semibold">
              {session.currentRound} / {session.maxRounds}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(session.currentRound / session.maxRounds) * 100}%` }}
            />
          </div>
          <div className="text-xs text-gray-500">
            Duration: {Math.floor((Date.now() - session.startTime.getTime()) / 1000 / 60)}m
          </div>
        </div>
      </div>
    </div>
  );
};

// =============================================================================
// MAIN DEBATE VISUALIZATION COMPONENT
// =============================================================================

const DebateVisualization = ({
  session,
  onPause,
  onResume,
  onStop,
  onIntervene
}) => {
  const [activeParticipant, setActiveParticipant] = useState(null);

  // Simulate active participant based on most recent message
  useEffect(() => {
    if (session.messages.length > 0) {
      const latestMessage = session.messages[session.messages.length - 1];
      setActiveParticipant(latestMessage.participantId);
      
      // Clear active participant after 3 seconds
      const timer = setTimeout(() => setActiveParticipant(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [session.messages]);

  const getStatusIcon = () => {
    switch (session.status) {
      case 'active': return <Play className="h-4 w-4 text-green-500" />;
      case 'paused': return <Pause className="h-4 w-4 text-yellow-500" />;
      case 'completed': return <CheckCircle2 className="h-4 w-4 text-blue-500" />;
      case 'failed': return <AlertTriangle className="h-4 w-4 text-red-500" />;
      default: return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  return (
    <div className="h-full flex flex-col space-y-4 p-4">
      {/* Header with controls */}
      <div className="bg-white rounded-lg border shadow-sm p-4">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              {getStatusIcon()}
              {session.topic}
            </h2>
            <p className="text-sm text-gray-500">
              Chain-of-Debate Session • {session.participants.length} participants
            </p>
          </div>
          
          <div className="flex items-center gap-2">
            {session.status === 'active' && (
              <button 
                className="px-3 py-2 text-sm border rounded-md hover:bg-gray-50 flex items-center gap-1"
                onClick={onPause}
              >
                <Pause className="h-4 w-4" />
                Pause
              </button>
            )}
            
            {session.status === 'paused' && (
              <button 
                className="px-3 py-2 text-sm border rounded-md hover:bg-gray-50 flex items-center gap-1"
                onClick={onResume}
              >
                <Play className="h-4 w-4" />
                Resume
              </button>
            )}
            
            <button 
              className="px-3 py-2 text-sm border rounded-md hover:bg-orange-50 text-orange-600 hover:text-orange-700"
              onClick={() => onIntervene('guidance')}
            >
              Intervene
            </button>
            
            <button 
              className="px-3 py-2 text-sm bg-red-500 text-white rounded-md hover:bg-red-600"
              onClick={onStop}
            >
              Stop
            </button>
          </div>
        </div>
      </div>

      {/* Main visualization area */}
      <div className="flex-1 grid grid-cols-4 gap-4">
        {/* Left column - Participants and metrics */}
        <div className="space-y-4">
          <ParticipantCircle 
            participants={session.participants} 
            activeParticipant={activeParticipant}
          />
          <MetricsDashboard session={session} />
        </div>

        {/* Middle column - Message stream */}
        <div className="col-span-2">
          <MessageStream 
            messages={session.messages} 
            participants={session.participants}
          />
        </div>

        {/* Right column - Decision timeline */}
        <div>
          <DecisionTimeline decisions={session.decisions} />
        </div>
      </div>

      {/* Low confidence warning */}
      {session.overallConfidence < 0.7 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 transition-all duration-300">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-yellow-600" />
            <span className="font-semibold text-yellow-800">Low Confidence Detected</span>
          </div>
          <p className="text-sm text-yellow-700 mt-1">
            The debate confidence has dropped below 70%. Consider providing guidance or clarification.
          </p>
          <div className="flex gap-2 mt-3">
            <button 
              className="px-3 py-1 text-sm border border-yellow-300 rounded hover:bg-yellow-100"
              onClick={() => onIntervene('guidance')}
            >
              Provide Guidance
            </button>
            <button 
              className="px-3 py-1 text-sm border border-yellow-300 rounded hover:bg-yellow-100"
              onClick={() => onIntervene('redirect')}
            >
              Redirect Discussion
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DebateVisualization;