/**
 * ClaudiaIntegration Component - Main Integration Hub
 * 
 * Central component for Claudia + UltraMCP integration
 * Provides unified interface for debate visualization and local model management
 */

import React, { useState, useEffect } from 'react';
import { 
  Brain, 
  Cpu, 
  Settings, 
  Activity,
  Play,
  Pause,
  StopCircle,
  RefreshCw,
  AlertTriangle,
  Users
} from 'lucide-react';

import DebateVisualization from './DebateVisualization';
import LocalModelManager from './LocalModelManager';

// =============================================================================
// SAMPLE DATA
// =============================================================================

const sampleDebateSession = {
  id: 'debate-123',
  topic: 'Should we migrate to microservices architecture?',
  status: 'active',
  currentRound: 2,
  maxRounds: 3,
  startTime: new Date(Date.now() - 1000 * 60 * 15), // 15 minutes ago
  participants: [
    {
      id: 'qwen-25-14b',
      name: 'Strategic Analyst',
      model: 'qwen2.5:14b',
      role: 'CFO',
      type: 'local',
      status: 'responding',
      confidence: 0.92,
      responseCount: 3,
      avgResponseTime: 32.5,
      color: '#8B5CF6'
    },
    {
      id: 'llama-31-8b',
      name: 'Balanced Reasoner',
      model: 'llama3.1:8b',
      role: 'CTO',
      type: 'local',
      status: 'active',
      confidence: 0.88,
      responseCount: 3,
      avgResponseTime: 17.5,
      color: '#10B981'
    },
    {
      id: 'qwen-coder-7b',
      name: 'Technical Specialist',
      model: 'qwen-coder:7b',
      role: 'Architect',
      type: 'local',
      status: 'thinking',
      confidence: 0.95,
      responseCount: 2,
      avgResponseTime: 14.0,
      color: '#3B82F6'
    }
  ],
  messages: [
    {
      id: 'msg-1',
      participantId: 'qwen-25-14b',
      content: 'From a strategic perspective, microservices offer better scalability and team autonomy. However, we need to consider the operational complexity and initial overhead.',
      timestamp: new Date(Date.now() - 1000 * 60 * 10),
      round: 1,
      confidence: 0.92,
      wordCount: 28,
      sentiment: 'neutral',
      keyPoints: ['scalability', 'team autonomy', 'operational complexity']
    },
    {
      id: 'msg-2',
      participantId: 'llama-31-8b',
      content: 'I agree with the strategic benefits. Additionally, microservices enable technology diversity and fault isolation. The DevOps investment is significant but manageable with proper planning.',
      timestamp: new Date(Date.now() - 1000 * 60 * 8),
      round: 1,
      confidence: 0.88,
      wordCount: 32,
      sentiment: 'positive',
      keyPoints: ['technology diversity', 'fault isolation', 'DevOps investment']
    },
    {
      id: 'msg-3',
      participantId: 'qwen-coder-7b',
      content: 'From a technical standpoint, our current monolith has performance bottlenecks. Microservices would allow targeted optimization and independent deployments.',
      timestamp: new Date(Date.now() - 1000 * 60 * 5),
      round: 2,
      confidence: 0.95,
      wordCount: 25,
      sentiment: 'positive',
      keyPoints: ['performance bottlenecks', 'targeted optimization', 'independent deployments']
    }
  ],
  decisions: [
    {
      id: 'decision-1',
      timestamp: new Date(Date.now() - 1000 * 60 * 5),
      description: 'Microservices provide better scalability',
      confidence: 0.92,
      supportingParticipants: ['qwen-25-14b', 'llama-31-8b', 'qwen-coder-7b'],
      opposingParticipants: [],
      status: 'consensus'
    },
    {
      id: 'decision-2',
      timestamp: new Date(Date.now() - 1000 * 60 * 3),
      description: 'DevOps complexity is manageable',
      confidence: 0.78,
      supportingParticipants: ['llama-31-8b'],
      opposingParticipants: [],
      status: 'pending'
    }
  ],
  overallConfidence: 0.85,
  costBreakdown: {
    local: 0.0,
    api: 0.0,
    total: 0.0
  },
  privacyScore: 100.0
};

// =============================================================================
// NAVIGATION COMPONENT
// =============================================================================

const Navigation = ({ activeView, onViewChange }) => {
  const views = [
    { id: 'debate', label: 'Debate Visualization', icon: Users },
    { id: 'models', label: 'Local Models', icon: Cpu },
    { id: 'settings', label: 'Settings', icon: Settings }
  ];

  return (
    <div className="bg-white border-b px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="h-6 w-6 text-blue-600" />
          <h1 className="text-xl font-bold">Claudia + UltraMCP</h1>
          <span className="text-sm text-gray-500">• Visual Multi-LLM Platform</span>
        </div>
        
        <nav className="flex items-center gap-1">
          {views.map((view) => {
            const Icon = view.icon;
            return (
              <button
                key={view.id}
                onClick={() => onViewChange(view.id)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${
                  activeView === view.id
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                <Icon className="h-4 w-4" />
                {view.label}
              </button>
            );
          })}
        </nav>
      </div>
    </div>
  );
};

// =============================================================================
// STATUS BAR COMPONENT
// =============================================================================

const StatusBar = ({ debateSession, localModels }) => {
  const activeModels = localModels.filter(m => m.status === 'active').length;
  const totalRequests = localModels.reduce((sum, m) => sum + m.performance.totalRequests, 0);

  return (
    <div className="bg-gray-50 border-t px-6 py-3">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-green-600" />
            <span className="font-medium">System Status:</span>
            <span className="text-green-600">Operational</span>
          </div>
          
          <div className="flex items-center gap-2">
            <Cpu className="h-4 w-4 text-blue-600" />
            <span>{activeModels}/5 Models Active</span>
          </div>
          
          <div className="flex items-center gap-2">
            <Brain className="h-4 w-4 text-purple-600" />
            <span>{totalRequests} Total Requests</span>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span>100% Privacy Score</span>
          </div>
          
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span>$0.00 Session Cost</span>
          </div>
        </div>
      </div>
    </div>
  );
};

// =============================================================================
// QUICK ACTIONS COMPONENT
// =============================================================================

const QuickActions = ({ debateSession, onStartDebate, onStartChat }) => {
  return (
    <div className="bg-white rounded-lg border shadow-sm p-4 mb-6">
      <h3 className="font-semibold mb-4">Quick Actions</h3>
      
      <div className="grid grid-cols-3 gap-4">
        <button 
          className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-400 hover:bg-blue-50 transition-colors"
          onClick={onStartDebate}
        >
          <Users className="h-6 w-6 text-gray-400 mx-auto mb-2" />
          <div className="text-sm font-medium">Start New Debate</div>
          <div className="text-xs text-gray-500">Multi-LLM discussion</div>
        </button>
        
        <button 
          className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-green-400 hover:bg-green-50 transition-colors"
          onClick={onStartChat}
        >
          <Brain className="h-6 w-6 text-gray-400 mx-auto mb-2" />
          <div className="text-sm font-medium">Local Model Chat</div>
          <div className="text-xs text-gray-500">Zero-cost AI chat</div>
        </button>
        
        <button className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-purple-400 hover:bg-purple-50 transition-colors">
          <Settings className="h-6 w-6 text-gray-400 mx-auto mb-2" />
          <div className="text-sm font-medium">Cost Optimization</div>
          <div className="text-xs text-gray-500">Smart routing</div>
        </button>
      </div>
    </div>
  );
};

// =============================================================================
// MAIN CLAUDIA INTEGRATION COMPONENT
// =============================================================================

const ClaudiaIntegration = () => {
  const [activeView, setActiveView] = useState('debate');
  const [debateSession, setDebateSession] = useState(sampleDebateSession);
  const [localModels, setLocalModels] = useState([]);
  const [loading, setLoading] = useState(false);

  // Fetch local models data
  useEffect(() => {
    // This would normally fetch from the MCP servers
    // For now, using sample data from LocalModelManager
    setLocalModels([
      {
        id: 'qwen-25-14b',
        name: 'Qwen 2.5 14B',
        version: '14b',
        size: '9.0 GB',
        ramUsage: '~12 GB',
        contextLength: 32000,
        specialization: 'Complex reasoning, strategic analysis',
        role: 'Strategic Analyst',
        status: 'active',
        performance: {
          avgResponseTime: 32.5,
          tokensPerSecond: 15.2,
          totalRequests: 147,
          avgConfidence: 0.92,
          uptime: 98.5,
          lastUsed: new Date(Date.now() - 1000 * 60 * 5)
        },
        capabilities: ['Strategic Planning', 'Complex Analysis', 'Research', 'Decision Making'],
        costPerToken: 0.0,
        privacyScore: 100,
        color: '#8B5CF6',
        icon: '🧠'
      }
      // Add other models as needed
    ]);
  }, []);

  // Debate control handlers
  const handlePauseDebate = () => {
    setDebateSession(prev => ({ ...prev, status: 'paused' }));
  };

  const handleResumeDebate = () => {
    setDebateSession(prev => ({ ...prev, status: 'active' }));
  };

  const handleStopDebate = () => {
    setDebateSession(prev => ({ ...prev, status: 'completed' }));
  };

  const handleIntervene = (type) => {
    console.log(`Intervention type: ${type}`);
    // Handle human intervention
  };

  // Model management handlers
  const handleModelStart = (modelId) => {
    setLocalModels(prev => prev.map(model => 
      model.id === modelId ? { ...model, status: 'active' } : model
    ));
  };

  const handleModelStop = (modelId) => {
    setLocalModels(prev => prev.map(model => 
      model.id === modelId ? { ...model, status: 'stopped' } : model
    ));
  };

  const handleModelConfigure = (modelId, config) => {
    console.log(`Configuring model ${modelId}:`, config);
  };

  const handleModelRemove = (modelId) => {
    setLocalModels(prev => prev.filter(model => model.id !== modelId));
  };

  const handleModelDownload = (modelName) => {
    console.log(`Downloading model: ${modelName}`);
  };

  const handleRefresh = () => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      // Refresh data
    }, 1000);
  };

  // Quick action handlers
  const handleStartDebate = () => {
    const topic = prompt('Enter debate topic:');
    if (topic) {
      setDebateSession(prev => ({
        ...prev,
        topic,
        status: 'active',
        currentRound: 1,
        startTime: new Date(),
        messages: []
      }));
      setActiveView('debate');
    }
  };

  const handleStartChat = () => {
    // Navigate to chat interface or open chat modal
    console.log('Starting local model chat...');
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Navigation */}
      <Navigation activeView={activeView} onViewChange={setActiveView} />
      
      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        {activeView === 'debate' && (
          <div className="h-full p-6">
            <QuickActions 
              debateSession={debateSession}
              onStartDebate={handleStartDebate}
              onStartChat={handleStartChat}
            />
            
            <DebateVisualization
              session={debateSession}
              onPause={handlePauseDebate}
              onResume={handleResumeDebate}
              onStop={handleStopDebate}
              onIntervene={handleIntervene}
            />
          </div>
        )}
        
        {activeView === 'models' && (
          <LocalModelManager
            models={localModels}
            onModelStart={handleModelStart}
            onModelStop={handleModelStop}
            onModelRemove={handleModelRemove}
            onModelDownload={handleModelDownload}
            onModelConfigure={handleModelConfigure}
            onRefresh={handleRefresh}
          />
        )}
        
        {activeView === 'settings' && (
          <div className="p-6">
            <div className="bg-white rounded-lg border shadow-sm p-6">
              <h2 className="text-xl font-semibold mb-4">Claudia Integration Settings</h2>
              
              <div className="space-y-6">
                <div>
                  <h3 className="font-medium mb-3">MCP Server Configuration</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Chain-of-Debate Server:</span>
                      <span className="text-green-600">Connected</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Local Models Server:</span>
                      <span className="text-green-600">Connected</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Hybrid Decision Server:</span>
                      <span className="text-green-600">Connected</span>
                    </div>
                  </div>
                </div>
                
                <div>
                  <h3 className="font-medium mb-3">Default Preferences</h3>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <label className="text-sm">Prefer local models</label>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" className="sr-only peer" defaultChecked />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                      </label>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <label className="text-sm">Privacy-first mode</label>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" className="sr-only peer" defaultChecked />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                      </label>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <label className="text-sm">Auto-start debates on topic input</label>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" className="sr-only peer" />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                      </label>
                    </div>
                  </div>
                </div>
                
                <div>
                  <h3 className="font-medium mb-3">Performance</h3>
                  <div className="text-sm text-gray-600">
                    All processing is performed locally with zero external API calls.
                    Privacy score: 100% • Cost per session: $0.00
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
      
      {/* Status Bar */}
      <StatusBar debateSession={debateSession} localModels={localModels} />
    </div>
  );
};

export default ClaudiaIntegration;