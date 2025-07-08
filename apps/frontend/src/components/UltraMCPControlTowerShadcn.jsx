import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Progress } from './ui/progress';
import { Alert, AlertDescription } from './ui/alert';
import { Input } from './ui/input';
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Cpu, 
  Database, 
  DollarSign, 
  Eye, 
  EyeOff, 
  MessageSquare, 
  Pause, 
  Play, 
  RefreshCw, 
  Shield, 
  Square, 
  Users, 
  Zap,
  TrendingUp,
  Brain,
  Settings,
  BarChart3
} from 'lucide-react';

const UltraMCPControlTowerShadcn = () => {
  const [connected, setConnected] = useState(false);
  const [systemStatus, setSystemStatus] = useState('idle');
  const [activeView, setActiveView] = useState('overview');
  
  // System metrics
  const [metrics, setMetrics] = useState({
    localModelsActive: 5,
    apiModelsActive: 3,
    totalCost: 0.0,
    privacyScore: 100,
    avgConfidence: 0.85,
    activeDebates: 2,
    totalRequests: 1247
  });

  // Local models data
  const [localModels] = useState([
    { name: 'Qwen 2.5 14B', status: 'active', confidence: 0.92, role: 'Strategic Analyst', requests: 147 },
    { name: 'Llama 3.1 8B', status: 'active', confidence: 0.88, role: 'Balanced Reasoner', requests: 203 },
    { name: 'Qwen Coder 7B', status: 'active', confidence: 0.95, role: 'Technical Specialist', requests: 89 },
    { name: 'Mistral 7B', status: 'active', confidence: 0.83, role: 'Rapid Analyst', requests: 312 },
    { name: 'DeepSeek Coder 6.7B', status: 'active', confidence: 0.91, role: 'System Architect', requests: 156 }
  ]);

  // Active debates
  const [activeDebates] = useState([
    {
      id: 'debate-1',
      topic: 'Microservices vs Monolith Architecture',
      participants: ['Qwen 2.5 14B', 'Llama 3.1 8B', 'Mistral 7B'],
      status: 'active',
      round: 2,
      confidence: 0.89,
      startTime: new Date(Date.now() - 15 * 60 * 1000)
    },
    {
      id: 'debate-2', 
      topic: 'React vs Vue for Frontend Framework',
      participants: ['Qwen Coder 7B', 'DeepSeek Coder 6.7B'],
      status: 'paused',
      round: 1,
      confidence: 0.76,
      startTime: new Date(Date.now() - 8 * 60 * 1000)
    }
  ]);

  // Live events
  const [liveEvents, setLiveEvents] = useState([
    { id: 1, time: new Date(), type: 'debate_started', message: 'New debate: Microservices vs Monolith', level: 'info' },
    { id: 2, time: new Date(Date.now() - 2 * 60 * 1000), type: 'model_response', message: 'Qwen 2.5 14B: Strategic analysis complete', level: 'success' },
    { id: 3, time: new Date(Date.now() - 5 * 60 * 1000), type: 'consensus_reached', message: 'Debate consensus: 87% confidence', level: 'success' }
  ]);

  // Check connection status
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const response = await fetch('/api/health');
        if (response.ok) {
          setConnected(true);
          setSystemStatus('operational');
        }
      } catch (error) {
        setConnected(false);
        setSystemStatus('disconnected');
      }
    };

    checkConnection();
    const interval = setInterval(checkConnection, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'paused': return 'bg-yellow-100 text-yellow-800';
      case 'stopped': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active': return <Play className="h-3 w-3" />;
      case 'paused': return <Pause className="h-3 w-3" />;
      case 'stopped': return <Square className="h-3 w-3" />;
      default: return <Clock className="h-3 w-3" />;
    }
  };

  const formatDuration = (startTime) => {
    const duration = Math.floor((Date.now() - startTime) / 1000 / 60);
    return `${duration}m`;
  };

  return (
    <div className="space-y-6">
      {/* System Status Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                UltraMCP Control Tower
              </CardTitle>
              <CardDescription>
                Real-time system monitoring and debate orchestration
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={connected ? "default" : "destructive"}>
                {connected ? "Connected" : "Disconnected"}
              </Badge>
              <Button variant="outline" size="sm">
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* System Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Local Models</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.localModelsActive}</div>
            <p className="text-xs text-muted-foreground">Active and ready</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Debates</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.activeDebates}</div>
            <p className="text-xs text-muted-foreground">Running discussions</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Privacy Score</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{metrics.privacyScore}%</div>
            <p className="text-xs text-muted-foreground">Local processing</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">${metrics.totalCost.toFixed(2)}</div>
            <p className="text-xs text-muted-foreground">Current session</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeView} onValueChange={setActiveView} className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="models">Local Models</TabsTrigger>
          <TabsTrigger value="debates">Active Debates</TabsTrigger>
          <TabsTrigger value="events">Live Events</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* System Health */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  System Health
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>System Load</span>
                    <span>23%</span>
                  </div>
                  <Progress value={23} />
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Memory Usage</span>
                    <span>67%</span>
                  </div>
                  <Progress value={67} />
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>API Rate Limits</span>
                    <span>12%</span>
                  </div>
                  <Progress value={12} />
                </div>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="h-5 w-5" />
                  Quick Actions
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button className="w-full justify-start">
                  <Play className="h-4 w-4 mr-2" />
                  Start New Debate
                </Button>
                <Button variant="outline" className="w-full justify-start">
                  <Users className="h-4 w-4 mr-2" />
                  Model Performance Review
                </Button>
                <Button variant="outline" className="w-full justify-start">
                  <BarChart3 className="h-4 w-4 mr-2" />
                  Generate Analytics Report
                </Button>
                <Button variant="outline" className="w-full justify-start">
                  <Settings className="h-4 w-4 mr-2" />
                  System Configuration
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Local Models Tab */}
        <TabsContent value="models" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {localModels.map((model, index) => (
              <Card key={index}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{model.name}</CardTitle>
                    <Badge className={getStatusColor(model.status)}>
                      {getStatusIcon(model.status)}
                      <span className="ml-1">{model.status}</span>
                    </Badge>
                  </div>
                  <CardDescription>{model.role}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span>Confidence</span>
                        <span>{(model.confidence * 100).toFixed(0)}%</span>
                      </div>
                      <Progress value={model.confidence * 100} />
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Total Requests</span>
                      <span className="font-medium">{model.requests}</span>
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline" className="flex-1">
                        <Settings className="h-3 w-3 mr-1" />
                        Configure
                      </Button>
                      <Button size="sm" variant="outline">
                        <Eye className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Active Debates Tab */}
        <TabsContent value="debates" className="space-y-4">
          <div className="space-y-4">
            {activeDebates.map((debate) => (
              <Card key={debate.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-lg">{debate.topic}</CardTitle>
                      <CardDescription>
                        Round {debate.round} • Started {formatDuration(debate.startTime)} ago
                      </CardDescription>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge className={getStatusColor(debate.status)}>
                        {getStatusIcon(debate.status)}
                        <span className="ml-1">{debate.status}</span>
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Consensus Confidence</span>
                        <span>{(debate.confidence * 100).toFixed(0)}%</span>
                      </div>
                      <Progress value={debate.confidence * 100} />
                    </div>
                    
                    <div>
                      <div className="text-sm font-medium mb-2">Participants</div>
                      <div className="flex flex-wrap gap-1">
                        {debate.participants.map((participant, idx) => (
                          <Badge key={idx} variant="outline">
                            <Brain className="h-3 w-3 mr-1" />
                            {participant}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <Button size="sm" variant={debate.status === 'active' ? "destructive" : "default"}>
                        {debate.status === 'active' ? (
                          <>
                            <Pause className="h-3 w-3 mr-1" />
                            Pause
                          </>
                        ) : (
                          <>
                            <Play className="h-3 w-3 mr-1" />
                            Resume
                          </>
                        )}
                      </Button>
                      <Button size="sm" variant="outline">
                        <Eye className="h-3 w-3 mr-1" />
                        Monitor
                      </Button>
                      <Button size="sm" variant="outline">
                        <MessageSquare className="h-3 w-3 mr-1" />
                        Intervene
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Live Events Tab */}
        <TabsContent value="events" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Live System Events
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {liveEvents.map((event) => (
                  <div key={event.id} className="flex items-start space-x-3 p-3 rounded-lg border">
                    <div className="flex-shrink-0 mt-0.5">
                      {event.level === 'success' && <CheckCircle className="h-4 w-4 text-green-500" />}
                      {event.level === 'warning' && <AlertTriangle className="h-4 w-4 text-yellow-500" />}
                      {event.level === 'error' && <AlertTriangle className="h-4 w-4 text-red-500" />}
                      {event.level === 'info' && <Activity className="h-4 w-4 text-blue-500" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium">{event.message}</p>
                      <p className="text-xs text-muted-foreground">
                        {event.time.toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default UltraMCPControlTowerShadcn;