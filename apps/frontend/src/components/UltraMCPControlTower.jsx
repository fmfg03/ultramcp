import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Chip,
  LinearProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  Tooltip,
  Badge
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Pause,
  Speed,
  Security,
  MonetizationOn,
  Psychology,
  Warning,
  CheckCircle,
  Error,
  Info,
  Refresh,
  Settings,
  Visibility,
  VisibilityOff,
  Chat,
  Dashboard,
  Timeline,
  Analytics,
  Memory,
  Storage,
  CloudOff,
  Api,
  Computer,
  Group,
  Assignment,
  PausePresentation
} from '@mui/icons-material';
import { io } from 'socket.io-client';

const UltraMCPControlTower = () => {
  // Core State
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [systemStatus, setSystemStatus] = useState('idle');
  
  // UI State
  const [currentView, setCurrentView] = useState('overview');
  const [interventionDialog, setInterventionDialog] = useState(false);
  const [newEvaluationDialog, setNewEvaluationDialog] = useState(false);
  
  // Real-time Data
  const [activeDebates, setActiveDebates] = useState([]);
  const [liveEvents, setLiveEvents] = useState([]);
  const [systemMetrics, setSystemMetrics] = useState({
    localModelsActive: 5,
    apiModelsActive: 3,
    totalCost: 0.0,
    privacyScore: 100,
    avgConfidence: 0.85
  });
  
  // Local Models State
  const [localModels, setLocalModels] = useState([
    { name: 'Qwen 2.5 14B', status: 'active', confidence: 0.92, role: 'Strategic Analyst', requests: 147 },
    { name: 'Llama 3.1 8B', status: 'active', confidence: 0.88, role: 'Balanced Reasoner', requests: 203 },
    { name: 'Qwen Coder 7B', status: 'active', confidence: 0.95, role: 'Technical Specialist', requests: 89 },
    { name: 'Mistral 7B', status: 'active', confidence: 0.83, role: 'Rapid Analyst', requests: 312 },
    { name: 'DeepSeek Coder 6.7B', status: 'active', confidence: 0.91, role: 'System Architect', requests: 156 }
  ]);
  
  // Evaluation Form State
  const [evaluationForm, setEvaluationForm] = useState({
    topic: '',
    mode: 'cod-local',
    maxRounds: 3,
    confidenceThreshold: 0.75,
    enablePrivacyMode: true,
    selectedModels: []
  });
  
  // Current Intervention
  const [currentIntervention, setCurrentIntervention] = useState(null);
  
  const eventsRef = useRef(null);

  // Initialize WebSocket Connection
  useEffect(() => {
    const socketConnection = io('ws://sam.chat:8001', {
      transports: ['websocket']
    });
    
    socketConnection.on('connect', () => {
      setConnected(true);
      setSocket(socketConnection);
    });
    
    socketConnection.on('disconnect', () => {
      setConnected(false);
    });
    
    // Real-time event handlers
    socketConnection.on('debate_update', (data) => {
      setActiveDebates(prev => {
        const updated = prev.filter(d => d.id !== data.debate_id);
        return [...updated, data];
      });
      addLiveEvent('debate_update', `Debate ${data.debate_id}: ${data.status}`, data.confidence);
    });
    
    socketConnection.on('model_response', (data) => {
      addLiveEvent('model_response', `${data.model}: ${data.response.substring(0, 100)}...`, data.confidence);
    });
    
    socketConnection.on('system_metrics', (metrics) => {
      setSystemMetrics(metrics);
    });
    
    socketConnection.on('confidence_alert', (alert) => {
      if (alert.confidence < evaluationForm.confidenceThreshold) {
        setCurrentIntervention(alert);
        setInterventionDialog(true);
      }
    });
    
    return () => socketConnection.close();
  }, []);

  const addLiveEvent = (type, message, confidence) => {
    const event = {
      id: Date.now(),
      type,
      message,
      confidence,
      timestamp: new Date().toISOString(),
      needsAttention: confidence < 0.8
    };
    
    setLiveEvents(prev => [event, ...prev.slice(0, 49)]); // Keep last 50 events
    
    // Auto-scroll to top
    if (eventsRef.current) {
      eventsRef.current.scrollTop = 0;
    }
  };

  const launchEvaluation = () => {
    if (!socket) return;
    
    const evaluationConfig = {
      ...evaluationForm,
      id: `eval_${Date.now()}`,
      timestamp: new Date().toISOString()
    };
    
    socket.emit('launch_evaluation', evaluationConfig);
    
    addLiveEvent('evaluation_launched', `New evaluation: ${evaluationForm.topic}`, 1.0);
    setNewEvaluationDialog(false);
    
    // Reset form
    setEvaluationForm({
      topic: '',
      mode: 'cod-local',
      maxRounds: 3,
      confidenceThreshold: 0.75,
      enablePrivacyMode: true,
      selectedModels: []
    });
  };

  const handleIntervention = (action) => {
    if (!socket || !currentIntervention) return;
    
    socket.emit('human_intervention', {
      debate_id: currentIntervention.debate_id,
      action,
      timestamp: new Date().toISOString()
    });
    
    addLiveEvent('intervention', `Human intervention: ${action}`, 1.0);
    setInterventionDialog(false);
    setCurrentIntervention(null);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'success';
      case 'warning': return 'warning';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.9) return 'success';
    if (confidence >= 0.75) return 'warning';
    return 'error';
  };

  const formatCurrency = (amount) => `$${amount.toFixed(4)}`;

  return (
    <Box sx={{ flexGrow: 1, padding: 3, backgroundColor: '#f5f5f5', minHeight: '100vh' }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 'bold', color: '#1976d2' }}>
          🚀 UltraMCP Control Tower
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Chip 
            icon={connected ? <CheckCircle /> : <Error />}
            label={connected ? 'Connected' : 'Disconnected'}
            color={connected ? 'success' : 'error'}
          />
          <Button
            variant="contained"
            startIcon={<PlayArrow />}
            onClick={() => setNewEvaluationDialog(true)}
            size="large"
          >
            Launch Evaluation
          </Button>
        </Box>
      </Box>

      {/* System Overview Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Computer sx={{ mr: 1, color: '#4caf50' }} />
                <Typography variant="h6">Local Models</Typography>
              </Box>
              <Typography variant="h4" color="primary">
                {systemMetrics.localModelsActive}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Active & Ready
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <MonetizationOn sx={{ mr: 1, color: '#ff9800' }} />
                <Typography variant="h6">Cost Today</Typography>
              </Box>
              <Typography variant="h4" color="primary">
                {formatCurrency(systemMetrics.totalCost)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                98% Savings vs API
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Security sx={{ mr: 1, color: '#2196f3' }} />
                <Typography variant="h6">Privacy Score</Typography>
              </Box>
              <Typography variant="h4" color="primary">
                {systemMetrics.privacyScore}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                100% Local Processing
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Psychology sx={{ mr: 1, color: '#9c27b0' }} />
                <Typography variant="h6">Avg Confidence</Typography>
              </Box>
              <Typography variant="h4" color="primary">
                {(systemMetrics.avgConfidence * 100).toFixed(1)}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                High Quality Results
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Local Models Status */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '400px' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                🤖 Local Model Status
              </Typography>
              <TableContainer sx={{ maxHeight: 320 }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Model</TableCell>
                      <TableCell>Role</TableCell>
                      <TableCell>Confidence</TableCell>
                      <TableCell>Requests</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {localModels.map((model, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Chip 
                              size="small" 
                              color={getStatusColor(model.status)}
                              sx={{ mr: 1, width: 8, height: 8 }}
                            />
                            {model.name}
                          </Box>
                        </TableCell>
                        <TableCell>{model.role}</TableCell>
                        <TableCell>
                          <Chip 
                            label={`${(model.confidence * 100).toFixed(0)}%`}
                            color={getConfidenceColor(model.confidence)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{model.requests}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Live Event Feed */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '400px' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                📡 Live Event Feed
              </Typography>
              <Box 
                ref={eventsRef}
                sx={{ 
                  height: 320, 
                  overflow: 'auto',
                  backgroundColor: '#000',
                  color: '#00ff00',
                  fontFamily: 'monospace',
                  fontSize: '0.8rem',
                  padding: 1,
                  borderRadius: 1
                }}
              >
                {liveEvents.map((event) => (
                  <Box key={event.id} sx={{ mb: 0.5 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Typography 
                        variant="caption" 
                        sx={{ color: '#888', mr: 1 }}
                      >
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </Typography>
                      <Chip 
                        label={event.type}
                        size="small"
                        sx={{ mr: 1, height: 16, fontSize: '0.6rem' }}
                        color={event.needsAttention ? 'warning' : 'default'}
                      />
                      <Typography variant="caption">
                        {event.message}
                      </Typography>
                    </Box>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Active Debates */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                🎭 Active Debates & Evaluations
              </Typography>
              {activeDebates.length === 0 ? (
                <Alert severity="info">
                  No active debates. Click "Launch Evaluation" to start a new one.
                </Alert>
              ) : (
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>ID</TableCell>
                        <TableCell>Topic</TableCell>
                        <TableCell>Mode</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Confidence</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {activeDebates.map((debate) => (
                        <TableRow key={debate.id}>
                          <TableCell>{debate.id}</TableCell>
                          <TableCell>{debate.topic}</TableCell>
                          <TableCell>
                            <Chip label={debate.mode} size="small" />
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={debate.status}
                              color={getStatusColor(debate.status)}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <LinearProgress 
                                variant="determinate" 
                                value={debate.confidence * 100}
                                sx={{ width: 60, mr: 1 }}
                                color={getConfidenceColor(debate.confidence)}
                              />
                              {(debate.confidence * 100).toFixed(0)}%
                            </Box>
                          </TableCell>
                          <TableCell>
                            <IconButton size="small">
                              <Visibility />
                            </IconButton>
                            <IconButton size="small">
                              <PausePresentation />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Launch New Evaluation Dialog */}
      <Dialog 
        open={newEvaluationDialog} 
        onClose={() => setNewEvaluationDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>🚀 Launch New Evaluation</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Evaluation Topic"
                value={evaluationForm.topic}
                onChange={(e) => setEvaluationForm({...evaluationForm, topic: e.target.value})}
                placeholder="e.g., Should we migrate to microservices architecture?"
              />
            </Grid>
            
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Mode</InputLabel>
                <Select
                  value={evaluationForm.mode}
                  onChange={(e) => setEvaluationForm({...evaluationForm, mode: e.target.value})}
                >
                  <MenuItem value="cod-local">🤖 Local Only (100% Privacy)</MenuItem>
                  <MenuItem value="cod-hybrid">🔀 Hybrid (Local + API)</MenuItem>
                  <MenuItem value="cod-privacy">🔒 Privacy First</MenuItem>
                  <MenuItem value="cod-cost-optimized">💰 Cost Optimized</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={6}>
              <TextField
                fullWidth
                type="number"
                label="Max Rounds"
                value={evaluationForm.maxRounds}
                onChange={(e) => setEvaluationForm({...evaluationForm, maxRounds: parseInt(e.target.value)})}
              />
            </Grid>
            
            <Grid item xs={6}>
              <TextField
                fullWidth
                type="number"
                label="Confidence Threshold"
                value={evaluationForm.confidenceThreshold}
                onChange={(e) => setEvaluationForm({...evaluationForm, confidenceThreshold: parseFloat(e.target.value)})}
                inputProps={{ min: 0, max: 1, step: 0.05 }}
              />
            </Grid>
            
            <Grid item xs={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={evaluationForm.enablePrivacyMode}
                    onChange={(e) => setEvaluationForm({...evaluationForm, enablePrivacyMode: e.target.checked})}
                  />
                }
                label="Enable Privacy Mode"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewEvaluationDialog(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={launchEvaluation}
            disabled={!evaluationForm.topic}
          >
            Launch
          </Button>
        </DialogActions>
      </Dialog>

      {/* Intervention Dialog */}
      <Dialog
        open={interventionDialog}
        onClose={() => setInterventionDialog(false)}
      >
        <DialogTitle>⚠️ Low Confidence - Intervention Required</DialogTitle>
        <DialogContent>
          {currentIntervention && (
            <Box>
              <Alert severity="warning" sx={{ mb: 2 }}>
                Confidence score below threshold: {(currentIntervention.confidence * 100).toFixed(1)}%
              </Alert>
              <Typography variant="body1" gutterBottom>
                <strong>Debate:</strong> {currentIntervention.debate_id}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {currentIntervention.message}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => handleIntervention('continue')}>
            Continue Anyway
          </Button>
          <Button onClick={() => handleIntervention('pause')}>
            Pause Debate
          </Button>
          <Button 
            variant="contained" 
            onClick={() => handleIntervention('override')}
          >
            Manual Override
          </Button>
        </DialogActions>
      </Dialog>

      {/* Floating Action Button for Quick Actions */}
      <Fab
        color="primary"
        aria-label="quick-action"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={() => setNewEvaluationDialog(true)}
      >
        <PlayArrow />
      </Fab>
    </Box>
  );
};

export default UltraMCPControlTower;