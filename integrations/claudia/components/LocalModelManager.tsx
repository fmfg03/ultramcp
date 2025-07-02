/**
 * LocalModelManager Component
 * 
 * Comprehensive management interface for UltraMCP's 5 local LLM models
 * Features: Performance monitoring, usage analytics, model selection, cost tracking
 */

import React, { useState, useEffect } from 'react';
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
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  Switch,
  Slider,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui';
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
// TYPES
// =============================================================================

interface LocalModel {
  id: string;
  name: string;
  version: string;
  size: string; // "9.0 GB"
  ramUsage: string; // "~12 GB"
  contextLength: number; // 32000
  specialization: string;
  role: string;
  status: 'active' | 'idle' | 'loading' | 'error' | 'stopped';
  performance: {
    avgResponseTime: number; // seconds
    tokensPerSecond: number;
    totalRequests: number;
    avgConfidence: number;
    uptime: number; // percentage
    lastUsed: Date;
  };
  capabilities: string[];
  costPerToken: number; // $0.00 for local models
  privacyScore: number; // 100 for local models
  color: string;
  icon: string;
}

interface ModelMetrics {
  totalModels: number;
  activeModels: number;
  totalStorage: string;
  totalRAMUsage: string;
  combinedTokensPerSecond: number;
  totalRequests: number;
  avgConfidence: number;
  costSavings: number; // vs API models
}

interface LocalModelManagerProps {
  models: LocalModel[];
  metrics: ModelMetrics;
  onModelStart: (modelId: string) => void;
  onModelStop: (modelId: string) => void;
  onModelRemove: (modelId: string) => void;
  onModelDownload: (modelName: string) => void;
  onModelConfigure: (modelId: string, config: ModelConfig) => void;
  onRefresh: () => void;
}

interface ModelConfig {
  temperature: number;
  maxTokens: number;
  systemPrompt: string;
  rateLimitPerHour: number;
  privacyMode: boolean;
  autoStart: boolean;
}

// =============================================================================
// SAMPLE DATA
// =============================================================================

const sampleModels: LocalModel[] = [
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

const ModelCard: React.FC<{ 
  model: LocalModel; 
  onStart: () => void; 
  onStop: () => void; 
  onConfigure: () => void; 
  onRemove: () => void;
}> = ({ model, onStart, onStop, onConfigure, onRemove }) => {
  const [showDetails, setShowDetails] = useState(false);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-500';
      case 'idle': return 'text-yellow-500';
      case 'loading': return 'text-blue-500';
      case 'error': return 'text-red-500';
      case 'stopped': return 'text-gray-500';
      default: return 'text-gray-500';
    }
  };

  const getStatusIcon = (status: string) => {
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
    <Card className="h-full transition-all duration-200 hover:shadow-md">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div 
              className="w-10 h-10 rounded-lg flex items-center justify-center text-lg"
              style={{ backgroundColor: `${model.color}20`, color: model.color }}
            >
              {model.icon}
            </div>
            <div>
              <CardTitle className="text-base">{model.name}</CardTitle>
              <CardDescription className="text-sm">{model.role}</CardDescription>
            </div>
          </div>
          
          <div className={`flex items-center gap-1 ${getStatusColor(model.status)}`}>
            {getStatusIcon(model.status)}
            <Badge 
              variant={model.status === 'active' ? 'default' : 'secondary'}
              className="capitalize"
            >
              {model.status}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Key Metrics */}
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <div className="text-muted-foreground">Response Time</div>
            <div className="font-semibold">{model.performance.avgResponseTime.toFixed(1)}s</div>
          </div>
          <div>
            <div className="text-muted-foreground">Tokens/sec</div>
            <div className="font-semibold">{model.performance.tokensPerSecond.toFixed(1)}</div>
          </div>
          <div>
            <div className="text-muted-foreground">Requests</div>
            <div className="font-semibold">{model.performance.totalRequests}</div>
          </div>
          <div>
            <div className="text-muted-foreground">Confidence</div>
            <div className="font-semibold">{(model.performance.avgConfidence * 100).toFixed(0)}%</div>
          </div>
        </div>

        {/* Storage & Memory */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Storage:</span>
            <span className="font-semibold">{model.size}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">RAM Usage:</span>
            <span className="font-semibold">{model.ramUsage}</span>
          </div>
        </div>

        {/* Uptime Progress */}
        <div className="space-y-1">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Uptime</span>
            <span className="font-semibold">{model.performance.uptime.toFixed(1)}%</span>
          </div>
          <Progress value={model.performance.uptime} className="h-1" />
        </div>

        {/* Capabilities */}
        {showDetails && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-3"
          >
            <Separator />
            <div>
              <div className="text-sm text-muted-foreground mb-2">Specialization</div>
              <div className="text-sm">{model.specialization}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground mb-2">Capabilities</div>
              <div className="flex flex-wrap gap-1">
                {model.capabilities.map((capability, index) => (
                  <Badge key={index} variant="outline" className="text-xs">
                    {capability}
                  </Badge>
                ))}
              </div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground mb-1">Last Used</div>
              <div className="text-sm">{model.performance.lastUsed.toLocaleString()}</div>
            </div>
          </motion.div>
        )}

        {/* Actions */}
        <div className="flex flex-wrap gap-2 pt-2">
          {model.status === 'active' ? (
            <Button size="sm" variant="outline" onClick={onStop}>
              <StopCircle className="h-3 w-3 mr-1" />
              Stop
            </Button>
          ) : (
            <Button size="sm" onClick={onStart}>
              <PlayCircle className="h-3 w-3 mr-1" />
              Start
            </Button>
          )}
          
          <Button size="sm" variant="outline" onClick={onConfigure}>
            <Settings className="h-3 w-3 mr-1" />
            Config
          </Button>
          
          <Button 
            size="sm" 
            variant="ghost" 
            onClick={() => setShowDetails(!showDetails)}
          >
            <ChevronRight className={`h-3 w-3 transition-transform ${showDetails ? 'rotate-90' : ''}`} />
            {showDetails ? 'Less' : 'More'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

// =============================================================================
// PERFORMANCE CHARTS COMPONENT
// =============================================================================

const PerformanceCharts: React.FC<{ models: LocalModel[] }> = ({ models }) => {
  return (
    <div className="grid grid-cols-2 gap-4">
      {/* Response Time Comparison */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Response Time Comparison
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {models.map((model) => (
              <div key={model.id} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span>{model.name}</span>
                  <span className="font-semibold">{model.performance.avgResponseTime.toFixed(1)}s</span>
                </div>
                <Progress 
                  value={(1 / model.performance.avgResponseTime) * 100} 
                  className="h-2"
                  style={{ 
                    backgroundColor: `${model.color}20`,
                  }}
                />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Throughput Comparison */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2">
            <Zap className="h-4 w-4" />
            Throughput (Tokens/sec)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {models
              .sort((a, b) => b.performance.tokensPerSecond - a.performance.tokensPerSecond)
              .map((model) => (
                <div key={model.id} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span>{model.name}</span>
                    <span className="font-semibold">{model.performance.tokensPerSecond.toFixed(1)}</span>
                  </div>
                  <Progress 
                    value={model.performance.tokensPerSecond} 
                    className="h-2"
                    style={{ 
                      backgroundColor: `${model.color}20`,
                    }}
                  />
                </div>
              ))}
          </div>
        </CardContent>
      </Card>

      {/* Usage Distribution */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Usage Distribution
          </CardTitle>
        </CardHeader>
        <CardContent>
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
                    <Progress 
                      value={percentage} 
                      className="h-2"
                      style={{ 
                        backgroundColor: `${model.color}20`,
                      }}
                    />
                  </div>
                );
              })}
          </div>
        </CardContent>
      </Card>

      {/* Confidence Scores */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Confidence Scores
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {models
              .sort((a, b) => b.performance.avgConfidence - a.performance.avgConfidence)
              .map((model) => (
                <div key={model.id} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span>{model.name}</span>
                    <span className="font-semibold">{(model.performance.avgConfidence * 100).toFixed(1)}%</span>
                  </div>
                  <Progress 
                    value={model.performance.avgConfidence * 100} 
                    className="h-2"
                    style={{ 
                      backgroundColor: `${model.color}20`,
                    }}
                  />
                </div>
              ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// =============================================================================
// SYSTEM OVERVIEW COMPONENT
// =============================================================================

const SystemOverview: React.FC<{ metrics: ModelMetrics }> = ({ metrics }) => {
  return (
    <div className="grid grid-cols-4 gap-4">
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-green-600">{metrics.activeModels}</div>
              <div className="text-sm text-muted-foreground">Active Models</div>
            </div>
            <Brain className="h-8 w-8 text-green-600" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-blue-600">{metrics.totalStorage}</div>
              <div className="text-sm text-muted-foreground">Total Storage</div>
            </div>
            <HardDrive className="h-8 w-8 text-blue-600" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-purple-600">{metrics.combinedTokensPerSecond.toFixed(0)}</div>
              <div className="text-sm text-muted-foreground">Combined T/s</div>
            </div>
            <Gauge className="h-8 w-8 text-purple-600" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-green-600">${metrics.costSavings.toFixed(0)}</div>
              <div className="text-sm text-muted-foreground">Monthly Savings</div>
            </div>
            <DollarSign className="h-8 w-8 text-green-600" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// =============================================================================
// MAIN LOCAL MODEL MANAGER COMPONENT
// =============================================================================

const LocalModelManager: React.FC<LocalModelManagerProps> = ({
  models = sampleModels,
  metrics,
  onModelStart,
  onModelStop,
  onModelRemove,
  onModelDownload,
  onModelConfigure,
  onRefresh
}) => {
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [configDialog, setConfigDialog] = useState(false);

  const activeModels = models.filter(m => m.status === 'active');
  const totalRequests = models.reduce((sum, m) => sum + m.performance.totalRequests, 0);
  const avgConfidence = models.reduce((sum, m) => sum + m.performance.avgConfidence, 0) / models.length;

  // Calculate actual metrics from models
  const calculatedMetrics: ModelMetrics = {
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
    <div className="h-full flex flex-col space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Local Model Manager</h2>
          <p className="text-muted-foreground">
            Manage your 5 local LLM models • Zero cost, maximum privacy
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={onRefresh}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button>
            <Download className="h-4 w-4 mr-2" />
            Add Model
          </Button>
        </div>
      </div>

      {/* System Overview */}
      <SystemOverview metrics={calculatedMetrics} />

      {/* Main Content */}
      <Tabs defaultValue="models" className="flex-1">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="models">Models</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="models" className="space-y-4">
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
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <PerformanceCharts models={models} />
        </TabsContent>

        <TabsContent value="settings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Global Settings</CardTitle>
              <CardDescription>
                Configure global behavior for all local models
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">Auto-start models on system boot</div>
                  <div className="text-sm text-muted-foreground">
                    Automatically start all models when UltraMCP launches
                  </div>
                </div>
                <Switch />
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">Privacy-first mode</div>
                  <div className="text-sm text-muted-foreground">
                    Prefer local models over API models in hybrid scenarios
                  </div>
                </div>
                <Switch defaultChecked />
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">Performance monitoring</div>
                  <div className="text-sm text-muted-foreground">
                    Collect detailed performance and usage metrics
                  </div>
                </div>
                <Switch defaultChecked />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Configuration Dialog */}
      <Dialog open={configDialog} onOpenChange={setConfigDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Configure Model</DialogTitle>
            <DialogDescription>
              Adjust settings for the selected model
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Temperature</label>
              <Slider defaultValue={[0.7]} max={1} min={0} step={0.1} className="mt-2" />
            </div>
            
            <div>
              <label className="text-sm font-medium">Max Tokens</label>
              <Slider defaultValue={[2000]} max={8000} min={100} step={100} className="mt-2" />
            </div>
            
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Privacy Mode</label>
              <Switch defaultChecked />
            </div>
            
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Auto Start</label>
              <Switch />
            </div>
          </div>
          
          <div className="flex justify-end gap-2 mt-6">
            <Button variant="outline" onClick={() => setConfigDialog(false)}>
              Cancel
            </Button>
            <Button onClick={() => setConfigDialog(false)}>
              Save Changes
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default LocalModelManager;