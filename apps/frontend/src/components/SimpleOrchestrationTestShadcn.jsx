import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { Alert, AlertDescription } from './ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { 
  Play, 
  RefreshCw, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Loader2,
  Zap,
  BarChart3,
  Settings,
  Users,
  MessageSquare,
  ArrowRight
} from 'lucide-react';

const SimpleOrchestrationTestShadcn = () => {
  const [task, setTask] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('execute');

  // Sample execution history
  const [executionHistory] = useState([
    {
      id: 1,
      task: 'Analyze project architecture',
      status: 'completed',
      timestamp: new Date(Date.now() - 10 * 60 * 1000),
      duration: 45,
      services: ['blockoli', 'memory']
    },
    {
      id: 2,
      task: 'Security vulnerability scan',
      status: 'completed',
      timestamp: new Date(Date.now() - 25 * 60 * 1000),
      duration: 120,
      services: ['asterisk', 'security']
    },
    {
      id: 3,
      task: 'Multi-LLM debate on architecture',
      status: 'failed',
      timestamp: new Date(Date.now() - 45 * 60 * 1000),
      duration: 15,
      services: ['cod']
    }
  ]);

  const runTask = async () => {
    if (!task.trim()) {
      setError('Please enter a task to execute');
      return;
    }

    setIsRunning(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch('/api/run-task', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          request: task,
          options: {
            userId: 'demo-user',
            maxRetries: 2
          }
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Error executing task');
      }

      setResult(data);
      setTask('');

    } catch (err) {
      console.error('Error executing task:', err);
      setError(err.message);
    } finally {
      setIsRunning(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'running': return 'bg-blue-100 text-blue-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircle className="h-4 w-4" />;
      case 'running': return <Loader2 className="h-4 w-4 animate-spin" />;
      case 'failed': return <AlertTriangle className="h-4 w-4" />;
      default: return <Clock className="h-4 w-4" />;
    }
  };

  const presetTasks = [
    'Analyze the codebase architecture and provide improvement recommendations',
    'Perform a comprehensive security scan of the application',
    'Start a debate between AI models about best practices',
    'Generate a performance optimization report',
    'Review code quality and suggest refactoring opportunities'
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Orchestration Testing</h2>
          <p className="text-muted-foreground">
            Test and monitor UltraMCP service orchestration workflows
          </p>
        </div>
        <Button variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh Status
        </Button>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Executions</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{executionHistory.length}</div>
            <p className="text-xs text-muted-foreground">All time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {Math.round((executionHistory.filter(h => h.status === 'completed').length / executionHistory.length) * 100)}%
            </div>
            <p className="text-xs text-muted-foreground">Last 24 hours</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Duration</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Math.round(executionHistory.reduce((acc, h) => acc + h.duration, 0) / executionHistory.length)}s
            </div>
            <p className="text-xs text-muted-foreground">Per execution</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Services</CardTitle>
            <Settings className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">6</div>
            <p className="text-xs text-muted-foreground">Available</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="execute">Execute Task</TabsTrigger>
          <TabsTrigger value="history">Execution History</TabsTrigger>
          <TabsTrigger value="presets">Quick Presets</TabsTrigger>
        </TabsList>

        {/* Execute Task Tab */}
        <TabsContent value="execute" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Task Input */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5" />
                  Task Execution
                </CardTitle>
                <CardDescription>
                  Enter a task to execute using UltraMCP services
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Task Description</label>
                  <Input
                    value={task}
                    onChange={(e) => setTask(e.target.value)}
                    placeholder="Describe the task you want to execute..."
                    className="w-full"
                    onKeyPress={(e) => e.key === 'Enter' && runTask()}
                  />
                </div>

                <Button
                  onClick={runTask}
                  disabled={isRunning || !task.trim()}
                  className="w-full"
                >
                  {isRunning ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Executing Task...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 mr-2" />
                      Execute Task
                    </>
                  )}
                </Button>

                {error && (
                  <Alert variant="destructive">
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>

            {/* Results */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ArrowRight className="h-5 w-5" />
                  Execution Results
                </CardTitle>
                <CardDescription>
                  View the output and status of your task execution
                </CardDescription>
              </CardHeader>
              <CardContent>
                {result && (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span className="text-sm font-medium">Task Completed Successfully</span>
                    </div>
                    
                    <div className="p-4 bg-muted rounded-lg">
                      <pre className="text-sm whitespace-pre-wrap max-h-96 overflow-auto">
                        {typeof result === 'string' 
                          ? result 
                          : JSON.stringify(result, null, 2)
                        }
                      </pre>
                    </div>
                  </div>
                )}

                {!result && !error && !isRunning && (
                  <div className="flex items-center justify-center py-12 text-muted-foreground">
                    <div className="text-center">
                      <MessageSquare className="h-8 w-8 mx-auto mb-2" />
                      <p>Execute a task to see results here</p>
                    </div>
                  </div>
                )}

                {isRunning && (
                  <div className="flex items-center justify-center py-12">
                    <div className="text-center">
                      <Loader2 className="h-8 w-8 mx-auto mb-2 animate-spin" />
                      <p className="text-muted-foreground">Processing your task...</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Execution History Tab */}
        <TabsContent value="history" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Execution History</CardTitle>
              <CardDescription>
                View past task executions and their results
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {executionHistory.map((execution) => (
                  <div key={execution.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(execution.status)}
                      <div>
                        <div className="font-medium">{execution.task}</div>
                        <div className="text-sm text-muted-foreground">
                          {execution.timestamp.toLocaleString()} • {execution.duration}s duration
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="flex space-x-1">
                        {execution.services.map((service) => (
                          <Badge key={service} variant="outline" className="text-xs">
                            {service}
                          </Badge>
                        ))}
                      </div>
                      <Badge className={getStatusColor(execution.status)}>
                        {execution.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Quick Presets Tab */}
        <TabsContent value="presets" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5" />
                Quick Task Presets
              </CardTitle>
              <CardDescription>
                Choose from predefined tasks to test different UltraMCP services
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {presetTasks.map((presetTask, index) => (
                  <Card key={index} className="cursor-pointer hover:shadow-md transition-shadow"
                        onClick={() => setTask(presetTask)}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <p className="text-sm">{presetTask}</p>
                        <Button size="sm" variant="outline" onClick={(e) => {
                          e.stopPropagation();
                          setTask(presetTask);
                          setActiveTab('execute');
                        }}>
                          Use
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default SimpleOrchestrationTestShadcn;