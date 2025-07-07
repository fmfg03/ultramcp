import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { 
  Bot, 
  Play, 
  Shield, 
  Code, 
  Database, 
  Plus, 
  Download,
  Upload,
  Activity,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Clock,
  Zap
} from 'lucide-react';

// Types
interface UltraMCPAgent {
  id: string;
  name: string;
  icon: string;
  system_prompt: string;
  default_task: string;
  model: 'opus' | 'sonnet' | 'haiku';
  capabilities: {
    file_read: boolean;
    file_write: boolean;
    network: boolean;
    ultramcp_integration: boolean;
    [key: string]: boolean;
  };
  ultramcp_services: string[];
  created_at: string;
  updated_at: string;
}

interface AgentExecution {
  id: string;
  agent_id: string;
  agent_name: string;
  task: string;
  project_path: string;
  session_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  services_used: string[];
  metrics: {
    execution_time_ms?: number;
    services_called?: number;
    success?: boolean;
    [key: string]: any;
  };
  created_at: string;
  completed_at?: string;
}

interface ExecutionMetrics {
  total_executions: number;
  status_breakdown: Record<string, number>;
  service_usage: Record<string, number>;
  running_executions: number;
}

// Icon mapping
const ICON_MAP = {
  bot: Bot,
  shield: Shield,
  code: Code,
  database: Database,
};

const SERVICE_COLORS = {
  cod: 'bg-purple-100 text-purple-800',
  asterisk: 'bg-red-100 text-red-800',
  blockoli: 'bg-blue-100 text-blue-800',
  voice: 'bg-green-100 text-green-800',
  memory: 'bg-yellow-100 text-yellow-800',
  deepclaude: 'bg-indigo-100 text-indigo-800',
  control_tower: 'bg-orange-100 text-orange-800',
  voyage: 'bg-teal-100 text-teal-800',
  ref_tools: 'bg-pink-100 text-pink-800',
};

const UltraMCPAgentManager: React.FC = () => {
  const [agents, setAgents] = useState<UltraMCPAgent[]>([]);
  const [templates, setTemplates] = useState<Record<string, UltraMCPAgent>>({});
  const [executions, setExecutions] = useState<AgentExecution[]>([]);
  const [metrics, setMetrics] = useState<ExecutionMetrics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<UltraMCPAgent | null>(null);
  const [executionTask, setExecutionTask] = useState<string>('');
  const [projectPath, setProjectPath] = useState<string>('/root/ultramcp');
  const [showExecuteDialog, setShowExecuteDialog] = useState<boolean>(false);

  const API_BASE = 'http://sam.chat:8013';

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [agentsRes, templatesRes, executionsRes, metricsRes] = await Promise.all([
        fetch(`${API_BASE}/agents`),
        fetch(`${API_BASE}/agents/templates`),
        fetch(`${API_BASE}/executions?limit=20`),
        fetch(`${API_BASE}/metrics`)
      ]);

      if (!agentsRes.ok || !templatesRes.ok || !executionsRes.ok || !metricsRes.ok) {
        throw new Error('Failed to load agent data');
      }

      const [agentsData, templatesData, executionsData, metricsData] = await Promise.all([
        agentsRes.json(),
        templatesRes.json(),
        executionsRes.json(),
        metricsRes.json()
      ]);

      setAgents(agentsData);
      setTemplates(templatesData);
      setExecutions(executionsData);
      setMetrics(metricsData);
    } catch (err) {
      console.error('Failed to load agent data:', err);
      setError('Failed to load agent data');
    } finally {
      setLoading(false);
    }
  };

  const installTemplate = async (templateName: string) => {
    try {
      const response = await fetch(`${API_BASE}/agents/templates/${templateName}/install`, {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error('Failed to install template');
      }

      await loadData(); // Refresh data
    } catch (err) {
      console.error('Failed to install template:', err);
      setError('Failed to install template');
    }
  };

  const executeAgent = async () => {
    if (!selectedAgent) return;

    try {
      const response = await fetch(`${API_BASE}/agents/${selectedAgent.id}/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          task: executionTask || selectedAgent.default_task,
          project_path: projectPath
        })
      });

      if (!response.ok) {
        throw new Error('Failed to execute agent');
      }

      setShowExecuteDialog(false);
      setExecutionTask('');
      await loadData(); // Refresh data
    } catch (err) {
      console.error('Failed to execute agent:', err);
      setError('Failed to execute agent');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'running':
        return <Activity className="h-4 w-4 text-blue-500 animate-pulse" />;
      case 'failed':
        return <AlertTriangle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-yellow-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-yellow-100 text-yellow-800';
    }
  };

  const renderAgentCard = (agent: UltraMCPAgent, isTemplate: boolean = false) => {
    const IconComponent = ICON_MAP[agent.icon as keyof typeof ICON_MAP] || Bot;

    return (
      <Card key={agent.id || agent.name} className="cursor-pointer hover:shadow-lg transition-shadow">
        <CardHeader className="flex flex-row items-center space-y-0 pb-2">
          <div className="flex items-center space-x-2">
            <IconComponent className="h-5 w-5 text-blue-600" />
            <div>
              <CardTitle className="text-base">{agent.name}</CardTitle>
              <CardDescription className="text-sm">
                Model: {agent.model} • Services: {agent.ultramcp_services.length}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-600 mb-3 line-clamp-2">
            {agent.default_task}
          </p>
          
          <div className="flex flex-wrap gap-1 mb-3">
            {agent.ultramcp_services.slice(0, 3).map(service => (
              <Badge
                key={service}
                variant="outline"
                className={`text-xs ${SERVICE_COLORS[service as keyof typeof SERVICE_COLORS] || 'bg-gray-100 text-gray-800'}`}
              >
                {service}
              </Badge>
            ))}
            {agent.ultramcp_services.length > 3 && (
              <Badge variant="outline" className="text-xs">
                +{agent.ultramcp_services.length - 3}
              </Badge>
            )}
          </div>

          <div className="flex space-x-2">
            {isTemplate ? (
              <Button
                size="sm"
                onClick={() => installTemplate(agent.name)}
                className="flex-1"
              >
                <Download className="h-3 w-3 mr-1" />
                Install
              </Button>
            ) : (
              <Button
                size="sm"
                onClick={() => {
                  setSelectedAgent(agent);
                  setExecutionTask(agent.default_task);
                  setShowExecuteDialog(true);
                }}
                className="flex-1"
              >
                <Play className="h-3 w-3 mr-1" />
                Execute
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderMetricsDashboard = () => (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Executions</CardTitle>
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
            {metrics ? Math.round(((metrics.status_breakdown.completed || 0) / metrics.total_executions) * 100) : 0}%
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
          <Bot className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{agents.length}</div>
        </CardContent>
      </Card>
    </div>
  );

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">UltraMCP Agent Manager</h1>
          <p className="text-gray-600">
            Manage AI agents with native UltraMCP service integration
          </p>
        </div>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Create Agent
        </Button>
      </div>

      {error && (
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {metrics && renderMetricsDashboard()}

      <Tabs defaultValue="agents" className="space-y-6">
        <TabsList>
          <TabsTrigger value="agents">My Agents ({agents.length})</TabsTrigger>
          <TabsTrigger value="templates">Templates ({Object.keys(templates).length})</TabsTrigger>
          <TabsTrigger value="executions">Recent Executions</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="agents" className="space-y-6">
          {agents.length === 0 ? (
            <Card>
              <CardContent className="pt-6 text-center">
                <Bot className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-medium mb-2">No agents yet</h3>
                <p className="text-gray-600 mb-4">
                  Install a template or create your first agent to get started
                </p>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Your First Agent
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {agents.map(agent => renderAgentCard(agent))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="templates" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(templates).map(([name, template]) => 
              renderAgentCard(template, true)
            )}
          </div>
        </TabsContent>

        <TabsContent value="executions" className="space-y-6">
          <div className="space-y-4">
            {executions.map(execution => (
              <Card key={execution.id}>
                <CardHeader className="flex flex-row items-center space-y-0 pb-2">
                  <div className="flex items-center space-x-2 flex-1">
                    {getStatusIcon(execution.status)}
                    <div>
                      <CardTitle className="text-base">{execution.agent_name}</CardTitle>
                      <CardDescription className="text-sm">
                        {execution.task}
                      </CardDescription>
                    </div>
                  </div>
                  <Badge className={getStatusColor(execution.status)}>
                    {execution.status}
                  </Badge>
                </CardHeader>
                <CardContent>
                  <div className="flex justify-between text-sm text-gray-600">
                    <span>Project: {execution.project_path}</span>
                    <span>
                      {new Date(execution.created_at).toLocaleString()}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {execution.services_used.map(service => (
                      <Badge
                        key={service}
                        variant="outline"
                        className={`text-xs ${SERVICE_COLORS[service as keyof typeof SERVICE_COLORS] || 'bg-gray-100 text-gray-800'}`}
                      >
                        {service}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Service Usage</CardTitle>
                <CardDescription>
                  How often each UltraMCP service is used by agents
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {metrics && Object.entries(metrics.service_usage).map(([service, count]) => (
                    <div key={service} className="flex justify-between items-center">
                      <Badge className={SERVICE_COLORS[service as keyof typeof SERVICE_COLORS] || 'bg-gray-100 text-gray-800'}>
                        {service}
                      </Badge>
                      <span className="text-sm font-medium">{count} executions</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Execution Status</CardTitle>
                <CardDescription>
                  Breakdown of execution results
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {metrics && Object.entries(metrics.status_breakdown).map(([status, count]) => (
                    <div key={status} className="flex justify-between items-center">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(status)}
                        <span className="capitalize">{status}</span>
                      </div>
                      <span className="text-sm font-medium">{count}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Execute Agent Dialog */}
      <Dialog open={showExecuteDialog} onOpenChange={setShowExecuteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Execute Agent: {selectedAgent?.name}</DialogTitle>
            <DialogDescription>
              Configure the execution parameters for this agent
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Task</label>
              <Input
                value={executionTask}
                onChange={(e) => setExecutionTask(e.target.value)}
                placeholder="Enter task description..."
                className="mt-1"
              />
            </div>
            
            <div>
              <label className="text-sm font-medium">Project Path</label>
              <Input
                value={projectPath}
                onChange={(e) => setProjectPath(e.target.value)}
                placeholder="/root/ultramcp"
                className="mt-1"
              />
            </div>

            {selectedAgent && (
              <div>
                <label className="text-sm font-medium">Services Used</label>
                <div className="flex flex-wrap gap-1 mt-2">
                  {selectedAgent.ultramcp_services.map(service => (
                    <Badge
                      key={service}
                      className={SERVICE_COLORS[service as keyof typeof SERVICE_COLORS] || 'bg-gray-100 text-gray-800'}
                    >
                      {service}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowExecuteDialog(false)}>
              Cancel
            </Button>
            <Button onClick={executeAgent}>
              <Play className="h-4 w-4 mr-2" />
              Execute Agent
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default UltraMCPAgentManager;