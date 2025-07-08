import React, { useState, useEffect } from 'react';
import { Button } from './components/ui/button';
import { Card, CardContent } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { 
  Settings, 
  Code, 
  Brain, 
  BarChart3, 
  Bot,
  Menu,
  X,
  Wifi,
  WifiOff
} from 'lucide-react';

import MCPToolSelectorShadcn from './components/code/MCPToolSelectorShadcn';
import SimpleOrchestrationTestShadcn from './components/SimpleOrchestrationTestShadcn';
import UltraMCPControlTowerShadcn from './components/UltraMCPControlTowerShadcn';
import ClaudiaShadcn from './components/claudia/ClaudiaShadcn';

function App() {
  const [currentView, setCurrentView] = useState('control-tower');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('Connecting...');
  const [isConnected, setIsConnected] = useState(false);

  const views = [
    { 
      id: 'control-tower', 
      label: 'Control Tower', 
      icon: Settings,
      description: 'System management and monitoring'
    },
    { 
      id: 'orchestration', 
      label: 'Orchestration', 
      icon: BarChart3,
      description: 'Service coordination and workflows'
    },
    { 
      id: 'mcp-tools', 
      label: 'MCP Tools', 
      icon: Code,
      description: 'Model Context Protocol tools'
    },
    { 
      id: 'claudia', 
      label: 'Claudia', 
      icon: Bot,
      description: 'AI Assistant with agent management'
    }
  ];

  // Check backend connection
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const response = await fetch('/api/health');
        const data = await response.json();
        setConnectionStatus(`Connected - ${data.status}`);
        setIsConnected(true);
      } catch (err) {
        setConnectionStatus('Backend disconnected');
        setIsConnected(false);
      }
    };

    checkConnection();
    const interval = setInterval(checkConnection, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const currentViewData = views.find(view => view.id === currentView);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center">
          <div className="mr-4 hidden md:flex">
            <div className="mr-6 flex items-center space-x-2">
              <Brain className="h-7 w-7 text-primary" />
              <span className="hidden font-bold text-lg sm:inline-block">
                UltraMCP Supreme Stack
              </span>
            </div>
            <nav className="flex items-center space-x-6 text-sm font-medium">
              {views.map((view) => {
                const Icon = view.icon;
                return (
                  <Button
                    key={view.id}
                    variant={currentView === view.id ? "default" : "ghost"}
                    size="sm"
                    onClick={() => setCurrentView(view.id)}
                    className="flex items-center space-x-2"
                  >
                    <Icon className="h-4 w-4" />
                    <span>{view.label}</span>
                  </Button>
                );
              })}
            </nav>
          </div>
          
          {/* Mobile menu button */}
          <Button
            variant="ghost"
            size="sm"
            className="md:hidden"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>

          <div className="flex flex-1 items-center justify-between space-x-2 md:justify-end">
            <div className="w-full flex-1 md:w-auto md:flex-none">
              {/* Space for search or other controls */}
            </div>
            <nav className="flex items-center space-x-2">
              <Badge variant="outline" className="hidden sm:flex">
                v2.0.0
              </Badge>
              <div className="flex items-center space-x-2">
                {isConnected ? (
                  <Wifi className="h-4 w-4 text-green-500" />
                ) : (
                  <WifiOff className="h-4 w-4 text-red-500" />
                )}
                <span className="text-xs text-muted-foreground hidden lg:inline">
                  {connectionStatus}
                </span>
              </div>
            </nav>
          </div>
        </div>
      </header>

      {/* Mobile Navigation */}
      {mobileMenuOpen && (
        <div className="border-b bg-background md:hidden">
          <nav className="container flex flex-col space-y-2 py-4">
            {views.map((view) => {
              const Icon = view.icon;
              return (
                <Button
                  key={view.id}
                  variant={currentView === view.id ? "default" : "ghost"}
                  onClick={() => {
                    setCurrentView(view.id);
                    setMobileMenuOpen(false);
                  }}
                  className="justify-start h-auto p-3"
                >
                  <div className="flex items-center space-x-3">
                    <Icon className="h-5 w-5" />
                    <div className="text-left">
                      <div className="font-medium">{view.label}</div>
                      <div className="text-xs text-muted-foreground">{view.description}</div>
                    </div>
                  </div>
                </Button>
              );
            })}
          </nav>
        </div>
      )}

      {/* Main Content */}
      <main className="container mx-auto py-6">
        {/* Current View Header */}
        <div className="mb-6">
          <div className="flex items-center space-x-3 mb-2">
            {currentViewData && (
              <>
                <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-primary/10">
                  <currentViewData.icon className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold tracking-tight">{currentViewData.label}</h1>
                  <p className="text-muted-foreground">
                    {currentViewData.description}
                  </p>
                </div>
              </>
            )}
          </div>
        </div>

        {/* View Content */}
        <div className="space-y-6">
          {currentView === 'control-tower' && <UltraMCPControlTowerShadcn />}
          {currentView === 'orchestration' && <SimpleOrchestrationTestShadcn />}
          {currentView === 'mcp-tools' && <MCPToolSelectorShadcn />}
          {currentView === 'claudia' && <ClaudiaShadcn />}
        </div>
      </main>
    </div>
  );
}

export default App;