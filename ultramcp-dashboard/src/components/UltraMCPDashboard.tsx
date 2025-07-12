import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Activity,
  Bot,
  Database,
  Shield,
  Brain,
  Mic,
  Zap,
  Code,
  Search,
  BookOpen,
  Globe,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertTriangle,
  Flame,
  Server,
  Users,
  Settings,
  BarChart3,
  Heart
} from 'lucide-react'
import { cn, getServiceStatusColor, formatNumber, formatDuration } from '@/lib/utils'

interface ServiceStatus {
  name: string
  status: 'healthy' | 'unhealthy' | 'unknown'
  port: number
  description: string
  icon: React.ComponentType<{ className?: string }>
  lastCheck: string
  responseTime?: number
  uptime?: number
  requests?: number
}

interface Metric {
  name: string
  value: number
  change: number
  unit: string
  icon: React.ComponentType<{ className?: string }>
}

const UltraMCPDashboard: React.FC = () => {
  const [services, setServices] = useState<ServiceStatus[]>([
    {
      name: 'Chain-of-Debate',
      status: 'healthy',
      port: 8001,
      description: 'Multi-LLM orchestration service',
      icon: Bot,
      lastCheck: '2 minutes ago',
      responseTime: 120,
      uptime: 99.8,
      requests: 1247
    },
    {
      name: 'Asterisk Security',
      status: 'healthy', 
      port: 8002,
      description: 'Security scanning and compliance',
      icon: Shield,
      lastCheck: '1 minute ago',
      responseTime: 89,
      uptime: 99.9,
      requests: 892
    },
    {
      name: 'Context7 Docs',
      status: 'healthy',
      port: 8003,
      description: 'Real-time documentation service',
      icon: BookOpen,
      lastCheck: '3 minutes ago',
      responseTime: 67,
      uptime: 99.7,
      requests: 2341
    },
    {
      name: 'Voice System',
      status: 'healthy',
      port: 8004,
      description: 'Voice processing with WebSocket',
      icon: Mic,
      lastCheck: '1 minute ago',
      responseTime: 145,
      uptime: 99.5,
      requests: 567
    },
    {
      name: 'DeepClaude Engine',
      status: 'healthy',
      port: 8006,
      description: 'Metacognitive reasoning service',
      icon: Brain,
      lastCheck: '2 minutes ago',
      responseTime: 203,
      uptime: 99.6,
      requests: 789
    },
    {
      name: 'Control Tower',
      status: 'healthy',
      port: 8007,
      description: 'Service orchestration hub',
      icon: Settings,
      lastCheck: '1 minute ago',
      responseTime: 95,
      uptime: 99.9,
      requests: 1876
    },
    {
      name: 'Claude Memory',
      status: 'healthy',
      port: 8009,
      description: 'Semantic code analysis',
      icon: Database,
      lastCheck: '2 minutes ago',
      responseTime: 167,
      uptime: 99.4,
      requests: 1432
    },
    {
      name: 'VoyageAI',
      status: 'healthy',
      port: 8010,
      description: 'Enterprise embeddings service',
      icon: Globe,
      lastCheck: '3 minutes ago',
      responseTime: 234,
      uptime: 99.3,
      requests: 3421
    },
    {
      name: 'Unified Docs',
      status: 'healthy',
      port: 8012,
      description: 'Documentation intelligence hub',
      icon: Search,
      lastCheck: '1 minute ago',
      responseTime: 78,
      uptime: 99.8,
      requests: 2987
    },
    {
      name: 'Blockoli Intelligence',
      status: 'unknown',
      port: 8080,
      description: 'Code intelligence service',
      icon: Code,
      lastCheck: '5 minutes ago',
      responseTime: 0,
      uptime: 98.9,
      requests: 567
    },
    {
      name: 'Supabase Database',
      status: 'healthy',
      port: 54322,
      description: 'PostgreSQL with vector extensions',
      icon: Database,
      lastCheck: '1 minute ago',
      responseTime: 45,
      uptime: 99.9,
      requests: 5432
    },
    {
      name: 'Open WebUI',
      status: 'healthy',
      port: 3000,
      description: 'AI chat interface with pipelines',
      icon: Users,
      lastCheck: '2 minutes ago',
      responseTime: 234,
      uptime: 99.7,
      requests: 987
    }
  ])

  const [metrics, setMetrics] = useState<Metric[]>([
    {
      name: 'Total Requests',
      value: 24876,
      change: 12.5,
      unit: '',
      icon: Activity
    },
    {
      name: 'Active Services',
      value: 11,
      change: 0,
      unit: '/12',
      icon: Server
    },
    {
      name: 'Avg Response Time',
      value: 134,
      change: -8.2,
      unit: 'ms',
      icon: Clock
    },
    {
      name: 'System Uptime',
      value: 99.6,
      change: 0.1,
      unit: '%',
      icon: Heart
    }
  ])

  const healthyServices = services.filter(s => s.status === 'healthy').length
  const totalServices = services.length
  const systemHealth = (healthyServices / totalServices) * 100

  return (
    <div className="ultramcp-container py-8 space-y-8">
      {/* Header */}
      <div className="ultramcp-flex-between">
        <div>
          <h1 className="text-4xl font-bold ultramcp-gradient-text">
            UltraMCP Dashboard
          </h1>
          <p className="text-lg ultramcp-body mt-2">
            Complete AI Platform Management & Monitoring
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <Badge variant="outline" className="text-sm">
            <Activity className="w-3 h-3 mr-1" />
            {healthyServices}/{totalServices} Services Active
          </Badge>
          <Button variant="outline" size="sm">
            <Settings className="w-4 h-4 mr-2" />
            Settings
          </Button>
        </div>
      </div>

      {/* System Health Overview */}
      <Card className="ultramcp-card">
        <CardHeader>
          <CardTitle className="ultramcp-flex-between">
            System Health Overview
            <Badge 
              variant={systemHealth >= 90 ? 'default' : systemHealth >= 75 ? 'secondary' : 'destructive'}
              className="text-xs"
            >
              {systemHealth.toFixed(1)}% Healthy
            </Badge>
          </CardTitle>
          <CardDescription>
            Real-time monitoring of all UltraMCP services and infrastructure
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Progress value={systemHealth} className="w-full h-3" />
          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
            {metrics.map((metric, index) => (
              <div key={index} className="ultramcp-metric-card">
                <div className="ultramcp-flex-between mb-2">
                  <metric.icon className="w-5 h-5 text-ultramcp-primary" />
                  <span className={cn(
                    "text-xs font-medium",
                    metric.change > 0 ? "text-ultramcp-success" : 
                    metric.change < 0 ? "text-ultramcp-error" : "text-ultramcp-warning"
                  )}>
                    {metric.change > 0 ? '+' : ''}{metric.change}%
                  </span>
                </div>
                <div className="space-y-1">
                  <p className="text-2xl font-bold text-foreground">
                    {formatNumber(metric.value)}{metric.unit}
                  </p>
                  <p className="text-xs ultramcp-caption">{metric.name}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Services Grid */}
      <Tabs defaultValue="services" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="services">Services</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="logs">Logs</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>
        
        <TabsContent value="services" className="space-y-6">
          <div className="ultramcp-grid">
            {services.map((service, index) => (
              <Card key={index} className="ultramcp-service-card group">
                <CardHeader className="pb-3">
                  <div className="ultramcp-flex-between">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 rounded-lg bg-ultramcp-primary/10">
                        <service.icon className="w-5 h-5 text-ultramcp-primary" />
                      </div>
                      <div>
                        <CardTitle className="text-base">{service.name}</CardTitle>
                        <CardDescription className="text-xs">
                          Port {service.port}
                        </CardDescription>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className={cn(
                        "ultramcp-status-indicator",
                        service.status === 'healthy' ? 'ultramcp-status-healthy' :
                        service.status === 'unhealthy' ? 'ultramcp-status-unhealthy' :
                        'ultramcp-status-unknown'
                      )} />
                      <Badge 
                        variant={service.status === 'healthy' ? 'default' : 
                                service.status === 'unhealthy' ? 'destructive' : 'secondary'}
                        className="text-xs capitalize"
                      >
                        {service.status}
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <p className="text-sm ultramcp-body mb-4">{service.description}</p>
                  <div className="space-y-2">
                    <div className="ultramcp-flex-between text-xs">
                      <span className="ultramcp-caption">Response Time</span>
                      <span className="font-medium">
                        {service.responseTime ? `${service.responseTime}ms` : 'N/A'}
                      </span>
                    </div>
                    <div className="ultramcp-flex-between text-xs">
                      <span className="ultramcp-caption">Uptime</span>
                      <span className="font-medium">
                        {service.uptime ? `${service.uptime}%` : 'N/A'}
                      </span>
                    </div>
                    <div className="ultramcp-flex-between text-xs">
                      <span className="ultramcp-caption">Requests</span>
                      <span className="font-medium">
                        {service.requests ? formatNumber(service.requests) : 'N/A'}
                      </span>
                    </div>
                    <div className="ultramcp-flex-between text-xs">
                      <span className="ultramcp-caption">Last Check</span>
                      <span className="font-medium">{service.lastCheck}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="ultramcp-chart-container">
              <CardHeader>
                <CardTitle>Service Performance</CardTitle>
                <CardDescription>Response times over the last 24 hours</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="ultramcp-flex-center h-48 text-ultramcp-caption">
                  <BarChart3 className="w-12 h-12 mr-3" />
                  Performance charts will be rendered here
                </div>
              </CardContent>
            </Card>
            
            <Card className="ultramcp-chart-container">
              <CardHeader>
                <CardTitle>Request Volume</CardTitle>
                <CardDescription>API calls and pipeline executions</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="ultramcp-flex-center h-48 text-ultramcp-caption">
                  <TrendingUp className="w-12 h-12 mr-3" />
                  Request volume charts will be rendered here
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="logs" className="space-y-6">
          <Card className="ultramcp-card">
            <CardHeader>
              <CardTitle>System Logs</CardTitle>
              <CardDescription>Real-time logs from all UltraMCP services</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="ultramcp-flex-center h-64 text-ultramcp-caption">
                <Activity className="w-12 h-12 mr-3" />
                Real-time log streaming will be implemented here
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings" className="space-y-6">
          <Card className="ultramcp-card">
            <CardHeader>
              <CardTitle>Dashboard Settings</CardTitle>
              <CardDescription>Configure monitoring and alerting preferences</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="ultramcp-flex-center h-64 text-ultramcp-caption">
                <Settings className="w-12 h-12 mr-3" />
                Settings panel will be implemented here
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default UltraMCPDashboard