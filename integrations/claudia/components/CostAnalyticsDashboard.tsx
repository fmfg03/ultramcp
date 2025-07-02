/**
 * CostAnalyticsDashboard Component
 * 
 * Comprehensive cost analysis and optimization dashboard for UltraMCP
 * Features: Real-time cost tracking, savings calculator, optimization recommendations
 */

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Progress,
  Separator,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
  Alert,
  AlertDescription,
  AlertTitle,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui';
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  PieChart,
  BarChart3,
  Calculator,
  Lightbulb,
  AlertTriangle,
  CheckCircle2,
  Target,
  Calendar,
  Filter,
  Download,
  RefreshCw,
  Zap,
  Shield,
  Clock,
  Activity
} from 'lucide-react';

// =============================================================================
// TYPES
// =============================================================================

interface CostBreakdown {
  local: number;
  api: number;
  total: number;
  period: 'hour' | 'day' | 'week' | 'month';
}

interface ModelCost {
  modelName: string;
  type: 'local' | 'api';
  requests: number;
  tokens: number;
  cost: number;
  avgCostPerRequest: number;
  percentage: number;
  color: string;
}

interface SavingsCalculation {
  totalAPIEquivalent: number;
  actualCost: number;
  savings: number;
  savingsPercentage: number;
  localRequestCount: number;
  apiRequestCount: number;
}

interface OptimizationRecommendation {
  id: string;
  type: 'cost_reduction' | 'efficiency' | 'privacy' | 'performance';
  title: string;
  description: string;
  potentialSavings: number;
  impact: 'low' | 'medium' | 'high';
  effort: 'low' | 'medium' | 'high';
  icon: React.ReactNode;
}

interface UsageTrend {
  date: Date;
  localCost: number;
  apiCost: number;
  requests: number;
  savings: number;
}

interface CostAnalyticsProps {
  currentCosts: CostBreakdown;
  modelCosts: ModelCost[];
  savingsCalculation: SavingsCalculation;
  usageTrends: UsageTrend[];
  recommendations: OptimizationRecommendation[];
  onExport: (format: 'csv' | 'json' | 'pdf') => void;
  onRefresh: () => void;
}

// =============================================================================
// SAMPLE DATA
// =============================================================================

const sampleModelCosts: ModelCost[] = [
  {
    modelName: 'Qwen 2.5 14B',
    type: 'local',
    requests: 147,
    tokens: 58800,
    cost: 0.0,
    avgCostPerRequest: 0.0,
    percentage: 23.5,
    color: '#8B5CF6'
  },
  {
    modelName: 'Llama 3.1 8B',
    type: 'local',
    requests: 203,
    tokens: 81200,
    cost: 0.0,
    avgCostPerRequest: 0.0,
    percentage: 32.4,
    color: '#10B981'
  },
  {
    modelName: 'Mistral 7B',
    type: 'local',
    requests: 312,
    tokens: 124800,
    cost: 0.0,
    avgCostPerRequest: 0.0,
    percentage: 49.8,
    color: '#F59E0B'
  },
  {
    modelName: 'GPT-4',
    type: 'api',
    requests: 23,
    tokens: 15600,
    cost: 0.468,
    avgCostPerRequest: 0.0203,
    percentage: 3.7,
    color: '#3B82F6'
  },
  {
    modelName: 'Claude 3 Sonnet',
    type: 'api',
    requests: 15,
    tokens: 9800,
    cost: 0.147,
    avgCostPerRequest: 0.0098,
    percentage: 2.4,
    color: '#EF4444'
  }
];

const sampleRecommendations: OptimizationRecommendation[] = [
  {
    id: '1',
    type: 'cost_reduction',
    title: 'Increase Local Model Usage',
    description: 'Route 90% of simple queries to local models instead of API models',
    potentialSavings: 1200,
    impact: 'high',
    effort: 'low',
    icon: <Zap className="h-4 w-4" />
  },
  {
    id: '2',
    type: 'efficiency',
    title: 'Batch Similar Requests',
    description: 'Group similar requests to improve processing efficiency',
    potentialSavings: 300,
    impact: 'medium',
    effort: 'medium',
    icon: <BarChart3 className="h-4 w-4" />
  },
  {
    id: '3',
    type: 'privacy',
    title: 'Enable Privacy-First Mode',
    description: 'Process sensitive data only with local models',
    potentialSavings: 800,
    impact: 'high',
    effort: 'low',
    icon: <Shield className="h-4 w-4" />
  },
  {
    id: '4',
    type: 'performance',
    title: 'Cache Frequent Patterns',
    description: 'Cache results for frequently repeated queries',
    potentialSavings: 450,
    impact: 'medium',
    effort: 'high',
    icon: <Clock className="h-4 w-4" />
  }
];

// =============================================================================
// COST BREAKDOWN CHART COMPONENT
// =============================================================================

const CostBreakdownChart: React.FC<{ modelCosts: ModelCost[]; totalCost: number }> = ({ 
  modelCosts, 
  totalCost 
}) => {
  const localModels = modelCosts.filter(m => m.type === 'local');
  const apiModels = modelCosts.filter(m => m.type === 'api');
  
  const totalLocalRequests = localModels.reduce((sum, m) => sum + m.requests, 0);
  const totalAPIRequests = apiModels.reduce((sum, m) => sum + m.requests, 0);
  const totalRequests = totalLocalRequests + totalAPIRequests;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <PieChart className="h-5 w-5" />
          Cost Breakdown
        </CardTitle>
        <CardDescription>
          Distribution of costs across local and API models
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Summary Cards */}
        <div className="grid grid-cols-2 gap-4">
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-green-600">
                  ${totalCost.toFixed(4)}
                </div>
                <div className="text-sm text-muted-foreground">Total Cost</div>
              </div>
              <DollarSign className="h-8 w-8 text-green-600" />
            </div>
          </Card>
          
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-blue-600">
                  {((totalLocalRequests / totalRequests) * 100).toFixed(0)}%
                </div>
                <div className="text-sm text-muted-foreground">Local Usage</div>
              </div>
              <Shield className="h-8 w-8 text-blue-600" />
            </div>
          </Card>
        </div>

        {/* Model Cost Breakdown */}
        <div className="space-y-3">
          <h4 className="font-semibold">Cost by Model</h4>
          {modelCosts.map((model) => (
            <div key={model.modelName} className="space-y-2">
              <div className="flex justify-between text-sm">
                <div className="flex items-center gap-2">
                  <div 
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: model.color }}
                  />
                  <span>{model.modelName}</span>
                  <Badge variant={model.type === 'local' ? 'default' : 'secondary'}>
                    {model.type}
                  </Badge>
                </div>
                <div className="text-right">
                  <div className="font-semibold">
                    ${model.cost.toFixed(4)}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {model.requests} requests
                  </div>
                </div>
              </div>
              <Progress 
                value={model.percentage} 
                className="h-2"
                style={{ 
                  backgroundColor: `${model.color}20`
                }}
              />
            </div>
          ))}
        </div>

        {/* Local vs API Summary */}
        <Separator />
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="font-semibold text-green-600">Local Models</div>
            <div>Requests: {totalLocalRequests}</div>
            <div>Cost: $0.0000</div>
            <div>Avg/Request: $0.00</div>
          </div>
          <div>
            <div className="font-semibold text-blue-600">API Models</div>
            <div>Requests: {totalAPIRequests}</div>
            <div>Cost: ${apiModels.reduce((sum, m) => sum + m.cost, 0).toFixed(4)}</div>
            <div>Avg/Request: ${(apiModels.reduce((sum, m) => sum + m.cost, 0) / totalAPIRequests || 0).toFixed(4)}</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// =============================================================================
// SAVINGS CALCULATOR COMPONENT
// =============================================================================

const SavingsCalculator: React.FC<{ savings: SavingsCalculation }> = ({ savings }) => {
  const monthlyExtrapolation = savings.savings * 30; // Assuming daily savings
  const yearlyExtrapolation = monthlyExtrapolation * 12;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calculator className="h-5 w-5" />
          Savings Calculator
        </CardTitle>
        <CardDescription>
          Cost savings from using local models vs API-only approach
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Main Savings Display */}
        <div className="text-center space-y-2">
          <div className="text-4xl font-bold text-green-600">
            ${savings.savings.toFixed(2)}
          </div>
          <div className="text-lg text-muted-foreground">
            Saved Today
          </div>
          <Badge variant="outline" className="text-green-600">
            {savings.savingsPercentage.toFixed(1)}% savings
          </Badge>
        </div>

        {/* Breakdown */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="space-y-2">
            <div className="font-semibold">If Using API Only:</div>
            <div>Total Cost: ${savings.totalAPIEquivalent.toFixed(4)}</div>
            <div>Local Requests: {savings.localRequestCount}</div>
            <div>API Requests: {savings.apiRequestCount}</div>
          </div>
          <div className="space-y-2">
            <div className="font-semibold">Actual Hybrid Cost:</div>
            <div>Total Cost: ${savings.actualCost.toFixed(4)}</div>
            <div className="text-green-600">Savings: ${savings.savings.toFixed(4)}</div>
            <div className="text-xs text-muted-foreground">
              Local models: Free • API models: Paid
            </div>
          </div>
        </div>

        <Separator />

        {/* Projections */}
        <div className="space-y-3">
          <h4 className="font-semibold">Projected Savings</h4>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-xl font-bold text-green-600">
                ${monthlyExtrapolation.toFixed(0)}
              </div>
              <div className="text-sm text-muted-foreground">Monthly</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-green-600">
                ${yearlyExtrapolation.toFixed(0)}
              </div>
              <div className="text-sm text-muted-foreground">Yearly</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-blue-600">
                {((savings.localRequestCount / (savings.localRequestCount + savings.apiRequestCount)) * 100).toFixed(0)}%
              </div>
              <div className="text-sm text-muted-foreground">Local Usage</div>
            </div>
          </div>
        </div>

        {/* ROI Information */}
        <Alert>
          <TrendingUp className="h-4 w-4" />
          <AlertTitle>Return on Investment</AlertTitle>
          <AlertDescription>
            UltraMCP's local models pay for themselves in infrastructure costs within the first month
            through API cost savings alone.
          </AlertDescription>
        </Alert>
      </CardContent>
    </Card>
  );
};

// =============================================================================
// OPTIMIZATION RECOMMENDATIONS COMPONENT
// =============================================================================

const OptimizationRecommendations: React.FC<{ recommendations: OptimizationRecommendation[] }> = ({ 
  recommendations 
}) => {
  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high': return 'text-green-600';
      case 'medium': return 'text-yellow-600';
      case 'low': return 'text-gray-600';
      default: return 'text-gray-600';
    }
  };

  const getEffortColor = (effort: string) => {
    switch (effort) {
      case 'low': return 'bg-green-100 text-green-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'high': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const totalPotentialSavings = recommendations.reduce((sum, r) => sum + r.potentialSavings, 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Lightbulb className="h-5 w-5" />
          Optimization Recommendations
        </CardTitle>
        <CardDescription>
          AI-powered suggestions to reduce costs and improve efficiency
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Summary */}
        <Alert>
          <Target className="h-4 w-4" />
          <AlertTitle>Potential Annual Savings</AlertTitle>
          <AlertDescription>
            Implementing all recommendations could save up to ${totalPotentialSavings * 365} per year.
          </AlertDescription>
        </Alert>

        {/* Recommendations List */}
        <div className="space-y-4">
          {recommendations.map((rec) => (
            <motion.div
              key={rec.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="border rounded-lg p-4 space-y-3"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3 flex-1">
                  <div className="mt-1">{rec.icon}</div>
                  <div className="space-y-1 flex-1">
                    <div className="font-semibold">{rec.title}</div>
                    <div className="text-sm text-muted-foreground">
                      {rec.description}
                    </div>
                  </div>
                </div>
                
                <div className="text-right">
                  <div className="text-lg font-bold text-green-600">
                    ${rec.potentialSavings}/year
                  </div>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-1">
                    <span className="text-sm text-muted-foreground">Impact:</span>
                    <Badge 
                      variant="outline" 
                      className={getImpactColor(rec.impact)}
                    >
                      {rec.impact}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="text-sm text-muted-foreground">Effort:</span>
                    <Badge className={getEffortColor(rec.effort)}>
                      {rec.effort}
                    </Badge>
                  </div>
                </div>
                
                <Button size="sm" variant="outline">
                  Implement
                </Button>
              </div>
            </motion.div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

// =============================================================================
// USAGE TRENDS COMPONENT
// =============================================================================

const UsageTrends: React.FC<{ trends: UsageTrend[] }> = ({ trends }) => {
  const [timeRange, setTimeRange] = useState('7d');
  
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Usage Trends
            </CardTitle>
            <CardDescription>
              Historical cost and usage patterns
            </CardDescription>
          </div>
          
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="24h">Last 24h</SelectItem>
              <SelectItem value="7d">Last 7 days</SelectItem>
              <SelectItem value="30d">Last 30 days</SelectItem>
              <SelectItem value="90d">Last 90 days</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Summary Stats */}
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {trends.reduce((sum, t) => sum + t.requests, 0)}
            </div>
            <div className="text-sm text-muted-foreground">Total Requests</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              ${trends.reduce((sum, t) => sum + t.savings, 0).toFixed(2)}
            </div>
            <div className="text-sm text-muted-foreground">Total Savings</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              ${trends.reduce((sum, t) => sum + t.localCost + t.apiCost, 0).toFixed(4)}
            </div>
            <div className="text-sm text-muted-foreground">Total Cost</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">
              {trends.length > 1 ? 
                ((trends[trends.length - 1].savings - trends[0].savings) / trends[0].savings * 100).toFixed(1) + '%'
                : '0%'
              }
            </div>
            <div className="text-sm text-muted-foreground">Savings Growth</div>
          </div>
        </div>

        {/* Trend Visualization (simplified) */}
        <div className="space-y-2">
          <h4 className="font-semibold">Daily Savings Trend</h4>
          {trends.slice(-7).map((trend, index) => (
            <div key={index} className="flex items-center gap-4">
              <div className="w-16 text-sm text-muted-foreground">
                {trend.date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              </div>
              <div className="flex-1">
                <Progress 
                  value={(trend.savings / Math.max(...trends.map(t => t.savings))) * 100} 
                  className="h-3"
                />
              </div>
              <div className="w-20 text-sm font-semibold text-green-600">
                ${trend.savings.toFixed(2)}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

// =============================================================================
// MAIN COST ANALYTICS DASHBOARD COMPONENT
// =============================================================================

const CostAnalyticsDashboard: React.FC<CostAnalyticsProps> = ({
  currentCosts,
  modelCosts = sampleModelCosts,
  savingsCalculation,
  usageTrends,
  recommendations = sampleRecommendations,
  onExport,
  onRefresh
}) => {
  const [timeFilter, setTimeFilter] = useState('today');

  // Calculate sample savings if not provided
  const defaultSavings: SavingsCalculation = savingsCalculation || {
    totalAPIEquivalent: 18.45,
    actualCost: 0.615,
    savings: 17.835,
    savingsPercentage: 96.7,
    localRequestCount: 662,
    apiRequestCount: 38
  };

  const defaultCurrentCosts: CostBreakdown = currentCosts || {
    local: 0.0,
    api: 0.615,
    total: 0.615,
    period: 'day'
  };

  return (
    <div className="h-full flex flex-col space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Cost Analytics Dashboard</h2>
          <p className="text-muted-foreground">
            Real-time cost tracking and optimization insights
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Select value={timeFilter} onValueChange={setTimeFilter}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="today">Today</SelectItem>
              <SelectItem value="week">This Week</SelectItem>
              <SelectItem value="month">This Month</SelectItem>
              <SelectItem value="quarter">This Quarter</SelectItem>
            </SelectContent>
          </Select>
          
          <Button variant="outline" onClick={onRefresh}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          
          <Button onClick={() => onExport('csv')}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-green-600">
                  ${defaultSavings.savings.toFixed(2)}
                </div>
                <div className="text-sm text-muted-foreground">Today's Savings</div>
              </div>
              <TrendingDown className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-blue-600">
                  {defaultSavings.savingsPercentage.toFixed(1)}%
                </div>
                <div className="text-sm text-muted-foreground">Cost Reduction</div>
              </div>
              <Target className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-purple-600">
                  {((defaultSavings.localRequestCount / (defaultSavings.localRequestCount + defaultSavings.apiRequestCount)) * 100).toFixed(0)}%
                </div>
                <div className="text-sm text-muted-foreground">Local Usage</div>
              </div>
              <Shield className="h-8 w-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-orange-600">
                  ${(defaultSavings.savings * 365).toFixed(0)}
                </div>
                <div className="text-sm text-muted-foreground">Annual Projection</div>
              </div>
              <Calendar className="h-8 w-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="overview" className="flex-1">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="breakdown">Breakdown</TabsTrigger>
          <TabsTrigger value="trends">Trends</TabsTrigger>
          <TabsTrigger value="optimization">Optimization</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <CostBreakdownChart 
              modelCosts={modelCosts} 
              totalCost={defaultCurrentCosts.total} 
            />
            <SavingsCalculator savings={defaultSavings} />
          </div>
        </TabsContent>

        <TabsContent value="breakdown" className="space-y-4">
          <CostBreakdownChart 
            modelCosts={modelCosts} 
            totalCost={defaultCurrentCosts.total} 
          />
        </TabsContent>

        <TabsContent value="trends" className="space-y-4">
          {usageTrends && usageTrends.length > 0 ? (
            <UsageTrends trends={usageTrends} />
          ) : (
            <Card>
              <CardContent className="p-8 text-center">
                <Activity className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Trend Data Available</h3>
                <p className="text-muted-foreground">
                  Usage trends will appear here as you use the system over time.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="optimization" className="space-y-4">
          <OptimizationRecommendations recommendations={recommendations} />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default CostAnalyticsDashboard;