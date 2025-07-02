/**
 * DebateVisualization Component
 * 
 * Real-time visual interface for UltraMCP Chain-of-Debate Protocol
 * Features: Participant circles, message flow, decision timeline, confidence metrics
 */

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Badge, 
  Button, 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle,
  Progress,
  ScrollArea,
  Separator,
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger
} from '@/components/ui';
import { 
  Brain, 
  MessageSquare, 
  Clock, 
  Target, 
  TrendingUp, 
  Shield, 
  DollarSign,
  Pause,
  Play,
  RotateCcw,
  AlertTriangle,
  CheckCircle2,
  Users,
  Activity
} from 'lucide-react';

// =============================================================================
// TYPES
// =============================================================================

interface Participant {
  id: string;
  name: string;
  model: string;
  role: string;
  type: 'local' | 'api';
  status: 'active' | 'thinking' | 'responding' | 'idle';
  confidence: number;
  responseCount: number;
  avgResponseTime: number;
  color: string;
}

interface DebateMessage {
  id: string;
  participantId: string;
  content: string;
  timestamp: Date;
  round: number;
  confidence: number;
  wordCount: number;
  sentiment: 'positive' | 'negative' | 'neutral';
  keyPoints: string[];
}

interface Decision {
  id: string;
  timestamp: Date;
  description: string;
  confidence: number;
  supportingParticipants: string[];
  opposingParticipants: string[];
  status: 'pending' | 'consensus' | 'conflict';
}

interface DebateSession {
  id: string;
  topic: string;
  status: 'initializing' | 'active' | 'paused' | 'completed' | 'failed';
  currentRound: number;
  maxRounds: number;
  startTime: Date;
  participants: Participant[];
  messages: DebateMessage[];
  decisions: Decision[];
  overallConfidence: number;
  costBreakdown: {
    local: number;
    api: number;
    total: number;
  };
  privacyScore: number;
}

interface DebateVisualizationProps {
  session: DebateSession;
  onPause: () => void;
  onResume: () => void;
  onStop: () => void;
  onIntervene: (type: 'guidance' | 'redirect' | 'override') => void;
}

// =============================================================================
// PARTICIPANT CIRCLE COMPONENT
// =============================================================================

const ParticipantCircle: React.FC<{ participants: Participant[]; activeParticipant?: string }> = ({ 
  participants, 
  activeParticipant 
}) => {
  const radius = 120;
  const centerX = 150;
  const centerY = 150;

  const getParticipantPosition = (index: number, total: number) => {
    const angle = (index * 2 * Math.PI) / total - Math.PI / 2;
    return {
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle)
    };
  };

  return (
    <Card className="h-80">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <Users className="h-4 w-4" />
          Debate Participants
        </CardTitle>
      </CardHeader>
      <CardContent>
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
              <TooltipProvider key={participant.id}>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <motion.div
                      className="absolute"
                      style={{ 
                        left: pos.x - 25, 
                        top: pos.y - 25,
                        width: 50,
                        height: 50
                      }}
                      animate={{
                        scale: isActive ? 1.2 : 1,
                        rotate: participant.status === 'thinking' ? 360 : 0
                      }}
                      transition={{
                        scale: { duration: 0.3 },
                        rotate: { duration: 2, repeat: participant.status === 'thinking' ? Infinity : 0 }
                      }}
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
                    </motion.div>
                  </TooltipTrigger>
                  <TooltipContent>
                    <div className="space-y-1">
                      <div className="font-semibold">{participant.name}</div>
                      <div className="text-xs text-muted-foreground">{participant.model}</div>
                      <div className="text-xs">Role: {participant.role}</div>
                      <div className="text-xs">Confidence: {(participant.confidence * 100).toFixed(1)}%</div>
                      <div className="text-xs">Responses: {participant.responseCount}</div>
                      <div className="text-xs">Avg Time: {participant.avgResponseTime.toFixed(1)}s</div>
                    </div>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};

// =============================================================================
// MESSAGE STREAM COMPONENT
// =============================================================================

const MessageStream: React.FC<{ messages: DebateMessage[]; participants: Participant[] }> = ({ 
  messages, 
  participants 
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const getParticipant = (id: string) => participants.find(p => p.id === id);

  return (
    <Card className="h-96">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <MessageSquare className="h-4 w-4" />
          Debate Stream
          <Badge variant="outline" className="ml-auto">
            {messages.length} messages
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-80" ref={scrollRef}>
          <div className="space-y-4">
            {messages.map((message) => {
              const participant = getParticipant(message.participantId);
              if (!participant) return null;

              return (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="border rounded-lg p-3 space-y-2"
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
                      <Badge variant="outline" size="sm">
                        Round {message.round}
                      </Badge>
                    </div>
                    
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span>{message.timestamp.toLocaleTimeString()}</span>
                      <Badge 
                        variant={message.confidence > 0.8 ? 'default' : message.confidence > 0.6 ? 'secondary' : 'destructive'}
                        size="sm"
                      >
                        {(message.confidence * 100).toFixed(0)}%
                      </Badge>
                    </div>
                  </div>
                  
                  <div className="text-sm text-foreground">
                    {message.content}
                  </div>
                  
                  {message.keyPoints && message.keyPoints.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {message.keyPoints.map((point, index) => (
                        <Badge key={index} variant="outline" size="sm">
                          {point}
                        </Badge>
                      ))}
                    </div>
                  )}
                  
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>{message.wordCount} words</span>
                    <Badge 
                      variant={
                        message.sentiment === 'positive' ? 'default' :
                        message.sentiment === 'negative' ? 'destructive' : 'secondary'
                      }
                      size="sm"
                    >
                      {message.sentiment}
                    </Badge>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
};

// =============================================================================
// DECISION TIMELINE COMPONENT
// =============================================================================

const DecisionTimeline: React.FC<{ decisions: Decision[] }> = ({ decisions }) => {
  return (
    <Card className="h-64">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <Target className="h-4 w-4" />
          Decision Points
          <Badge variant="outline" className="ml-auto">
            {decisions.filter(d => d.status === 'consensus').length} consensus
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-48">
          <div className="space-y-3">
            {decisions.map((decision, index) => (
              <motion.div
                key={decision.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="flex items-start gap-3 border-l-2 border-muted pl-3"
              >
                <div className={`w-2 h-2 rounded-full mt-1 ${
                  decision.status === 'consensus' ? 'bg-green-500' :
                  decision.status === 'conflict' ? 'bg-red-500' : 'bg-yellow-500'
                }`} />
                
                <div className="flex-1 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">{decision.description}</span>
                    <Badge 
                      variant={
                        decision.status === 'consensus' ? 'default' :
                        decision.status === 'conflict' ? 'destructive' : 'secondary'
                      }
                      size="sm"
                    >
                      {decision.status}
                    </Badge>
                  </div>
                  
                  <div className="text-xs text-muted-foreground">
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
              </motion.div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
};

// =============================================================================
// METRICS DASHBOARD COMPONENT
// =============================================================================

const MetricsDashboard: React.FC<{ session: DebateSession }> = ({ session }) => {
  return (
    <div className="grid grid-cols-2 gap-4">
      {/* Confidence Meter */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Overall Confidence
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold">
                {(session.overallConfidence * 100).toFixed(1)}%
              </span>
              <Badge 
                variant={session.overallConfidence > 0.8 ? 'default' : session.overallConfidence > 0.6 ? 'secondary' : 'destructive'}
              >
                {session.overallConfidence > 0.8 ? 'High' : session.overallConfidence > 0.6 ? 'Medium' : 'Low'}
              </Badge>
            </div>
            <Progress value={session.overallConfidence * 100} className="h-2" />
          </div>
        </CardContent>
      </Card>

      {/* Privacy Score */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <Shield className="h-4 w-4" />
            Privacy Score
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold text-blue-600">
                {session.privacyScore.toFixed(0)}%
              </span>
              <Badge variant="outline">
                {session.privacyScore === 100 ? 'Local Only' : 'Hybrid'}
              </Badge>
            </div>
            <Progress value={session.privacyScore} className="h-2" />
          </div>
        </CardContent>
      </Card>

      {/* Cost Breakdown */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <DollarSign className="h-4 w-4" />
            Cost Breakdown
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Local</span>
              <span className="font-semibold text-green-600">
                ${session.costBreakdown.local.toFixed(4)}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">API</span>
              <span className="font-semibold text-blue-600">
                ${session.costBreakdown.api.toFixed(4)}
              </span>
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold">Total</span>
              <span className="font-bold">
                ${session.costBreakdown.total.toFixed(4)}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Progress */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Progress
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Round</span>
              <span className="font-semibold">
                {session.currentRound} / {session.maxRounds}
              </span>
            </div>
            <Progress 
              value={(session.currentRound / session.maxRounds) * 100} 
              className="h-2" 
            />
            <div className="text-xs text-muted-foreground">
              Duration: {Math.floor((Date.now() - session.startTime.getTime()) / 1000 / 60)}m
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// =============================================================================
// MAIN DEBATE VISUALIZATION COMPONENT
// =============================================================================

const DebateVisualization: React.FC<DebateVisualizationProps> = ({
  session,
  onPause,
  onResume,
  onStop,
  onIntervene
}) => {
  const [activeParticipant, setActiveParticipant] = useState<string | undefined>();

  // Simulate active participant based on most recent message
  useEffect(() => {
    if (session.messages.length > 0) {
      const latestMessage = session.messages[session.messages.length - 1];
      setActiveParticipant(latestMessage.participantId);
      
      // Clear active participant after 3 seconds
      const timer = setTimeout(() => setActiveParticipant(undefined), 3000);
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
    <div className="h-full flex flex-col space-y-4">
      {/* Header with controls */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <CardTitle className="flex items-center gap-2">
                {getStatusIcon()}
                {session.topic}
              </CardTitle>
              <CardDescription>
                Chain-of-Debate Session • {session.participants.length} participants
              </CardDescription>
            </div>
            
            <div className="flex items-center gap-2">
              {session.status === 'active' && (
                <Button variant="outline" size="sm" onClick={onPause}>
                  <Pause className="h-4 w-4 mr-1" />
                  Pause
                </Button>
              )}
              
              {session.status === 'paused' && (
                <Button variant="outline" size="sm" onClick={onResume}>
                  <Play className="h-4 w-4 mr-1" />
                  Resume
                </Button>
              )}
              
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => onIntervene('guidance')}
                className="text-orange-600 hover:text-orange-700"
              >
                Intervene
              </Button>
              
              <Button variant="destructive" size="sm" onClick={onStop}>
                Stop
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

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

      {/* Intervention modal would go here */}
      {session.overallConfidence < 0.7 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-yellow-50 border border-yellow-200 rounded-lg p-4"
        >
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-yellow-600" />
            <span className="font-semibold text-yellow-800">Low Confidence Detected</span>
          </div>
          <p className="text-sm text-yellow-700 mt-1">
            The debate confidence has dropped below 70%. Consider providing guidance or clarification.
          </p>
          <div className="flex gap-2 mt-3">
            <Button 
              size="sm" 
              variant="outline"
              onClick={() => onIntervene('guidance')}
            >
              Provide Guidance
            </Button>
            <Button 
              size="sm" 
              variant="outline"
              onClick={() => onIntervene('redirect')}
            >
              Redirect Discussion
            </Button>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default DebateVisualization;