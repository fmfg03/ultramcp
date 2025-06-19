import React from 'react'
import { useMCP } from '@/contexts/MCPContext'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { 
  Activity,
  Bot,
  Zap,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertTriangle,
  Flame
} from 'lucide-react'

const Dashboard = () => {
  const { 
    metrics, 
    systemStatus, 
    executionHistory, 
    logs, 
    currentExecution,
    agents 
  } = useMCP()

  const recentExecutions = executionHistory.slice(0, 5)
  const recentLogs = logs.slice(0, 10)

  const getStatusColor = (status) => {
    switch (status) {
      case 'connected': return 'text-green-500'
      case 'disconnected': return 'text-red-500'
      case 'unknown': return 'text-yellow-500'
      default: return 'text-muted-foreground'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">MCP DevTool Dashboard</h1>
        <p className="text-muted-foreground">
          Monitor and control your MCP agent system
        </p>
      </div>

      {/* System Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">MCP Server</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              <Badge variant={systemStatus.mcpServer === 'connected' ? 'default' : 'destructive'}>
                {systemStatus.mcpServer}
              </Badge>
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
            <p className="text-xs text-muted-foreground">
              {currentExecution ? '1 running' : 'All idle'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Tokens</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.totalTokens.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              Across all models
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(metrics.successRate * 100).toFixed(1)}%</div>
            <Progress value={metrics.successRate * 100} className="mt-2" />
          </CardContent>
        </Card>
      </div>

      {/* Current Execution */}
      {currentExecution && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <div className="status-indicator active"></div>
              <span>Current Execution</span>
            </CardTitle>
            <CardDescription>
              Agent: {currentExecution.agent} • Started: {new Date(currentExecution.timestamp).toLocaleTimeString()}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <p className="text-sm font-medium">Prompt:</p>
              <p className="text-sm text-muted-foreground bg-muted p-3 rounded-lg">
                {currentExecution.prompt}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Executions */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Executions</CardTitle>
            <CardDescription>
              Last {recentExecutions.length} agent executions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentExecutions.length > 0 ? (
                recentExecutions.map((execution, index) => (
                  <div key={execution.id || index} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                    <div className="flex items-center space-x-3">
                      {execution.status === 'completed' ? (
                        <CheckCircle className="w-4 h-4 text-green-500" />
                      ) : execution.status === 'error' ? (
                        <AlertTriangle className="w-4 h-4 text-red-500" />
                      ) : (
                        <Clock className="w-4 h-4 text-yellow-500" />
                      )}
                      <div>
                        <p className="text-sm font-medium">{execution.agent}</p>
                        <p className="text-xs text-muted-foreground">
                          {execution.prompt?.substring(0, 50)}...
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <Badge variant={execution.status === 'completed' ? 'default' : 'secondary'}>
                        {execution.status}
                      </Badge>
                      <p className="text-xs text-muted-foreground mt-1">
                        {new Date(execution.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground text-center py-4">
                  No recent executions
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* System Logs */}
        <Card>
          <CardHeader>
            <CardTitle>System Logs</CardTitle>
            <CardDescription>
              Real-time system activity
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-80 overflow-y-auto custom-scrollbar">
              {recentLogs.length > 0 ? (
                recentLogs.map((log, index) => (
                  <div key={log.id || index} className={`log-entry ${log.level} p-2 rounded text-xs`}>
                    <div className="flex items-center justify-between">
                      <span className="font-medium">
                        {log.level === 'warning' && log.source === 'contradiction' && (
                          <Flame className="w-3 h-3 inline mr-1" />
                        )}
                        {log.message}
                      </span>
                      <span className="text-muted-foreground">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    {log.source && (
                      <div className="text-muted-foreground mt-1">
                        Source: {log.source}
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground text-center py-4">
                  No recent logs
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Local LLMs Status */}
      <Card>
        <CardHeader>
          <CardTitle>Local LLM Status</CardTitle>
          <CardDescription>
            Status of local language models
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(systemStatus.localLLMs).map(([model, status]) => (
              <div key={model} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className={`status-indicator ${
                    status === 'connected' ? 'success' : 
                    status === 'disconnected' ? 'error' : 'idle'
                  }`}></div>
                  <span className="font-medium capitalize">{model}</span>
                </div>
                <Badge variant={status === 'connected' ? 'default' : 'secondary'}>
                  {status}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Contradiction Metrics */}
      {metrics.contradictionsApplied > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Flame className="w-5 h-5 text-orange-500" />
              <span>Contradiction Analysis</span>
            </CardTitle>
            <CardDescription>
              System improvement through explicit contradiction
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="metric-card">
                <div className="metric-value">{metrics.contradictionsApplied}</div>
                <div className="metric-label">Total Applied</div>
              </div>
              <div className="metric-card">
                <div className="metric-value">{metrics.avgResponseTime.toFixed(0)}ms</div>
                <div className="metric-label">Avg Response Time</div>
              </div>
              <div className="metric-card">
                <div className="metric-value">{(metrics.successRate * 100).toFixed(1)}%</div>
                <div className="metric-label">Success Rate</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default Dashboard

