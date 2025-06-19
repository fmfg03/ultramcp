import React, { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  Search, 
  Filter, 
  Download, 
  RefreshCw, 
  AlertCircle, 
  CheckCircle, 
  XCircle,
  Clock,
  Eye,
  EyeOff,
  Settings,
  Trash2
} from 'lucide-react'

const LangwatchViewer = () => {
  const [logs, setLogs] = useState([])
  const [filteredLogs, setFilteredLogs] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedLevel, setSelectedLevel] = useState('all')
  const [selectedAgent, setSelectedAgent] = useState('all')
  const [isConnected, setIsConnected] = useState(false)
  const [isAutoRefresh, setIsAutoRefresh] = useState(true)
  const [selectedLog, setSelectedLog] = useState(null)
  const [stats, setStats] = useState({
    total: 0,
    errors: 0,
    warnings: 0,
    info: 0,
    debug: 0
  })
  
  const wsRef = useRef(null)
  const scrollRef = useRef(null)

  // WebSocket connection for real-time logs
  useEffect(() => {
    connectToLangwatch()
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  // Filter logs when search or filters change
  useEffect(() => {
    filterLogs()
  }, [logs, searchTerm, selectedLevel, selectedAgent])

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (isAutoRefresh && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [filteredLogs, isAutoRefresh])

  const connectToLangwatch = () => {
    try {
      // Connect to Langwatch WebSocket endpoint
      const wsUrl = `ws://localhost:8124/langwatch`
      wsRef.current = new WebSocket(wsUrl)

      wsRef.current.onopen = () => {
        setIsConnected(true)
        console.log('Connected to Langwatch')
      }

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          if (data.type === 'log') {
            addNewLog(data.log)
          } else if (data.type === 'stats') {
            setStats(data.stats)
          } else if (data.type === 'batch') {
            setLogs(data.logs)
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

      wsRef.current.onclose = () => {
        setIsConnected(false)
        console.log('Disconnected from Langwatch')
        
        // Attempt to reconnect after 3 seconds
        setTimeout(() => {
          if (isAutoRefresh) {
            connectToLangwatch()
          }
        }, 3000)
      }

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error)
        setIsConnected(false)
      }

    } catch (error) {
      console.error('Failed to connect to Langwatch:', error)
      setIsConnected(false)
    }
  }

  const addNewLog = (newLog) => {
    setLogs(prevLogs => {
      const updatedLogs = [...prevLogs, newLog]
      // Keep only last 1000 logs to prevent memory issues
      return updatedLogs.slice(-1000)
    })
    
    // Update stats
    setStats(prevStats => ({
      ...prevStats,
      total: prevStats.total + 1,
      [newLog.level]: (prevStats[newLog.level] || 0) + 1
    }))
  }

  const filterLogs = () => {
    let filtered = logs

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(log => 
        log.message?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.agent?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.session_id?.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    // Filter by level
    if (selectedLevel !== 'all') {
      filtered = filtered.filter(log => log.level === selectedLevel)
    }

    // Filter by agent
    if (selectedAgent !== 'all') {
      filtered = filtered.filter(log => log.agent === selectedAgent)
    }

    setFilteredLogs(filtered)
  }

  const clearLogs = () => {
    setLogs([])
    setFilteredLogs([])
    setStats({
      total: 0,
      errors: 0,
      warnings: 0,
      info: 0,
      debug: 0
    })
  }

  const exportLogs = () => {
    const dataStr = JSON.stringify(filteredLogs, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `langwatch_logs_${new Date().toISOString().split('T')[0]}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  const refreshLogs = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'refresh' }))
    } else {
      connectToLangwatch()
    }
  }

  const getLevelColor = (level) => {
    switch (level) {
      case 'error': return 'bg-red-100 text-red-800 border-red-200'
      case 'warning': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'info': return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'debug': return 'bg-gray-100 text-gray-800 border-gray-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getLevelIcon = (level) => {
    switch (level) {
      case 'error': return <XCircle className="w-4 h-4" />
      case 'warning': return <AlertCircle className="w-4 h-4" />
      case 'info': return <CheckCircle className="w-4 h-4" />
      case 'debug': return <Settings className="w-4 h-4" />
      default: return <Clock className="w-4 h-4" />
    }
  }

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString()
  }

  const getUniqueAgents = () => {
    const agents = [...new Set(logs.map(log => log.agent).filter(Boolean))]
    return agents.sort()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Langwatch Logs</h2>
          <p className="text-gray-600">Real-time monitoring of MCP agent execution</p>
        </div>
        
        <div className="flex items-center space-x-2">
          <Badge 
            variant={isConnected ? "default" : "destructive"}
            className="flex items-center space-x-1"
          >
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
          </Badge>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsAutoRefresh(!isAutoRefresh)}
            className="flex items-center space-x-1"
          >
            {isAutoRefresh ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
            <span>Auto-refresh</span>
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold">{stats.total}</div>
            <div className="text-sm text-gray-600">Total Logs</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-red-600">{stats.errors || 0}</div>
            <div className="text-sm text-gray-600">Errors</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-yellow-600">{stats.warnings || 0}</div>
            <div className="text-sm text-gray-600">Warnings</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-blue-600">{stats.info || 0}</div>
            <div className="text-sm text-gray-600">Info</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-gray-600">{stats.debug || 0}</div>
            <div className="text-sm text-gray-600">Debug</div>
          </CardContent>
        </Card>
      </div>

      {/* Controls */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-4">
            {/* Search */}
            <div className="flex-1 min-w-64">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="Search logs..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            {/* Level Filter */}
            <select
              value={selectedLevel}
              onChange={(e) => setSelectedLevel(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Levels</option>
              <option value="error">Error</option>
              <option value="warning">Warning</option>
              <option value="info">Info</option>
              <option value="debug">Debug</option>
            </select>

            {/* Agent Filter */}
            <select
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Agents</option>
              {getUniqueAgents().map(agent => (
                <option key={agent} value={agent}>{agent}</option>
              ))}
            </select>

            {/* Action Buttons */}
            <Button
              variant="outline"
              size="sm"
              onClick={refreshLogs}
              className="flex items-center space-x-1"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Refresh</span>
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={exportLogs}
              className="flex items-center space-x-1"
            >
              <Download className="w-4 h-4" />
              <span>Export</span>
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={clearLogs}
              className="flex items-center space-x-1 text-red-600 hover:text-red-700"
            >
              <Trash2 className="w-4 h-4" />
              <span>Clear</span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Logs Display */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Logs List */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Logs ({filteredLogs.length})</span>
                <Badge variant="outline">{selectedLevel !== 'all' ? selectedLevel : 'all levels'}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="h-96" ref={scrollRef}>
                <div className="space-y-1 p-4">
                  {filteredLogs.length === 0 ? (
                    <div className="text-center text-gray-500 py-8">
                      {logs.length === 0 ? 'No logs available' : 'No logs match current filters'}
                    </div>
                  ) : (
                    filteredLogs.map((log, index) => (
                      <div
                        key={index}
                        className={`p-3 rounded-lg border cursor-pointer transition-colors hover:bg-gray-50 ${
                          selectedLog === log ? 'bg-blue-50 border-blue-200' : 'border-gray-200'
                        }`}
                        onClick={() => setSelectedLog(log)}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-center space-x-2 flex-1">
                            <Badge className={`${getLevelColor(log.level)} flex items-center space-x-1`}>
                              {getLevelIcon(log.level)}
                              <span className="capitalize">{log.level}</span>
                            </Badge>
                            
                            {log.agent && (
                              <Badge variant="outline" className="text-xs">
                                {log.agent}
                              </Badge>
                            )}
                            
                            <span className="text-xs text-gray-500">
                              {formatTimestamp(log.timestamp)}
                            </span>
                          </div>
                        </div>
                        
                        <div className="mt-2">
                          <p className="text-sm text-gray-900 line-clamp-2">
                            {log.message}
                          </p>
                          
                          {log.session_id && (
                            <p className="text-xs text-gray-500 mt-1">
                              Session: {log.session_id}
                            </p>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        {/* Log Details */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle>Log Details</CardTitle>
            </CardHeader>
            <CardContent>
              {selectedLog ? (
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-gray-700">Level</label>
                    <div className="mt-1">
                      <Badge className={getLevelColor(selectedLog.level)}>
                        {getLevelIcon(selectedLog.level)}
                        <span className="ml-1 capitalize">{selectedLog.level}</span>
                      </Badge>
                    </div>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-700">Timestamp</label>
                    <p className="mt-1 text-sm text-gray-900">
                      {new Date(selectedLog.timestamp).toLocaleString()}
                    </p>
                  </div>

                  {selectedLog.agent && (
                    <div>
                      <label className="text-sm font-medium text-gray-700">Agent</label>
                      <p className="mt-1 text-sm text-gray-900">{selectedLog.agent}</p>
                    </div>
                  )}

                  {selectedLog.session_id && (
                    <div>
                      <label className="text-sm font-medium text-gray-700">Session ID</label>
                      <p className="mt-1 text-sm text-gray-900 font-mono">{selectedLog.session_id}</p>
                    </div>
                  )}

                  <div>
                    <label className="text-sm font-medium text-gray-700">Message</label>
                    <p className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">
                      {selectedLog.message}
                    </p>
                  </div>

                  {selectedLog.metadata && (
                    <div>
                      <label className="text-sm font-medium text-gray-700">Metadata</label>
                      <pre className="mt-1 text-xs text-gray-900 bg-gray-50 p-2 rounded overflow-auto max-h-32">
                        {JSON.stringify(selectedLog.metadata, null, 2)}
                      </pre>
                    </div>
                  )}

                  {selectedLog.stack_trace && (
                    <div>
                      <label className="text-sm font-medium text-gray-700">Stack Trace</label>
                      <pre className="mt-1 text-xs text-red-900 bg-red-50 p-2 rounded overflow-auto max-h-32">
                        {selectedLog.stack_trace}
                      </pre>
                    </div>
                  )}

                  {selectedLog.context && (
                    <div>
                      <label className="text-sm font-medium text-gray-700">Context</label>
                      <pre className="mt-1 text-xs text-gray-900 bg-gray-50 p-2 rounded overflow-auto max-h-32">
                        {JSON.stringify(selectedLog.context, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center text-gray-500 py-8">
                  Select a log entry to view details
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default LangwatchViewer

