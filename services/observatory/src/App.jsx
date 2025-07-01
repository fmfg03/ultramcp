import React, { useState, useEffect } from 'react';
import './App.css';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Button } from './components/ui/button';
import { Progress } from './components/ui/progress';
import { 
  Activity, 
  Cpu, 
  Database, 
  Zap, 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Clock,
  DollarSign,
  Brain,
  Target,
  TrendingUp,
  TrendingDown,
  Pause,
  Play,
  RotateCcw,
  Settings,
  Terminal,
  Eye,
  Gauge
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, AreaChart, Area, BarChart, Bar } from 'recharts';

// Mock data generator
const generateMockData = () => {
  const agents = ['Manus', 'Sam', 'Perplexity', 'LangGraph'];
  const models = ['qwen2.5:14b', 'qwen2.5-coder:7b', 'deepseek-coder:6.7b', 'gpt-4o-mini', 'claude-3-haiku'];
  const taskTypes = ['coding', 'research', 'analysis', 'creative', 'reasoning'];
  
  return {
    timestamp: new Date().toISOString(),
    agent: agents[Math.floor(Math.random() * agents.length)],
    model: models[Math.floor(Math.random() * models.length)],
    taskType: taskTypes[Math.floor(Math.random() * taskTypes.length)],
    executionTime: Math.random() * 30 + 1,
    cost: Math.random() * 0.05,
    confidence: Math.random() * 0.4 + 0.6,
    success: Math.random() > 0.15,
    memoryUsage: Math.random() * 200 + 50,
    cpuUsage: Math.random() * 80 + 10
  };
};

const generatePerformanceData = () => {
  return Array.from({ length: 20 }, (_, i) => ({
    time: new Date(Date.now() - (19 - i) * 60000).toLocaleTimeString(),
    executions: Math.floor(Math.random() * 10) + 1,
    avgTime: Math.random() * 20 + 5,
    successRate: Math.random() * 30 + 70,
    cost: Math.random() * 0.1
  }));
};

function App() {
  const [isMonitoring, setIsMonitoring] = useState(true);
  const [currentExecution, setCurrentExecution] = useState(null);
  const [recentExecutions, setRecentExecutions] = useState([]);
  const [performanceData, setPerformanceData] = useState(generatePerformanceData());
  const [systemStats, setSystemStats] = useState({
    totalExecutions: 1247,
    successRate: 87.3,
    avgExecutionTime: 12.4,
    totalCost: 23.67,
    activeAgents: 3,
    modelsOnline: 5
  });
  const [terminalLogs, setTerminalLogs] = useState([
    { time: '14:32:01', level: 'INFO', message: 'MCP Observatory initialized' },
    { time: '14:32:02', level: 'SUCCESS', message: 'Connected to orchestration server' },
    { time: '14:32:03', level: 'INFO', message: 'Monitoring 5 models across 3 agents' }
  ]);

  // Simulate real-time updates
  useEffect(() => {
    if (!isMonitoring) return;

    const interval = setInterval(() => {
      const newExecution = generateMockData();
      setCurrentExecution(newExecution);
      
      setRecentExecutions(prev => [newExecution, ...prev.slice(0, 9)]);
      
      // Update terminal logs
      const logLevel = newExecution.success ? 'SUCCESS' : 'ERROR';
      const logMessage = `${newExecution.agent} executed ${newExecution.taskType} task using ${newExecution.model} - ${newExecution.success ? 'SUCCESS' : 'FAILED'} (${newExecution.executionTime.toFixed(1)}s)`;
      
      setTerminalLogs(prev => [
        { time: new Date().toLocaleTimeString(), level: logLevel, message: logMessage },
        ...prev.slice(0, 19)
      ]);

      // Update system stats
      setSystemStats(prev => ({
        ...prev,
        totalExecutions: prev.totalExecutions + 1,
        successRate: Math.random() * 10 + 80,
        avgExecutionTime: Math.random() * 5 + 10,
        totalCost: prev.totalCost + newExecution.cost
      }));

      // Update performance data
      if (Math.random() > 0.7) {
        setPerformanceData(prev => [
          ...prev.slice(1),
          {
            time: new Date().toLocaleTimeString(),
            executions: Math.floor(Math.random() * 10) + 1,
            avgTime: Math.random() * 20 + 5,
            successRate: Math.random() * 30 + 70,
            cost: Math.random() * 0.1
          }
        ]);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [isMonitoring]);

  const getStatusColor = (success) => {
    return success ? 'status-online' : 'status-error';
  };

  const getModelStatusColor = (model) => {
    if (model.includes('qwen') || model.includes('deepseek')) return 'status-online';
    if (model.includes('gpt') || model.includes('claude')) return 'status-warning';
    return 'status-info';
  };

  return (
    <div className="min-h-screen bg-background text-foreground nuclear-grid">
      {/* Header */}
      <div className="nuclear-terminal p-4 border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Eye className="w-8 h-8 nuclear-glow text-primary" />
              <h1 className="text-2xl font-bold nuclear-glow">MCP OBSERVATORY</h1>
            </div>
            <Badge className="nuclear-critical">NUCLEAR CONTROL</Badge>
            <Badge className={`${isMonitoring ? 'status-online' : 'status-offline'}`}>
              {isMonitoring ? 'MONITORING ACTIVE' : 'MONITORING PAUSED'}
            </Badge>
          </div>
          
          <div className="flex items-center space-x-2">
            <Button
              onClick={() => setIsMonitoring(!isMonitoring)}
              className="nuclear-button"
              size="sm"
            >
              {isMonitoring ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              {isMonitoring ? 'PAUSE' : 'RESUME'}
            </Button>
            <Button className="nuclear-button" size="sm">
              <RotateCcw className="w-4 h-4" />
              RESET
            </Button>
            <Button className="nuclear-button" size="sm">
              <Settings className="w-4 h-4" />
              CONFIG
            </Button>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* System Status Cards */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <Card className="metric-card">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">TOTAL EXEC</p>
                  <p className="metric-value text-lg nuclear-glow">{systemStats.totalExecutions}</p>
                </div>
                <Activity className="w-6 h-6 text-primary" />
              </div>
            </CardContent>
          </Card>

          <Card className="metric-card">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">SUCCESS RATE</p>
                  <p className={`metric-value text-lg ${systemStats.successRate > 85 ? 'status-online' : systemStats.successRate > 70 ? 'status-warning' : 'status-error'}`}>
                    {systemStats.successRate.toFixed(1)}%
                  </p>
                </div>
                <Target className="w-6 h-6 text-primary" />
              </div>
            </CardContent>
          </Card>

          <Card className="metric-card">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">AVG TIME</p>
                  <p className="metric-value text-lg nuclear-glow">{systemStats.avgExecutionTime.toFixed(1)}s</p>
                </div>
                <Clock className="w-6 h-6 text-primary" />
              </div>
            </CardContent>
          </Card>

          <Card className="metric-card">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">TOTAL COST</p>
                  <p className="metric-value text-lg nuclear-warning">${systemStats.totalCost.toFixed(2)}</p>
                </div>
                <DollarSign className="w-6 h-6 text-primary" />
              </div>
            </CardContent>
          </Card>

          <Card className="metric-card">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">AGENTS</p>
                  <p className="metric-value text-lg status-online">{systemStats.activeAgents}</p>
                </div>
                <Brain className="w-6 h-6 text-primary" />
              </div>
            </CardContent>
          </Card>

          <Card className="metric-card">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">MODELS</p>
                  <p className="metric-value text-lg status-online">{systemStats.modelsOnline}</p>
                </div>
                <Database className="w-6 h-6 text-primary" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Current Execution */}
        {currentExecution && (
          <Card className="nuclear-terminal nuclear-pulse">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Zap className="w-5 h-5 nuclear-blink" />
                <span>CURRENT EXECUTION</span>
                <Badge className={getStatusColor(currentExecution.success)}>
                  {currentExecution.success ? 'SUCCESS' : 'FAILED'}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-xs text-muted-foreground">AGENT</p>
                  <p className="font-bold nuclear-glow">{currentExecution.agent}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">MODEL</p>
                  <p className={`font-bold ${getModelStatusColor(currentExecution.model)}`}>
                    {currentExecution.model}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">TASK TYPE</p>
                  <p className="font-bold text-accent">{currentExecution.taskType.toUpperCase()}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">EXECUTION TIME</p>
                  <p className="font-bold nuclear-glow">{currentExecution.executionTime.toFixed(2)}s</p>
                </div>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-xs text-muted-foreground">CONFIDENCE</p>
                  <div className="flex items-center space-x-2">
                    <Progress value={currentExecution.confidence * 100} className="flex-1" />
                    <span className="text-sm font-bold">{(currentExecution.confidence * 100).toFixed(0)}%</span>
                  </div>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">COST</p>
                  <p className="font-bold nuclear-warning">${currentExecution.cost.toFixed(4)}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">MEMORY</p>
                  <p className="font-bold">{currentExecution.memoryUsage.toFixed(0)}MB</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">CPU</p>
                  <p className="font-bold">{currentExecution.cpuUsage.toFixed(0)}%</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Performance Chart */}
          <Card className="nuclear-terminal">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <TrendingUp className="w-5 h-5" />
                <span>PERFORMANCE METRICS</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333333" />
                  <XAxis dataKey="time" stroke="#00ff00" fontSize={10} />
                  <YAxis stroke="#00ff00" fontSize={10} />
                  <Area 
                    type="monotone" 
                    dataKey="successRate" 
                    stroke="#00ff00" 
                    fill="rgba(0, 255, 0, 0.1)" 
                    strokeWidth={2}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="avgTime" 
                    stroke="#ffff00" 
                    fill="rgba(255, 255, 0, 0.1)" 
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Recent Executions */}
          <Card className="nuclear-terminal">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Activity className="w-5 h-5" />
                <span>RECENT EXECUTIONS</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-80 overflow-y-auto">
                {recentExecutions.map((exec, index) => (
                  <div key={index} className="flex items-center justify-between p-2 nuclear-border rounded">
                    <div className="flex items-center space-x-3">
                      {exec.success ? 
                        <CheckCircle className="w-4 h-4 status-online" /> : 
                        <XCircle className="w-4 h-4 status-error" />
                      }
                      <div>
                        <p className="text-sm font-bold">{exec.agent}</p>
                        <p className="text-xs text-muted-foreground">{exec.taskType}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-bold">{exec.executionTime.toFixed(1)}s</p>
                      <p className="text-xs text-muted-foreground">{exec.model}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Terminal Logs */}
        <Card className="nuclear-terminal">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Terminal className="w-5 h-5" />
              <span>SYSTEM LOGS</span>
              <Badge className="nuclear-scan">LIVE</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="terminal-output">
              {terminalLogs.map((log, index) => (
                <div key={index} className="terminal-line">
                  <span className="terminal-prompt">[{log.time}]</span>
                  <span className={`ml-2 ${
                    log.level === 'ERROR' ? 'terminal-error' :
                    log.level === 'SUCCESS' ? 'terminal-success' :
                    log.level === 'INFO' ? 'terminal-info' : ''
                  }`}>
                    [{log.level}]
                  </span>
                  <span className="ml-2">{log.message}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Model Status Grid */}
        <Card className="nuclear-terminal">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Gauge className="w-5 h-5" />
              <span>MODEL STATUS MATRIX</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[
                { name: 'qwen2.5:14b', status: 'online', load: 78, cost: 0.00 },
                { name: 'qwen2.5-coder:7b', status: 'online', load: 45, cost: 0.00 },
                { name: 'deepseek-coder:6.7b', status: 'online', load: 23, cost: 0.00 },
                { name: 'gpt-4o-mini', status: 'standby', load: 12, cost: 0.02 },
                { name: 'claude-3-haiku', status: 'standby', load: 8, cost: 0.03 }
              ].map((model, index) => (
                <div key={index} className="nuclear-border p-3 rounded">
                  <div className="flex items-center justify-between mb-2">
                    <p className="font-bold text-sm">{model.name}</p>
                    <Badge className={
                      model.status === 'online' ? 'status-online' :
                      model.status === 'standby' ? 'status-warning' : 'status-error'
                    }>
                      {model.status.toUpperCase()}
                    </Badge>
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span>Load:</span>
                      <span>{model.load}%</span>
                    </div>
                    <Progress value={model.load} className="h-1" />
                    <div className="flex justify-between text-xs">
                      <span>Cost/1K:</span>
                      <span className={model.cost === 0 ? 'status-online' : 'nuclear-warning'}>
                        ${model.cost.toFixed(3)}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default App;

