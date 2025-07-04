import React, { useState, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AppBar, Toolbar, Typography, Button, Box, Container } from '@mui/material';
import { Dashboard, Build, Psychology, Assessment, AutoAwesome } from '@mui/icons-material';

import MCPToolSelector from './components/code/MCPToolSelector';
import SimpleOrchestrationTest from './components/SimpleOrchestrationTest';
import UltraMCPControlTower from './components/UltraMCPControlTower';
import ClaudiaIntegration from './components/claudia/ClaudiaIntegration';

// Material-UI theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    h4: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 500,
    },
  },
});

function App() {
  const [message, setMessage] = useState('');
  const [currentView, setCurrentView] = useState('control-tower'); // 'control-tower', 'orchestration', 'tools', 'claudia'

  // Fetch backend status on load
  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => setMessage(`Connected - ${data.status}`))
      .catch(err => setMessage('Backend disconnected'));
  }, []);

  const handleViewChange = (view) => {
    setCurrentView(view);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ flexGrow: 1, minHeight: '100vh' }}>
        {/* Navigation */}
        <AppBar position="static" elevation={1}>
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              🚀 UltraMCP Hybrid System
            </Typography>
            
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                color="inherit"
                startIcon={<Dashboard />}
                onClick={() => handleViewChange('control-tower')}
                variant={currentView === 'control-tower' ? 'outlined' : 'text'}
                sx={{ 
                  backgroundColor: currentView === 'control-tower' ? 'rgba(255,255,255,0.1)' : 'transparent',
                  border: currentView === 'control-tower' ? '1px solid rgba(255,255,255,0.3)' : 'none'
                }}
              >
                Control Tower
              </Button>
              
              <Button
                color="inherit"
                startIcon={<Psychology />}
                onClick={() => handleViewChange('orchestration')}
                variant={currentView === 'orchestration' ? 'outlined' : 'text'}
                sx={{ 
                  backgroundColor: currentView === 'orchestration' ? 'rgba(255,255,255,0.1)' : 'transparent',
                  border: currentView === 'orchestration' ? '1px solid rgba(255,255,255,0.3)' : 'none'
                }}
              >
                Orchestration
              </Button>
              
              <Button
                color="inherit"
                startIcon={<Build />}
                onClick={() => handleViewChange('tools')}
                variant={currentView === 'tools' ? 'outlined' : 'text'}
                sx={{ 
                  backgroundColor: currentView === 'tools' ? 'rgba(255,255,255,0.1)' : 'transparent',
                  border: currentView === 'tools' ? '1px solid rgba(255,255,255,0.3)' : 'none'
                }}
              >
                MCP Tools
              </Button>
              
              <Button
                color="inherit"
                startIcon={<AutoAwesome />}
                onClick={() => handleViewChange('claudia')}
                variant={currentView === 'claudia' ? 'outlined' : 'text'}
                sx={{ 
                  backgroundColor: currentView === 'claudia' ? 'rgba(255,255,255,0.1)' : 'transparent',
                  border: currentView === 'claudia' ? '1px solid rgba(255,255,255,0.3)' : 'none'
                }}
              >
                Claudia
              </Button>
            </Box>
            
            <Typography variant="caption" sx={{ ml: 2, opacity: 0.8 }}>
              {message}
            </Typography>
          </Toolbar>
        </AppBar>

        {/* Main Content */}
        <Box component="main" sx={{ flexGrow: 1 }}>
          {currentView === 'control-tower' && <UltraMCPControlTower />}
          
          {currentView === 'orchestration' && (
            <Container maxWidth="xl" sx={{ py: 3 }}>
              <SimpleOrchestrationTest />
            </Container>
          )}
          
          {currentView === 'tools' && (
            <Container maxWidth="xl" sx={{ py: 3 }}>
              <Box sx={{
                backgroundColor: 'white',
                borderRadius: 2,
                boxShadow: 1,
                p: 3
              }}>
                <Typography variant="h4" component="h2" gutterBottom>
                  MCP Tools Integration
                </Typography>
                <MCPToolSelector />
              </Box>
            </Container>
          )}
          
          {currentView === 'claudia' && <ClaudiaIntegration />}
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default App;