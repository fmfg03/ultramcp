import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  Avatar,
  IconButton,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
  Alert,
  LinearProgress,
  Tab,
  Tabs,
  Badge,
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Refresh,
  Settings,
  Memory,
  Speed,
  Security,
  Analytics,
  SmartToy,
  CloudDownload,
  CheckCircle,
  Error,
  Schedule,
  TrendingUp,
  Assessment,
  People,
  Code,
  Shield,
  Storage,
  Add,
} from '@mui/icons-material';

// Service icons mapping
const SERVICE_ICONS = {
  cod: People,
  asterisk: Shield,
  blockoli: Code,
  voice: SmartToy,
  memory: Memory,
  deepclaude: Analytics,
  control_tower: Settings,
  database: Storage,
};

// Service colors
const SERVICE_COLORS = {
  cod: '#9C27B0',
  asterisk: '#F44336', 
  blockoli: '#2196F3',
  voice: '#4CAF50',
  memory: '#FF9800',
  deepclaude: '#3F51B5',
  control_tower: '#FF5722',
  database: '#607D8B',
};

const ClaudiaModern = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [agents, setAgents] = useState([]);
  const [templates, setTemplates] = useState({});
  const [executions, setExecutions] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [executeDialog, setExecuteDialog] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [taskInput, setTaskInput] = useState('');

  // Load data on mount and refresh every 10 seconds
  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [agentsRes, templatesRes, executionsRes, metricsRes] = await Promise.all([
        fetch('/api/agents'),
        fetch('/api/agents/templates'),
        fetch('/api/executions'),
        fetch('/api/metrics')
      ]);

      if (agentsRes.ok) setAgents(await agentsRes.json());
      if (templatesRes.ok) setTemplates(await templatesRes.json());
      if (executionsRes.ok) setExecutions(await executionsRes.json());
      if (metricsRes.ok) setMetrics(await metricsRes.json());
    } catch (err) {
      console.error('Error loading data:', err);
      setError('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const executeAgent = async () => {
    if (!selectedAgent) return;

    try {
      const response = await fetch(`/api/agents/${selectedAgent.id}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task: taskInput || selectedAgent.default_task,
          project_path: '/root/ultramcp'
        })
      });

      if (response.ok) {
        setExecuteDialog(false);
        setTaskInput('');
        setSelectedAgent(null);
        loadData();
      }
    } catch (err) {
      setError('Failed to execute agent');
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

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'running': return 'info';
      case 'failed': return 'error';
      default: return 'warning';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircle color="success" />;
      case 'running': return <CircularProgress size={20} />;
      case 'failed': return <Error color="error" />;
      default: return <Schedule color="warning" />;
    }
  };

  const MetricsCards = () => (
    <Grid container spacing={3} sx={{ mb: 4 }}>
      <Grid item xs={12} sm={6} md={3}>
        <Card elevation={0} sx={{ bgcolor: '#f8f9fa', border: '1px solid #e9ecef' }}>
          <CardContent sx={{ pb: '16px !important' }}>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Total Agents
                </Typography>
                <Typography variant="h4" component="div" fontWeight="bold">
                  {agents.length}
                </Typography>
              </Box>
              <Avatar sx={{ bgcolor: '#2196F3', width: 56, height: 56 }}>
                <SmartToy />
              </Avatar>
            </Box>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} sm={6} md={3}>
        <Card elevation={0} sx={{ bgcolor: '#f8f9fa', border: '1px solid #e9ecef' }}>
          <CardContent sx={{ pb: '16px !important' }}>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Executions
                </Typography>
                <Typography variant="h4" component="div" fontWeight="bold">
                  {metrics?.total_executions || 0}
                </Typography>
              </Box>
              <Avatar sx={{ bgcolor: '#4CAF50', width: 56, height: 56 }}>
                <PlayArrow />
              </Avatar>
            </Box>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} sm={6} md={3}>
        <Card elevation={0} sx={{ bgcolor: '#f8f9fa', border: '1px solid #e9ecef' }}>
          <CardContent sx={{ pb: '16px !important' }}>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Running Now
                </Typography>
                <Typography variant="h4" component="div" fontWeight="bold" color="info.main">
                  {metrics?.running_executions || 0}
                </Typography>
              </Box>
              <Avatar sx={{ bgcolor: '#FF9800', width: 56, height: 56 }}>
                <Speed />
              </Avatar>
            </Box>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} sm={6} md={3}>
        <Card elevation={0} sx={{ bgcolor: '#f8f9fa', border: '1px solid #e9ecef' }}>
          <CardContent sx={{ pb: '16px !important' }}>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Success Rate
                </Typography>
                <Typography variant="h4" component="div" fontWeight="bold" color="success.main">
                  {metrics ? Math.round(((metrics.status_breakdown?.completed || 0) / metrics.total_executions) * 100) : 0}%
                </Typography>
              </Box>
              <Avatar sx={{ bgcolor: '#4CAF50', width: 56, height: 56 }}>
                <TrendingUp />
              </Avatar>
            </Box>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const AgentsTab = () => (
    <Box>
      {agents.length === 0 ? (
        <Paper sx={{ p: 6, textAlign: 'center', bgcolor: '#fafafa' }}>
          <SmartToy sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h5" gutterBottom>
            No agents installed
          </Typography>
          <Typography color="textSecondary" paragraph>
            Install a template or create your first agent to get started
          </Typography>
          <Button variant="contained" startIcon={<CloudDownload />}>
            Browse Templates
          </Button>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {agents.map((agent) => (
            <Grid item xs={12} sm={6} md={4} key={agent.id}>
              <Card 
                elevation={0} 
                sx={{ 
                  border: '1px solid #e9ecef',
                  '&:hover': { 
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                    transform: 'translateY(-2px)',
                    transition: 'all 0.2s ease-in-out'
                  }
                }}
              >
                <CardContent>
                  <Box display="flex" alignItems="center" mb={2}>
                    <Avatar sx={{ bgcolor: '#2196F3', mr: 2 }}>
                      <SmartToy />
                    </Avatar>
                    <Box>
                      <Typography variant="h6" component="div">
                        {agent.name}
                      </Typography>
                      <Typography color="textSecondary" variant="body2">
                        Model: {agent.model}
                      </Typography>
                    </Box>
                  </Box>

                  <Typography variant="body2" color="textSecondary" paragraph>
                    {agent.default_task}
                  </Typography>

                  <Box display="flex" flexWrap="wrap" gap={1} mb={2}>
                    {agent.ultramcp_services?.slice(0, 3).map((service) => {
                      const ServiceIcon = SERVICE_ICONS[service] || Settings;
                      return (
                        <Chip
                          key={service}
                          label={service}
                          size="small"
                          icon={<ServiceIcon />}
                          sx={{ 
                            backgroundColor: SERVICE_COLORS[service] + '20',
                            color: SERVICE_COLORS[service],
                            fontWeight: 500
                          }}
                        />
                      );
                    })}
                    {agent.ultramcp_services?.length > 3 && (
                      <Chip
                        label={`+${agent.ultramcp_services.length - 3}`}
                        size="small"
                        variant="outlined"
                      />
                    )}
                  </Box>
                </CardContent>

                <CardActions>
                  <Button
                    fullWidth
                    variant="contained"
                    startIcon={<PlayArrow />}
                    onClick={() => {
                      setSelectedAgent(agent);
                      setTaskInput(agent.default_task);
                      setExecuteDialog(true);
                    }}
                  >
                    Execute Agent
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );

  const TemplatesTab = () => (
    <Grid container spacing={3}>
      {Object.entries(templates).map(([name, template]) => (
        <Grid item xs={12} sm={6} md={4} key={name}>
          <Card elevation={0} sx={{ border: '1px solid #e9ecef' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Avatar sx={{ bgcolor: '#9C27B0', mr: 2 }}>
                  <CloudDownload />
                </Avatar>
                <Box>
                  <Typography variant="h6" component="div">
                    {template.name}
                  </Typography>
                  <Typography color="textSecondary" variant="body2">
                    Template
                  </Typography>
                </Box>
              </Box>

              <Typography variant="body2" color="textSecondary" paragraph>
                {template.default_task}
              </Typography>

              <Box display="flex" flexWrap="wrap" gap={1} mb={2}>
                {template.ultramcp_services?.map((service) => {
                  const ServiceIcon = SERVICE_ICONS[service] || Settings;
                  return (
                    <Chip
                      key={service}
                      label={service}
                      size="small"
                      icon={<ServiceIcon />}
                      sx={{ 
                        backgroundColor: SERVICE_COLORS[service] + '20',
                        color: SERVICE_COLORS[service],
                        fontWeight: 500
                      }}
                    />
                  );
                })}
              </Box>
            </CardContent>

            <CardActions>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<CloudDownload />}
                onClick={() => installTemplate(name)}
              >
                Install Template
              </Button>
            </CardActions>
          </Card>
        </Grid>
      ))}
    </Grid>
  );

  const ExecutionsTab = () => (
    <Box>
      {executions.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center', bgcolor: '#fafafa' }}>
          <Assessment sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            No executions yet
          </Typography>
          <Typography color="textSecondary">
            Execute an agent to see results here
          </Typography>
        </Paper>
      ) : (
        <List>
          {executions.slice(0, 10).map((execution, index) => (
            <React.Fragment key={execution.id}>
              <ListItem>
                <ListItemIcon>
                  {getStatusIcon(execution.status)}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Box display="flex" alignItems="center" gap={1}>
                      <Typography variant="subtitle1">
                        {execution.agent_name}
                      </Typography>
                      <Chip
                        label={execution.status}
                        size="small"
                        color={getStatusColor(execution.status)}
                        variant="outlined"
                      />
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="body2" color="textSecondary">
                        {execution.task}
                      </Typography>
                      <Box display="flex" flexWrap="wrap" gap={0.5} mt={1}>
                        {execution.services_used?.map((service) => (
                          <Chip
                            key={service}
                            label={service}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: '0.7rem', height: 20 }}
                          />
                        ))}
                      </Box>
                    </Box>
                  }
                />
                <ListItemSecondaryAction>
                  <Typography variant="caption" color="textSecondary">
                    {new Date(execution.created_at).toLocaleString()}
                  </Typography>
                </ListItemSecondaryAction>
              </ListItem>
              {index < executions.length - 1 && <Divider />}
            </React.Fragment>
          ))}
        </List>
      )}
    </Box>
  );

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box>
          <Typography variant="h3" component="h1" fontWeight="bold" gutterBottom>
            Claudia AI Assistant
          </Typography>
          <Typography variant="subtitle1" color="textSecondary">
            Intelligent agent management with UltraMCP integration
          </Typography>
        </Box>
        
        <Box display="flex" gap={2}>
          <IconButton onClick={loadData} disabled={loading}>
            <Refresh />
          </IconButton>
          <Button variant="contained" startIcon={<Add />} disabled>
            Create Agent
          </Button>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Loading Progress */}
      {loading && <LinearProgress sx={{ mb: 3 }} />}

      {/* Metrics Cards */}
      <MetricsCards />

      {/* Tabs */}
      <Paper elevation={0} sx={{ border: '1px solid #e9ecef' }}>
        <Tabs
          value={activeTab}
          onChange={(e, newValue) => setActiveTab(newValue)}
          sx={{ borderBottom: '1px solid #e9ecef' }}
        >
          <Tab label={`My Agents (${agents.length})`} />
          <Tab label={`Templates (${Object.keys(templates).length})`} />
          <Tab label="Recent Executions" />
        </Tabs>

        <Box sx={{ p: 3 }}>
          {activeTab === 0 && <AgentsTab />}
          {activeTab === 1 && <TemplatesTab />}
          {activeTab === 2 && <ExecutionsTab />}
        </Box>
      </Paper>

      {/* Execute Agent Dialog */}
      <Dialog open={executeDialog} onClose={() => setExecuteDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          Execute Agent: {selectedAgent?.name}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Task Description"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={taskInput}
            onChange={(e) => setTaskInput(e.target.value)}
            placeholder="Enter the task you want the agent to perform..."
            sx={{ mt: 2 }}
          />
          
          {selectedAgent?.ultramcp_services && (
            <Box mt={3}>
              <Typography variant="subtitle2" gutterBottom>
                Services this agent will use:
              </Typography>
              <Box display="flex" flexWrap="wrap" gap={1}>
                {selectedAgent.ultramcp_services.map((service) => {
                  const ServiceIcon = SERVICE_ICONS[service] || Settings;
                  return (
                    <Chip
                      key={service}
                      label={service}
                      icon={<ServiceIcon />}
                      sx={{ 
                        backgroundColor: SERVICE_COLORS[service] + '20',
                        color: SERVICE_COLORS[service]
                      }}
                    />
                  );
                })}
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExecuteDialog(false)}>
            Cancel
          </Button>
          <Button onClick={executeAgent} variant="contained" startIcon={<PlayArrow />}>
            Execute Agent
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default ClaudiaModern;