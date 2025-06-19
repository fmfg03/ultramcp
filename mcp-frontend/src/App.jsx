import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Activity, 
  Brain, 
  BarChart3, 
  Users, 
  Search,
  Settings,
  Zap,
  Terminal,
  GitBranch
} from 'lucide-react';

import AgentControlCenter from './components/agent/AgentControlCenter';

// Placeholder components for other tabs
const LangGraphVisualizer = () => (
  <div className="brutalist-card p-8 text-center">
    <GitBranch className="w-16 h-16 mx-auto mb-4 text-gray-400" />
    <h2 className="text-2xl font-bold uppercase mb-2">LangGraph Visualizer</h2>
    <p className="text-gray-600">Visual flow & node control - Coming Soon</p>
  </div>
);

const IntelligenceDashboard = () => (
  <div className="brutalist-card p-8 text-center">
    <Brain className="w-16 h-16 mx-auto mb-4 text-gray-400" />
    <h2 className="text-2xl font-bold uppercase mb-2">Intelligence Dashboard</h2>
    <p className="text-gray-600">Contradictions & rewards - Coming Soon</p>
  </div>
);

const LogsMetricsPanel = () => (
  <div className="brutalist-card p-8 text-center">
    <BarChart3 className="w-16 h-16 mx-auto mb-4 text-gray-400" />
    <h2 className="text-2xl font-bold uppercase mb-2">Logs & Metrics</h2>
    <p className="text-gray-600">Performance monitoring - Coming Soon</p>
  </div>
);

const AttendeePanel = () => (
  <div className="brutalist-card p-8 text-center">
    <Users className="w-16 h-16 mx-auto mb-4 text-gray-400" />
    <h2 className="text-2xl font-bold uppercase mb-2">Attendee Panel</h2>
    <p className="text-gray-600">Meeting transcriptions - Coming Soon</p>
  </div>
);

const ResearchHub = () => (
  <div className="brutalist-card p-8 text-center">
    <Search className="w-16 h-16 mx-auto mb-4 text-gray-400" />
    <h2 className="text-2xl font-bold uppercase mb-2">Research Hub</h2>
    <p className="text-gray-600">Perplexity-as-a-Service - Coming Soon</p>
  </div>
);

const App = () => {
  const [activeTab, setActiveTab] = useState('control');
  const [isConnected, setIsConnected] = useState(false);

  const tabs = [
    {
      id: 'control',
      name: 'Agent Control',
      icon: Activity,
      component: AgentControlCenter,
      description: 'Live agent execution & prompt ops'
    },
    {
      id: 'graph',
      name: 'LangGraph',
      icon: GitBranch,
      component: LangGraphVisualizer,
      description: 'Visual flow & node control'
    },
    {
      id: 'intelligence',
      name: 'Intelligence',
      icon: Brain,
      component: IntelligenceDashboard,
      description: 'Contradictions & rewards'
    },
    {
      id: 'logs',
      name: 'Logs & Metrics',
      icon: BarChart3,
      component: LogsMetricsPanel,
      description: 'Performance monitoring'
    },
    {
      id: 'attendee',
      name: 'Attendee',
      icon: Users,
      component: AttendeePanel,
      description: 'Meeting transcriptions'
    },
    {
      id: 'research',
      name: 'Research Hub',
      icon: Search,
      component: ResearchHub,
      description: 'Perplexity-as-a-Service'
    }
  ];

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component;

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <div className="w-80 bg-white border-r-4 border-black shadow-[8px_0px_0px_0px_rgba(0,0,0,1)]">
        <div className="p-6 border-b-4 border-black bg-black text-white">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white rounded-none flex items-center justify-center">
              <Terminal className="w-6 h-6 text-black" />
            </div>
            <div>
              <h1 className="text-xl font-bold uppercase tracking-wider">MCP SYSTEM</h1>
              <p className="text-sm opacity-80">DevOps Intelligence Hub</p>
            </div>
          </div>
          
          <div className="mt-4 flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`} />
            <span className="text-sm font-mono">
              {isConnected ? 'CONNECTED' : 'DISCONNECTED'}
            </span>
          </div>
        </div>

        <nav className="p-4 space-y-2">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            
            return (
              <motion.button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full p-4 text-left border-4 border-black transition-all duration-150 ${
                  isActive 
                    ? 'bg-black text-white shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]' 
                    : 'bg-white hover:bg-gray-100 shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]'
                }`}
                whileHover={{ x: 2, y: 2 }}
                whileTap={{ x: 1, y: 1 }}
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-5 h-5" />
                  <div>
                    <div className="font-bold uppercase tracking-wide text-sm">
                      {tab.name}
                    </div>
                    <div className={`text-xs ${isActive ? 'text-gray-300' : 'text-gray-500'}`}>
                      {tab.description}
                    </div>
                  </div>
                </div>
              </motion.button>
            );
          })}
        </nav>

        <div className="absolute bottom-4 left-4 right-4">
          <div className="brutalist-card p-4">
            <h3 className="font-bold uppercase text-sm mb-2">System Status</h3>
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between">
                <span>Local LLMs:</span>
                <span className="text-green-600 font-bold">5 ACTIVE</span>
              </div>
              <div className="flex justify-between">
                <span>API Keys:</span>
                <span className="text-green-600 font-bold">4 VALID</span>
              </div>
              <div className="flex justify-between">
                <span>Agents:</span>
                <span className="text-blue-600 font-bold">3 RUNNING</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 flex flex-col">
        <div className="h-16 bg-white border-b-4 border-black flex items-center justify-between px-6">
          <div>
            <h2 className="text-2xl font-bold uppercase tracking-wider">
              {tabs.find(tab => tab.id === activeTab)?.name}
            </h2>
            <p className="text-sm text-gray-600">
              {tabs.find(tab => tab.id === activeTab)?.description}
            </p>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="live-indicator">
              <div className="flex items-center gap-2 bg-red-500 text-white px-3 py-1 font-bold text-sm uppercase tracking-wider">
                <Zap className="w-4 h-4" />
                LIVE
              </div>
            </div>
            
            <button className="brutalist-button p-2">
              <Settings className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="flex-1 p-6 overflow-auto">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className="h-full"
            >
              {ActiveComponent && <ActiveComponent />}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};

export default App;

