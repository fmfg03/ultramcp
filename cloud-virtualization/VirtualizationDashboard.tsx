import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Cloud,
  Server,
  Container,
  Globe,
  Zap,
  Plus,
  Settings,
  BarChart3,
  Activity,
  Cpu,
  HardDrive,
  Network,
  MapPin,
  Layers,
  Shield
} from 'lucide-react'
import { cn, formatBytes, formatNumber } from '@/lib/utils'

interface CloudInstance {
  id: string
  name: string
  type: 'vm' | 'container' | 'sandbox'
  provider: 'aws' | 'gcp' | 'azure' | 'local'
  region: string
  status: 'running' | 'stopped' | 'pending' | 'error'
  specs: {
    cpu: number
    memory: number
    disk: number
  }
  metrics: {
    cpu_usage: number
    memory_usage: number
    disk_usage: number
    network_in: number
    network_out: number
  }
  services: string[]
  uptime: number
  cost_per_hour?: number
}

interface CloudProvider {
  name: string
  icon: React.ComponentType<{ className?: string }>
  color: string
  instances: number
  regions: string[]
  total_cost: number
}

const VirtualizationDashboard: React.FC = () => {
  const [instances, setInstances] = useState<CloudInstance[]>([
    {
      id: 'aws-cod-1',
      name: 'ultramcp-cod-us-east',
      type: 'vm',
      provider: 'aws',
      region: 'us-east-1',
      status: 'running',
      specs: { cpu: 4, memory: 8192, disk: 100 },
      metrics: { cpu_usage: 45.2, memory_usage: 67.8, disk_usage: 23.1, network_in: 1024, network_out: 2048 },
      services: ['chain-of-debate', 'control-tower'],
      uptime: 99.9,
      cost_per_hour: 0.12
    },
    {
      id: 'gcp-memory-1', 
      name: 'ultramcp-memory-europe',
      type: 'vm',
      provider: 'gcp',
      region: 'europe-west1',
      status: 'running',
      specs: { cpu: 2, memory: 4096, disk: 50 },
      metrics: { cpu_usage: 32.1, memory_usage: 54.3, disk_usage: 45.7, network_in: 512, network_out: 1024 },
      services: ['claude-memory', 'voyage-ai'],
      uptime: 99.7,
      cost_per_hour: 0.08
    },
    {
      id: 'local-sandbox-1',
      name: 'security-sandbox-01',
      type: 'sandbox',
      provider: 'local',
      region: 'datacenter-1',
      status: 'running',
      specs: { cpu: 1, memory: 1024, disk: 20 },
      metrics: { cpu_usage: 15.5, memory_usage: 32.1, disk_usage: 12.3, network_in: 256, network_out: 128 },
      services: ['asterisk-security'],
      uptime: 100.0
    }
  ])

  const [providers, setProviders] = useState<CloudProvider[]>([
    {
      name: 'AWS',
      icon: Cloud,
      color: '#FF9900',
      instances: 5,
      regions: ['us-east-1', 'us-west-2', 'eu-west-1'],
      total_cost: 2.34
    },
    {
      name: 'Google Cloud',
      icon: Globe,
      color: '#4285F4', 
      instances: 3,
      regions: ['europe-west1', 'asia-southeast1'],
      total_cost: 1.78
    },
    {
      name: 'Local',
      icon: Server,
      color: '#6B7280',
      instances: 4,
      regions: ['datacenter-1'],
      total_cost: 0.00
    }
  ])

  const totalInstances = instances.length
  const runningInstances = instances.filter(i => i.status === 'running').length
  const totalMonthlyCost = instances.reduce((sum, i) => sum + (i.cost_per_hour || 0) * 24 * 30, 0)
  const avgCpuUsage = instances.reduce((sum, i) => sum + i.metrics.cpu_usage, 0) / instances.length

  const getProviderColor = (provider: string) => {
    switch (provider) {
      case 'aws': return 'bg-orange-500'
      case 'gcp': return 'bg-blue-500'
      case 'azure': return 'bg-cyan-500'
      case 'local': return 'bg-gray-500'
      default: return 'bg-gray-400'
    }
  }

  const getInstanceTypeIcon = (type: string) => {
    switch (type) {
      case 'vm': return Server
      case 'container': return Container
      case 'sandbox': return Shield
      default: return Server
    }
  }

  return (
    <div className="ultramcp-container py-8 space-y-8">
      {/* Header */}
      <div className="ultramcp-flex-between">
        <div>
          <h1 className="text-4xl font-bold ultramcp-gradient-text">
            Cloud Virtualization
          </h1>
          <p className="text-lg ultramcp-body mt-2">
            Gestión distribuida de infraestructura UltraMCP
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <Badge variant="outline" className="text-sm">
            <Activity className="w-3 h-3 mr-1" />
            {runningInstances}/{totalInstances} Activas
          </Badge>
          <Button variant="outline" size="sm">
            <Plus className="w-4 h-4 mr-2" />
            Nueva Instancia
          </Button>
        </div>
      </div>

      {/* Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="ultramcp-metric-card">
          <CardContent className="p-6">
            <div className="ultramcp-flex-between">
              <Server className="w-8 h-8 text-ultramcp-primary" />
              <span className="text-2xl font-bold">{totalInstances}</span>
            </div>
            <p className="text-sm ultramcp-caption mt-2">Total Instancias</p>
          </CardContent>
        </Card>

        <Card className="ultramcp-metric-card">
          <CardContent className="p-6">
            <div className="ultramcp-flex-between">
              <Cpu className="w-8 h-8 text-ultramcp-accent" />
              <span className="text-2xl font-bold">{avgCpuUsage.toFixed(1)}%</span>
            </div>
            <p className="text-sm ultramcp-caption mt-2">CPU Promedio</p>
          </CardContent>
        </Card>

        <Card className="ultramcp-metric-card">
          <CardContent className="p-6">
            <div className="ultramcp-flex-between">
              <Globe className="w-8 h-8 text-ultramcp-success" />
              <span className="text-2xl font-bold">{providers.length}</span>
            </div>
            <p className="text-sm ultramcp-caption mt-2">Proveedores</p>
          </CardContent>
        </Card>

        <Card className="ultramcp-metric-card">
          <CardContent className="p-6">
            <div className="ultramcp-flex-between">
              <BarChart3 className="w-8 h-8 text-ultramcp-warning" />
              <span className="text-2xl font-bold">${totalMonthlyCost.toFixed(0)}</span>
            </div>
            <p className="text-sm ultramcp-caption mt-2">Costo Mensual</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="instances" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="instances">Instancias</TabsTrigger>
          <TabsTrigger value="providers">Proveedores</TabsTrigger>
          <TabsTrigger value="monitoring">Monitoreo</TabsTrigger>
          <TabsTrigger value="scaling">Auto-scaling</TabsTrigger>
        </TabsList>

        <TabsContent value="instances" className="space-y-6">
          <div className="ultramcp-grid">
            {instances.map((instance) => {
              const IconComponent = getInstanceTypeIcon(instance.type)
              return (
                <Card key={instance.id} className="ultramcp-service-card">
                  <CardHeader className="pb-3">
                    <div className="ultramcp-flex-between">
                      <div className="flex items-center space-x-3">
                        <div className={cn(
                          "p-2 rounded-lg",
                          getProviderColor(instance.provider),
                          "bg-opacity-10"
                        )}>
                          <IconComponent className="w-5 h-5" />
                        </div>
                        <div>
                          <CardTitle className="text-base">{instance.name}</CardTitle>
                          <CardDescription className="text-xs">
                            {instance.provider.toUpperCase()} • {instance.region}
                          </CardDescription>
                        </div>
                      </div>
                      <Badge 
                        variant={instance.status === 'running' ? 'default' : 'destructive'}
                        className="text-xs capitalize"
                      >
                        {instance.status}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-0">
                    {/* Specs */}
                    <div className="grid grid-cols-3 gap-4 mb-4">
                      <div className="text-center">
                        <div className="text-lg font-bold">{instance.specs.cpu}</div>
                        <div className="text-xs ultramcp-caption">vCPUs</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold">{formatBytes(instance.specs.memory * 1024 * 1024)}</div>
                        <div className="text-xs ultramcp-caption">RAM</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold">{instance.specs.disk}GB</div>
                        <div className="text-xs ultramcp-caption">Storage</div>
                      </div>
                    </div>

                    {/* Metrics */}
                    <div className="space-y-3">
                      <div>
                        <div className="ultramcp-flex-between text-xs mb-1">
                          <span>CPU</span>
                          <span>{instance.metrics.cpu_usage.toFixed(1)}%</span>
                        </div>
                        <Progress value={instance.metrics.cpu_usage} className="h-2" />
                      </div>
                      <div>
                        <div className="ultramcp-flex-between text-xs mb-1">
                          <span>Memory</span>
                          <span>{instance.metrics.memory_usage.toFixed(1)}%</span>
                        </div>
                        <Progress value={instance.metrics.memory_usage} className="h-2" />
                      </div>
                      <div>
                        <div className="ultramcp-flex-between text-xs mb-1">
                          <span>Disk</span>
                          <span>{instance.metrics.disk_usage.toFixed(1)}%</span>
                        </div>
                        <Progress value={instance.metrics.disk_usage} className="h-2" />
                      </div>
                    </div>

                    {/* Services */}
                    <div className="mt-4">
                      <div className="text-xs ultramcp-caption mb-2">Servicios:</div>
                      <div className="flex flex-wrap gap-1">
                        {instance.services.map((service, idx) => (
                          <Badge key={idx} variant="outline" className="text-xs">
                            {service}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    {/* Cost */}
                    {instance.cost_per_hour && (
                      <div className="mt-4 ultramcp-flex-between text-xs">
                        <span className="ultramcp-caption">Costo/hora:</span>
                        <span className="font-medium">${instance.cost_per_hour.toFixed(3)}</span>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </TabsContent>

        <TabsContent value="providers" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {providers.map((provider, index) => (
              <Card key={index} className="ultramcp-service-card">
                <CardHeader>
                  <div className="ultramcp-flex-between">
                    <div className="flex items-center space-x-3">
                      <provider.icon className="w-8 h-8" style={{ color: provider.color }} />
                      <div>
                        <CardTitle className="text-lg">{provider.name}</CardTitle>
                        <CardDescription>{provider.instances} instancias</CardDescription>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <div className="ultramcp-flex-between text-sm mb-2">
                        <span>Regiones activas:</span>
                        <span>{provider.regions.length}</span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {provider.regions.map((region, idx) => (
                          <Badge key={idx} variant="outline" className="text-xs">
                            <MapPin className="w-3 h-3 mr-1" />
                            {region}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    
                    {provider.total_cost > 0 && (
                      <div className="ultramcp-flex-between">
                        <span className="text-sm ultramcp-caption">Costo/día:</span>
                        <span className="text-lg font-bold text-ultramcp-primary">
                          ${provider.total_cost.toFixed(2)}
                        </span>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="monitoring" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="ultramcp-chart-container">
              <CardHeader>
                <CardTitle>Uso de Recursos</CardTitle>
                <CardDescription>CPU y memoria en tiempo real</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="ultramcp-flex-center h-48 text-ultramcp-caption">
                  <Activity className="w-12 h-12 mr-3" />
                  Gráficos de monitoreo en tiempo real
                </div>
              </CardContent>
            </Card>
            
            <Card className="ultramcp-chart-container">
              <CardHeader>
                <CardTitle>Distribución Geográfica</CardTitle>
                <CardDescription>Instancias por región</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="ultramcp-flex-center h-48 text-ultramcp-caption">
                  <Globe className="w-12 h-12 mr-3" />
                  Mapa de distribución global
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="scaling" className="space-y-6">
          <Card className="ultramcp-card">
            <CardHeader>
              <CardTitle>Políticas de Auto-scaling</CardTitle>
              <CardDescription>Configuración de escalado automático</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="ultramcp-flex-center h-64 text-ultramcp-caption">
                <Zap className="w-12 h-12 mr-3" />
                Panel de configuración de auto-scaling
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default VirtualizationDashboard