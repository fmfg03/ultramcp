import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Alert, AlertDescription } from '../ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { 
  Code, 
  Play, 
  RefreshCw, 
  Settings, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Loader2,
  ChevronRight,
  Wrench,
  Zap
} from 'lucide-react';

const MCPToolSelectorShadcn = () => {
  const [allTools, setAllTools] = useState([]);
  const [toolsByAdapter, setToolsByAdapter] = useState({});
  const [selectedToolId, setSelectedToolId] = useState('');
  const [selectedToolDetails, setSelectedToolDetails] = useState(null);
  const [parameterValues, setParameterValues] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState(null);
  const [executionError, setExecutionError] = useState(null);

  // Fetch all tools on component mount
  useEffect(() => {
    fetch('/api/tools')
      .then(res => {
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
      })
      .then(data => {
        console.log('✅ Tools loaded successfully:', data);
        
        const tools = data.tools || data || [];
        setAllTools(tools);
        
        // Group tools by type for the dropdown
        const groupedTools = tools.reduce((acc, tool) => {
          const groupKey = tool.type || 'general';
          if (!acc[groupKey]) {
            acc[groupKey] = [];
          }
          acc[groupKey].push(tool);
          return acc;
        }, {});
        
        setToolsByAdapter(groupedTools);
        setLoading(false);
      })
      .catch(error => {
        console.error('❌ Error fetching tools:', error);
        setError(`Failed to load tools: ${error.message}`);
        setLoading(false);
      });
  }, []);

  // Handle tool selection
  const handleToolSelection = (toolId) => {
    setSelectedToolId(toolId);
    setExecutionResult(null);
    setExecutionError(null);
    
    const tool = allTools.find(t => t.name === toolId);
    if (tool) {
      setSelectedToolDetails(tool);
      // Initialize parameter values
      const initialParams = {};
      if (tool.inputSchema && tool.inputSchema.properties) {
        Object.keys(tool.inputSchema.properties).forEach(key => {
          initialParams[key] = '';
        });
      }
      setParameterValues(initialParams);
    }
  };

  // Handle parameter value changes
  const handleParameterChange = (paramName, value) => {
    setParameterValues(prev => ({
      ...prev,
      [paramName]: value
    }));
  };

  // Execute the selected tool
  const executeTool = async () => {
    if (!selectedToolDetails) return;

    setIsExecuting(true);
    setExecutionError(null);
    setExecutionResult(null);

    try {
      const response = await fetch('/api/tools/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          toolName: selectedToolDetails.name,
          parameters: parameterValues,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setExecutionResult(result);
      console.log('✅ Tool executed successfully:', result);
    } catch (error) {
      console.error('❌ Error executing tool:', error);
      setExecutionError(error.message);
    } finally {
      setIsExecuting(false);
    }
  };

  const renderParameterInput = (paramName, paramSchema) => {
    const value = parameterValues[paramName] || '';
    
    return (
      <div key={paramName} className="space-y-2">
        <label className="text-sm font-medium">
          {paramName}
          {paramSchema.required && <span className="text-red-500 ml-1">*</span>}
        </label>
        {paramSchema.description && (
          <p className="text-xs text-muted-foreground">{paramSchema.description}</p>
        )}
        
        {paramSchema.enum ? (
          <Select value={value} onValueChange={(val) => handleParameterChange(paramName, val)}>
            <SelectTrigger>
              <SelectValue placeholder={`Select ${paramName}`} />
            </SelectTrigger>
            <SelectContent>
              {paramSchema.enum.map((option) => (
                <SelectItem key={option} value={option}>
                  {option}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : (
          <Input
            type={paramSchema.type === 'number' ? 'number' : 'text'}
            value={value}
            onChange={(e) => handleParameterChange(paramName, e.target.value)}
            placeholder={paramSchema.default || `Enter ${paramName}`}
            className="w-full"
          />
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="flex items-center space-x-2">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span>Loading MCP tools...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">MCP Tools</h2>
          <p className="text-muted-foreground">
            Execute Model Context Protocol tools and integrations
          </p>
        </div>
        <Button variant="outline" onClick={() => window.location.reload()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh Tools
        </Button>
      </div>

      {/* Tools Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Tools</CardTitle>
            <Wrench className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{allTools.length}</div>
            <p className="text-xs text-muted-foreground">Available for execution</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Adapters</CardTitle>
            <Settings className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{Object.keys(toolsByAdapter).length}</div>
            <p className="text-xs text-muted-foreground">Connected adapters</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Status</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">Ready</div>
            <p className="text-xs text-muted-foreground">System operational</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Tool Interface */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Tool Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Code className="h-5 w-5" />
              Tool Selection
            </CardTitle>
            <CardDescription>
              Choose a tool to execute from the available MCP adapters
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Tool Selector */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Select Tool</label>
              <Select value={selectedToolId} onValueChange={handleToolSelection}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose a tool to execute" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(toolsByAdapter).map(([adapterType, tools]) => (
                    <div key={adapterType}>
                      <div className="px-2 py-1.5 text-sm font-semibold text-muted-foreground border-b">
                        {adapterType.toUpperCase()}
                      </div>
                      {tools.map((tool) => (
                        <SelectItem key={tool.name} value={tool.name}>
                          <div className="flex items-center space-x-2">
                            <Zap className="h-3 w-3" />
                            <span>{tool.name}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </div>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Tool Details */}
            {selectedToolDetails && (
              <div className="space-y-4 p-4 border rounded-lg bg-muted/50">
                <div>
                  <h4 className="font-medium">{selectedToolDetails.name}</h4>
                  <p className="text-sm text-muted-foreground mt-1">
                    {selectedToolDetails.description}
                  </p>
                </div>

                {/* Parameters */}
                {selectedToolDetails.inputSchema && selectedToolDetails.inputSchema.properties && (
                  <div className="space-y-3">
                    <h5 className="text-sm font-medium">Parameters</h5>
                    {Object.entries(selectedToolDetails.inputSchema.properties).map(([paramName, paramSchema]) =>
                      renderParameterInput(paramName, paramSchema)
                    )}
                  </div>
                )}

                {/* Execute Button */}
                <Button 
                  onClick={executeTool} 
                  disabled={isExecuting} 
                  className="w-full"
                >
                  {isExecuting ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Executing...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 mr-2" />
                      Execute Tool
                    </>
                  )}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Execution Results */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ChevronRight className="h-5 w-5" />
              Execution Results
            </CardTitle>
            <CardDescription>
              View the output from tool execution
            </CardDescription>
          </CardHeader>
          <CardContent>
            {executionError && (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>{executionError}</AlertDescription>
              </Alert>
            )}

            {executionResult && (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span className="text-sm font-medium">Execution Successful</span>
                </div>
                
                <div className="p-4 bg-muted rounded-lg">
                  <pre className="text-sm whitespace-pre-wrap overflow-auto max-h-96">
                    {typeof executionResult === 'string' 
                      ? executionResult 
                      : JSON.stringify(executionResult, null, 2)
                    }
                  </pre>
                </div>
              </div>
            )}

            {!executionResult && !executionError && !isExecuting && (
              <div className="flex items-center justify-center py-12 text-muted-foreground">
                <div className="text-center">
                  <Clock className="h-8 w-8 mx-auto mb-2" />
                  <p>Select and execute a tool to see results</p>
                </div>
              </div>
            )}

            {isExecuting && (
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <Loader2 className="h-8 w-8 mx-auto mb-2 animate-spin" />
                  <p className="text-muted-foreground">Executing tool...</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Available Tools List */}
      <Card>
        <CardHeader>
          <CardTitle>Available Tools</CardTitle>
          <CardDescription>
            Browse all available MCP tools by adapter type
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue={Object.keys(toolsByAdapter)[0]} className="w-full">
            <TabsList className="grid w-full grid-cols-auto">
              {Object.keys(toolsByAdapter).map((adapterType) => (
                <TabsTrigger key={adapterType} value={adapterType}>
                  {adapterType.toUpperCase()}
                </TabsTrigger>
              ))}
            </TabsList>
            
            {Object.entries(toolsByAdapter).map(([adapterType, tools]) => (
              <TabsContent key={adapterType} value={adapterType} className="space-y-3">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {tools.map((tool) => (
                    <Card key={tool.name} className="cursor-pointer hover:shadow-md transition-shadow"
                          onClick={() => handleToolSelection(tool.name)}>
                      <CardContent className="p-4">
                        <div className="flex items-center space-x-2 mb-2">
                          <Zap className="h-4 w-4 text-primary" />
                          <h4 className="font-medium">{tool.name}</h4>
                        </div>
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          {tool.description}
                        </p>
                        <div className="mt-3">
                          <Badge variant="outline">{adapterType}</Badge>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </TabsContent>
            ))}
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};

export default MCPToolSelectorShadcn;