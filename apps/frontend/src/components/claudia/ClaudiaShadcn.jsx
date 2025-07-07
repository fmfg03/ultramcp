import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { 
  Bot, 
  Play, 
  Download, 
  RefreshCw, 
  Plus,
  Activity,
  TrendingUp,
  Users,
  Code,
  Shield,
  Database,
  CheckCircle,
  Clock,
  AlertTriangle,
  Zap
} from 'lucide-react';

const ClaudiaShadcn = () => {
  const [agents, setAgents] = useState([]);
  const [templates, setTemplates] = useState({});
  const [executions, setExecutions] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Service configurations
  const serviceConfig = {
    cod: { icon: Users, color: 'bg-purple-100 text-purple-800', name: 'Chain-of-Debate' },
    asterisk: { icon: Shield, color: 'bg-red-100 text-red-800', name: 'Security' },
    blockoli: { icon: Code, color: 'bg-blue-100 text-blue-800', name: 'Code Intelligence' },
    voice: { icon: Bot, color: 'bg-green-100 text-green-800', name: 'Voice System' },
    memory: { icon: Database, color: 'bg-yellow-100 text-yellow-800', name: 'Memory' },
    deepclaude: { icon: Activity, color: 'bg-indigo-100 text-indigo-800', name: 'DeepClaude' },
    control_tower: { icon: TrendingUp, color: 'bg-orange-100 text-orange-800', name: 'Control Tower' },
  };

  // Load data on mount and refresh
  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log('🔄 Loading data from API...');

      // Load agents
      try {
        const agentsRes = await fetch('/api/agents');
        console.log('📡 Agents response status:', agentsRes.status);
        if (agentsRes.ok) {
          const agentsData = await agentsRes.json();
          console.log('🤖 Agents loaded:', agentsData.length);
          setAgents(agentsData || []);
        }
      } catch (err) {
        console.error('❌ Error loading agents:', err);
      }

      // Load templates (may not exist)
      try {
        const templatesRes = await fetch('/api/agents/templates');
        if (templatesRes.ok) {
          const templatesData = await templatesRes.json();
          console.log('📋 Templates loaded:', Object.keys(templatesData).length);
          setTemplates(templatesData || {});
        }
      } catch (err) {
        console.error('⚠️ Templates not available:', err.message);
        setTemplates({});
      }

      // Load executions
      try {
        const executionsRes = await fetch('/api/executions');
        console.log('📊 Executions response status:', executionsRes.status);
        if (executionsRes.ok) {
          const executionsData = await executionsRes.json();
          console.log('📈 Executions loaded:', executionsData.length);
          setExecutions(executionsData || []);
        }
      } catch (err) {
        console.error('❌ Error loading executions:', err);
      }

      // Load metrics
      try {
        const metricsRes = await fetch('/api/metrics');
        console.log('📈 Metrics response status:', metricsRes.status);
        if (metricsRes.ok) {
          const metricsData = await metricsRes.json();
          console.log('📊 Metrics loaded:', metricsData);
          setMetrics(metricsData || null);
        }
      } catch (err) {
        console.error('❌ Error loading metrics:', err);
      }

      console.log('✅ Data loading complete');
    } catch (err) {
      console.error('💥 Critical error loading data:', err);
      setError(`Failed to load data: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const installTemplate = async (templateName) => {
    try {
      const response = await fetch(`/api/agents/templates/${templateName}/install`, {
        method: 'POST'
      });
      if (response.ok) loadData();
    } catch (err) {
      setError('Failed to install template');
    }
  };

  const executeAgent = async (agent) => {
    const task = prompt(`Execute ${agent.name}:\n\nWhat task should it perform?`, agent.default_task);
    if (!task) return;

    try {
      const response = await fetch(`/api/agents/${agent.id}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task,
          project_path: '/root/ultramcp'
        })
      });
      if (response.ok) loadData();
    } catch (err) {
      setError('Failed to execute agent');
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'running': return <Activity className="h-4 w-4 text-blue-500 animate-pulse" />;
      case 'failed': return <AlertTriangle className="h-4 w-4 text-red-500" />;
      default: return <Clock className="h-4 w-4 text-yellow-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'running': return 'bg-blue-100 text-blue-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-yellow-100 text-yellow-800';
    }
  };

  // Debug logging
  console.log('🔍 Component state:', { 
    agentsCount: agents.length, 
    executionsCount: executions.length, 
    metricsData: metrics,
    loading,
    error 
  });

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-bold tracking-tight">Claudia AI Assistant</h1>
          <p className="text-muted-foreground mt-2">
            Intelligent agent management with UltraMCP integration • {agents.length} agents • {executions.length} executions
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={loadData} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button disabled>
            <Plus className="h-4 w-4 mr-2" />
            Create Agent
          </Button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertTriangle className="h-5 w-5 text-red-400 mr-2" />
            <span className="text-red-800">{error}</span>
            <Button 
              variant="ghost" 
              size="sm" 
              className="ml-auto text-red-600"
              onClick={() => setError(null)}
            >
              ×
            </Button>
          </div>
        </div>
      )}

      {/* Metrics Dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Agents</CardTitle>
            <Bot className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{agents.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Executions</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.total_executions || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Running Now</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{metrics?.running_executions || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {metrics && metrics.total_executions > 0 
                ? Math.round(((metrics.status_breakdown?.completed || 0) / metrics.total_executions) * 100)
                : 0}%
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="agents" className="space-y-4">
        <TabsList>
          <TabsTrigger value="agents">My Agents ({agents.length})</TabsTrigger>
          <TabsTrigger value="templates">Templates ({Object.keys(templates).length})</TabsTrigger>
          <TabsTrigger value="executions">Recent Executions</TabsTrigger>
        </TabsList>

        {/* Agents Tab */}
        <TabsContent value="agents" className="space-y-4">
          {agents.length === 0 ? (
            <Card>
              <CardContent className="pt-6 text-center py-12">
                <Bot className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium mb-2">No agents installed</h3>
                <p className="text-muted-foreground mb-4">
                  Install a template to get started with AI agents
                </p>
                <Button>
                  <Download className="h-4 w-4 mr-2" />
                  Browse Templates
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {agents.map((agent) => (
                <Card key={agent.id} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-blue-100 rounded-lg">
                        <Bot className="h-5 w-5 text-blue-600" />
                      </div>
                      <div>
                        <CardTitle className="text-lg">{agent.name}</CardTitle>
                        <CardDescription>Model: {agent.model}</CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
                      {agent.default_task}
                    </p>
                    
                    <div className="flex flex-wrap gap-1 mb-4">
                      {agent.ultramcp_services?.slice(0, 3).map((service) => {
                        const config = serviceConfig[service] || { icon: Bot, color: 'bg-gray-100 text-gray-800', name: service };
                        const IconComponent = config.icon;
                        return (
                          <Badge key={service} variant="outline" className={`text-xs ${config.color}`}>
                            <IconComponent className="h-3 w-3 mr-1" />
                            {config.name}
                          </Badge>
                        );
                      })}
                      {agent.ultramcp_services?.length > 3 && (
                        <Badge variant="outline" className="text-xs">
                          +{agent.ultramcp_services.length - 3}
                        </Badge>
                      )}
                    </div>

                    <Button 
                      className="w-full" 
                      onClick={() => executeAgent(agent)}
                    >
                      <Play className="h-4 w-4 mr-2" />
                      Execute Agent
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Templates Tab */}
        <TabsContent value="templates" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(templates).map(([name, template]) => (
              <Card key={name} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-purple-100 rounded-lg">
                      <Download className="h-5 w-5 text-purple-600" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{template.name}</CardTitle>
                      <CardDescription>Template</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
                    {template.default_task}
                  </p>
                  
                  <div className="flex flex-wrap gap-1 mb-4">
                    {template.ultramcp_services?.map((service) => {
                      const config = serviceConfig[service] || { icon: Bot, color: 'bg-gray-100 text-gray-800', name: service };
                      const IconComponent = config.icon;
                      return (
                        <Badge key={service} variant="outline" className={`text-xs ${config.color}`}>
                          <IconComponent className="h-3 w-3 mr-1" />
                          {config.name}
                        </Badge>
                      );
                    })}
                  </div>

                  <Button 
                    variant="outline" 
                    className="w-full"
                    onClick={() => installTemplate(name)}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Install Template
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Executions Tab */}
        <TabsContent value="executions" className="space-y-4">
          {executions.length === 0 ? (
            <Card>
              <CardContent className="pt-6 text-center py-12">
                <Activity className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium mb-2">No executions yet</h3>
                <p className="text-muted-foreground">
                  Execute an agent to see results here
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {executions.slice(0, 10).map((execution) => (
                <Card key={execution.id}>
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {getStatusIcon(execution.status)}
                        <div>
                          <div className="flex items-center gap-2">
                            <h4 className="font-medium">{execution.agent_name}</h4>
                            <Badge className={getStatusColor(execution.status)}>
                              {execution.status}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground mt-1">
                            {execution.task}
                          </p>
                          <div className="flex flex-wrap gap-1 mt-2">
                            {execution.services_used?.map((service) => (
                              <Badge key={service} variant="outline" className="text-xs">
                                {service}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      </div>
                      <div className="text-right text-sm text-muted-foreground">
                        {new Date(execution.created_at).toLocaleString()}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ClaudiaShadcn;