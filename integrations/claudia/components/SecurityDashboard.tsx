import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CardHeader,
  LinearProgress,
  Chip,
  Alert,
  AlertTitle,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Tab,
  Tabs,
  TabPanel,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  Badge,
  Avatar
} from '@mui/material';
import {
  Security as SecurityIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as CheckCircleIcon,
  BugReport as BugReportIcon,
  Shield as ShieldIcon,
  Assessment as AssessmentIcon,
  Timeline as TimelineIcon,
  Refresh as RefreshIcon,
  PlayArrow as PlayArrowIcon,
  Stop as StopIcon,
  Visibility as VisibilityIcon,
  GetApp as GetAppIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar } from 'recharts';

// Types for security data
interface SecurityVulnerability {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  title: string;
  description: string;
  cwe_id?: string;
  owasp_category?: string;
  line_number?: number;
  code_snippet?: string;
  remediation?: string;
  confidence: number;
  file_path?: string;
}

interface SecurityScanResult {
  scan_id: string;
  timestamp: string;
  scan_type: string;
  risk_score: number;
  vulnerabilities: SecurityVulnerability[];
  compliance_status: Record<string, boolean>;
  scan_duration: number;
  lines_scanned: number;
  files_scanned: number;
}

interface SecurityMetrics {
  health_score: number;
  total_vulnerabilities: number;
  critical_vulnerabilities: number;
  high_vulnerabilities: number;
  medium_vulnerabilities: number;
  low_vulnerabilities: number;
  risk_score: number;
  compliance_percentage: number;
  scan_history: SecurityScanResult[];
  active_monitoring: boolean;
}

interface SecurityDebateResult {
  debate_id: string;
  timestamp: string;
  mode: string;
  participants: string[];
  consensus: string;
  secure_alternatives: string[];
  remediation_roadmap: any;
  confidence_score: number;
  security_improvement_score: number;
}

const SecurityDashboard: React.FC = () => {
  const [securityMetrics, setSecurityMetrics] = useState<SecurityMetrics | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [selectedVulnerability, setSelectedVulnerability] = useState<SecurityVulnerability | null>(null);
  const [securityDebates, setSecurityDebates] = useState<SecurityDebateResult[]>([]);
  const [monitoringActive, setMonitoringActive] = useState(false);

  // Mock data for demonstration
  useEffect(() => {
    // Simulate loading security metrics
    const mockMetrics: SecurityMetrics = {
      health_score: 7.5,
      total_vulnerabilities: 12,
      critical_vulnerabilities: 2,
      high_vulnerabilities: 3,
      medium_vulnerabilities: 5,
      low_vulnerabilities: 2,
      risk_score: 6.2,
      compliance_percentage: 78,
      active_monitoring: true,
      scan_history: [
        {
          scan_id: 'scan_001',
          timestamp: '2024-01-15T10:30:00Z',
          scan_type: 'codebase',
          risk_score: 6.2,
          vulnerabilities: [],
          compliance_status: { 'SOC2': true, 'GDPR': false, 'ISO27001': true },
          scan_duration: 45.2,
          lines_scanned: 15420,
          files_scanned: 156
        }
      ]
    };
    setSecurityMetrics(mockMetrics);
  }, []);

  const handleRunSecurityScan = async () => {
    setLoading(true);
    // Simulate security scan
    await new Promise(resolve => setTimeout(resolve, 3000));
    setLoading(false);
  };

  const handleStartSecurityDebate = async (topic: string) => {
    setLoading(true);
    // Simulate starting security debate
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    const mockDebate: SecurityDebateResult = {
      debate_id: `debate_${Date.now()}`,
      timestamp: new Date().toISOString(),
      mode: 'security_first',
      participants: ['Asterisk Scanner', 'DeepClaude Analyst', 'Local Privacy Expert'],
      consensus: 'Security vulnerabilities identified require immediate attention. Implementing secure alternatives recommended.',
      secure_alternatives: [
        'Implement parameterized queries to prevent SQL injection',
        'Add input validation and sanitization',
        'Use bcrypt for password hashing'
      ],
      remediation_roadmap: {},
      confidence_score: 0.89,
      security_improvement_score: 8.5
    };
    
    setSecurityDebates(prev => [mockDebate, ...prev]);
    setLoading(false);
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return '#d32f2f';
      case 'high': return '#f57c00';
      case 'medium': return '#fbc02d';
      case 'low': return '#388e3c';
      default: return '#757575';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical': return <ErrorIcon style={{ color: '#d32f2f' }} />;
      case 'high': return <WarningIcon style={{ color: '#f57c00' }} />;
      case 'medium': return <WarningIcon style={{ color: '#fbc02d' }} />;
      case 'low': return <CheckCircleIcon style={{ color: '#388e3c' }} />;
      default: return <BugReportIcon style={{ color: '#757575' }} />;
    }
  };

  const renderOverviewTab = () => (
    <Grid container spacing={3}>
      {/* Security Health Score */}
      <Grid item xs={12} md={4}>
        <Card>
          <CardHeader
            title="Security Health Score"
            avatar={<Avatar sx={{ bgcolor: securityMetrics?.health_score >= 8 ? '#4caf50' : securityMetrics?.health_score >= 6 ? '#ff9800' : '#f44336' }}>
              <ShieldIcon />
            </Avatar>}
          />
          <CardContent>
            <Typography variant="h3" component="div" gutterBottom>
              {securityMetrics?.health_score.toFixed(1)}/10
            </Typography>
            <LinearProgress 
              variant="determinate" 
              value={securityMetrics?.health_score * 10} 
              sx={{ height: 8, mb: 2 }}
              color={securityMetrics?.health_score >= 8 ? 'success' : securityMetrics?.health_score >= 6 ? 'warning' : 'error'}
            />
            <Typography variant="body2" color="text.secondary">
              {securityMetrics?.health_score >= 8 ? 'Excellent security posture' : 
               securityMetrics?.health_score >= 6 ? 'Good with room for improvement' : 
               'Needs immediate attention'}
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      {/* Risk Score */}
      <Grid item xs={12} md={4}>
        <Card>
          <CardHeader
            title="Risk Score"
            avatar={<Avatar sx={{ bgcolor: '#f44336' }}>
              <AssessmentIcon />
            </Avatar>}
          />
          <CardContent>
            <Typography variant="h3" component="div" gutterBottom>
              {securityMetrics?.risk_score.toFixed(1)}/10
            </Typography>
            <LinearProgress 
              variant="determinate" 
              value={securityMetrics?.risk_score * 10} 
              sx={{ height: 8, mb: 2 }}
              color="error"
            />
            <Typography variant="body2" color="text.secondary">
              Based on {securityMetrics?.total_vulnerabilities} vulnerabilities
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      {/* Compliance Status */}
      <Grid item xs={12} md={4}>
        <Card>
          <CardHeader
            title="Compliance Status"
            avatar={<Avatar sx={{ bgcolor: '#2196f3' }}>
              <SecurityIcon />
            </Avatar>}
          />
          <CardContent>
            <Typography variant="h3" component="div" gutterBottom>
              {securityMetrics?.compliance_percentage}%
            </Typography>
            <LinearProgress 
              variant="determinate" 
              value={securityMetrics?.compliance_percentage} 
              sx={{ height: 8, mb: 2 }}
              color={securityMetrics?.compliance_percentage >= 80 ? 'success' : 'warning'}
            />
            <Typography variant="body2" color="text.secondary">
              SOC2, GDPR, ISO27001 standards
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      {/* Vulnerability Breakdown */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardHeader 
            title="Vulnerability Breakdown"
            action={
              <Tooltip title="Run Security Scan">
                <IconButton onClick={handleRunSecurityScan} disabled={loading}>
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
            }
          />
          <CardContent>
            {loading ? (
              <Box display="flex" alignItems="center" justifyContent="center" height={200}>
                <LinearProgress sx={{ width: '100%' }} />
              </Box>
            ) : (
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Box display="flex" alignItems="center" mb={1}>
                    <ErrorIcon sx={{ color: '#d32f2f', mr: 1 }} />
                    <Typography variant="body2">Critical: {securityMetrics?.critical_vulnerabilities}</Typography>
                  </Box>
                  <Box display="flex" alignItems="center" mb={1}>
                    <WarningIcon sx={{ color: '#f57c00', mr: 1 }} />
                    <Typography variant="body2">High: {securityMetrics?.high_vulnerabilities}</Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box display="flex" alignItems="center" mb={1}>
                    <WarningIcon sx={{ color: '#fbc02d', mr: 1 }} />
                    <Typography variant="body2">Medium: {securityMetrics?.medium_vulnerabilities}</Typography>
                  </Box>
                  <Box display="flex" alignItems="center" mb={1}>
                    <CheckCircleIcon sx={{ color: '#388e3c', mr: 1 }} />
                    <Typography variant="body2">Low: {securityMetrics?.low_vulnerabilities}</Typography>
                  </Box>
                </Grid>
              </Grid>
            )}
          </CardContent>
        </Card>
      </Grid>

      {/* Security Actions */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardHeader title="Security Actions" />
          <CardContent>
            <List>
              <ListItem>
                <ListItemIcon>
                  <PlayArrowIcon />
                </ListItemIcon>
                <ListItemText primary="Run Security Scan" secondary="Scan codebase for vulnerabilities" />
                <IconButton onClick={handleRunSecurityScan} disabled={loading}>
                  <PlayArrowIcon />
                </IconButton>
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <AssessmentIcon />
                </ListItemIcon>
                <ListItemText primary="Start Security Debate" secondary="Multi-LLM security analysis" />
                <IconButton onClick={() => handleStartSecurityDebate('Code security review')}>
                  <PlayArrowIcon />
                </IconButton>
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <TimelineIcon />
                </ListItemIcon>
                <ListItemText primary="Security Monitoring" secondary={monitoringActive ? 'Active' : 'Inactive'} />
                <IconButton onClick={() => setMonitoringActive(!monitoringActive)}>
                  {monitoringActive ? <StopIcon color="error" /> : <PlayArrowIcon color="success" />}
                </IconButton>
              </ListItem>
            </List>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderVulnerabilitiesTab = () => (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">Security Vulnerabilities</Typography>
        <Button 
          variant="contained" 
          startIcon={<RefreshIcon />}
          onClick={handleRunSecurityScan}
          disabled={loading}
        >
          Scan Now
        </Button>
      </Box>

      {/* Mock vulnerabilities list */}
      <Grid container spacing={2}>
        {[
          {
            id: 'vuln_001',
            severity: 'critical' as const,
            title: 'SQL Injection Vulnerability',
            description: 'Unsanitized user input in database query',
            file_path: 'src/auth/login.py',
            line_number: 45,
            confidence: 0.95
          },
          {
            id: 'vuln_002', 
            severity: 'high' as const,
            title: 'Cross-Site Scripting (XSS)',
            description: 'Unescaped user input in HTML output',
            file_path: 'src/views/profile.py',
            line_number: 23,
            confidence: 0.87
          },
          {
            id: 'vuln_003',
            severity: 'medium' as const,
            title: 'Weak Password Hashing',
            description: 'Using MD5 for password hashing',
            file_path: 'src/auth/password.py',
            line_number: 67,
            confidence: 0.92
          }
        ].map((vuln) => (
          <Grid item xs={12} key={vuln.id}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="between">
                  <Box display="flex" alignItems="center" flex={1}>
                    {getSeverityIcon(vuln.severity)}
                    <Box ml={2}>
                      <Typography variant="h6" component="div">
                        {vuln.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {vuln.description}
                      </Typography>
                      <Typography variant="caption" display="block">
                        {vuln.file_path}:{vuln.line_number} • Confidence: {(vuln.confidence * 100).toFixed(0)}%
                      </Typography>
                    </Box>
                  </Box>
                  <Box>
                    <Chip 
                      label={vuln.severity.toUpperCase()} 
                      size="small"
                      sx={{ 
                        bgcolor: getSeverityColor(vuln.severity),
                        color: 'white',
                        mr: 1
                      }}
                    />
                    <IconButton onClick={() => setSelectedVulnerability(vuln)}>
                      <VisibilityIcon />
                    </IconButton>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );

  const renderDebatesTab = () => (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">Security Debates</Typography>
        <Button 
          variant="contained" 
          startIcon={<PlayArrowIcon />}
          onClick={() => handleStartSecurityDebate('Security architecture review')}
          disabled={loading}
        >
          Start New Debate
        </Button>
      </Box>

      <Grid container spacing={2}>
        {securityDebates.map((debate) => (
          <Grid item xs={12} key={debate.debate_id}>
            <Card>
              <CardHeader
                title={`Security Debate - ${debate.mode}`}
                subheader={new Date(debate.timestamp).toLocaleString()}
                action={
                  <Chip 
                    label={`Confidence: ${(debate.confidence_score * 100).toFixed(0)}%`}
                    size="small"
                    color="primary"
                  />
                }
              />
              <CardContent>
                <Typography variant="body2" paragraph>
                  <strong>Participants:</strong> {debate.participants.join(', ')}
                </Typography>
                <Typography variant="body2" paragraph>
                  <strong>Consensus:</strong> {debate.consensus}
                </Typography>
                {debate.secure_alternatives.length > 0 && (
                  <Box>
                    <Typography variant="body2" fontWeight="bold" gutterBottom>
                      Secure Alternatives:
                    </Typography>
                    <List dense>
                      {debate.secure_alternatives.map((alternative, index) => (
                        <ListItem key={index}>
                          <ListItemIcon>
                            <CheckCircleIcon color="success" />
                          </ListItemIcon>
                          <ListItemText primary={alternative} />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}
                <Box mt={2}>
                  <LinearProgress 
                    variant="determinate" 
                    value={debate.security_improvement_score * 10} 
                    sx={{ height: 6 }}
                    color="success"
                  />
                  <Typography variant="caption" color="text.secondary">
                    Security Improvement Score: {debate.security_improvement_score.toFixed(1)}/10
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );

  const renderComplianceTab = () => (
    <Box>
      <Typography variant="h6" gutterBottom>Compliance Status</Typography>
      
      <Grid container spacing={3}>
        {/* Compliance Standards */}
        {[
          { name: 'SOC 2', status: true, percentage: 85 },
          { name: 'GDPR', status: false, percentage: 72 },
          { name: 'ISO 27001', status: true, percentage: 90 },
          { name: 'HIPAA', status: false, percentage: 45 },
          { name: 'PCI DSS', status: true, percentage: 88 }
        ].map((standard) => (
          <Grid item xs={12} md={6} key={standard.name}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="between">
                  <Box display="flex" alignItems="center">
                    {standard.status ? 
                      <CheckCircleIcon color="success" /> : 
                      <ErrorIcon color="error" />
                    }
                    <Typography variant="h6" ml={1}>
                      {standard.name}
                    </Typography>
                  </Box>
                  <Typography variant="h6">
                    {standard.percentage}%
                  </Typography>
                </Box>
                <LinearProgress 
                  variant="determinate" 
                  value={standard.percentage} 
                  sx={{ mt: 2, height: 8 }}
                  color={standard.status ? 'success' : 'error'}
                />
                <Box mt={1}>
                  <Button 
                    size="small" 
                    onClick={() => handleStartSecurityDebate(`${standard.name} compliance analysis`)}
                  >
                    Analyze Compliance
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );

  if (!securityMetrics) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <LinearProgress sx={{ width: '50%' }} />
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box display="flex" alignItems="center" justifyContent="between" mb={3}>
        <Typography variant="h4" component="h1" gutterBottom>
          🛡️ Security Dashboard
        </Typography>
        <Box>
          <Badge color="error" badgeContent={securityMetrics.critical_vulnerabilities + securityMetrics.high_vulnerabilities}>
            <Chip 
              icon={<SecurityIcon />}
              label={monitoringActive ? 'Monitoring Active' : 'Monitoring Inactive'}
              color={monitoringActive ? 'success' : 'default'}
              variant={monitoringActive ? 'filled' : 'outlined'}
            />
          </Badge>
        </Box>
      </Box>

      {/* Critical Alerts */}
      {securityMetrics.critical_vulnerabilities > 0 && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <AlertTitle>Critical Security Issues Detected</AlertTitle>
          {securityMetrics.critical_vulnerabilities} critical vulnerabilities require immediate attention.
          <Button 
            size="small" 
            sx={{ ml: 2 }}
            onClick={() => handleStartSecurityDebate('Critical vulnerability remediation')}
          >
            Start Security Debate
          </Button>
        </Alert>
      )}

      {/* Navigation Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)}>
          <Tab label="Overview" />
          <Tab label="Vulnerabilities" />
          <Tab label="Security Debates" />
          <Tab label="Compliance" />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      {activeTab === 0 && renderOverviewTab()}
      {activeTab === 1 && renderVulnerabilitiesTab()}
      {activeTab === 2 && renderDebatesTab()}
      {activeTab === 3 && renderComplianceTab()}

      {/* Vulnerability Detail Dialog */}
      <Dialog
        open={selectedVulnerability !== null}
        onClose={() => setSelectedVulnerability(null)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {selectedVulnerability && (
            <Box display="flex" alignItems="center">
              {getSeverityIcon(selectedVulnerability.severity)}
              <Typography variant="h6" ml={1}>
                {selectedVulnerability.title}
              </Typography>
            </Box>
          )}
        </DialogTitle>
        <DialogContent>
          {selectedVulnerability && (
            <Box>
              <Typography variant="body1" paragraph>
                {selectedVulnerability.description}
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                <strong>File:</strong> {selectedVulnerability.file_path}:{selectedVulnerability.line_number}
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                <strong>Confidence:</strong> {(selectedVulnerability.confidence * 100).toFixed(0)}%
              </Typography>
              {selectedVulnerability.remediation && (
                <Box>
                  <Typography variant="body2" fontWeight="bold" gutterBottom>
                    Remediation:
                  </Typography>
                  <Typography variant="body2">
                    {selectedVulnerability.remediation}
                  </Typography>
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedVulnerability(null)}>Close</Button>
          <Button 
            variant="contained" 
            onClick={() => {
              handleStartSecurityDebate(`Fix ${selectedVulnerability?.title}`);
              setSelectedVulnerability(null);
            }}
          >
            Start Security Debate
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SecurityDashboard;