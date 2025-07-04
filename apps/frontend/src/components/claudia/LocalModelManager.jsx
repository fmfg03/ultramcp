/**
 * LocalModelManager Component - Adapted for UltraMCP Frontend
 * 
 * Comprehensive management interface for UltraMCP's 5 local LLM models
 * Features: Performance monitoring, usage analytics, model selection, cost tracking
 */

import React, { useState, useEffect } from 'react';
import {
  Cpu,
  HardDrive,
  Zap,
  Activity,
  Clock,
  BarChart3,
  Settings,
  Download,
  Trash2,
  PlayCircle,
  StopCircle,
  RefreshCw,
  TrendingUp,
  Shield,
  DollarSign,
  Brain,
  ChevronRight,
  AlertCircle,
  CheckCircle2,
  Gauge
} from 'lucide-react';

// =============================================================================
// SAMPLE DATA
// =============================================================================

const sampleModels = [
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
      lastUsed: new Date(Date.now() - 1000 * 60 * 5) // 5 minutes ago
    },
    capabilities: ['Strategic Planning', 'Complex Analysis', 'Research', 'Decision Making'],
    costPerToken: 0.0,
    privacyScore: 100,
    color: '#8B5CF6',
    icon: '🧠'
  },
  {
    id: 'llama-31-8b',
    name: 'Llama 3.1 8B',
    version: '8b',
    size: '4.9 GB',
    ramUsage: '~7 GB',
    contextLength: 128000,
    specialization: 'High-quality general analysis',
    role: 'Balanced Reasoner',
    status: 'active',
    performance: {
      avgResponseTime: 17.5,
      tokensPerSecond: 28.4,
      totalRequests: 203,
      avgConfidence: 0.88,
      uptime: 99.2,
      lastUsed: new Date(Date.now() - 1000 * 60 * 2) // 2 minutes ago
    },
    capabilities: ['General Analysis', 'Writing', 'Reasoning', 'Creative Tasks'],
    costPerToken: 0.0,
    privacyScore: 100,
    color: '#10B981',
    icon: '⚖️'
  },
  {
    id: 'qwen-coder-7b',
    name: 'Qwen Coder 7B',
    version: '7b',
    size: '4.7 GB',
    ramUsage: '~7 GB',
    contextLength: 32000,
    specialization: 'Technical analysis, code review',
    role: 'Technical Specialist',
    status: 'active',
    performance: {
      avgResponseTime: 14.0,
      tokensPerSecond: 35.1,
      totalRequests: 89,
      avgConfidence: 0.95,
      uptime: 97.8,
      lastUsed: new Date(Date.now() - 1000 * 60 * 10) // 10 minutes ago
    },
    capabilities: ['Code Review', 'Architecture', 'Technical Analysis', 'Debugging'],
    costPerToken: 0.0,
    privacyScore: 100,
    color: '#3B82F6',
    icon: '💻'
  },
  {
    id: 'mistral-7b',
    name: 'Mistral 7B',
    version: '7b',
    size: '4.1 GB',
    ramUsage: '~6 GB',
    contextLength: 32000,
    specialization: 'Quick analysis, practical views',
    role: 'Rapid Analyst',
    status: 'active',
    performance: {
      avgResponseTime: 10.0,
      tokensPerSecond: 42.7,
      totalRequests: 312,
      avgConfidence: 0.83,
      uptime: 99.7,
      lastUsed: new Date(Date.now() - 1000 * 30) // 30 seconds ago
    },
    capabilities: ['Rapid Analysis', 'Brainstorming', 'Quick Feedback', 'Iteration'],
    costPerToken: 0.0,
    privacyScore: 100,
    color: '#F59E0B',
    icon: '⚡'
  },
  {
    id: 'deepseek-coder-67b',
    name: 'DeepSeek Coder 6.7B',
    version: '6.7b',
    size: '3.8 GB',
    ramUsage: '~6 GB',
    contextLength: 16000,
    specialization: 'Advanced technical evaluation',
    role: 'System Architect',
    status: 'idle',
    performance: {
      avgResponseTime: 16.0,
      tokensPerSecond: 31.3,
      totalRequests: 156,
      avgConfidence: 0.91,
      uptime: 95.4,
      lastUsed: new Date(Date.now() - 1000 * 60 * 30) // 30 minutes ago
    },
    capabilities: ['System Design', 'Algorithm Analysis', 'Code Optimization', 'Architecture'],
    costPerToken: 0.0,
    privacyScore: 100,
    color: '#EF4444',
    icon: '🏗️'
  }
];

// =============================================================================
// MODEL CARD COMPONENT
// =============================================================================

const ModelCard = ({ model, onStart, onStop, onConfigure, onRemove }) => {
  const [showDetails, setShowDetails] = useState(false);

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'text-green-500';
      case 'idle': return 'text-yellow-500';
      case 'loading': return 'text-blue-500';
      case 'error': return 'text-red-500';
      case 'stopped': return 'text-gray-500';
      default: return 'text-gray-500';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active': return <CheckCircle2 className="h-4 w-4" />;
      case 'idle': return <Clock className="h-4 w-4" />;
      case 'loading': return <RefreshCw className="h-4 w-4 animate-spin" />;
      case 'error': return <AlertCircle className="h-4 w-4" />;
      case 'stopped': return <StopCircle className="h-4 w-4" />;
      default: return <Activity className="h-4 w-4" />;
    }
  };

  return (
    <div className="bg-white rounded-lg border shadow-sm p-4 h-full transition-all duration-200 hover:shadow-md">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div 
            className="w-10 h-10 rounded-lg flex items-center justify-center text-lg"
            style={{ backgroundColor: `${model.color}20`, color: model.color }}
          >
            {model.icon}
          </div>
          <div>
            <h3 className="font-semibold">{model.name}</h3>
            <p className="text-sm text-gray-500">{model.role}</p>
          </div>
        </div>
        
        <div className={`flex items-center gap-1 ${getStatusColor(model.status)}`}>
          {getStatusIcon(model.status)}
          <span className={`text-xs px-2 py-1 rounded ${
            model.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
          }`}>
            {model.status}
          </span>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 gap-3 text-sm mb-4">
        <div>
          <div className="text-gray-500">Response Time</div>
          <div className="font-semibold">{model.performance.avgResponseTime.toFixed(1)}s</div>
        </div>
        <div>
          <div className="text-gray-500">Tokens/sec</div>
          <div className="font-semibold">{model.performance.tokensPerSecond.toFixed(1)}</div>
        </div>
        <div>
          <div className="text-gray-500">Requests</div>
          <div className="font-semibold">{model.performance.totalRequests}</div>
        </div>
        <div>
          <div className="text-gray-500">Confidence</div>
          <div className="font-semibold">{(model.performance.avgConfidence * 100).toFixed(0)}%</div>
        </div>
      </div>

      {/* Storage & Memory */}
      <div className="space-y-2 mb-4">
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Storage:</span>
          <span className="font-semibold">{model.size}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">RAM Usage:</span>
          <span className="font-semibold">{model.ramUsage}</span>
        </div>
      </div>

      {/* Uptime Progress */}
      <div className="space-y-1 mb-4">
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Uptime</span>
          <span className="font-semibold">{model.performance.uptime.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-1">
          <div 
            className="bg-blue-600 h-1 rounded-full transition-all duration-300"
            style={{ width: `${model.performance.uptime}%` }}
          />
        </div>
      </div>

      {/* Capabilities */}
      {showDetails && (
        <div className="space-y-3 mb-4 border-t pt-4">
          <div>
            <div className="text-sm text-gray-500 mb-2">Specialization</div>
            <div className="text-sm">{model.specialization}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500 mb-2">Capabilities</div>
            <div className="flex flex-wrap gap-1">
              {model.capabilities.map((capability, index) => (
                <span key={index} className="text-xs bg-gray-100 text-gray-800 px-2 py-1 rounded">
                  {capability}
                </span>
              ))}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-500 mb-1">Last Used</div>
            <div className="text-sm">{model.performance.lastUsed.toLocaleString()}</div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex flex-wrap gap-2">
        {model.status === 'active' ? (
          <button 
            className="px-3 py-1 text-sm border rounded hover:bg-gray-50 flex items-center gap-1"
            onClick={onStop}
          >
            <StopCircle className="h-3 w-3" />
            Stop
          </button>
        ) : (
          <button 
            className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 flex items-center gap-1"
            onClick={onStart}
          >
            <PlayCircle className="h-3 w-3" />
            Start
          </button>
        )}
        
        <button 
          className="px-3 py-1 text-sm border rounded hover:bg-gray-50 flex items-center gap-1"
          onClick={onConfigure}
        >
          <Settings className="h-3 w-3" />
          Config
        </button>
        
        <button 
          className="px-3 py-1 text-sm text-gray-500 hover:bg-gray-50 flex items-center gap-1"
          onClick={() => setShowDetails(!showDetails)}
        >
          <ChevronRight className={`h-3 w-3 transition-transform ${showDetails ? 'rotate-90' : ''}`} />
          {showDetails ? 'Less' : 'More'}
        </button>
      </div>
    </div>
  );
};

// =============================================================================
// PERFORMANCE CHARTS COMPONENT
// =============================================================================

const PerformanceCharts = ({ models }) => {
  return (
    <div className="grid grid-cols-2 gap-4">
      {/* Response Time Comparison */}
      <div className="bg-white rounded-lg border shadow-sm p-4">
        <div className="flex items-center gap-2 mb-4">
          <Clock className="h-4 w-4" />
          <h3 className="text-sm font-semibold">Response Time Comparison</h3>
        </div>
        <div className="space-y-3">
          {models.map((model) => (
            <div key={model.id} className="space-y-1">
              <div className="flex justify-between text-sm">
                <span>{model.name}</span>
                <span className="font-semibold">{model.performance.avgResponseTime.toFixed(1)}s</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="h-2 rounded-full transition-all duration-300"
                  style={{ 
                    width: `${(1 / model.performance.avgResponseTime) * 100}%`,
                    backgroundColor: model.color 
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Throughput Comparison */}
      <div className="bg-white rounded-lg border shadow-sm p-4">
        <div className="flex items-center gap-2 mb-4">
          <Zap className="h-4 w-4" />
          <h3 className="text-sm font-semibold">Throughput (Tokens/sec)</h3>
        </div>
        <div className="space-y-3">
          {models
            .sort((a, b) => b.performance.tokensPerSecond - a.performance.tokensPerSecond)
            .map((model) => (
              <div key={model.id} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span>{model.name}</span>
                  <span className="font-semibold">{model.performance.tokensPerSecond.toFixed(1)}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="h-2 rounded-full transition-all duration-300"
                    style={{ 
                      width: `${model.performance.tokensPerSecond}%`,
                      backgroundColor: model.color 
                    }}
                  />
                </div>
              </div>
            ))}
        </div>
      </div>

      {/* Usage Distribution */}
      <div className="bg-white rounded-lg border shadow-sm p-4">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 className="h-4 w-4" />
          <h3 className="text-sm font-semibold">Usage Distribution</h3>
        </div>
        <div className="space-y-3">
          {models
            .sort((a, b) => b.performance.totalRequests - a.performance.totalRequests)
            .map((model) => {
              const maxRequests = Math.max(...models.map(m => m.performance.totalRequests));
              const percentage = (model.performance.totalRequests / maxRequests) * 100;
              
              return (
                <div key={model.id} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span>{model.name}</span>
                    <span className="font-semibold">{model.performance.totalRequests}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="h-2 rounded-full transition-all duration-300"
                      style={{ 
                        width: `${percentage}%`,
                        backgroundColor: model.color 
                      }}
                    />
                  </div>
                </div>
              );
            })}
        </div>
      </div>

      {/* Confidence Scores */}
      <div className="bg-white rounded-lg border shadow-sm p-4">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="h-4 w-4" />
          <h3 className="text-sm font-semibold">Confidence Scores</h3>
        </div>
        <div className="space-y-3">
          {models
            .sort((a, b) => b.performance.avgConfidence - a.performance.avgConfidence)
            .map((model) => (
              <div key={model.id} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span>{model.name}</span>
                  <span className="font-semibold">{(model.performance.avgConfidence * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="h-2 rounded-full transition-all duration-300"
                    style={{ 
                      width: `${model.performance.avgConfidence * 100}%`,
                      backgroundColor: model.color 
                    }}
                  />
                </div>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
};

// =============================================================================
// SYSTEM OVERVIEW COMPONENT
// =============================================================================

const SystemOverview = ({ metrics }) => {
  return (
    <div className="grid grid-cols-4 gap-4">
      <div className="bg-white rounded-lg border shadow-sm p-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold text-green-600">{metrics.activeModels}</div>
            <div className="text-sm text-gray-500">Active Models</div>
          </div>
          <Brain className="h-8 w-8 text-green-600" />
        </div>
      </div>

      <div className="bg-white rounded-lg border shadow-sm p-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold text-blue-600">{metrics.totalStorage}</div>
            <div className="text-sm text-gray-500">Total Storage</div>
          </div>
          <HardDrive className="h-8 w-8 text-blue-600" />
        </div>
      </div>

      <div className="bg-white rounded-lg border shadow-sm p-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold text-purple-600">{metrics.combinedTokensPerSecond.toFixed(0)}</div>
            <div className="text-sm text-gray-500">Combined T/s</div>
          </div>
          <Gauge className="h-8 w-8 text-purple-600" />
        </div>
      </div>

      <div className="bg-white rounded-lg border shadow-sm p-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold text-green-600">${metrics.costSavings.toFixed(0)}</div>
            <div className="text-sm text-gray-500">Monthly Savings</div>
          </div>
          <DollarSign className="h-8 w-8 text-green-600" />
        </div>
      </div>
    </div>
  );
};

// =============================================================================
// MAIN LOCAL MODEL MANAGER COMPONENT
// =============================================================================

const LocalModelManager = ({
  models = sampleModels,
  onModelStart = () => {},
  onModelStop = () => {},
  onModelRemove = () => {},
  onModelDownload = () => {},
  onModelConfigure = () => {},
  onRefresh = () => {}
}) => {
  const [selectedModel, setSelectedModel] = useState(null);
  const [configDialog, setConfigDialog] = useState(false);
  const [activeTab, setActiveTab] = useState('models');

  const activeModels = models.filter(m => m.status === 'active');
  const totalRequests = models.reduce((sum, m) => sum + m.performance.totalRequests, 0);
  const avgConfidence = models.reduce((sum, m) => sum + m.performance.avgConfidence, 0) / models.length;

  // Calculate actual metrics from models
  const calculatedMetrics = {
    totalModels: models.length,
    activeModels: activeModels.length,
    totalStorage: models.reduce((sum, m) => sum + parseFloat(m.size), 0).toFixed(1) + ' GB',
    totalRAMUsage: models.reduce((sum, m) => sum + parseFloat(m.ramUsage.replace('~', '').replace(' GB', '')), 0).toFixed(1) + ' GB',
    combinedTokensPerSecond: activeModels.reduce((sum, m) => sum + m.performance.tokensPerSecond, 0),
    totalRequests,
    avgConfidence,
    costSavings: totalRequests * 0.03 // Assuming $0.03 per request saved vs API
  };

  return (
    <div className="h-full flex flex-col space-y-6 p-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Local Model Manager</h2>
          <p className="text-gray-500">
            Manage your 5 local LLM models • Zero cost, maximum privacy
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <button 
            className="px-3 py-2 border rounded-md hover:bg-gray-50 flex items-center gap-2"
            onClick={onRefresh}
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
          <button className="px-3 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 flex items-center gap-2">
            <Download className="h-4 w-4" />
            Add Model
          </button>
        </div>
      </div>

      {/* System Overview */}
      <SystemOverview metrics={calculatedMetrics} />

      {/* Main Content Tabs */}
      <div className="flex-1">
        <div className="flex border-b mb-6">
          <button 
            className={`px-4 py-2 border-b-2 ${activeTab === 'models' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500'}`}
            onClick={() => setActiveTab('models')}
          >
            Models
          </button>
          <button 
            className={`px-4 py-2 border-b-2 ${activeTab === 'performance' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500'}`}
            onClick={() => setActiveTab('performance')}
          >
            Performance
          </button>
          <button 
            className={`px-4 py-2 border-b-2 ${activeTab === 'settings' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500'}`}
            onClick={() => setActiveTab('settings')}
          >
            Settings
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'models' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {models.map((model) => (
              <ModelCard
                key={model.id}
                model={model}
                onStart={() => onModelStart(model.id)}
                onStop={() => onModelStop(model.id)}
                onConfigure={() => {
                  setSelectedModel(model.id);
                  setConfigDialog(true);
                }}
                onRemove={() => onModelRemove(model.id)}
              />
            ))}
          </div>
        )}

        {activeTab === 'performance' && (
          <PerformanceCharts models={models} />
        )}

        {activeTab === 'settings' && (
          <div className="bg-white rounded-lg border shadow-sm p-6">
            <h3 className="text-lg font-semibold mb-2">Global Settings</h3>
            <p className="text-gray-500 mb-6">Configure global behavior for all local models</p>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">Auto-start models on system boot</div>
                  <div className="text-sm text-gray-500">
                    Automatically start all models when UltraMCP launches
                  </div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">Privacy-first mode</div>
                  <div className="text-sm text-gray-500">
                    Prefer local models over API models in hybrid scenarios
                  </div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" defaultChecked />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">Performance monitoring</div>
                  <div className="text-sm text-gray-500">
                    Collect detailed performance and usage metrics
                  </div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" defaultChecked />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Configuration Dialog */}
      {configDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-2">Configure Model</h3>
            <p className="text-gray-500 mb-4">Adjust settings for the selected model</p>
            
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium block mb-2">Temperature</label>
                <input type="range" min="0" max="1" step="0.1" defaultValue="0.7" className="w-full" />
              </div>
              
              <div>
                <label className="text-sm font-medium block mb-2">Max Tokens</label>
                <input type="range" min="100" max="8000" step="100" defaultValue="2000" className="w-full" />
              </div>
              
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium">Privacy Mode</label>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" defaultChecked />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>
              
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium">Auto Start</label>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>
            </div>
            
            <div className="flex justify-end gap-2 mt-6">
              <button 
                className="px-4 py-2 border rounded-md hover:bg-gray-50"
                onClick={() => setConfigDialog(false)}
              >
                Cancel
              </button>
              <button 
                className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
                onClick={() => setConfigDialog(false)}
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LocalModelManager;