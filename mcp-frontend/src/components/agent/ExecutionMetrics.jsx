import React from 'react';
import { Activity, Clock, Zap, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

const ExecutionMetrics = ({ metrics, isExecuting }) => {
  const formatDuration = (ms) => {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  const formatTokensPerSecond = (tokens, duration) => {
    if (!tokens || !duration) return '0';
    return ((tokens / duration) * 1000).toFixed(1);
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'running': return <Activity className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'completed': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error': return <XCircle className="w-4 h-4 text-red-500" />;
      case 'idle': return <Clock className="w-4 h-4 text-gray-500" />;
      default: return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return 'text-blue-600 bg-blue-50 border-blue-500';
      case 'completed': return 'text-green-600 bg-green-50 border-green-500';
      case 'error': return 'text-red-600 bg-red-50 border-red-500';
      case 'idle': return 'text-gray-600 bg-gray-50 border-gray-500';
      default: return 'text-gray-600 bg-gray-50 border-gray-500';
    }
  };

  return (
    <div className="brutalist-card p-4">
      <h3 className="font-bold uppercase text-sm mb-3 tracking-wider flex items-center gap-2">
        <Zap className="w-4 h-4" />
        Execution Metrics
      </h3>

      {/* Current Status */}
      <div className={`p-3 border-4 border-black mb-4 ${getStatusColor(metrics.status)}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {getStatusIcon(metrics.status)}
            <span className="font-bold uppercase text-sm">
              {metrics.status || 'IDLE'}
            </span>
          </div>
          {isExecuting && (
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-current rounded-full animate-pulse" />
              <span className="text-xs font-mono">LIVE</span>
            </div>
          )}
        </div>
        
        {metrics.error && (
          <div className="mt-2 text-xs font-mono bg-white p-2 border-2 border-current">
            <div className="flex items-center gap-1 mb-1">
              <AlertTriangle className="w-3 h-3" />
              <span className="font-bold">ERROR:</span>
            </div>
            <div className="text-red-700">{metrics.error}</div>
          </div>
        )}
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        {/* Duration */}
        <div className="text-center p-3 bg-blue-50 border-4 border-blue-500">
          <div className="flex items-center justify-center gap-1 mb-1">
            <Clock className="w-4 h-4 text-blue-600" />
            <span className="font-bold text-xs uppercase text-blue-600">Duration</span>
          </div>
          <div className="font-bold text-lg text-blue-600 font-mono">
            {formatDuration(metrics.duration || 0)}
          </div>
        </div>

        {/* Tokens/sec */}
        <div className="text-center p-3 bg-green-50 border-4 border-green-500">
          <div className="flex items-center justify-center gap-1 mb-1">
            <Zap className="w-4 h-4 text-green-600" />
            <span className="font-bold text-xs uppercase text-green-600">Tokens/sec</span>
          </div>
          <div className="font-bold text-lg text-green-600 font-mono">
            {formatTokensPerSecond(metrics.tokensGenerated, metrics.duration)}
          </div>
        </div>
      </div>

      {/* Detailed Stats */}
      <div className="space-y-2 text-xs font-mono">
        <div className="flex justify-between p-2 bg-gray-50 border-2 border-gray-300">
          <span>Tokens Generated:</span>
          <span className="font-bold">{(metrics.tokensGenerated || 0).toLocaleString()}</span>
        </div>
        
        <div className="flex justify-between p-2 bg-gray-50 border-2 border-gray-300">
          <span>Tokens Input:</span>
          <span className="font-bold">{(metrics.tokensInput || 0).toLocaleString()}</span>
        </div>
        
        <div className="flex justify-between p-2 bg-gray-50 border-2 border-gray-300">
          <span>Retries:</span>
          <span className={`font-bold ${metrics.retries > 0 ? 'text-orange-600' : ''}`}>
            {metrics.retries || 0}
          </span>
        </div>
        
        <div className="flex justify-between p-2 bg-gray-50 border-2 border-gray-300">
          <span>Model:</span>
          <span className="font-bold">{metrics.model || 'Unknown'}</span>
        </div>
        
        <div className="flex justify-between p-2 bg-gray-50 border-2 border-gray-300">
          <span>Provider:</span>
          <span className="font-bold">{metrics.provider || 'Unknown'}</span>
        </div>
      </div>

      {/* Cost Estimation (if available) */}
      {metrics.estimatedCost && (
        <div className="mt-4 p-3 bg-yellow-50 border-4 border-yellow-500">
          <div className="flex items-center justify-between">
            <span className="font-bold text-xs uppercase text-yellow-600">Estimated Cost</span>
            <span className="font-bold text-lg text-yellow-600 font-mono">
              ${metrics.estimatedCost.toFixed(4)}
            </span>
          </div>
          <div className="text-xs text-yellow-600 mt-1">
            Input: ${(metrics.inputCost || 0).toFixed(4)} • 
            Output: ${(metrics.outputCost || 0).toFixed(4)}
          </div>
        </div>
      )}

      {/* Session Info */}
      <div className="mt-4 p-3 bg-gray-50 border-4 border-black">
        <h4 className="font-bold text-xs uppercase mb-2">Session Info</h4>
        <div className="space-y-1 text-xs font-mono">
          <div className="flex justify-between">
            <span>Session ID:</span>
            <span className="font-bold">{metrics.sessionId || 'N/A'}</span>
          </div>
          <div className="flex justify-between">
            <span>Started:</span>
            <span className="font-bold">
              {metrics.startTime ? new Date(metrics.startTime).toLocaleTimeString() : 'N/A'}
            </span>
          </div>
          <div className="flex justify-between">
            <span>Agent:</span>
            <span className="font-bold">{metrics.agent || 'N/A'}</span>
          </div>
        </div>
      </div>

      {/* Real-time Progress */}
      {isExecuting && (
        <div className="mt-4">
          <div className="flex items-center justify-between text-xs font-mono mb-2">
            <span>Processing...</span>
            <span>{Math.floor((Date.now() - (metrics.startTime || Date.now())) / 1000)}s</span>
          </div>
          <div className="w-full bg-gray-200 border-2 border-black h-2">
            <div className="bg-blue-500 h-full animate-pulse" style={{ width: '100%' }} />
          </div>
        </div>
      )}
    </div>
  );
};

export default ExecutionMetrics;

