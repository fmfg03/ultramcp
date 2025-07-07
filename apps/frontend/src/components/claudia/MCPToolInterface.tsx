import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  Tooltip,
  Paper,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Badge
} from '@mui/material';
import {
  ExpandMore,
  PlayArrow,
  Build,
  Code,
  Security,
  RecordVoiceOver,
  Assignment,
  Refresh,
  Settings,
  Info,
  CheckCircle,
  Error,
  Warning,
  Schedule
} from '@mui/icons-material';

const API_BASE = 'http://sam.chat:8013';

interface MCPTool {
  name: string;
  description: string;
  inputSchema: {
    type: string;
    properties: { [key: string]: any };
    required?: string[];
  };
}

interface MCPResource {
  uri: string;
  name: string;
  description: string;
  mimeType: string;
}

interface MCPPrompt {
  name: string;
  description: string;
  arguments: Array<{
    name: string;
    description: string;
    required: boolean;
  }>;
}

interface ToolExecution {
  id: string;
  tool: string;
  status: 'running' | 'completed' | 'failed';
  result?: any;
  error?: string;
  timestamp: string;
}

export const MCPToolInterface: React.FC = () => {
  const [tools, setTools] = useState<MCPTool[]>([]);
  const [resources, setResources] = useState<MCPResource[]>([]);
  const [prompts, setPrompts] = useState<MCPPrompt[]>([]);
  const [selectedTool, setSelectedTool] = useState<MCPTool | null>(null);
  const [toolArguments, setToolArguments] = useState<{ [key: string]: any }>({});
  const [executions, setExecutions] = useState<ToolExecution[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [executeDialogOpen, setExecuteDialogOpen] = useState(false);
  const [selectedTab, setSelectedTab] = useState<'tools' | 'resources' | 'prompts'>('tools');
  const [mcpStatus, setMcpStatus] = useState<'enabled' | 'disabled' | 'unknown'>('unknown');

  useEffect(() => {
    loadMCPData();
    checkMCPStatus();
    const interval = setInterval(loadMCPData, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const checkMCPStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/health`);
      const data = await response.json();
      setMcpStatus(data.mcp_protocol === 'enabled' ? 'enabled' : 'disabled');
    } catch (error) {
      setMcpStatus('unknown');
    }
  };

  const loadMCPData = async () => {
    try {
      // Load tools
      const toolsResponse = await fetch(`${API_BASE}/mcp/tools`);
      if (toolsResponse.ok) {
        const toolsData = await toolsResponse.json();
        setTools(toolsData.tools || []);
      }

      // Load resources
      const resourcesResponse = await fetch(`${API_BASE}/mcp/resources`);
      if (resourcesResponse.ok) {
        const resourcesData = await resourcesResponse.json();
        setResources(resourcesData.resources || []);
      }

      // Load prompts
      const promptsResponse = await fetch(`${API_BASE}/mcp/prompts`);
      if (promptsResponse.ok) {
        const promptsData = await promptsResponse.json();
        setPrompts(promptsData.prompts || []);
      }
    } catch (error) {
      console.error('Failed to load MCP data:', error);
      setError('Failed to load MCP data');
    }
  };

  const getToolIcon = (toolName: string) => {
    if (toolName.includes('security')) return <Security color="error" />;
    if (toolName.includes('code') || toolName.includes('analysis')) return <Code color="primary" />;
    if (toolName.includes('debate')) return <Assignment color="secondary" />;
    if (toolName.includes('voice')) return <RecordVoiceOver color="success" />;
    return <Build color="action" />;
  };

  const openExecuteDialog = (tool: MCPTool) => {
    setSelectedTool(tool);
    setToolArguments({});
    setExecuteDialogOpen(true);
  };

  const handleArgumentChange = (argName: string, value: any) => {
    setToolArguments(prev => ({
      ...prev,
      [argName]: value
    }));
  };

  const renderInputField = (propName: string, propSchema: any, required: boolean = false) => {
    const value = toolArguments[propName] || '';
    const commonProps = {
      fullWidth: true,
      variant: 'outlined' as const,
      margin: 'normal' as const,
      required,
      value,
      onChange: (e: any) => handleArgumentChange(propName, e.target.value)
    };

    if (propSchema.enum) {
      return (
        <FormControl {...commonProps}>
          <InputLabel>{propName}</InputLabel>
          <Select
            label={propName}
            value={value}
            onChange={(e) => handleArgumentChange(propName, e.target.value)}
          >
            {propSchema.enum.map((option: string) => (
              <MenuItem key={option} value={option}>{option}</MenuItem>
            ))}
          </Select>
        </FormControl>
      );
    }

    if (propSchema.type === 'array') {
      return (
        <TextField
          {...commonProps}
          label={`${propName} (comma-separated)`}
          helperText={propSchema.description}
          onChange={(e) => handleArgumentChange(propName, e.target.value.split(',').map(s => s.trim()))}
        />
      );
    }

    if (propSchema.type === 'integer' || propSchema.type === 'number') {
      return (
        <TextField
          {...commonProps}
          label={propName}
          type="number"
          helperText={propSchema.description}
          inputProps={{
            min: propSchema.minimum,
            max: propSchema.maximum
          }}
        />
      );
    }

    return (
      <TextField
        {...commonProps}
        label={propName}
        helperText={propSchema.description}
        multiline={propSchema.description?.includes('path') ? false : true}
        rows={propSchema.description?.includes('path') ? 1 : 3}
      />
    );
  };

  const executeTool = async () => {
    if (!selectedTool) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/mcp/tools/${selectedTool.name}/call`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(toolArguments),
      });

      if (response.ok) {
        const result = await response.json();
        const execution: ToolExecution = {
          id: `exec_${Date.now()}`,
          tool: selectedTool.name,
          status: 'completed',
          result: result.result,
          timestamp: new Date().toISOString()
        };
        setExecutions(prev => [execution, ...prev]);
        setExecuteDialogOpen(false);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Tool execution failed');
      }
    } catch (error) {
      setError('Network error during tool execution');
    } finally {
      setLoading(false);
    }
  };

  const readResource = async (resource: MCPResource) => {
    try {
      const response = await fetch(`${API_BASE}/mcp/resources/read?uri=${encodeURIComponent(resource.uri)}`);
      if (response.ok) {
        const data = await response.json();
        // Display resource content in a dialog or expand it inline
        console.log('Resource content:', data);
      }
    } catch (error) {
      console.error('Failed to read resource:', error);
    }
  };

  const StatusIndicator = () => (
    <Box display="flex" alignItems="center" gap={1}>
      <Typography variant="h6">MCP Protocol Status:</Typography>
      <Chip
        icon={mcpStatus === 'enabled' ? <CheckCircle /> : mcpStatus === 'disabled' ? <Warning /> : <Error />}
        label={mcpStatus === 'enabled' ? 'Enabled' : mcpStatus === 'disabled' ? 'Disabled' : 'Unknown'}
        color={mcpStatus === 'enabled' ? 'success' : mcpStatus === 'disabled' ? 'warning' : 'error'}
      />
      <Tooltip title="Refresh status">
        <IconButton onClick={checkMCPStatus} size="small">
          <Refresh />
        </IconButton>
      </Tooltip>
    </Box>
  );

  return (
    <Box sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          MCP Protocol Interface
        </Typography>
        <StatusIndicator />
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Box display="flex" gap={2} mb={2}>
                <Button
                  variant={selectedTab === 'tools' ? 'contained' : 'outlined'}
                  onClick={() => setSelectedTab('tools')}
                  startIcon={<Build />}
                >
                  Tools ({tools.length})
                </Button>
                <Button
                  variant={selectedTab === 'resources' ? 'contained' : 'outlined'}
                  onClick={() => setSelectedTab('resources')}
                  startIcon={<Assignment />}
                >
                  Resources ({resources.length})
                </Button>
                <Button
                  variant={selectedTab === 'prompts' ? 'contained' : 'outlined'}
                  onClick={() => setSelectedTab('prompts')}
                  startIcon={<Info />}
                >
                  Prompts ({prompts.length})
                </Button>
              </Box>

              {selectedTab === 'tools' && (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Available MCP Tools
                  </Typography>
                  {tools.map((tool) => (
                    <Accordion key={tool.name}>
                      <AccordionSummary expandIcon={<ExpandMore />}>
                        <Box display="flex" alignItems="center" gap={2}>
                          {getToolIcon(tool.name)}
                          <Box>
                            <Typography variant="subtitle1">{tool.name}</Typography>
                            <Typography variant="body2" color="text.secondary">
                              {tool.description}
                            </Typography>
                          </Box>
                        </Box>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Box>
                          <Typography variant="body2" paragraph>
                            <strong>Input Schema:</strong>
                          </Typography>
                          <Paper sx={{ p: 2, mb: 2, bgcolor: 'grey.50' }}>
                            <pre style={{ margin: 0, fontSize: '0.875rem' }}>
                              {JSON.stringify(tool.inputSchema, null, 2)}
                            </pre>
                          </Paper>
                          <Button
                            variant="contained"
                            startIcon={<PlayArrow />}
                            onClick={() => openExecuteDialog(tool)}
                          >
                            Execute Tool
                          </Button>
                        </Box>
                      </AccordionDetails>
                    </Accordion>
                  ))}
                </Box>
              )}

              {selectedTab === 'resources' && (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Available MCP Resources
                  </Typography>
                  <List>
                    {resources.map((resource) => (
                      <ListItem key={resource.uri} divider>
                        <ListItemIcon>
                          <Assignment />
                        </ListItemIcon>
                        <ListItemText
                          primary={resource.name}
                          secondary={
                            <Box>
                              <Typography variant="body2">{resource.description}</Typography>
                              <Typography variant="caption" color="text.secondary">
                                URI: {resource.uri} | Type: {resource.mimeType}
                              </Typography>
                            </Box>
                          }
                        />
                        <Button
                          size="small"
                          onClick={() => readResource(resource)}
                        >
                          Read
                        </Button>
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}

              {selectedTab === 'prompts' && (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Available MCP Prompts
                  </Typography>
                  {prompts.map((prompt) => (
                    <Card key={prompt.name} sx={{ mb: 2 }}>
                      <CardContent>
                        <Typography variant="h6">{prompt.name}</Typography>
                        <Typography variant="body2" color="text.secondary" paragraph>
                          {prompt.description}
                        </Typography>
                        <Typography variant="subtitle2">Arguments:</Typography>
                        {prompt.arguments.map((arg) => (
                          <Chip
                            key={arg.name}
                            label={`${arg.name}${arg.required ? ' *' : ''}`}
                            size="small"
                            sx={{ mr: 1, mb: 1 }}
                            color={arg.required ? 'primary' : 'default'}
                          />
                        ))}
                      </CardContent>
                    </Card>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Executions
              </Typography>
              {executions.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  No executions yet
                </Typography>
              ) : (
                <List>
                  {executions.slice(0, 5).map((execution) => (
                    <ListItem key={execution.id} divider>
                      <ListItemIcon>
                        {execution.status === 'completed' ? (
                          <CheckCircle color="success" />
                        ) : execution.status === 'failed' ? (
                          <Error color="error" />
                        ) : (
                          <Schedule color="warning" />
                        )}
                      </ListItemIcon>
                      <ListItemText
                        primary={execution.tool}
                        secondary={
                          <Box>
                            <Typography variant="caption">
                              {new Date(execution.timestamp).toLocaleString()}
                            </Typography>
                            {execution.error && (
                              <Typography variant="caption" color="error" display="block">
                                {execution.error}
                              </Typography>
                            )}
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tool Execution Dialog */}
      <Dialog
        open={executeDialogOpen}
        onClose={() => setExecuteDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Execute Tool: {selectedTool?.name}
        </DialogTitle>
        <DialogContent>
          {selectedTool && (
            <Box>
              <Typography variant="body2" color="text.secondary" paragraph>
                {selectedTool.description}
              </Typography>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" gutterBottom>
                Tool Arguments
              </Typography>
              {Object.entries(selectedTool.inputSchema.properties || {}).map(([propName, propSchema]: [string, any]) => (
                <Box key={propName}>
                  {renderInputField(
                    propName,
                    propSchema,
                    selectedTool.inputSchema.required?.includes(propName)
                  )}
                </Box>
              ))}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExecuteDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={executeTool}
            variant="contained"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : <PlayArrow />}
          >
            {loading ? 'Executing...' : 'Execute'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};