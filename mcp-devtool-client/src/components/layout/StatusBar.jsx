import React from 'react'
import { useMCP } from '@/contexts/MCPContext'
import { useWebSocket } from '@/contexts/WebSocketContext'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'

const StatusBar = () => {
  const { metrics, logs, currentExecution } = useMCP()
  const { isConnected } = useWebSocket()

  const getLatestLog = () => {
    return logs.length > 0 ? logs[0] : null
  }

  const latestLog = getLatestLog()

  return (
    <div className="h-8 bg-muted/50 border-t border-border px-4 flex items-center justify-between text-xs">
      {/* Left side - Latest activity */}
      <div className="flex items-center space-x-4">
        {latestLog && (
          <>
            <span className="text-muted-foreground">
              {new Date(latestLog.timestamp).toLocaleTimeString()}
            </span>
            <span className={`font-medium ${
              latestLog.level === 'error' ? 'text-red-500' :
              latestLog.level === 'warning' ? 'text-yellow-500' :
              latestLog.level === 'info' ? 'text-blue-500' :
              'text-muted-foreground'
            }`}>
              {latestLog.message}
            </span>
          </>
        )}
      </div>

      {/* Right side - System metrics */}
      <div className="flex items-center space-x-4">
        {/* Connection status */}
        <Badge variant={isConnected ? 'default' : 'destructive'} className="text-xs">
          {isConnected ? 'Connected' : 'Disconnected'}
        </Badge>

        <Separator orientation="vertical" className="h-4" />

        {/* Execution status */}
        {currentExecution ? (
          <Badge variant="secondary" className="text-xs">
            Executing
          </Badge>
        ) : (
          <span className="text-muted-foreground">Ready</span>
        )}

        <Separator orientation="vertical" className="h-4" />

        {/* Metrics */}
        <div className="flex items-center space-x-3">
          <span className="text-muted-foreground">
            Tokens: {metrics.totalTokens.toLocaleString()}
          </span>
          <span className="text-muted-foreground">
            Avg: {metrics.avgResponseTime.toFixed(0)}ms
          </span>
          <span className="text-muted-foreground">
            Success: {(metrics.successRate * 100).toFixed(1)}%
          </span>
          {metrics.contradictionsApplied > 0 && (
            <span className="text-orange-500">
              🔥 {metrics.contradictionsApplied}
            </span>
          )}
        </div>

        <Separator orientation="vertical" className="h-4" />

        {/* Log count */}
        <span className="text-muted-foreground">
          Logs: {logs.length}
        </span>
      </div>
    </div>
  )
}

export default StatusBar

