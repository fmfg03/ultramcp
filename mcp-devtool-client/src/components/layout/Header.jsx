import React from 'react'
import { useTheme } from 'next-themes'
import { useMCP } from '@/contexts/MCPContext'
import { useWebSocket } from '@/contexts/WebSocketContext'
import { Button } from '@/components/ui/button'
import { 
  Sun, 
  Moon, 
  Maximize2, 
  Minimize2,
  Wifi,
  WifiOff,
  RefreshCw
} from 'lucide-react'

const Header = () => {
  const { theme, setTheme } = useTheme()
  const { isConnected, connectionStatus } = useWebSocket()
  const { systemStatus, currentExecution } = useMCP()

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark')
  }

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen()
    } else {
      document.exitFullscreen()
    }
  }

  const refreshConnection = () => {
    window.location.reload()
  }

  return (
    <header className="h-14 border-b border-border bg-card px-6 flex items-center justify-between">
      {/* Left side - Current status */}
      <div className="flex items-center space-x-4">
        {/* Connection status */}
        <div className="flex items-center space-x-2">
          {isConnected ? (
            <Wifi className="w-4 h-4 text-green-500" />
          ) : (
            <WifiOff className="w-4 h-4 text-red-500" />
          )}
          <span className="text-sm text-muted-foreground">
            {connectionStatus === 'connected' ? 'Connected' : 'Disconnected'}
          </span>
        </div>

        {/* Current execution indicator */}
        {currentExecution && (
          <div className="flex items-center space-x-2">
            <div className="status-indicator active"></div>
            <span className="text-sm text-muted-foreground">
              Running: {currentExecution.agent}
            </span>
          </div>
        )}

        {/* System status indicators */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1">
            <div className={`status-indicator ${systemStatus.mcpServer === 'connected' ? 'success' : 'error'}`}></div>
            <span className="text-xs text-muted-foreground">MCP</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className={`status-indicator ${systemStatus.langwatchService === 'connected' ? 'success' : 'error'}`}></div>
            <span className="text-xs text-muted-foreground">Langwatch</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className={`status-indicator ${Object.values(systemStatus.localLLMs).some(status => status === 'connected') ? 'success' : 'idle'}`}></div>
            <span className="text-xs text-muted-foreground">LLMs</span>
          </div>
        </div>
      </div>

      {/* Right side - Controls */}
      <div className="flex items-center space-x-2">
        {/* Refresh button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={refreshConnection}
          className="w-8 h-8 p-0"
        >
          <RefreshCw className="w-4 h-4" />
        </Button>

        {/* Theme toggle */}
        <Button
          variant="ghost"
          size="sm"
          onClick={toggleTheme}
          className="w-8 h-8 p-0"
        >
          {theme === 'dark' ? (
            <Sun className="w-4 h-4" />
          ) : (
            <Moon className="w-4 h-4" />
          )}
        </Button>

        {/* Fullscreen toggle */}
        <Button
          variant="ghost"
          size="sm"
          onClick={toggleFullscreen}
          className="w-8 h-8 p-0"
        >
          <Maximize2 className="w-4 h-4" />
        </Button>
      </div>
    </header>
  )
}

export default Header

